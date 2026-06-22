import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def create_child_doctypes():
    child_tables = [
        {
            "name": "Jameah Academic Qualification",
            "fields": [
                {"fieldname": "degree", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Degree", "in_list_view": 1},
                {"fieldname": "specialization", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Specialization", "in_list_view": 1},
                {"fieldname": "institute", "fieldtype": "Data", "label": "Institute/University", "in_list_view": 1},
                {"fieldname": "country", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Country"},
                {"fieldname": "graduation_year", "fieldtype": "Data", "label": "Graduation Year", "in_list_view": 1}
            ]
        },
        {
            "name": "Jameah Work Experience",
            "fields": [
                {"fieldname": "company", "fieldtype": "Data", "label": "Company/Organization", "in_list_view": 1},
                {"fieldname": "city", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "City"},
                {"fieldname": "country", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Country"},
                {"fieldname": "college_administration", "fieldtype": "Data", "label": "College / Administration"},
                {"fieldname": "section", "fieldtype": "Data", "label": "Section"},
                {"fieldname": "designation", "fieldtype": "Data", "label": "Designation", "in_list_view": 1},
                {"fieldname": "start_date", "fieldtype": "Date", "label": "Start Date", "in_list_view": 1},
                {"fieldname": "end_date", "fieldtype": "Date", "label": "End Date", "in_list_view": 1},
                {"fieldname": "job_duties", "fieldtype": "Small Text", "label": "Job Duties"}
            ]
        },
        {
            "name": "Jameah Training Course",
            "fields": [
                {"fieldname": "course_name", "fieldtype": "Data", "label": "Course Name", "in_list_view": 1},
                {"fieldname": "course_type", "fieldtype": "Data", "label": "Type"},
                {"fieldname": "provider", "fieldtype": "Data", "label": "Provider", "in_list_view": 1},
                {"fieldname": "duration", "fieldtype": "Data", "label": "Duration (Days)", "in_list_view": 1},
                {"fieldname": "date", "fieldtype": "Date", "label": "Date"},
                {"fieldname": "city", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "City"},
                {"fieldname": "country", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Country"}
            ]
        },
        {
            "name": "Jameah Research Publication",
            "fields": [
                {"fieldname": "title", "fieldtype": "Data", "label": "Publication Title", "in_list_view": 1},
                {"fieldname": "journal", "fieldtype": "Data", "label": "Journal/Conference", "in_list_view": 1},
                {"fieldname": "publication_date", "fieldtype": "Date", "label": "Publication Date", "in_list_view": 1},
                {"fieldname": "link", "fieldtype": "Data", "label": "Link/DOI"}
            ]
        },
        {
            "name": "Jameah Award",
            "fields": [
                {"fieldname": "award_name", "fieldtype": "Data", "label": "Award Name", "in_list_view": 1},
                {"fieldname": "organization", "fieldtype": "Data", "label": "Organization", "in_list_view": 1},
                {"fieldname": "date", "fieldtype": "Date", "label": "Date", "in_list_view": 1}
            ]
        }
    ]

    for table in child_tables:
        if not frappe.db.exists("DocType", table["name"]):
            doc = frappe.get_doc({
                "doctype": "DocType",
                "name": table["name"],
                "module": "Medical Hrms",
                "custom": 1,
                "istable": 1,
                "fields": table["fields"]
            })
            doc.insert(ignore_permissions=True)
            print(f"Created Child Table: {table['name']}")

def link_tables_to_parents():
    table_fields = [
        {
            "fieldname": "custom_jameah_qualifications",
            "label": "Qualifications",
            "fieldtype": "Table",
            "options": "Jameah Academic Qualification",
            "insert_after": "custom_job_duties"
        },
        {
            "fieldname": "custom_jameah_experience",
            "label": "Work Experience",
            "fieldtype": "Table",
            "options": "Jameah Work Experience",
            "insert_after": "custom_jameah_qualifications"
        },
        {
            "fieldname": "custom_jameah_training",
            "label": "Training Courses",
            "fieldtype": "Table",
            "options": "Jameah Training Course",
            "insert_after": "custom_jameah_experience"
        },
        {
            "fieldname": "custom_jameah_publications",
            "label": "Research Publications",
            "fieldtype": "Table",
            "options": "Jameah Research Publication",
            "insert_after": "custom_jameah_training"
        },
        {
            "fieldname": "custom_jameah_awards",
            "label": "Awards",
            "fieldtype": "Table",
            "options": "Jameah Award",
            "insert_after": "custom_jameah_publications"
        }
    ]

    custom_fields = {
        "Employee": table_fields,
        "Instructor": table_fields
    }

    create_custom_fields(custom_fields, update=True)
    print("Linked Child Tables to Employee and Instructor Doctypes.")

def execute():
    create_child_doctypes()
    link_tables_to_parents()
    frappe.db.commit()
