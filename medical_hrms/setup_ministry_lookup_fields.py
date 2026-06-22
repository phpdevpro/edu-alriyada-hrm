import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from medical_hrms.ministry_lookup_config import EMPLOYEE_EDUCATION_MINISTRY_FIELDS, EMPLOYEE_MINISTRY_FIELDS


DOCTYPE = "Jameah Ministry Code"


CODE_CATEGORY_OPTIONS = [
	"Academic ranks",
	"Admission to study",
	"Coding academic departments",
	"Coding cities and governora",
	"Coding of academic degrees",
	"Coding of educational insti",
	"College Coding Guide",
	"Cumulative GPA",
	"Detailed field - 37",
	"Educational level - 33",
	"Gender",
	"General situation",
	"Identity type",
	"Included specializations - 39",
	"Job ranks",
	"Job status",
	"Narrow Field - 36",
	"Nationality",
	"Nature of the work of the",
	"Program duration coding",
	"Registration status",
	"Religions",
	"Residential status coding",
	"Scholarship Classificatio",
	"Social status",
	"Specialization Coding Guide",
	"Specializations - 38",
	"Student Bonus",
	"Student Evaluation Coding",
	"Student transfer status",
	"Study type coding",
	"Sub-level education - 34",
	"Summer registration status",
	"Type of appointment",
	"Type of grant",
	"Type of secondary school ce",
	"Type of special needs",
	"Type of specialization",
	"Wide Field - 35",
]


def _link_field(field):
	return {
		"fieldname": field["fieldname"],
		"label": field["label"],
		"fieldtype": "Link",
		"options": DOCTYPE,
		"insert_after": field["insert_after"],
		"description": "",
	}


def _plain_field(fieldname, label, fieldtype, insert_after, **kwargs):
	field = {
		"fieldname": fieldname,
		"label": label,
		"fieldtype": fieldtype,
		"insert_after": insert_after,
	}
	field.update(kwargs)
	return field


def _configure_ministry_code_doctype():
	if not frappe.db.exists("DocType", DOCTYPE):
		print(f"Skipped search configuration: {DOCTYPE} not found")
		return

	frappe.db.set_value(
		"DocType",
		DOCTYPE,
		{
			"title_field": "name_english",
			"search_fields": "name_english",
			"show_title_field_in_link": 1,
		},
		update_modified=False,
	)

	frappe.db.delete(
		"Property Setter",
		{
			"doc_type": DOCTYPE,
			"field_name": "code_category",
			"property": ["in", ["fieldtype", "options"]],
		},
	)
	make_property_setter(DOCTYPE, "code_category", "fieldtype", "Select", "Data")
	make_property_setter(DOCTYPE, "code_category", "options", "\n".join(CODE_CATEGORY_OPTIONS), "Text")


def _configure_existing_employee_fields():
	frappe.db.delete(
		"Property Setter",
		{
			"doc_type": "Employee",
			"field_name": "gender",
			"property": "options",
		},
	)
	make_property_setter(
		"Employee",
		"gender",
		"options",
		DOCTYPE,
		"Link",
	)


def _backfill_employee_gender_values():
	gender_codes = frappe.get_all(
		DOCTYPE,
		filters={"code_category": "Gender"},
		fields=["name", "name_english"],
	)
	for gender_code in gender_codes:
		frappe.db.sql(
			"""
			update `tabEmployee`
			set gender = %(code_name)s
			where gender = %(gender_label)s
			""",
			{
				"code_name": gender_code.name,
				"gender_label": gender_code.name_english,
			},
		)


def _set_employee_custom_field_order():
	identity_anchor = "custom_last_name_ar" if frappe.get_meta("Employee").has_field("custom_last_name_ar") else "employee_name"
	field_order = [
		("custom_jameah_identity", identity_anchor),
		("custom_identity_type", "custom_jameah_identity"),
		("custom_jameah_nationality", "custom_identity_type"),
		("custom_identity_number", "custom_jameah_nationality"),
		("custom_original_home_id_number", "custom_identity_number"),
		("custom_identity_issue_date", "custom_original_home_id_number"),
		("custom_identity_issue_place", "custom_identity_issue_date"),
		("custom_ministry_place_of_birth", "custom_identity_issue_place"),
		("custom_jameah_ministry_codes_section", "custom_ministry_place_of_birth"),
		("custom_is_special_needs", "custom_jameah_ministry_codes_section"),
		("custom_ministry_special_needs_type", "custom_is_special_needs"),
		("custom_ministry_religion", "custom_ministry_special_needs_type"),
		("custom_ministry_work_city", "custom_ministry_religion"),
		("custom_ministry_job_rank", "custom_ministry_work_city"),
		("custom_ministry_accommodation", "custom_ministry_job_rank"),
	]

	for idx, (fieldname, insert_after) in enumerate(field_order, start=18):
		custom_field = f"Employee-{fieldname}"
		if not frappe.db.exists("Custom Field", custom_field):
			continue

		frappe.db.set_value(
			"Custom Field",
			custom_field,
			{"insert_after": insert_after, "idx": idx},
			update_modified=False,
		)

	if frappe.db.exists("Custom Field", "Employee-custom_jameah_nationality"):
		frappe.db.set_value(
			"Custom Field",
			"Employee-custom_jameah_nationality",
			"reqd",
			1,
			update_modified=False,
		)

	profile_table_order = [
		("custom_job_duties", "bio", 140),
		("custom_jameah_qualifications", "custom_job_duties", 141),
		("custom_jameah_experience", "custom_jameah_qualifications", 142),
		("custom_jameah_training", "custom_jameah_experience", 143),
		("custom_jameah_publications", "custom_jameah_training", 144),
		("custom_jameah_awards", "custom_jameah_publications", 145),
	]

	for fieldname, insert_after, idx in profile_table_order:
		custom_field = f"Employee-{fieldname}"
		if not frappe.db.exists("Custom Field", custom_field):
			continue

		frappe.db.set_value(
			"Custom Field",
			custom_field,
			{"insert_after": insert_after, "idx": idx},
			update_modified=False,
		)


