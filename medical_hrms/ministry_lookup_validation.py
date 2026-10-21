import re

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
	clear_values_that_do_not_apply(doc)
	for field in MINISTRY_LOOKUP_FIELD_MAP["Employee"]:
		_validate_field(doc, field["fieldname"], field["category"])

	_validate_identity_number_by_nationality(doc)

	for row in doc.get("education") or []:
		validate_employee_education_ministry_lookups(row)

	for row in doc.get("custom_jameah_experience") or []:
		validate_jameah_work_experience_ministry_lookups(row)

	for row in doc.get("custom_jameah_training") or []:
		validate_jameah_training_course_ministry_lookups(row)

	for row in doc.get("custom_jameah_qualifications") or []:
		validate_jameah_academic_qualification_ministry_lookups(row)

	for row in doc.get("custom_jameah_previous_experience") or []:
		validate_jameah_previous_work_experience_ministry_lookups(row)


def validate_employee_education_ministry_lookups(doc, method=None):
	for field in MINISTRY_LOOKUP_FIELD_MAP["Employee Education"]:
		_validate_field(doc, field["fieldname"], field["category"])


SAUDI_NATIONALITY_CODES = {"101"}
# Identity types that are 10-digit Kingdom civil registry numbers -> first
# digit (Ministry sheet "30 - Identity type": 01 National ID, 03 Iqama).
# Gulf ID, Passport and Border Number have other formats, so they only
# need a number.
IDENTITY_NUMBER_PREFIX = {"01": "1", "03": "2"}
NATIONAL_ID_TYPE_CODES = {"01"}


def ministry_codes(category):
	"""Codes of one category (all Ministry codes, see ministry_codes.sync)."""
	return frappe.get_all(
		DOCTYPE,
		filters={"code_category": category},
		fields=["name", "ministry_code", "name_english", "name_arabic"],
		order_by="name_english",
	)


def find_ministry_code(category, label):
	wanted = (label or "").strip().lower()
	for row in ministry_codes(category):
		if wanted in {(row.name or "").lower(), (row.ministry_code or "").lower(),
				(row.name_english or "").strip().lower(), (row.name_arabic or "").strip().lower()}:
			return row.name
	return None


def is_saudi_nationality(nationality):
	values = frappe.db.get_value(DOCTYPE, nationality, ["ministry_code", "name_english"], as_dict=True)
	return bool(values) and (
		values.ministry_code in SAUDI_NATIONALITY_CODES or (values.name_english or "").lower().startswith("saudi")
	)


def identity_problems(nationality, identity_type, identity_number):
	"""Ministry rules (MINISTRY_FIELD_MAPPING.html, Employee/Faculty Personal
	Information): Nationality, Identity type and IdentityNumber - the Kingdom
	civil registry number, i.e. National ID for Saudis, Iqama for residents -
	are mandatory for everyone. The home-country ID is optional.
	Returns a list of messages; shared by Employee validation, the job
	application and the Instructor data sheet import."""
	problems = []
	if not nationality:
		problems.append("Nationality is required.")
	if not identity_type:
		problems.append("Identity Type is required (e.g. National ID or Iqama).")
	number = (identity_number or "").strip()
	if not number:
		problems.append("Identity Number is required.")

	type_code = frappe.db.get_value(DOCTYPE, identity_type, "ministry_code") if identity_type else None
	prefix = IDENTITY_NUMBER_PREFIX.get(type_code)
	if prefix and number:
		label = "A National ID" if type_code in NATIONAL_ID_TYPE_CODES else "An Iqama"
		if not re.fullmatch(r"\d{10}", number):
			problems.append(f"{label} number has exactly 10 digits; '{number}' does not.")
		elif not number.startswith(prefix):
			problems.append(f"{label} number starts with {prefix}; '{number}' does not.")
	if nationality and type_code in NATIONAL_ID_TYPE_CODES and not is_saudi_nationality(nationality):
		problems.append("A National ID is only issued to Saudi nationals; residents use an Iqama.")
	return problems


def clear_values_that_do_not_apply(doc):
	"""The Employee form hides these fields when they do not apply, but the job
	application form and imports can still fill them. Left in place, the
	Ministry views would send a special-needs type for someone without special
	needs, and every save of such a record would be "Not Saved" on opening."""
	if not frappe.utils.cint(doc.get("custom_is_special_needs")) and doc.get("custom_ministry_special_needs_type"):
		doc.custom_ministry_special_needs_type = None
	nationality = doc.get("custom_jameah_nationality")
	if doc.get("custom_original_home_id_number") and nationality and is_saudi_nationality(nationality):
		doc.custom_original_home_id_number = None


def _validate_identity_number_by_nationality(doc):
	problems = identity_problems(
		doc.get("custom_jameah_nationality"), doc.get("custom_identity_type"), doc.get("custom_identity_number")
	)
	if problems:
		frappe.throw("<br>".join(problems), title="Ministry Identity Details")
	_validate_unique_identity(doc)


def _validate_unique_identity(doc):
	"""One Employee per person: the Kingdom identity number identifies them
	to the Ministry, and Job Number must not repeat within a company."""
	checks = [
		("custom_identity_number", {"custom_identity_number": doc.get("custom_identity_number")}, "Identity Number"),
	]
	if doc.get("custom_original_home_id_number") and doc.get("custom_jameah_nationality"):
		checks.append((
			"custom_original_home_id_number",
			{"custom_original_home_id_number": doc.custom_original_home_id_number,
				"custom_jameah_nationality": doc.custom_jameah_nationality},
			"ID Number in Country of Origin",
		))
	if doc.get("employee_number"):
		checks.append(("employee_number", {"employee_number": doc.employee_number, "company": doc.company}, "Job Number"))

	for fieldname, filters, label in checks:
		existing = frappe.db.get_value("Employee", {**filters, "name": ["!=", doc.name or ""]}, ["name", "employee_name"], as_dict=True)
		if existing:
			frappe.throw(
				f"{label} {frappe.bold(doc.get(fieldname))} is already registered to Employee "
				f"{frappe.bold(existing.name)} ({existing.employee_name}). Each person can only be registered once.",
				title="Duplicate Employee",
				exc=frappe.DuplicateEntryError,
			)


def validate_jameah_work_experience_ministry_lookups(doc, method=None):
	for field in MINISTRY_LOOKUP_FIELD_MAP["Jameah Work Experience"]:
		_validate_field(doc, field["fieldname"], field["category"])


def validate_jameah_training_course_ministry_lookups(doc, method=None):
	for field in MINISTRY_LOOKUP_FIELD_MAP["Jameah Training Course"]:
		_validate_field(doc, field["fieldname"], field["category"])


def validate_jameah_academic_qualification_ministry_lookups(doc, method=None):
	for field in MINISTRY_LOOKUP_FIELD_MAP["Jameah Academic Qualification"]:
		_validate_field(doc, field["fieldname"], field["category"])


def validate_jameah_previous_work_experience_ministry_lookups(doc, method=None):
	for field in MINISTRY_LOOKUP_FIELD_MAP["Jameah Previous Work Experience"]:
		_validate_field(doc, field["fieldname"], field["category"])


def core_gender(ministry_gender):
	"""The core Gender named like a Ministry Gender code (Gender::1 -> Male), or None."""
	if not ministry_gender or frappe.db.exists("Gender", ministry_gender):
		return ministry_gender
	english = frappe.db.get_value(DOCTYPE, {"name": ministry_gender, "code_category": "Gender"}, "name_english")
	return english if english and frappe.db.exists("Gender", english) else None
