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
                {"fieldname": "current_academic_year_date", "fieldtype": "Date", "label": "School Year History", "reqd": 1, "in_list_view": 1},
                {"fieldname": "employment_status", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Employee's Job Status", "reqd": 1, "in_list_view": 1},
                {"fieldname": "institute", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Educational Entity", "reqd": 1, "in_list_view": 1},
                {"fieldname": "location", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Geographical Work Location", "reqd": 1},
                {"fieldname": "academic_department", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Academic Department", "reqd": 1},
                {"fieldname": "employee_number", "fieldtype": "Data", "label": "Job Number"},
                {"fieldname": "profession_rank", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Job Rank", "reqd": 1},
                {"fieldname": "hiring_date", "fieldtype": "Date", "label": "Date of Appointment to the Rank"},
                {"fieldname": "accommodation", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Housing"},
                {"fieldname": "city", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "City"},
                {"fieldname": "country", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Country"},
                {"fieldname": "college_administration", "fieldtype": "Data", "label": "College / Administration"},
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
            continue

        doc = frappe.get_doc("DocType", table["name"])
        existing_fields = {field.fieldname: field for field in doc.fields}
        changed = False

        if table["name"] == "Jameah Work Experience":
            for fieldname in ("company", "section"):
                custom_field = f"{table['name']}-{fieldname}"
                if frappe.db.exists("Custom Field", custom_field):
                    frappe.delete_doc("Custom Field", custom_field, ignore_permissions=True)
                if fieldname in existing_fields:
                    doc.remove(existing_fields[fieldname])
                    changed = True

        for definition in table["fields"]:
            fieldname = definition["fieldname"]
            if fieldname not in existing_fields:
                doc.append("fields", definition)
                changed = True
                continue

            field = existing_fields[fieldname]
            for property_name, value in definition.items():
                if field.get(property_name) != value:
                    field.set(property_name, value)
                    changed = True

        if changed:
            doc.save(ignore_permissions=True)

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
            "label": "Employee Academic Experience",
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
        "Instructor": [
            dict(field, label="Academic Experience")
            if field["fieldname"] == "custom_jameah_experience"
            else field
            for field in table_fields
        ]
    }

    create_custom_fields(custom_fields, update=True)
    print("Linked Child Tables to Employee and Instructor Doctypes.")

def execute():
    create_child_doctypes()
    link_tables_to_parents()
    frappe.db.commit()
