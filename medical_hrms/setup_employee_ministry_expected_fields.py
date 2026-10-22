import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from medical_hrms.create_child_tables import create_child_doctypes, link_tables_to_parents
from medical_hrms.create_jameah_doctypes import create_jameah_ministry_code
from medical_hrms.ministry_lookup_config import MINISTRY_LOOKUP_FIELD_MAP
from medical_hrms.setup_jameah_fields import add_jameah_fields
from medical_hrms.setup_ministry_lookup_fields import execute as setup_ministry_lookup_fields


CUSTOM_FIELD_LABELS = {
	("Employee", "custom_identity_number"): "Identity Civil Registry in the Kingdom",
	("Employee", "custom_ministry_special_needs_type"): "Type of Special Needs",
	("Employee", "custom_ministry_work_city"): "City (Geographical Place of Business)",
	("Employee", "custom_ministry_accommodation"): "Housing",
	("Employee", "custom_jameah_experience"): "Employee Academic Experience",
	("Employee", "custom_jameah_previous_experience"): "Employee Previous Experience",
	("Employee", "custom_jameah_training"): "Employee Professional Certificates & Training Courses",
	("Employee Education", "custom_ministry_assessment_type"): "Appreciation",
	("Employee Education", "custom_ministry_gpa_type"): "Rate Type",
	("Employee Education", "custom_ministry_study_type"): "Study System",
	("Employee Education", "custom_ministry_graduate_from"): "Graduation Place",
	("Employee Education", "custom_ministry_faculty"): "College",
	("Employee Education", "custom_date_of_scientific_degree"): "Date of Obtaining the Qualification",
	("Employee Education", "custom_ministry_city"): "City",
}

STANDARD_FIELD_LABELS = {
	("Employee", "status"): "Employee's Job Status",
	("Employee", "company"): "Educational Entity",
	("Employee", "branch"): "Geographical Work Location",
	("Employee", "department"): "Academic Department",
	("Employee", "employee_number"): "Job Number",
	("Employee", "education"): "Employee Academic Qualifications",
	("Employee Education", "class_per"): "Graduation Rate",
}

REQUIRED_CUSTOM_FIELDS = {
	("Employee", "custom_ministry_work_city"),
	("Employee", "custom_ministry_job_rank"),
	("Employee Education", "custom_ministry_scientific_degree"),
	("Employee Education", "custom_ministry_major"),
	("Employee Education", "custom_ministry_country"),
	("Employee Education", "custom_ministry_assessment_type"),
	("Employee Education", "custom_ministry_gpa_type"),
	("Employee Education", "custom_ministry_study_type"),
	("Employee Education", "custom_ministry_graduate_from"),
	("Employee Education", "custom_ministry_faculty"),
	("Employee Education", "custom_date_of_scientific_degree"),
	("Employee Education", "custom_ministry_city"),
}

REQUIRED_STANDARD_FIELDS = {
	("Employee", "branch"),
	("Employee", "department"),
	("Employee Education", "class_per"),
}

CHILD_FIELD_LABELS = {
	("Jameah Training Course", "date"): "Course History",
	("Jameah Work Experience", "designation"): "Job Title",
	("Jameah Work Experience", "end_date"): "End of Work Date",
}

LOOKUP_DOCTYPE = "Jameah Ministry Code"

ACADEMIC_EXPERIENCE_DOCTYPE = "Jameah Work Experience"
PREVIOUS_EXPERIENCE_DOCTYPE = "Jameah Previous Work Experience"
ACADEMIC_QUALIFICATION_DOCTYPE = "Jameah Academic Qualification"


def _link_field(fieldname, label, reqd=0):
	return {"fieldname": fieldname, "fieldtype": "Link", "options": LOOKUP_DOCTYPE, "label": label, "reqd": reqd}


def _plain_field(fieldname, fieldtype, label, reqd=0, **kwargs):
	field = {"fieldname": fieldname, "fieldtype": fieldtype, "label": label, "reqd": reqd}
	field.update(kwargs)
	return field


