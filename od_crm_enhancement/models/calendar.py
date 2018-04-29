# Copyright (C) 2018 - TODAY, Emanju.de
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class CalendarAttendee(models.Model):
    _inherit = 'calendar.attendee'

    @api.multi
    def _send_mail_to_attendees(self, template_xmlid, force_send=False):
        """ Send mail for event invitation to event attendees only if calendar notification is on.
            :param template_xmlid: xml id of the email template to use to send the invitation
            :param force_send: if set to True, the mail(s) will be sent immediately (instead of the next queue processing)
        """
        if self._context.get('exclude_mail_to_attendees'):
            return super(CalendarAttendee, self)._send_mail_to_attendees(
                    template_xmlid, force_send=force_send)
        new_attendee_list = []
        for attendee in self:
            # Find related attendee's User
            user = self.env['res.users'].search(
                [('partner_id', '=', attendee.partner_id.id)])
            # Check calendar notification type
            if user.calendar_notification_type == 'on':
                new_attendee_list.append(attendee.id)
        # Send updated attendee list and update context to avoid recursive
        ctx = {'exclude_mail_to_attendees': True}
        self = self.browse(new_attendee_list)
        return self.with_context(ctx)._send_mail_to_attendees(
            template_xmlid, force_send=force_send)
