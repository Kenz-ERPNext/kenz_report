# Party Statement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a branded customer statement (Script Report + Print Format + bulk-print endpoint) inside the `kenz_report` Frappe app that reproduces the reference CHEF ALARABI Party Statement layout and matches the design at [docs/superpowers/specs/2026-05-27-party-statement-design.md](../specs/2026-05-27-party-statement-design.md).

**Architecture:** A Frappe Script Report whose `execute(filters)` builds a body by UNION-ing four normalized source-document subqueries (Sales Invoice non-return, Sales Invoice return, Payment Entry, Journal Entry against receivable), prepends an opening-balance row per customer (computed from `tabGL Entry` before `from_date`), appends a closing-balance row, and runs a Python cumulative balance pass. A Jinja Print Format renders the branded PDF; a whitelisted bulk-print endpoint loops customers and concatenates pages.

**Tech Stack:** Python 3 (Frappe controllers), Frappe Framework v15 (Script Report API, `frappe.db.sql`, `frappe.qb` not used — raw parameterized SQL for the union), Jinja2 (Print Format), JavaScript (`frappe.query_reports` API), ERPNext doctypes (Customer, Sales Invoice, Payment Entry, Journal Entry, GL Entry).

**Test environment:** All tests run via `bench --site <test_site> run-tests --app kenz_report --module <dotted.path>`. Tests use `FrappeTestCase` from `frappe.tests.utils` and create their own customer/invoice fixtures (no reliance on `_Test Customer` because that fixture's company may not match our test company).

---

## File Plan

**New files:**
- `kenz_report/kenz_report/report/__init__.py` — module init
- `kenz_report/kenz_report/report/party_statement/__init__.py` — module init
- `kenz_report/kenz_report/report/party_statement/party_statement.json` — Script Report definition (filters, roles)
- `kenz_report/kenz_report/report/party_statement/party_statement.py` — `execute(filters)` and internal helpers; one focused file containing the whole data pipeline (≈350 LOC target)
- `kenz_report/kenz_report/report/party_statement/party_statement.js` — filter UI hooks + "Print Statement" button
- `kenz_report/kenz_report/report/party_statement/test_party_statement.py` — unit tests
- `kenz_report/kenz_report/print_format/__init__.py` — module init
- `kenz_report/kenz_report/print_format/party_statement/__init__.py` — module init
- `kenz_report/kenz_report/print_format/party_statement/party_statement.json` — Custom Print Format doctype record (Jinja HTML+CSS)
- `kenz_report/api/__init__.py` — module init
- `kenz_report/api/party_statement.py` — whitelisted `print_statement` endpoint

**Modified files:**
- `kenz_report/kenz_report/hooks.py` — add `fixtures` entry so the Print Format ships with the app

The single-file `party_statement.py` keeps the data pipeline together (each helper is short, the file stays scannable). If it grows past ~400 LOC during implementation, split into `_queries.py` + `party_statement.py`. Don't split prematurely.

---

## Conventions Used Throughout

**SQL style:** All queries use `frappe.db.sql(query, values, as_dict=True)` with named parameters `%(name)s` — never string-interpolated values. Backticks around table names (`` `tabSales Invoice` ``).

**Money values:** Always cast through `flt()` from `frappe.utils` after fetching; never trust raw decimals from joins.

**Filters object:** Treated as a dict (the report framework passes a dict; the API endpoint receives a JSON string and parses with `frappe.parse_json`).

**Test isolation:** Each test creates its own Customer + Sales Invoice / Payment Entry / Journal Entry and tears down via `FrappeTestCase`'s rollback (default behavior). Tests use a helper `_make_customer()`, `_make_sales_invoice()`, etc., defined once at the top of `test_party_statement.py`.

---

## Task 1: Scaffold module directories and empty `__init__.py` files

**Files:**
- Create: `kenz_report/kenz_report/report/__init__.py`
- Create: `kenz_report/kenz_report/report/party_statement/__init__.py`
- Create: `kenz_report/kenz_report/print_format/__init__.py`
- Create: `kenz_report/kenz_report/print_format/party_statement/__init__.py`
- Create: `kenz_report/api/__init__.py`

- [ ] **Step 1: Create all five empty `__init__.py` files**

```bash
mkdir -p kenz_report/kenz_report/report/party_statement
mkdir -p kenz_report/kenz_report/print_format/party_statement
mkdir -p kenz_report/api
touch kenz_report/kenz_report/report/__init__.py
touch kenz_report/kenz_report/report/party_statement/__init__.py
touch kenz_report/kenz_report/print_format/__init__.py
touch kenz_report/kenz_report/print_format/party_statement/__init__.py
touch kenz_report/api/__init__.py
```

- [ ] **Step 2: Verify**

Run: `find kenz_report -type d -newer kenz_report/hooks.py`
Expected: prints the new directories.

- [ ] **Step 3: Commit**

```bash
git add kenz_report/
git commit -m "chore: scaffold party_statement module directories"
```

---

## Task 2: Create the Script Report definition JSON

**Files:**
- Create: `kenz_report/kenz_report/report/party_statement/party_statement.json`

- [ ] **Step 1: Write the report JSON**

```json
{
 "add_total_row": 0,
 "columns": [],
 "creation": "2026-05-27 10:00:00.000000",
 "disable_prepared_report": 0,
 "disabled": 0,
 "docstatus": 0,
 "doctype": "Report",
 "filters": [],
 "idx": 0,
 "is_standard": "Yes",
 "json": "{}",
 "letterhead": null,
 "modified": "2026-05-27 10:00:00.000000",
 "modified_by": "Administrator",
 "module": "Kenz Report",
 "name": "Party Statement",
 "owner": "Administrator",
 "prepared_report": 0,
 "ref_doctype": "Sales Invoice",
 "report_name": "Party Statement",
 "report_type": "Script Report",
 "roles": [
  {"role": "Accounts Manager"},
  {"role": "Accounts User"},
  {"role": "Sales Manager"}
 ]
}
```

**Notes for the engineer:**
- `ref_doctype: "Sales Invoice"` is a Frappe quirk: Script Reports require *some* reference doctype even when they aggregate multiple sources. Sales Invoice is the dominant document and an OK home for the report in the Desk's "Reports" menu.
- `module: "Kenz Report"` matches the `modules.txt` entry of this app.
- Columns and filters are defined in Python; the JSON keeps them empty.

- [ ] **Step 2: Run `bench migrate` on the dev site**

Run: `bench --site <dev_site> migrate`
Expected: no errors. The "Party Statement" report appears under Accounts module in Desk.

- [ ] **Step 3: Commit**

```bash
git add kenz_report/kenz_report/report/party_statement/party_statement.json
git commit -m "feat: register Party Statement script report"
```

---

## Task 3: `execute()` returns columns and empty data — establish the skeleton

**Files:**
- Create: `kenz_report/kenz_report/report/party_statement/party_statement.py`
- Create: `kenz_report/kenz_report/report/party_statement/test_party_statement.py`

- [ ] **Step 1: Write the failing test**

Create `test_party_statement.py`:

```python
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from kenz_report.kenz_report.report.party_statement.party_statement import execute


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
        labels = [c["label"] for c in columns]
        self.assertEqual(labels, [
            "TRX Date", "TRX No / Inv No", "Tran-Type",
            "TRX Amount", "Paid Amount", "Debit", "Credit", "Balance",
        ])

    def test_execute_returns_list_data(self):
        columns, data = execute(self._base_filters())
        self.assertIsInstance(data, list)
```

- [ ] **Step 2: Run test, confirm it fails**

Run: `bench --site <test_site> run-tests --app kenz_report --module kenz_report.kenz_report.report.party_statement.test_party_statement`
Expected: ImportError / ModuleNotFoundError on `party_statement.party_statement`.

- [ ] **Step 3: Write minimal `party_statement.py`**

```python
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
```

- [ ] **Step 4: Run tests, confirm both pass**

Run: `bench --site <test_site> run-tests --app kenz_report --module kenz_report.kenz_report.report.party_statement.test_party_statement`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add kenz_report/kenz_report/report/party_statement/party_statement.py \
        kenz_report/kenz_report/report/party_statement/test_party_statement.py
git commit -m "feat: party_statement execute() returns column skeleton"
```

---

## Task 4: Filter validation — date range and required fields

**Files:**
- Modify: `kenz_report/kenz_report/report/party_statement/party_statement.py`
- Modify: `kenz_report/kenz_report/report/party_statement/test_party_statement.py`

- [ ] **Step 1: Add failing tests**

Append to `TestPartyStatement`:

```python
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
```

- [ ] **Step 2: Run tests, confirm new ones fail**

Run: `bench --site <test_site> run-tests --app kenz_report --module kenz_report.kenz_report.report.party_statement.test_party_statement`
Expected: 3 new failures (no ValidationError raised).

- [ ] **Step 3: Add validation to `execute()`**

Add at the top of `execute()`, right after `filters = frappe._dict(...)`:

```python
    _validate_filters(filters)
```

And add the helper:

```python
def _validate_filters(filters):
    if not filters.get("company"):
        frappe.throw(_("Company is required"))
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("From Date and To Date are required"))
    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date must be on or before To Date"))
