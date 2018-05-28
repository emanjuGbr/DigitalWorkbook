# -*- coding: utf-8 -*-
{
    'name': 'Odoo OneDrive Integration',
    'version': '11.0.1.0.0',
    'category': 'Document Management',
    'summary': 'The tool to automatically synchronize Odoo attachments with OneDrive files in both ways',
    'description': '''
Odoo OneDrive Integration
=======
This Odoo tool manages an automatic synchronization between Odoo documents and OneDrive/Sharepoint files.
Deals with documents in Odoo have not changed but now the attachments are hierarchically stored in one cloud.
Thus, you can manage them into the cloud.
    ''',
    'auto_install': False,
    'author': 'IT Libertas',
    'website': 'https://itlibertas.com',
    'depends': [
        'cloud_base',
    ],
    'price': '450.00',
    'currency': 'EUR',
    'data': [
        'data/data.xml',
        'data/cron.xml',
        'views/res_config_settings.xml',
        'views/ir_attachment_view.xml',
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
        'python': [
            'onedrivesdk',
            'requests',
            'asyncio',
        ],
    },

}
