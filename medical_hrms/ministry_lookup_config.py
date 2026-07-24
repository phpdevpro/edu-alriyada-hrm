EMPLOYEE_EXISTING_MINISTRY_FIELDS = [
	{
		"fieldname": "gender",
		"label": "Gender",
		"category": "Gender",
	},
	{
		"fieldname": "custom_identity_type",
		"label": "Identity Type",
		"category": "Identity type",
	},
	{
		"fieldname": "custom_identity_issue_place",
		"label": "Identity Issue Place",
		"category": "Coding cities and governora",
	},
	{
		"fieldname": "custom_ministry_place_of_birth",
		"label": "Place of Birth",
		"category": "Coding cities and governora",
	},
	{
		"fieldname": "custom_jameah_nationality",
		"label": "Nationality",
		"category": "Nationality",
	},
]


EMPLOYEE_MINISTRY_FIELDS = [
	{
		"fieldname": "custom_ministry_special_needs_type",
		"label": "Special Needs Type",
		"category": "Type of special needs",
		"insert_after": "custom_is_special_needs",
	},
	{
		"fieldname": "custom_ministry_religion",
		"label": "Religion",
		"category": "Religions",
		"insert_after": "custom_ministry_special_needs_type",
	},
	{
		"fieldname": "custom_ministry_work_city",
		"label": "Work City",
		"category": "Coding cities and governora",
		"insert_after": "custom_ministry_religion",
	},
	{
		"fieldname": "custom_ministry_job_rank",
		"label": "Job Rank",
		"category": "Job ranks",
		"insert_after": "custom_ministry_work_city",
	},
	{
		"fieldname": "custom_ministry_accommodation",
		"label": "Accommodation",
		"category": "Residential status coding",
		"insert_after": "custom_ministry_job_rank",
	},
]


EMPLOYEE_EDUCATION_MINISTRY_FIELDS = [
	{
		"fieldname": "custom_ministry_scientific_degree",
		"label": "Academic Qualification",
		"category": "Coding of academic degrees",
		"insert_after": "qualification",
	},
	{
		"fieldname": "custom_ministry_major",
		"label": "General Specialization",
		"category": "Specialization Coding Guide",
		"insert_after": "custom_ministry_scientific_degree",
	},
	{
		"fieldname": "custom_ministry_minor",
		"label": "Subspecialty",
		"category": "Specialization Coding Guide",
		"insert_after": "custom_ministry_major",
	},
	{
		"fieldname": "custom_ministry_assessment_type",
		"label": "Appreciation",
		"category": "Cumulative GPA",
		"insert_after": "custom_ministry_minor",
	},
	{
		"fieldname": "custom_ministry_gpa_type",
		"label": "GPA Type",
		"category": "Cumulative GPA",
		"insert_after": "custom_ministry_assessment_type",
	},
	{
		"fieldname": "custom_ministry_study_type",
		"label": "Study Type",
		"category": "Study type coding",
		"insert_after": "custom_ministry_gpa_type",
	},
	{
		"fieldname": "custom_ministry_graduate_from",
		"label": "Graduation Institution",
		"category": "Coding of educational insti",
		"insert_after": "custom_ministry_study_type",
	},
	{
		"fieldname": "custom_ministry_faculty",
		"label": "College",
		"category": "College Coding Guide",
		"insert_after": "custom_ministry_graduate_from",
	},
	{
		"fieldname": "custom_ministry_city",
		"label": "Graduation City",
		"category": "Coding cities and governora",
		"insert_after": "custom_ministry_faculty",
	},
	{
		"fieldname": "custom_ministry_country",
		"label": "Graduation Country/Nationality",
		"category": "Nationality",
		"insert_after": "custom_ministry_city",
	},
]


JAMEAH_WORK_EXPERIENCE_MINISTRY_FIELDS = [
	{
		"fieldname": "city",
		"label": "City",
		"category": "Coding cities and governora",
	},
	{
		"fieldname": "country",
		"label": "Country",
		"category": "Nationality",
	},
]


JAMEAH_TRAINING_COURSE_MINISTRY_FIELDS = [
	{
		"fieldname": "city",
		"label": "City",
		"category": "Coding cities and governora",
	},
	{
		"fieldname": "country",
		"label": "Country",
		"category": "Nationality",
	},
]


MINISTRY_LOOKUP_FIELD_MAP = {
	"Employee": EMPLOYEE_EXISTING_MINISTRY_FIELDS + EMPLOYEE_MINISTRY_FIELDS,
	"Employee Education": EMPLOYEE_EDUCATION_MINISTRY_FIELDS,
	"Jameah Work Experience": JAMEAH_WORK_EXPERIENCE_MINISTRY_FIELDS,
	"Jameah Training Course": JAMEAH_TRAINING_COURSE_MINISTRY_FIELDS,
}


def get_ministry_lookup_category(doctype: str, fieldname: str) -> str | None:
	for field in MINISTRY_LOOKUP_FIELD_MAP.get(doctype, []):
		if field["fieldname"] == fieldname:
			return field["category"]
	return None
