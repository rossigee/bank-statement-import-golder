# Copyright 2022 Ross Golder (https://golder.org)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


def _make_stmts_vals(journal_id, name, lines):
    """Build a minimal stmts_vals list as the import pipeline would produce."""
    return [{
        'journal_id': journal_id,
        'name': name,
        'date': name + '-28',
        'balance_start': 0.0,
        'balance_end_real': 100.0,
        'transactions': lines,
    }]


def _make_line(unique_id, amount=10.0, payment_ref='Test'):
    return {
        'unique_import_id': unique_id,
        'date': '2024-01-15',
        'amount': amount,
        'payment_ref': payment_ref,
        'name': payment_ref,
    }


class TestCreateBankStatements(TransactionCase):

    def setUp(self):
        super().setUp()
        self.journal = self.env['account.journal'].create({
            'name': 'Test Update Journal',
            'type': 'bank',
            'code': 'TUPD',
        })
        self.wizard = self.env['account.statement.import'].sudo()

    def _call(self, stmts_vals):
        result = {'statement_ids': [], 'notifications': []}
        self.wizard._create_bank_statements(stmts_vals, result)
        return result

    # ------------------------------------------------------------------
    # Core bug: all lines already exist, statement does NOT exist yet
    # ------------------------------------------------------------------

    def test_all_lines_duplicate_no_existing_statement_creates_statement(self):
        """Statement record is created even when every line is a duplicate."""
        # Pre-create a line with a known unique_import_id in another statement
        other_stmt = self.env['account.bank.statement'].create({
            'name': '2024-00',
            'journal_id': self.journal.id,
        })
        existing_line = self.env['account.bank.statement.line'].create({
            'statement_id': other_stmt.id,
            'name': 'Pre-existing',
            'amount': 10.0,
            'date': '2024-01-15',
            'unique_import_id': 'uid-001',
        })

        stmts_vals = _make_stmts_vals(
            self.journal.id, '2024-01',
            [_make_line('uid-001')],
        )
        result = self._call(stmts_vals)

        self.assertTrue(result['statement_ids'], "Statement ID must be returned")
        stmt = self.env['account.bank.statement'].browse(result['statement_ids'][0])
        self.assertTrue(stmt.exists(), "Statement record must be created")
        self.assertEqual(stmt.name, '2024-01')

    def test_all_lines_duplicate_existing_line_reassociated(self):
        """When all lines are duplicates, existing lines are moved to the new statement."""
        other_stmt = self.env['account.bank.statement'].create({
            'name': '2024-00',
            'journal_id': self.journal.id,
        })
        existing_line = self.env['account.bank.statement.line'].create({
            'statement_id': other_stmt.id,
            'name': 'Pre-existing',
            'amount': 10.0,
            'date': '2024-01-15',
            'unique_import_id': 'uid-002',
        })

        stmts_vals = _make_stmts_vals(
            self.journal.id, '2024-01',
            [_make_line('uid-002')],
        )
        result = self._call(stmts_vals)

        existing_line.refresh()
        new_stmt_id = result['statement_ids'][0]
        self.assertEqual(
            existing_line.statement_id.id, new_stmt_id,
            "Duplicate line must be re-associated with the new statement",
        )

    def test_all_lines_duplicate_notification_shown(self):
        """A user-facing notification is produced when duplicate lines are skipped."""
        stmt = self.env['account.bank.statement'].create({
            'name': '2024-00', 'journal_id': self.journal.id,
        })
        self.env['account.bank.statement.line'].create({
            'statement_id': stmt.id, 'name': 'L1', 'amount': 5.0,
            'date': '2024-01-15', 'unique_import_id': 'uid-010',
        })
        self.env['account.bank.statement.line'].create({
            'statement_id': stmt.id, 'name': 'L2', 'amount': 5.0,
            'date': '2024-01-16', 'unique_import_id': 'uid-011',
        })

        stmts_vals = _make_stmts_vals(
            self.journal.id, '2024-02',
            [_make_line('uid-010'), _make_line('uid-011')],
        )
        result = self._call(stmts_vals)

        self.assertTrue(result['notifications'], "Notifications must be produced")
        self.assertIn('2', result['notifications'][0])

    # ------------------------------------------------------------------
    # Normal cases
    # ------------------------------------------------------------------

    def test_no_duplicates_creates_statement_with_all_lines(self):
        """Normal import: statement is created with all new lines."""
        stmts_vals = _make_stmts_vals(
            self.journal.id, '2024-03',
            [_make_line('uid-100', amount=50.0), _make_line('uid-101', amount=-20.0)],
        )
        result = self._call(stmts_vals)

        self.assertTrue(result['statement_ids'])
        stmt = self.env['account.bank.statement'].browse(result['statement_ids'][0])
        self.assertEqual(len(stmt.line_ids), 2)

    def test_partial_duplicates_only_new_lines_added(self):
        """When some lines are new and some are duplicates, only new ones are inserted."""
        other_stmt = self.env['account.bank.statement'].create({
            'name': '2024-00', 'journal_id': self.journal.id,
        })
        self.env['account.bank.statement.line'].create({
            'statement_id': other_stmt.id, 'name': 'Old', 'amount': 10.0,
            'date': '2024-01-15', 'unique_import_id': 'uid-200',
        })

        stmts_vals = _make_stmts_vals(
            self.journal.id, '2024-04',
            [_make_line('uid-200'), _make_line('uid-201', amount=99.0)],
        )
        result = self._call(stmts_vals)

        stmt = self.env['account.bank.statement'].browse(result['statement_ids'][0])
        new_lines = stmt.line_ids.filtered(lambda l: l.unique_import_id == 'uid-201')
        self.assertEqual(len(new_lines), 1, "Only the non-duplicate line should be created")

    def test_statement_already_exists_returns_existing(self):
        """If a statement with the same name/journal already exists, it is reused."""
        existing_stmt = self.env['account.bank.statement'].create({
            'name': '2024-05', 'journal_id': self.journal.id,
        })

        stmts_vals = _make_stmts_vals(
            self.journal.id, '2024-05',
            [_make_line('uid-300', amount=10.0)],
        )
        result = self._call(stmts_vals)

        self.assertEqual(result['statement_ids'][0], existing_stmt.id,
                         "Existing statement must be reused, not duplicated")

    def test_balance_end_real_missing_does_not_crash(self):
        """Missing balance_end_real in st_vals does not raise KeyError."""
        stmts_vals = _make_stmts_vals(
            self.journal.id, '2024-06',
            [_make_line('uid-400')],
        )
        # Remove balance_end_real to simulate a parser that omits it
        del stmts_vals[0]['balance_end_real']

        try:
            result = self._call(stmts_vals)
        except KeyError as e:
            self.fail(f"KeyError raised for missing balance_end_real: {e}")

        self.assertTrue(result['statement_ids'])
