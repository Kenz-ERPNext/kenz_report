import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from kenz_report.kenz_report.report.party_statement.party_statement import execute


def _ensure_account(company, account_name, account_type, parent_field):
    """Return an account name of the given account_type for the company,
    creating a stub one only if none exists."""
    existing = frappe.db.get_value(
        "Account",
        {"company": company, "account_type": account_type, "is_group": 0},
        "name",
    )
    if existing:
        return existing
    parent = frappe.db.get_value(
        "Account", {"company": company, "account_name": parent_field, "is_group": 1}, "name"
    )
    acc = frappe.get_doc({
        "doctype": "Account", "account_name": account_name,
        "company": company, "parent_account": parent,
        "account_type": account_type, "is_group": 0,
    }).insert(ignore_permissions=True, ignore_if_duplicate=True)
    return acc.name


def _make_customer(name_suffix):
    cust_name = f"_PS Customer {name_suffix}"
    if frappe.db.exists("Customer", cust_name):
        return cust_name
    return frappe.get_doc({
        "doctype": "Customer",
        "customer_name": cust_name,
        "customer_type": "Company",
        "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name"),
        "territory": frappe.db.get_value("Territory", {"is_group": 0}, "name"),
    }).insert(ignore_permissions=True).name


def _make_item():
    item_code = "_PS Test Item"
    if frappe.db.exists("Item", item_code):
        return item_code
    tax_template = frappe.db.get_value("Tax Template", {}, "name")
    doc = {
        "doctype": "Item", "item_code": item_code, "item_name": item_code,
        "item_group": frappe.db.get_value("Item Group", {"is_group": 0}, "name"),
        "stock_uom": "Nos", "is_stock_item": 0,
    }
    if tax_template:
        doc["custom_item_tax_template"] = tax_template
    return frappe.get_doc(doc).insert(ignore_permissions=True).name


def _make_sales_invoice(customer, company, posting_date, amount, is_return=0, return_against=None):
    income_account = frappe.db.get_value(
        "Account",
        {"company": company, "account_type": "Income Account", "is_group": 0},
        "name",
    )
    tax_account = frappe.db.get_value(
        "Account",
        {"company": company, "account_type": "Tax", "is_group": 0},
        "name",
    )
    taxes = []
    if tax_account:
        taxes = [{
            "charge_type": "On Net Total",
            "account_head": tax_account,
            "description": "VAT",
            "rate": 0,
        }]
    si = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": customer,
        "company": company,
        "posting_date": posting_date,
        "due_date": posting_date,
        "is_return": is_return,
        "return_against": return_against,
        "items": [{
            "item_code": _make_item(),
            "qty": -1 if is_return else 1,
            "rate": amount,
            "income_account": income_account,
        }],
        "taxes": taxes,
    })
    si.insert(ignore_permissions=True)
    si.submit()
    return si


def _make_journal_entry(customer, company, posting_date, debit_amount=0, credit_amount=0):
    receivable = frappe.get_cached_value("Company", company, "default_receivable_account")
    offset = frappe.db.get_value(
        "Account",
        {"company": company, "account_type": "Bank", "is_group": 0},
        "name",
    ) or frappe.db.get_value(
        "Account", {"company": company, "account_type": "Cash", "is_group": 0}, "name"
    )
    je = frappe.get_doc({
        "doctype": "Journal Entry",
        "company": company,
        "posting_date": posting_date,
        "voucher_type": "Journal Entry",
        "accounts": [
            {
                "account": receivable, "party_type": "Customer", "party": customer,
                "debit_in_account_currency": debit_amount,
                "credit_in_account_currency": credit_amount,
            },
            {
                "account": offset,
                "debit_in_account_currency": credit_amount,
                "credit_in_account_currency": debit_amount,
            },
        ],
    })
    je.insert(ignore_permissions=True)
    je.submit()
    return je


def _make_payment_entry(customer, company, posting_date, amount, against_invoice=None):
    receivable = frappe.get_cached_value("Company", company, "default_receivable_account")
    cash = frappe.db.get_value(
        "Account", {"company": company, "account_type": "Cash", "is_group": 0}, "name"
    )
    pe = frappe.get_doc({
        "doctype": "Payment Entry",
        "payment_type": "Receive",
        "company": company,
        "posting_date": posting_date,
        "party_type": "Customer",
        "party": customer,
        "paid_from": receivable,
        "paid_to": cash,
        "paid_amount": amount,
        "received_amount": amount,
        "references": ([{
            "reference_doctype": "Sales Invoice",
            "reference_name": against_invoice.name,
            "allocated_amount": amount,
        }] if against_invoice else []),
    })
    pe.insert(ignore_permissions=True)
    pe.submit()
    return pe


