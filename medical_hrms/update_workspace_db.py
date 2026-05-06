import frappe

def execute():
    workspace = frappe.get_doc('Workspace', 'Medical HRMS')
    
    workspace.content = '''[
        {
            "id": "block1",
            "type": "header",
            "data": {"text": "Licenses and Compliance", "level": 4}
        },
        {
            "id": "block2",
            "type": "shortcut",
            "data": {"shortcut_name": "Employee Medical License", "col": 4}
        },
        {
            "id": "block3",
            "type": "header",
            "data": {"text": "Time and Attendance", "level": 4}
        },
        {
            "id": "block4",
            "type": "shortcut",
            "data": {"shortcut_name": "Permission Request", "col": 3}
        },
        {
            "id": "block5",
            "type": "shortcut",
            "data": {"shortcut_name": "Return from Leave Request", "col": 3}
        },
        {
            "id": "block6",
            "type": "shortcut",
            "data": {"shortcut_name": "Remote Work Request", "col": 3}
        },
        {
            "id": "block7",
            "type": "shortcut",
            "data": {"shortcut_name": "Leave Plan Request", "col": 3}
        },
        {
            "id": "block8",
            "type": "header",
            "data": {"text": "Financial and Admin", "level": 4}
        },
        {
            "id": "block9",
            "type": "shortcut",
            "data": {"shortcut_name": "Pre Approved Overtime Request", "col": 3}
        },
        {
            "id": "block10",
            "type": "shortcut",
            "data": {"shortcut_name": "Salary Certificate Request", "col": 3}
        },
        {
            "id": "block11",
            "type": "shortcut",
            "data": {"shortcut_name": "Children Education Allowance Request", "col": 3}
        },
        {
            "id": "block12",
            "type": "shortcut",
            "data": {"shortcut_name": "Company Car Request", "col": 3}
        },
        {
            "id": "block13",
            "type": "header",
            "data": {"text": "Career and Updates", "level": 4}
        },
        {
            "id": "block14",
            "type": "shortcut",
            "data": {"shortcut_name": "Contract Renewal Request", "col": 4}
        },
        {
            "id": "block15",
            "type": "shortcut",
            "data": {"shortcut_name": "Employee Training Request", "col": 4}
        },
        {
            "id": "block16",
            "type": "shortcut",
            "data": {"shortcut_name": "Employee Data Update Request", "col": 4}
        }
    ]'''

    workspace.is_standard = 1
    workspace.public = 1
    workspace.flags.ignore_permissions = True
    workspace.save(ignore_permissions=True)
    frappe.db.commit()
    print("Workspace Content Updated for V15")
