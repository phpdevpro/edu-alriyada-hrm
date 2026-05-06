import frappe

def execute():
    doctype_name = "Remote Work Request"
    
    if frappe.db.exists("DocType", doctype_name):
        return

    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": doctype_name,
        "module": "Medical Hrms",
        "custom": 0,
        "autoname": "format:RWR-{YY}-{MM}-{#####}",
        "naming_rule": "Expression",
        "istable": 0,
        "editable_grid": 1,
        "track_changes": 1,
        "fields": [
            {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "reqd": 1, "in_list_view": 1},
            {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Read Only", "fetch_from": "employee.employee_name", "in_list_view": 1},
            {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date", "reqd": 1},
            {"fieldname": "to_date", "label": "To Date", "fieldtype": "Date", "reqd": 1},
            {"fieldname": "duration", "label": "Duration (Days)", "fieldtype": "Int", "read_only": 1},
            {"fieldname": "work_plan", "label": "Work Plan/Deliverables", "fieldtype": "Text", "reqd": 1},
            {"fieldname": "location", "label": "Remote Location", "fieldtype": "Data", "reqd": 1},
            {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Draft\nPending Manager\nPending Dept Head\nApproved\nRejected", "default": "Draft", "in_list_view": 1}
        ]
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"DocType {doctype_name} created successfully.")