class TestPartyStatement(FrappeTestCase):
    def _base_filters(self):
        company = frappe.db.get_single_value("Global Defaults", "default_company") \
            or frappe.db.get_value("Company", {}, "name")
        return {
            "company": company,
            "from_date": add_days(today(), -30),
            "to_date": today(),
        }

    def test_execute_returns_eight_columns(self):
        columns, data = execute(self._base_filters())
        self.assertEqual(len(columns), 8)
        fieldnames = [c["fieldname"] for c in columns]
        self.assertEqual(fieldnames, [
            "posting_date", "voucher_no", "tran_type",
            "trx_amount", "paid_amount", "debit", "credit", "balance",
        ])

    def test_execute_returns_list_data(self):
        columns, data = execute(self._base_filters())
        self.assertEqual(data, [])

    def test_from_date_after_to_date_raises(self):
        filters = self._base_filters()
        filters["from_date"] = today()
        filters["to_date"] = add_days(today(), -10)
        with self.assertRaises(frappe.ValidationError):
            execute(filters)

    def test_missing_company_raises(self):
        with self.assertRaises(frappe.ValidationError):
            execute({"from_date": today(), "to_date": today()})

    def test_missing_dates_raise(self):
        with self.assertRaises(frappe.ValidationError):
            execute({"company": self._base_filters()["company"]})

    def test_fixture_helpers_create_documents(self):
        customer = _make_customer("Smoke")
        si = _make_sales_invoice(customer, self._base_filters()["company"], today(), 100)
        self.assertEqual(si.docstatus, 1)
        self.assertEqual(si.customer, customer)

    def test_sales_invoice_appears_as_sales_row(self):
        customer = _make_customer("SI")
        company = self._base_filters()["company"]
        si = _make_sales_invoice(customer, company, today(), 500)

        filters = self._base_filters()
        filters["customer"] = customer
        columns, data = execute(filters)

        sales_rows = [r for r in data if r.get("tran_type") == "SALES"]
        self.assertEqual(len(sales_rows), 1)
        row = sales_rows[0]
        self.assertEqual(row["voucher_no"], si.name)
        self.assertEqual(row["voucher_type"], "Sales Invoice")
        self.assertEqual(row["debit"], 500)
        self.assertEqual(row["credit"], 0)
        self.assertEqual(row["trx_amount"], 500)

    def test_sales_return_appears_as_salesreturn_row(self):
        customer = _make_customer("SR")
        company = self._base_filters()["company"]
        si = _make_sales_invoice(customer, company, today(), 200)
        ret = _make_sales_invoice(customer, company, today(), 200, is_return=1, return_against=si.name)

        filters = self._base_filters()
        filters["customer"] = customer
        columns, data = execute(filters)

        ret_rows = [r for r in data if r.get("tran_type") == "SALESRETURN"]
        self.assertEqual(len(ret_rows), 1)
        row = ret_rows[0]
        self.assertEqual(row["debit"], 0)
        self.assertEqual(row["credit"], 200)
        self.assertEqual(row["trx_amount"], 200)

    def test_payment_entry_appears_as_receipt_row(self):
        customer = _make_customer("PE")
        company = self._base_filters()["company"]
        si = _make_sales_invoice(customer, company, today(), 300)
        pe = _make_payment_entry(customer, company, today(), 100, against_invoice=si)

        filters = self._base_filters()
        filters["customer"] = customer
        columns, data = execute(filters)

        receipts = [r for r in data if r.get("tran_type") == "RECEIPT"]
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["voucher_no"], pe.name)
        self.assertEqual(receipts[0]["credit"], 100)
        self.assertEqual(receipts[0]["debit"], 0)
        self.assertEqual(receipts[0]["trx_amount"], 100)

    def test_payment_allocates_to_invoice_paid_amount(self):
        customer = _make_customer("PEAlloc")
        company = self._base_filters()["company"]
        si = _make_sales_invoice(customer, company, today(), 400)
        _make_payment_entry(customer, company, today(), 150, against_invoice=si)

        filters = self._base_filters()
        filters["customer"] = customer
        columns, data = execute(filters)

        sales_row = next(r for r in data if r.get("voucher_no") == si.name)
        self.assertEqual(sales_row["paid_amount"], 150)

    def test_journal_entry_appears_as_jv_row(self):
        customer = _make_customer("JV")
        company = self._base_filters()["company"]
        je = _make_journal_entry(customer, company, today(), debit_amount=75)

        filters = self._base_filters()
        filters["customer"] = customer
        columns, data = execute(filters)

        jvs = [r for r in data if r.get("tran_type") == "JV"]
        self.assertEqual(len(jvs), 1)
        self.assertEqual(jvs[0]["voucher_no"], je.name)
        self.assertEqual(jvs[0]["debit"], 75)
        self.assertEqual(jvs[0]["credit"], 0)
        self.assertEqual(jvs[0]["trx_amount"], 75)

    def test_opening_balance_from_pre_period_invoice(self):
        customer = _make_customer("OB")
        company = self._base_filters()["company"]
        # Pre-period activity: submit a Journal Entry against the receivable account
        # 60 days before from_date. This posts to GL Entry, contributing to opening balance.
        _make_journal_entry(customer, company, add_days(today(), -60), debit_amount=250)

        filters = self._base_filters()
        filters["customer"] = customer
        columns, data = execute(filters)

        opening = [r for r in data if r.get("tran_type") == "OPENING BALANCE"]
        self.assertEqual(len(opening), 1)
        self.assertEqual(opening[0]["balance"], 250)
        self.assertEqual(opening[0]["customer"], customer)
