
import frappe

from medical_hrms.ministry_lookup_config import MINISTRY_LOOKUP_FIELD_MAP


DOCTYPE = "Jameah Ministry Code"


def _validate_field(doc, fieldname: str, expected_category: str):
	field = doc.meta.get_field(fieldname)
	if not field or field.fieldtype != "Link" or field.options != DOCTYPE:
		return

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

	for row in doc.get("custom_jameah_qualifications") or []:
		validate_jameah_academic_qualification_ministry_lookups(row)

	for row in doc.get("custom_jameah_experience") or []:
		validate_jameah_work_experience_ministry_lookups(row)

	for row in doc.get("custom_jameah_training") or []:
		validate_jameah_training_course_ministry_lookups(row)


def validate_employee_education_ministry_lookups(doc, method=None):
	for field in MINISTRY_LOOKUP_FIELD_MAP["Employee Education"]:
		_validate_field(doc, field["fieldname"], field["category"])


def validate_jameah_academic_qualification_ministry_lookups(doc, method=None):
	for field in MINISTRY_LOOKUP_FIELD_MAP["Jameah Academic Qualification"]:
		_validate_field(doc, field["fieldname"], field["category"])


def _validate_identity_number_by_nationality(doc):
	nationality = doc.get("custom_jameah_nationality")
	if not nationality:
		frappe.throw("Nationality is required.")

	nationality_values = frappe.db.get_value(
		DOCTYPE, nationality, ["ministry_code", "name_english"], as_dict=True
	)
	ministry_code = nationality_values.ministry_code if nationality_values else None
	nationality_name = nationality_values.name_english if nationality_values else None
	is_saudi = ministry_code in {"101", "N-SA"} or (nationality_name or "").lower().startswith("saudi")

	if is_saudi and not doc.get("custom_identity_number"):
		frappe.throw("Identity Number is required for Saudi employees.")

	if not is_saudi and not doc.get("custom_original_home_id_number"):
		frappe.throw("ID Number in Country of Origin for Non-Saudis is required.")


def validate_jameah_work_experience_ministry_lookups(doc, method=None):
	for field in MINISTRY_LOOKUP_FIELD_MAP["Jameah Work Experience"]:
		_validate_field(doc, field["fieldname"], field["category"])


def validate_jameah_training_course_ministry_lookups(doc, method=None):
	for field in MINISTRY_LOOKUP_FIELD_MAP["Jameah Training Course"]:
		_validate_field(doc, field["fieldname"], field["category"])
