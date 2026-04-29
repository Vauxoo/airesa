{
    "name": "Airesa",
    "summary": """
    Instance creator for airesa. This is the app.
    """,
    "author": "Vauxoo",
    "website": "https://www.vauxoo.com",
    "license": "OPL-1",
    "category": "Installer",
    "version": "19.0.1.0.5",
    "depends": [
        "accountant",
        "base_partner_sequence",
        "credit_management",
        "crm",
        "hr",
        "l10n_mx_avoid_reversal_entry",
        "l10n_mx_edi_document",
        "l10n_mx_edi_payment_split",
        "point_of_sale",
        "purchase",
        "sale_management",
        "stock_manual_transfer",
        "stock_no_negative",
    ],
    "data": [
        "data/res_company_data.xml",
        "data/res_partner_data.xml",
    ],
    "application": True,
}
