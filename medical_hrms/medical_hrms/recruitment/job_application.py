# Copyright (c) 2026, Admin and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime, nowdate, validate_email_address
from frappe.utils.file_manager import save_file

INSTRUCTOR_ROLE_NAME = "Instructor"


def _get_or_create_designation_for_role(role):
	"""The public form no longer lets applicants pick a Designation
	themselves - it's derived from whichever Role the application link was
	generated for (e.g. "Instructor"), so HR can't get a mismatched pair.
	Designation is a plain Link with no seeded data matching Role names, so
	this finds an existing one by that name or creates it on first use."""
	if not role:
		return None
	if frappe.db.exists("Designation", role):
		return role
	try:
		designation = frappe.get_doc({"doctype": "Designation", "designation_name": role})
		designation.insert(ignore_permissions=True)
		return designation.name
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Could not auto-create Designation for Role {role}")
		return None


def _resolve_gender_from_ministry_code(ministry_code):
	"""Employee Job Applicant.gender (and Employee.gender, see
	setup_ministry_lookup_fields.py) both store a Jameah Ministry Code name
	(e.g. "Gender::2", same lookup table as nationality/religion/etc - see
	the "Gender" data-category select in job-application.html) rather than
	a real Gender doctype value - but some OTHER doctypes (e.g. Instructor,
	whose gender field links to the education app's "Gender Edu" doctype)
	still expect the real label ("Male", "Female", ...). Jameah Ministry
	Code's name_english for the "Gender" category is seeded to match those
	real labels exactly, so this resolves one to the other where needed."""
	if not ministry_code:
		return None
	return frappe.db.get_value("Jameah Ministry Code", ministry_code, "name_english")


def _resolve_department_edu_from_employee(employee_department):
	"""Same mismatch as gender: Employee.department links to the core
	"Department" doctype (e.g. "Internal Medicine - ARC"), but
	Instructor.department links to the education app's "Department Edu"
	doctype instead - two different doctypes, so the value can't just be
	copied across. Both carry a human label in department_name (e.g.
	"Internal Medicine") that matches between them even though the Link
	values themselves don't, so resolve through that instead."""
	if not employee_department:
		return None
	label = frappe.db.get_value("Department", employee_department, "department_name")
	if not label:
		return None
	return frappe.db.get_value("Department Edu", {"department_name": label}, "name")


# Instructor (education app) carries its own copy of the same Jameah
# ministry demographic/identity/contact fields as Employee, added as Custom
# Fields with IDENTICAL fieldnames on both doctypes (see Customize Form on
# either) - so once Employee has them (already populated from the applicant
# by copy_matching_employee_fields in create_employee_from_applicant), they
# can be copied straight across by fieldname. Excluded here: fields handled
# separately above because their Link target doctype differs between
# Employee and Instructor (gender, department), "status" (explicitly set to
# "Active" - Employee's own status options include values like "Suspended"
# that aren't valid for Instructor), "employee" (linked afterwards via a
# raw DB write, see below), and plain system/meta fields.
INSTRUCTOR_SCALAR_COPY_SKIP_FIELDS = {
	"name", "owner", "creation", "modified", "modified_by", "docstatus", "idx",
	"naming_series", "doctype", "status", "gender", "department", "employee",
}

# Same identical-fieldname mirroring as above, but for the child tables
# (Qualifications, Work Experience, Training Courses, Publications, Awards,
# Previous Experience) - both doctypes use the exact same child DocTypes.
INSTRUCTOR_CHILD_TABLE_FIELDNAMES = [
	"custom_jameah_qualifications",
	"custom_jameah_experience",
	"custom_jameah_previous_experience",
	"custom_jameah_training",
	"custom_jameah_publications",
	"custom_jameah_awards",
]


def _copy_matching_scalar_fields(source, target, skip_fields):
	source_meta = source.meta
	for field in target.meta.fields:
		if field.fieldtype in ("Table", "Table MultiSelect", "Section Break", "Column Break", "Tab Break", "HTML"):
			continue
		if field.fieldname in skip_fields:
			continue
		if not source_meta.has_field(field.fieldname):
			continue
		value = source.get(field.fieldname)
		if value not in (None, ""):
			target.set(field.fieldname, value)


