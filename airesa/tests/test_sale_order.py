from odoo import Command
from odoo.tests import tagged

from odoo.addons.sale.tests.common import TestSaleCommon


@tagged("test_sale_order_airesa", "post_install", "-at_install")
class TestSaleOrder(TestSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.payment_user = cls.company_data["default_user_salesman"]
        cls.payment_user.group_ids |= cls.env.ref("account.group_account_invoice") | cls.env.ref(
            "sales_team.group_sale_salesman_all_leads"
        )
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner_a.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.company_data["product_order_no"].id,
                            "product_uom_qty": 1,
                            "tax_ids": False,
                        }
                    )
                ],
            }
        )
        cls.sale_order.action_confirm()
        cls.invoice = cls.sale_order._create_invoices()
        cls.invoice.action_post()
        cls.env["generic.security.model.restriction"].create(
            {
                "name": "Test block sale order writes",
                "model_id": cls.env["ir.model"]._get_id("sale.order"),
                "user_ids": [(4, cls.payment_user.id)],
                "domain_simple": "[(0, '=', 1)]",
                "apply_mode_read": False,
                "apply_mode_write": True,
                "apply_mode_create": False,
                "apply_mode_unlink": False,
            }
        )

    def _register_payment(self):
        return (
            self.env["account.payment.register"]
            .with_user(self.payment_user)
            .with_context(
                active_model="account.move",
                active_ids=self.invoice.ids,
            )
            .create(
                {
                    "journal_id": self.company_data["default_journal_bank"].id,
                }
            )
            .action_create_payments()
        )

    def test_paid_invoice_log_on_read_only_sale_order(self):
        sale_order = self.sale_order.with_user(self.payment_user)
        self.assertTrue(sale_order.has_access("read"))
        self.assertFalse(sale_order.has_access("write"))
        previous_message_ids = sale_order.sudo().message_ids.ids

        self._register_payment()

        self.assertTrue(self.invoice.currency_id.is_zero(self.invoice.amount_residual))
        paid_message = (
            self.env["mail.message"]
            .sudo()
            .search(
                [
                    ("model", "=", "sale.order"),
                    ("res_id", "=", self.sale_order.id),
                    ("id", "not in", previous_message_ids),
                    ("body", "ilike", self.invoice.name),
                ]
            )
        )
        self.assertTrue(paid_message)
