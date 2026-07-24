import frappe


def execute():
	sequence = [
		"custom_first_name_en", "custom_second_name_en", "custom_third_name_en", "custom_last_name_en",
		"custom_first_name_ar", "custom_second_name_ar", "custom_third_name_ar", "custom_last_name_ar",
		"custom_identity_type", "custom_identity_number", "custom_identity_issue_date", "custom_identity_issue_place",
		"custom_original_home_id_number", "custom_ministry_place_of_birth", "custom_jameah_nationality", "custom_ministry_religion",
		"custom_is_special_needs", "custom_ministry_special_needs_type", "custom_work_telephone_number", "custom_work_telephone_extention_number",
		"custom_first_name", "custom_middle_name", "custom_last_name", "custom_employee_name", "custom_salutation", "custom_employee_number",
		"custom_date_of_joining", "custom_company", "custom_cell_number", "custom_personal_email", "custom_company_email",
		"custom_prefered_contact_email", "custom_prefered_email", "custom_user_id", "custom_permanent_address", "custom_current_address",
		"custom_passport_number", "custom_date_of_issue", "custom_valid_upto", "custom_place_of_issue", "custom_marital_status",
		"custom_blood_group", "custom_family_background", "custom_health_details", "custom_branch", "custom_reports_to", "custom_holiday_list",
		"custom_salary_mode", "custom_bank_name", "custom_bank_ac_no", "custom_salary_currency", "custom_ctc", "custom_contract_end_date",
		"custom_notice_number_of_days", "custom_date_of_retirement", "custom_attendance_device_id", "custom_iban",
	]
	for idx, fieldname in enumerate(sequence, start=138):
		name = frappe.db.get_value("Custom Field", {"dt": "Employee Job Applicant", "fieldname": fieldname}, "name")
		if name:
			frappe.db.set_value("Custom Field", name, "idx", idx, update_modified=False)
	frappe.clear_cache(doctype="Employee Job Applicant")
