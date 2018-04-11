# Copyright (C) 2018 - TODAY, Emanju.de
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def find_or_create_root_directory(self, client):
        """Find or create Odoo root directory on OneDrive"""
        Config = self.env['res.config.settings']
        drive = Config.get_param('onedrive_drive_id', 'me')
        res_id = Config.get_param('onedrive_root_dir_id', '')
        if not res_id:
            res_id = mkdir(client, drive, 'root', 'Odoo')
            Config.set_param('onedrive_root_dir_id', res_id)
        return res_id

    @api.multi
    def find_or_create_model_directory(self, client, root_id):
        """Find or create directory for model of related object"""
        self.ensure_one()
        Config = self.env['res.config.settings']
        drive = Config.get_param('onedrive_drive_id', 'me')
        model = self.env['onedrive.model'].search(
            [('name', '=', 'res.partner')],
            limit=1,
        )
        if model:
            return client.item(id=model.onedrive_id)

        res_id = mkdir(
            client, drive, root_id, self.env['res.partner']._description)

        values = {
            'name': 'res.partner',
            'onedrive_id': res_id,
        }
        self.env['onedrive.model'].create(values)

        return res_id

    @api.multi
    def find_or_create_object_directory(self, client, model_dir_id):
        """Find or create directory for related object"""
        self.ensure_one()
        Config = self.env['res.config.settings']
        drive = Config.get_param('onedrive_drive_id', 'me')

        obj = self.env['onedrive.object'].search(
            [('name', '=', 'res.partner'), ('res_id', '=', self.id)],
            limit=1,
        )
        if obj:
            return client.item(id=obj.onedrive_id)

        res = mkdir(client, drive, model_dir_id, self.id)

        values = {
            'name': 'res.partner',
            'res_id': self.id,
            'onedrive_id': res,
        }
        self.env['onedrive.object'].create(values)
        return client.item(id=res)


    @api.multi
    def redirect_onedrive_folder(self):
        "Redirect to Onedrive Contacts folder"
        self.ensure_one()
        # Check credentials for login
        Client = self.env['onedrive.client'].get_client()
        # Set path to redirect
        root_dir = self.find_or_create_root_directory(client)
        model_dir = self.find_or_create_model_directory(client, root_dir)
        object_dir = self.find_or_create_object_directory(client, model_dir)
        path = client.item(
            id=object_dir.id).create_link('view').post().link.web_url
        return {
            'type': 'ir.actions.act_url',
            'url': path,
            'target': 'new',
        }
