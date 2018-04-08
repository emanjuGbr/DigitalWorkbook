# Copyright (C) 2018 - TODAY, Emanju.de
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    @api.multi
    def redirect_one_drive_folder(self):
        "Redirect to Onedrive Leads folder"
        self.ensure_one()
        Owncloud = self.env['owncloud.client']
        # Check credentials for login
        Client = Owncloud._get_client()
        # Set path to redirect
        path = Owncloud.get_object_directory_path('crm.lead', self.id)
        return {
            'type': 'ir.actions.act_url',
            'url': Client.get_url(path),
            'target': 'new',
        }
