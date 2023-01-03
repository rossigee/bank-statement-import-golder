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
        and return data used by the reconciliation widget
        """
        abs_obj = self.env["account.bank.statement"]
        absl_obj = self.env["account.bank.statement.line"]

        # Filter out already imported transactions and create statements.
        statement_ids = []
        existing_st_lines = {}
        for st_vals in stmts_vals:
            st_lines_to_create = []
            for lvals in st_vals["transactions"]:
                existing_line = False
                if lvals.get("unique_import_id"):
                    existing_line = absl_obj.sudo().search(
                        [
                            ("unique_import_id", "=", lvals["unique_import_id"]),
                        ],
                        limit=1,
                    )
                    # we can only have 1 anyhow because we have a unicity SQL constraint
                if existing_line:
                    existing_st_lines[existing_line.id] = existing_line
                    # Statement balance will be unaffected?
                    #if "balance_start" in st_vals:
                    #    st_vals["balance_start"] += float(lvals["amount"])
                else:
                    st_lines_to_create.append(lvals)

            if len(st_lines_to_create) > 0:
                if not st_lines_to_create[0].get("sequence"):
                    for seq, vals in enumerate(st_lines_to_create, start=1):
                        vals["sequence"] = seq

                # Remove values that won't be used to create records
                st_vals.pop("transactions", None)

                # NOTE: This is the part where we need to diverge from base/upstream...

                # Create (or update) the statement with lines
                statement_id = self._find_or_create_statement_ids(st_vals, st_lines_to_create)
                statement_ids.append(statement_id)
        
        if not statement_ids:
            return False
        result["statement_ids"].extend(statement_ids)

        # Prepare import feedback
        num_ignored = len(existing_st_lines)
        if num_ignored > 0:
            result["notifications"].append(
                {
                    "type": "warning",
                    "message": _(
                        "%d transactions had already been imported and were ignored."
                    )
                    % num_ignored
                    if num_ignored > 1
                    else _("1 transaction had already been imported and was ignored."),
                    "details": {
                        "name": _("Already imported items"),
                        "model": "account.bank.statement.line",
                        "ids": list([x.id for x in existing_st_lines]),
                    },
                }
            )

    # Override
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

    # Custom
    def _find_or_create_statement_ids(self, st_vals, st_lines):
        abs_obj = self.env["account.bank.statement"]
        absl_obj = self.env["account.bank.statement.line"]

        # If no statement for this date, create one and return it
        stmt = abs_obj.search([
            ('name', '=', st_vals['name']),
            ('journal_id', '=', st_vals['journal_id'])
        ], limit=1)
        if not bool(stmt):
            return abs_obj.create(st_vals).id

        # Otherwise, add transactions to existing statement
        for line in st_lines:
            line['statement_id'] = stmt.id
            absl_obj.create(line)

        # Update statement ending value
        stmt.write({
            'balance_end_real': st_vals['balance_end_real']
        })
        return stmt.id
