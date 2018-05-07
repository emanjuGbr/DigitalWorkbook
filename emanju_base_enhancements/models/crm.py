# Copyright (C) 2018 - TODAY, Emanju.de
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def create(self, vals):
        # Check team id at create time
        if 'team_id' in vals and vals.get('team_id'):
            # Browse team record
            team = self.env['crm.team'].browse(vals.get('team_id'))
            # Check team has Channel leader
            if team.user_id:
                # Assign channel leader to salesperson
                vals.update({'user_id': team.user_id.id})
        return super(CRMLead, self).create(vals)
