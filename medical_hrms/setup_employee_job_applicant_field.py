import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

APPLICANT_DOCTYPE = "Employee Job Applicant"

EMPLOYEE_FIELDS = [
	{
		"fieldname": "custom_job_applicant",
		"label": "Job Applicant",
		"fieldtype": "Link",
		"options": APPLICANT_DOCTYPE,
		"insert_after": "custom_zip_code",
		"read_only": 1,
		"allow_on_submit": 1,
		"no_copy": 1,
	},
]


def execute():
	if not frappe.db.exists("DocType", APPLICANT_DOCTYPE):
		# Employee Job Applicant is created by the recruitment feature's own
		# doctype JSON during the same migrate; nothing to link yet if it
		# somehow isn't present.
		print(f"Skipped: {APPLICANT_DOCTYPE} not found.")
		return

	create_custom_fields({"Employee": EMPLOYEE_FIELDS}, update=True)
	frappe.clear_cache(doctype="Employee")
	frappe.db.commit()
	print("Created/updated Employee.custom_job_applicant field.")
