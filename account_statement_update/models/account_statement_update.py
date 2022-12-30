# Copyright 2022 Ross Golder (https://golder.org)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

"""
Allow bank statements to be (re)imported idempotently.
"""

from calendar import monthrange
import logging

from odoo import models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountStatementImport(models.TransientModel):
    """
    Allow bank statements to be (re)imported idempotently.
    """

    _inherit = 'account.statement.import'

    def _create_bank_statements(self, stmts_vals, result):
        """
        Create new bank statements from imported values, filtering out
        already imported transactions, and returns data used by the
        reconciliation widget.
        """
        statement_line = self.env['account.statement.line']

        # Filter out already imported transactions and create statements
        statement_ids = []
        ignored_statement_lines_import_ids = []
        for st_vals in stmts_vals:
            filtered_st_lines = []
            for line_vals in st_vals['transactions']:
                if 'unique_import_id' not in line_vals or not line_vals['unique_import_id']:
                    imported = bool(statement_line.sudo().search([
                        ('unique_import_id', '=', line_vals['unique_import_id'])
                    ], limit=1))
                    if not imported:
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

        # Prepare import feedback
        notifications = []
        num_ignored = len(ignored_statement_lines_import_ids)
        if num_ignored > 0:
            if num_ignored > 1:
                message = _("%d transactions had already been imported and were ignored.") % num_ignored
            else:
                message = _("1 transaction had already been imported and was ignored.")
            notifications += [{
                'type': 'warning',
                'message': message,
                'details': {
                    'name': _('Already imported items'),
                    'model': 'account.statement.line',
                    'ids': statement_line.search([('unique_import_id', 'in', ignored_statement_lines_import_ids)]).ids
                }
            }]
        return statement_ids, notifications

    def _complete_stmts_vals(self, stmts_vals, journal, _):
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
        statement = self.env['account.statement']
        statement_line = self.env['account.statement.line']

        # Get statement name from date of first line
        lines = st_vals['line_ids']
        if len(lines) == 0:
            raise UserError(_('No lines found in statement'))
        st_name = lines[0][2]['date'][0:7]

        # If no statement for this date, create one and return it
        journal_id = st_vals['journal_id']
        stmt = statement.search([
            ('name', '=', st_name),
            ('journal_id', '=', journal_id)
        ], limit=1)
        if not bool(stmt):
            return statement.create(st_vals).id

        # Otherwise, add transactions to existing statement
        for line_vals in lines:
            trx = line_vals[2]
            trx['statement_id'] = stmt.id
            statement_line.create(trx)

        # Update statement ending value
        stmt.write({
            'balance_end_real': st_vals['balance_end_real']
        })
        return stmt.id
