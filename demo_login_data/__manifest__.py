# -*- coding: utf-8 -*-
{
    'name': "demo_login_data",

    'summary': """
        This modules adds login credentials to the login screen for demo instance.""",

    'description': """
        This modules adds login credentials to the login screen for demo instance.
    """,

    'author': "emanju",
    'website': "http://www.emanju.de",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'web'],

    # always loaded
    'data': [
        'views/webclient_templates.xml',
    ],
}