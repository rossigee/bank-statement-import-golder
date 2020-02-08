# Copyright 2020 Ross Golder (https://golder.org)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from calendar import monthrange
from decimal import Decimal
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    def _create_bank_statements(self, stmts_vals):
        """ Create new bank statements from imported values, filtering out already imported transactions, and returns data used by the reconciliation widget """
        BankStatementLine = self.env['account.bank.statement.line']

        # Filter out already imported transactions and create statements
        statement_ids = []
        ignored_statement_lines_import_ids = []
        for st_vals in stmts_vals:
            filtered_st_lines = []
            for line_vals in st_vals['transactions']:
                if 'unique_import_id' not in line_vals \
                   or not line_vals['unique_import_id'] \
                   or not bool(BankStatementLine.sudo().search([('unique_import_id', '=', line_vals['unique_import_id'])], limit=1)):
                    filtered_st_lines.append(line_vals)
                else:
                    ignored_statement_lines_import_ids.append(line_vals['unique_import_id'])
                    if 'balance_start' in st_vals:
                        st_vals['balance_start'] += float(line_vals['amount'])

            if len(filtered_st_lines) > 0:
                # Remove values that won't be used to create records
                st_vals.pop('transactions', None)
                # Create the statement
                st_vals['line_ids'] = [[0, False, line] for line in filtered_st_lines]
                statement_ids.append(self._find_or_create_statement_ids(st_vals))
        if len(statement_ids) == 0:
            raise UserError(_('You have already imported all transactions in that file.'))

        # Prepare import feedback
        notifications = []
        num_ignored = len(ignored_statement_lines_import_ids)
        if num_ignored > 0:
            notifications += [{
                'type': 'warning',
                'message': _("%d transactions had already been imported and were ignored.") % num_ignored if num_ignored > 1 else _("1 transaction had already been imported and was ignored."),
                'details': {
                    'name': _('Already imported items'),
                    'model': 'account.bank.statement.line',
                    'ids': BankStatementLine.search([('unique_import_id', 'in', ignored_statement_lines_import_ids)]).ids
                }
            }]
        return statement_ids, notifications

    def _complete_stmts_vals(self, stmts_vals, journal, account_number):
        for st_vals in stmts_vals:
            st_vals['journal_id'] = journal.id

            # Set statement name based on first transaction date year and month
            transactions = st_vals['transactions']
            if len(transactions) == 0:
                raise UserError(_('No transactions found in statement'))
            st_vals['name'] = transactions[0]['date'][0:7]

            # Set statement date based on last day of month
            year = int(st_vals['name'][0:4])
            month = int(st_vals['name'][5:7])
            st_vals['date'] = st_vals['name'] + "-" + str(monthrange(year, month)[1])
        return stmts_vals

    def _find_or_create_statement_ids(self, st_vals):
        BankStatement = self.env['account.bank.statement']
        BankStatementLine = self.env['account.bank.statement.line']

        # Get statement name from date of first line
        lines = st_vals['line_ids']
        journal_id = st_vals['journal_id']
        if len(lines) == 0:
            raise UserError(_('No lines found in statement'))
        st_name = lines[0][2]['date'][0:7]

        # If no statement for this date, create one and return it
        journal_id = st_vals['journal_id']
        stmt = BankStatement.search([
            ('name', '=', st_name),
            ('journal_id', '=', journal_id)
        ], limit=1)
        if not(bool(stmt)):
            return BankStatement.create(st_vals).id

        # Otherwise, add transactions to existing statement
        for line_vals in lines:
            trx = line_vals[2]
            trx['statement_id'] = stmt.id
            BankStatementLine.create(trx)

        # Update statement ending value
        _logger.info(st_vals)
        stmt['balance_end_real'] = st_vals['balance_end_real']
        BankStatement.write(stmt)
        return stmt.id
