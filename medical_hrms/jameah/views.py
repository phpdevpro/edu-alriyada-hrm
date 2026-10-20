"""Ministry (Jameah) database views for Students and Employees.

One view per section of MINISTRY_FIELD_MAPPING.html, with the spec's column
names, so the Jameah agent can read them directly. Each column is declared
once below (name, SQL, spec type, note); the SELECT, the documentation and
the verification tests are all built from that list.

Rules every view follows:
- Lookup columns carry the bare Ministry code (e.g. 101), never a record name.
  A code is emitted only when it is in the official Jameah Ministry Code list
  for that column's category; anything else is NULL, never a guess.
- Values from Education masters go through the Jameah Code Map (Verified rows
  only), because their own code columns are not all Ministry codes.
- Phone and other Integer columns are digits only; empty text becomes NULL.

Names are prefixed "jameah" (lowercase j) so they never collide with the
Education app's own viewJameah* views.
"""
import json
import os
import re

import frappe

SETTINGS = "Jameah Settings"
HIJRI_NEW_YEARS = json.load(open(os.path.join(os.path.dirname(__file__), "hijri_new_years.json")))


def q(value):
	return frappe.db.escape(value)


class View:
	def __init__(self, name, section, source, key):
		self.name, self.section, self.source, self.key = name, section, source, key
		self.columns = []  # (column, sql, spec_type, note)
		self.joins = []
		self.categories = {}  # Lookup column -> Ministry code category
		self.alias_category = {}

	def col(self, column, sql, spec_type="String", note=""):
		self.columns.append((column, sql, spec_type, note))
		used = {self.alias_category[a] for a in re.findall(r"(\w+)\.ministry_code", sql) if a in self.alias_category}
		if spec_type == "Lookup" and len(used) == 1:
			self.categories[column] = used.pop()
		return self

	def join(self, sql):
		if sql not in self.joins:
			self.joins.append(sql)

	# Code resolution -------------------------------------------------------
	def ministry(self, alias, link_expr, category):
		"""Value is a Jameah Ministry Code record name (Employee fields)."""
		self.alias_category[alias] = category
		self.join(f"LEFT JOIN `tabJameah Ministry Code` {alias} ON {alias}.name = {link_expr} AND {alias}.code_category = {q(category)}")
		return f"{alias}.ministry_code"

	def official(self, alias, code_expr, category):
		"""Value is a bare code (Student Ministry Detail); check it is in the official list."""
		self.alias_category[alias] = category
		self.join(
			f"LEFT JOIN `tabJameah Ministry Code` {alias} ON {alias}.name = CONCAT({q(category + '::')}, {code_expr}) "
			f"AND {alias}.code_category = {q(category)}")
		return f"{alias}.ministry_code"

	def mapped(self, alias, source, value_expr, category):
		"""Value from an Education master/select: resolve through a Verified Code Map row."""
		self.alias_category[alias] = category
		self.join(
			f"LEFT JOIN `tabJameah Code Map` {alias}_m ON {alias}_m.source_doctype = {q(source)} "
			f"AND {alias}_m.source_value = {value_expr} AND {alias}_m.code_category = {q(category)} AND {alias}_m.status = 'Verified'")
		self.join(
			f"LEFT JOIN `tabJameah Ministry Code` {alias} ON {alias}.name = {alias}_m.jameah_code AND {alias}.code_category = {q(category)}")
		return f"{alias}.ministry_code"

	def setting(self, alias, field, category):
		self.join("CROSS JOIN jameah_cfg cfg")
		return self.ministry(alias, f"cfg.{field}", category)

	def sql(self):
		cols = ",\n\t".join(f"{expr} AS `{name}`" for name, expr, _t, _n in self.columns)
		joins = "\n".join(self.joins)
		return f"SELECT\n\t{cols}\nFROM {self.source}\n{joins}"


def text(expr):
	return f"NULLIF(TRIM({expr}), '')"


def digits(expr):
	return f"NULLIF(REGEXP_REPLACE(IFNULL({expr}, ''), '[^0-9]', ''), '')"


def yes_no(expr):
	return f"(CASE {expr} WHEN 'Yes' THEN 1 WHEN 'No' THEN 0 END)"


def real_date(expr):
	# 1900-01-01 and similar placeholders from the data migration are not real dates.
	return f"(CASE WHEN {expr} >= '1920-01-01' THEN {expr} END)"


NULL = "CAST(NULL AS CHAR)"


def hijri_year(date_expr):
	"""Umm al-Qura Hijri year of a Gregorian date (table of 1 Muharram dates)."""
	cases = " ".join(f"WHEN {date_expr} >= '{start}' THEN {year}" for year, start in reversed(HIJRI_NEW_YEARS))
	return f"(CASE WHEN {date_expr} IS NULL THEN NULL {cases} END)"


# ---------------------------------------------------------------------------
# Shared building blocks

CFG_VIEW = "jameah_cfg"
CFG_FIELDS = ("institute", "college", "study_country", "study_location_city", "regular_study_type",
	"bridging_study_type", "gpa_type", "program_period", "program_period_unit", "file_base_url", "employee_company")


