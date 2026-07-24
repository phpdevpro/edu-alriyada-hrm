import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	fields = [
		("custom_first_name_en", "First Name (English)", "Data"), ("custom_second_name_en", "Second Name (English)", "Data"),
		("custom_third_name_en", "Third Name (English)", "Data"), ("custom_last_name_en", "Fourth Name (English)", "Data"),
		("custom_first_name_ar", "First Name (Arabic)", "Data"), ("custom_second_name_ar", "Second Name (Arabic)", "Data"),
		("custom_third_name_ar", "Third Name (Arabic)", "Data"), ("custom_last_name_ar", "Fourth Name (Arabic)", "Data"),
		("custom_identity_type", "Identity Type", "Data"), ("custom_identity_number", "Identity Number", "Data"),
		("custom_identity_issue_date", "Identity Issue Date", "Date"), ("custom_identity_issue_place", "Identity Issue Place", "Data"),
		("custom_original_home_id_number", "Origin ID Number", "Data"), ("custom_ministry_place_of_birth", "Place of Birth", "Data"),
		("custom_jameah_nationality", "Nationality", "Data"), ("custom_ministry_religion", "Religion", "Data"),
		("custom_is_special_needs", "Is Special Needs", "Check"), ("custom_ministry_special_needs_type", "Special Needs Type", "Data"),
		("custom_work_telephone_number", "Work Telephone", "Data"), ("custom_work_telephone_extention_number", "Work Telephone Extension", "Data"),
		("first_name", "First Name", "Data"), ("middle_name", "Middle Name", "Data"), ("last_name", "Last Name", "Data"),
		("employee_name", "Full Name", "Data"), ("salutation", "Salutation", "Data"), ("employee_number", "Employee Number", "Data"),
		("date_of_joining", "Date of Joining", "Date"), ("company", "Company", "Data"), ("cell_number", "Mobile", "Data"),
		("personal_email", "Personal Email", "Data"), ("company_email", "Company Email", "Data"), ("prefered_contact_email", "Preferred Contact Email", "Data"),
		("prefered_email", "Preferred Email", "Data"), ("user_id", "User ID", "Data"), ("permanent_address", "Permanent Address", "Small Text"),
		("current_address", "Current Address", "Small Text"), ("permanent_accommodation_type", "Permanent Accommodation Type", "Data"),
		("current_accommodation_type", "Current Accommodation Type", "Data"), ("passport_number", "Passport Number", "Data"),
		("date_of_issue", "Date of Issue", "Date"), ("valid_upto", "Valid Upto", "Date"), ("place_of_issue", "Place of Issue", "Data"),
		("marital_status", "Marital Status", "Data"), ("blood_group", "Blood Group", "Data"), ("family_background", "Family Background", "Small Text"),
		("health_details", "Health Details", "Small Text"), ("branch", "Branch", "Data"), ("reports_to", "Reports To", "Data"),
		("holiday_list", "Holiday List", "Data"), ("salary_mode", "Salary Mode", "Data"), ("bank_name", "Bank Name", "Data"),
		("bank_ac_no", "Bank A/C No.", "Data"), ("salary_currency", "Salary Currency", "Data"), ("ctc", "CTC", "Float"),
		("contract_end_date", "Contract End Date", "Date"), ("notice_number_of_days", "Notice (days)", "Int"),
		("date_of_retirement", "Date of Retirement", "Date"), ("attendance_device_id", "Attendance Device ID", "Data"), ("iban", "IBAN", "Data"),
	]
	specs = []
	for fieldname, label, fieldtype in fields:
		if not frappe.db.exists("DocField", {"parent": "Employee Job Applicant", "fieldname": fieldname}) and not frappe.db.exists("Custom Field", {"dt": "Employee Job Applicant", "fieldname": "custom_" + fieldname}):
			specs.append({"fieldname": "custom_" + fieldname, "fieldtype": fieldtype, "label": label})
	if specs:
		create_custom_fields({"Employee Job Applicant": specs}, update=True)
