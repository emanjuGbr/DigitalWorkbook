# -*- coding: utf-8 -*-

import logging
import base64

from odoo import api, models

_logger = logging.getLogger(__name__)

try:
    from .onedrive_service import Client, onedrivesdk
    from asyncio import new_event_loop
except ImportError as e:
    _logger.debug(e)


class onedrive_client(models.AbstractModel):
    _name = "onedrive.client"

    def get_auth_url(self, client=None):
        """Get URL of authentification page"""
        Config = self.env['res.config.settings']
        Config.set_param('onedrive_session', '')

        client = client or self.get_client()
        url = client.auth_provider.get_auth_url(
            Config.get_param('onedrive_redirect_uri', ''),
        )
        return url

    @api.model
    def save_session(self, client):
        """Save session of client to database"""
        Config = self.env['res.config.settings']
        res = client.auth_provider._session.save_session(string=True)
        Config.set_param('onedrive_session', base64.b64encode(res))

    @api.model
    def load_session(self, client):
        """Load session of client from database"""
        Config = self.env['res.config.settings']
        session_pickle = base64.b64decode(Config.get_param('onedrive_session', ''))
        try:
            client.auth_provider.load_session(string=session_pickle)
        except Exception as e:
            _logger.error('Onedrive: Can\'t restore session: %s\nSession:\n%s', e, session_pickle)
            Config.set_param('onedrive_session', '')
        client.auth_provider.refresh_token()

    @api.model
    def get_client(self):
        """Returns initialized onedrivesdk Client instance"""
        Config = self.env['res.config.settings']
        base_url = Config.get_param('onedrive_api_base_url', '')
        http_provider = onedrivesdk.HttpProvider()
        auth_provider_params = {
            'http_provider': http_provider,
            'client_id': Config.get_param('onedrive_client_id', ''),
            'loop': new_event_loop(),
        }

        if Config.get_param('onedrive_business'):
            auth_provider_params.update({
                'auth_server_url': Config.get_param('onedrive_api_auth_server_url', ''),
                'auth_token_url': Config.get_param('onedrive_auth_token_url', ''),
            })
        else:
            auth_provider_params.update({
                'scopes': ['wl.signin', 'onedrive.readwrite', 'wl.offline_access'],
            })

        auth_provider = onedrivesdk.AuthProvider(**auth_provider_params)
        client = Client(base_url, auth_provider, http_provider, db_name=self._cr.dbname)
        if Config.get_param('onedrive_session', ''):
            self.load_session(client)

        return client