```

- [ ] **Step 4: Run all tests, confirm they pass**

Run: `bench --site <test_site> run-tests --app kenz_report --module kenz_report.kenz_report.report.party_statement.test_party_statement`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add kenz_report/kenz_report/report/party_statement/
git commit -m "feat: validate company and date range in party_statement"
```

---

## Task 5: Test fixtures helper — `_make_customer`, `_make_sales_invoice`, `_make_payment_entry`

**Files:**
- Modify: `kenz_report/kenz_report/report/party_statement/test_party_statement.py`

- [ ] **Step 1: Add fixture helpers at the top of the test module**

Insert above the `TestPartyStatement` class:

```python
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
    return frappe.get_doc({
        "doctype": "Item", "item_code": item_code, "item_name": item_code,
        "item_group": frappe.db.get_value("Item Group", {"is_group": 0}, "name"),
        "stock_uom": "Nos", "is_stock_item": 0,
    }).insert(ignore_permissions=True).name


def _make_sales_invoice(customer, company, posting_date, amount, is_return=0, return_against=None):
    income_account = frappe.db.get_value(
        "Account",
        {"company": company, "account_type": "Income Account", "is_group": 0},
        "name",
    )
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
    })
    si.insert(ignore_permissions=True)
    si.submit()
    return si


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
```

**Notes for the engineer:**
- These helpers assume the test site has ERPNext installed with at least one Company that has receivable/income/cash accounts set. The test site is created by `bench new-site` and then `bench --site <site> install-app erpnext`.
- `ignore_permissions=True` is used throughout — these are test fixtures, not user-flow code.
- If the test company lacks a Cash account, the engineer should pick the first account where `account_type='Cash'`. The helper does this.

- [ ] **Step 2: Add a smoke test that the helpers work**

Append to `TestPartyStatement`:

```python
    def test_fixture_helpers_create_documents(self):
        customer = _make_customer("Smoke")
        si = _make_sales_invoice(customer, self._base_filters()["company"], today(), 100)
        self.assertEqual(si.docstatus, 1)
        self.assertEqual(si.customer, customer)
```

- [ ] **Step 3: Run tests, confirm pass**

Run: `bench --site <test_site> run-tests --app kenz_report --module kenz_report.kenz_report.report.party_statement.test_party_statement`
Expected: 6 passed.

- [ ] **Step 4: Commit**

```bash
git add kenz_report/kenz_report/report/party_statement/test_party_statement.py
git commit -m "test: add party_statement test fixture helpers"
```