def cfg_view_sql():
	cols = ", ".join(f"MAX(CASE WHEN field = {q(f)} THEN value END) AS `{f}`" for f in CFG_FIELDS)
	return f"SELECT {cols} FROM `tabSingles` WHERE doctype = {q(SETTINGS)}"


# Employees reported to the Ministry as Employees: the configured company, and
# never teaching staff (an Instructor points at them) - those go as Faculty.
EMPLOYEE_POPULATION = f"""(
	SELECT e.* FROM `tabEmployee` e CROSS JOIN {CFG_VIEW} c0
	WHERE (IFNULL(c0.employee_company, '') = '' OR e.company = c0.employee_company)
	AND NOT EXISTS (
		SELECT 1 FROM `tabInstructor` i
		WHERE i.employee = e.name
		OR (IFNULL(e.user_id, '') != '' AND i.email = e.user_id)
		OR (IFNULL(e.company_email, '') != '' AND i.email = e.company_email))
) e"""


def employee_child(view_name, section, doctype, parentfield):
	v = View(view_name, section,
		f"`tab{doctype}` r JOIN {EMPLOYEE_POPULATION} ON e.name = r.parent AND r.parenttype = 'Employee' AND r.parentfield = {q(parentfield)}",
		key=("EmployeeId", "RecordId"))
	v.col("EmployeeId", "e.name", "Key", "Employee ID (record key).")
	v.col("RecordId", "r.name", "Key", "Row ID (record key).")
	return v


# ---------------------------------------------------------------------------
# Employees

