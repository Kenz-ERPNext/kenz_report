# Copyright (c) 2026, sammish and contributors
# For license information, please see license.txt

import frappe


from erpnext.accounts.report.sales_register.sales_register import execute as sales_register_execute

def execute(filters=None):
    result = sales_register_execute(filters)

    columns = result[0]
    data = result[1]

    # Columns you don't want to show
    hide_columns = [
        "owner",
        "warehouse",
        "customer_group",
        "territory",
        "cost_center",
        "remarks",
        "sales_order",
        "delivery_note",
        "project",
        "mode_of_payment",
        "receivable_account",
        "currency",
    ]

    columns = [c for c in columns if c.get("fieldname") not in hide_columns]

    return (
        columns,
        data,
        *result[2:]   # Preserve the remaining return values
    )