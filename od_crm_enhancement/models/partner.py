# Copyright (C) 2018 - TODAY, Emanju.de
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if 'composition_mode' in self._context and self._context.get(
                'composition_mode') == 'comment':
            return super(ResPartner, self).name_search(name, args=args,
                                                       operator=operator,
                                                       limit=limit)
        elif 'show_email' in self._context and 'force_email' in self._context:
            partner_ids = []
            ('name', operator, name)
            for user in self.env['res.users'].search([]):
                partner_ids.append(user.partner_id.id)
            partner_ids = self.search(
                [('id', 'in', partner_ids), ('name', operator, name)])
            return partner_ids.name_get()
        return super(ResPartner, self).name_search(name, args=args,
                                                   operator=operator,
                                                   limit=limit)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None,
                    order=None):
        if 'composition_mode' in self._context and self._context.get(
                'composition_mode') == 'comment':
            super(ResPartner, self).search_read(domain=domain,
                                                fields=fields,
                                                offset=offset,
                                                limit=limit,
                                                order=order)
        elif 'show_email' in self._context and 'force_email' in self._context:
            partner_ids = []
            for user in self.env['res.users'].search([]):
                partner_ids.append(user.partner_id.id)
            domain += [('id', 'in', partner_ids)]
        return super(ResPartner, self).search_read(domain=domain,
                                                   fields=fields,
                                                   offset=offset,
                                                   limit=limit,
                                                   order=order)
