import frappe

def execute():
    doctype_name = "Permission Request"
    
    if frappe.db.exists("DocType", doctype_name):
        return

    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": doctype_name,
        "module": "Medical Hrms",
        "custom": 0,
        "autoname": "format:PR-{YY}-{MM}-{#####}",
        "naming_rule": "Expression",
        "istable": 0,
        "editable_grid": 1,
        "track_changes": 1,
        "fields": [
            {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "reqd": 1, "in_list_view": 1},
            {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Read Only", "fetch_from": "employee.employee_name", "in_list_view": 1},
            {"fieldname": "date", "label": "Date", "fieldtype": "Date", "reqd": 1, "in_list_view": 1},
            {"fieldname": "from_time", "label": "From Time", "fieldtype": "Time", "reqd": 1},
            {"fieldname": "to_time", "label": "To Time", "fieldtype": "Time", "reqd": 1},
            {"fieldname": "duration_hours", "label": "Duration (Hours)", "fieldtype": "Float", "read_only": 1},
            {"fieldname": "reason", "label": "Reason", "fieldtype": "Small Text", "reqd": 1},
            {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Draft\nPending\nApproved\nRejected", "default": "Draft", "in_list_view": 1}
        ]
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"DocType {doctype_name} created successfully.")
