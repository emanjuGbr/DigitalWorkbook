# -*- coding: utf-8 -*-
{
    'name': 'Cloud Base',
    'version': '1.1',
    'category': 'Document Management',
    'summary': 'The core for Odoo integration with cloud file systems (ownCloud, Dropbox, Onedrive, etc.)',
    'description': '''
The technical base for Odoo integration with cloud services (such as ownCloud, Dropbox, Onedrive, etc.)
    ''',
    'price': '140.00',
    'currency': 'EUR',
    'auto_install': False,
    'author': 'IT Libertas',
    'website': 'https://odootools.com',
    'depends': [
        'document',
        'base_setup',
    ],
    'data': [
        'data/data.xml',
        'data/sync_formats_data.xml',
        'security/ir.model.access.csv',
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
    },

}
