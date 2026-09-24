from odoo import SUPERUSER_ID, api

from odoo.addons.airesa.hooks import set_invoice_report_on_sale_journals


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    set_invoice_report_on_sale_journals(env)