---

## Task 6: Sales Invoice row (SALES) — query and integrate into `execute()`

**Files:**
- Modify: `kenz_report/kenz_report/report/party_statement/party_statement.py`
- Modify: `kenz_report/kenz_report/report/party_statement/test_party_statement.py`

- [ ] **Step 1: Write the failing test**

Append:

```python
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
```

- [ ] **Step 2: Run, confirm failure**

Expected: `len(sales_rows) == 0` (execute still returns `[]`).

- [ ] **Step 3: Implement SI query + integrate**

Add to `party_statement.py`:

```python
from frappe.utils import flt


def execute(filters=None):
    filters = frappe._dict(filters or {})
    _validate_filters(filters)
    columns = _get_columns(filters)
    data = _get_data(filters)
    return columns, data


def _get_data(filters):
    rows = []
    rows.extend(_get_sales_invoice_rows(filters, is_return=0))
    return [_normalize_row(r) for r in rows]


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
```

- [ ] **Step 4: Run, confirm test passes**

Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add kenz_report/kenz_report/report/party_statement/
git commit -m "feat: add SALES rows from Sales Invoice"
```

---

## Task 7: Sales Return row (SALESRETURN)

**Files:**
- Modify: `kenz_report/kenz_report/report/party_statement/party_statement.py`
- Modify: `kenz_report/kenz_report/report/party_statement/test_party_statement.py`

- [ ] **Step 1: Write the failing test**

Append:

```python
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
```

- [ ] **Step 2: Run, confirm it fails**

Expected: `len(ret_rows) == 0`.

- [ ] **Step 3: Wire the second SI call in `_get_data`**

Edit `_get_data`:

```python
def _get_data(filters):
    rows = []
    rows.extend(_get_sales_invoice_rows(filters, is_return=0))
    rows.extend(_get_sales_invoice_rows(filters, is_return=1))
    return [_normalize_row(r) for r in rows]
```

- [ ] **Step 4: Run, confirm pass**

Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add kenz_report/kenz_report/report/party_statement/
git commit -m "feat: add SALESRETURN rows from is_return Sales Invoice"
```

---

## Task 8: Payment Entry row (RECEIPT) and per-invoice paid_amount

**Files:**
- Modify: `kenz_report/kenz_report/report/party_statement/party_statement.py`
- Modify: `kenz_report/kenz_report/report/party_statement/test_party_statement.py`

- [ ] **Step 1: Write the failing tests**

Append:

```python
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
```

- [ ] **Step 2: Run, confirm both fail**

Expected: 2 failures (no RECEIPT rows; paid_amount = 0 on SI row).

- [ ] **Step 3: Add Payment Entry query**

Add to `party_statement.py`:

```python
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
```

And update `_get_data`:

```python
def _get_data(filters):
    rows = []
    rows.extend(_get_sales_invoice_rows(filters, is_return=0))
    rows.extend(_get_sales_invoice_rows(filters, is_return=1))
    rows.extend(_get_payment_entry_rows(filters))
    return [_normalize_row(r) for r in rows]
```

- [ ] **Step 4: Run, confirm pass**

Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add kenz_report/kenz_report/report/party_statement/
git commit -m "feat: add RECEIPT rows and per-invoice paid_amount allocation"
```

---

## Task 9: Journal Entry row (JV) against the receivable account

**Files:**
- Modify: `kenz_report/kenz_report/report/party_statement/party_statement.py`
- Modify: `kenz_report/kenz_report/report/party_statement/test_party_statement.py`

- [ ] **Step 1: Add a JE fixture helper to the test file**

Above `TestPartyStatement`, add:

```python
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
```

- [ ] **Step 2: Write the failing test**

Append:

```python
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
```

- [ ] **Step 3: Run, confirm failure**

Expected: `len(jvs) == 0`.

- [ ] **Step 4: Implement JE query + receivable resolution helper**

Add to `party_statement.py`:

```python
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
```

Update `_get_data`:

```python
def _get_data(filters):
    rows = []
    rows.extend(_get_sales_invoice_rows(filters, is_return=0))
    rows.extend(_get_sales_invoice_rows(filters, is_return=1))
    rows.extend(_get_payment_entry_rows(filters))
    rows.extend(_get_journal_entry_rows(filters))
    return [_normalize_row(r) for r in rows]
```

- [ ] **Step 5: Run, confirm pass**

Expected: 11 passed.

- [ ] **Step 6: Commit**

```bash
git add kenz_report/kenz_report/report/party_statement/
git commit -m "feat: add JV rows from Journal Entry against receivable account"
```

---

## Task 10: Opening balance row from GL Entry before from_date

**Files:**
- Modify: `kenz_report/kenz_report/report/party_statement/party_statement.py`
- Modify: `kenz_report/kenz_report/report/party_statement/test_party_statement.py`

- [ ] **Step 1: Write the failing test**

Append:

```python
    def test_opening_balance_from_pre_period_invoice(self):
        customer = _make_customer("OB")
        company = self._base_filters()["company"]
        _make_sales_invoice(customer, company, add_days(today(), -60), 250)

        filters = self._base_filters()
        filters["customer"] = customer
        columns, data = execute(filters)

        opening = [r for r in data if r.get("tran_type") == "OPENING BALANCE"]
        self.assertEqual(len(opening), 1)
        self.assertEqual(opening[0]["balance"], 250)
        self.assertEqual(opening[0]["customer"], customer)
