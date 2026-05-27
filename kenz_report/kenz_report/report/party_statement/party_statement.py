import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = _get_columns(filters)
    return columns, []


def _get_columns(filters):
    currency = frappe.get_cached_value("Company", filters.company, "default_currency") \
        if filters.get("company") else None
    return [
        {"label": _("TRX Date"), "fieldname": "posting_date",
         "fieldtype": "Date", "width": 100},
        {"label": _("TRX No / Inv No"), "fieldname": "voucher_no",
         "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 140},
        {"label": _("Tran-Type"), "fieldname": "tran_type",
         "fieldtype": "Data", "width": 110},
        {"label": _("TRX Amount"), "fieldname": "trx_amount",
         "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": _("Paid Amount"), "fieldname": "paid_amount",
         "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": _("Debit"), "fieldname": "debit",
         "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": _("Credit"), "fieldname": "credit",
         "fieldtype": "Currency", "options": "currency", "width": 120},
        {"label": _("Balance"), "fieldname": "balance",
         "fieldtype": "Currency", "options": "currency", "width": 130},
    ]
