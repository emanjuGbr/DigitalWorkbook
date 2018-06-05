# Copyright (C) 2018 - TODAY, Emanju.de
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
import html2text


class CalendarAttendee(models.Model):
    _inherit = 'calendar.event'

    template_id = fields.Many2one(
        'mail.template',
        domain=[('model', '=', 'calendar.event')]
    )

    @api.onchange('template_id')
    def onchange_template_id(self):
        if self.template_id and self.template_id.body_html:
            self.description = html2text.html2text(self.template_id.body_html)
