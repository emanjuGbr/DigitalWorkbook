# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

PARAMS = [
    ("owncloud_url", ""),
    ("owncloud_login", ""),
    ("owncloud_password", ""),
    ("owncloud_root_dir", "Odoo"),
    ("owncloud_state", "draft"),
]


class res_config_settings(models.TransientModel):
    _inherit = "res.config.settings"

    owncloud_url = fields.Char(string="Url")
    owncloud_login = fields.Char(string="Login")
    owncloud_password = fields.Char(string="Password")
    owncloud_root_dir = fields.Char(string="Root Directory")
    owncloud_state = fields.Selection(
        (
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
        ),
        string="State",
    )

    @api.model
    def get_values(self):
        Config = self.env['ir.config_parameter'].sudo()
        res = super(res_config_settings, self).get_values()
        values = {}
        for field_name, default in PARAMS:
            values[field_name] = Config.get_param(field_name, default)
        res.update(**values)
        return res

    @api.multi
    def set_values(self):
        Config = self.env['ir.config_parameter'].sudo()
        super(res_config_settings, self).set_values()
        for field_name, default in PARAMS:
            value = getattr(self, field_name, default)
            Config.set_param(field_name, value)

    @api.multi
    def action_test_owncloud(self):
        self.set_values()
        try:
            self.env['owncloud.client'].test_login()
            return self.action_confirm_owncloud()
        except Exception as e:
            _logger.debug(e)
            raise UserError(
                'Please check your Owncloud credentials.'
                'It seems that some of the parameters is not correctly set.'
            )

    @api.multi
    def action_confirm_owncloud(self):
        self.env['ir.config_parameter'].set_param('owncloud_state', 'confirmed')
        return self.action_open_owncloud_config()

    @api.multi
    def action_reset_owncloud(self):
        self.env['ir.config_parameter'].set_param('owncloud_state', 'draft')
        return self.action_open_owncloud_config()

    @api.multi
    def action_open_owncloud_config(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'res.config.settings',
            'target': 'inline',
            'context': {
                'module': 'owncloud',
            }
        }

    @api.multi
    def action_sync_to_owncloud(self):
        self.env['ir.attachment'].cron_synchronize_attachments()

    @api.multi
    def action_sync_from_owncloud(self):
        self.env['ir.attachment'].cron_update_from_owncloud()
