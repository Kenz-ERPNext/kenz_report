
import frappe
from erpnext.accounts.report.sales_register.sales_register import execute


@frappe.whitelist()
def print_sales_register(filters):

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
        "sales_register_print",   
        "html"
    )

    if not template:
        frappe.throw("Print Format 'sales_register_print' not found")

    html = frappe.render_template(template, context)

    return {
        "html": html,
        "filename": "Sales Register.pdf"
    }




