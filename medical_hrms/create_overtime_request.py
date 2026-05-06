import frappe

def execute():
    doctype_name = "Pre Approved Overtime Request"
    
    if frappe.db.exists("DocType", doctype_name):
        return

    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": doctype_name,
        "module": "Medical Hrms",
        "custom": 0,
        "autoname": "format:OT-{YY}-{MM}-{#####}",
        "naming_rule": "Expression",
        "istable": 0,
        "editable_grid": 1,
        "track_changes": 1,
        "fields": [
            {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "reqd": 1, "in_list_view": 1},
            {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Read Only", "fetch_from": "employee.employee_name", "in_list_view": 1},
            {"fieldname": "date", "label": "Planned OT Date", "fieldtype": "Date", "reqd": 1, "in_list_view": 1},
            {"fieldname": "ot_hours_requested", "label": "Estimated Hours", "fieldtype": "Float", "reqd": 1, "in_list_view": 1},
            {"fieldname": "ot_type", "label": "Overtime Type", "fieldtype": "Select", "options": "Regular (1.5x)\nHoliday/Weekend (2x)\nNight Shift Premium (+25%)", "reqd": 1},
            {"fieldname": "business_justification", "label": "Business Justification", "fieldtype": "Small Text", "reqd": 1},
            {"fieldname": "compensation_preference", "label": "Compensation Preference", "fieldtype": "Select", "options": "Overtime Pay\nTime Off in Lieu (Comp-Off)", "default": "Overtime Pay"},
            {"fieldname": "section_break_approval", "fieldtype": "Section Break", "label": "Approvals"},
            {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Draft\nPending Manager\nPending Dept Head\nApproved\nRejected", "default": "Draft", "in_list_view": 1}
        ]
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"DocType {doctype_name} created successfully.")
