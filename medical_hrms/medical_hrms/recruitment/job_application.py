import frappe
import re
from frappe import _
from frappe.utils import get_datetime, now_datetime, nowdate, validate_email_address
from frappe.utils.file_manager import save_file

ACADEMIC_CATEGORY = "Academic Staff"
NON_ACADEMIC_CATEGORY = "Non-Academic / Other Staff"
HR_ROLES = ("HR User", "HR Manager", "System Manager")
APPLICANT_DOCTYPE = "Employee Job Applicant"

TABLE_FIELD_MAP = {
	"academic_qualifications": [
		"academic_qualification",
		"general_specialization_main",
		"subspecialty",
		"appreciation",
		"graduation_rate",
		"rate_type",
		"study_system",
		"graduation_place",
		"college",
		"qualification_date",
		"graduation_year_ad",
		"city",
		"country",
	],
	"academic_work_experience": [
		"school_year_history",
		"employee_job_status",
		"job_title",
		"educational_entity",
		"geographical_work_location",
		"academic_department",
		"job_number",
		"job_rank",
		"date_of_appointment_to_the_rank",
		"start_date",
		"end_of_work_date",
		"job_duties",
		"housing",
	],
	"previous_work_experience": [
		"job_title",
		"institution_or_company",
		"city",
		"country",
		"college_administration",
		"section",
		"start_date",
		"end_of_work_date",
		"job_duties",
	],
	"professional_certificates_training": [
		"course_name",
		"certificate_type",
		"issuing_authority",
		"course_history",
		"course_duration",
		"city",
		"country",
	],
	"research_publications": ["title", "journal", "publication_date", "link"],
	"awards": ["award_name", "organization", "award_date", "details"],
}

TABLE_FIELD_ALIASES = {
	"academic_qualifications": {"academic_qualification": "degree", "general_specialization_main": "specialization", "subspecialty": "minor", "appreciation": "assessment_type", "graduation_rate": "gpa", "rate_type": "gpa_type", "study_system": "study_type", "graduation_place": "institute", "college": "faculty", "graduation_year_ad": "graduation_year"},
	"academic_work_experience": {"school_year_history": "current_academic_year_date", "employee_job_status": "employment_status_code", "job_title": "profession", "educational_entity": "institute_code", "geographical_work_location": "location_code", "academic_department": "section_code", "job_number": "employee_number", "job_rank": "profession_rank_code", "date_of_appointment_to_the_rank": "hiring_date", "start_date": "start_working_date", "end_of_work_date": "end_working_date", "job_duties": "functional_tasks", "housing": "accommodation_code"},
	"previous_work_experience": {"job_title": "profession", "institution_or_company": "organization_name", "start_date": "start_work_date", "end_of_work_date": "end_work_date", "job_duties": "functional_tasks"},
	"professional_certificates_training": {"certificate_type": "course_type", "issuing_authority": "issuer", "course_history": "course_date", "course_duration": "course_period", "city": "course_city", "country": "course_country"},
	"awards": {"award_date": "date"},
}


def is_hr_admin():
	if frappe.session.user == "Guest":
		return False
	roles = frappe.get_roles()
	return any(role in roles for role in HR_ROLES)


def get_application_link(token: str):
	if not token:
		return None

	return frappe.db.get_value(
		"Job Application Link",
		{"generated_token": token},
		["name", "application_category", "is_active", "valid_from", "valid_until"],
		as_dict=True,
	)


def validate_application_link(token: str):
	if not token:
		return False, "missing", None

	link = get_application_link(token)
	if not link:
		return False, "invalid", None

	if not link.is_active:
		return False, "inactive", link

	now = now_datetime()
	if link.valid_from and now < get_datetime(link.valid_from):
		return False, "not_started", link

	if link.valid_until and now > get_datetime(link.valid_until):
		return False, "expired", link

	return True, "", link


