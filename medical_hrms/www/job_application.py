# Copyright (c) 2026, Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, format_datetime, getdate, nowdate
from medical_hrms.medical_hrms.recruitment.job_application import (
	ACADEMIC_CATEGORY,
	get_invalid_message,
	is_hr_admin,
	validate_application_link,
)


# Only the lookup categories this form uses are sent to the browser (the full table has ~10,000 rows).
FORM_CODE_CATEGORIES = [
	"Coding academic departments",
	"Coding cities and governora",
	"Coding of academic degrees",
	"Coding of educational insti",
	"Cumulative GPA",
	"Gender",
	"Identity type",
	"Job ranks",
	"Job status",
	"Nationality",
	"Religions",
	"Residential status coding",
	"Specialization Coding Guide",
	"Study type coding",
	"Type of special needs",
]


def get_context(context):
	context.no_cache = 1
	context.title = _("Employee Applicant")
	context.body_class = "job-application-page"

	token = frappe.form_dict.get("token")
	is_valid = False
	invalid_message = ""
	application_category = None
	role = None
	valid_until = None
	days_left = None
	is_admin_preview = False

	if token:
		is_valid, reason, link = validate_application_link(token)
		if is_valid:
			application_category = link.application_category
			role = link.role
			if link.valid_until:
				valid_until = format_datetime(link.valid_until, "d MMM yyyy")
				days_left = date_diff(getdate(link.valid_until), getdate(nowdate()))
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
	context.role = role
	context.valid_until = valid_until
	context.days_left = days_left
	context.is_admin_preview = is_admin_preview
	context.token = token
	context.job_application_config = {
		"token": token,
		"application_category": application_category,
		"role": role,
		"allow_category_override": is_admin_preview,
		"is_ar": (frappe.local.lang or "").lower().startswith("ar"),
		"page_title": _("Employee Applicant"),
		"ministry_codes": frappe.get_all(
			"Jameah Ministry Code",
			filters={"code_category": ["in", FORM_CODE_CATEGORIES]},
			fields=["name", "name_english", "name_arabic", "code_category"],
			order_by="name_english",
			ignore_permissions=True,
		),
	}
	context.company = frappe.db.get_default("company")
