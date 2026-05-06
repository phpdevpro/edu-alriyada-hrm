import frappe

def execute():
    doctype_name = "Employee Medical License"
    
    if frappe.db.exists("DocType", doctype_name):
        print(f"DocType {doctype_name} already exists.")
        return

    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": doctype_name,
        "module": "Medical Hrms",
        "custom": 0,
        "autoname": "format:EML-{YY}-{MM}-{#####}",
        "naming_rule": "Expression",
        "istable": 0,
        "editable_grid": 1,
        "track_changes": 1,
        "fields": [
            {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "reqd": 1, "in_list_view": 1},
            {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Read Only", "fetch_from": "employee.employee_name", "in_list_view": 1},
            {"fieldname": "column_break_1", "fieldtype": "Column Break"},
            {"fieldname": "license_type", "label": "License Type", "fieldtype": "Select", "options": "\nMedical Board Registration\nNursing License\nPharmacy License\nSpecialty Board Certification\nBLS/ACLS/PALS Certification\nOther", "reqd": 1, "in_list_view": 1},
            {"fieldname": "license_number", "label": "License/Registration Number", "fieldtype": "Data", "reqd": 1},
            
            {"fieldname": "section_break_1", "fieldtype": "Section Break", "label": "Validity Details"},
            {"fieldname": "issuing_authority", "label": "Issuing Authority / State Board", "fieldtype": "Data"},
            {"fieldname": "issue_date", "label": "Issue Date", "fieldtype": "Date"},
            {"fieldname": "column_break_2", "fieldtype": "Column Break"},
            {"fieldname": "expiry_date", "label": "Expiry Date", "fieldtype": "Date", "reqd": 1, "in_list_view": 1},
            {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Active\nExpired\nSuspended\nRevoked", "default": "Active", "in_list_view": 1},
            
            {"fieldname": "section_break_2", "fieldtype": "Section Break", "label": "Documentation"},
            {"fieldname": "license_document", "label": "License Copy / Certificate", "fieldtype": "Attach"},
            {"fieldname": "notes", "label": "Notes / Conditions", "fieldtype": "Text"}
        ],
        "permissions": [
            {"role": "HR Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
            {"role": "HR User", "read": 1, "write": 1, "create": 1},
            {"role": "Employee", "read": 1}
        ]
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"DocType {doctype_name} created successfully.")
