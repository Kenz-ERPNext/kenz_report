import frappe

from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import (
    execute as standard_execute,
)


def execute(filters=None):

    result = standard_execute(filters)

    columns = result[0]
    data = result[1]

    columns.insert(
        2,
        {
            "label": "Customer Name",
            "fieldname": "customer_name",
            "fieldtype": "Data",
            "width": 200,
        },
    )

    customer_map = dict(
        frappe.get_all(
            "Customer",
            fields=["name", "customer_name"],
            as_list=True,
        )
    )

    for row in data:
        if isinstance(row, dict):
            row["customer_name"] = customer_map.get(row.get("party"), "")

    return columns, data