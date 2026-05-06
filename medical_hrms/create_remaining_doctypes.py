import frappe

def execute():
    # 1. Leave Planning Request
    if not frappe.db.exists('DocType', 'Leave Plan Request'):
        doc1 = frappe.get_doc({
            'doctype': 'DocType', 'name': 'Leave Plan Request', 'module': 'Medical Hrms', 'custom': 0,
            'autoname': 'format:LPR-{YY}-{MM}-{#####}', 'naming_rule': 'Expression',
            'istable': 0, 'editable_grid': 1, 'track_changes': 1,
            'fields': [
                {'fieldname': 'employee', 'label': 'Employee', 'fieldtype': 'Link', 'options': 'Employee', 'reqd': 1, 'in_list_view': 1},
                {'fieldname': 'for_year', 'label': 'For Year', 'fieldtype': 'Data', 'reqd': 1},
                {'fieldname': 'planned_days', 'label': 'Total Planned Days', 'fieldtype': 'Int'},
                {'fieldname': 'status', 'label': 'Status', 'fieldtype': 'Select', 'options': 'Draft\nPending Manager\nPending Dept Head\nApproved\nRejected', 'default': 'Draft'}
            ]
        })
        doc1.insert(ignore_permissions=True)

    # 2. Contract Renewal Request
    if not frappe.db.exists('DocType', 'Contract Renewal Request'):
        doc2 = frappe.get_doc({
            'doctype': 'DocType', 'name': 'Contract Renewal Request', 'module': 'Medical Hrms', 'custom': 0,
            'autoname': 'format:CRR-{YY}-{MM}-{#####}', 'naming_rule': 'Expression',
            'istable': 0, 'editable_grid': 1, 'track_changes': 1,
            'fields': [
                {'fieldname': 'employee', 'label': 'Employee', 'fieldtype': 'Link', 'options': 'Employee', 'reqd': 1, 'in_list_view': 1},
                {'fieldname': 'current_contract_end', 'label': 'Current Expiry', 'fieldtype': 'Date', 'reqd': 1},
                {'fieldname': 'manager_recommendation', 'label': 'Recommendation', 'fieldtype': 'Select', 'options': 'Renew (Same Terms)\nRenew (Revised Terms)\nNon-Renewal', 'reqd': 1},
                {'fieldname': 'proposed_salary_increase', 'label': 'Proposed Salary Increase (%)', 'fieldtype': 'Percent'},
                {'fieldname': 'status', 'label': 'Status', 'fieldtype': 'Select', 'options': 'Draft\nPending Manager\nPending Dept Head\nPending HR\nPending VP\nApproved\nRejected', 'default': 'Draft'}
            ]
        })
        doc2.insert(ignore_permissions=True)

    # 3. Employee Data Update Request
    if not frappe.db.exists('DocType', 'Employee Data Update Request'):
        doc3 = frappe.get_doc({
            'doctype': 'DocType', 'name': 'Employee Data Update Request', 'module': 'Medical Hrms', 'custom': 0,
            'autoname': 'format:EDU-{YY}-{MM}-{#####}', 'naming_rule': 'Expression',
            'istable': 0, 'editable_grid': 1, 'track_changes': 1,
            'fields': [
                {'fieldname': 'employee', 'label': 'Employee', 'fieldtype': 'Link', 'options': 'Employee', 'reqd': 1, 'in_list_view': 1},
                {'fieldname': 'update_type', 'label': 'Update Type', 'fieldtype': 'Select', 'options': 'Name Spelling\nAddress\nEmergency Contact\nMarital Status', 'reqd': 1},
                {'fieldname': 'new_value', 'label': 'New Value / Details', 'fieldtype': 'Text', 'reqd': 1},
                {'fieldname': 'supporting_document', 'label': 'Supporting Document (ID/Certificate)', 'fieldtype': 'Attach'},
                {'fieldname': 'status', 'label': 'Status', 'fieldtype': 'Select', 'options': 'Draft\nPending Manager Acknowledgment\nPending HR Verification\nIT Updated\nCompleted', 'default': 'Draft'}
            ]
        })
        doc3.insert(ignore_permissions=True)

    frappe.db.commit()
    print('Remaining Doctypes created successfully.')
