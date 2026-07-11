import frappe

from erpnext.accounts.report.general_ledger.general_ledger import (
    execute as general_ledger_execute
)

def execute(filters=None):
    result = general_ledger_execute(filters)

    columns = result[0]
    data = result[1]

    hide_columns = [
        "account",
        "currency",
        "voucher_subtype",
        "cost_center",
        "project",
        "against_voucher",
        "against_voucher_type",
        "against",
        "bill_no",
        
    ]

    columns = [
        c for c in columns
        if c.get("fieldname") not in hide_columns
    ]

    return (
        columns,
        data,
        *result[2:]
    )