```

- [ ] **Step 2: Run, confirm failure**

Expected: no OPENING BALANCE row.

- [ ] **Step 3: Implement opening balance query + integration**

Add to `party_statement.py`:

```python
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
```

Replace `_get_data`:

```python
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
```

- [ ] **Step 4: Run, confirm pass**

Expected: 12 passed.

- [ ] **Step 5: Commit**

```bash
git add kenz_report/kenz_report/report/party_statement/
git commit -m "feat: prepend opening balance row per customer from GL Entry"
```

---

## Task 11: Running balance and closing-balance row

**Files:**
- Modify: `kenz_report/kenz_report/report/party_statement/party_statement.py`
- Modify: `kenz_report/kenz_report/report/party_statement/test_party_statement.py`

- [ ] **Step 1: Write the failing tests**

Append:

```python
    def test_running_balance_cumulative(self):
        customer = _make_customer("Run")
        company = self._base_filters()["company"]
        _make_sales_invoice(customer, company, add_days(today(), -2), 100)
        _make_sales_invoice(customer, company, add_days(today(), -1), 50)
        _make_payment_entry(customer, company, today(), 30)

        filters = self._base_filters()
        filters["customer"] = customer
        columns, data = execute(filters)

        opening = next(r for r in data if r["tran_type"] == "OPENING BALANCE")
        body = [r for r in data
                if r["tran_type"] in ("SALES", "RECEIPT")]
        balances = [r["balance"] for r in body]
        # opening=0, +100, +150, -30 → 120
        self.assertEqual(balances, [100, 150, 120])

    def test_closing_balance_row_present(self):
        customer = _make_customer("Close")
        company = self._base_filters()["company"]
        _make_sales_invoice(customer, company, today(), 200)
        _make_payment_entry(customer, company, today(), 50)

        filters = self._base_filters()
        filters["customer"] = customer
        columns, data = execute(filters)
        closing = [r for r in data if r["tran_type"] == "CLOSING BALANCE"]
        self.assertEqual(len(closing), 1)
        self.assertEqual(closing[0]["debit"], 200)
        self.assertEqual(closing[0]["credit"], 50)
        self.assertEqual(closing[0]["balance"], 150)
```

- [ ] **Step 2: Run, confirm both fail**

- [ ] **Step 3: Add running/closing logic**

Add to `party_statement.py`:

```python
def _closing_row(customer, customer_name, total_debit, total_credit, balance):
    return {
        "customer": customer,
        "customer_name": customer_name,
        "posting_date": None,
        "voucher_type": None,
        "voucher_no": "",
        "tran_type": "CLOSING BALANCE",
        "trx_amount": 0.0,
        "paid_amount": 0.0,
        "debit": total_debit,
        "credit": total_credit,
        "balance": balance,
    }
```

Update the per-customer assembly loop in `_get_data`:

```python
    for customer in customers:
        customer_name = frappe.db.get_value("Customer", customer, "customer_name") or customer
        opening = _get_opening_balance(filters, customer)
        opening_row = _opening_row(customer, customer_name, opening)
        final.append(opening_row)

        rows = sorted(body_by_customer.get(customer, []),
                      key=lambda r: (r["posting_date"], r["voucher_no"]))
        running = opening
        total_debit = 0.0
        total_credit = 0.0
        for row in rows:
            running += row["debit"] - row["credit"]
            row["balance"] = running
            total_debit += row["debit"]
            total_credit += row["credit"]
        final.extend(rows)
        final.append(_closing_row(customer, customer_name,
                                  total_debit, total_credit, running))
```

- [ ] **Step 4: Run, confirm pass**

Expected: 14 passed.

- [ ] **Step 5: Commit**

```bash
git add kenz_report/kenz_report/report/party_statement/
git commit -m "feat: compute running balance and append closing-balance row"
```

---

## Task 12: Multi-customer ordering, group-header row, address/mobile fetch

**Files:**
- Modify: `kenz_report/kenz_report/report/party_statement/party_statement.py`
- Modify: `kenz_report/kenz_report/report/party_statement/test_party_statement.py`

- [ ] **Step 1: Write the failing tests**

Append:

```python
    def test_multi_customer_two_separate_blocks(self):
        company = self._base_filters()["company"]
        cust_a = _make_customer("MultA")
        cust_b = _make_customer("MultB")
        _make_sales_invoice(cust_a, company, today(), 100)
        _make_sales_invoice(cust_b, company, today(), 200)

        # No customer filter — both should appear
        columns, data = execute(self._base_filters())

        customers_seen = [r["customer"] for r in data
                          if r["tran_type"] in ("OPENING BALANCE", "CLOSING BALANCE")]
        # Each customer contributes 1 opening + 1 closing row
        self.assertEqual(customers_seen.count(cust_a), 2)
        self.assertEqual(customers_seen.count(cust_b), 2)

    def test_group_header_row_carries_customer_info(self):
        customer = _make_customer("GH")
        company = self._base_filters()["company"]
        _make_sales_invoice(customer, company, today(), 100)

        filters = self._base_filters()
        filters["customer"] = customer
        columns, data = execute(filters)

        headers = [r for r in data if r.get("is_group_header")]
        self.assertEqual(len(headers), 1)
        self.assertEqual(headers[0]["customer"], customer)
        self.assertIn("customer_name", headers[0])
```

- [ ] **Step 2: Run, confirm failure**

Expected: no `is_group_header` rows; multi-customer order may also be wrong if a customer with only opening-balance rows (no body) is missing.

- [ ] **Step 3: Update `_get_data` to emit group-header rows and to include customers that have opening balance but no body rows**

Add helper:

```python
def _group_header_row(customer, customer_name, address, mobile):
    return {
        "customer": customer,
        "customer_name": customer_name,
        "address_display": address,
        "mobile_no": mobile,
        "posting_date": None,
        "voucher_type": None,
        "voucher_no": "",
        "tran_type": "",
        "trx_amount": 0.0,
        "paid_amount": 0.0,
        "debit": 0.0,
        "credit": 0.0,
        "balance": 0.0,
        "is_group_header": 1,
    }


