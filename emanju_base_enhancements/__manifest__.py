# Copyright (C) 2018 - TODAY, Emanju.de
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Emnanju base enhancements",
    "summary": "Enhances Odoo to suit to the usage of the industry",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "Bhavesh Odedra, Emanju",
    "category": "CRM",
    "website": "emanju.de",
    "depends": ["mail", "crm", "calendar"],
    "data": [
        #"data/mail_data.xml",
        "data/mail_template_data.xml",
        "views/mail_templates_chatter.xml",
        "views/mail_compose_message.xml",
        "views/calendar_view.xml",
        "wizard/mail_compose_message_view.xml",
    ],
    "installable": True,
}
