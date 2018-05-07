# Copyright (C) 2018 - TODAY, Emanju.de
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    calendar_notification_type = fields.Selection([
        ('on', 'On'),
        ('off', 'Off')],
        'Calendar Notification', default="off",
        help="Policy on how to handle Chatter notifications:\n"
             "- On: Enable to receive messages in the inbox for new meeting "
             "invitations)\n"
             "- Off: Disable to receive messages in the inbox for new meeting "
             "invitations)"
    )
