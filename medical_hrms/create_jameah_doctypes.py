import frappe

def create_jameah_ministry_code():
    doctype_name = "Jameah Ministry Code"
    if not frappe.db.exists("DocType", doctype_name):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": doctype_name,
            "module": "Medical Hrms",
            "custom": 1,
            "autoname": "format:{code_category}::{ministry_code}",
<<<<<<< HEAD
            "title_field": "name_english",
=======
>>>>>>> 31a5d95401dd98673b8dda7840d4f2a7600b47d9
            "fields": [
                {
                    "fieldname": "code_category",
                    "fieldtype": "Data",
                    "label": "Code Category",
                    "reqd": 1,
                    "in_list_view": 1,
                    "in_standard_filter": 1
                },
                {
                    "fieldname": "ministry_code",
                    "fieldtype": "Data",
                    "label": "Ministry Code",
                    "reqd": 1,
                    "in_list_view": 1
                },
                {
                    "fieldname": "name_english",
                    "fieldtype": "Data",
                    "label": "Name (English)",
                    "reqd": 1,
                    "in_list_view": 1
                },
                {
                    "fieldname": "name_arabic",
                    "fieldtype": "Data",
                    "label": "Name (Arabic)",
                    "reqd": 1,
                    "in_list_view": 1
                }
            ],
            "permissions": [
                {
                    "role": "System Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1
                },
                {
                    "role": "HR User",
                    "read": 1
                }
            ],
            "sort_field": "modified",
            "sort_order": "DESC",
            "track_changes": 1,
            "naming_rule": "By fieldname"
        })
        doc.insert(ignore_permissions=True)
        print(f"Created DocType: {doctype_name}")
    else:
        print(f"DocType {doctype_name} already exists.")

def execute():
    create_jameah_ministry_code()
    frappe.db.commit()
