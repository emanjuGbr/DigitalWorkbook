# -*- coding: utf-8 -*-

import logging

from odoo import models, api
from odoo.exceptions import UserError

from ..libs.owncloud_service import Client as OwncloudClient

_logger = logging.getLogger(__name__)


class owncloud_client(models.AbstractModel):
    _name = "owncloud.client"

    DEFAULT_ROOT_DIR = "Odoo"

    def upload_file(self, remote_path_components, local_path):
        """Upload a local file to a given Owncloud path."""
        client = self._get_client()
        remote_path_components.insert(0, self._get_root_dir())
        try:
            return client.upload(remote_path_components, local_path)
        except Exception as e:
            _logger.error(e, exc_info=True)
            raise UserError("Unable to upload file")

    def remove_file(self, path, file_id):
        """Remove a file from Owncloud."""
        client = self._get_client()
        try:
            client.remove(path, file_id)
        except Exception as e:
            _logger.error(e, exc_info=True)
            raise UserError("Unable to remove file")

    def get_object_directory_path(self, model, res_id):
        """Get a directory name for an object from Owncloud."""
        model_name = self.get_model_directory_path(model)
        obj = self.env[model].browse(res_id)
        object_name = u"{}_{}".format(obj.name_get()[0][1], res_id)
        ObjectMap = self.env['owncloud.object']
        object_map = ObjectMap.search(
            [('name', '=', model), ('res_id', '=', res_id)],
            limit=1,
            order='id desc',
        )
        client = self._get_client()
        owncloud_id, name = client.find_or_create_object_directory(
            (model_name, object_name),
            object_map.owncloud_id if object_map else False,
        )
        if not object_map:
            values = {
                'name': model,
                'res_id': res_id,
                'owncloud_id': owncloud_id,
            }
            ObjectMap.create(values)
        return [model_name, name]

    def get_model_directory_path(self, model):
        """Get a directory name for a model from Owncloud."""
        Model = self.env[model]
        ModelMap = self.env['owncloud.model']
        client = self._get_client()
        model_map = ModelMap.search(
            [
                ('name', '=', model),
            ],
            limit=1,
            order='id desc',
        )
        owncloud_id, name = client.find_or_create_model_directory(
            Model._description,
            model_map.owncloud_id if model_map else False,
        )
        if not model_map:
            values = {
                'name': model,
                'owncloud_id': owncloud_id,
            }
            ModelMap.create(values)
        return name

    def list_root(self):
        client = self._get_client()
        return client.list_root()

    def list_path(self, path):
        client = self._get_client()
        return client.list_path(path)

    def get_url(self, path):
        client = self._get_client()
        return client.get_url(path)

    def test_login(self):
        try:
            self.with_context(bypass_confirm=True)._get_client()
        except Exception as e:
            _logger.debug(e, exc_info=True)
            raise e

    @api.multi
    def _get_client(self):
        """Get an Owncloud client instance."""
        Config = self.env['ir.config_parameter']
        if (not Config.get_param('owncloud_state') == 'confirmed' and
                not self._context.get('bypass_confirm')):
            raise UserError('Owncloud credentials are not active.')
        url = Config.get_param('owncloud_url')
        login = Config.get_param('owncloud_login')
        password = Config.get_param('owncloud_password')
        root_dir = self._get_root_dir()
        if not (url and login and password):
            raise UserError("No credentials were provided for the Owncloud client.")
        try:
            return OwncloudClient(url, login, password, root_dir)
        except Exception as e:
            _logger.debug(e, exc_info=True)
            raise UserError(u'Unable to connect to an Owncloud instance: {}'.format(e))

    @api.model
    def _get_root_dir(self):
        """Get a root directory name for Owncloud."""
        return self.env['ir.config_parameter'].get_param(
            'owncloud_root_dir', self.DEFAULT_ROOT_DIR,
        )
