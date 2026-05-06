import frappe

def execute():
    workspace_name = "Medical HRMS"
    if frappe.db.exists("Workspace", workspace_name):
        frappe.delete_doc("Workspace", workspace_name)

    doc = frappe.get_doc({
        "doctype": "Workspace",
        "name": workspace_name,
        "title": "Medical HRMS",
        "label": "Medical HRMS",
        "icon": "heart",
        "category": "Modules",
        "module": "Medical Hrms",
        "is_standard": 1,
        "public": 1,
        "roles": [
            {"role": "HR User"},
            {"role": "HR Manager"},
            {"role": "System Manager"}
        ],
        "sequence_id": 10.0,
        "links": [
            {"label": "Licenses & Compliance", "type": "Card Break"},
            {"label": "Employee Medical License", "type": "Link", "link_type": "DocType", "link_to": "Employee Medical License"},
            
            {"label": "Time & Attendance", "type": "Card Break"},
            {"label": "Permission Request", "type": "Link", "link_type": "DocType", "link_to": "Permission Request"},
            {"label": "Remote Work Request", "type": "Link", "link_type": "DocType", "link_to": "Remote Work Request"},
            {"label": "Return from Leave Request", "type": "Link", "link_type": "DocType", "link_to": "Return from Leave Request"},
            {"label": "Leave Plan Request", "type": "Link", "link_type": "DocType", "link_to": "Leave Plan Request"},
            
            {"label": "Financial & Admin", "type": "Card Break"},
            {"label": "Pre Approved Overtime Request", "type": "Link", "link_type": "DocType", "link_to": "Pre Approved Overtime Request"},
            {"label": "Salary Certificate Request", "type": "Link", "link_type": "DocType", "link_to": "Salary Certificate Request"},
            {"label": "Children Education Allowance Request", "type": "Link", "link_type": "DocType", "link_to": "Children Education Allowance Request"},
            {"label": "Company Car Request", "type": "Link", "link_type": "DocType", "link_to": "Company Car Request"},
            
            {"label": "Career & Updates", "type": "Card Break"},
            {"label": "Contract Renewal Request", "type": "Link", "link_type": "DocType", "link_to": "Contract Renewal Request"},
            {"label": "Employee Training Request", "type": "Link", "link_type": "DocType", "link_to": "Employee Training Request"},
            {"label": "Employee Data Update Request", "type": "Link", "link_type": "DocType", "link_to": "Employee Data Update Request"}
        ]
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print("Medical HRMS Workspace created successfully.")
