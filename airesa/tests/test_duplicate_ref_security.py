from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestDuplicateRefSecurity(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.team_a = cls.env["crm.team"].sudo().create({"name": "Team A"})
        cls.team_b = cls.env["crm.team"].sudo().create({"name": "Team B"})

        cls.restricted_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Restricted User",
                    "login": "restricted_user_test",
                    "email": "restricted@test.com",
                    "company_id": cls.env.company.id,
                    "company_ids": [Command.link(cls.env.company.id)],
                    "group_ids": [
                        Command.link(cls.env.ref("account.group_account_invoice").id),
                        Command.link(cls.env.ref("sales_team.group_sale_salesman").id),
                        Command.link(cls.env.ref("base.group_user").id),
                    ],
                }
            )
        )

        cls.env["crm.team.member"].sudo().create(
            {
                "user_id": cls.restricted_user.id,
                "crm_team_id": cls.team_a.id,
            }
        )

        account_move_model = cls.env["ir.model"].search([("model", "=", "account.move")], limit=1)
        cls.restriction = (
            cls.env["generic.security.model.restriction"]
            .sudo()
            .create(
                {
                    "name": "Invoice team restriction",
                    "model_id": account_move_model.id,
                    "user_ids": [Command.link(cls.restricted_user.id)],
                    "domain_simple": "[('team_id', '=', %d)]" % cls.team_a.id,
                    "domain_type": "simple",
                    "apply_mode_read": True,
                    "apply_mode_write": True,
                    "apply_mode_create": True,
                    "apply_mode_unlink": True,
                }
            )
        )

        common_date = fields.Date.from_string("2026-01-15")

        move_sudo = cls.env["account.move"].sudo()
        cls.invoice_a = move_sudo.create(
            [
                {
                    "move_type": "out_invoice",
                    "partner_id": cls.partner_a.id,
                    "invoice_date": common_date,
                    "ref": "DUP-REF-001",
                    "team_id": cls.team_a.id,
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "name": "test line",
                                "price_unit": 500.0,
                                "quantity": 1,
                            },
                        ),
                    ],
                }
            ]
        )
        cls.invoice_a.action_post()

        cls.invoice_b = move_sudo.create(
            [
                {
                    "move_type": "out_invoice",
                    "partner_id": cls.partner_a.id,
                    "invoice_date": common_date,
                    "ref": "DUP-REF-001",
                    "team_id": cls.team_b.id,
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "name": "test line",
                                "price_unit": 500.0,
                                "quantity": 1,
                            },
                        ),
                    ],
                }
            ]
        )
        cls.invoice_b.action_post()

        cls.env.flush_all()

    def test_01_list_view_only_own_team(self):
        """Tree view must show only invoices from the user's own team."""
        move_sudo = self.env["account.move"].sudo()
        invoice_c = move_sudo.create(
            [
                {
                    "move_type": "out_invoice",
                    "partner_id": self.partner_a.id,
                    "invoice_date": fields.Date.from_string("2026-06-01"),
                    "ref": "TEAM-C-ONLY",
                    "team_id": self.team_b.id,
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "name": "test line",
                                "price_unit": 300.0,
                                "quantity": 1,
                            },
                        )
                    ],
                }
            ]
        )
        invoice_c.action_post()
        self.env.flush_all()

        result = (
            self.env["account.move"]
            .with_user(self.restricted_user)
            .search_read(
                domain=[("id", "in", (self.invoice_a | self.invoice_b | invoice_c).ids)],
                fields=["id", "ref", "team_id"],
            )
        )
        result_ids = {r["id"] for r in result}
        self.assertIn(self.invoice_a.id, result_ids)
        self.assertNotIn(self.invoice_b.id, result_ids)
        self.assertNotIn(invoice_c.id, result_ids)

    def test_02_search_count_only_own_team(self):
        """search_count must exclude cross-team invoices."""
        count = self.env["account.move"].with_user(self.restricted_user).search_count([("ref", "=", "DUP-REF-001")])
        self.assertEqual(count, 1)

    def test_03_duplicated_ref_excludes_cross_team(self):
        """duplicated_ref_ids must not surface a duplicate from another team:
        the unreadable move is filtered out instead of granting access."""
        invoice_a = self.invoice_a.with_user(self.restricted_user)
        self.assertNotIn(self.invoice_b, invoice_a.duplicated_ref_ids)
        self.assertFalse(invoice_a.duplicated_ref_ids)

    def test_04_same_team_duplicate_still_detected(self):
        """Filtering only drops unreadable duplicates: a duplicate on the user's
        own team must still be reported."""
        invoice_a2 = (
            self.env["account.move"]
            .sudo()
            .create(
                [
                    {
                        "move_type": "out_invoice",
                        "partner_id": self.partner_a.id,
                        "invoice_date": fields.Date.from_string("2026-01-15"),
                        "ref": "DUP-REF-001",
                        "team_id": self.team_a.id,
                        "invoice_line_ids": [
                            Command.create(
                                {
                                    "name": "test line",
                                    "price_unit": 500.0,
                                    "quantity": 1,
                                },
                            )
                        ],
                    }
                ]
            )
        )
        invoice_a2.action_post()
        self.env.flush_all()

        duplicated = self.invoice_a.with_user(self.restricted_user).duplicated_ref_ids
        self.assertIn(invoice_a2, duplicated)
        self.assertNotIn(self.invoice_b, duplicated)

    def test_05_privileged_user_still_sees_cross_team_duplicate(self):
        """The core behaviour is untouched for users with full access: the
        cross-team duplicate is still detected under sudo."""
        duplicated = self.invoice_a.sudo().duplicated_ref_ids
        self.assertIn(self.invoice_b, duplicated)

    def test_06_web_read_excludes_cross_team_duplicate(self):
        """web_read (form view load) must not raise and must not leak the
        cross-team duplicate in duplicated_ref_ids."""
        invoice_a = self.invoice_a.with_user(self.restricted_user)
        spec = {
            "duplicated_ref_ids": {},
            "is_draft_duplicated_ref_ids": {},
            "is_exact_move_duplicate": {},
            "state": {},
        }
        result = invoice_a.web_read(spec)
        self.assertEqual(len(result), 1)
        self.assertNotIn(self.invoice_b.id, result[0].get("duplicated_ref_ids", []))

    def test_07_search_cross_team_id_blocked(self):
        """Direct access via id_in search for cross-team invoice must be blocked."""
        domain = [("id", "in", [self.invoice_b.id])]
        result = self.env["account.move"].with_user(self.restricted_user).search(domain)
        self.assertNotIn(self.invoice_b, result)

    def test_08_web_read_cross_team_directly_blocked(self):
        """web_read on cross-team invoice directly (not via duplicate link) must
        raise AccessError: llama a read() que pasa por _check_access."""
        with self.assertRaises(AccessError):
            self.invoice_b.with_user(self.restricted_user).web_read({"name": {}})

    def test_09_state_field_blocked_for_fresh_cross_team_record(self):
        """Accessing a stored field (state) on a fresh cross-team record not
        previously cached must raise AccessError."""
        new_b = (
            self.env["account.move"]
            .sudo()
            .create(
                [
                    {
                        "move_type": "out_invoice",
                        "partner_id": self.partner_a.id,
                        "invoice_date": fields.Date.from_string("2026-07-01"),
                        "ref": "FRESH-B-001",
                        "team_id": self.team_b.id,
                        "invoice_line_ids": [
                            Command.create(
                                {
                                    "name": "test line",
                                    "price_unit": 100.0,
                                    "quantity": 1,
                                },
                            )
                        ],
                    }
                ]
            )
        )
        new_b.action_post()
        self.env.flush_all()

        with self.assertRaises(AccessError):
            new_b.with_user(self.restricted_user).read(["state"])
