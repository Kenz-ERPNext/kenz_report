from erpnext.accounts.report.purchase_register.purchase_register import (
    execute as purchase_register_execute
)

def execute(filters=None):
    result = purchase_register_execute(filters)

    columns = result[0]
    data = result[1]

    hide_columns = [
        # Add fieldnames you don't want
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