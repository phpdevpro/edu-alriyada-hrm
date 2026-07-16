import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime, nowdate, validate_email_address
from frappe.utils.file_manager import save_file

ACADEMIC_CATEGORY = "Academic Staff"
NON_ACADEMIC_CATEGORY = "Non-Academic / Other Staff"
HR_ROLES = ("HR User", "HR Manager", "System Manager")
APPLICANT_DOCTYPE = "Medical HRMS Job Applicant"

TABLE_FIELD_MAP = {
	"education": [
		"school_univ",
		"qualification",
		"level",
		"year_of_passing",
		"class_per",
		"maj_opt_subj",
	],
	"work_experience": [
		"company_name",
		"designation",
		"salary",
		"address",
		"contact",
		"total_experience",
	],
	"skills": ["skill_name", "proficiency", "years_of_experience"],
	"training_courses": ["course_name", "provider", "completion_date", "duration"],
	"academic_certifications": [
		"certification_name",
		"issuing_body",
		"issue_date",
		"expiry_date",
		"certificate_id",
	],
	"teaching_experience": [
		"institution",
		"designation",
		"subject_area",
		"start_date",
		"end_date",
		"years",
	],
	"research_publications": ["title", "journal", "publication_date", "link"],
	"professional_memberships": [
		"organization",
		"membership_id",
		"start_date",
		"end_date",
		"status",
	],
	"awards": ["award_name", "organization", "award_date", "details"],
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
	token = token or frappe.form_dict.get("token")
	link = None

	if token:
		is_valid, reason, link = validate_application_link(token)
		if not is_valid:
			frappe.throw(_(get_invalid_message(reason)))
	elif frappe.session.user == "Guest":
		frappe.throw(_("Application link is required."))

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
	doc.application_details_json = frappe.as_json(payload)

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

	resume_file = frappe.request.files.get("resume_file") if hasattr(frappe, "request") else None
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

	copy_child_table(applicant, employee, "education", "education")
	copy_child_table(applicant, employee, "work_experience", "external_work_history")
	copy_child_table(applicant, employee, "skills", "custom_skills")
	copy_child_table(applicant, employee, "training_courses", "custom_training_courses")
	copy_child_table(applicant, employee, "academic_certifications", "custom_academic_certifications")
	copy_child_table(applicant, employee, "teaching_experience", "custom_teaching_experience")
	copy_child_table(applicant, employee, "research_publications", "custom_research_publications")
	copy_child_table(applicant, employee, "professional_memberships", "custom_professional_memberships")
	copy_child_table(applicant, employee, "awards", "custom_awards")

	employee.insert()
	return {"employee": employee.name}


def validate_payload(payload, application_category):
	required = {
		"full_name": "Full Name",
		"email": "Email",
		"phone": "Phone Number",
		"designation": "Designation",
		"department": "Department",
	}
	missing = [label for key, label in required.items() if not payload.get(key)]
	if missing:
		frappe.throw(_("Missing required fields: {0}").format(", ".join(missing)))

	if payload.get("email"):
		validate_email_address(payload.get("email"), True)

	if application_category == ACADEMIC_CATEGORY:
		# Only Academic Qualifications is required
		rows = payload.get("academic_qualifications") or []
		if not rows:
			frappe.throw(_("Academic Qualifications are required."))


def append_child_rows(doc, payload):
	payload_map = {
		"education": payload.get("education"),
		"work_experience": payload.get("work_experience"),
		"skills": payload.get("skills"),
		"training_courses": payload.get("training_courses"),
		"academic_certifications": payload.get("academic_certifications"),
		"teaching_experience": payload.get("teaching_experience"),
		"research_publications": payload.get("research_publications"),
		"professional_memberships": payload.get("professional_memberships"),
		"awards": payload.get("awards"),
	}

	for fieldname, rows in payload_map.items():
		append_rows(doc, fieldname, rows or [])


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

	for row in rows:
		cleaned = cleanup_child_row(row.as_dict())
		if cleaned:
			target.append(target_field, cleaned)


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
