import frappe

def execute():
    # Link Employee to Instructor
    if not frappe.db.exists('Custom Field', 'Employee-custom_instructor'):
        custom_field = frappe.get_doc({
            'doctype': 'Custom Field',
            'dt': 'Employee',
            'fieldname': 'custom_instructor',
            'label': 'LMS Instructor',
            'fieldtype': 'Link',
            'options': 'Instructor',
            'insert_after': 'user_id'
        })
        custom_field.insert()
    
    # Commit changes
    frappe.db.commit()
