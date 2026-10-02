import frappe

from medical_hrms.create_child_tables import create_child_doctypes, link_tables_to_parents


def execute():
	create_child_doctypes()
	link_tables_to_parents()

	obsolete_employee_field = "Employee-custom_school_year_history"
	if frappe.db.exists("Custom Field", obsolete_employee_field):
		frappe.delete_doc("Custom Field", obsolete_employee_field, ignore_permissions=True)

	parent_field = "Employee-custom_jameah_experience"
	if frappe.db.exists("Custom Field", parent_field):
		frappe.db.set_value(
			"Custom Field",
			parent_field,
			"label",
			"Employee Academic Experience",
			update_modified=False,
		)

	frappe.clear_cache(doctype="Employee")
	frappe.clear_cache(doctype="Jameah Work Experience")
	frappe.db.commit()
	print("Updated Employee Academic Experience fields.")
