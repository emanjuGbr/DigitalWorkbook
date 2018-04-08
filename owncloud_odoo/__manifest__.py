# -*- coding: utf-8 -*-
{
    'name': 'OwnCloud Odoo Integration',
    'version': '1.1',
    'category': 'Document Management',
    'summary': 'Manage Odoo documents in OwnCloud/NextCloud (bilateral sync)',
    'description': '''


    ''',
    'price': '450.00',
    'currency': 'EUR',
    'auto_install': False,
    'author': 'IT Libertas',
    'website': 'https://odootools.com',
    'depends': [
        'cloud_base',
    ],
    'data': [
        'data/data.xml',
        'data/cron.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings.xml'
    ],
    'qweb': [

    ],
    'js': [

    ],
    'demo': [

    ],
    'test': [

    ],
    'license': 'Other proprietary',
    'images': [
        'static/description/main.png',
    ],
    'update_xml': [

    ],
    'application': True,
    'installable': True,
    'private_category': True,
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    'post_load': 'post_load',
    'uninstall_hook': 'uninstall_hook',
    'external_dependencies': {
        'python': ['six'],
    },

}
