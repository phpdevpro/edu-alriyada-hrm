import frappe

def execute():
    doctype_name = "Salary Certificate Request"
    
    if frappe.db.exists("DocType", doctype_name):
        return

    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": doctype_name,
        "module": "Medical Hrms",
        "custom": 0,
        "autoname": "format:SCR-{YY}-{MM}-{#####}",
        "naming_rule": "Expression",
        "istable": 0,
        "editable_grid": 1,
        "track_changes": 1,
        "fields": [
            {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "reqd": 1, "in_list_view": 1},
            {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Read Only", "fetch_from": "employee.employee_name", "in_list_view": 1},
            {"fieldname": "purpose", "label": "Purpose", "fieldtype": "Select", "options": "Bank Loan\nVisa Application\nRental Agreement\nEmbassy\nOther", "reqd": 1, "in_list_view": 1},
            {"fieldname": "language_preference", "label": "Language", "fieldtype": "Select", "options": "English\nArabic\nBilingual", "default": "English"},
            {"fieldname": "addressee", "label": "Addressee (To Whom)", "fieldtype": "Data", "default": "To Whom It May Concern", "reqd": 1},
            {"fieldname": "include_salary_breakdown", "label": "Include Salary Breakdown?", "fieldtype": "Check", "default": 0, "description": "Checked = include basic + allowances. Unchecked = grand total only."},
            {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Draft\nPending Manager\nPending HR\nIssued\nRejected", "default": "Draft", "in_list_view": 1}
        ]
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"DocType {doctype_name} created successfully.")
