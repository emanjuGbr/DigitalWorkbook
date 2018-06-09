# Copyright (C) 2018 - TODAY, Emanju.de
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _compute_opportunity_count(self):
        # Recompute opportunity count
        for partner in self:
            # the opportunity count should counts the opportunities of this \
            #company and all its contacts
            operator = 'child_of' if partner.is_company else '='
            partner.opportunity_count = self.env['crm.lead'].search_count(
                [('partner_id', operator, partner.id),
                 ('type', '=', 'opportunity'),
                 '|', ('active', '=', False), ('active', '=', True)])