def _skip_standard_fields(custom_fields):
	filtered_fields = {}
	for doctype, fields in custom_fields.items():
		meta = frappe.get_meta(doctype)
		filtered_fields[doctype] = []

		for field in fields:
			fieldname = field["fieldname"]
			if meta.has_field(fieldname) and not frappe.db.exists("Custom Field", f"{doctype}-{fieldname}"):
				continue
			filtered_fields[doctype].append(field)

	return filtered_fields


def execute():
	identity_anchor = "custom_last_name_ar" if frappe.get_meta("Employee").has_field("custom_last_name_ar") else "employee_name"
	employee_fields = [
		{
			"fieldname": "custom_jameah_identity",
			"label": "Identity Details",
			"fieldtype": "Section Break",
			"insert_after": identity_anchor,
		},
		_plain_field(
			"custom_identity_type",
			"Identity Type",
			"Link",
			"custom_jameah_identity",
			options=DOCTYPE,
		),
		_plain_field(
			"custom_jameah_nationality",
			"Nationality",
			"Link",
			"custom_identity_type",
			options=DOCTYPE,
			reqd=1,
		),
		_plain_field(
			"custom_identity_number",
			"Identity Number",
			"Data",
			"custom_jameah_nationality",
		),
		_plain_field(
			"custom_identity_issue_date",
			"Identity Issue Date",
			"Date",
			"custom_original_home_id_number",
		),
		_plain_field(
			"custom_identity_issue_place",
			"Identity Issue Place",
			"Link",
			"custom_identity_issue_date",
			options=DOCTYPE,
		),
		_plain_field(
			"custom_ministry_place_of_birth",
			"Place of Birth",
			"Link",
			"custom_identity_issue_place",
			options=DOCTYPE,
		),
		_plain_field(
			"custom_original_home_id_number",
			"ID Number in Country of Origin for Non-Saudis",
			"Data",
			"custom_identity_number",
		),
		{
			"fieldname": "custom_jameah_ministry_codes_section",
			"label": "Reference Codes",
			"fieldtype": "Section Break",
			"insert_after": "custom_jameah_nationality",
		},
		_plain_field(
			"custom_is_special_needs",
			"Has Special Needs",
			"Check",
			"custom_jameah_ministry_codes_section",
		),
		_plain_field(
			"custom_zip_code",
			"Zip Code",
			"Data",
			"current_address",
		),
		_plain_field(
			"custom_date_of_appointment_to_rank",
			"Date of Appointment to Rank",
			"Date",
			"final_confirmation_date",
		),
		_plain_field(
			"custom_job_duties",
			"Job Duties",
			"Small Text",
			"bio",
		),
	]
	employee_fields.extend(_link_field(field) for field in EMPLOYEE_MINISTRY_FIELDS)

	custom_fields = {
		"Employee": employee_fields,
		"Employee Education": [_link_field(field) for field in EMPLOYEE_EDUCATION_MINISTRY_FIELDS],
	}
	custom_fields["Employee Education"].append(
		_plain_field(
			"custom_date_of_scientific_degree",
			"Date of Obtaining Qualification",
			"Date",
			"custom_ministry_country",
		)
	)
	custom_fields["Jameah Work Experience"] = [
		_plain_field("city", "City", "Link", "company", options=DOCTYPE),
		_plain_field("country", "Country", "Link", "city", options=DOCTYPE),
		_plain_field("college_administration", "College / Administration", "Data", "country"),
		_plain_field("section", "Section", "Data", "college_administration"),
		_plain_field("job_duties", "Job Duties", "Small Text", "end_date"),
	]
	custom_fields["Jameah Training Course"] = [
		_plain_field("course_type", "Type", "Data", "course_name"),
		_plain_field("city", "City", "Link", "date", options=DOCTYPE),
		_plain_field("country", "Country", "Link", "city", options=DOCTYPE),
	]

	create_custom_fields(_skip_standard_fields(custom_fields), update=True)
	_configure_ministry_code_doctype()
	_configure_existing_employee_fields()
	_backfill_employee_gender_values()
	_set_employee_custom_field_order()
	frappe.clear_cache(doctype="Employee")
	frappe.clear_cache(doctype="Employee Education")
	frappe.clear_cache(doctype=DOCTYPE)
	frappe.db.commit()
	print("Created/updated Employee and Employee Education ministry lookup fields.")
