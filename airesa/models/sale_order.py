from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _mail_post_access = "read"
