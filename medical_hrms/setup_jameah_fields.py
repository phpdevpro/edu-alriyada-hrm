import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def add_jameah_fields():
    # Define common fields to be added to both Employee and Instructor
    jameah_fields = [
        {
            "fieldname": "custom_jameah_demographics",
            "label": "Demographics",
            "fieldtype": "Section Break",
            "insert_after": "employee_name" # For employee, will adjust for instructor below if needed
        },
        {
            "fieldname": "custom_first_name_en",
            "label": "First Name (English)",
            "fieldtype": "Data",
            "insert_after": "custom_jameah_demographics"
        },
        {
            "fieldname": "custom_second_name_en",
            "label": "Second Name (English)",
            "fieldtype": "Data",
            "insert_after": "custom_first_name_en"
        },
        {
            "fieldname": "custom_third_name_en",
            "label": "Third Name (English)",
            "fieldtype": "Data",
            "insert_after": "custom_second_name_en"
        },
        {
            "fieldname": "custom_last_name_en",
            "label": "Last Name (English)",
            "fieldtype": "Data",
            "insert_after": "custom_third_name_en"
        },
        {
            "fieldname": "custom_arabic_names_col",
            "fieldtype": "Column Break",
            "insert_after": "custom_last_name_en"
        },
        {
            "fieldname": "custom_first_name_ar",
            "label": "First Name (Arabic)",
            "fieldtype": "Data",
            "insert_after": "custom_arabic_names_col"
        },
        {
            "fieldname": "custom_second_name_ar",
            "label": "Second Name (Arabic)",
            "fieldtype": "Data",
            "insert_after": "custom_first_name_ar"
        },
        {
            "fieldname": "custom_third_name_ar",
            "label": "Third Name (Arabic)",
            "fieldtype": "Data",
            "insert_after": "custom_second_name_ar"
        },
        {
            "fieldname": "custom_last_name_ar",
            "label": "Last Name (Arabic)",
            "fieldtype": "Data",
            "insert_after": "custom_third_name_ar"
        },
        {
            "fieldname": "custom_jameah_identity",
            "label": "Identity Details",
            "fieldtype": "Section Break",
            "insert_after": "custom_last_name_ar"
        },
        {
            "fieldname": "custom_identity_type",
            "label": "Identity Type",
            "fieldtype": "Link",
            "options": "Jameah Ministry Code",
            "insert_after": "custom_jameah_identity"
        },
        {
            "fieldname": "custom_identity_number",
            "label": "Identity Number",
            "fieldtype": "Data",
            "insert_after": "custom_identity_type"
        },
        {
            "fieldname": "custom_identity_issue_date",
            "label": "Identity Issue Date",
            "fieldtype": "Date",
            "insert_after": "custom_identity_number"
        },
        {
            "fieldname": "custom_identity_issue_place",
            "label": "Identity Issue Place",
            "fieldtype": "Link",
            "options": "Jameah Ministry Code",
            "insert_after": "custom_identity_issue_date"
        },
        {
            "fieldname": "custom_jameah_nationality",
            "label": "Nationality",
            "fieldtype": "Link",
            "options": "Jameah Ministry Code",
            "insert_after": "custom_identity_issue_place"
        }
    ]

    custom_fields = {
        "Employee": jameah_fields,
        "Instructor": [dict(f, insert_after="instructor_name" if f["fieldname"] == "custom_jameah_demographics" else f["insert_after"]) for f in jameah_fields]
    }

    create_custom_fields(custom_fields, update=True)
    print("Injected Jameah fields into Employee and Instructor Doctypes.")

def execute():
    add_jameah_fields()
    frappe.db.commit()
