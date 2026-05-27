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