def employee_views():
	views = []

	v = View("jameahEmployeePersonalInfo", "Employee Personal Information", EMPLOYEE_POPULATION, key=("EmployeeId",))
	v.col("EmployeeId", "e.name", "Key", "Employee ID (record key).")
	v.col("ArabicFirstName", text("e.custom_first_name_ar"))
	v.col("ArabicSecondName", text("e.custom_second_name_ar"))
	v.col("ArabicThirdName", text("e.custom_third_name_ar"))
	v.col("ArabicFourthName", text("e.custom_last_name_ar"), note="Arabic last name.")
	v.col("EnglishFirstName", f"COALESCE({text('e.custom_first_name_en')}, {text('e.first_name')})", note="Falls back to the HR first name.")
	v.col("EnglishSecondName", f"COALESCE({text('e.custom_second_name_en')}, {text('e.middle_name')})", note="Falls back to the HR middle name.")
	v.col("EnglishThirdName", text("e.custom_third_name_en"))
	v.col("EnglishFourthName", f"COALESCE({text('e.custom_last_name_en')}, {text('e.last_name')})", note="English last name; falls back to the HR last name.")
	v.col("IdentityTypeCode", v.ministry("it", "e.custom_identity_type", "Identity type"), "Lookup")
	v.col("SpecialNeedsTypeCode", v.ministry("sn", "e.custom_ministry_special_needs_type", "Type of special needs"), "Lookup")
	v.col("IdentityNumber", digits("e.custom_identity_number"), "Integer")
	v.col("BirthPlace", v.ministry("bp", "e.custom_ministry_place_of_birth", "Coding cities and governora"), "Lookup")
	v.col("GregorianBirthDate", real_date("e.date_of_birth"), "Date")
	v.col("PassportNumber", text("e.passport_number"))
	v.col("OriginalHomeIDNumber", text("e.custom_original_home_id_number"))
	v.col("IsMaleGender", f"(CASE {v.ministry('gn', 'e.gender', 'Gender')} WHEN '1' THEN 1 WHEN '2' THEN 0 END)", "Boolean", "1 = male, 0 = female.")
	v.col("NationalityCode", v.ministry("nt", "e.custom_jameah_nationality", "Nationality"), "Lookup")
	v.col("MaritalStatusCode", v.mapped("ms", "Employee.marital_status", "e.marital_status", "Social status"), "Lookup")
	v.col("ReligionCode", v.ministry("rl", "e.custom_ministry_religion", "Religions"), "Lookup")
	v.col("PostalAddress", text("e.current_address"))
	v.col("CityCode", v.ministry("wc", "e.custom_ministry_work_city", "Coding cities and governora"), "Lookup", "City of the place of work.")
	v.col("ZipCode", digits("e.custom_zip_code"), "Integer")
	v.col("Email", f"COALESCE({text('e.prefered_email')}, {text('e.company_email')}, {text('e.personal_email')})", note="Preferred, else company, else personal email.")
	v.col("HomeTelephoneNumber", digits("e.custom_home_telephone_number"), "Integer")
	v.col("WorkTelephoneNumber", digits("e.custom_work_telephone_number"), "Integer")
	v.col("WorkTelephoneExtentionNumber", digits("e.custom_work_telephone_extention_number"), "Integer")
	v.col("MobileNumber", digits("e.cell_number"), "Integer")
	v.col("IsSpecialNeeds", "IFNULL(e.custom_is_special_needs, 0)", "Boolean")
	v.col("SpecialNeedCode", v.ministry("sn2", "e.custom_ministry_special_needs_type", "Type of special needs"), "Lookup", "Same as SpecialNeedsTypeCode (the spec lists both).")
	v.col("LastUpdateDate", "e.modified", "Date")
	views.append(v)

	v = employee_child("jameahEmployeeAcademicQualifications", "Employee Academic Qualifications", "Jameah Academic Qualification", "custom_jameah_qualifications")
	v.col("IsLastAcademicDataRecord", "IFNULL(r.is_last_academic_data_record, 0)", "Boolean")
	v.col("ScientificDegreeCode", v.ministry("dg", "r.degree", "Coding of academic degrees"), "Lookup")
	v.col("MajorCode", v.ministry("mj", "r.specialization", "Specialization Coding Guide"), "Lookup")
	v.col("MinorCode", v.ministry("mn", "r.minor", "Specialization Coding Guide"), "Lookup")
	v.col("AssessmentTypeCode", v.ministry("at", "r.assessment_type", "Student Evaluation Coding"), "Lookup",
		"Ministry 'appreciation' list (excellent, very good...). Values saved from the old GPA-system list are not sent.")
	v.col("GPA", "r.gpa", "Number")
	v.col("GPATypeCode", v.ministry("gt", "r.gpa_type", "Cumulative GPA"), "Lookup")
	v.col("StudyTypeCode", v.ministry("st", "r.study_type", "Study type coding"), "Lookup")
	v.col("GraduateFrom", text("r.institute"))
	v.col("Faculty", text("r.faculty"))
	v.col("DateOfScientificDegree", real_date("r.qualification_date"), "Date")
	v.col("GraduationYear", "NULLIF(r.graduation_year, 0)", "Integer")
	v.col("City", text("r.city"))
	v.col("CountryCode", v.ministry("cn", "r.country", "Nationality"), "Lookup")
	views.append(v)

	v = employee_child("jameahEmployeeAcademicExperience", "Employee Academic Experience", "Jameah Work Experience", "custom_jameah_experience")
	v.col("IsLatestWorkExperienceRecord", "IFNULL(r.is_latest_work_experience_record, 0)", "Boolean")
	v.col("CurrentAcademicYeardate", real_date("r.current_academic_year_date"), "Date")
	v.col("EmploymentStatusCode", v.ministry("js", "r.employment_status_code", "Job status"), "Lookup")
	v.col("profession", text("r.designation"), note="Job title.")
	v.col("InstituteCode", v.ministry("ic", "r.institute_code", "Coding of educational insti"), "Lookup")
	v.col("LocationCode", v.ministry("lc", "r.location_code", "Coding cities and governora"), "Lookup")
	v.col("SectionCode", v.ministry("sc", "r.section_code", "Coding academic departments"), "Lookup")
	v.col("EmployeeNumber", f"COALESCE({text('r.employee_number')}, CASE WHEN r.is_latest_work_experience_record = 1 THEN {text('e.employee_number')} END)",
		note="Job number; the current record falls back to the HR job number.")
	v.col("ProfessionRankCode", v.ministry("pr", "r.profession_rank_code", "Job ranks"), "Lookup")
	v.col("HiringDate", real_date("r.hiring_date"), "Date")
	v.col("StartWorkingDate", real_date("r.start_date"), "Date")
	v.col("EndWorkingDate", real_date("r.end_date"), "Date")
	v.col("FunctionalTasks", text("r.job_duties"))
	v.col("AccommodationCode", v.ministry("ac", "r.accommodation_code", "Residential status coding"), "Lookup")
	views.append(v)

	v = employee_child("jameahEmployeePreviousExperience", "Employee Previous Experience", "Jameah Previous Work Experience", "custom_jameah_previous_experience")
	v.col("Profession", text("r.profession"))
	v.col("OrganizationName", text("r.organization_name"))
	v.col("City", text("r.city"))
	v.col("CountryCode", v.ministry("cn", "r.country", "Nationality"), "Lookup")
	v.col("Department", text("r.department"))
	v.col("Section", text("r.section"))
	v.col("StartWorkDate", real_date("r.start_work_date"), "Date")
	v.col("EndWorkDate", real_date("r.end_work_date"), "Date")
	v.col("FunctionalTasks", text("r.functional_tasks"))
	views.append(v)

	v = employee_child("jameahEmployeeProfessionalCertificates", "Employee Professional Certificates & Training Courses", "Jameah Training Course", "custom_jameah_training")
	v.col("CourseName", text("r.course_name"))
	v.col("CourseType", text("r.course_type"))
	v.col("Issuer", text("r.provider"))
	v.col("CourseDate", real_date("r.date"), "Date")
	v.col("CoursePeriod", text("r.duration"), note="Duration in days.")
	v.col("CourseCity", text("r.city"))
	v.col("CourseCountry", v.ministry("cn", "r.country", "Nationality"), "Lookup")
	views.append(v)
	return views


# ---------------------------------------------------------------------------
# Students

STUDENT = "`tabStudent` s LEFT JOIN `tabStudent Ministry Detail` d ON d.student = s.name"


def student_child(view_name, section, doctype, parentfield, row_key):
	v = View(view_name, section,
		f"`tab{doctype}` r JOIN `tabStudent` s ON s.name = r.parent AND r.parenttype = 'Student' AND r.parentfield = {q(parentfield)}",
		key=("StudentId", row_key))
	v.col("StudentId", "s.name", "Key", "Student number (record key).")
	v.col(row_key, "r.name", "Key", "Row ID (record key).")
	return v


