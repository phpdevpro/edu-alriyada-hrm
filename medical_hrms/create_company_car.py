import frappe

def execute():
    doctype_name = "Company Car Request"
    
    if frappe.db.exists("DocType", doctype_name):
        return

    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": doctype_name,
        "module": "Medical Hrms",
        "custom": 0,
        "autoname": "format:CCR-{YY}-{MM}-{#####}",
        "naming_rule": "Expression",
        "istable": 0,
        "editable_grid": 1,
        "track_changes": 1,
        "fields": [
            {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "reqd": 1, "in_list_view": 1},
            {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Read Only", "fetch_from": "employee.employee_name", "in_list_view": 1},
            {"fieldname": "business_justification", "label": "Business Justification", "fieldtype": "Text", "reqd": 1},
            {"fieldname": "client_visits_per_week", "label": "Avg Client/Site Visits per Week", "fieldtype": "Int", "reqd": 1},
            {"fieldname": "preferred_category", "label": "Preferred Vehicle Category", "fieldtype": "Select", "options": "Compact\nSedan\nSUV\nVan/Minibus", "default": "Compact"},
            {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Draft\nPending Manager\nPending Dept Head\nPending HR\nPending Finance\nApproved\nRejected", "default": "Draft", "in_list_view": 1}
        ]
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"DocType {doctype_name} created successfully.")
