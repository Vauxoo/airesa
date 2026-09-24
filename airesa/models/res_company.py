from odoo import fields, models
from odoo.tools import format_date, formatLang

PROMISSORY_NOTE_TEXT = """<p>
Por el presente pagaré reconozco deber y me obligo a pagar en esta ciudad o en la que se me
requiera de pago a __COMPANY__ el día __DUE_DATE__ la cantidad
de __AMOUNT__ valor recibido en mercancía y/o servicios a mi entera satisfacción, monto pagadero al
tipo de cambio del D.O.F. del día de la operación. Este pagaré es mercantil y está regido por la
Ley General de Operaciones y Títulos de Crédito artículos 170 a 174 y artículos correlativos. De
no verificarse el pago en tiempo, abonaré el rédito del 5% por ciento mensual por todo el tiempo
que esté insoluto, sin perjuicio al cobro más los gastos que por ello se originen.
</p>"""

INVOICE_POLICY_TEXT = """<p>
Si usted desea hacer válida una garantía y/o realizar la devolución de un producto adquirido
porque presenta alguna falla, lo invitamos a contactar a su vendedor. Para devoluciones usted
cuenta con 5 días naturales y posterior a ello aplica cargo del 20% sobre valor factura a partir
de la fecha de facturación; la devolución del material a AIRESA, en la sucursal que expidió
la factura, correrá por cuenta del cliente; el producto está sujeto a revisión por parte del
fabricante. Para garantía será
necesario presentar su factura y cumplir con las políticas del fabricante.
</p>
<p>
<strong>NO APLICA GARANTÍA O DEVOLUCIÓN EN:</strong> aspas, partes eléctricas, instrumentos de
precisión, compresores fraccionarios, mercancías que presenten fallas por accidente y/o
quemaduras en productos de fabricación especial, sobre pedido, en promoción o de remate.
</p>"""


class ResCompany(models.Model):
    _inherit = "res.company"

    print_promissory_note = fields.Boolean(
        string="Print Promissory Note on Customer Invoices",
        default=True,
        help="Print the promissory note block on every customer invoice.",
    )
    promissory_note_text = fields.Html(
        default=PROMISSORY_NOTE_TEXT,
        help="Legal wording of the promissory note printed on customer invoices. Use the "
        "__COMPANY__, __DUE_DATE__ and __AMOUNT__ placeholders to insert the issuing company's "
        "name, the invoice's own due date and its amount in number and words.",
    )
    invoice_policy_text = fields.Html(
        default=INVOICE_POLICY_TEXT,
        help="Return and warranty policy printed at the end of every customer invoice. Leave "
        "empty to hide the block.",
    )

    def _get_promissory_note_text(self, invoice):
        self.ensure_one()
        text = self.promissory_note_text
        if not text:
            return text
        due_date_str = format_date(self.env, invoice.invoice_date_due) if invoice.invoice_date_due else ""
        amount_str = formatLang(self.env, invoice.amount_total, currency_obj=invoice.currency_id)
        amount_full = f"{amount_str} {invoice.amount_total_words}"
        return (
            text.replace("__COMPANY__", self.name)
            .replace("__DUE_DATE__", due_date_str)
            .replace("__AMOUNT__", amount_full)
        )
