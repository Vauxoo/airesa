from freezegun import freeze_time

from odoo.tests import tagged
from odoo.tools import format_date

from odoo.addons.l10n_mx_edi.tests.common import TestMxEdiCommon

from ..hooks import post_init_hook


@tagged("post_install_l10n", "post_install", "-at_install")
class TestReportInvoice(TestMxEdiCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report = cls.env.ref("airesa.action_report_invoice")
        cls.env.company.write(
            {
                "promissory_note_text": "<p>Promissory note wording under test</p>",
                "invoice_policy_text": "<p>Policy wording under test</p>",
            }
        )

    def _render(self, invoice):
        html, _report_type = self.env["ir.actions.report"]._render_qweb_html(self.report, invoice.ids)
        return html.decode()

    def test_report_available_only_for_customer_documents(self):
        customer_invoice = self.env["account.move"].new({"move_type": "out_invoice"})
        vendor_bill = self.env["account.move"].new({"move_type": "in_invoice"})
        self.assertTrue(customer_invoice._is_action_report_available(self.report))
        self.assertFalse(vendor_bill._is_action_report_available(self.report))
        self.assertIn(self.report, customer_invoice._get_available_invoice_template_pdf_report_ids())

    def test_post_init_hook_sets_sale_journal_default(self):
        sale_journals = self.env["account.journal"].search([("type", "=", "sale")])
        sale_journals.invoice_template_pdf_report_id = False
        post_init_hook(self.env)
        self.assertEqual(sale_journals.invoice_template_pdf_report_id, self.report)

    def test_promissory_note_prints_on_ppd_invoice(self):
        invoice = self._create_invoice()
        self.assertEqual(invoice.l10n_mx_edi_payment_policy, "PPD")
        html = self._render(invoice)
        self.assertIn('name="promissory_note"', html)
        self.assertIn("Promissory note wording under test", html)
        self.assertIn(invoice.amount_total_words, html)
        self.assertIn('name="signature"', html)
        self.assertIn("Policy wording under test", html)

    def test_promissory_note_prints_on_pue_invoice(self):
        invoice = self._create_invoice(invoice_date_due=self.frozen_today.date())
        self.assertEqual(invoice.l10n_mx_edi_payment_policy, "PUE")
        html = self._render(invoice)
        self.assertIn('name="promissory_note"', html)
        self.assertIn('name="signature"', html)

    def test_company_can_disable_promissory_note(self):
        self.env.company.print_promissory_note = False
        invoice = self._create_invoice()
        html = self._render(invoice)
        self.assertNotIn('name="promissory_note"', html)

    def test_new_company_gets_default_texts(self):
        company = self.env["res.company"].create({"name": "Airesa Branch"})
        self.assertIn("pagaré", company.promissory_note_text)
        self.assertIn("__COMPANY__", company.promissory_note_text)
        self.assertIn("__DUE_DATE__", company.promissory_note_text)
        self.assertIn("__AMOUNT__", company.promissory_note_text)
        self.assertIn("AIRESA", company.invoice_policy_text)
        self.assertTrue(company.print_promissory_note)

    def test_empty_policy_hides_block(self):
        self.env.company.invoice_policy_text = False
        invoice = self._create_invoice()
        html = self._render(invoice)
        self.assertNotIn('name="invoice_policy"', html)

    def test_invoice_policy_text_prints_as_is(self):
        self.env.company.invoice_policy_text = "<p>Return it to AIRESA.</p>"
        invoice = self._create_invoice()
        html = self._render(invoice)
        self.assertIn("Return it to AIRESA.", html)

    def test_get_promissory_note_text_method(self):
        self.env.company.promissory_note_text = "<p>__COMPANY__ / __DUE_DATE__ / __AMOUNT__</p>"
        invoice = self._create_invoice(invoice_date_due="2017-02-15")
        text = self.env.company._get_promissory_note_text(invoice)
        self.assertNotIn("__COMPANY__", text)
        self.assertNotIn("__DUE_DATE__", text)
        self.assertNotIn("__AMOUNT__", text)
        self.assertIn(self.env.company.name, text)
        self.assertIn(format_date(self.env, invoice.invoice_date_due), text)

    def test_promissory_note_beneficiary_follows_invoicing_company(self):
        second_company = self.env["res.company"].create({"name": "Airesa Branch"})
        invoice = self._create_invoice()
        text = second_company._get_promissory_note_text(invoice)
        self.assertIn("Airesa Branch", text)
        self.assertNotIn("Aire y Equipos para Refrigeración", text)

    def test_observations_block_shows_narration(self):
        invoice = self._create_invoice()
        invoice.narration = "<p>Handle with care</p>"
        html = self._render(invoice)
        self.assertIn("Observaciones / Notas de entrega", html)
        self.assertIn("Handle with care", html)

    def test_observations_block_hidden_when_empty(self):
        invoice = self._create_invoice()
        invoice.narration = False
        html = self._render(invoice)
        self.assertNotIn("Observaciones / Notas de entrega", html)

    def test_product_barcode_shown_on_invoice_line(self):
        invoice = self._create_invoice()
        invoice.invoice_line_ids[0].product_id.barcode = "7501234567890"
        html = self._render(invoice)
        self.assertIn("7501234567890", html)

    @freeze_time("2017-01-01")
    def test_stamped_invoice_keeps_cfdi_block(self):
        invoice = self._create_invoice()
        with self.with_mocked_pac_sign_success():
            invoice._l10n_mx_edi_cfdi_invoice_try_send()
        self.assertEqual(invoice._get_name_invoice_report(), "l10n_mx_edi.report_invoice_document")
        html = self._render(invoice)
        self.assertIn('id="complement"', html)
        self.assertIn(invoice.l10n_mx_edi_cfdi_uuid, html)
        self.assertIn('name="promissory_note"', html)
        self.assertIn("Código SAT", html)
        self.assertNotIn("Payment Communication", html)
        self.assertIn(format_date(self.env, invoice.invoice_date_due), html)
        self.assertIn(invoice.amount_total_words, html)
