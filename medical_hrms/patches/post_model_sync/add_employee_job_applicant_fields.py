import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	custom_fields = [
		("custom_first_name_en", "First Name (English)"), ("custom_second_name_en", "Second Name (English)"),
		("custom_third_name_en", "Third Name (English)"), ("custom_last_name_en", "Fourth Name (English)"),
		("custom_first_name_ar", "First Name (Arabic)"), ("custom_second_name_ar", "Second Name (Arabic)"),
		("custom_third_name_ar", "Third Name (Arabic)"), ("custom_last_name_ar", "Fourth Name (Arabic)"),
		("custom_identity_type", "Identity Type"), ("custom_identity_number", "Identity Number"),
		("custom_identity_issue_date", "Identity Issue Date"), ("custom_identity_issue_place", "Identity Issue Place"),
		("custom_original_home_id_number", "Origin ID Number"), ("custom_ministry_place_of_birth", "Place of Birth"),
		("custom_jameah_nationality", "Nationality"), ("custom_ministry_religion", "Religion"),
		("custom_is_special_needs", "Is Special Needs"), ("custom_ministry_special_needs_type", "Special Needs Type"),
		("custom_work_telephone_number", "Work Telephone"), ("custom_work_telephone_extention_number", "Work Telephone Extension"),
	]
	create_custom_fields({"Employee Job Applicant": [{"fieldname": name, "fieldtype": "Date" if name.endswith("_date") else "Data", "label": label} for name, label in custom_fields]}, update=True)
	fields = [
		("employee_name", "Applicant Name"), ("personal_email", "Personal Email"), ("cell_number", "Mobile"),
		("company", "Company"), ("first_name", "First Name"), ("middle_name", "Middle Name"),
		("last_name", "Last Name"), ("salutation", "Salutation"), ("employee_number", "Employee Number"),
		("date_of_joining", "Date of Joining"), ("company_email", "Company Email"),
		("prefered_contact_email", "Preferred Contact Email"), ("prefered_email", "Preferred Email"),
		("user_id", "User ID"), ("permanent_address", "Permanent Address"), ("current_address", "Current Address"),
		("passport_number", "Passport Number"), ("date_of_issue", "Date of Issue"), ("valid_upto", "Valid Upto"),
		("place_of_issue", "Place of Issue"), ("marital_status", "Marital Status"), ("blood_group", "Blood Group"),
		("family_background", "Family Background"), ("health_details", "Health Details"), ("branch", "Branch"),
		("reports_to", "Reports To"), ("holiday_list", "Holiday List"), ("salary_mode", "Salary Mode"),
		("bank_name", "Bank Name"), ("bank_ac_no", "Bank A/C No."), ("salary_currency", "Salary Currency"),
		("ctc", "CTC"), ("contract_end_date", "Contract End Date"), ("notice_number_of_days", "Notice (days)"),
		("date_of_retirement", "Date of Retirement"), ("attendance_device_id", "Attendance Device ID"),
		("iban", "IBAN"), ("permanent_accommodation_type", "Permanent Accommodation Type"),
		("current_accommodation_type", "Current Accommodation Type"),
	]
	create_custom_fields({"Employee Job Applicant": [{"fieldname": "custom_" + name, "fieldtype": "Data", "label": label} for name, label in fields]}, update=True)