def names(v, prefix):
	v.col("ArabicFirstName", text(f"{prefix}.first_name_ar"))
	v.col("ArabicSecondName", text(f"{prefix}.second_name_ar"))
	v.col("ArabicThirdName", text(f"{prefix}.third_name_ar"))
	v.col("ArabicFourthName", text(f"{prefix}.fourth_name_ar"))
	v.col("EnglishFirstName", text(f"{prefix}.first_name"))
	v.col("EnglishSecondName", text(f"{prefix}.second_name"))
	v.col("EnglishThirdName", text(f"{prefix}.third_name"))
	v.col("EnglishFourthName", text(f"{prefix}.fourth_name"))


def study_type(v):
	"""Student Ministry Detail when set; else the configured bridging/regular study type."""
	from_detail = v.official("sty", "d.study_type", "Study type coding")
	v.join("LEFT JOIN (SELECT DISTINCT student FROM `tabStudent Bridging Course`) br ON br.student = s.name")
	bridging = v.setting("stb", "bridging_study_type", "Study type coding")
	regular = v.setting("str", "regular_study_type", "Study type coding")
	return f"COALESCE({from_detail}, CASE WHEN br.student IS NOT NULL THEN {bridging} ELSE {regular} END)"


def student_views():
	views = []

	v = View("jameahStudentPersonalInfo", "1. Personal Information", STUDENT + " LEFT JOIN `tabStudent Applicant` sa ON sa.name = s.applicant", key=("StudentId",))
	v.col("StudentId", "s.name", "Key", "Student number (record key).")
	names(v, "s")
	v.col("Email", text("s.email_id"))
	v.col("MobileNumber", digits("s.mobile_number"), "Integer")
	v.col("IdentityTypeCode", v.mapped("it", "Identity Type (Select)", "s.id_type", "Identity type"), "Lookup")
	v.col("SpecialNeedsTypeCode", v.mapped("sn", "Special Need", "s.special_need_type", "Type of special needs"), "Lookup")
	v.col("IdentityNumber", digits("s.civil_registry"), "Integer")
	v.col("PassportNumber", text("sa.passport_number"))
	v.col("BorderNumber", digits("sa.border_number"), "Integer")
	v.col("HomeIdentityNumber", text("sa.id_number_in_the_country"))
	v.col("BirthPlaceId", v.official("bp", "d.birth_place", "Coding cities and governora"), "Lookup",
		"From Student Ministry Detail; Student.place_of_birth is a country, not a city.")
	v.col("BirthDate", real_date("s.date_of_birth"), "Date", "Placeholder dates before 1920 (e.g. 1900-01-01) are sent as NULL.")
	v.col("Gender", v.mapped("gd", "Gender Edu", "s.gender", "Gender"), "Lookup")
	v.col("NationalityId", f"COALESCE({v.official('ndt', 'd.nationality', 'Nationality')}, {v.mapped('ntx', 'Nationality (text)', 's.nationality', 'Nationality')})", "Lookup")
	v.col("MaritalStatusId", v.mapped("ms", "Marital Status", "s.marital_status", "Social status"), "Lookup")
	v.col("OriginalLanguageId", NULL, "Lookup", "No Ministry code list exists for languages, so nothing is sent.")
	v.col("ReligionId", v.mapped("rl", "Religion", "s.religion", "Religions"), "Lookup")
	v.col("SpecialNeedsId", "IFNULL(s.special_need, 0)", "Boolean")
	v.col("SpecialNeedId", v.mapped("sn2", "Special Need", "s.special_need_type", "Type of special needs"), "Lookup", "Same as SpecialNeedsTypeCode (the spec lists both).")
	v.col("LastUpdateDate", "GREATEST(s.modified, COALESCE(d.modified, s.modified), COALESCE(sa.modified, s.modified))", "Date")
	views.append(v)

	v = student_child("jameahStudentCompanion", "2. Companion / Guardian", "Student Guardian", "guardians", "CompanionId")
	names(v, "r")
	v.col("IdentityNumber", NULL, "Integer", "Guardian identity number is not stored.")
	v.col("IdentityTypeId", v.mapped("it", "Identity Type (Select)", "r.id_type_civil_registration_type", "Identity type"), "Lookup")
	v.col("IdentityExpiryDate", real_date("r.id_expiry_date"), "Date")
	v.col("NationalityId", v.mapped("ntx", "Nationality (text)", "r.nationality", "Nationality"), "Lookup")
	v.col("RelationshipTypeId", NULL, "Lookup", "No Ministry code list exists for relationships, so nothing is sent.")
	v.col("MobileNumber", digits("r.mobile_number"), "Integer")
	views.append(v)

	v = View("jameahStudentForeignAddress", "3. Foreign Address",
		"`tabStudent` s JOIN `tabStudent Non Saudi` ns ON ns.name = s.sponsor_name JOIN `tabAddress Edu` a ON a.name = ns.address",
		key=("StudentId",))
	v.col("StudentId", "s.name", "Key", "Student number (record key).")
	v.col("CountryId", v.mapped("cn", "Country Edu", "a.country", "Nationality"), "Lookup")
	v.col("City", text("a.city"))
	v.col("State", text("a.state"))
	v.col("Neighborhood", text("a.neighbourhood"))
	v.col("Street", text("a.address_line1"))
	v.col("HouseNumber", text("a.building_number"))
	v.col("HousingStatusId", NULL, "Lookup", "The spec has no Ministry list for foreign housing status.")
	v.col("PostalAddress", text("a.postal_address"))
	v.col("ZipCode", digits("a.postal_code"), "Integer")
	v.col("HomeTelephoneNumber", digits("a.phone"), "Integer")
	v.col("MobileNumber", digits("a.mobile"), "Integer")
	views.append(v)

	v = student_child("jameahStudentRelatives", "4. Relatives", "Student Sibling", "siblings", "RelativeId")
	v.join("LEFT JOIN `tabAddress Edu` a ON a.name = r.address")
	names(v, "r")
	v.col("CountryId", v.mapped("cn", "Country Edu", "a.country", "Nationality"), "Lookup")
	v.col("City", text("a.city"))
	v.col("RelationshipId", NULL, "Lookup", "No Ministry code list exists for relationships, so nothing is sent.")
	v.col("TelephoneNumber", digits("a.phone"), "Integer")
	v.col("MobileNumber", digits("a.mobile"), "Integer")
	v.col("PostalAddress", text("a.postal_address"))
	v.col("EmailAddress", text("r.email_address"))
	views.append(v)

	v = View("jameahStudentKSAAddress", "5. Address In the Kingdom / KSA (Local) Address", STUDENT + " LEFT JOIN `tabAddress Edu` a ON a.name = s.address", key=("StudentId",))
	v.col("StudentId", "s.name", "Key", "Student number (record key).")
	v.col("City", v.mapped("ct", "City", "s.current_city", "Coding cities and governora"), "Lookup")
	v.col("HousingStatusId", f"COALESCE({v.official('hsd', 'd.housing_status', 'Residential status coding')}, {v.mapped('hs', 'Address Edu.housing_status', 'a.housing_status', 'Residential status coding')})", "Lookup")
	v.col("PostalAddress", text("a.postal_address"))
	v.col("ZipCode", digits("a.postal_code"), "Integer")
	v.col("HomeTelephoneNumber", digits("a.phone"), "Integer")
	v.col("MobileNumber", digits("a.mobile"), "Integer")
	v.col("StreetName", text("a.address_line1"))
	v.col("AdditionalNumber", digits("a.additional_number"), "Integer")
	v.col("BuildingNumber", digits("a.building_number"), "Integer")
	views.append(v)

	v = student_child("jameahStudentHighSchoolCertificate", "6. High School Certificate", "Student Certificate", "certificates", "CertificateId")
	v.join("LEFT JOIN `tabStudent Ministry Detail` d ON d.student = s.name")
	v.col("CertificateTypeId", v.mapped("ctp", "Certificate Type", "r.type_of_certificate", "Type of secondary school ce"), "Lookup")
	v.col("CertificateYearHijri", "NULLIF(r.hs_year_of_obtaining_the_ceritificate_post_secondary_hijiri, 0)", "Integer")
	v.col("CertificateSourceCityId", v.mapped("cc", "City", "r.city_of_high_school", "Coding cities and governora"), "Lookup")
	v.col("Percentage", "r.high_school_percentage", "Number")
	v.col("CertificateYearGregorian", digits("r.hs_year_of_obtaining_the_ceritificate_post_secondary"), "Integer")
	v.col("IsObtainedInSaudiArabia", yes_no("r.high_school_diploma_obtained_in_kingdom"), "Boolean")
	saudi = v.official("sau", "'101'", "Nationality")
	v.col("CertificateSourceCountryCode",
		f"COALESCE({v.official('csd', 'd.certificate_source_country', 'Nationality')}, "
		f"{v.mapped('cso', 'Country Edu', 'r.high_school_diploma_obtained_in_outside_kigdom', 'Nationality')}, "
		f"CASE WHEN r.high_school_diploma_obtained_in_kingdom = 'Yes' THEN {saudi} END)", "Lookup",
		"Student Ministry Detail, else the outside-the-Kingdom country, else Saudi Arabia (101) when obtained in the Kingdom.")
	views.append(v)

	v = View("jameahStudentContact", "7. Contact", "`tabStudent` s LEFT JOIN `tabSocial Media Account` sm ON sm.name = s.social_media_account", key=("StudentId",))
	v.col("StudentId", "s.name", "Key", "Student number (record key).")
	v.col("EmailAddress", text("s.email_id"))
	v.col("MobileNumber", digits("s.mobile_number"), "Integer")
	v.col("TwitterAccount", text("sm.twitter"))
	v.col("FaceBookAccount", text("sm.facebook"))
	v.col("OtherConnectionAccounts", text("sm.other_account"))
	views.append(v)

	v = View("jameahStudentScholarship", "8. Scholarship", STUDENT, key=("StudentId",))
	v.col("StudentId", "s.name", "Key", "Student number (record key).")
	v.col("StudyScholarshipTypeId", v.official("sch", "d.study_scholarship_type", "Type of grant"), "Lookup")
	v.col("ScholarshipClassificationId", v.official("scc", "d.scholarship_classification", "Scholarship Classificatio"), "Lookup")
	v.col("StudyTypeId", study_type(v), "Lookup", "Student Ministry Detail, else Jameah Settings (bridging or regular study type).")
	v.col("VisaNumber", NULL, "Integer", "Visa data is not stored.")
	v.col("VisitDate", NULL, "Date", "Visa data is not stored.")
	views.append(v)

	v = View("jameahStudentAcademicDetails", "9. Academic Details",
		"`tabProgram Enrollment` pe JOIN `tabStudent` s ON s.name = pe.student AND pe.docstatus = 1 "
		"LEFT JOIN `tabProgram` p ON p.name = pe.program "
		"LEFT JOIN `tabStudent Ministry Detail` d ON d.student = s.name "
		"LEFT JOIN `tabAcademic Year` ay ON ay.name = pe.academic_year "
		"LEFT JOIN `jameah_student_summary` sm ON sm.student = s.name "
		"LEFT JOIN `tabAcademic Term` lt ON lt.name = sm.latest_term",
		key=("StudentId", "EnrollmentId"))
	v.col("StudentId", "s.name", "Key", "Student number (record key).")
	v.col("EnrollmentId", "pe.name", "Key", "Program Enrollment (record key).")
	v.col("StudentIdentityNumber", "s.name", "String", "The student's academic number (digits only), not the login email.")
	v.col("UniversityId", v.setting("uni", "institute", "Coding of educational insti"), "Lookup")
	degree = v.mapped("deg", "Degree", "p.academic_degree", "Coding of academic degrees")
	v.col("TargetScientificDegreeId", degree, "Lookup")
	v.col("GrantedScientificDegreeId",
		f"COALESCE({v.official('gdd', 'd.granted_scientific_degree', 'Coding of academic degrees')}, CASE WHEN s.original_status = 'Graduated' THEN {degree} END)",
		"Lookup", "Student Ministry Detail, else the program degree for graduated students.")
	college = v.setting("col", "college", "College Coding Guide")
	v.col("AdmissionCollegeId", college, "Lookup")
	v.col("CurrentCollegeId", college, "Lookup")
	v.col("UniversityDepartmentId",
		f"COALESCE({v.official('udd', 'd.university_department', 'Coding academic departments')}, {v.mapped('udp', 'Program', 'pe.program', 'Coding academic departments')})", "Lookup")
	major = v.mapped("maj", "Major", "p.academic_program_major", "Specialization Coding Guide")
	v.col("UniversityMajorId", major, "Lookup")
	v.col("SaudiMajorCode", f"COALESCE({v.official('smd', 'd.saudi_major_code', 'Specialization Coding Guide')}, {major})", "Lookup")
	v.col("SaudiEducationLevelCode", v.mapped("edl", "Education Level", "p.academic_education_level", "Educational level - 33"), "Lookup")
	v.col("UniversityMinorId", v.official("umn", "d.university_minor", "Specialization Coding Guide"), "Lookup")
	v.col("StudyProgramPeriod", "NULLIF(CAST(cfg.program_period AS UNSIGNED), 0)", "Integer")
	v.col("StudyProgramPeriodUnitId", v.setting("ppu", "program_period_unit", "Program duration coding"), "Lookup")
	# Credit hours and GPA come from jameah_student_summary (see summary.py), refreshed hourly.
	v.col("RequestedCreditHoursCount", "ROUND(NULLIF(sm.required, 0))", "Integer", "Credit hours on the student's plan (as the transcript shows them).")
	v.col("RegisteredCreditHoursCount", "(CASE WHEN sm.has_plan = 1 THEN ROUND(sm.registered) END)", "Integer", "Plan courses registered and not yet graded.")
	passed = "(IFNULL(sm.earned, 0) + IFNULL(sm.transferred, 0))"
	v.col("PassedCreditHoursCount", f"(CASE WHEN sm.has_plan = 1 OR sm.transferred IS NOT NULL THEN ROUND({passed}) END)", "Integer",
		"Earned hours plus transferred (bridging) hours.")
	v.col("RemainingCreditHoursCount",
		f"(CASE WHEN s.original_status = 'Graduated' THEN 0 WHEN NULLIF(sm.required, 0) IS NULL THEN NULL ELSE ROUND(GREATEST(sm.required - {passed}, 0)) END)",
		"Integer", "0 for graduates.")
	v.col("AcademicStatusId",
		f"COALESCE({v.official('asd', 'd.academic_status', 'General situation')}, {v.mapped('ast', 'Student Status', 's.original_status', 'General situation')})", "Lookup")
	v.col("StudyTypeId", study_type(v), "Lookup", "Student Ministry Detail, else Jameah Settings (bridging or regular study type).")
	v.col("ScholarshipTypeCode", v.official("stc", "d.scholarship_type_code", "Type of grant"), "Lookup")
	# "Current" academic year = the year of the latest term the student registered courses in.
	v.join("LEFT JOIN `tabAcademic Year` cy ON cy.name = COALESCE(lt.academic_year, pe.academic_year)")
	v.col("CurrentAcademicYeardate", real_date("cy.year_start_date"), "Date", "Start of the latest academic year the student registered courses in.")
	v.col("ScientificDegreeCode", degree, "Lookup", "Same as TargetScientificDegreeId (the spec lists both).")
	v.col("StudentRewardAmount", NULL, "Number", "Rewards are not tracked.")
	v.col("IsLastAcademicDataRecord", "(CASE WHEN pe.name = sm.latest_enrollment THEN 1 ELSE 0 END)", "Boolean")
	v.col("RegistrationStatusId", v.mapped("rgs", "Student.current_year_status", "s.current_year_status", "Registration status"), "Lookup",
		"The spec table spells it RegisrationStatusId; its own code-mapping table and the Ministry use RegistrationStatusId.")
	v.col("CurrentAcademicYearId", "cy.name", "Lookup", "Academic year name, e.g. 2025-2026 (no Ministry list).")
	v.col("AdmissionHijriYear", hijri_year("ay.year_start_date"), "Integer", "Hijri (Umm al-Qura) year in which the admission academic year starts.")
	v.col("CurrentYear", NULL, "Integer", "Not defined clearly enough in the spec to compute.")
	v.col("AdmissionGregorianYear", f"YEAR({real_date('ay.year_start_date')})", "Integer", "Gregorian year in which the admission academic year starts.")
	# Graduation term from the graduate document (one per graduate).
	v.join("""LEFT JOIN (
		SELECT student, SUBSTRING_INDEX(GROUP_CONCAT(academic_term ORDER BY creation DESC SEPARATOR '\\n'), '\\n', 1) AS academic_term
		FROM `tabGraduate Document` WHERE IFNULL(academic_term, '') != '' GROUP BY student
	) gd ON gd.student = s.name AND s.original_status = 'Graduated'
	LEFT JOIN `tabAcademic Term` gt ON gt.name = gd.academic_term""")
	graduation_date = f"COALESCE({real_date('s.date_of_leaving')}, {real_date('gt.term_end_date')})"
	v.col("GraduationYear", f"(CASE WHEN s.original_status = 'Graduated' THEN YEAR({graduation_date}) END)", "Integer",
		"Year of the leaving date, else of the end of the graduation term (Graduate Document).")
	v.col("GraduationSemesterTypeId",
		f"COALESCE({v.official('gsd', 'd.graduation_semester_type', 'Admission to study')}, {v.mapped('gst', 'Academic Term.term_name', 'gt.term_name', 'Admission to study')})",
		"Lookup", "Student Ministry Detail, else the semester of the graduation term (Graduate Document).")
	v.col("SpecialityClassificationCode", v.official("spc", "d.speciality_classification", "Type of specialization"), "Lookup")
	v.col("AttendanceSemesterTypeId", v.official("atd", "d.attendance_semester_type", "Admission to study"), "Lookup")
	v.col("CurrentSemesterTypeId", v.mapped("cst", "Academic Term.term_name", "lt.term_name", "Admission to study"), "Lookup", "Semester of the latest course registration.")
	v.col("GPATypeId", v.setting("gpt", "gpa_type", "Cumulative GPA"), "Lookup")
	v.col("GPA", "sm.gpa", "Number", "Cumulative GPA as on the transcript (exact, rounded half up); NULL when no graded credit hours.")
	v.col("CurrentSemesterAssesmentId", v.official("csa", "d.current_semester_assessment", "Student Evaluation Coding"), "Lookup")
	v.col("WarningCount", NULL, "Number", "Academic warnings are not tracked.")
	v.col("AccumulatedAssesmentId", v.official("aca", "d.accumulated_assessment", "Student Evaluation Coding"), "Lookup")
	v.col("IsRewardReceivedForCurrentSemester", NULL, "Boolean", "Rewards are not tracked.")
	v.col("StudyLocationCityId",
		f"COALESCE({v.official('slc', 'd.study_location_city', 'Coding cities and governora')}, {v.setting('slg', 'study_location_city', 'Coding cities and governora')})",
		"Lookup", "Student Ministry Detail, else the campus city in Jameah Settings.")
	v.col("CountryId", v.setting("cty", "study_country", "Nationality"), "Lookup")
	v.col("GraduationDate", f"(CASE WHEN s.original_status = 'Graduated' THEN {graduation_date} END)", "Date",
		"Leaving date, else the end date of the graduation term (Graduate Document).")
	v.col("SummerSemesterRegistrationStatus", v.official("ssr", "d.summer_semester_registration_status", "Summer registration status"), "Lookup")
	v.col("IsTransferred", v.official("trs", "d.transfer_status", "Student transfer status"), "Lookup")
	v.col("IsAccommodationInUniversity", "IFNULL(pe.boarding_student, 0)", "Boolean")
	v.col("IsMajorEducational", f"(CASE {v.official('mty', 'd.major_type', 'Type of specialization')} WHEN '1' THEN 1 WHEN '2' THEN 0 END)", "Boolean")
	v.col("MajorTypeId", NULL, "Lookup", "No source field.")
	v.col("AcceptanceDate", real_date("pe.enrollment_date"), "Date")
	v.col("DisclaimerDate", NULL, "Date", "Clearance is not tracked.")
	v.col("DisclaimerDecisionOrBarginNumber", NULL, "String", "Clearance is not tracked.")
	v.col("DateOfLastUpdateOnAcademicStatus", "GREATEST(pe.modified, s.modified)", "Date")
	grant = v.official("hsg", "d.study_scholarship_type", "Type of grant")
	v.col("HasScholarship", f"(CASE WHEN {grant} IN ('11', '12', '21', '22') THEN 1 WHEN {grant} IN ('31', '98') THEN 0 END)", "Boolean",
		"From the grant type: government/private grant = 1, own expense / not applicable = 0, unknown = NULL.")
	v.col("ScholarshipClassificationCode", v.official("scl", "d.scholarship_classification_code", "Scholarship Classificatio"), "Lookup")
	v.col("AdmissionDate", real_date("pe.enrollment_date"), "Date")
	v.col("HasThesis", f"(CASE WHEN {degree} IN ('1', '2', '7', '15', '22', '23') THEN 0 END)", "Boolean",
		"0 for diploma and bachelor programs (no thesis); unknown for postgraduate.")
	v.col("ThesisTitle", NULL, "String", "Theses are not tracked.")
	v.join("CROSS JOIN jameah_cfg cfg")
	views.append(v)

	v = View("jameahStudentAttachments", "10. Attachments", "", key=("StudentId", "AttachmentTitle"))
	v.columns = [
		("StudentId", "x.student", "Key", "Student number (record key)."),
		("AttachmentTypeCode", NULL, "Lookup", "The Ministry has not published an attachment type list."),
		("AttachmentURL", "CONCAT(IFNULL(cfg.file_base_url, ''), x.url)", "String", "File Base URL from Jameah Settings + file path."),
		("AttachmentTitle", "x.title", "String", "Document name."),
	]
	unions = " UNION ALL ".join(
		f"SELECT r.parent AS student, {q(label)} AS title, r.`{field}` AS url FROM `tabStudent Document` r "
		f"WHERE r.parenttype = 'Student' AND r.parentfield = 'documents' AND IFNULL(r.`{field}`, '') != ''"
		for field, label in STUDENT_DOCUMENT_FIELDS)
	v.source = f"({unions}) x JOIN `tabStudent` s ON s.name = x.student CROSS JOIN jameah_cfg cfg"
	views.append(v)
	return views


