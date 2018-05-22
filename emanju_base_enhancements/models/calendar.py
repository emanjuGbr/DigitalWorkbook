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

    @api.model
    def create(self, vals):
        res = super(CalendarAttendee, self).create(vals)
        my_list = [x.id for x in res.partner_ids]
        user_list = self.env['res.users'].search(
                    [('partner_id', 'in', my_list),
                     ('calendar_notification_type', '=', 'on')])
        new_partner_list = [x.partner_id.id for x in user_list]
        message = self.env['mail.message'].create(
            {'body': res.description,
             'subject': res.name,
             'message_type': 'comment',
             'subtype_id': self.env.ref('mail.mt_comment').id,
             'res_id': res.id,
             'author_id': 1,
             'model': 'calendar.event',
             'partner_ids' : [(6, 0, new_partner_list)]})
        for partner in new_partner_list:
            noti = self.env['mail.notification'].create(
                {'mail_message_id' : message.id,
                 'res_partner_id' : partner})
        return res
