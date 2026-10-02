# Shared config describing which Employee/Employee Education/Jameah * child
# table fields are Jameah Ministry Code lookups, and which lookup category
# (Jameah Ministry Code.code_category) each one draws its options from.
# Consumed by ministry_lookup_validation.py (validates saved values are a
# code from the right category) and setup_ministry_lookup_fields.py /
# setup_employee_ministry_expected_fields.py (wires up the Link filters and
# field metadata so the UI only offers the right category's codes).

EMPLOYEE_EXISTING_MINISTRY_FIELDS = [
	{"fieldname": "gender", "label": "Gender", "category": "Gender"},
	{"fieldname": "custom_identity_type", "label": "Identity Type", "category": "Identity type"},
	{"fieldname": "custom_identity_issue_place", "label": "Identity Issue Place", "category": "Coding cities and governora"},
	{"fieldname": "custom_ministry_place_of_birth", "label": "Place of Birth", "category": "Coding cities and governora"},
	{"fieldname": "custom_jameah_nationality", "label": "Nationality", "category": "Nationality"},
]

EMPLOYEE_MINISTRY_FIELDS = [
	{"fieldname": "custom_ministry_special_needs_type", "label": "Special Needs Type", "category": "Type of special needs", "insert_after": "custom_is_special_needs"},
	{"fieldname": "custom_ministry_religion", "label": "Religion", "category": "Religions", "insert_after": "custom_ministry_special_needs_type"},
	{"fieldname": "custom_ministry_work_city", "label": "Work City", "category": "Coding cities and governora", "insert_after": "custom_ministry_religion"},
	{"fieldname": "custom_ministry_job_rank", "label": "Job Rank", "category": "Job ranks", "insert_after": "custom_ministry_work_city"},
	{"fieldname": "custom_ministry_accommodation", "label": "Accommodation", "category": "Residential status coding", "insert_after": "custom_ministry_job_rank"},
]

EMPLOYEE_EDUCATION_MINISTRY_FIELDS = [
	{"fieldname": "custom_ministry_scientific_degree", "label": "Academic Qualification", "category": "Coding of academic degrees", "insert_after": "qualification"},
	{"fieldname": "custom_ministry_major", "label": "General Specialization", "category": "Specialization Coding Guide", "insert_after": "custom_ministry_scientific_degree"},
	{"fieldname": "custom_ministry_minor", "label": "Subspecialty", "category": "Specialization Coding Guide", "insert_after": "custom_ministry_major"},
	{"fieldname": "custom_ministry_assessment_type", "label": "Appreciation", "category": "Cumulative GPA", "insert_after": "custom_ministry_minor"},
	{"fieldname": "custom_ministry_gpa_type", "label": "GPA Type", "category": "Cumulative GPA", "insert_after": "custom_ministry_assessment_type"},
	{"fieldname": "custom_ministry_study_type", "label": "Study Type", "category": "Study type coding", "insert_after": "custom_ministry_gpa_type"},
	{"fieldname": "custom_ministry_country", "label": "Graduation Country/Nationality", "category": "Nationality", "insert_after": "custom_ministry_study_type"},
]

JAMEAH_ACADEMIC_QUALIFICATION_MINISTRY_FIELDS = [
	{"fieldname": "degree", "label": "Degree", "category": "Coding of academic degrees"},
	{"fieldname": "specialization", "label": "Specialization", "category": "Specialization Coding Guide"},
	{"fieldname": "country", "label": "Country", "category": "Nationality"},
	{"fieldname": "minor", "label": "Subspecialty", "category": "Specialization Coding Guide"},
	{"fieldname": "assessment_type", "label": "Appreciation", "category": "Cumulative GPA"},
	{"fieldname": "gpa_type", "label": "Rate Type", "category": "Cumulative GPA"},
	{"fieldname": "study_type", "label": "Study Type", "category": "Study type coding"},
]

JAMEAH_WORK_EXPERIENCE_MINISTRY_FIELDS = [
	{"fieldname": "employment_status_code", "label": "Employee's Job Status", "category": "Job status"},
	{"fieldname": "institute_code", "label": "Educational Entity", "category": "Coding of educational insti"},
	{"fieldname": "location_code", "label": "Geographical Work Location", "category": "Coding cities and governora"},
	{"fieldname": "section_code", "label": "Academic Department", "category": "Coding academic departments"},
	{"fieldname": "profession_rank_code", "label": "Job Rank", "category": "Job ranks"},
	{"fieldname": "accommodation_code", "label": "Housing", "category": "Residential status coding"},
]

JAMEAH_TRAINING_COURSE_MINISTRY_FIELDS = [
	{"fieldname": "country", "label": "Country", "category": "Nationality"},
]

JAMEAH_PREVIOUS_WORK_EXPERIENCE_MINISTRY_FIELDS = [
	{"fieldname": "country", "label": "Country", "category": "Nationality"},
]

MINISTRY_LOOKUP_FIELD_MAP = {
	"Employee": EMPLOYEE_EXISTING_MINISTRY_FIELDS + EMPLOYEE_MINISTRY_FIELDS,
	"Employee Education": EMPLOYEE_EDUCATION_MINISTRY_FIELDS,
	"Jameah Work Experience": JAMEAH_WORK_EXPERIENCE_MINISTRY_FIELDS,
	"Jameah Training Course": JAMEAH_TRAINING_COURSE_MINISTRY_FIELDS,
	"Jameah Academic Qualification": JAMEAH_ACADEMIC_QUALIFICATION_MINISTRY_FIELDS,
	"Jameah Previous Work Experience": JAMEAH_PREVIOUS_WORK_EXPERIENCE_MINISTRY_FIELDS,
}


def get_ministry_lookup_category(doctype: str, fieldname: str) -> str | None:
	for field in MINISTRY_LOOKUP_FIELD_MAP.get(doctype, []):
		if field["fieldname"] == fieldname:
			return field["category"]
	return None