def _copy_matching_child_tables(source, target, fieldnames):
	for fieldname in fieldnames:
		rows = source.get(fieldname) or []
		if not rows:
			continue
		child_doctype = target.meta.get_field(fieldname).options
		valid_fields = [f.fieldname for f in frappe.get_meta(child_doctype).fields]
		for row in rows:
			cleaned = {fn: row.get(fn) for fn in valid_fields if row.get(fn) not in (None, "")}
			if cleaned:
				target.append(fieldname, cleaned)


def _create_instructor_from_employee(applicant, employee):
	"""Auto-create the matching Instructor record when an applicant who
	applied under the "Instructor" Role is accepted and converted to an
	Employee - so HR doesn't have to remember a separate manual step.

	Instructor.email normally must be an official college address (see
	Instructor.validate_college_email_domain in the education app) - a job
	applicant's email_id is almost always their personal address instead.
	Per instruction, the Instructor record should still be created either
	way, so this sets the `ignore_college_email_domain_check` flag that
	validate_college_email_domain() now respects, scoped to just this
	auto-create path - manually creating/editing an Instructor from the UI
	still enforces the real domain rule. HR can update the email to an
	official one later once assigned; that edit will go through the normal
	(enforced) validation.

	The only thing still required is a non-blank email, since Instructor's
	own after_insert() unconditionally creates a matching User account
	straight from self.email - a blank email would fail there regardless
	of the domain check.
	"""
	email = (applicant.email_id or "").strip().lower()
	if not email:
		frappe.msgprint(
			_(
				"This applicant applied for the Instructor role, but has no email on file, "
				"so a matching Instructor record could not be created automatically (an email "
				"is needed to create their login). Please create it manually once an email "
				"has been added."
			),
			title=_("Instructor Record Not Created"),
			indicator="orange",
		)
		return None

	arabic_name = (
		" ".join(
			filter(
				None,
				[
					applicant.custom_first_name_ar,
					applicant.custom_second_name_ar,
					applicant.custom_third_name_ar,
					applicant.custom_last_name_ar,
				],
			)
		)
		or applicant.applicant_name
	)

	try:
		# Both Instructor.gender (-> Gender Edu) and Instructor.department
		# (-> Department Edu) have fetch_from pointing at the matching
		# Employee field, which would otherwise overwrite our resolved
		# values with Employee's raw (differently-typed) Link value the
		# moment Employee is linked and saved - every save, not just the
		# first. So: insert first with Employee left unlinked (nothing to
		# fetch from yet, so the resolved values save cleanly), then link
		# Employee via a direct DB write that bypasses the fetch/validate
		# cycle entirely, preserving both resolved values.
		instructor = frappe.new_doc("Instructor")
		instructor.instructor_name = applicant.applicant_name
		instructor.arabic_name = arabic_name
		instructor.email = email
		instructor.personal_email_id = applicant.email_id
		instructor.mobile_no = employee.cell_number or applicant.phone_number
		instructor.employee_no = employee.employee_number or employee.name
		instructor.gender = _resolve_gender_from_ministry_code(applicant.gender)
		instructor.department = _resolve_department_edu_from_employee(employee.department)
		instructor.status = "Active"
		_copy_matching_scalar_fields(employee, instructor, INSTRUCTOR_SCALAR_COPY_SKIP_FIELDS)
		_copy_matching_child_tables(employee, instructor, INSTRUCTOR_CHILD_TABLE_FIELDNAMES)
		instructor.flags.ignore_mandatory = True
		instructor.flags.ignore_college_email_domain_check = True
		instructor.insert(ignore_permissions=True)
		frappe.db.set_value("Instructor", instructor.name, "employee", employee.name)
		return instructor.name
	except Exception:
		frappe.log_error(
			frappe.get_traceback(), f"Could not auto-create Instructor for Employee {employee.name}"
		)
		frappe.msgprint(
			_("The Employee was created, but the matching Instructor record could not be "
				"created automatically. Please create it manually."),
			title=_("Instructor Record Not Created"),
			indicator="orange",
		)
		return None


ACADEMIC_CATEGORY = "Academic Staff"
NON_ACADEMIC_CATEGORY = "Non-Academic / Other Staff"
HR_ROLES = ("HR User", "HR Manager", "System Manager")
APPLICANT_DOCTYPE = "Employee Job Applicant"

