import frappe

def execute():
    doctype_name = "Return from Leave Request"
    
    if frappe.db.exists("DocType", doctype_name):
        return

    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": doctype_name,
        "module": "Medical Hrms",
        "custom": 0,
        "autoname": "format:RLR-{YY}-{MM}-{#####}",
        "naming_rule": "Expression",
        "istable": 0,
        "editable_grid": 1,
        "track_changes": 1,
        "fields": [
            {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "reqd": 1, "in_list_view": 1},
            {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Read Only", "fetch_from": "employee.employee_name", "in_list_view": 1},
            {"fieldname": "leave_application", "label": "Leave Application", "fieldtype": "Link", "options": "Leave Application", "reqd": 1},
            {"fieldname": "planned_return_date", "label": "Planned Return Date", "fieldtype": "Date", "read_only": 1, "fetch_from": "leave_application.to_date"},
            {"fieldname": "actual_return_date", "label": "Actual Return Date", "fieldtype": "Date", "reqd": 1, "in_list_view": 1},
            {"fieldname": "section_break_medical", "fieldtype": "Section Break", "label": "Medical / Fitness Clearance"},
            {"fieldname": "fitness_certificate", "label": "Fitness Certificate", "fieldtype": "Attach"},
            {"fieldname": "occupational_health_clearance", "label": "Occupational Health Clearance", "fieldtype": "Select", "options": "Not Required\nPending\nCleared for Full Duty\nCleared for Modified Duty\nNot Cleared"},
            {"fieldname": "section_break_status", "fieldtype": "Section Break", "label": "Workflow Status"},
            {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Draft\nPending HR Review\nPending Manager Readiness\nPending Occupational Health\nCompleted", "default": "Draft", "in_list_view": 1}
        ]
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"DocType {doctype_name} created successfully.")
