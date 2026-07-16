import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


MINISTRY_CODE = "Jameah Ministry Code"


def _field(fieldname, label, fieldtype="Data", **kwargs):
	return {"fieldname": fieldname, "label": label, "fieldtype": fieldtype, **kwargs}


def _link(fieldname, label, **kwargs):
	return _field(fieldname, label, "Link", options=MINISTRY_CODE, **kwargs)


CHILD_DOCTYPES = {
	"Job Applicant Academic Qualification": [
		_link("subspecialty", "Subspecialty", in_list_view=1),
		_link("appreciation", "Appreciation", reqd=1, in_list_view=1),
		_field("graduation_rate", "Graduation Rate", "Float", reqd=1, in_list_view=1),
		_link("rate_type", "Rate Type", reqd=1),
		_link("study_system", "Study System", reqd=1),
		_field("graduation_place", "Graduation Place", reqd=1),
		_link("college", "College", reqd=1),
		_field(
			"qualification_date",
			"Date of Obtaining the Qualification",
			"Date",
			reqd=1,
			in_list_view=1,
		),
		_link("city", "City", reqd=1),
	],
	"Job Applicant Academic Experience": [
		_field("school_year_history", "School Year History", reqd=1, in_list_view=1),
		_link("employment_status", "Employee's Job Status", reqd=1, in_list_view=1),
		_field("educational_entity", "Educational Entity", reqd=1, in_list_view=1),
		_link("work_location", "Geographical Work Location", reqd=1),
		_link("academic_department", "Academic Department", reqd=1),
		_field("job_number", "Job Number"),
		_link("job_rank", "Job Rank", reqd=1),
		_field("appointment_to_rank_date", "Date of Appointment to the Rank", "Date"),
		_field("job_duties", "Job Duties", "Small Text"),
		_link("housing", "Housing"),
	],
	"Job Applicant Previous Experience": [
		_field("job_title", "Job Title", in_list_view=1),
		_field(
			"organization_name",
			"Educational Institution / Company",
			in_list_view=1,
		),
		_link("city", "City"),
		_link("country", "Country"),
		_field("college_administration", "College / Administration"),
		_field("section", "Section"),
		_field("start_date", "Start Date", "Date", in_list_view=1),
		_field("end_date", "End of Work Date", "Date", in_list_view=1),
		_field("job_duties", "Job Duties", "Small Text"),
	],
	"Job Applicant Training Course": [
		_field("course_type", "Type", in_list_view=1),
		_field("course_date", "Course History", "Date", in_list_view=1),
		_link("city", "City"),
		_link("country", "Country"),
	],
}


JOB_APPLICANT_FIELDS = [
	_field(
		"custom_ministry_personal_information",
		"Employee Personal Information",
		"Section Break",
		insert_after="country",
	),
	_link(
		"custom_ministry_special_needs_type",
		"Type of Special Needs",
		insert_after="custom_ministry_personal_information",
	),
	_field(
		"custom_ministry_identity_number",
		"Identity Civil Registry in the Kingdom",
		reqd=1,
		insert_after="custom_ministry_special_needs_type",
	),
	_link(
		"custom_ministry_place_of_birth",
		"Place of Birth",
		insert_after="custom_ministry_identity_number",
	),
	_field(
		"custom_ministry_origin_id_number",
		"ID Number in the Country of Origin for Non-Saudis",
		insert_after="custom_ministry_place_of_birth",
	),
	_link(
		"custom_ministry_religion",
		"Religion",
		insert_after="custom_ministry_origin_id_number",
	),
	_link(
		"custom_ministry_business_city",
		"City (Geographical Place of Business)",
		reqd=1,
		insert_after="custom_ministry_religion",
	),
	_field(
		"custom_ministry_zip_code",
		"Zip Code",
		insert_after="custom_ministry_business_city",
	),
	_field(
		"custom_ministry_academic_qualifications_section",
		"Employee Academic Qualifications",
		"Section Break",
		insert_after="custom_ministry_zip_code",
	),
	_field(
		"custom_ministry_academic_qualifications",
		"Academic Qualifications",
		"Table",
		options="Job Applicant Academic Qualification",
		insert_after="custom_ministry_academic_qualifications_section",
	),
	_field(
		"custom_ministry_academic_experience_section",
		"Employee Academic Experience",
		"Section Break",
		insert_after="custom_ministry_academic_qualifications",
	),
	_field(
		"custom_ministry_academic_experience",
		"Academic Experience",
		"Table",
		options="Job Applicant Academic Experience",
		insert_after="custom_ministry_academic_experience_section",
	),
	_field(
		"custom_ministry_previous_experience_section",
		"Employee Previous Experience",
		"Section Break",
		insert_after="custom_ministry_academic_experience",
	),
	_field(
		"custom_ministry_previous_experience",
		"Previous Experience",
		"Table",
		options="Job Applicant Previous Experience",
		insert_after="custom_ministry_previous_experience_section",
	),
	_field(
		"custom_ministry_training_section",
		"Employee Professional Certificates & Training Courses",
		"Section Break",
		insert_after="custom_ministry_previous_experience",
	),
	_field(
		"custom_ministry_training_courses",
		"Professional Certificates & Training Courses",
		"Table",
		options="Job Applicant Training Course",
		insert_after="custom_ministry_training_section",
	),
]


def _ensure_child_doctype(doctype_name, fields):
	if not frappe.db.exists("DocType", doctype_name):
		frappe.get_doc(
			{
				"doctype": "DocType",
				"name": doctype_name,
				"module": "Medical Hrms",
				"custom": 1,
				"istable": 1,
				"editable_grid": 1,
				"fields": fields,
			}
		).insert(ignore_permissions=True)
		return

	doc = frappe.get_doc("DocType", doctype_name)
	existing_fields = {field.fieldname: field for field in doc.fields}
	changed = False
	for definition in fields:
		fieldname = definition["fieldname"]
		if fieldname not in existing_fields:
			doc.append("fields", definition)
			changed = True
			continue

		field = existing_fields[fieldname]
		for property_name, value in definition.items():
			if field.get(property_name) != value:
				field.set(property_name, value)
				changed = True

	if changed:
		doc.save(ignore_permissions=True)


def execute():
	for doctype_name, fields in CHILD_DOCTYPES.items():
		_ensure_child_doctype(doctype_name, fields)

	create_custom_fields({"Job Applicant": JOB_APPLICANT_FIELDS}, update=True)
	frappe.clear_cache(doctype="Job Applicant")
	frappe.db.commit()
	print("Created/updated Job Applicant Ministry fields and child tables.")
