import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def create_facility_doctype():
    if not frappe.db.exists("DocType", "Jameah Facility"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Jameah Facility",
            "module": "Medical Hrms",
            "custom": 1,
            "autoname": "field:facility_name_en",
            "fields": [
                {"fieldname": "facility_name_en", "fieldtype": "Data", "label": "Facility Name (English)", "reqd": 1, "in_list_view": 1},
                {"fieldname": "facility_name_ar", "fieldtype": "Data", "label": "Facility Name (Arabic)", "reqd": 1, "in_list_view": 1},
                {"fieldname": "facility_type", "fieldtype": "Select", "options": "Hospital\nClinic\nLaboratory\nResearch Center\nClassroom\nOther", "label": "Facility Type", "in_list_view": 1},
                {"fieldname": "branch", "fieldtype": "Link", "options": "Jameah Branch", "label": "Branch"},
                {"fieldname": "college", "fieldtype": "Link", "options": "Jameah College", "label": "College"},
                {"fieldname": "ministry_code", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Ministry Code", "in_list_view": 1}
            ],
            "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}],
            "naming_rule": "By fieldname"
        })
        doc.insert(ignore_permissions=True)
        print("Created DocType: Jameah Facility")
    else:
        print("DocType Jameah Facility already exists.")

def link_facility_to_employee():
    facility_fields = [
        {
            "fieldname": "custom_jameah_facility",
            "label": "Assigned Facility (Hospital/Clinic/Lab)",
            "fieldtype": "Link",
            "options": "Jameah Facility",
            "insert_after": "custom_jameah_academic_department"
        }
    ]

    custom_fields = {
        "Employee": facility_fields,
        "Instructor": facility_fields
    }

    create_custom_fields(custom_fields, update=True)
    print("Linked Facility to Employee and Instructor.")

def execute():
    create_facility_doctype()
    link_facility_to_employee()
    frappe.db.commit()
