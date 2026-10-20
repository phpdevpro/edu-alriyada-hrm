"""Settings behind the HR Academic Schedules & Presence page (after_migrate).

- HR Settings: the "after hours" cut-off for the faculty report (16:00) and
  the Holiday List of official days off used for the academic timetable.
- Academic Event Type: "Suspends Regular Classes", so academic-calendar
  periods such as final exams or semester breaks drop out of the schedules.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

AFTER_HOURS_FIELD = "custom_faculty_after_hours_cutoff"
HOLIDAY_LIST_FIELD = "custom_academic_holiday_list"
SUSPENDS_FIELD = "custom_suspends_regular_classes"
SEEDED_KEY = "medical_hrms_suspending_event_types_seeded"
# Event types that normally replace the regular timetable. Seeded once;
# HR can change the tick on each Academic Event Type afterwards.
SUSPENDING_EVENT_TYPES = ("End of the Semester Vacation", "Final Exams", "Resit Final Exams")


def execute():
	create_custom_fields({
		"HR Settings": [
			{"fieldname": "custom_academic_presence_section", "fieldtype": "Section Break",
				"label": "Academic Schedules & Presence", "insert_after": "custom_remote_work_monthly_limit"},
			{"fieldname": AFTER_HOURS_FIELD, "fieldtype": "Time", "label": "Faculty After-hours Cut-off",
				"default": "16:00:00", "insert_after": "custom_academic_presence_section",
				"description": "The \"Faculty After 4 PM\" report lists faculty on campus after this time."},
			{"fieldname": HOLIDAY_LIST_FIELD, "fieldtype": "Link", "options": "Holiday List",
				"label": "Academic Holiday List", "insert_after": AFTER_HOURS_FIELD,
				"description": "Official days off (national holidays, weekends). No classes are scheduled on these dates. "
					"Leave empty to use the company's default Holiday List."},
		],
		"Academic Event Type": [
			{"fieldname": SUSPENDS_FIELD, "fieldtype": "Check", "label": "Suspends Regular Classes",
				"insert_after": "schedule_type",
				"description": "Tick for events during which the weekly timetable does not run (e.g. final exams, semester break)."},
		],
	}, update=True)

	settings = frappe.get_doc("HR Settings")
	if not settings.get(AFTER_HOURS_FIELD):
		settings.db_set(AFTER_HOURS_FIELD, "16:00:00", update_modified=False)

	if not frappe.db.get_global(SEEDED_KEY):
		for event_type in SUSPENDING_EVENT_TYPES:
			if frappe.db.exists("Academic Event Type", event_type):
				frappe.db.set_value("Academic Event Type", event_type, SUSPENDS_FIELD, 1, update_modified=False)
		frappe.db.set_global(SEEDED_KEY, "1")
	frappe.clear_cache(doctype="HR Settings")
	frappe.clear_cache(doctype="Academic Event Type")