@frappe.whitelist(allow_guest=True)
def submit_application(data, token=None):
	payload = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	payload = normalize_payload(payload)
	token = token or frappe.form_dict.get("token")
	link = None

	if token:
		is_valid, reason, link = validate_application_link(token)
		if not is_valid:
			frappe.throw(_(get_invalid_message(reason)))
	# Token-based links remain validated when supplied. The standalone public form
	# is also allowed to submit without a token.

	if link:
		application_category = link.application_category
	else:
		application_category = payload.get("application_category") or ACADEMIC_CATEGORY

	validate_payload(payload, application_category)

	doc = frappe.new_doc(APPLICANT_DOCTYPE)
	doc.applicant_name = payload.get("full_name")
	doc.email_id = payload.get("email")
	doc.phone_number = payload.get("phone")
	doc.status = "Pending"
	doc.designation = payload.get("designation")
	doc.department = payload.get("department")
	doc.application_category = application_category
	doc.application_token = token
	doc.date_of_birth = payload.get("date_of_birth")
	doc.gender = payload.get("gender")
	doc.nic_passport = payload.get("nic_passport")
	doc.address = payload.get("address")
	doc.emergency_contact_name = payload.get("emergency_contact_name")
	doc.emergency_contact_phone = payload.get("emergency_contact_phone")
	doc.emergency_contact_relation = payload.get("emergency_contact_relation")
	doc.expected_salary = payload.get("expected_salary")
	doc.cover_letter = payload.get("cover_letter")
	doc.resume_link = payload.get("resume_link")
	doc.custom_first_name_en = payload.get("custom_first_name_en")
	doc.custom_second_name_en = payload.get("custom_second_name_en")
	doc.custom_third_name_en = payload.get("custom_third_name_en")
	doc.custom_last_name_en = payload.get("custom_last_name_en")
	doc.custom_first_name_ar = payload.get("custom_first_name_ar")
	doc.custom_second_name_ar = payload.get("custom_second_name_ar")
	doc.custom_third_name_ar = payload.get("custom_third_name_ar")
	doc.custom_last_name_ar = payload.get("custom_last_name_ar")
	doc.custom_identity_type = payload.get("custom_identity_type")
	doc.custom_identity_number = payload.get("custom_identity_number")
	doc.custom_identity_issue_date = payload.get("custom_identity_issue_date")
	doc.custom_identity_issue_place = payload.get("custom_identity_issue_place")
	doc.custom_original_home_id_number = payload.get("custom_original_home_id_number")
	doc.custom_ministry_place_of_birth = payload.get("custom_ministry_place_of_birth")
	doc.custom_jameah_nationality = payload.get("custom_jameah_nationality")
	doc.custom_ministry_religion = payload.get("custom_ministry_religion")
	doc.custom_is_special_needs = payload.get("custom_is_special_needs")
	doc.custom_ministry_special_needs_type = payload.get("custom_ministry_special_needs_type")
	doc.custom_work_telephone_number = payload.get("custom_work_telephone_number")
	doc.custom_work_telephone_extention_number = payload.get("custom_work_telephone_extention_number")
	doc.custom_ministry_work_city = payload.get("custom_ministry_work_city")
	doc.custom_ministry_job_rank = payload.get("custom_ministry_job_rank")
	doc.custom_ministry_accommodation = payload.get("custom_ministry_accommodation")
	doc.application_details_json = frappe.as_json(payload)
	copy_payload_fields_to_applicant(doc, payload)

	currency = payload.get("expected_salary_currency") or frappe.db.get_default("currency")
	if currency:
		doc.currency = currency

	if doc.designation and not frappe.db.exists("Designation", doc.designation):
		frappe.throw(_("Designation {0} is not valid.").format(doc.designation))

	if doc.department and not frappe.db.exists("Department", doc.department):
		frappe.throw(_("Department {0} is not valid.").format(doc.department))

	append_child_rows(doc, payload)

	doc.flags.ignore_permissions = True
	doc.insert()

	resume_file = None
	try:
		resume_file = frappe.request.files.get("resume_file")
	except RuntimeError:
		# Direct calls and background contexts do not have an HTTP request.
		pass
	if resume_file:
		file_doc = save_file(
			resume_file.filename,
			resume_file.stream.read(),
			APPLICANT_DOCTYPE,
			doc.name,
			is_private=1,
		)
		doc.db_set("resume_attachment", file_doc.file_url)

	return {"job_applicant": doc.name}


@frappe.whitelist()
def accept_application(job_applicant):
	frappe.has_permission(APPLICANT_DOCTYPE, "write", throw=True)
	applicant = frappe.get_doc(APPLICANT_DOCTYPE, job_applicant)
	applicant.db_set("status", "Accepted")
	return {"status": "Accepted"}


@frappe.whitelist()
def reject_application(job_applicant):
	frappe.has_permission(APPLICANT_DOCTYPE, "write", throw=True)
	applicant = frappe.get_doc(APPLICANT_DOCTYPE, job_applicant)
	applicant.db_set("status", "Rejected")
	return {"status": "Rejected"}


