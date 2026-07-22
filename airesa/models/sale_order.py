from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def message_post(self, **kwargs):
        """Post the invoice-paid log without granting sale order write access."""
        if self.env.context.get("airesa_invoice_paid_hook") and not self.has_access("write"):
            self = self.sudo()
        return super().message_post(**kwargs)
