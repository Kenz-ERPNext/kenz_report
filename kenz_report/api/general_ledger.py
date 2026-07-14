import frappe
from erpnext.accounts.report.general_ledger.general_ledger import execute

@frappe.whitelist()
def print_general_ledger(filters):

    filters = frappe._dict(frappe.parse_json(filters))

    columns, data = execute(filters)

    company_name = frappe.get_cached_value(
        "Company",
        filters.company,
        "company_name"
    )

    context = {
        "company_name": company_name,
        "columns": columns,
        "rows": data,
        "filters": filters,
        "frappe": frappe,
    }

    template = frappe.db.get_value(
        "Print Format",
        "general_ledger_print",
        "html"
    )

    if not template:
        frappe.throw("Print Format 'general_ledger_print' not found")

    html = frappe.render_template(template, context)

    return {
        "html": html,
        "filename": "General Ledger.pdf"
    }