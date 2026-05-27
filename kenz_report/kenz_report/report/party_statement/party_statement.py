import frappe
from frappe import _
from frappe.utils import flt


def _validate_filters(filters):
    if not filters.get("company"):
        frappe.throw(_("Company is required"))
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("From Date and To Date are required"))
    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date must be on or before To Date"))


def execute(filters=None):
    filters = frappe._dict(filters or {})
    _validate_filters(filters)
    columns = _get_columns(filters)
    data = _get_data(filters)
    return columns, data


def _get_receivable_account(company):
    account = frappe.get_cached_value("Company", company, "default_receivable_account")
    if not account:
        frappe.throw(_("Set Default Receivable Account on Company {0}").format(company))
    return account


def _get_journal_entry_rows(filters):
    customer_clause = ""
    if filters.get("customer"):
        customer_clause = " AND jea.party = %(customer)s "
    sql = f"""
        SELECT jea.party AS customer,
               c.customer_name AS customer_name,
               je.posting_date AS posting_date,
               'Journal Entry' AS voucher_type,
               je.name AS voucher_no,
               'JV' AS tran_type,
               (jea.debit_in_account_currency + jea.credit_in_account_currency) AS trx_amount,
               0 AS paid_amount,
               jea.debit_in_account_currency AS debit,
               jea.credit_in_account_currency AS credit
        FROM `tabJournal Entry Account` jea
        JOIN `tabJournal Entry` je ON je.name = jea.parent
        LEFT JOIN `tabCustomer` c ON c.name = jea.party
        WHERE je.docstatus = 1
          AND je.company = %(company)s
          AND jea.account = %(receivable_account)s
          AND jea.party_type = 'Customer'
          AND je.posting_date BETWEEN %(from_date)s AND %(to_date)s
          {customer_clause}
        ORDER BY je.posting_date, je.name
    """
    params = dict(filters)
    params["receivable_account"] = _get_receivable_account(filters.company)
    return frappe.db.sql(sql, params, as_dict=True)


def _get_payment_entry_rows(filters):
    customer_clause = ""
    if filters.get("customer"):
        customer_clause = " AND pe.party = %(customer)s "
    sql = f"""
        SELECT pe.party AS customer,
               c.customer_name AS customer_name,
               pe.posting_date AS posting_date,
               'Payment Entry' AS voucher_type,
               pe.name AS voucher_no,
               'RECEIPT' AS tran_type,
               pe.paid_amount AS trx_amount,
               0 AS paid_amount,
               0 AS debit,
               pe.paid_amount AS credit
        FROM `tabPayment Entry` pe
        LEFT JOIN `tabCustomer` c ON c.name = pe.party
        WHERE pe.docstatus = 1
          AND pe.company = %(company)s
          AND pe.party_type = 'Customer'
          AND pe.payment_type = 'Receive'
          AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s
          {customer_clause}
        ORDER BY pe.posting_date, pe.name
    """
    return frappe.db.sql(sql, filters, as_dict=True)


def _get_opening_balance(filters, customer):
    sql = """
        SELECT IFNULL(SUM(debit - credit), 0) AS opening
        FROM `tabGL Entry`
        WHERE company = %(company)s
          AND account = %(receivable_account)s
          AND party_type = 'Customer'
          AND party = %(customer)s
          AND posting_date < %(from_date)s
          AND is_cancelled = 0
    """
    result = frappe.db.sql(sql, {
        "company": filters.company,
        "receivable_account": _get_receivable_account(filters.company),
        "customer": customer,
        "from_date": filters.from_date,
    }, as_dict=True)
    return flt(result[0]["opening"]) if result else 0.0


def _customers_in_data(filters, body_rows):
    """Return the set of customers in the data, respecting the customer filter."""
    if filters.get("customer"):
        return [filters.customer]
    return sorted({r["customer"] for r in body_rows if r.get("customer")})


def _opening_row(customer, customer_name, opening):
    return {
        "customer": customer,
        "customer_name": customer_name,
        "posting_date": None,
        "voucher_type": None,
        "voucher_no": "",
        "tran_type": "OPENING BALANCE",
        "trx_amount": 0.0,
        "paid_amount": 0.0,
        "debit": 0.0,
        "credit": 0.0,
        "balance": opening,
    }


def _get_data(filters):
    body = []
    body.extend(_get_sales_invoice_rows(filters, is_return=0))
    body.extend(_get_sales_invoice_rows(filters, is_return=1))
    body.extend(_get_payment_entry_rows(filters))
    body.extend(_get_journal_entry_rows(filters))
    body = [_normalize_row(r) for r in body]

    customers = _customers_in_data(filters, body)
    final = []
    body_by_customer = {c: [] for c in customers}
    for row in body:
        if row["customer"] in body_by_customer:
            body_by_customer[row["customer"]].append(row)

    for customer in customers:
        customer_name = frappe.db.get_value("Customer", customer, "customer_name") or customer
        opening = _get_opening_balance(filters, customer)
        final.append(_opening_row(customer, customer_name, opening))
        rows = sorted(body_by_customer.get(customer, []),
                      key=lambda r: (r["posting_date"], r["voucher_no"]))
        final.extend(rows)

    return final


def _customer_filter_clause(filters, table_alias):
    if filters.get("customer"):
        return f" AND {table_alias}.customer = %(customer)s "
    return ""


def _payment_amount_subquery():
    return (
        "(SELECT IFNULL(SUM(per.allocated_amount), 0) "
        " FROM `tabPayment Entry Reference` per "
        " JOIN `tabPayment Entry` pe ON pe.name = per.parent "
        " WHERE per.reference_doctype = 'Sales Invoice' "
        "   AND per.reference_name = si.name "
        "   AND pe.docstatus = 1)"
    )


def _get_sales_invoice_rows(filters, is_return):
    tran_type = "SALESRETURN" if is_return else "SALES"
    customer_clause = _customer_filter_clause(filters, "si")
    if is_return:
        amount_expr = "ABS(si.grand_total)"
        debit_expr = "0"
        credit_expr = amount_expr
        paid_expr = "0"
    else:
        amount_expr = "si.grand_total"
        debit_expr = amount_expr
        credit_expr = "0"
        paid_expr = _payment_amount_subquery()
    sql = f"""
        SELECT si.customer AS customer,
               si.customer_name AS customer_name,
               si.posting_date AS posting_date,
               'Sales Invoice' AS voucher_type,
               si.name AS voucher_no,
               %(tran_type)s AS tran_type,
               {amount_expr} AS trx_amount,
               {paid_expr} AS paid_amount,
               {debit_expr} AS debit,
               {credit_expr} AS credit
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
          AND si.company = %(company)s
          AND si.is_return = %(is_return)s
          AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
          {customer_clause}
        ORDER BY si.posting_date, si.name
    """
    return frappe.db.sql(sql, {
        **filters,
        "is_return": is_return,
        "tran_type": tran_type,
    }, as_dict=True)


def _normalize_row(row):
    return {
        "customer": row.get("customer"),
        "customer_name": row.get("customer_name"),
        "posting_date": row.get("posting_date"),
        "voucher_type": row.get("voucher_type"),
        "voucher_no": row.get("voucher_no"),
        "tran_type": row.get("tran_type"),
        "trx_amount": flt(row.get("trx_amount")),
        "paid_amount": flt(row.get("paid_amount")),
        "debit": flt(row.get("debit")),
        "credit": flt(row.get("credit")),
        "balance": 0.0,
    }


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