@frappe.whitelist()
def create_employee_from_applicant(job_applicant):
	frappe.has_permission(APPLICANT_DOCTYPE, "write", throw=True)
	applicant = frappe.get_doc(APPLICANT_DOCTYPE, job_applicant)

	if applicant.status != "Accepted":
		frappe.throw(_("Only accepted applications can be converted to an Employee."))

	if frappe.db.exists("Employee", {"custom_job_applicant": applicant.name}):
		frappe.throw(_("An Employee record already exists for this applicant."))

	first_name, last_name = split_full_name(applicant.applicant_name)
	company = get_default_company()
	if not company:
		frappe.throw(_("Please set a default Company before creating an Employee."))

	employee = frappe.new_doc("Employee")
	employee.first_name = first_name or applicant.applicant_name
	employee.last_name = last_name
	employee.employee_name = applicant.applicant_name
	employee.company = company
	employee.date_of_joining = nowdate()
	employee.personal_email = applicant.email_id
	employee.cell_number = applicant.phone_number
	employee.gender = applicant.gender
	employee.custom_first_name_en = applicant.custom_first_name_en
	employee.custom_second_name_en = applicant.custom_second_name_en
	employee.custom_third_name_en = applicant.custom_third_name_en
	employee.custom_last_name_en = applicant.custom_last_name_en
	employee.custom_first_name_ar = applicant.custom_first_name_ar
	employee.custom_second_name_ar = applicant.custom_second_name_ar
	employee.custom_third_name_ar = applicant.custom_third_name_ar
	employee.custom_last_name_ar = applicant.custom_last_name_ar
	employee.custom_identity_type = applicant.custom_identity_type
	employee.custom_identity_number = applicant.custom_identity_number
	employee.custom_identity_issue_date = applicant.custom_identity_issue_date
	employee.custom_identity_issue_place = applicant.custom_identity_issue_place
	employee.custom_original_home_id_number = applicant.custom_original_home_id_number
	employee.custom_ministry_place_of_birth = applicant.custom_ministry_place_of_birth
	employee.custom_jameah_nationality = applicant.custom_jameah_nationality
	employee.custom_ministry_religion = applicant.custom_ministry_religion
	employee.custom_is_special_needs = applicant.custom_is_special_needs
	employee.custom_ministry_special_needs_type = applicant.custom_ministry_special_needs_type
	employee.custom_work_telephone_number = applicant.custom_work_telephone_number
	employee.custom_work_telephone_extention_number = applicant.custom_work_telephone_extention_number
	employee.custom_ministry_work_city = applicant.custom_ministry_work_city
	employee.custom_ministry_job_rank = applicant.custom_ministry_job_rank
	employee.custom_ministry_accommodation = applicant.custom_ministry_accommodation
	employee.date_of_birth = applicant.date_of_birth
	employee.designation = applicant.designation
	employee.department = applicant.department
	employee.current_address = applicant.address
	employee.permanent_address = applicant.address
	employee.emergency_phone_number = applicant.emergency_contact_phone
	employee.person_to_be_contacted = applicant.emergency_contact_name
	employee.relation = applicant.emergency_contact_relation
	employee.custom_application_category = applicant.application_category
	employee.custom_expected_salary = applicant.expected_salary
	employee.custom_nic_passport = applicant.nic_passport
	employee.custom_resume_attachment = applicant.resume_attachment
	employee.custom_job_applicant = applicant.name
	employee.bio = applicant.cover_letter
	copy_matching_employee_fields(applicant, employee)

	copy_child_table(applicant, employee, "academic_qualifications", "education")
	copy_child_table(applicant, employee, "academic_work_experience", "external_work_history")
	copy_child_table(applicant, employee, "previous_work_experience", "internal_work_history")

	employee.insert()
	return {"employee": employee.name}


def validate_payload(payload, application_category):
	required = {
		"full_name": "Full Name",
		"email": "Email",
		"phone": "Phone Number",
	}
	missing = [label for key, label in required.items() if not payload.get(key)]
	if missing:
		frappe.throw(_("Missing required fields: {0}").format(", ".join(missing)))

	if payload.get("email"):
		validate_email_address(payload.get("email"), True)

	arabic_pattern = re.compile(r"^[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\s'’-]+$")
	for fieldname in ("custom_first_name_ar", "custom_second_name_ar", "custom_third_name_ar", "custom_last_name_ar"):
		value = payload.get(fieldname)
		if value and not arabic_pattern.fullmatch(value):
			frappe.throw(_("{0} must contain Arabic letters only.").format(fieldname))

	if application_category == ACADEMIC_CATEGORY:
		rows = payload.get("academic_qualifications") or []
		if not rows:
			frappe.throw(_("Academic Qualifications are required."))


