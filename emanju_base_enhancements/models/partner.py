# Copyright (C) 2018 - TODAY, Emanju.de
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        # At the drop down time, method will be fire
        if 'composition_mode' in self._context and self._context.get(
                'composition_mode') == 'comment':
            # Display external contacts
            return super(ResPartner, self).name_search(name, args=args,
                                                       operator=operator,
                                                       limit=limit)
        elif 'show_email' in self._context and 'force_email' in self._context:
            # Restrict external contacts to followup
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
        # User enter any keyword to search contact name, method will fire
        if 'composition_mode' in self._context and self._context.get(
                'composition_mode') == 'comment':
            # Display external contacts
            super(ResPartner, self).search_read(domain=domain,
                                                fields=fields,
                                                offset=offset,
                                                limit=limit,
                                                order=order)
        elif 'show_email' in self._context and 'force_email' in self._context:
            # Restrict external contacts to followup
            partner_ids = []
            for user in self.env['res.users'].search([]):
                partner_ids.append(user.partner_id.id)
            domain += [('id', 'in', partner_ids)]
        return super(ResPartner, self).search_read(domain=domain,
                                                   fields=fields,
                                                   offset=offset,
                                                   limit=limit,
                                                   order=order)

    @api.model
    def _get_default_country(self):
        country = self.env['res.country'].search(
            [('code', '=', 'DE')], limit=1)
        return country

    country_id = fields.Many2one(
        'res.country',
        string='Country',
        default=_get_default_country
    )
