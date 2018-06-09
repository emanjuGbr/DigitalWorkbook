# -*- coding: utf-8 -*-

import logging

from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from ast import literal_eval

import json

_logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    _logger.debug('Cannot `import requests`.')

try:
    from onedrivesdk.helpers.resource_discovery import ResourceDiscoveryRequest, ServiceInfo

    class AnyVersionResourceDiscoveryRequest(ResourceDiscoveryRequest):

        def get_all_service_info(self, access_token, sharepoint_base_url):
            headers = {'Authorization': 'Bearer ' + access_token}
            response = json.loads(requests.get(self._discovery_service_url,
                                               headers=headers).text)
            service_info_list = [ServiceInfo(x) for x in response['value']]
            # Get all services, not just the ones with service_api_version 'v2.0'
            # Filter only on service_resource_id
            sharepoint_services = \
                [si for si in service_info_list
                 if si.service_resource_id == sharepoint_base_url]
            return sharepoint_services
except ImportError:
    _logger.debug('Cannot `import onedrivesdk`.')

PARAMS = (
    ('onedrive_client_id', str, ''),
    ('onedrive_client_secret', str, ''),
    ('onedrive_api_base_url', str, 'https://api.onedrive.com/v1.0/'),
    ('onedrive_api_auth_server_url', str, 'https://login.microsoftonline.com/common/oauth2/authorize'),
    ('onedrive_auth_token_url', str, 'https://login.microsoftonline.com/common/oauth2/token'),
    ('onedrive_auth_resource_url', str, 'https://api.office.com/discovery/'),
    ('onedrive_redirect_uri', str, 'http://localhost:8069/one_drive_token'),
    ('onedrive_business', safe_eval, False),
    ('onedrive_sharepoint_sites', safe_eval, False),
    ('onedrive_sharepoint_base_url', str, ''),
    ('onedrive_sharepoint_site_name', str, ''),
    ('onedrive_sharepoint_drive', str, 'my'),
    ('onedrive_drive_id', str, 'my'),
    ('onedrive_config_state', str, 'draft'),
)


