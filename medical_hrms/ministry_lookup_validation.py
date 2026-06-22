import frappe

from medical_hrms.ministry_lookup_config import MINISTRY_LOOKUP_FIELD_MAP


DOCTYPE = "Jameah Ministry Code"


def _validate_field(doc, fieldname: str, expected_category: str):
	value = doc.get(fieldname)
	if not value:
		return

	actual_category = frappe.db.get_value(DOCTYPE, value, "code_category")
	if actual_category != expected_category:
		label = doc.meta.get_label(fieldname) or fieldname
		frappe.throw(
			f"{label} must be from ministry category '{expected_category}'. "
			f"Selected record belongs to '{actual_category or 'Unknown'}'."
		)


def validate_employee_ministry_lookups(doc, method=None):
	for field in MINISTRY_LOOKUP_FIELD_MAP["Employee"]:
		_validate_field(doc, field["fieldname"], field["category"])

	_validate_identity_number_by_nationality(doc)

	for row in doc.get("education") or []:
		validate_employee_education_ministry_lookups(row)

	for row in doc.get("custom_jameah_experience") or []:
		validate_jameah_work_experience_ministry_lookups(row)

	for row in doc.get("custom_jameah_training") or []:
		validate_jameah_training_course_ministry_lookups(row)


def validate_employee_education_ministry_lookups(doc, method=None):
	for field in MINISTRY_LOOKUP_FIELD_MAP["Employee Education"]:
		_validate_field(doc, field["fieldname"], field["category"])


def _validate_identity_number_by_nationality(doc):
	nationality = doc.get("custom_jameah_nationality")
	if not nationality:
		frappe.throw("Nationality is required.")

	ministry_code = frappe.db.get_value(DOCTYPE, nationality, "ministry_code")
	if ministry_code == "101" and not doc.get("custom_identity_number"):
		frappe.throw("Identity Number is required for Saudi employees.")

	if ministry_code != "101" and not doc.get("custom_original_home_id_number"):
		frappe.throw("ID Number in Country of Origin for Non-Saudis is required.")


def validate_jameah_work_experience_ministry_lookups(doc, method=None):
	for field in MINISTRY_LOOKUP_FIELD_MAP["Jameah Work Experience"]:
		_validate_field(doc, field["fieldname"], field["category"])


def validate_jameah_training_course_ministry_lookups(doc, method=None):
	for field in MINISTRY_LOOKUP_FIELD_MAP["Jameah Training Course"]:
		_validate_field(doc, field["fieldname"], field["category"])
