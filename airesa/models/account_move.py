from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _invoice_paid_hook(self):
        """Allow the automatic paid-invoice log on read-only sale orders."""
        self = self.with_context(airesa_invoice_paid_hook=True)
        return super()._invoice_paid_hook()
