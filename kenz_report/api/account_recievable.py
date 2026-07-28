import frappe

from erpnext.accounts.report.accounts_receivable.accounts_receivable import (
    execute
)


@frappe.whitelist()
def print_accounts_receivable(filters):

    filters = frappe._dict(frappe.parse_json(filters))

    result = execute(filters)

    columns = result[0]
    data = result[1]

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
        "account_receivable_print",
        "html"
    )

    html = frappe.render_template(template, context)

    return {
        "html": html,
        "filename": "Accounts Receivable.pdf"
    }