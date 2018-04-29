# Copyright (C) 2018 - TODAY, Emanju.de
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    stage_id_3 = fields.Boolean('Stage name', compute='_get_stage_proposition')

    @api.multi
    def _get_stage_proposition(self):
        for lead in self:
            # Disable Mark won/lost button
            lead.stage_id_3 = True
            # Get proposition xml ID
            if lead.stage_id == self.env.ref('crm.stage_lead3'):
                # Enable Mark won/lost button
                lead.stage_id_3 = False

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

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        # Load data from Kanban view
        if 'search_default_partner_id' in self._context:
            domain += ['|', ('active', '=', True), ('active', '=', False)]
        return super(CRMLead, self).read_group(domain,
                                               fields,
                                               groupby,
                                               offset=offset,
                                               limit=limit,
                                               orderby=orderby)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None,
                    order=None):
        # Load data from list view
        if 'search_default_partner_id' in self._context:
            domain += ['|', ['active', '=', True], ['active', '=', False]]
        return super(CRMLead, self).search_read(domain=domain,
                                                fields=fields,
                                                offset=offset,
                                                limit=limit,
                                                order=order)

