# Copyright (C) 2018 - TODAY, Emanju.de
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Emanju branding",
    "summary": "provides the scope (dependencies), configuration and data of "
               "Odoo",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "Bhavesh Odedra, Emanju",
    "category": "CRM",
    "website": "emanju.de",
    "depends": [
        "web",
        "web_tour",
        "web_enterprise",
    ],
    "data": [
        "views/webclient_templates.xml",
    ],
    "qweb": [
        "static/src/xml/base.xml",
    ],
    "installable": True,
}
