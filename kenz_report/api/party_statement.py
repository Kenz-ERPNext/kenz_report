import frappe

from kenz_report.kenz_report.report.party_statement.party_statement import execute


@frappe.whitelist()
def print_statement(filters):
    frappe.only_for(["Accounts Manager", "Accounts User", "Sales Manager"])
    filters = frappe.parse_json(filters)
    columns, data = execute(filters)

    blocks = _group_by_customer(data)
    template = _get_print_template()
    parts = []
    for customer, rows in blocks.items():
        ctx = _build_print_context(filters, customer, rows)
        parts.append(frappe.render_template(template, ctx))
    html = '<div style="page-break-after:always;"></div>'.join(parts)
    html = _wrap_html(html)

    return {
        "html": html,
        "filename": f"Party Statement {filters.get('from_date')} to {filters.get('to_date')}.pdf",
    }


def _group_by_customer(rows):
    blocks = {}
    order = []
    for r in rows:
        cust = r.get("customer")
        if not cust:
            continue
        if cust not in blocks:
            blocks[cust] = []
            order.append(cust)
        blocks[cust].append(r)
    return {c: blocks[c] for c in order}


def _build_print_context(filters, customer, rows):
    header = next((r for r in rows if r.get("is_group_header")), {})
    body = [r for r in rows if not r.get("is_group_header")]
    company_name = frappe.get_cached_value("Company", filters.get("company"), "company_name")
    return {
        "company_name": company_name,
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "customer": customer,
        "customer_name": header.get("customer_name") or customer,
        "address": header.get("address_display") or "",
        "mobile": header.get("mobile_no") or "",
        "rows": body,
        "frappe": frappe,
    }


def _get_print_template():
    html = frappe.db.get_value("Print Format", "Party Statement", "html")
    if not html:
        frappe.throw("Print Format 'Party Statement' is not installed")
    return html


def _wrap_html(body):
    return (
        '<html><head><meta charset="utf-8"><title>Party Statement</title></head>'
        f'<body>{body}</body></html>'
    )