# Payload keys accepted for each applicant child table. Every one of these
# tables now points directly at the same child DocType Employee uses (see
# employee_job_applicant.json), so the fieldnames here ARE the real fieldnames
# on the live Jameah * DocTypes - no aliasing in either direction.
TABLE_FIELD_MAP = {
	"academic_qualifications": [
		"is_last_academic_data_record",
		"degree",
		"specialization",
		"minor",
		"assessment_type",
		"gpa",
		"gpa_type",
		"study_type",
		"institute",
		"faculty",
		"qualification_date",
		"graduation_year",
		"city",
		"country",
	],
	"academic_work_experience": [
		"is_latest_work_experience_record",
		"current_academic_year_date",
		"employment_status_code",
		"designation",
		"institute_code",
		"location_code",
		"section_code",
		"employee_number",
		"profession_rank_code",
		"hiring_date",
		"start_date",
		"end_date",
		"job_duties",
		"accommodation_code",
	],
	"previous_work_experience": [
		"profession",
		"organization_name",
		"city",
		"country",
		"department",
		"section",
		"start_work_date",
		"end_work_date",
		"functional_tasks",
	],
	"professional_certificates_training": [
		"course_name",
		"course_type",
		"provider",
		"duration",
		"date",
		"city",
		"country",
	],
	"research_publications": [
		"title",
		"journal",
		"publication_date",
		"link",
	],
	"awards": [
		"award_name",
		"organization",
		"date",
	],
}

# The applicant's child tables and Employee's child tables are now the exact
# same DocType (see employee_job_applicant.json / Employee's custom_jameah_*
# fields), so converting an applicant into an Employee is a straight
# field-for-field copy - just the target fieldname on Employee differs.
EMPLOYEE_CHILD_TABLE_MAP = {
	"academic_qualifications": "custom_jameah_qualifications",
	"academic_work_experience": "custom_jameah_experience",
	"previous_work_experience": "custom_jameah_previous_experience",
	"professional_certificates_training": "custom_jameah_training",
	"research_publications": "custom_jameah_publications",
	"awards": "custom_jameah_awards",
}


def is_hr_admin():
	if frappe.session.user == "Guest":
		return False
	roles = frappe.get_roles()
	return any(role in roles for role in HR_ROLES)


def get_application_link(token=None):
	if not token:
		return None
	return frappe.db.get_value(
		"Job Application Link",
		{"generated_token": token},
		["name", "application_category", "role", "is_active", "valid_from", "valid_until"],
		as_dict=True,
	)


def validate_application_link(token=None):
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
	payload = frappe.parse_json(data) if isinstance(data, str) else (data or frappe.form_dict)
	payload = normalize_payload(payload)

	token = token or frappe.form_dict.get("token")
	link = None
	if token:
		is_valid, reason, link = validate_application_link(token)
		if not is_valid:
			frappe.throw(_(get_invalid_message(reason)))

	if link:
		application_category = link.application_category
		role = link.role
	else:
		application_category = payload.get("application_category") or ACADEMIC_CATEGORY
		role = payload.get("role")

	validate_payload(payload, application_category)

	doc = frappe.new_doc(APPLICANT_DOCTYPE)
	doc.applicant_name = payload.get("full_name")
	doc.email_id = payload.get("email")
	doc.phone_number = payload.get("phone")
	doc.status = "Pending"
	doc.role = role
	doc.designation = _get_or_create_designation_for_role(role)
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

	append_child_rows(doc, payload)

	# The qualification/experience/training child tables are now the same
	# Jameah * DocTypes Employee uses, which carry ministry-mandated required
	# fields (e.g. Link fields with no seeded lookup options yet). A public
	# applicant can't always satisfy those, so intake stays permissive here;
	# HR reviews and completes the record before Accept -> Create Employee.
	doc.flags.ignore_permissions = True
	doc.flags.ignore_mandatory = True
	doc.insert()

	files = getattr(frappe.request, "files", None) if frappe.request else None
	if files and files.get("resume"):
		uploaded = files.get("resume")
		file_doc = save_file(
			uploaded.filename,
			uploaded.stream.read(),
			doc.doctype,
			doc.name,
			folder=None,
			decode=False,
			is_private=1,
		)
		doc.db_set("resume_attachment", file_doc.file_url)

	return {"name": doc.name, "status": doc.status}


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

	# gender is deliberately NOT set explicitly here: Employee.gender (like
	# Employee Job Applicant.gender) was repointed from the real Gender
	# doctype to Jameah Ministry Code by setup_ministry_lookup_fields.py,
	# so the raw code value (e.g. "Gender::1") copy_matching_employee_fields
	# already pulls from the applicant's submitted JSON above is correct
	# as-is - translating it here would break the Link instead of fixing it.

	for source_field, target_field in EMPLOYEE_CHILD_TABLE_MAP.items():
		copy_child_table(applicant, employee, source_field, target_field)

	# The public application form cannot realistically capture every field the
	# ministry customizations mark mandatory on Employee/Employee child tables
	# (e.g. Branch, some Jameah Academic Qualification codes). Rather than
	# blocking the accept -> convert workflow, create the Employee as a draft
	# HR can complete; ignore_mandatory mirrors the ignore_permissions flag
	# already used for the applicant's own insert in submit_application.
	employee.flags.ignore_mandatory = True
	employee.insert(ignore_permissions=True)

	instructor_name = None
	if applicant.role == INSTRUCTOR_ROLE_NAME:
		instructor_name = _create_instructor_from_employee(applicant, employee)

	return {"employee": employee.name, "instructor": instructor_name}


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
		validate_email_address(payload.get("email"), throw=True)

	arabic_pattern = re.compile("^[؀-ۿݐ-ݿࢠ-ࣿ\\s'’-]+$")
	for fieldname in (
		"custom_first_name_ar",
		"custom_second_name_ar",
		"custom_third_name_ar",
		"custom_last_name_ar",
	):
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
	payload.setdefault("full_name", build_full_name(payload))
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
		if rows:
			append_rows(doc, fieldname, rows)


