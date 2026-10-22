"""Remove the unused copy of the applicant Ministry fields from HRMS's own Job Applicant.

The old setup_job_applicant_ministry_fields patch (run on 2026-09-11) added Ministry custom fields
and four custom child tables to HRMS's "Job Applicant". Recruitment uses our own "Employee Job
Applicant" instead, which has its own fields for the same data, so the copy was never filled and
only duplicated the form. It was removed by hand on the development site; this does the same on
any other site.

Nothing is deleted if it holds data: a field with a value on any Job Applicant, or a child table
with rows, is kept and reported.
"""
import frappe

FIELDS = (
	"custom_ministry_personal_information", "custom_ministry_special_needs_type", "custom_ministry_identity_number",
	"custom_ministry_place_of_birth", "custom_ministry_origin_id_number", "custom_ministry_religion",
	"custom_ministry_business_city", "custom_ministry_zip_code", "custom_ministry_academic_qualifications_section",
	"custom_ministry_academic_qualifications", "custom_ministry_academic_experience_section",
	"custom_ministry_academic_experience", "custom_ministry_previous_experience_section",
	"custom_ministry_previous_experience", "custom_ministry_training_section", "custom_ministry_training_courses",
)
CHILD_DOCTYPES = (
	"Job Applicant Academic Qualification", "Job Applicant Academic Experience",
	"Job Applicant Previous Experience", "Job Applicant Training Course",
)
DATA_TYPES = {"Data", "Link"}


def holds_data(fieldname, fieldtype):
	if fieldtype not in DATA_TYPES or not frappe.db.has_column("Job Applicant", fieldname):
		return False
	return bool(frappe.db.sql(f"SELECT 1 FROM `tabJob Applicant` WHERE IFNULL(`{fieldname}`, '') != '' LIMIT 1"))


def execute():
	kept = []
	for cf in frappe.get_all("Custom Field", filters={"dt": "Job Applicant", "fieldname": ["in", FIELDS]}, fields=["name", "fieldname", "fieldtype"]):
		if holds_data(cf.fieldname, cf.fieldtype):
			kept.append(cf.fieldname)
			continue
		frappe.delete_doc("Custom Field", cf.name, ignore_permissions=True, force=True)

	for doctype in CHILD_DOCTYPES:
		if not frappe.db.exists("DocType", {"name": doctype, "custom": 1}):
			continue
		if frappe.db.table_exists(doctype) and frappe.db.count(doctype):
			kept.append(doctype)
			continue
		frappe.delete_doc("DocType", doctype, ignore_permissions=True, force=True)

	if kept:
		print(f"Kept (they hold data, check before removing by hand): {', '.join(kept)}")
	frappe.clear_cache(doctype="Job Applicant")
