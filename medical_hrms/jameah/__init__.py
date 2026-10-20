"""Ministry of Education (Jameah) integration: code crosswalk and database views.

after_migrate runs execute(): fills the Jameah Settings values that are
certain, refreshes the Jameah Code Map and (re)creates the views.
"""
import frappe
from frappe.utils import get_url

SETTINGS = "Jameah Settings"


def _set_if_empty(settings, field, value):
	if value and not settings.get(field):
		settings.set(field, value)
		return True
	return False


def ensure_settings():
	"""Pre-fill only values that are certain; everything else is HR/Academic Affairs' decision."""
	settings = frappe.get_single(SETTINGS)
	changed = False
	# RCHS in the Ministry list of educational institutions.
	if frappe.db.get_value("Jameah Ministry Code", "Coding of educational insti::P18", "name_english") == "Al-Riyada College for Health Sciences":
		changed |= _set_if_empty(settings, "institute", "Coding of educational insti::P18")
	if frappe.db.exists("Jameah Ministry Code", "Nationality::101"):
		changed |= _set_if_empty(settings, "study_country", "Nationality::101")
	# Grades are on a 5-point scale (A+ = 5.0).
	if frappe.db.sql("SELECT MAX(point) FROM `tabGrade`")[0][0] == 5:
		changed |= _set_if_empty(settings, "gpa_type", "Cumulative GPA::1")
	changed |= _set_if_empty(settings, "employee_company", frappe.db.get_default("company"))
	changed |= _set_if_empty(settings, "file_base_url", get_url())
	if changed:
		settings.flags.ignore_permissions = True
		settings.save()


def execute():
	from medical_hrms.jameah import code_map, summary, views

	if not frappe.db.exists("DocType", "Jameah Ministry Code"):
		return
	frappe.db.add_index("Jameah Code Map", ["source_doctype", "source_value(100)", "code_category"], "source_lookup")
	frappe.db.add_index("Jameah Ministry Code", ["code_category", "ministry_code"], "category_code")
	ensure_settings()
	code_map.refresh()
	summary.ensure_table()
	views.create_views()
	frappe.db.commit()
	summary.refresh()
