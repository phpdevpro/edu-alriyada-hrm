import frappe


def execute():
	for field in frappe.get_all("Custom Field", filters={"dt": "Employee Job Applicant"}, pluck="name"):
		frappe.delete_doc("Custom Field", field, force=True, ignore_permissions=True)
	frappe.clear_cache(doctype="Employee Job Applicant")
