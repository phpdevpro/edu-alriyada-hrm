import frappe

def execute():
    doctype_name = "Children Medical Allowance Request"
    
    if frappe.db.exists("DocType", doctype_name):
        return

    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": doctype_name,
        "module": "Medical Hrms",
        "custom": 0,
        "autoname": "format:CEA-{YY}-{MM}-{#####}",
        "naming_rule": "Expression",
        "istable": 0,
        "editable_grid": 1,
        "track_changes": 1,
        "fields": [
            {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "reqd": 1, "in_list_view": 1},
            {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Read Only", "fetch_from": "employee.employee_name", "in_list_view": 1},
            {"fieldname": "child_name", "label": "Child's Name", "fieldtype": "Data", "reqd": 1, "in_list_view": 1},
            {"fieldname": "school_name", "label": "School/Institution", "fieldtype": "Data", "reqd": 1},
            {"fieldname": "academic_year", "label": "Academic Year", "fieldtype": "Select", "options": "2025-2026\n2026-2027\n2027-2028", "reqd": 1},
            {"fieldname": "fee_amount_requested", "label": "Total Fee Amount on Invoice", "fieldtype": "Currency", "reqd": 1, "in_list_view": 1},
            {"fieldname": "approved_amount", "label": "Approved Amount (Subject to Cap)", "fieldtype": "Currency", "read_only": 1, "description": "HR calculates based on Grade cap."},
            {"fieldname": "payment_preference", "label": "Payment Preference", "fieldtype": "Select", "options": "Direct to School\nReimbursement to Employee", "reqd": 1},
            {"fieldname": "invoice_attachment", "label": "Upload Fee Invoice", "fieldtype": "Attach", "reqd": 1},
            {"fieldname": "birth_certificate", "label": "Child Birth Certificate", "fieldtype": "Attach"},
            {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Draft\nPending HR Review\nPending HR Director\nPending Finance\nApproved\nRejected", "default": "Draft", "in_list_view": 1}
        ]
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"DocType {doctype_name} created successfully.")