ACADEMIC_EXPERIENCE_FIELDS = [
	_plain_field("is_latest_work_experience_record", "Check", "Latest Record of Work Experience", reqd=1, default="1"),
	_plain_field("current_academic_year_date", "Date", "School Year History", reqd=1),
	_link_field("employment_status_code", "Employee's Job Status", reqd=1),
	_plain_field("designation", "Data", "Job Title"),
	_link_field("institute_code", "Educational Entity", reqd=1),
	_link_field("location_code", "Geographical Work Location", reqd=1),
	_link_field("section_code", "Academic Department", reqd=1),
	_plain_field("employee_number", "Data", "Job Number"),
	_link_field("profession_rank_code", "Job Rank", reqd=1),
	_plain_field("hiring_date", "Date", "Date of Appointment to the Rank"),
	_plain_field("start_date", "Date", "Start Date"),
	_plain_field("end_date", "Date", "End of Work Date"),
	_plain_field("job_duties", "Small Text", "Job Duties"),
	_link_field("accommodation_code", "Housing"),
]

PREVIOUS_EXPERIENCE_FIELDS = [
	_plain_field("profession", "Data", "Job Title"),
	_plain_field("organization_name", "Data", "Name of educational institution/company"),
	_plain_field("city", "Data", "The city"),
	_link_field("country", "Country"),
	_plain_field("department", "Data", "College / Administration"),
	_plain_field("section", "Data", "Section"),
	_plain_field("start_work_date", "Date", "Start date"),
	_plain_field("end_work_date", "Date", "End of work date"),
	_plain_field("functional_tasks", "Data", "Job Duties"),
]

ACADEMIC_QUALIFICATION_FIELDS = [
	_plain_field("is_last_academic_data_record", "Check", "Latest academic data record", reqd=1, default="1"),
	_link_field("degree", "Academic qualification", reqd=1),
	_link_field("specialization", "General Specialization (Main)", reqd=1),
	_link_field("minor", "Subspecialty"),
	_link_field("assessment_type", "Appreciation", reqd=1),
	_plain_field("gpa", "Float", "Graduation rate", reqd=1),
	_link_field("gpa_type", "Rate type", reqd=1),
	_link_field("study_type", "Study system", reqd=1),
	_plain_field("institute", "Data", "Graduation Place", reqd=1),
	_plain_field("faculty", "Data", "College", reqd=1),
	_plain_field("qualification_date", "Date", "Date of obtaining the qualification", reqd=1),
	_plain_field("graduation_year", "Int", "Graduation year AD", reqd=1),
	_plain_field("city", "Data", "The city", reqd=1),
	_link_field("country", "Country (Graduation Country)", reqd=1),
]


def _set_custom_field_labels():
	for (doctype, fieldname), label in CUSTOM_FIELD_LABELS.items():
		name = f"{doctype}-{fieldname}"
		if frappe.db.exists("Custom Field", name):
			frappe.db.set_value("Custom Field", name, "label", label, update_modified=False)


def _set_required_custom_fields():
	for doctype, fieldname in REQUIRED_CUSTOM_FIELDS:
		name = f"{doctype}-{fieldname}"
		if frappe.db.exists("Custom Field", name):
			frappe.db.set_value("Custom Field", name, "reqd", 1, update_modified=False)


def _set_standard_field_labels():
	for (doctype, fieldname), label in STANDARD_FIELD_LABELS.items():
		if frappe.get_meta(doctype).has_field(fieldname):
			make_property_setter(doctype, fieldname, "label", label, "Data")


def _set_required_standard_fields():
	for doctype, fieldname in REQUIRED_STANDARD_FIELDS:
		if frappe.get_meta(doctype).has_field(fieldname):
			make_property_setter(doctype, fieldname, "reqd", 1, "Check")


def _set_child_field_labels():
	for (doctype, fieldname), label in CHILD_FIELD_LABELS.items():
		frappe.db.set_value(
			"DocField",
			{"parent": doctype, "fieldname": fieldname},
			"label",
			label,
			update_modified=False,
		)


