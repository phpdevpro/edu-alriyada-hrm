
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


DOCTYPE = "Jameah Ministry Code"


def _field(fieldname, label, fieldtype, insert_after, **kwargs):
	field = {
		"fieldname": fieldname,
		"label": label,
		"fieldtype": fieldtype,
		"insert_after": insert_after,
	}
	field.update(kwargs)
	return field


def _section(fieldname, label, insert_after):
	return {
		"fieldname": fieldname,
		"label": label,
		"fieldtype": "Section Break",
		"insert_after": insert_after,
	}


def _set_required(doctype, fieldname, required):
	make_property_setter(
		doctype,
		fieldname,
		"reqd",
		1 if required else 0,
		"Check",
		validate_fields_for_doctype=False,
	)


def _build_jameah_fields(anchor_field):
	return [
		_section("custom_jameah_demographics", "Employee Personal Information", anchor_field),
		_field(
			"custom_first_name_en",
			"First Name (English)",
			"Data",
			"custom_jameah_demographics",
			reqd=1,
		),
		_field(
			"custom_second_name_en",
			"Second Name (English)",
			"Data",
			"custom_first_name_en",
			reqd=1,
		),
		_field(
			"custom_third_name_en",
			"Third Name (English)",
			"Data",
			"custom_second_name_en",
		),
		_field(
			"custom_last_name_en",
			"Fourth Name (English)",
			"Data",
			"custom_third_name_en",
			reqd=1,
		),
		_field(
			"custom_arabic_names_col",
			"",
			"Column Break",
			"custom_last_name_en",
		),
		_field(
			"custom_first_name_ar",
			"First Name (Arabic)",
			"Data",
			"custom_arabic_names_col",
			reqd=1,
		),
		_field(
			"custom_second_name_ar",
			"Second Name (Arabic)",
			"Data",
			"custom_first_name_ar",
			reqd=1,
		),
		_field(
			"custom_third_name_ar",
			"Third Name (Arabic)",
			"Data",
			"custom_second_name_ar",
		),
		_field(
			"custom_last_name_ar",
			"Fourth Name (Arabic)",
			"Data",
			"custom_third_name_ar",
			reqd=1,
		),
		_section("custom_jameah_identity", "Identity Details", "custom_last_name_ar"),
		_field(
			"custom_identity_type",
			"Identity type",
			"Link",
			"custom_jameah_identity",
			options=DOCTYPE,
			reqd=1,
		),
		_field(
			"custom_identity_number",
			"Identity Civil Registry in the Kingdom",
			"Data",
			"custom_identity_type",
		),
		_field(
			"custom_identity_issue_date",
			"Identity Issue Date",
			"Date",
			"custom_identity_number",
		),
		_field(
			"custom_identity_issue_place",
			"Identity Issue Place",
			"Link",
			"custom_identity_issue_date",
			options=DOCTYPE,
		),
		_field(
			"custom_original_home_id_number",
			"ID number in the country of origin for non-Saudis",
			"Data",
			"custom_identity_issue_place",
		),
		_field(
			"custom_ministry_place_of_birth",
			"Place of Birth",
			"Link",
			"custom_original_home_id_number",
			options=DOCTYPE,
		),
		_field(
			"custom_jameah_nationality",
			"Nationality",
			"Link",
			"custom_ministry_place_of_birth",
			options=DOCTYPE,
			reqd=1,
		),
		_field(
			"custom_ministry_religion",
			"Religion",
			"Link",
			"custom_jameah_nationality",
			options=DOCTYPE,
		),
		_field(
			"custom_is_special_needs",
			"Is Special Needs",
			"Check",
			"custom_ministry_religion",
			default=0,
		),
		_field(
			"custom_ministry_special_needs_type",
			"Type of special needs",
			"Link",
			"custom_is_special_needs",
			options=DOCTYPE,
		),
		_section("custom_jameah_contact", "Work Contact Details", "custom_ministry_special_needs_type"),
		_field(
			"custom_work_telephone_number",
			"Work Telephone Number",
			"Data",
			"custom_jameah_contact",
			options="Phone",
		),
		_field(
			"custom_work_telephone_extention_number",
			"Work Telephone Extension Number",
			"Data",
			"custom_work_telephone_number",
			options="Phone",
		),
	]


def add_jameah_fields():
	# Keep Employee and Instructor aligned with the same Jameah field set.
	custom_fields = {
		"Employee": _build_jameah_fields("employee_name"),
		"Instructor": _build_jameah_fields("instructor_name"),
	}

	create_custom_fields(custom_fields, update=True)

	# Align core Employee validation with the ministry requirements.
	_set_required("Employee", "middle_name", 1)
	_set_required("Employee", "personal_email", 1)
	_set_required("Employee", "cell_number", 1)

	frappe.clear_cache(doctype="Employee")
	frappe.clear_cache(doctype="Instructor")
	print("Injected Jameah fields into Employee and Instructor Doctypes.")


def execute():
	add_jameah_fields()
	frappe.db.commit()
