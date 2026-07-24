<<<<<<< HEAD

=======
>>>>>>> 31a5d95401dd98673b8dda7840d4f2a7600b47d9
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


<<<<<<< HEAD
JAMEAH_ACADEMIC_QUALIFICATION_MINISTRY_FIELDS = [
	{
		"fieldname": "degree",
		"label": "Academic qualification",
		"category": "Coding of academic degrees",
	},
	{
		"fieldname": "specialization",
		"label": "General Specialization (Main)",
		"category": "Specialization Coding Guide",
	},
	{
		"fieldname": "minor",
		"label": "Subspecialty",
		"category": "Specialization Coding Guide",
	},
	{
		"fieldname": "assessment_type",
		"label": "Appreciation",
		"category": "Cumulative GPA",
	},
	{
		"fieldname": "gpa_type",
		"label": "Rate type",
		"category": "Cumulative GPA",
	},
	{
		"fieldname": "study_type",
		"label": "Study system",
		"category": "Study type coding",
	},
	{
		"fieldname": "institute",
		"label": "Graduation Place",
		"category": "Coding of educational insti",
	},
	{
		"fieldname": "faculty",
		"label": "College",
		"category": "College Coding Guide",
	},
	{
		"fieldname": "city",
		"label": "The city",
		"category": "Coding cities and governora",
	},
	{
		"fieldname": "country",
		"label": "Country (Graduation Country)",
		"category": "Nationality",
	},
]


JAMEAH_ACADEMIC_WORK_EXPERIENCE_MINISTRY_FIELDS = [
	{
		"fieldname": "employment_status_code",
		"label": "Employee's job status",
		"category": "Job status",
	},
	{
		"fieldname": "institute_code",
		"label": "Educational entity",
		"category": "Coding of educational insti",
	},
	{
		"fieldname": "location_code",
		"label": "Geographical work location",
		"category": "Coding cities and governora",
	},
	{
		"fieldname": "section_code",
		"label": "Academic Department",
		"category": "Coding academic departments",
	},
	{
		"fieldname": "profession_rank_code",
		"label": "Job rank",
		"category": "Job ranks",
	},
	{
		"fieldname": "accommodation_code",
		"label": "Housing",
		"category": "Residential status coding",
	},
]


JAMEAH_PREVIOUS_WORK_EXPERIENCE_MINISTRY_FIELDS = [
	{
		"fieldname": "city",
		"label": "The city",
		"category": "Coding cities and governora",
	},
	{
		"fieldname": "country",
		"label": "Country",
		"category": "Nationality",
	},
]


=======
>>>>>>> 31a5d95401dd98673b8dda7840d4f2a7600b47d9
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


<<<<<<< HEAD
JAMEAH_PROFESSIONAL_CERTIFICATES_TRAINING_COURSES_MINISTRY_FIELDS = [
	{
		"fieldname": "course_city",
=======
JAMEAH_TRAINING_COURSE_MINISTRY_FIELDS = [
	{
		"fieldname": "city",
>>>>>>> 31a5d95401dd98673b8dda7840d4f2a7600b47d9
		"label": "City",
		"category": "Coding cities and governora",
	},
	{
<<<<<<< HEAD
		"fieldname": "course_country",
=======
		"fieldname": "country",
>>>>>>> 31a5d95401dd98673b8dda7840d4f2a7600b47d9
		"label": "Country",
		"category": "Nationality",
	},
]


MINISTRY_LOOKUP_FIELD_MAP = {
	"Employee": EMPLOYEE_EXISTING_MINISTRY_FIELDS + EMPLOYEE_MINISTRY_FIELDS,
	"Employee Education": EMPLOYEE_EDUCATION_MINISTRY_FIELDS,
<<<<<<< HEAD
	"Jameah Academic Qualification": JAMEAH_ACADEMIC_QUALIFICATION_MINISTRY_FIELDS,
	"Jameah Academic Work Experience": JAMEAH_ACADEMIC_WORK_EXPERIENCE_MINISTRY_FIELDS,
	"Jameah Previous Work Experience": JAMEAH_PREVIOUS_WORK_EXPERIENCE_MINISTRY_FIELDS,
	"Jameah Professional Certificates and Training Courses": JAMEAH_PROFESSIONAL_CERTIFICATES_TRAINING_COURSES_MINISTRY_FIELDS,
=======
	"Jameah Work Experience": JAMEAH_WORK_EXPERIENCE_MINISTRY_FIELDS,
	"Jameah Training Course": JAMEAH_TRAINING_COURSE_MINISTRY_FIELDS,
>>>>>>> 31a5d95401dd98673b8dda7840d4f2a7600b47d9
}


def get_ministry_lookup_category(doctype: str, fieldname: str) -> str | None:
	for field in MINISTRY_LOOKUP_FIELD_MAP.get(doctype, []):
		if field["fieldname"] == fieldname:
			return field["category"]
	return None