def _customer_contact_info(customer):
    address = ""
    mobile = ""
    try:
        from frappe.contacts.doctype.address.address import get_default_address
        addr_name = get_default_address("Customer", customer)
        if addr_name:
            address = frappe.db.get_value("Address", addr_name, "address_line1") or ""
            city = frappe.db.get_value("Address", addr_name, "city") or ""
            if city:
                address = f"{address}, {city}" if address else city
    except Exception:
        pass
    try:
        contact_name = frappe.db.get_value(
            "Dynamic Link",
            {"parenttype": "Contact", "link_doctype": "Customer", "link_name": customer},
            "parent",
        )
        if contact_name:
            mobile = frappe.db.get_value("Contact", contact_name, "mobile_no") or ""
    except Exception:
        pass
    return address, mobile
```

Update the assembly loop to include header rows and to include customers with non-zero opening even if no body:

```python
def _customers_in_data(filters, body_rows):
    if filters.get("customer"):
        return [filters.customer]
    body_customers = {r["customer"] for r in body_rows if r.get("customer")}
    # Also include customers with opening balance but no body rows:
    # cheap heuristic — when no customer filter, GL Entry list:
    receivable = _get_receivable_account(filters.company)
    opening_customers = frappe.db.sql_list("""
        SELECT DISTINCT party FROM `tabGL Entry`
        WHERE company = %(company)s
          AND account = %(receivable_account)s
          AND party_type = 'Customer'
          AND posting_date < %(from_date)s
          AND is_cancelled = 0
    """, {"company": filters.company, "receivable_account": receivable,
          "from_date": filters.from_date})
    return sorted(body_customers | set(opening_customers))
```

In the loop, replace the opening append:

```python
    for customer in customers:
        customer_name = frappe.db.get_value("Customer", customer, "customer_name") or customer
        address, mobile = _customer_contact_info(customer)
        final.append(_group_header_row(customer, customer_name, address, mobile))
        opening = _get_opening_balance(filters, customer)
        final.append(_opening_row(customer, customer_name, opening))
        ...  # (rest of body / closing as before)
```

Mark `is_opening` / `is_closing` in their respective rows by adding the flag to `_opening_row` and `_closing_row`:

```python
# In _opening_row:
    return {... , "is_opening": 1}
# In _closing_row:
    return {... , "is_closing": 1}
```

- [ ] **Step 4: Run, confirm tests pass**

Expected: 16 passed.

- [ ] **Step 5: Commit**

```bash
git add kenz_report/kenz_report/report/party_statement/
git commit -m "feat: emit group-header row and support multi-customer blocks"
```

---

## Task 13: `show_only_with_balance` filter and customer-group/territory drilldowns

**Files:**
- Modify: `kenz_report/kenz_report/report/party_statement/party_statement.py`
- Modify: `kenz_report/kenz_report/report/party_statement/test_party_statement.py`

- [ ] **Step 1: Write the failing tests**

Append:

```python
    def test_show_only_with_balance_drops_zero_net_customers(self):
        customer = _make_customer("Zero")
        company = self._base_filters()["company"]
        si = _make_sales_invoice(customer, company, today(), 100)
        _make_payment_entry(customer, company, today(), 100, against_invoice=si)

        filters = self._base_filters()
        filters["show_only_with_balance"] = 1
        # customer has zero net → must not appear
        columns, data = execute(filters)
        customers_seen = {r.get("customer") for r in data if r.get("customer")}
        self.assertNotIn(customer, customers_seen)

    def test_customer_group_filter(self):
        company = self._base_filters()["company"]
        # Use the default customer_group created by _make_customer
        customer = _make_customer("CG")
        group = frappe.db.get_value("Customer", customer, "customer_group")
        _make_sales_invoice(customer, company, today(), 50)

        filters = self._base_filters()
        filters["customer_group"] = group
        columns, data = execute(filters)
        customers_seen = {r.get("customer") for r in data if r.get("customer")}
        self.assertIn(customer, customers_seen)
```

- [ ] **Step 2: Run, confirm failure**

Expected: `show_only_with_balance` ignored; `customer_group` ignored.

- [ ] **Step 3: Add customer-group/territory/sales_person joins to each subquery**

Add a shared helper in `party_statement.py`:

```python
def _customer_scope_join_and_clause(filters):
    """Return (extra_join, extra_where) SQL fragments for filtering by
    customer_group / territory / sales_person. Returns ('', '') when no
    drilldown is active or when filters.customer is set."""
    if filters.get("customer"):
        return "", ""
    joins = []
    clauses = []
    if filters.get("customer_group") or filters.get("territory"):
        joins.append("LEFT JOIN `tabCustomer` c ON c.name = {customer_field}")
        if filters.get("customer_group"):
            clauses.append("c.customer_group = %(customer_group)s")
        if filters.get("territory"):
            clauses.append("c.territory = %(territory)s")
    if filters.get("sales_person"):
        joins.append(
            "LEFT JOIN `tabSales Team` st "
            "ON st.parent = {customer_field} AND st.parenttype = 'Customer'"
        )
        clauses.append("st.sales_person = %(sales_person)s")
    return " ".join(joins), (" AND " + " AND ".join(clauses)) if clauses else ""
```

Update `_get_sales_invoice_rows`, `_get_payment_entry_rows`, `_get_journal_entry_rows` to embed the join/clause with the correct `customer_field` value:
- SI: `si.customer`
- PE: `pe.party`
- JE: `jea.party`

Example for `_get_sales_invoice_rows`:

```python
    extra_join, extra_where = _customer_scope_join_and_clause(filters)
    extra_join = extra_join.format(customer_field="si.customer")
    sql = f"""
        SELECT ...
        FROM `tabSales Invoice` si
        {extra_join}
        WHERE si.docstatus = 1
          AND si.company = %(company)s
          AND si.is_return = %(is_return)s
          AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
          {customer_clause}
          {extra_where}
        ORDER BY si.posting_date, si.name
    """
