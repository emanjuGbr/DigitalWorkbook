# Copyright (C) 2018 - TODAY, Emanju.de
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    stage_id_3 = fields.Boolean('Stage name', compute='_get_stage_proposition')

    @api.multi
    def _get_stage_proposition(self):
        for lead in self:
            lead.stage_id_3 = True
            if lead.stage_id == self.env.ref('crm.stage_lead3'):
                lead.stage_id_3 = False

    @api.model
    def create(self, vals):
        if 'team_id' in vals and vals.get('team_id'):
            team = self.env['crm.team'].browse(vals.get('team_id'))
            if team.user_id:
                vals.update({'user_id': team.user_id.id})
        return super(CRMLead, self).create(vals)
