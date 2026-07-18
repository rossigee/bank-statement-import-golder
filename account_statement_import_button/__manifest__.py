# Copyright 2022 Ross Golder (https://golder.org)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Statement List Import Button',
    'version': '17.0.1.1.0',
    'author': 'Ross Golder',
    'website': 'https://golder.org/',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'summary': 'Add Import (OCA) button to bank statement list view',
    'depends': [
        'account_statement_import_base',
    ],
    'assets': {
        'web.assets_backend': [
            'account_statement_import_button/static/src/xml/button.xml',
            'account_statement_import_button/static/src/js/button.js',
        ],
    },
    'installable': True,
}