```

Apply analogously to PE (replace `c.customer_name AS customer_name` to use the existing `c` alias from the join — drop the duplicate LEFT JOIN if a scope-driven one is already present; simplest is to always use the scope-driven `c` join and remove the existing `LEFT JOIN tabCustomer c` line in PE/JE when the scope join is added).

The simplest reliable approach: always emit the `LEFT JOIN tabCustomer c ON c.name = <customer_field>` in PE and JE, and have `_customer_scope_join_and_clause` only emit the Sales Team join. Rewrite:

```python
def _customer_scope_join_and_clause(filters, customer_field):
    if filters.get("customer"):
        return "", ""
    join = ""
    clauses = []
    if filters.get("customer_group"):
        clauses.append("c.customer_group = %(customer_group)s")
    if filters.get("territory"):
        clauses.append("c.territory = %(territory)s")
    if filters.get("sales_person"):
        join = (
            f"LEFT JOIN `tabSales Team` st "
            f"ON st.parent = {customer_field} AND st.parenttype = 'Customer' "
        )
        clauses.append("st.sales_person = %(sales_person)s")
    where = (" AND " + " AND ".join(clauses)) if clauses else ""
    return join, where
```

Then in `_get_sales_invoice_rows`, ensure there's a `LEFT JOIN tabCustomer c ON c.name = si.customer` (we don't currently have one — add it if `customer_group` or `territory` is set, OR just always add it; the LEFT JOIN cost is negligible).

For consistency, **always** include `LEFT JOIN tabCustomer c ON c.name = <customer_field>` in all three subqueries, then the scope helper only emits the Sales Team join + WHERE clauses.

- [ ] **Step 4: Apply `show_only_with_balance` filter at the end of `_get_data`**

Add at the bottom of `_get_data`, before `return final`:

```python
    if filters.get("show_only_with_balance"):
        final = _drop_zero_balance_customers(final)
    return final


def _drop_zero_balance_customers(rows):
    # Group by customer; keep block only if its closing-balance row's balance != 0
    blocks = {}
    order = []
    for r in rows:
        cust = r.get("customer")
        if cust not in blocks:
            blocks[cust] = []
            order.append(cust)
        blocks[cust].append(r)
    kept = []
    for cust in order:
        block = blocks[cust]
        closing = next((r for r in block if r.get("is_closing")), None)
        if closing and abs(flt(closing["balance"])) < 0.005:
            continue
        kept.extend(block)
    return kept
```

- [ ] **Step 5: Run, confirm tests pass**

Expected: 18 passed.

- [ ] **Step 6: Commit**

```bash
git add kenz_report/kenz_report/report/party_statement/
git commit -m "feat: customer-group/territory/sales-person filters and show_only_with_balance"
```

---

## Task 14: Attach `currency` to every data row

**Files:**
- Modify: `kenz_report/kenz_report/report/party_statement/party_statement.py`
- Modify: `kenz_report/kenz_report/report/party_statement/test_party_statement.py`

- [ ] **Step 1: Failing test**

Append:

```python
    def test_currency_attached_to_rows(self):
        customer = _make_customer("Cur")
        company = self._base_filters()["company"]
        _make_sales_invoice(customer, company, today(), 100)
        filters = self._base_filters()
        filters["customer"] = customer
        columns, data = execute(filters)
        body_rows = [r for r in data if r["tran_type"] == "SALES"]
        currency = frappe.get_cached_value("Company", company, "default_currency")
        for r in body_rows:
            self.assertEqual(r.get("currency"), currency)
```

- [ ] **Step 2: Run, confirm failure** (`currency` is None on rows).

- [ ] **Step 3: Inject currency into every emitted row**

In `_get_data`, just before `return final`:

```python
    currency = frappe.get_cached_value("Company", filters.company, "default_currency")
    for r in final:
        r["currency"] = currency
```

- [ ] **Step 4: Run, confirm pass.** Expected: 19 passed.

- [ ] **Step 5: Commit**

```bash
git add kenz_report/kenz_report/report/party_statement/
git commit -m "feat: attach company currency to party_statement rows"
```

---

## Task 15: Create the Print Format JSON record

**Files:**
- Create: `kenz_report/kenz_report/print_format/party_statement/party_statement.json`

- [ ] **Step 1: Write the print format JSON**

```json
{
 "creation": "2026-05-27 10:00:00.000000",
 "css": "",
 "custom_format": 1,
 "default_print_language": "en",
 "disabled": 0,
 "doc_type": "",
 "docstatus": 0,
 "doctype": "Print Format",
 "font": "Default",
 "html": "<!-- see body below -->",
 "idx": 0,
 "line_breaks": 0,
 "margin_bottom": 12.0,
 "margin_left": 12.0,
 "margin_right": 12.0,
 "margin_top": 12.0,
 "modified": "2026-05-27 10:00:00.000000",
 "modified_by": "Administrator",
 "module": "Kenz Report",
 "name": "Party Statement",
 "owner": "Administrator",
 "page_number": "Hide",
 "print_format_builder": 0,
 "print_format_type": "Jinja",
 "show_section_headings": 0,
 "standard": "Yes"
}
```

Replace the `html` value with the following (encoded as a single JSON string — escape newlines as `\n` and double quotes as `\"`). Engineer can write the template into a `.html` file first for sanity, then JSON-encode it:

