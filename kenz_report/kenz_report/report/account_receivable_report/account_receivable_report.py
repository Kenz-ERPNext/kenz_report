import frappe

from erpnext.accounts.report.accounts_receivable.accounts_receivable import (
    execute as standard_execute
)


def execute(filters=None):

    result = standard_execute(filters)

    columns = result[0]
    data = result[1]

    # Add Customer Name column after Customer
    columns.insert(
        3,
        {
            "label": "Customer Name",
            "fieldname": "customer_name",
            "fieldtype": "Data",
            "width": 180,
        }
    )


    for row in data:

        if row.get("party"):

            row["customer_name"] = frappe.db.get_value(
                "Customer",
                row.party,
                "customer_name"
            )

        else:
            row["customer_name"] = ""


    return (
        columns,
        data,
        *result[2:]
    )