STUDENT_DOCUMENT_FIELDS = [
	("id_photo", "ID Photo"), ("aptitude_test", "Aptitude Test"), ("saat_result", "Achievement Test Result"),
	("tofel", "TOEFL"), ("other_certificate", "Other Certificate"), ("intern_letter", "Internship Letter"),
	("cpr", "CPR Certificate"), ("letter_employer", "Employer Letter"), ("certificate_qualification", "Qualification Certificate"),
	("cetrificate_authority", "Saudi Authority License Certificate"), ("photo_of_student", "Photo of the Student"),
	("passport_photo", "Passport"), ("payment_slip", "Payment Slip"),
]


def all_views():
	# Student views read the Education app's tables.
	return employee_views() + (student_views() if frappe.db.table_exists("Student") else [])


def grant_statements(user="jameah_reader", host="%"):
	"""SQL for a read-only account the Ministry (Jameah) agent can use.

	The views run with their definer's rights, so the account needs SELECT on
	the views only - it cannot read any ERP table directly. Run as the MariaDB
	administrator and replace the password.
	"""
	db = frappe.conf.db_name
	lines = [f"CREATE USER IF NOT EXISTS '{user}'@'{host}' IDENTIFIED BY '<choose a strong password>';"]
	lines += [f"GRANT SELECT ON `{db}`.`{v.name}` TO '{user}'@'{host}';" for v in all_views()]
	return "\n".join(lines)


