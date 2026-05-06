import frappe


REQUEST_DOCTYPES = [
    "Employee Data Update Request",
    "Contract Renewal Request",
    "Leave Plan Request",
    "Employee Training Request",
    "Company Car Request",
    "Children Education Allowance Request",
    "Salary Certificate Request",
    "Pre Approved Overtime Request",
    "Return From Leave Request",
    "Remote Work Request",
    "Permission Request",
    "Employee Medical License",
]


BASE_PERMISSIONS = [
    {
        "role": "Employee",
        "permlevel": 0,
        "read": 1,
        "write": 1,
        "create": 1,
        "delete": 0,
        "submit": 0,
        "cancel": 0,
        "amend": 0,
        "print": 1,
        "email": 1,
        "report": 1,
        "export": 0,
        "share": 0,
    },
    {
        "role": "HR User",
        "permlevel": 0,
        "read": 1,
        "write": 1,
        "create": 1,
        "delete": 0,
        "submit": 0,
        "cancel": 0,
        "amend": 0,
        "print": 1,
        "email": 1,
        "report": 1,
        "export": 1,
        "share": 1,
    },
    {
        "role": "HR Manager",
        "permlevel": 0,
        "read": 1,
        "write": 1,
        "create": 1,
        "delete": 1,
        "submit": 0,
        "cancel": 0,
        "amend": 0,
        "print": 1,
        "email": 1,
        "report": 1,
        "export": 1,
        "share": 1,
    },
    {
        "role": "System Manager",
        "permlevel": 0,
        "read": 1,
        "write": 1,
        "create": 1,
        "delete": 1,
        "submit": 0,
        "cancel": 0,
        "amend": 0,
        "print": 1,
        "email": 1,
        "report": 1,
        "export": 1,
        "share": 1,
    },
]


FINANCE_PERMISSION = {
    "role": "Accounts Manager",
    "permlevel": 0,
    "read": 1,
    "write": 1,
    "create": 0,
    "delete": 0,
    "submit": 0,
    "cancel": 0,
    "amend": 0,
    "print": 1,
    "email": 1,
    "report": 1,
    "export": 1,
    "share": 0,
}


FINANCE_DOCTYPES = {
    "Employee Training Request",
    "Company Car Request",
    "Children Education Allowance Request",
    "Pre Approved Overtime Request",
}


def _apply_permissions(doctype_name: str):
    dt = frappe.get_doc("DocType", doctype_name)
    dt.set("permissions", [])

    for row in BASE_PERMISSIONS:
        dt.append("permissions", row)

    if doctype_name in FINANCE_DOCTYPES:
        dt.append("permissions", FINANCE_PERMISSION)

    dt.save(ignore_permissions=True)
    print(f"Updated permissions: {doctype_name}")


def execute():
    for doctype_name in REQUEST_DOCTYPES:
        if frappe.db.exists("DocType", doctype_name):
            _apply_permissions(doctype_name)
        else:
            print(f"Skipped missing doctype: {doctype_name}")

    frappe.db.commit()
    print("HRM request governance permissions applied.")
