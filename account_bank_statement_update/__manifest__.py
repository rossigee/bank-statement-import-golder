# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Online Bank Statements Updater',
    'version': '12.0.1.0.0',
    'author':
        'Ross Golder',
    'website': 'https://golder.org/',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'summary': 'Update bank statements already imported',
    'depends': [
        'account_bank_statement_import',
    ],
    'data': [
        'views/account_bank_statement_update.xml',
    ],
    'installable': True,
}
