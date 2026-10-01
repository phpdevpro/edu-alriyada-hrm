import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from medical_hrms.create_child_tables import create_child_doctypes, link_tables_to_parents
from medical_hrms.create_jameah_doctypes import create_jameah_ministry_code
from medical_hrms.setup_jameah_fields import add_jameah_fields
from medical_hrms.setup_ministry_lookup_fields import execute as setup_ministry_lookup_fields


CUSTOM_FIELD_LABELS = {
	("Employee", "custom_identity_number"): "Identity Civil Registry in the Kingdom",
	("Employee", "custom_ministry_special_needs_type"): "Type of Special Needs",
	("Employee", "custom_ministry_work_city"): "City (Geographical Place of Business)",
	("Employee", "custom_ministry_accommodation"): "Housing",
	("Employee", "custom_jameah_experience"): "Employee Academic Experience",
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


def execute():
	create_jameah_ministry_code()
	add_jameah_fields()
	create_child_doctypes()
	link_tables_to_parents()
	setup_ministry_lookup_fields()
	_set_custom_field_labels()
	_set_required_custom_fields()
	_set_standard_field_labels()
	_set_required_standard_fields()
	_set_child_field_labels()

	for doctype in (
		"Employee",
		"Employee Education",
		"Jameah Academic Qualification",
		"Jameah Work Experience",
		"Jameah Training Course",
	):
		frappe.clear_cache(doctype=doctype)

	frappe.db.commit()
	print("Created/updated the Ministry fields expected on Employee.")