class res_config_settings(models.TransientModel):
    _inherit = "res.config.settings"
    _description = "Transient model with configs for OneDrive"

    @api.model
    def get_values(self):
        Config = self.env['ir.config_parameter'].sudo()
        res = super(res_config_settings, self).get_values()
        values = {}
        for field_name, getter, default in PARAMS:
            values[field_name] = getter(str(Config.get_param(field_name, default)))
        res.update(values)
        return res

    def set_values(self):
        Config = self.env['ir.config_parameter'].sudo()
        super(res_config_settings, self).set_values()
        for field_name, _, _ in PARAMS:
            value = getattr(self, field_name)
            Config.set_param(field_name, str(value))

    onedrive_client_secret = fields.Char(
        string="App Secret key",
    )
    onedrive_client_id = fields.Char(
        string="App client_id",
    )
    onedrive_api_base_url = fields.Char(
        default='https://api.onedrive.com/v1.0/',
        string="Base API url",
    )
    onedrive_api_auth_server_url = fields.Char(
        default='https://login.microsoftonline.com/common/oauth2/authorize',
        string="Auth API url",
    )
    onedrive_auth_token_url = fields.Char(
        default='https://login.microsoftonline.com/common/oauth2/token',
        string="Token API url",
    )
    onedrive_auth_resource_url = fields.Char(
        default='https://api.office.com/discovery/',
        string="Resource discovery API url",
    )
    onedrive_redirect_uri = fields.Char(
        string="Redirect URL",
        default='http://localhost:8069/one_drive_token',
    )
    onedrive_business = fields.Boolean(
        string="OneDrive for business?",
    )
    onedrive_sharepoint_sites = fields.Boolean(
        string="Use sharepoint sites?",
    )
    onedrive_sharepoint_base_url = fields.Char(
        string="Sharepoint URL",
    )
    onedrive_sharepoint_site_name = fields.Char(
        string="Sharepoint site",
    )
    onedrive_sharepoint_drive = fields.Char(
        string="Directory on sharepoint site",
    )
    onedrive_drive_id = fields.Char(
        string="Drive id in OneDrive",
        default='me',
    )
    onedrive_config_state = fields.Selection(
        [('draft', 'Not Confirmed'), ('confirmed', 'Confirmed')],
        default='draft',
    )

    @api.multi
    def login_to_onedrive(self):
        """Opens new window with login page to onedrive"""
        self.ensure_one()
        Config = self.env['res.config.settings']
        Config.set_param('onedrive_session', '')
        auth_url = self.env['onedrive.client'].get_auth_url()
        res = {
            'name': 'Go to website',
            'res_model': 'ir.actions.act_url',
            'type': 'ir.actions.act_url',
            'target': 'current',
            'url': auth_url
        }
        return res

    @api.model
    def create_onedrive_session(self, code=False):
        """Authenticates to OndDrive with code from company or external one and creates session"""
        client = self.env['onedrive.client'].get_client()
        Config = self.env['res.config.settings']
        values = self.get_values()
        if code and client:
            _logger.debug("Trying to create onedrive session...")
            redirect_uri = values['onedrive_redirect_uri']
            client_secret = values['onedrive_client_secret']
            try:
                if values['onedrive_business']:
                    _logger.debug("Authenticate business account")
                    resource = Config.get_param("onedrive_auth_resource_url", "")
                    client.auth_provider.authenticate(
                        code, redirect_uri, client_secret,
                        resource=resource,
                    )
                    service_info = False
                    if values.get('onedrive_sharepoint_sites'):
                        sharepoint_base_url = Config.get_param("onedrive_sharepoint_base_url", "")
                        sharepoint_site = Config.get_param("onedrive_sharepoint_site_name", "")
                        _logger.debug("Trying to get sharepoint service info")
                        service_info = AnyVersionResourceDiscoveryRequest().get_all_service_info(
                            client.auth_provider.access_token, sharepoint_base_url,
                        )[0]
                        Config.set_param(
                            "onedrive_api_base_url",
                            '{}sites/{}/_api/v2.0/'.format(sharepoint_base_url, sharepoint_site),
                        )
                    else:
                        _logger.debug("Trying to get service info")
                        service_info = ResourceDiscoveryRequest().get_service_info(client.auth_provider.access_token)[0]
                        self.env["res.config.settings"].set_param(
                            "onedrive_api_base_url",
                            service_info.service_resource_id + '_api/v2.0/',
                        )
                    _logger.debug("Trying to redeem refresh token")
                    client.auth_provider.redeem_refresh_token(service_info.service_resource_id)

                else:
                    _logger.debug("Authentificate simple account")
                    client.auth_provider.authenticate(code, redirect_uri, client_secret)
                self.env['onedrive.client'].save_session(client)
                Config.set_param('onedrive_config_state', 'confirmed')
            except Exception as e:
                _logger.debug('Authentification failed. Reason: {}'.format(e))
                raise UserError("Can't authenticate to OneDrive")
        else:
            _logger.debug("No valid code or client provided. Code: {}".format(code))
            raise UserError("Can't authenticate to OneDrive")

    @api.model
    def search_drive_id(self, client=None):
        """Search drive_id in OneDrive for selected directory if business or me"""
        Config = self.env['res.config.settings']
        client = self.env['onedrive.client'].get_client()
        sharepoint_sites = Config.get_param('onedrive_sharepoint_sites', '')
        sharepoint_drive = Config.get_param('onedrive_sharepoint_drive', 'me')
        _logger.debug(
            'Search Onedrive drive "%s" on sharepoint sites "%s"',
            sharepoint_drive, sharepoint_sites,
        )
        drive = 'me'
        if sharepoint_sites:
            for prop in client.drives.get()._prop_list:
                if prop['name'] == sharepoint_drive:
                    drive = prop['id']
                    break
        _logger.debug('Set onedrive active drive to "%s"', drive)
        Config.set_param('onedrive_drive_id', drive)

    @api.multi
    def test_connection(self, client=None):
        """Example function of OneDrive client usage"""
        Config = self.env['res.config.settings']
        client = self.env['onedrive.client'].get_client()
        self.ensure_one()
        try:
            drive_id = Config.get_param("onedrive_drive_id", "me")
            client.item(drive=drive_id, id='root').children.request(top=5).get()
        except:
            raise UserError("Can't establish connection!")
        else:
            raise UserError("Success!")

    @api.multi
    def reset(self):
        params, _, _ = zip(*PARAMS)

        _logger.debug(
            'Reset Onedrive configuration',
        )

        self._cr.execute('DELETE FROM ir_config_parameter WHERE key IN %s', (params,))

        _logger.debug(
            'Cleanup Onedrive tables with external ids from previous configuration',
        )
        self._cr.execute("DELETE FROM onedrive_model")
        self._cr.execute("DELETE FROM onedrive_object")
        return {
            'name': 'OneDrive Settings',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'inline',
            'res_model': 'res.config.settings',
        }

    @api.multi
    def sync_to_onedrive(self):
        self.env['ir.attachment'].cron_synchronize_attachments()

    @api.multi
    def sync_from_onedrive(self):
        self.env['ir.attachment'].cron_update_from_onedrive()

    @api.model
    def get_param(self, param, default=False):
        """
        Alias for ir.config_parameter method get_param.
        If getter specified for param - apply it
        """
        Config = self.env['ir.config_parameter'].sudo()
        local_params = { key: (value, default) for key, value, default in PARAMS}
        res = Config.get_param(param, default)
        if param in local_params:
            getter = local_params[param][0]
            try:
                res = getter(res)
            except:
                pass
        return res

    @api.model
    def set_param(self, param, value):
        """
        Alias for ir.config_parameter method set_param.
        """
        return self.env['ir.config_parameter'].sudo().set_param(param, value)
