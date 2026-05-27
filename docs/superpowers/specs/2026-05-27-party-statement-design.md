# Party Statement Report — Design Spec

**Date:** 2026-05-27
**App:** `kenz_report`
**Author:** Sammish Thundiyil (with Claude)
**Status:** Approved for planning

---

## 1. Purpose

Build a **Party Statement** report in the `kenz_report` app that reproduces the
branded customer-ledger PDF shown in the reference screenshot (CHEF ALARABI
header with red/green decorative stripes). The report lists every customer
transaction within a selected period — Sales Invoices, Sales Returns, Payment
Entries, and Journal Entries against the customer's receivable account — with
a running balance and opening/closing balance rows.

It must be usable both as an interactive desk report (filtered, drilled-down)
and as a printable PDF suitable for emailing to customers, including a
multi-customer bulk-print mode that produces one statement per customer in a
single PDF.

## 2. Scope

**In scope:**
- Customer-only statements (one party type)
- Transactions: Sales Invoice, Sales Return (`is_return=1`), Payment Entry
  (Receive against Customer party), Journal Entry rows against the configured
  receivable account
- Opening balance computed from GL Entry before the from-date
- Running balance per row, closing balance per customer
- Print Format matching the reference screenshot (company header from Company
  doctype, red/green stripe bars, period/party/address/mobile block, table
  with TRX Date / TRX No / Tran-Type / TRX Amount / Paid Amount / Debit /
  Credit / Balance)
- Multi-customer bulk PDF (one statement per customer, page-break between)
- Filters: Company, From Date, To Date (mandatory); Customer, Customer Group,
  Territory, Sales Person, Show Only With Balance (optional)

**Out of scope (deferred):**
- Supplier statements (code structure leaves room to add later, but no supplier
  paths in this iteration)
- Multi-currency conversion (statement is in company's default currency only;
  transactions in other currencies are taken at their base-currency value)
- Aging buckets / overdue analysis
- Customizable header text per company (header is sourced from Company doctype;
  no separate settings doctype)
- Web-page (public URL) delivery

## 3. Architecture

### 3.1 File Layout

```
kenz_report/kenz_report/
├── report/
│   └── party_statement/
│       ├── __init__.py
│       ├── party_statement.json          # Script Report definition
│       ├── party_statement.py            # execute(filters) → columns, data
│       ├── party_statement.js            # Filter UI + "Print Statement" button
│       └── test_party_statement.py       # Unit tests
└── print_format/
    └── party_statement/
        ├── __init__.py
        └── party_statement.json          # Custom Print Format (Jinja HTML+CSS)

kenz_report/api/
├── __init__.py
└── party_statement.py                    # Whitelisted bulk-print endpoint
```

### 3.2 Module Boundaries

| Unit | Responsibility | Interface |
|------|----------------|-----------|
| `party_statement.py:execute` | Compute columns + data for the Script Report | `execute(filters: dict) -> (columns, data)` |
| `party_statement.py` internal helpers | Query each source doc, calculate opening balance, calculate running balance, group by customer | private functions, callable by the bulk-print API |
| `party_statement.js` | Render filters, intercept "Print Statement" menu action | `frappe.query_reports["Party Statement"]` |
| `print_format/party_statement` | Pure Jinja template + CSS, no Python logic | rendered via `frappe.render_template` |
| `api/party_statement.py:print_statement` | Re-run execute, group by customer, render template per customer, return concatenated HTML | `print_statement(filters: str) -> {"html": str, "filename": str}` (whitelisted) |

The report and the bulk-print endpoint share the same data-loading code by
extracting a `get_statement_data(filters)` function in `party_statement.py`
that both `execute()` and the API endpoint call.

## 4. Filters

```python
filters = [
    # Mandatory
    {"fieldname": "company", "label": "Company", "fieldtype": "Link",
     "options": "Company",
     "default": frappe.defaults.get_user_default("Company"), "reqd": 1},
    {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date",
     "default": "fiscal year start", "reqd": 1},
    {"fieldname": "to_date", "label": "To Date", "fieldtype": "Date",
     "default": "today", "reqd": 1},

    # Optional drilldowns
    {"fieldname": "customer", "label": "Customer", "fieldtype": "Link",
     "options": "Customer"},
    {"fieldname": "customer_group", "label": "Customer Group",
     "fieldtype": "Link", "options": "Customer Group"},
    {"fieldname": "territory", "label": "Territory", "fieldtype": "Link",
     "options": "Territory"},
    {"fieldname": "sales_person", "label": "Sales Person",
     "fieldtype": "Link", "options": "Sales Person"},

    # Display
    {"fieldname": "show_only_with_balance",
     "label": "Only Customers with Balance",
     "fieldtype": "Check", "default": 0},
]
```

