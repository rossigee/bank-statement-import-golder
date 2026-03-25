# Copyright 2022 Ross Golder (https://golder.org)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestImportButton(TransactionCase):

    def test_import_action_exists(self):
        """OCA import action is reachable (dependency correctly satisfied)."""
        action = self.env.ref(
            'account_statement_import_file.account_statement_import_action',
            raise_if_not_found=False,
        )
        self.assertIsNotNone(
            action,
            "account_statement_import_file.account_statement_import_action not found — "
            "is account_statement_import_file installed?",
        )
        self.assertEqual(action.res_model, 'account.statement.import')
        self.assertEqual(action.target, 'new')

    def test_bank_statement_list_view_exists(self):
        """Base bank statement list view exists for the button to attach to."""
        view = self.env.ref('account.view_bank_statement_tree', raise_if_not_found=False)
        self.assertIsNotNone(view, "account.view_bank_statement_tree not found")
        self.assertEqual(view.model, 'account.bank.statement')
        self.assertEqual(view.type, 'tree')
