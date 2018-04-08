# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)

try:
    import six
    from owncloud import Client as OwncloudClient, FileInfo, HTTPResponseError
    from six.moves.urllib import parse
except ImportError as e:
    _logger.error(e)
    OwncloudClient = object
    FileInfo = object


class FileInfo(FileInfo):

    def get_file_id(self):
        return self.attributes.get('{http://owncloud.org/ns}fileid')


class PatchedClient(OwncloudClient):

    def __init__(self, *args, **kwargs):
        super(PatchedClient, self).__init__(*args, **kwargs)
        self._odoo_login = None

    def login(self, login, password):
        result = super(PatchedClient, self).login(login, password)
        self._odoo_login = login
        return result

    def list(self, path, depth=1):
        """The list method extension for getting additional file attributes
        from Owncloud."""
        if not path.endswith('/'):
            path += '/'

        headers = {}
        if isinstance(depth, int) or depth == "infinity":
            headers['Depth'] = str(depth)
        data = """<?xml version="1.0"?>
            <d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
              <d:prop>
                    <d:getlastmodified />
                    <d:getetag />
                    <d:getcontenttype />
                    <d:resourcetype />
                    <d:getcontentlength />
                    <d:quota-available-bytes />
                    <d:quota-used-bytes />
                    <oc:fileid />
                    <oc:permissions />
                    <oc:size />
              </d:prop>
            </d:propfind>
        """
        res = self._make_dav_request(
            'PROPFIND',
            path,
            headers=headers,
            data=data,
        )
        # first one is always the root, remove it from listing
        if res:
            return res[1:]
        return None

    def _parse_dav_element(self, dav_response):
        """Return an instance of the modified FileInfo class."""
        href = parse.unquote(
            self._strip_dav_path(dav_response.find('{DAV:}href').text)
        )
        if six.PY2:
            href = href.decode('utf-8')

        file_type = 'file'
        if href[-1] == '/':
            file_type = 'dir'

        file_attrs = {}
        attrs = dav_response.find('{DAV:}propstat')
        attrs = attrs.find('{DAV:}prop')
        for attr in attrs:
            file_attrs[attr.tag] = attr.text

        return FileInfo(href, file_type, file_attrs)


class Client(object):
    """Caching wrapper for the owncloud client."""

    _cache = []

    @classmethod
    def _get_cached_client(cls, url, login):
        """Find a cached client instance for the given credentials."""
        cached_clients = list(filter(
            lambda c: c.client._odoo_login == login and c.client.url.startswith(url),
            cls._cache,
        ))
        if cached_clients:
            return cached_clients[0]

    def __new__(cls, url, login, password, root_dir):
        client = cls._get_cached_client(url, login)
        if not client:
            client = super(Client, cls).__new__(cls)
        return client

    def __init__(self, url, login, password, root_dir):
        if self not in self._cache:
            self._cache.append(self)
            self.root_dir = root_dir
            self.client = PatchedClient(url)
            self.client.login(login, password)

    def upload(self, remote_path_components, local_path):
        """Upload a file to a given path.
        Create intermediate directories if needed."""
        remote_file_dir = remote_path_components[:-1]
        file_name = remote_path_components[-1]
        for counter, remote_path_part in enumerate(remote_file_dir):
            parent_dir = self._build_path(remote_path_components[:counter])
            current_dir = self._build_path(remote_path_components[:counter + 1])
            ls = [
                p.get_path() for p in
                self.client.list(parent_dir if counter else '.')
            ]
            if current_dir not in ls:
                mkdir_ok = self.client.mkdir(current_dir)
                if not mkdir_ok:
                    raise UserWarning(u"Unable to create remote directory: {}".format(current_dir))
        full_remote_path = self._build_path(remote_path_components)
        upload_ok = self.client.put_file(full_remote_path, local_path)
        if upload_ok:
            ls = self.client.list(self._build_path(remote_file_dir))
            remote_file = list(filter(lambda d: d.get_name() == file_name, ls))[0]
            return (
                remote_file.get_file_id(),
                full_remote_path,
                self.client.share_file_with_link(full_remote_path).get_link(),
            )

    def mkdir(self, path):
        return self.client.mkdir(path)

    def remove(self, path, file_id):
        full_path = self._build_path([self.root_dir] + path)
        ls = self.client.list(full_path)
        file_to_delete = list(filter(lambda f: f.get_file_id() == file_id, ls))
        if file_to_delete:
            self.client.delete(file_to_delete[0].path)

    def find_or_create_model_directory(self, model_dir, file_id=False):
        """Find or create an Owncloud directory using a given path."""
        self._make_sure_root_dir_exists()
        ls = self.client.list(self.root_dir)
        abs_path = [self.root_dir]
        return self._find_or_create_directory(ls, model_dir, file_id, abs_path)

    def find_or_create_object_directory(self, path, file_id=False):
        """Find or create an Owncloud directory using a given path."""
        model_dir, object_dir = path
        abs_path = [self.root_dir, model_dir]
        ls = self.client.list(self._build_path(abs_path))
        return self._find_or_create_directory(ls, object_dir, file_id, abs_path)

    def list_root(self):
        self._make_sure_root_dir_exists()
        dirs = self.client.list(self.root_dir)
        return {d.get_file_id(): d.get_path() for d in dirs}

    def list_path(self, path):
        dirs = self.client.list(path)
        return {d.get_file_id(): (d.get_name(), d.path) for d in dirs}

    def get_url(self, path):
        return self.client.share_file_with_link(path).get_link()

    def _find_or_create_directory(self, ls, dir_name, file_id, abs_path):
        result = None
        if file_id:
            matching_dir = list(filter(lambda d: d.get_file_id() == file_id, ls))
            if matching_dir:
                result = matching_dir[0]
        if not result:
            ls_name = map(lambda d: d.get_name(), ls)
            if dir_name in ls_name:
                # create a new directory using a numeric postfix in case of collision
                is_unique = False
                postfix = 1
                while not is_unique:
                    new_name = u'{}_{}'.format(dir_name, postfix)
                    is_unique = new_name not in ls_name
                    postfix += 1
                dir_name = new_name
            full_path = self._build_path(abs_path + [dir_name])
            mkdir_ok = self.mkdir(full_path)
            if not mkdir_ok:
                raise UserWarning(u"Unable to create remote directory: {}".format(full_path))
            ls = self.client.list(self._build_path(abs_path))
            result = list(filter(lambda d: d.get_name() == dir_name, ls))[0]
        return result.get_file_id(), result.get_name()

    def _build_path(self, components):
        return u'/' + u'/'.join(components)

    def _make_sure_root_dir_exists(self):
        root_dir = self.root_dir
        try:
            self.client.list(root_dir)
        except HTTPResponseError:
            self.client.mkdir(root_dir)
