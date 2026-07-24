import frappe


def execute():
	fieldnames = [
		"custom_old_parent", "custom_rgt", "custom_lft", "custom_feedback", "custom_reason_for_leaving",
		"custom_encashment_date", "custom_leave_encashed", "custom_new_workplace", "custom_held_on",
		"custom_relieving_date", "custom_resignation_letter_date", "custom_bio", "custom_health_insurance_no",
		"custom_health_insurance_provider", "custom_payroll_cost_center", "custom_shift_request_approver",
		"custom_leave_approver", "custom_expense_approver", "custom_default_shift", "custom_relation",
	]
	for fieldname in fieldnames:
		name = frappe.db.get_value("Custom Field", {"dt": "Employee Job Applicant", "fieldname": fieldname}, "name")
		if name:
			frappe.db.set_value("Custom Field", name, "hidden", 1, update_modified=False)
	frappe.clear_cache(doctype="Employee Job Applicant")