def _replace_child_table_fields(doctype, field_specs):
	if not frappe.db.exists("DocType", doctype):
		print(f"Skipped: {doctype} not found.")
		return

	doc = frappe.get_doc("DocType", doctype)
	doc.fields = []
	for idx, field in enumerate(field_specs, start=1):
		field = dict(field)
		field["idx"] = idx
		doc.append("fields", field)
	doc.save(ignore_permissions=True)


def _rebuild_experience_child_tables():
	_replace_child_table_fields(ACADEMIC_EXPERIENCE_DOCTYPE, ACADEMIC_EXPERIENCE_FIELDS)
	_replace_child_table_fields(PREVIOUS_EXPERIENCE_DOCTYPE, PREVIOUS_EXPERIENCE_FIELDS)
	_replace_child_table_fields(ACADEMIC_QUALIFICATION_DOCTYPE, ACADEMIC_QUALIFICATION_FIELDS)


FIELDS_TO_DOWNGRADE_TO_TEXT = [
	("Employee Education", "custom_ministry_graduate_from"),
	("Employee Education", "custom_ministry_faculty"),
	("Employee Education", "custom_ministry_city"),
	("Jameah Training Course", "city"),
]


def _downgrade_link_fields_to_text():
	for doctype, fieldname in FIELDS_TO_DOWNGRADE_TO_TEXT:
		custom_field_name = f"{doctype}-{fieldname}"
		if frappe.db.exists("Custom Field", custom_field_name):
			frappe.db.set_value(
				"Custom Field",
				custom_field_name,
				{"fieldtype": "Data", "options": "", "link_filters": None},
				update_modified=False,
			)
			continue

		is_custom_doctype = frappe.db.get_value("DocType", doctype, "custom")
		if is_custom_doctype and frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname}):
			frappe.db.set_value(
				"DocField",
				{"parent": doctype, "fieldname": fieldname},
				{"fieldtype": "Data", "options": None, "link_filters": None},
				update_modified=False,
			)


def _set_link_filter(doctype, fieldname, category):
	filters_json = frappe.as_json([[LOOKUP_DOCTYPE, "code_category", "=", category]], indent=0)

	custom_field_name = f"{doctype}-{fieldname}"
	if frappe.db.exists("Custom Field", custom_field_name):
		frappe.db.set_value("Custom Field", custom_field_name, "link_filters", filters_json, update_modified=False)
		return

	is_custom_doctype = frappe.db.get_value("DocType", doctype, "custom")
	if is_custom_doctype and frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname}):
		frappe.db.set_value(
			"DocField", {"parent": doctype, "fieldname": fieldname}, "link_filters", filters_json, update_modified=False
		)
		return

	if frappe.get_meta(doctype).has_field(fieldname):
		make_property_setter(doctype, fieldname, "link_filters", filters_json, "JSON")


def _apply_ministry_code_link_filters():
	for doctype, fields in MINISTRY_LOOKUP_FIELD_MAP.items():
		for field in fields:
			_set_link_filter(doctype, field["fieldname"], field["category"])


def execute():
	create_jameah_ministry_code()
	add_jameah_fields()
	create_child_doctypes()
	link_tables_to_parents()
	setup_ministry_lookup_fields()
	_rebuild_experience_child_tables()
	_downgrade_link_fields_to_text()
	_set_custom_field_labels()
	_set_required_custom_fields()
	_set_standard_field_labels()
	_set_required_standard_fields()
	_set_child_field_labels()
	_apply_ministry_code_link_filters()

	for doctype in (
		"Employee",
		"Employee Education",
		"Jameah Academic Qualification",
		"Jameah Work Experience",
		"Jameah Previous Work Experience",
		"Jameah Training Course",
	):
		frappe.clear_cache(doctype=doctype)

	frappe.db.commit()
	print("Created/updated the Ministry fields expected on Employee.")
