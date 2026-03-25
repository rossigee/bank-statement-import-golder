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
        Create new bank statements from imported values,
        filtering out already imported transactions,
        and return data used by the reconciliation widget.

        The statement record is always created (or found) even when every
        transaction line is a duplicate, so that the statement header exists
        and existing lines can be re-associated with it.
        """
        absl_obj = self.env["account.bank.statement.line"]

        for st_vals in stmts_vals:
            existing_st_lines = {}
            st_lines_to_create = []

            for lvals in st_vals["transactions"]:
                existing_line = False
                if lvals.get("unique_import_id"):
                    existing_line = absl_obj.sudo().search(
                        [("unique_import_id", "=", lvals["unique_import_id"])],
                        limit=1,
                    )
                    # we can only have 1 anyhow because of the unicity SQL constraint
                if existing_line:
                    existing_st_lines[existing_line.id] = existing_line
                else:
                    st_lines_to_create.append(lvals)

            # Resequence new lines
            if st_lines_to_create and not st_lines_to_create[0].get("sequence"):
                for seq, vals in enumerate(st_lines_to_create, start=1):
                    vals["sequence"] = seq

            # Remove values that won't be used to create the statement record
            st_vals.pop("transactions", None)

            # Always find or create the statement, even when all lines are duplicates
            statement_id = self._find_or_create_statement_ids(st_vals, st_lines_to_create)
            result["statement_ids"].append(statement_id)

            # Re-associate any existing duplicate lines with this statement
            for line_id, line in existing_st_lines.items():
                if line.statement_id.id != statement_id:
                    line.write({'statement_id': statement_id})

            # Prepare import feedback
            num_ignored = len(existing_st_lines)
            if num_ignored > 0:
                if num_ignored == 1:
                    message = _("1 transaction had already been imported and was ignored.")
                else:
                    message = _(
                        "%d transactions had already been imported and were ignored."
                    ) % num_ignored
                result["notifications"].append(message)

    # Override
    def _complete_stmts_vals(self, stmts_vals, journal, account_number):
        speeddict = journal._statement_line_import_speeddict()
        for st_vals in stmts_vals:
            st_vals['journal_id'] = journal.id

            # Set statement name based on first transaction date year and month
            transactions = st_vals['transactions']
            if len(transactions) == 0:
                raise UserError(_('No transactions found in statement'))
            st_vals['name'] = transactions[0]['date'][0:7]

            # As per superclass
            for lvals in transactions:
                lvals["journal_id"] = journal.id
                journal._statement_line_import_update_unique_import_id(
                    lvals, account_number
                )
                journal._statement_line_import_update_hook(lvals, speeddict)
                if not lvals.get("payment_ref"):
                    raise UserError(_("Missing payment_ref on a transaction."))

            # Set statement date based on last day of month
            year = int(st_vals['name'][0:4])
            month = int(st_vals['name'][5:7])
            st_vals['date'] = st_vals['name'] + "-" + str(monthrange(year, month)[1])

        return stmts_vals

    # Custom
    def _find_or_create_statement_ids(self, st_vals, st_lines):
        abs_obj = self.env["account.bank.statement"]
        absl_obj = self.env["account.bank.statement.line"]

        # If no statement for this date, create one and return it
        stmt = abs_obj.search([
            ('name', '=', st_vals['name']),
            ('journal_id', '=', st_vals['journal_id'])
        ], limit=1)
        if not stmt:
            stmt = abs_obj.create(st_vals)

        # Add given transactions to statement
        for line in st_lines:
            line['statement_id'] = stmt.id
            absl_obj.create(line)

        # Update statement ending value (balance_end_real may not be set by all parsers)
        stmt.write({
            'balance_end_real': st_vals.get('balance_end_real', 0.0)
        })
        return stmt.id
