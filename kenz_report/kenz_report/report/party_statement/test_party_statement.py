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