def normalize_payload(payload):
	"""Accept the public form's Employee field names and legacy API names."""
	payload = dict(payload or {})
	payload.setdefault("full_name", payload.get("employee_name") or build_full_name(payload))
	payload.setdefault("email", payload.get("personal_email"))
	payload.setdefault("phone", payload.get("cell_number"))
	payload.setdefault("address", payload.get("current_address") or payload.get("permanent_address"))
	payload.setdefault("gender", payload.get("gender"))
	payload.setdefault("nic_passport", payload.get("custom_nic_passport") or payload.get("passport_number"))
	payload.setdefault("cover_letter", payload.get("bio"))
	return payload


def append_child_rows(doc, payload):
	payload_map = {
		"academic_qualifications": payload.get("academic_qualifications"),
		"academic_work_experience": payload.get("academic_work_experience"),
		"previous_work_experience": payload.get("previous_work_experience"),
		"professional_certificates_training": payload.get("professional_certificates_training"),
		"research_publications": payload.get("research_publications"),
		"awards": payload.get("awards"),
	}

	for fieldname, rows in payload_map.items():
		append_rows(doc, fieldname, rows or [])


def append_rows(doc, fieldname, rows):
	allowed_fields = TABLE_FIELD_MAP.get(fieldname, [])
	for row in rows:
		if not isinstance(row, dict):
			continue

		cleaned = {}
		for key in allowed_fields:
			if row.get(key) not in (None, ""):
				cleaned[TABLE_FIELD_ALIASES.get(fieldname, {}).get(key, key)] = row.get(key)
		if cleaned:
			doc.append(fieldname, cleaned)


def copy_child_table(source, target, source_field, target_field):
	rows = source.get(source_field) or []
	if not rows:
		return

	for row in rows:
		cleaned = cleanup_child_row(row.as_dict())
		if cleaned:
			target.append(target_field, cleaned)


def copy_matching_employee_fields(source, target):
	"""Copy scalar fields submitted by the applicant when Employee has the same fieldname."""
	data = frappe.parse_json(source.application_details_json or "{}")
	for field in frappe.get_meta("Employee").fields:
		if field.fieldtype in ("Table", "Table MultiSelect", "Section Break", "Column Break", "Tab Break", "HTML"):
			continue
		if field.fieldname in data and field.fieldname not in {"name", "employee_name", "first_name", "last_name", "company"}:
			if target.meta.has_field(field.fieldname):
				setattr(target, field.fieldname, data[field.fieldname])
		elif target.meta.has_field("custom_" + field.fieldname) and getattr(source, "custom_" + field.fieldname, None):
			setattr(target, field.fieldname, getattr(source, "custom_" + field.fieldname))


def copy_payload_fields_to_applicant(doc, payload):
	"""Persist every scalar form value in a real Applicant field when available."""
	applicant_meta = doc.meta
	employee_meta = frappe.get_meta("Employee")
	for fieldname, value in payload.items():
		if isinstance(value, (list, dict)) or value in (None, ""):
			continue
		if applicant_meta.has_field(fieldname):
			setattr(doc, fieldname, value)
		elif employee_meta.has_field(fieldname) and applicant_meta.has_field("custom_" + fieldname):
			setattr(doc, "custom_" + fieldname, value)


def cleanup_child_row(row_dict):
	discard = {
		"name",
		"doctype",
		"parent",
		"parenttype",
		"parentfield",
		"idx",
		"owner",
		"creation",
		"modified",
		"modified_by",
	}
	return {key: value for key, value in row_dict.items() if key not in discard and value not in (None, "")}


def split_full_name(full_name):
	parts = (full_name or "").strip().split()
	if not parts:
		return "", ""
	if len(parts) == 1:
		return parts[0], ""
	return parts[0], " ".join(parts[1:])


def get_default_company():
	return frappe.db.get_default("company") or frappe.db.get_single_value("Global Defaults", "default_company")


def get_invalid_message(reason):
	messages = {
		"missing": "Application link is required.",
		"invalid": "The application link is invalid.",
		"inactive": "This application link is not active.",
		"not_started": "This application link is not active yet.",
		"expired": "This application link has expired.",
	}
	return messages.get(reason, "The application link is invalid.")



def build_full_name(payload):
	parts = [payload.get("custom_first_name_en"), payload.get("custom_second_name_en"), payload.get("custom_third_name_en"), payload.get("custom_last_name_en")]
	if not any(parts):
		parts = [payload.get("first_name"), payload.get("middle_name"), payload.get("last_name")]
	return " ".join([part for part in parts if part]).strip()
