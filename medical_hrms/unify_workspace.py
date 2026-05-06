import frappe

def execute():
    workspace = frappe.get_doc('Workspace', 'Medical HRMS')
    
    workspace.content = '''[
        {
            "id": "block_ta_head",
            "type": "header",
            "data": {"text": "1. Time & Attendance", "level": 4}
        },
        {
            "id": "block_ta_1",
            "type": "shortcut",
            "data": {"shortcut_name": "Leave Application", "col": 3}
        },
        {
            "id": "block_ta_2",
            "type": "shortcut",
            "data": {"shortcut_name": "Permission Request", "col": 3}
        },
        {
            "id": "block_ta_3",
            "type": "shortcut",
            "data": {"shortcut_name": "Remote Work Request", "col": 3}
        },
        {
            "id": "block_ta_4",
            "type": "shortcut",
            "data": {"shortcut_name": "Return from Leave Request", "col": 3}
        },
        {
            "id": "block_ta_5",
            "type": "shortcut",
            "data": {"shortcut_name": "Leave Plan Request", "col": 3}
        },
        {
            "id": "block_ta_6",
            "type": "shortcut",
            "data": {"shortcut_name": "Attendance Request", "col": 3}
        },
        
        {
            "id": "block_fa_head",
            "type": "header",
            "data": {"text": "2. Financial & Admin", "level": 4}
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
            "data": {"shortcut_name": "Pre Approved Overtime Request", "col": 3}
        },
        {
            "id": "block_fa_4",
            "type": "shortcut",
            "data": {"shortcut_name": "Salary Certificate Request", "col": 3}
        },
        {
            "id": "block_fa_5",
            "type": "shortcut",
            "data": {"shortcut_name": "Children Education Allowance Request", "col": 4}
        },
        {
            "id": "block_fa_6",
            "type": "shortcut",
            "data": {"shortcut_name": "Company Car Request", "col": 3}
        },
        
        {
            "id": "block_cu_head",
            "type": "header",
            "data": {"text": "3. Career & Updates", "level": 4}
        },
        {
            "id": "block_cu_1",
            "type": "shortcut",
            "data": {"shortcut_name": "Employee Separation", "col": 3}
        },
        {
            "id": "block_cu_2",
            "type": "shortcut",
            "data": {"shortcut_name": "Full and Final Statement", "col": 3}
        },
        {
            "id": "block_cu_3",
            "type": "shortcut",
            "data": {"shortcut_name": "Contract Renewal Request", "col": 3}
        },
        {
            "id": "block_cu_4",
            "type": "shortcut",
            "data": {"shortcut_name": "Employee Training Request", "col": 3}
        },
        {
            "id": "block_cu_5",
            "type": "shortcut",
            "data": {"shortcut_name": "Employee Data Update Request", "col": 4}
        },
        
        {
            "id": "block_mc_head",
            "type": "header",
            "data": {"text": "4. Medical Compliance (Hospital)", "level": 4}
        },
        {
            "id": "block_mc_1",
            "type": "shortcut",
            "data": {"shortcut_name": "Employee Medical License", "col": 4}
        }
    ]'''

    workspace.save(ignore_permissions=True)
    frappe.db.commit()
    print("Unified Workspace Content Updated")
