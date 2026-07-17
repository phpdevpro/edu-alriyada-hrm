
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def _ensure_child_doctype(doctype_name, field_specs):
	if not frappe.db.exists("DocType", doctype_name):
		doc = frappe.get_doc({
			"doctype": "DocType",
			"name": doctype_name,
			"module": "Medical Hrms",
			"custom": 1,
			"istable": 1,
			"fields": field_specs,
		})
		doc.insert(ignore_permissions=True)
		print(f"Created Child Table: {doctype_name}")
		return

	doc = frappe.get_doc("DocType", doctype_name)
	existing = {field.fieldname: field for field in doc.fields}
	changed = False

	for spec in field_specs:
		fieldname = spec["fieldname"]
		df = existing.get(fieldname)
		if df:
			for key, value in spec.items():
				setattr(df, key, value)
			changed = True
			continue

		doc.append("fields", spec)
		changed = True

	if changed:
		doc.save(ignore_permissions=True)
		print(f"Updated Child Table: {doctype_name}")


ACADEMIC_QUALIFICATION_FIELDS = [
	{"fieldname": "is_last_academic_data_record", "fieldtype": "Check", "label": "Latest academic data record", "default": 0, "read_only": 1, "hidden": 1},
	{"fieldname": "degree", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Academic qualification", "in_list_view": 1, "reqd": 1},
	{"fieldname": "specialization", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "General Specialization (Main)", "in_list_view": 1, "reqd": 1},
	{"fieldname": "minor", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Subspecialty"},
	{"fieldname": "assessment_type", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Appreciation", "reqd": 1},
	{"fieldname": "gpa", "fieldtype": "Float", "label": "Graduation rate", "reqd": 1},
	{"fieldname": "gpa_type", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Rate type", "reqd": 1},
	{"fieldname": "study_type", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Study system", "reqd": 1},
	{"fieldname": "institute", "fieldtype": "Data", "label": "Graduation Place", "in_list_view": 1, "reqd": 1},
	{"fieldname": "faculty", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "College", "reqd": 1},
	{"fieldname": "qualification_date", "fieldtype": "Date", "label": "Date of obtaining the qualification", "reqd": 1},
	{"fieldname": "graduation_year", "fieldtype": "Int", "label": "Graduation year AD", "in_list_view": 1, "reqd": 1},
	{"fieldname": "city", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "The city", "reqd": 1},
	{"fieldname": "country", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Country (Graduation Country)", "in_list_view": 1, "reqd": 1},
]


def create_child_doctypes():
	child_tables = [
		{
			"name": "Jameah Academic Qualification",
			"fields": ACADEMIC_QUALIFICATION_FIELDS,
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
				{"fieldname": "job_duties", "fieldtype": "Small Text", "label": "Job Duties"},
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
				{"fieldname": "country", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Country"},
			]
		},
		{
			"name": "Jameah Research Publication",
			"fields": [
				{"fieldname": "title", "fieldtype": "Data", "label": "Publication Title", "in_list_view": 1},
				{"fieldname": "journal", "fieldtype": "Data", "label": "Journal/Conference", "in_list_view": 1},
				{"fieldname": "publication_date", "fieldtype": "Date", "label": "Publication Date", "in_list_view": 1},
				{"fieldname": "link", "fieldtype": "Data", "label": "Link/DOI"},
			]
		},
		{
			"name": "Jameah Award",
			"fields": [
				{"fieldname": "award_name", "fieldtype": "Data", "label": "Award Name", "in_list_view": 1},
				{"fieldname": "organization", "fieldtype": "Data", "label": "Organization", "in_list_view": 1},
				{"fieldname": "date", "fieldtype": "Date", "label": "Date", "in_list_view": 1},
			]
		},
	]

	for table in child_tables:
		_ensure_child_doctype(table["name"], table["fields"])


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
	frappe.clear_cache(doctype="Jameah Academic Qualification")
	frappe.clear_cache(doctype="Jameah Work Experience")
	frappe.clear_cache(doctype="Jameah Training Course")
	frappe.db.commit()
