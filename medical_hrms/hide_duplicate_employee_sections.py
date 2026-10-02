import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

# Core HRMS's Employee doctype ships its own Education / Work History
# sections (education, educational_qualification, internal_work_history,
# external_work_history, history_in_company, previous_work_experience).
# This app replaced them with the Jameah ministry-mandated equivalents
# (custom_jameah_qualifications, custom_jameah_experience,
# custom_jameah_previous_experience, etc. - see create_child_tables.py),
# so the original core sections are hidden here to avoid showing both side
# by side. These were previously only a manual Customize Form change on one
# site (never captured in a script), so a fresh install/migrate didn't hide
# them - see also employee_number/naming_series below, which were tweaked
# the same way.
EMPLOYEE_HIDDEN_FIELDS = [
	"education",
	"educational_qualification",
	"external_work_history",
	"history_in_company",
	"internal_work_history",
	"previous_work_experience",
	"employee_number",
]

EMPLOYEE_VISIBLE_FIELDS = [
	"naming_series",
]


def execute():
	for fieldname in EMPLOYEE_HIDDEN_FIELDS:
		make_property_setter("Employee", fieldname, "hidden", 1, "Check")
	for fieldname in EMPLOYEE_VISIBLE_FIELDS:
		make_property_setter("Employee", fieldname, "hidden", 0, "Check")

	frappe.clear_cache(doctype="Employee")
	frappe.db.commit()
	print("Hidden duplicate standard Employee sections in favor of the Jameah equivalents.")