**Validation in `execute()`:**
- `from_date <= to_date` → else `frappe.throw(_("From Date must be before To Date"))`
- If `customer` is set, the group/territory/sales-person filters are ignored
  (single-customer mode wins). All four are honored together when `customer`
  is blank.

## 5. Data Layer

### 5.1 Receivable Account Resolution

```python
receivable_account = frappe.get_cached_value(
    "Company", filters.company, "default_receivable_account"
)
if not receivable_account:
    frappe.throw(_("Set Default Receivable Account on Company {0}").format(
        filters.company
    ))
```

Used by both the Journal Entry filter and the opening-balance query.

### 5.2 Union of Source Documents (Body Rows)

Four parallel subqueries produce a normalized column set, UNION ALL'd, ordered
by `(customer, posting_date, voucher_no)`.

**Normalized columns (every subquery must produce these):**
`customer`, `customer_name`, `posting_date`, `voucher_type`, `voucher_no`,
`tran_type`, `trx_amount`, `paid_amount`, `debit`, `credit`.

**Per-source mapping:**

| Source | Filter | tran_type | trx_amount | paid_amount | debit | credit |
|--------|--------|-----------|------------|-------------|-------|--------|
| Sales Invoice (`is_return=0`) | `docstatus=1`, `company`, `posting_date` between | `SALES` | `grand_total` | `(SELECT SUM(per.allocated_amount) FROM 'tabPayment Entry Reference' per JOIN 'tabPayment Entry' pe ON pe.name=per.parent WHERE per.reference_doctype='Sales Invoice' AND per.reference_name=si.name AND pe.docstatus=1)` | `grand_total` | `0` |
| Sales Invoice (`is_return=1`) | as above + `is_return=1` | `SALESRETURN` | `ABS(grand_total)` | `0` | `0` | `ABS(grand_total)` |
| Payment Entry | `docstatus=1`, `party_type='Customer'`, `payment_type='Receive'`, `posting_date` between, `company` | `RECEIPT` | `paid_amount` | `0` | `0` | `paid_amount` |
| Journal Entry (via `tabJournal Entry Account`) | `je.docstatus=1`, `jea.account=receivable_account`, `jea.party_type='Customer'`, `je.company`, `je.posting_date` between | `JV` | `jea.debit_in_account_currency + jea.credit_in_account_currency` | `0` | `jea.debit_in_account_currency` | `jea.credit_in_account_currency` |

The `voucher_no` column displays as "TRX No / Inv No" (matching the
screenshot). External references like PO number or cheque number are not
shown — the document name (`INV\CA\7008`-style) is what appears.

**Optional-filter joins:** When `customer_group`, `territory`, or `sales_person`
is set (and `customer` is blank), each subquery joins `tabCustomer` (and
`tabSales Team` for sales_person) and filters accordingly. Sales Person on
Payment Entry / Journal Entry rows is resolved via the Customer's primary
Sales Team entry, since PE/JE don't carry sales-person directly.

**Address & Mobile:** Fetched per-customer in Python (not in the union) via
`frappe.contacts.doctype.address.address.get_default_address` and
`frappe.contacts.doctype.contact.contact.get_default_contact`. Stored on the
group-header row that introduces each customer block.

### 5.3 Opening Balance

Computed per customer (one query per customer in multi-customer mode; one
query in single-customer mode):

```sql
SELECT IFNULL(SUM(debit - credit), 0) AS opening
FROM `tabGL Entry`
WHERE company = %(company)s
  AND account = %(receivable_account)s
  AND party_type = 'Customer'
  AND party = %(customer)s
  AND posting_date < %(from_date)s
  AND is_cancelled = 0
```

Emitted as the first non-header row of each customer block, with
`tran_type='OPENING BALANCE'`, all numeric columns zero except `balance` = the
opening value.

### 5.4 Running & Closing Balance

After union rows are fetched and grouped by customer:

```python
running = opening_balance
for row in customer_rows:
    running += (row.debit or 0) - (row.credit or 0)
    row.balance = running
```

