
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.model.utils.rename_field import rename_field
from frappe.model.rename_doc import rename_doc


OLD_WORK_EXPERIENCE_DOCTYPE = "Jameah Work Experience"
NEW_WORK_EXPERIENCE_DOCTYPE = "Jameah Academic Work Experience"
NEW_PREVIOUS_WORK_EXPERIENCE_DOCTYPE = "Jameah Previous Work Experience"
OLD_TRAINING_DOCTYPE = "Jameah Training Course"
NEW_TRAINING_DOCTYPE = "Jameah Professional Certificates and Training Courses"


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
		doc.save(ignore_permissions=True, ignore_version=True)
		print(f"Updated Child Table: {doctype_name}")


def _rename_legacy_work_experience_doctype():
	if frappe.db.exists("DocType", OLD_WORK_EXPERIENCE_DOCTYPE) and not frappe.db.exists(
		"DocType", NEW_WORK_EXPERIENCE_DOCTYPE
	):
		rename_doc("DocType", OLD_WORK_EXPERIENCE_DOCTYPE, NEW_WORK_EXPERIENCE_DOCTYPE, force=True, ignore_permissions=True)
		frappe.clear_cache()
		print(f"Renamed Child Table: {OLD_WORK_EXPERIENCE_DOCTYPE} -> {NEW_WORK_EXPERIENCE_DOCTYPE}")


def _rename_legacy_training_doctype():
	if frappe.db.exists("DocType", OLD_TRAINING_DOCTYPE) and not frappe.db.exists("DocType", NEW_TRAINING_DOCTYPE):
		rename_doc("DocType", OLD_TRAINING_DOCTYPE, NEW_TRAINING_DOCTYPE, force=True, ignore_permissions=True)
		frappe.clear_cache()
		print(f"Renamed Child Table: {OLD_TRAINING_DOCTYPE} -> {NEW_TRAINING_DOCTYPE}")


