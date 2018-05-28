# -*- coding: utf-8 -*-

import sys
import logging

_logger = logging.getLogger(__name__)

try:
    import onedrivesdk
    from asyncio import new_event_loop

    @staticmethod
    def load_session(**load_session_kwargs):
        """Override load_session for read session from string"""
        if load_session_kwargs.get("string"):
            import pickle
            return pickle.loads(load_session_kwargs["string"])
        else:
            return onedrivesdk.session.Session.load_session(**load_session_kwargs)

    def save_session(self, **save_session_kwargs):
        """Override save_session for dump session to string"""
        if save_session_kwargs.get("string"):
            import pickle
            return pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)
        else:
            return onedrivesdk.session.Session.save_session(self, **save_session_kwargs)

    onedrivesdk.session.Session.load_session = load_session
    onedrivesdk.session.Session.save_session = save_session

    if sys.version_info.major < 3:
        from onedrivesdk.request.children_collection import ChildrenCollectionRequestBuilder
        from onedrivesdk.request.item_request_builder import ItemRequestBuilder

        def __getitem__(self, key):
            """Get the ItemRequestBuilder with the specified key

            Args:
                key (str): The key to get a ItemRequestBuilder for

            Returns:
                :class:`ItemRequestBuilder<onedrivesdk.request.item_request_builder.ItemRequestBuilder>`:
                    A ItemRequestBuilder for that key
            """
            return ItemRequestBuilder(self.append_to_request_url(unicode(key)), self._client)

        ChildrenCollectionRequestBuilder.__getitem__ = __getitem__

    class Client(onedrivesdk.OneDriveClient):
        _cache = {}

        def __new__(cls, *args, **kwargs):
            """Overrwrite __new__ for using single client instance per database"""
            db_name = kwargs.get('db_name')
            if db_name in cls._cache:
                client = cls._cache.get(db_name)
            else:
                client = onedrivesdk.OneDriveClient.__new__(cls)
                cls._cache[db_name] = client
            return client

        def __init__(self, *args, **kwargs):
            kwargs.pop('db_name', False)
            super(Client, self).__init__(*args, loop=new_event_loop(), **kwargs)

except ImportError as e:
    _logger.error(e)