```html
<style>
  .ps-page { font-family: Arial, sans-serif; font-size: 9pt; color: #111; }
  .ps-company { text-align: center; font-weight: bold; font-size: 18pt; margin-bottom: 4px; }
  .ps-stripes { display: flex; align-items: center; gap: 8px; margin: 6px 0 8px 0; }
  .ps-stripe { height: 14px; flex: 1; }
  .ps-stripe-red {
    background: repeating-linear-gradient(135deg, #d11 0 6px, transparent 6px 12px);
  }
  .ps-stripe-spacer { flex: 0 0 30%; }
  .ps-stripe-green {
    background: repeating-linear-gradient(135deg, #0a0 0 6px, transparent 6px 12px);
  }
  .ps-title { text-align: center; font-weight: bold; font-size: 13pt; margin: 6px 0; }
  .ps-meta { border-top: 1px solid #888; border-bottom: 1px solid #888;
             padding: 6px 4px; margin-bottom: 8px; }
  .ps-meta div { margin: 2px 0; }
  table.ps-tbl { width: 100%; border-collapse: collapse; }
  table.ps-tbl th, table.ps-tbl td { border: 1px solid #888; padding: 4px 6px; }
  table.ps-tbl th { background: #f0f0f0; text-align: center; font-weight: bold; }
  table.ps-tbl td.num { text-align: right; }
  .ps-page-break { page-break-after: always; }
</style>
<div class="ps-page">
  <div class="ps-company">{{ company_name|upper }}</div>
  <div class="ps-stripes">
    <div class="ps-stripe ps-stripe-red"></div>
    <div class="ps-stripe-spacer"></div>
    <div class="ps-stripe ps-stripe-green"></div>
  </div>
  <div class="ps-title">Party Statement</div>
  <div class="ps-meta">
    <div><b>Period</b>&nbsp;&nbsp;: {{ frappe.utils.formatdate(from_date) }}&nbsp;&nbsp;&nbsp;{{ frappe.utils.formatdate(to_date) }}</div>
    <div><b>Party</b>&nbsp;&nbsp;&nbsp;: {{ customer_name }}</div>
    <div><b>Address</b>&nbsp;: {{ address or "" }}</div>
    <div><b>Mobile</b>&nbsp;&nbsp;: {{ mobile or "0" }}</div>
  </div>
  <table class="ps-tbl">
    <thead>
      <tr>
        <th>TRX DATE</th><th>TRX No / Inv No</th><th>TRAN-TYPE</th>
        <th>TRX AMOUNT</th><th>PAID AMOUNT</th>
        <th>DEBIT</th><th>CREDIT</th><th>BALANCE</th>
      </tr>
    </thead>
    <tbody>
    {% for row in rows %}
      <tr>
        <td>{% if row.posting_date %}{{ frappe.utils.formatdate(row.posting_date) }}{% endif %}</td>
        <td>{{ row.voucher_no or "" }}</td>
        <td>{{ row.tran_type }}</td>
        <td class="num">{{ "{:,.3f}".format(row.trx_amount or 0) }}</td>
        <td class="num">{{ "{:,.3f}".format(row.paid_amount or 0) }}</td>
        <td class="num">{{ "{:,.3f}".format(row.debit or 0) }}</td>
        <td class="num">{{ "{:,.3f}".format(row.credit or 0) }}</td>
        <td class="num">{{ "{:,.3f}".format(row.balance or 0) }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
</div>
```

**Notes:**
- The template expects context vars: `company_name`, `from_date`, `to_date`, `customer_name`, `address`, `mobile`, `rows`.
- Numbers formatted with 3 decimals to match the screenshot.
- The header row in `rows` (`is_group_header`) should be filtered out by the caller before passing — the caller assembles `customer_name`/`address`/`mobile` from that row.

- [ ] **Step 2: Run `bench migrate`**

Expected: print format "Party Statement" exists in Desk under "Print Format" list.

- [ ] **Step 3: Commit**

```bash
git add kenz_report/kenz_report/print_format/party_statement/party_statement.json
git commit -m "feat: add Party Statement print format"
```

---

## Task 16: Register Print Format as a fixture in hooks.py

**Files:**
- Modify: `kenz_report/kenz_report/hooks.py`

- [ ] **Step 1: Append `fixtures` to `hooks.py`**

At the end of `hooks.py`, add:

```python
fixtures = [
    {
        "doctype": "Print Format",
        "filters": [["name", "in", ["Party Statement"]]],
    },
]
```

- [ ] **Step 2: Run `bench migrate` on a fresh test site to confirm the print format is installed**

```bash
bench --site <fresh_test_site> install-app kenz_report
bench --site <fresh_test_site> migrate
bench --site <fresh_test_site> console
# In console:
#   frappe.db.exists("Print Format", "Party Statement")
# Expected: returns "Party Statement"
```

- [ ] **Step 3: Commit**

```bash
git add kenz_report/kenz_report/hooks.py
git commit -m "chore: register Party Statement print format as fixture"
```

---

## Task 17: Bulk-print API endpoint

**Files:**
- Create: `kenz_report/api/party_statement.py`
- Modify: `kenz_report/kenz_report/report/party_statement/test_party_statement.py`

- [ ] **Step 1: Failing test**

Append:

```python
    def test_print_statement_endpoint_returns_html_for_each_customer(self):
        from kenz_report.api.party_statement import print_statement
        company = self._base_filters()["company"]
        cust_a = _make_customer("PA")
        cust_b = _make_customer("PB")
        _make_sales_invoice(cust_a, company, today(), 100)
        _make_sales_invoice(cust_b, company, today(), 200)

        result = print_statement(frappe.as_json(self._base_filters()))
        html = result["html"]
        self.assertIn("Party Statement", html)
        self.assertIn(cust_a, html)
        self.assertIn(cust_b, html)
        self.assertIn("page-break-after", html)
```

- [ ] **Step 2: Confirm failure** — module doesn't exist.

- [ ] **Step 3: Implement endpoint**

Create `kenz_report/api/party_statement.py`:

```python
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
```

- [ ] **Step 4: Run, confirm pass**

Expected: 20 passed.

- [ ] **Step 5: Commit**

```bash
git add kenz_report/api/party_statement.py \
        kenz_report/kenz_report/report/party_statement/test_party_statement.py
git commit -m "feat: bulk-print endpoint for party_statement"
```

---

## Task 18: Script Report JS — filters and Print button

**Files:**
- Create: `kenz_report/kenz_report/report/party_statement/party_statement.js`

- [ ] **Step 1: Write the JS**