def _rename_legacy_training_fields():
	field_map = [
		("provider", "issuer"),
		("duration", "course_period"),
		("date", "course_date"),
		("city", "course_city"),
		("country", "course_country"),
	]

	for old_field, new_field in field_map:
		if frappe.db.exists("DocField", {"parent": NEW_TRAINING_DOCTYPE, "fieldname": old_field}) and not frappe.db.exists(
			"DocField", {"parent": NEW_TRAINING_DOCTYPE, "fieldname": new_field}
		):
			rename_field(NEW_TRAINING_DOCTYPE, old_field, new_field)


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
			"name": NEW_WORK_EXPERIENCE_DOCTYPE,
			"fields": [
				{"fieldname": "is_latest_work_experience_record", "fieldtype": "Check", "label": "Latest record of work experience", "default": 1, "read_only": 1, "in_list_view": 1},
				{"fieldname": "current_academic_year_date", "fieldtype": "Date", "label": "School year history", "reqd": 1, "in_list_view": 1},
				{"fieldname": "employment_status_code", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Employee's job status", "reqd": 1},
				{"fieldname": "profession", "fieldtype": "Data", "label": "Job Title"},
				{"fieldname": "institute_code", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Educational entity", "reqd": 1},
				{"fieldname": "location_code", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Geographical work location", "reqd": 1},
				{"fieldname": "section_code", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Academic Department", "reqd": 1},
				{"fieldname": "employee_number", "fieldtype": "Data", "label": "Job Number"},
				{"fieldname": "profession_rank_code", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Job rank", "reqd": 1},
				{"fieldname": "hiring_date", "fieldtype": "Date", "label": "Date of appointment to the rank"},
				{"fieldname": "start_working_date", "fieldtype": "Date", "label": "Start date"},
				{"fieldname": "end_working_date", "fieldtype": "Date", "label": "End of work date"},
				{"fieldname": "functional_tasks", "fieldtype": "Data", "label": "Job Duties"},
				{"fieldname": "accommodation_code", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Housing"},
			]
		},
		{
			"name": NEW_PREVIOUS_WORK_EXPERIENCE_DOCTYPE,
			"fields": [
				{"fieldname": "profession", "fieldtype": "Data", "label": "Job Title"},
				{"fieldname": "organization_name", "fieldtype": "Data", "label": "Name of educational institution/company", "in_list_view": 1},
				{"fieldname": "city", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "The city"},
				{"fieldname": "country", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Country"},
				{"fieldname": "department", "fieldtype": "Data", "label": "College / Administration"},
				{"fieldname": "section", "fieldtype": "Data", "label": "Section"},
				{"fieldname": "start_work_date", "fieldtype": "Date", "label": "Start date"},
				{"fieldname": "end_work_date", "fieldtype": "Date", "label": "End of work date"},
				{"fieldname": "functional_tasks", "fieldtype": "Data", "label": "Job Duties"},
			]
		},
		{
			"name": NEW_TRAINING_DOCTYPE,
			"fields": [
				{"fieldname": "course_name", "fieldtype": "Data", "label": "Course Name", "in_list_view": 1},
				{"fieldname": "course_type", "fieldtype": "Data", "label": "Type"},
				{"fieldname": "issuer", "fieldtype": "Data", "label": "Issuing Authority", "in_list_view": 1},
				{"fieldname": "course_date", "fieldtype": "Date", "label": "Course history", "in_list_view": 1},
				{"fieldname": "course_period", "fieldtype": "Data", "label": "Course duration", "in_list_view": 1},
				{"fieldname": "course_city", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "The city"},
				{"fieldname": "course_country", "fieldtype": "Link", "options": "Jameah Ministry Code", "label": "Country"},
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
			"label": "Academic Qualifications",
			"fieldtype": "Table",
			"options": "Jameah Academic Qualification",
			"insert_after": "custom_job_duties"
		},
		{
			"fieldname": "custom_jameah_experience",
			"label": "Academic Work Experience",
			"fieldtype": "Table",
			"options": NEW_WORK_EXPERIENCE_DOCTYPE,
			"insert_after": "custom_jameah_qualifications"
		},
		{
			"fieldname": "custom_jameah_previous_experience",
			"label": "Previous Work Experience",
			"fieldtype": "Table",
			"options": NEW_PREVIOUS_WORK_EXPERIENCE_DOCTYPE,
			"insert_after": "custom_jameah_experience"
		},
		{
			"fieldname": "custom_jameah_training",
			"label": "Professional Certificates & Training Courses",
			"fieldtype": "Table",
			"options": NEW_TRAINING_DOCTYPE,
			"insert_after": "custom_jameah_previous_experience"
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

	for parent in ("Employee", "Instructor"):
		fieldname = f"{parent}-custom_jameah_experience"
		if frappe.db.exists("Custom Field", fieldname):
			frappe.db.set_value(
				"Custom Field",
				fieldname,
				{
					"label": "Academic Work Experience",
					"options": NEW_WORK_EXPERIENCE_DOCTYPE,
				},
				update_modified=False,
			)
		prev_fieldname = f"{parent}-custom_jameah_previous_experience"
		if frappe.db.exists("Custom Field", prev_fieldname):
			frappe.db.set_value(
				"Custom Field",
				prev_fieldname,
				{
					"label": "Previous Work Experience",
					"options": NEW_PREVIOUS_WORK_EXPERIENCE_DOCTYPE,
				},
				update_modified=False,
			)
		training_fieldname = f"{parent}-custom_jameah_training"
		if frappe.db.exists("Custom Field", training_fieldname):
			frappe.db.set_value(
				"Custom Field",
				training_fieldname,
				{
					"label": "Professional Certificates & Training Courses",
					"options": NEW_TRAINING_DOCTYPE,
				},
				update_modified=False,
			)
	print("Linked Child Tables to Employee and Instructor Doctypes.")


def execute():
	_rename_legacy_work_experience_doctype()
	_rename_legacy_training_doctype()
	_rename_legacy_training_fields()
	create_child_doctypes()
	link_tables_to_parents()
	frappe.clear_cache(doctype="Jameah Academic Qualification")
	frappe.clear_cache(doctype=NEW_WORK_EXPERIENCE_DOCTYPE)
	frappe.clear_cache(doctype=NEW_PREVIOUS_WORK_EXPERIENCE_DOCTYPE)
	frappe.clear_cache(doctype=NEW_TRAINING_DOCTYPE)
	frappe.db.commit()