A closing-balance row is appended to each customer block:
`tran_type='CLOSING BALANCE'`, `debit` = sum of debits, `credit` = sum of
credits, `balance` = final running value.

### 5.5 Final Data Shape

The `data` list returned by `execute()` is a flat list of dicts. Customer
blocks are concatenated in customer-name order. Each block:

```
[customer_group_header_row]      # is_group_header=1, carries customer_name, address, mobile
[opening_balance_row]            # is_opening=1
[transaction rows]               # in (posting_date, voucher_no) order
[closing_balance_row]            # is_closing=1
```

If `show_only_with_balance=1`, blocks where opening + sum(debit) - sum(credit)
== 0 are dropped entirely.

## 6. Columns (Script Report Output)

```python
columns = [
    {"label": "TRX Date",        "fieldname": "posting_date", "fieldtype": "Date",          "width": 100},
    {"label": "TRX No / Inv No", "fieldname": "voucher_no",   "fieldtype": "Dynamic Link",  "options": "voucher_type", "width": 140},
    {"label": "Tran-Type",       "fieldname": "tran_type",    "fieldtype": "Data",          "width": 110},
    {"label": "TRX Amount",      "fieldname": "trx_amount",   "fieldtype": "Currency",      "options": "currency", "width": 120},
    {"label": "Paid Amount",     "fieldname": "paid_amount",  "fieldtype": "Currency",      "options": "currency", "width": 120},
    {"label": "Debit",           "fieldname": "debit",        "fieldtype": "Currency",      "options": "currency", "width": 120},
    {"label": "Credit",          "fieldname": "credit",       "fieldtype": "Currency",      "options": "currency", "width": 120},
    {"label": "Balance",         "fieldname": "balance",      "fieldtype": "Currency",      "options": "currency", "width": 130},
]
```

`currency` is sourced from `Company.default_currency` and attached to every
row dict.

**Hidden fields** carried in each row dict for the print format to consume but
not rendered as columns: `customer`, `customer_name`, `address_display`,
`mobile_no`, `is_group_header`, `is_opening`, `is_closing`, `voucher_type`.

The `report_summary` returned by `execute()` includes the grand totals
(total debit, total credit, net movement, final balance) when exactly one
customer is in the result.

## 7. Print Format

### 7.1 Print Format DocType Record

A Custom Print Format will be installed via a fixture or `after_install` hook:

```json
{
  "doctype": "Print Format",
  "name": "Party Statement",
  "doc_type": "",
  "print_format_type": "Jinja",
  "custom_format": 1,
  "standard": "No",
  "html": "<jinja template here>"
}
```

`doc_type` is blank because the print format is not bound to a single document
— it is rendered programmatically from the report context.

### 7.2 Layout

```
┌─────────────────────────────────────────────────┐
│              {{ company.company_name }}         │  bold, centered, 18pt
├─[red diagonal stripes 35% width]─[green stripes 35% width]─┤
│           Party Statement                       │  bold, centered, 14pt
├─────────────────────────────────────────────────┤
│ Period   : {{ from_date }}    {{ to_date }}     │
│ Party    : {{ customer_name }}                  │
│ Address  : {{ address_display }}                │
│ Mobile   : {{ mobile_no }}                      │
├─────────────────────────────────────────────────┤
│ Table with thin borders, right-aligned numbers  │
│ TRX Date │ TRX No │ Tran-Type │ TRX Amt │ ...   │
│ ... rows ...                                    │
└─────────────────────────────────────────────────┘
```

### 7.3 CSS

- **Red stripe bar** (left, 35% width): `linear-gradient(135deg, #d11 0, #d11 6px, transparent 6px, transparent 12px) repeat-x; height: 18px;`
- **Green stripe bar** (right, 35% width): same pattern with `#0a0`
- **A4 portrait**, `@page` margin 12mm
- Body font 9pt sans-serif
- Numeric columns right-aligned, header row bold with light-gray background
- Per-customer block wrapped in `<div class="customer-block">` with
  `page-break-after: always` (the last block omits the page-break)

All CSS lives inline inside the print format's `html` field (so it travels
with the print format and survives bench migrations).

## 8. Multi-Customer Bulk Print

### 8.1 JS Trigger

In `party_statement.js`, the report's `onload` hook adds a custom button:

```javascript
report.page.add_inner_button(__('Print Statement'), () => {
    frappe.call({
        method: 'kenz_report.api.party_statement.print_statement',
        args: { filters: report.get_values() },
        callback: (r) => {
            if (r.message && r.message.html) {
                const w = window.open();
                w.document.write(r.message.html);
                w.document.close();
                w.print();
            }
        }
    });
});
```

### 8.2 Server Endpoint

```python
@frappe.whitelist()
def print_statement(filters):
    filters = frappe.parse_json(filters)
    columns, data = execute(filters)
    blocks_by_customer = group_rows_by_customer(data)
    html_parts = []
    for customer, rows in blocks_by_customer.items():
        ctx = build_print_context(filters, customer, rows)
        html_parts.append(frappe.render_template(get_print_template(), ctx))
    html = '<div style="page-break-after:always"></div>'.join(html_parts)
    return {
        "html": wrap_with_styles(html),
        "filename": f"Party Statement {filters['from_date']} to {filters['to_date']}.pdf",
    }
```

`get_print_template()` reads the template body from the `Party Statement`
Print Format record. `wrap_with_styles()` wraps the concatenated HTML in
`<html><head><style>...</style></head><body>...</body></html>` for proper
PDF rendering.

## 9. Permissions

The Script Report is restricted to roles that already have access to customer
financial data:
- `Accounts Manager`
- `Accounts User`
- `Sales Manager`

Permissions are declared in `party_statement.json` under the `roles` array.

The bulk-print endpoint checks the same roles via
`frappe.only_for(["Accounts Manager", "Accounts User", "Sales Manager"])`.

## 10. Testing Strategy

`test_party_statement.py` (extends `FrappeTestCase`, uses ERPNext's standard
`_Test Customer`, `_Test Item`, `_Test Company` fixtures):

1. **`test_opening_balance_from_gl`** — submit a Sales Invoice dated before
   `from_date`; the opening balance row equals its `grand_total`.
2. **`test_sales_invoice_row`** — submit SI inside period; row has
   `tran_type='SALES'`, `debit=grand_total`, `credit=0`,
   `trx_amount=grand_total`.
3. **`test_sales_return_row`** — submit return SI (`is_return=1`,
   `return_against=...`); row has `tran_type='SALESRETURN'`,
   `credit=ABS(grand_total)`, `debit=0`.
4. **`test_payment_entry_row`** — submit PE referencing SI; assert PE row's
   `tran_type='RECEIPT'`, and the corresponding SI row's `paid_amount` equals
   the allocated amount.
5. **`test_journal_entry_against_receivable`** — submit JE touching the
   receivable account against the customer; row has `tran_type='JV'` with
   correct debit/credit.
6. **`test_running_balance`** — sequence of [SI, PE, SI, SalesReturn]; assert
   each row's `balance` is cumulative opening + sum(debit-credit so far).
7. **`test_closing_balance_row`** — assert the closing row's debit/credit are
   the period totals and balance equals the final running balance.
8. **`test_multi_customer_grouping`** — two customers; assert two separate
   blocks (group header + opening + transactions + closing), correctly
   ordered.
9. **`test_filter_customer_group`** — group filter narrows the result to
   members of that group only.
10. **`test_show_only_with_balance`** — customer with zero net activity is
    excluded when the flag is set.
11. **`test_date_range_validation`** — `from_date > to_date` raises
    `frappe.ValidationError`.
12. **`test_bulk_print_endpoint`** — call `print_statement` with two
    customers; assert the returned HTML contains both customer names and a
    page-break.

Tests run via `bench --site test_site run-tests --app kenz_report --module
kenz_report.kenz_report.report.party_statement.test_party_statement`.

## 11. Open Questions / Future Work

- **Aging buckets** — likely a separate report (Customer Aging) rather than
  added to this one.
- **Supplier mode** — when added, the union subqueries will be parameterized
  on `party_type` and source-doc set (Purchase Invoice / Purchase Return /
  Payment Entry payment_type='Pay'). The Print Format may be cloned or
  branched on party_type.
- **Email delivery** — bulk-email of the generated PDFs (one per customer) to
  each customer's primary contact is a likely follow-up; out of scope for
  this iteration.
- **Custom letterhead per company** — the red/green stripes are currently
  hardcoded in print-format CSS. If multiple companies need different brand
  colors, lift these into a `Party Statement Settings` doctype later.