def append_rows(doc, fieldname, rows):
	allowed_fields = TABLE_FIELD_MAP.get(fieldname, [])
	for row in rows:
		if not isinstance(row, dict):
			continue
		cleaned = {key: row.get(key) for key in allowed_fields if row.get(key) not in (None, "")}
		if cleaned:
			doc.append(fieldname, cleaned)


def copy_child_table(source, target, source_field, target_field):
	rows = source.get(source_field) or []
	if not rows:
		return
	allowed_fields = TABLE_FIELD_MAP.get(source_field, [])
	for row in rows:
		cleaned = {key: row.get(key) for key in allowed_fields if row.get(key) not in (None, "")}
		if cleaned:
			target.append(target_field, cleaned)


def copy_matching_employee_fields(source, target):
	"""Copy scalar fields submitted by the applicant when Employee has the same fieldname."""
	data = frappe.parse_json(source.application_details_json or "{}")
	for field in frappe.get_meta("Employee").fields:
		if field.fieldtype in ("Table", "Table MultiSelect", "Section Break", "Column Break", "Tab Break", "HTML"):
			continue
		if field.fieldname in ("name", "company", "last_name", "first_name", "employee_name"):
			continue

		if field.fieldname in data and target.meta.has_field(field.fieldname):
			setattr(target, field.fieldname, data[field.fieldname])
			continue

		custom_fieldname = "custom_" + field.fieldname
		if target.meta.has_field(field.fieldname) and getattr(source, custom_fieldname, None):
			setattr(target, field.fieldname, getattr(source, custom_fieldname))


def copy_payload_fields_to_applicant(doc, payload):
	"""Persist every scalar form value in a real Applicant field when available."""
	applicant_meta = doc.meta
	employee_meta = frappe.get_meta("Employee")
	for fieldname, value in payload.items():
		if isinstance(value, (list, dict)) or value in (None, ""):
			continue
		if applicant_meta.has_field(fieldname):
			setattr(doc, fieldname, value)
			continue
		if employee_meta.has_field(fieldname) and applicant_meta.has_field("custom_" + fieldname):
			setattr(doc, "custom_" + fieldname, value)


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
	parts = [
		payload.get("custom_first_name_en"),
		payload.get("custom_second_name_en"),
		payload.get("custom_third_name_en"),
		payload.get("custom_last_name_en"),
	]
	if not any(parts):
		parts = [
			payload.get("first_name"),
			payload.get("middle_name"),
			payload.get("last_name"),
		]
	return " ".join(part for part in parts if part).strip()