```javascript
frappe.query_reports["Party Statement"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1,
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            reqd: 1,
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1,
        },
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer",
        },
        {
            fieldname: "customer_group",
            label: __("Customer Group"),
            fieldtype: "Link",
            options: "Customer Group",
        },
        {
            fieldname: "territory",
            label: __("Territory"),
            fieldtype: "Link",
            options: "Territory",
        },
        {
            fieldname: "sales_person",
            label: __("Sales Person"),
            fieldtype: "Link",
            options: "Sales Person",
        },
        {
            fieldname: "show_only_with_balance",
            label: __("Only Customers with Balance"),
            fieldtype: "Check",
            default: 0,
        },
    ],

    onload(report) {
        report.page.add_inner_button(__("Print Statement"), () => {
            const filters = report.get_values();
            frappe.call({
                method: "kenz_report.api.party_statement.print_statement",
                args: { filters },
                callback(r) {
                    if (!r.message || !r.message.html) return;
                    const w = window.open("", "_blank");
                    w.document.write(r.message.html);
                    w.document.close();
                    w.focus();
                    setTimeout(() => w.print(), 500);
                },
            });
        });
    },

    formatter(value, row, column, data, default_formatter) {
        if (data && (data.is_opening || data.is_closing)) {
            value = default_formatter(value, row, column, data);
            return `<b>${value}</b>`;
        }
        if (data && data.is_group_header) {
            value = default_formatter(value, row, column, data);
            return `<span style="background:#eef; font-weight:bold">${value}</span>`;
        }
        return default_formatter(value, row, column, data);
    },
};
```

- [ ] **Step 2: Reload the report in Desk and verify filters render**

Run: `bench --site <dev_site> clear-cache && bench build --app kenz_report`
Open the "Party Statement" report in Desk. Confirm:
- All 8 filters present
- "Print Statement" button in the menu
- Opening/closing rows are bolded; group-header row has shaded background

- [ ] **Step 3: Commit**

```bash
git add kenz_report/kenz_report/report/party_statement/party_statement.js
git commit -m "feat: party_statement filters and Print Statement button"
```

---

## Task 19: End-to-end smoke check (manual)

**Files:** none

- [ ] **Step 1: Run the full test suite**

```bash
bench --site <test_site> run-tests --app kenz_report
```
Expected: all 20 tests pass.

- [ ] **Step 2: Open the report in the Desk on a real site**

- Pick a Company, last 30 days, leave Customer blank
- Confirm multiple customer blocks appear, each with group header + opening + body + closing
- Pick a single customer that has both invoices and a payment in the period
- Click "Print Statement" — confirm the popup opens and the printed page matches the screenshot layout (red/green stripes, period/party/address/mobile, table with 3-decimal money formatting)

- [ ] **Step 3: Push the develop branch**

```bash
git push
```

---

## Self-Review Checklist (run before handing off)

- [ ] Spec coverage:
  - [ ] Customer-only scope → Tasks 6–9
  - [ ] Sales Invoice rows → Task 6
  - [ ] Sales Return rows → Task 7
  - [ ] Payment Entry rows + per-invoice paid_amount → Task 8
  - [ ] Journal Entry rows against receivable → Task 9
  - [ ] Opening balance from GL Entry → Task 10
  - [ ] Running + closing balance → Task 11
  - [ ] Multi-customer blocks, group header, address/mobile → Task 12
  - [ ] customer/customer_group/territory/sales_person/show_only_with_balance filters → Tasks 6, 13
  - [ ] Company + date validation → Task 4
  - [ ] Columns + currency → Tasks 3, 14
  - [ ] Print Format → Task 15
  - [ ] Print Format as fixture → Task 16
  - [ ] Bulk-print endpoint → Task 17
  - [ ] Report JS (filters + Print button) → Task 18
  - [ ] Permissions: Accounts Manager / User / Sales Manager → Task 2 (Report JSON `roles`), Task 17 (`frappe.only_for`)

- [ ] All 12 spec test cases covered:
  - [ ] `test_opening_balance_from_gl` → Task 10
  - [ ] `test_sales_invoice_row` → Task 6
  - [ ] `test_sales_return_row` → Task 7
  - [ ] `test_payment_entry_row` (+ paid_amount) → Task 8
  - [ ] `test_journal_entry_against_receivable` → Task 9
  - [ ] `test_running_balance` → Task 11
  - [ ] `test_closing_balance_row` → Task 11
  - [ ] `test_multi_customer_grouping` → Task 12
  - [ ] `test_filter_customer_group` → Task 13
  - [ ] `test_show_only_with_balance` → Task 13
  - [ ] `test_date_range_validation` → Task 4
  - [ ] `test_bulk_print_endpoint` → Task 17

- [ ] No placeholders (no "TBD", "TODO", "Similar to Task N", or empty steps).

- [ ] Type/name consistency:
  - Function names: `execute`, `_get_data`, `_get_columns`, `_validate_filters`, `_get_sales_invoice_rows`, `_get_payment_entry_rows`, `_get_journal_entry_rows`, `_get_opening_balance`, `_customers_in_data`, `_opening_row`, `_closing_row`, `_group_header_row`, `_customer_contact_info`, `_customer_scope_join_and_clause`, `_drop_zero_balance_customers`, `_normalize_row`, `_payment_amount_subquery`, `_get_receivable_account`. Verified consistent across all tasks.
  - API endpoint: `print_statement`, `_group_by_customer`, `_build_print_context`, `_get_print_template`, `_wrap_html`. Consistent.
  - Row dict keys: `customer`, `customer_name`, `posting_date`, `voucher_type`, `voucher_no`, `tran_type`, `trx_amount`, `paid_amount`, `debit`, `credit`, `balance`, `currency`, `is_group_header`, `is_opening`, `is_closing`, `address_display`, `mobile_no`. Consistent across queries, normalizer, opening/closing/header builders, and print context.