def mapping_markdown():
	"""Column-by-column documentation of every view, generated from the definitions above."""
	out = ["# Ministry (Jameah) views: column mapping", "",
		"Generated by `medical_hrms.jameah.views.mapping_markdown()` from the view definitions. Do not edit by hand.", ""]
	for v in all_views():
		out += [f"## `{v.name}`", "", f"Spec section: **{v.section}**. One row per: {', '.join(v.key)}.", "",
			"| Column | Type | Source (SQL) | Ministry list | Note |", "|---|---|---|---|---|"]
		for name, sql, spec_type, note in v.columns:
			src = " ".join(sql.split()).replace("|", "\\|")
			if len(src) > 160:
				src = src[:157] + "..."
			out.append(f"| `{name}` | {spec_type} | `{src}` | {v.categories.get(name, '')} | {note} |")
		out.append("")
	return "\n".join(out)


def create_views():
	frappe.db.sql_ddl(f"CREATE OR REPLACE SQL SECURITY DEFINER VIEW `{CFG_VIEW}` AS {cfg_view_sql()}")
	created = []
	for v in all_views():
		frappe.db.sql_ddl(f"CREATE OR REPLACE SQL SECURITY DEFINER VIEW `{v.name}` AS {v.sql()}")
		created.append(v.name)
	return created


def drop_views():
	for v in all_views():
		frappe.db.sql_ddl(f"DROP VIEW IF EXISTS `{v.name}`")
	frappe.db.sql_ddl(f"DROP VIEW IF EXISTS `{CFG_VIEW}`")
