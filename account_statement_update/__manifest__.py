# Copyright 2020 Ross Golder (https://golder.org)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Online Bank Statements Updater',
    'version': '14.0.1.0.0',
    'author':
        'Ross Golder',
    'website': 'https://golder.org/',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'summary': 'Update bank statements already imported',
    'depends': [
        'account_statement_import',
    ],
    'data': [
        'views/account_statement_update.xml',
    ],
    'installable': True,
}
