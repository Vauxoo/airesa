def set_invoice_report_on_sale_journals(env):
    report = env.ref("airesa.action_report_invoice")
    sale_journals = env["account.journal"].with_context(active_test=False).search([("type", "=", "sale")])
    sale_journals.write({"invoice_template_pdf_report_id": report.id})


def post_init_hook(env):
    set_invoice_report_on_sale_journals(env)
