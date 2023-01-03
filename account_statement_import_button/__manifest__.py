# Copyright 2022 Ross Golder (https://golder.org)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Statement List Import Button',
    'version': '14.0.1.0.0',
    'author':
        'Ross Golder',
    'website': 'https://golder.org/',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'summary': 'Add Import button to statement list view',
    'depends': [
        'account_statement_import',
    ],
    'data': [
        'views/account_statement_import_button.xml',
    ],
    'qweb': [
        'static/src/xml/button.xml',
    ],
    'js': [
        'static/src/js/button.js',
    ],
    'installable': True,
}
