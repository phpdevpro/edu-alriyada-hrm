import frappe
from frappe import _

from medical_hrms.medical_hrms.recruitment.job_application import (
	ACADEMIC_CATEGORY,
	get_invalid_message,
	is_hr_admin,
	validate_application_link,
)


def get_context(context):
	context.no_cache = 1
	context.title = _("Employee Applicant")
	context.body_class = "job-application-page"

	token = frappe.form_dict.get("token")
	is_valid = False
	invalid_message = ""
	application_category = None
	is_admin_preview = False

	if token:
		is_valid, reason, link = validate_application_link(token)
		if is_valid:
			application_category = link.application_category
		else:
			invalid_message = get_invalid_message(reason)
	elif is_hr_admin():
		is_valid = True
		is_admin_preview = True
		application_category = ACADEMIC_CATEGORY
	else:
		is_valid = True
		application_category = ACADEMIC_CATEGORY

	context.is_valid = is_valid
	context.invalid_message = invalid_message
	context.application_category = application_category
	context.is_admin_preview = is_admin_preview
	context.token = token

	context.designations = frappe.get_all(
		"Designation",
		fields=["name"],
		order_by="name",
		ignore_permissions=True,
	)
	context.departments = frappe.get_all(
		"Department",
		fields=["name"],
		order_by="name",
		ignore_permissions=True,
	)

	context.job_application_config = {
		"token": token,
		"application_category": application_category,
		"allow_category_override": is_admin_preview,
		"page_title": _("Employee Applicant"),
		"ministry_codes": frappe.get_all("Jameah Ministry Code", fields=["name", "name_english"], order_by="name_english", ignore_permissions=True),
	}
	context.company = frappe.db.get_default("company")
