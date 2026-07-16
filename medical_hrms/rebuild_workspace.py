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
        "content": '''[
            {
                "id": "block_intro_head",
                "type": "header",
                "data": {"text": "Medical HRMS - Administration Panel", "level": 2}
            },
            {
                "id": "block_intro_desc",
                "type": "paragraph",
                "data": {"text": "Centralized HR hub for employee services, approvals, compliance, and HR-finance handoffs."}
            },

            {
                "id": "block_es_head",
                "type": "header",
                "data": {"text": "1. Employee Services", "level": 4}
            },
            {
                "id": "block_es_1",
                "type": "shortcut",
                "data": {"shortcut_name": "Permission Request", "col": 3}
            },
            {
                "id": "block_es_2",
                "type": "shortcut",
                "data": {"shortcut_name": "Remote Work Request", "col": 3}
            },
            {
                "id": "block_es_3",
                "type": "shortcut",
                "data": {"shortcut_name": "Leave Plan Request", "col": 3}
            },
            {
                "id": "block_es_4",
                "type": "shortcut",
                "data": {"shortcut_name": "Return from Leave Request", "col": 3}
            },
            {
                "id": "block_es_5",
                "type": "shortcut",
                "data": {"shortcut_name": "Salary Certificate Request", "col": 3}
            },

            {
                "id": "block_ta_head",
                "type": "header",
                "data": {"text": "2. Time & Attendance", "level": 4}
            },
            {
                "id": "block_ta_1",
                "type": "shortcut",
                "data": {"shortcut_name": "Leave Application", "col": 3}
            },
            {
                "id": "block_ta_2",
                "type": "shortcut",
                "data": {"shortcut_name": "Attendance Request", "col": 3}
            },
            {
                "id": "block_ta_3",
                "type": "shortcut",
                "data": {"shortcut_name": "Pre Approved Overtime Request", "col": 3}
            },

            {
                "id": "block_fa_head",
                "type": "header",
                "data": {"text": "3. Financial & Admin", "level": 4}
            },
            {
                "id": "block_fa_1",
                "type": "shortcut",
                "data": {"shortcut_name": "Expense Claim", "col": 3}
            },
            {
                "id": "block_fa_2",
                "type": "shortcut",
                "data": {"shortcut_name": "Travel Request", "col": 3}
            },
            {
                "id": "block_fa_3",
                "type": "shortcut",
                "data": {"shortcut_name": "Children Medical Allowance Request", "col": 3}
            },
            {
                "id": "block_fa_4",
                "type": "shortcut",
                "data": {"shortcut_name": "Company Car Request", "col": 3}
            },

            {
                "id": "block_cu_head",
                "type": "header",
                "data": {"text": "4. Career & Compliance", "level": 4}
            },
            {
                "id": "block_cu_1",
                "type": "shortcut",
                "data": {"shortcut_name": "Contract Renewal Request", "col": 3}
            },
            {
                "id": "block_cu_2",
                "type": "shortcut",
                "data": {"shortcut_name": "Employee Training Request", "col": 3}
            },
            {
                "id": "block_cu_1",
                "type": "shortcut",
                "data": {"shortcut_name": "Employee Separation", "col": 3}
            },
            {
                "id": "block_cu_3",
                "type": "shortcut",
                "data": {"shortcut_name": "Full and Final Statement", "col": 3}
            },
            {
                "id": "block_cu_4",
                "type": "shortcut",
                "data": {"shortcut_name": "Employee Data Update Request", "col": 3}
            },
            {
                "id": "block_cu_5",
                "type": "shortcut",
                "data": {"shortcut_name": "Employee Medical License", "col": 3}
            },

            {
                "id": "block_md_head",
                "type": "header",
                "data": {"text": "5. Jameah Master Data", "level": 4}
            },
            {
                "id": "block_md_1",
                "type": "shortcut",
                "data": {"shortcut_name": "Jameah Ministry Code", "col": 3}
            },
            {
                "id": "block_md_2",
                "type": "shortcut",
                "data": {"shortcut_name": "Jameah Branch", "col": 3}
            },
            {
                "id": "block_md_3",
                "type": "shortcut",
                "data": {"shortcut_name": "Jameah Agency", "col": 3}
            },
            {
                "id": "block_md_4",
                "type": "shortcut",
                "data": {"shortcut_name": "Jameah Deanery", "col": 3}
            },
            {
                "id": "block_md_5",
                "type": "shortcut",
                "data": {"shortcut_name": "Jameah College", "col": 3}
            },
            {
                "id": "block_md_6",
                "type": "shortcut",
                "data": {"shortcut_name": "Jameah Academic Department", "col": 3}
            },
            {
                "id": "block_md_7",
                "type": "shortcut",
                "data": {"shortcut_name": "Jameah Facility", "col": 3}
            }
        ]''',
        "shortcuts": [
            {"label": "Leave Application", "type": "DocType", "link_to": "Leave Application"},
            {"label": "Permission Request", "type": "DocType", "link_to": "Permission Request"},
            {"label": "Remote Work Request", "type": "DocType", "link_to": "Remote Work Request"},
            {"label": "Return from Leave Request", "type": "DocType", "link_to": "Return from Leave Request"},
            {"label": "Leave Plan Request", "type": "DocType", "link_to": "Leave Plan Request"},
            {"label": "Attendance Request", "type": "DocType", "link_to": "Attendance Request"},
            
            {"label": "Expense Claim", "type": "DocType", "link_to": "Expense Claim"},
            {"label": "Travel Request", "type": "DocType", "link_to": "Travel Request"},
            {"label": "Pre Approved Overtime Request", "type": "DocType", "link_to": "Pre Approved Overtime Request"},
            {"label": "Salary Certificate Request", "type": "DocType", "link_to": "Salary Certificate Request"},
            {"label": "Children Medical Allowance Request", "type": "DocType", "link_to": "Children Medical Allowance Request"},
            {"label": "Company Car Request", "type": "DocType", "link_to": "Company Car Request"},
            
            {"label": "Employee Separation", "type": "DocType", "link_to": "Employee Separation"},
            {"label": "Full and Final Statement", "type": "DocType", "link_to": "Full and Final Statement"},
            {"label": "Contract Renewal Request", "type": "DocType", "link_to": "Contract Renewal Request"},
            {"label": "Employee Training Request", "type": "DocType", "link_to": "Employee Training Request"},
            {"label": "Employee Data Update Request", "type": "DocType", "link_to": "Employee Data Update Request"},

            {"label": "Employee Medical License", "type": "DocType", "link_to": "Employee Medical License"},
            {"label": "Jameah Ministry Code", "type": "DocType", "link_to": "Jameah Ministry Code"},
            {"label": "Jameah Branch", "type": "DocType", "link_to": "Jameah Branch"},
            {"label": "Jameah Agency", "type": "DocType", "link_to": "Jameah Agency"},
            {"label": "Jameah Deanery", "type": "DocType", "link_to": "Jameah Deanery"},
            {"label": "Jameah College", "type": "DocType", "link_to": "Jameah College"},
            {"label": "Jameah Academic Department", "type": "DocType", "link_to": "Jameah Academic Department"},
            {"label": "Jameah Facility", "type": "DocType", "link_to": "Jameah Facility"}
        ]
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print("Workspace Re-created successfully with correct shortcut mappings.")
