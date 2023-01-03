# Copyright 2020 Ross Golder (https://golder.org)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Custom bank statements handler',
    'version': '14.0.1.0.0',
    'author':
        'Ross Golder',
    'website': 'https://golder.org/',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'summary': 'Imports new lines into an existing bank statement.',
    'depends': [
        'account_statement_import',
    ],
    'data': [
        'views/account_statement_update.xml',
    ],
    'installable': True,
}
