import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def create_institute_doctypes():
    doctypes = [
        {
            "name": "Jameah Branch",
            "autoname_field": "branch_name_en",
            "fields": [
                {"fieldname": "branch_name_en", "fieldtype": "Data", "label": "Branch Name (English)", "reqd": 1, "in_list_view": 1},
                {"fieldname": "branch_name_ar", "fieldtype": "Data", "label": "Branch Name (Arabic)", "reqd": 1, "in_list_view": 1},
                {"fieldname": "ministry_code", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Ministry Code", "in_list_view": 1}
            ]
        },
        {
            "name": "Jameah Agency",
            "autoname_field": "agency_name_en",
            "fields": [
                {"fieldname": "agency_name_en", "fieldtype": "Data", "label": "Agency Name (English)", "reqd": 1, "in_list_view": 1},
                {"fieldname": "agency_name_ar", "fieldtype": "Data", "label": "Agency Name (Arabic)", "reqd": 1, "in_list_view": 1},
                {"fieldname": "branch", "fieldtype": "Link", "options": "Jameah Branch", "label": "Branch", "in_list_view": 1},
                {"fieldname": "ministry_code", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Ministry Code"}
            ]
        },
        {
            "name": "Jameah Deanery",
            "autoname_field": "deanery_name_en",
            "fields": [
                {"fieldname": "deanery_name_en", "fieldtype": "Data", "label": "Deanery Name (English)", "reqd": 1, "in_list_view": 1},
                {"fieldname": "deanery_name_ar", "fieldtype": "Data", "label": "Deanery Name (Arabic)", "reqd": 1, "in_list_view": 1},
                {"fieldname": "agency", "fieldtype": "Link", "options": "Jameah Agency", "label": "Parent Agency", "in_list_view": 1},
                {"fieldname": "ministry_code", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Ministry Code"}
            ]
        },
        {
            "name": "Jameah College",
            "autoname_field": "college_name_en",
            "fields": [
                {"fieldname": "college_name_en", "fieldtype": "Data", "label": "College Name (English)", "reqd": 1, "in_list_view": 1},
                {"fieldname": "college_name_ar", "fieldtype": "Data", "label": "College Name (Arabic)", "reqd": 1, "in_list_view": 1},
                {"fieldname": "branch", "fieldtype": "Link", "options": "Jameah Branch", "label": "Branch", "in_list_view": 1},
                {"fieldname": "ministry_code", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Ministry Code"}
            ]
        },
        {
            "name": "Jameah Academic Department",
            "autoname_field": "department_name_en",
            "fields": [
                {"fieldname": "department_name_en", "fieldtype": "Data", "label": "Department Name (English)", "reqd": 1, "in_list_view": 1},
                {"fieldname": "department_name_ar", "fieldtype": "Data", "label": "Department Name (Arabic)", "reqd": 1, "in_list_view": 1},
                {"fieldname": "college", "fieldtype": "Link", "options": "Jameah College", "label": "Parent College", "in_list_view": 1},
                {"fieldname": "ministry_code", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Ministry Code"}
            ]
        }
    ]

    for dt in doctypes:
        if not frappe.db.exists("DocType", dt["name"]):
            doc = frappe.get_doc({
                "doctype": "DocType",
                "name": dt["name"],
                "module": "Medical Hrms",
                "custom": 1,
                "autoname": "field:" + dt["autoname_field"],
                "fields": dt["fields"],
                "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}],
                "naming_rule": "By fieldname"
            })
            doc.insert(ignore_permissions=True)
            print(f"Created DocType: {dt['name']}")

def link_institute_to_employee_instructor():
    institute_fields = [
        {
            "fieldname": "custom_jameah_institute_details",
            "label": "Institute Placement",
            "fieldtype": "Section Break",
            "insert_after": "department" # Insert after standard department
        },
        {
            "fieldname": "custom_jameah_branch",
            "label": "Branch",
            "fieldtype": "Link",
            "options": "Jameah Branch",
            "insert_after": "custom_jameah_institute_details"
        },
        {
            "fieldname": "custom_jameah_agency",
            "label": "Agency",
            "fieldtype": "Link",
            "options": "Jameah Agency",
            "insert_after": "custom_jameah_branch"
        },
        {
            "fieldname": "custom_jameah_deanery",
            "label": "Deanery",
            "fieldtype": "Link",
            "options": "Jameah Deanery",
            "insert_after": "custom_jameah_agency"
        },
        {
            "fieldname": "custom_jameah_college",
            "label": "College",
            "fieldtype": "Link",
            "options": "Jameah College",
            "insert_after": "custom_jameah_deanery"
        },
        {
            "fieldname": "custom_jameah_academic_department",
            "label": "Academic Department",
            "fieldtype": "Link",
            "options": "Jameah Academic Department",
            "insert_after": "custom_jameah_college"
        }
    ]

    custom_fields = {
        "Employee": institute_fields,
        "Instructor": institute_fields
    }

    create_custom_fields(custom_fields, update=True)
    print("Linked Institute fields to Employee and Instructor.")

def execute():
    create_institute_doctypes()
    link_institute_to_employee_instructor()
    frappe.db.commit()
