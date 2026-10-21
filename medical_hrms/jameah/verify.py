"""Independent check of the Ministry views against the source tables.

For every view this rebuilds the expected rows in Python from the Frappe
records (not from the view SQL) and compares them value by value. It also
checks that every Lookup column holds a code from the official Ministry list,
counts missing mandatory values, and applies the Ministry's format rules.

	bench --site <site> execute medical_hrms.jameah.verify.run
"""
import bisect
import datetime
import decimal
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict

import frappe
from frappe.utils import getdate

from medical_hrms.jameah import summary
from medical_hrms.jameah import views as V

SPEC = os.path.join(os.path.dirname(__file__), "spec_columns.json")


# ---------------------------------------------------------------- helpers

def key(value):
	# MariaDB compares these columns case-insensitively and ignores trailing spaces.
	return (value or "").rstrip().casefold()


class Codes:
	def __init__(self):
		self.official = {r.name: r for r in frappe.get_all("Jameah Ministry Code", fields=["name", "code_category", "ministry_code"])}
		self.by_category = defaultdict(set)
		for r in self.official.values():
			self.by_category[r.code_category].add(r.ministry_code)
		self.map = {
			(r.source_doctype, key(r.source_value), r.code_category): r.jameah_code
			for r in frappe.get_all("Jameah Code Map", filters={"status": "Verified"}, fields=["source_doctype", "source_value", "code_category", "jameah_code"])
		}
		self.cfg = frappe.get_single("Jameah Settings")

	def ministry(self, link, category):
		r = self.official.get(link) if link else None
		return r.ministry_code if r and r.code_category == category else None

	def official_code(self, code, category):
		return self.ministry(f"{category}::{code}", category) if code else None

	def mapped(self, source, value, category):
		return self.ministry(self.map.get((source, key(value), category)), category) if value else None

	def setting(self, field, category):
		return self.ministry(self.cfg.get(field), category)


def text(value):
	if value is None:
		return None
	value = str(value).strip(" ")
	# MariaDB treats a string of only diacritics/format marks as equal to '' (so NULLIF gives NULL).
	if all(unicodedata.category(ch) in ("Mn", "Me", "Cf") for ch in value):
		return None
	return value


def digits(value):
	return re.sub(r"[^0-9]", "", str(value or "")) or None


def real_date(value):
	return value if value and str(value) >= "1920-01-01" else None


def coalesce(*values):
	return next((v for v in values if v is not None), None)


# Students whose exact GPA differs from the Education transcript by more than
# rounding (filled by expected_student_academic). GPA_TIES: exact x.xx5 values
# the transcript rounds down because it adds up in floating point.
GPA_DISAGREEMENTS, GPA_TIES, EXACT_GPA = [], [], {}


def same(a, b):
	if a is None or b is None:
		return a is None and b is None
	if isinstance(a, (int, float, decimal.Decimal)) and isinstance(b, (int, float, decimal.Decimal)):
		return abs(float(a) - float(b)) < 0.005
	if isinstance(a, (datetime.date, datetime.datetime)) or isinstance(b, (datetime.date, datetime.datetime)):
		return str(a) == str(b)
	return str(a) == str(b)


HIJRI_STARTS = [datetime.date.fromisoformat(d) for _y, d in V.HIJRI_NEW_YEARS]
HIJRI_YEARS = [y for y, _d in V.HIJRI_NEW_YEARS]


def hijri_year(date):
	if not date:
		return None
	i = bisect.bisect_right(HIJRI_STARTS, date) - 1
	return HIJRI_YEARS[i] if i >= 0 else None


def rows(doctype, fields, filters=None):
	return frappe.get_all(doctype, fields=fields, filters=filters or {}, limit_page_length=0)


# ---------------------------------------------------------------- employees

def employee_population(c):
	instructors = rows("Instructor", ["employee", "email"])
	linked = {i.employee for i in instructors if i.employee}
	emails = {key(i.email) for i in instructors if i.email}
	company = c.cfg.employee_company
	out = {}
	for e in rows("Employee", ["*"]):
		if company and e.company != company:
			continue
		if e.name in linked or (e.user_id and key(e.user_id) in emails) or (e.company_email and key(e.company_email) in emails):
			continue
		out[e.name] = e
	return out


def expected_employee_personal(c, emps):
	out = {}
	for e in emps.values():
		g = c.ministry(e.gender, "Gender")
		out[(e.name,)] = {
			"EmployeeId": e.name,
			"ArabicFirstName": text(e.custom_first_name_ar), "ArabicSecondName": text(e.custom_second_name_ar),
			"ArabicThirdName": text(e.custom_third_name_ar), "ArabicFourthName": text(e.custom_last_name_ar),
			"EnglishFirstName": coalesce(text(e.custom_first_name_en), text(e.first_name)),
			"EnglishSecondName": coalesce(text(e.custom_second_name_en), text(e.middle_name)),
			"EnglishThirdName": text(e.custom_third_name_en),
			"EnglishFourthName": coalesce(text(e.custom_last_name_en), text(e.last_name)),
			"IdentityTypeCode": c.ministry(e.custom_identity_type, "Identity type"),
			"SpecialNeedsTypeCode": c.ministry(e.custom_ministry_special_needs_type, "Type of special needs") if e.custom_is_special_needs else None,
			"IdentityNumber": digits(e.custom_identity_number),
			"BirthPlace": c.ministry(e.custom_ministry_place_of_birth, "Coding cities and governora"),
			"GregorianBirthDate": real_date(e.date_of_birth),
			"PassportNumber": text(e.passport_number),
			"OriginalHomeIDNumber": text(e.custom_original_home_id_number),
			"IsMaleGender": {"1": 1, "2": 0}.get(g),
			"NationalityCode": c.ministry(e.custom_jameah_nationality, "Nationality"),
			"MaritalStatusCode": c.mapped("Employee.marital_status", e.marital_status, "Social status"),
			"ReligionCode": c.ministry(e.custom_ministry_religion, "Religions"),
			"PostalAddress": text(e.current_address),
			"CityCode": c.ministry(e.custom_ministry_work_city, "Coding cities and governora"),
			"ZipCode": digits(e.custom_zip_code),
			"Email": coalesce(text(e.prefered_email), text(e.company_email), text(e.personal_email)),
			"HomeTelephoneNumber": digits(e.custom_home_telephone_number),
			"WorkTelephoneNumber": digits(e.custom_work_telephone_number),
			"WorkTelephoneExtentionNumber": digits(e.custom_work_telephone_extention_number),
			"MobileNumber": digits(e.cell_number),
			"IsSpecialNeeds": e.custom_is_special_needs or 0,
			"SpecialNeedCode": c.ministry(e.custom_ministry_special_needs_type, "Type of special needs") if e.custom_is_special_needs else None,
			"LastUpdateDate": e.modified,
		}
	return out


def employee_children(doctype, parentfield, emps):
	return [r for r in rows(doctype, ["*"], {"parenttype": "Employee", "parentfield": parentfield}) if r.parent in emps]


def expected_employee_qualifications(c, emps):
	out = {}
	for r in employee_children("Jameah Academic Qualification", "custom_jameah_qualifications", emps):
		out[(r.parent, r.name)] = {
			"EmployeeId": r.parent, "RecordId": r.name,
			"IsLastAcademicDataRecord": r.is_last_academic_data_record or 0,
			"ScientificDegreeCode": c.ministry(r.degree, "Coding of academic degrees"),
			"MajorCode": c.ministry(r.specialization, "Specialization Coding Guide"),
			"MinorCode": c.ministry(r.minor, "Specialization Coding Guide"),
			"AssessmentTypeCode": c.ministry(r.assessment_type, "Student Evaluation Coding"),
			"GPA": r.gpa,
			"GPATypeCode": c.ministry(r.gpa_type, "Cumulative GPA"),
			"StudyTypeCode": c.ministry(r.study_type, "Study type coding"),
			"GraduateFrom": text(r.institute), "Faculty": text(r.faculty),
			"DateOfScientificDegree": real_date(r.qualification_date),
			"GraduationYear": r.graduation_year or None,
			"City": text(r.city), "CountryCode": c.ministry(r.country, "Nationality"),
		}
	return out


def expected_employee_experience(c, emps):
	out = {}
	for r in employee_children("Jameah Work Experience", "custom_jameah_experience", emps):
		e = emps[r.parent]
		out[(r.parent, r.name)] = {
			"EmployeeId": r.parent, "RecordId": r.name,
			"IsLatestWorkExperienceRecord": r.is_latest_work_experience_record or 0,
			"CurrentAcademicYeardate": real_date(r.current_academic_year_date),
			"EmploymentStatusCode": c.ministry(r.employment_status_code, "Job status"),
			"profession": text(r.designation),
			"InstituteCode": c.ministry(r.institute_code, "Coding of educational insti"),
			"LocationCode": c.ministry(r.location_code, "Coding cities and governora"),
			"SectionCode": c.ministry(r.section_code, "Coding academic departments"),
			"EmployeeNumber": coalesce(text(r.employee_number), text(e.employee_number) if r.is_latest_work_experience_record == 1 else None),
			"ProfessionRankCode": c.ministry(r.profession_rank_code, "Job ranks"),
			"HiringDate": real_date(r.hiring_date), "StartWorkingDate": real_date(r.start_date), "EndWorkingDate": real_date(r.end_date),
			"FunctionalTasks": text(r.job_duties),
			"AccommodationCode": c.ministry(r.accommodation_code, "Residential status coding"),
		}
	return out


def expected_employee_previous(c, emps):
	out = {}
	for r in employee_children("Jameah Previous Work Experience", "custom_jameah_previous_experience", emps):
		out[(r.parent, r.name)] = {
			"EmployeeId": r.parent, "RecordId": r.name,
			"Profession": text(r.profession), "OrganizationName": text(r.organization_name), "City": text(r.city),
			"CountryCode": c.ministry(r.country, "Nationality"), "Department": text(r.department), "Section": text(r.section),
			"StartWorkDate": real_date(r.start_work_date), "EndWorkDate": real_date(r.end_work_date), "FunctionalTasks": text(r.functional_tasks),
		}
	return out


def expected_employee_training(c, emps):
	out = {}
	for r in employee_children("Jameah Training Course", "custom_jameah_training", emps):
		out[(r.parent, r.name)] = {
			"EmployeeId": r.parent, "RecordId": r.name,
			"CourseName": text(r.course_name), "CourseType": text(r.course_type), "Issuer": text(r.provider),
			"CourseDate": real_date(r.date), "CoursePeriod": text(r.duration), "CourseCity": text(r.city),
			"CourseCountry": c.ministry(r.country, "Nationality"),
		}
	return out


# ---------------------------------------------------------------- students

def names(r):
	return {
		"ArabicFirstName": text(r.first_name_ar), "ArabicSecondName": text(r.second_name_ar),
		"ArabicThirdName": text(r.third_name_ar), "ArabicFourthName": text(r.fourth_name_ar),
		"EnglishFirstName": text(r.first_name), "EnglishSecondName": text(r.second_name),
		"EnglishThirdName": text(r.third_name), "EnglishFourthName": text(r.fourth_name),
	}


class StudentData:
	def __init__(self):
		self.students = {s.name: s for s in rows("Student", ["*"])}
		self.detail = {d.student: d for d in rows("Student Ministry Detail", ["*"])}
		self.applicants = {a.name: a for a in rows("Student Applicant", ["name", "passport_number", "border_number", "id_number_in_the_country", "modified"])}
		self.addresses = {a.name: a for a in rows("Address Edu", ["*"])}
		self.bridging = {b.student for b in rows("Student Bridging Course", ["student"])}


def study_type(c, sd, s):
	d = sd.detail.get(s.name) or frappe._dict()
	fallback = c.setting("bridging_study_type", "Study type coding") if s.name in sd.bridging else c.setting("regular_study_type", "Study type coding")
	return coalesce(c.official_code(d.study_type, "Study type coding"), fallback)


def expected_student_personal(c, sd):
	out = {}
	for s in sd.students.values():
		d = sd.detail.get(s.name) or frappe._dict()
		a = sd.applicants.get(s.applicant) or frappe._dict()
		out[(s.name,)] = {
			"StudentId": s.name, **names(s),
			"Email": text(s.email_id), "MobileNumber": digits(s.mobile_number),
			"IdentityTypeCode": c.mapped("Identity Type (Select)", s.id_type, "Identity type"),
			"SpecialNeedsTypeCode": c.mapped("Special Need", s.special_need_type, "Type of special needs") if s.special_need else None,
			"IdentityNumber": digits(s.civil_registry),
			"PassportNumber": text(a.passport_number), "BorderNumber": digits(a.border_number),
			"HomeIdentityNumber": text(a.id_number_in_the_country),
			"BirthPlaceId": c.official_code(d.birth_place, "Coding cities and governora"),
			"BirthDate": real_date(s.date_of_birth),
			"Gender": c.mapped("Gender Edu", s.gender, "Gender"),
			"NationalityId": coalesce(c.official_code(d.nationality, "Nationality"), c.mapped("Nationality (text)", s.nationality, "Nationality")),
			"MaritalStatusId": c.mapped("Marital Status", s.marital_status, "Social status"),
			"OriginalLanguageId": None,
			"ReligionId": c.mapped("Religion", s.religion, "Religions"),
			"SpecialNeedsId": s.special_need or 0,
			"SpecialNeedId": c.mapped("Special Need", s.special_need_type, "Type of special needs") if s.special_need else None,
			"LastUpdateDate": max(x for x in (s.modified, d.get("modified"), a.get("modified")) if x),
		}
	return out


def student_children(doctype, parentfield, sd):
	return [r for r in rows(doctype, ["*"], {"parenttype": "Student", "parentfield": parentfield}) if r.parent in sd.students]


def expected_student_companion(c, sd):
	out = {}
	for r in student_children("Student Guardian", "guardians", sd):
		out[(r.parent, r.name)] = {
			"StudentId": r.parent, "CompanionId": r.name, **names(r),
			"IdentityNumber": None,
			"IdentityTypeId": c.mapped("Identity Type (Select)", r.id_type_civil_registration_type, "Identity type"),
			"IdentityExpiryDate": real_date(r.id_expiry_date),
			"NationalityId": c.mapped("Nationality (text)", r.nationality, "Nationality"),
			"RelationshipTypeId": None, "MobileNumber": digits(r.mobile_number),
		}
	return out


def expected_student_foreign_address(c, sd):
	sponsors = {n.name: n for n in rows("Student Non Saudi", ["name", "address"])}
	out = {}
	for s in sd.students.values():
		ns = sponsors.get(s.sponsor_name)
		a = sd.addresses.get(ns.address) if ns and ns.address else None
		if not a:
			continue
		out[(s.name,)] = {
			"StudentId": s.name, "CountryId": c.mapped("Country Edu", a.country, "Nationality"),
			"City": text(a.city), "State": text(a.state), "Neighborhood": text(a.neighbourhood), "Street": text(a.address_line1),
			"HouseNumber": text(a.building_number), "HousingStatusId": None, "PostalAddress": text(a.postal_address),
			"ZipCode": digits(a.postal_code), "HomeTelephoneNumber": digits(a.phone), "MobileNumber": digits(a.mobile),
		}
	return out


def expected_student_relatives(c, sd):
	out = {}
	for r in student_children("Student Sibling", "siblings", sd):
		a = sd.addresses.get(r.address) or frappe._dict()
		out[(r.parent, r.name)] = {
			"StudentId": r.parent, "RelativeId": r.name, **names(r),
			"CountryId": c.mapped("Country Edu", a.country, "Nationality"), "City": text(a.city), "RelationshipId": None,
			"TelephoneNumber": digits(a.phone), "MobileNumber": digits(a.mobile), "PostalAddress": text(a.postal_address),
			"EmailAddress": text(r.email_address),
		}
	return out


def expected_student_ksa_address(c, sd):
	out = {}
	for s in sd.students.values():
		d = sd.detail.get(s.name) or frappe._dict()
		a = sd.addresses.get(s.address) or frappe._dict()
		out[(s.name,)] = {
			"StudentId": s.name, "City": c.mapped("City", s.current_city, "Coding cities and governora"),
			"HousingStatusId": coalesce(c.official_code(d.housing_status, "Residential status coding"),
				c.mapped("Address Edu.housing_status", a.housing_status, "Residential status coding")),
			"PostalAddress": text(a.postal_address), "ZipCode": digits(a.postal_code), "HomeTelephoneNumber": digits(a.phone),
			"MobileNumber": digits(a.mobile), "StreetName": text(a.address_line1), "AdditionalNumber": digits(a.additional_number),
			"BuildingNumber": digits(a.building_number),
		}
	return out


def expected_student_certificate(c, sd):
	out = {}
	for r in student_children("Student Certificate", "certificates", sd):
		d = sd.detail.get(r.parent) or frappe._dict()
		in_ksa = r.high_school_diploma_obtained_in_kingdom
		out[(r.parent, r.name)] = {
			"StudentId": r.parent, "CertificateId": r.name,
			"CertificateTypeId": c.mapped("Certificate Type", r.type_of_certificate, "Type of secondary school ce"),
			"CertificateYearHijri": r.hs_year_of_obtaining_the_ceritificate_post_secondary_hijiri or None,
			"CertificateSourceCityId": c.mapped("City", r.city_of_high_school, "Coding cities and governora"),
			"Percentage": r.high_school_percentage,
			"CertificateYearGregorian": digits(r.hs_year_of_obtaining_the_ceritificate_post_secondary),
			"IsObtainedInSaudiArabia": {"Yes": 1, "No": 0}.get(in_ksa),
			"CertificateSourceCountryCode": coalesce(
				c.official_code(d.certificate_source_country, "Nationality"),
				c.mapped("Country Edu", r.high_school_diploma_obtained_in_outside_kigdom, "Nationality"),
				c.official_code("101", "Nationality") if in_ksa == "Yes" else None),
		}
	return out


def expected_student_contact(c, sd):
	social = {m.name: m for m in rows("Social Media Account", ["*"])}
	out = {}
	for s in sd.students.values():
		m = social.get(s.social_media_account) or frappe._dict()
		out[(s.name,)] = {
			"StudentId": s.name, "EmailAddress": text(s.email_id), "MobileNumber": digits(s.mobile_number),
			"TwitterAccount": text(m.twitter), "FaceBookAccount": text(m.facebook), "OtherConnectionAccounts": text(m.other_account),
		}
	return out


def expected_student_scholarship(c, sd):
	out = {}
	for s in sd.students.values():
		d = sd.detail.get(s.name) or frappe._dict()
		out[(s.name,)] = {
			"StudentId": s.name,
			"StudyScholarshipTypeId": c.official_code(d.study_scholarship_type, "Type of grant"),
			"ScholarshipClassificationId": c.official_code(d.scholarship_classification, "Scholarship Classificatio"),
			"StudyTypeId": study_type(c, sd, s), "VisaNumber": None, "VisitDate": None,
		}
	return out


def student_credits():
	"""Per student, following education.helper.get_transcript_summary."""
	latest = {}
	for g in frappe.db.sql("SELECT student_id, course, final_result FROM `tabGrade Assessment Results` ORDER BY creation ASC", as_dict=True):
		latest[(g.student_id, g.course)] = g.final_result or None
	plans = {p.name: p.student for p in rows("Student Plan", ["name", "student"])}
	out = defaultdict(lambda: {"required": 0.0, "earned": 0.0, "registered": 0.0})
	for l in rows("Student Plan List", ["parent", "course", "credit", "status"], {"parenttype": "Student Plan", "parentfield": "student_plan_list"}):
		student = plans.get(l.parent)
		if not student:
			continue
		result = latest.get((student, l.course))
		credit = float(l.credit or 0)
		row = out[student]
		row["required"] += credit
		if result == "Pass" or (result is None and l.status == "Passed"):
			row["earned"] += credit
		if result is None and l.status == "Registered":
			row["registered"] += credit
	transferred = defaultdict(float)
	for b in rows("Student Bridging Course", ["student", "calc_hours"]):
		transferred[b.student] += float(b.calc_hours or 0)
	return out, transferred


def latest_terms():
	terms = {t.name: t for t in rows("Academic Term", ["name", "academic_year", "term_name", "term_start_date"])}
	best = {}
	for e in frappe.db.sql("SELECT student, academic_term FROM `tabStudent Course Enrollment` WHERE docstatus < 2", as_dict=True):
		t = terms.get(e.academic_term)
		if not t:
			continue
		rank = (getdate(t.term_start_date) if real_date(t.term_start_date) else datetime.date.min, t.name)
		if e.student not in best or rank > best[e.student][0]:
			best[e.student] = (rank, t)
	return {s: t for s, (_r, t) in best.items()}


def exact_gpa():
	"""Transcript GPA rebuilt with exact decimals, rounded half up (independent of the view SQL)."""
	from decimal import ROUND_HALF_UP, Decimal
	plan = {}
	for pe in frappe.db.sql("SELECT student, study_plan FROM `tabProgram Enrollment` WHERE IFNULL(study_plan, '') != '' ORDER BY creation ASC", as_dict=True):
		plan[pe.student] = pe.study_plan
	plan_ccds = defaultdict(list)
	for r in rows("Academic Level Course", ["parent", "level_course"], {"parentfield": "course_level"}):
		if r.level_course:
			plan_ccds[r.parent].append(r.level_course)
	ccd_course = {r.name: r.course for r in rows("Course Curriculum Definition", ["name", "course"])}
	credits = defaultdict(Decimal)
	for r in rows("Course Class Type", ["parent", "class_type", "credit_hours", "contact_hours"], {"parenttype": "Course Curriculum Definition"}):
		if r.class_type:
			credits[r.parent] += Decimal(str(r.credit_hours or 0)) or Decimal(str(r.contact_hours or 0))
	grades = defaultdict(list)
	for g in rows("Grade Assessment Results", ["student_id", "course", "points"]):
		grades[(g.student_id, g.course)].append(Decimal(str(g.points or 0)))
	bridging = defaultdict(set)
	for b in rows("Student Bridging Course", ["student", "equivalent_course"]):
		bridging[b.student].add(b.equivalent_course)
	out = {}
	for student, sp in plan.items():
		weighted = total = Decimal(0)
		for ccd in plan_ccds.get(sp, []):
			course = ccd_course.get(ccd)
			if not course or course in bridging[student]:
				continue
			for points in grades.get((student, course), ()):
				weighted += points * credits[ccd]
				total += credits[ccd]
		if total:
			EXACT_GPA[student] = weighted / total
			out[student] = (weighted / total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
	return out


def education_gpa(student_ids):
	"""The Education app's old transcript GPA (read only), for Education versions
	without utils/gpa.py."""
	from education.education.page.course_registration_monitoring.course_registration_monitoring import _bulk_cumulative_gpa
	return _bulk_cumulative_gpa(student_ids)


def expected_student_academic(c, sd):
	enrollments = rows("Program Enrollment", ["*"], {"docstatus": 1})
	programs = {p.name: p for p in rows("Program", ["name", "academic_degree", "academic_education_level", "academic_program_major"])}
	years = {y.name: y for y in rows("Academic Year", ["name", "year_start_date"])}
	official_hours = summary.official_credit_hours(list(sd.students))
	if official_hours is not None:
		# The view must carry Education's official credit hours exactly (utils/credit_hours.py).
		credits = {sid: h for sid, h in official_hours.items() if h}
		transferred = {sid: h["transferred"] for sid, h in credits.items()}
	else:
		credits, transferred = student_credits()
	terms = latest_terms()
	all_terms = {t.name: t for t in rows("Academic Term", ["name", "term_name", "term_end_date"])}
	graduation_term = {}
	for gdoc in rows("Graduate Document", ["student", "academic_term", "creation"]):
		if gdoc.academic_term and (gdoc.student not in graduation_term or gdoc.creation > graduation_term[gdoc.student][0]):
			graduation_term[gdoc.student] = (gdoc.creation, all_terms.get(gdoc.academic_term))
	GPA_DISAGREEMENTS.clear()
	GPA_TIES.clear()
	official = summary.official_gpas(list(sd.students))
	if official is not None:
		# The view must carry the college's official GPA exactly (Education's utils/gpa.py).
		gpa = {sid: decimal.Decimal(str(v)).quantize(decimal.Decimal("0.01")) for sid, v in official.items() if v is not None}
		transcript = {}
	else:
		gpa = exact_gpa()
		transcript = education_gpa(list(sd.students))
	for sid, value in (gpa.items() if transcript else ()):
		diff = abs(float(value) - float(transcript.get(sid) or 0))
		if diff < 0.0001:
			continue
		row = {"student": sid, "exact": str(EXACT_GPA[sid]), "view": str(value), "transcript": transcript.get(sid)}
		tie = (EXACT_GPA[sid] * 1000) % 10 == 5 and (EXACT_GPA[sid] * 1000) == (EXACT_GPA[sid] * 1000).to_integral_value()
		(GPA_TIES if tie and diff < 0.0101 else GPA_DISAGREEMENTS).append(row)
	for sid, value in transcript.items():
		if value and sid not in gpa:
			GPA_DISAGREEMENTS.append({"student": sid, "exact": None, "view": None, "transcript": value})
	latest_pe = {}
	for pe in sorted(enrollments, key=lambda x: (getdate(x.enrollment_date) if real_date(x.enrollment_date) else datetime.date.min, x.creation)):
		latest_pe[pe.student] = pe.name
	out = {}
	for pe in enrollments:
		s = sd.students.get(pe.student)
		if not s:
			continue
		d = sd.detail.get(s.name) or frappe._dict()
		p = programs.get(pe.program) or frappe._dict()
		degree = c.mapped("Degree", p.academic_degree, "Coding of academic degrees")
		major = c.mapped("Major", p.academic_program_major, "Specialization Coding Guide")
		cr = credits.get(s.name)
		tr = transferred.get(s.name)
		passed = round((cr["earned"] if cr else 0) + (tr or 0)) if (cr or s.name in transferred) else None
		required = cr["required"] if cr and cr["required"] else None
		if s.original_status == "Graduated":
			remaining = 0
		elif required is None:
			remaining = None
		else:
			remaining = round(max(required - ((cr["earned"] if cr else 0) + (tr or 0)), 0))
		t = terms.get(s.name)
		cy = years.get(t.academic_year if t else pe.academic_year)
		ay = years.get(pe.academic_year)
		grant = c.official_code(d.study_scholarship_type, "Type of grant")
		gterm = graduation_term.get(s.name, (None, None))[1] if s.original_status == "Graduated" else None
		graduated_on = coalesce(real_date(s.date_of_leaving), real_date(gterm.term_end_date) if gterm else None) if s.original_status == "Graduated" else None
		g = gpa.get(s.name)
		out[(s.name, pe.name)] = {
			"StudentId": s.name, "EnrollmentId": pe.name, "StudentIdentityNumber": s.name,
			"UniversityId": c.setting("institute", "Coding of educational insti"),
			"TargetScientificDegreeId": degree,
			"GrantedScientificDegreeId": coalesce(c.official_code(d.granted_scientific_degree, "Coding of academic degrees"), degree if s.original_status == "Graduated" else None),
			"AdmissionCollegeId": c.setting("college", "College Coding Guide"),
			"CurrentCollegeId": c.setting("college", "College Coding Guide"),
			"UniversityDepartmentId": coalesce(c.official_code(d.university_department, "Coding academic departments"), c.mapped("Program", pe.program, "Coding academic departments")),
			"UniversityMajorId": major,
			"SaudiMajorCode": coalesce(c.official_code(d.saudi_major_code, "Specialization Coding Guide"), major),
			"SaudiEducationLevelCode": c.mapped("Education Level", p.academic_education_level, "Educational level - 33"),
			"UniversityMinorId": c.official_code(d.university_minor, "Specialization Coding Guide"),
			"StudyProgramPeriod": c.cfg.program_period or None,
			"StudyProgramPeriodUnitId": c.setting("program_period_unit", "Program duration coding"),
			"RequestedCreditHoursCount": round(required) if required else None,
			"RegisteredCreditHoursCount": round(cr["registered"]) if cr else None,
			"PassedCreditHoursCount": passed,
			"RemainingCreditHoursCount": remaining,
			"AcademicStatusId": coalesce(c.official_code(d.academic_status, "General situation"), c.mapped("Student Status", s.original_status, "General situation")),
			"StudyTypeId": study_type(c, sd, s),
			"ScholarshipTypeCode": c.official_code(d.scholarship_type_code, "Type of grant"),
			"CurrentAcademicYeardate": real_date(cy.year_start_date) if cy else None,
			"ScientificDegreeCode": degree, "StudentRewardAmount": None,
			"IsLastAcademicDataRecord": 1 if latest_pe.get(s.name) == pe.name else 0,
			"RegistrationStatusId": c.mapped("Student.current_year_status", s.current_year_status, "Registration status"),
			"CurrentAcademicYearId": cy.name if cy else None,
			"AdmissionHijriYear": hijri_year(getdate(ay.year_start_date)) if ay and real_date(ay.year_start_date) else None,
			"CurrentYear": None,
			"AdmissionGregorianYear": getdate(ay.year_start_date).year if ay and real_date(ay.year_start_date) else None,
			"GraduationYear": getdate(graduated_on).year if graduated_on else None,
			"GraduationSemesterTypeId": coalesce(c.official_code(d.graduation_semester_type, "Admission to study"),
				c.mapped("Academic Term.term_name", gterm.term_name, "Admission to study") if gterm else None),
			"SpecialityClassificationCode": c.official_code(d.speciality_classification, "Type of specialization"),
			"AttendanceSemesterTypeId": c.official_code(d.attendance_semester_type, "Admission to study"),
			"CurrentSemesterTypeId": c.mapped("Academic Term.term_name", t.term_name, "Admission to study") if t else None,
			"GPATypeId": c.setting("gpa_type", "Cumulative GPA"),
			"GPA": g,
			"CurrentSemesterAssesmentId": c.official_code(d.current_semester_assessment, "Student Evaluation Coding"),
			"WarningCount": None,
			"AccumulatedAssesmentId": c.official_code(d.accumulated_assessment, "Student Evaluation Coding"),
			"IsRewardReceivedForCurrentSemester": None,
			"StudyLocationCityId": coalesce(c.official_code(d.study_location_city, "Coding cities and governora"), c.setting("study_location_city", "Coding cities and governora")),
			"CountryId": c.setting("study_country", "Nationality"),
			"GraduationDate": graduated_on,
			"SummerSemesterRegistrationStatus": c.official_code(d.summer_semester_registration_status, "Summer registration status"),
			"IsTransferred": c.official_code(d.transfer_status, "Student transfer status"),
			"IsAccommodationInUniversity": pe.boarding_student or 0,
			"IsMajorEducational": {"1": 1, "2": 0}.get(c.official_code(d.major_type, "Type of specialization")),
			"MajorTypeId": None, "AcceptanceDate": real_date(pe.enrollment_date),
			"DisclaimerDate": None, "DisclaimerDecisionOrBarginNumber": None,
			"DateOfLastUpdateOnAcademicStatus": max(pe.modified, s.modified),
			"HasScholarship": 1 if grant in ("11", "12", "21", "22") else 0 if grant in ("31", "98") else None,
			"ScholarshipClassificationCode": c.official_code(d.scholarship_classification_code, "Scholarship Classificatio"),
			"AdmissionDate": real_date(pe.enrollment_date),
			"HasThesis": 0 if degree in ("1", "2", "7", "15", "22", "23") else None,
			"ThesisTitle": None,
		}
	return out


def expected_student_attachments(c, sd):
	base = c.cfg.file_base_url or ""
	out = {}
	for r in student_children("Student Document", "documents", sd):
		for field, label in V.STUDENT_DOCUMENT_FIELDS:
			if r.get(field):
				out[(r.parent, label, r.name)] = {"StudentId": r.parent, "AttachmentTypeCode": None, "AttachmentURL": base + r.get(field), "AttachmentTitle": label}
	return out


EXPECTED = {
	"jameahEmployeePersonalInfo": expected_employee_personal,
	"jameahEmployeeAcademicQualifications": expected_employee_qualifications,
	"jameahEmployeeAcademicExperience": expected_employee_experience,
	"jameahEmployeePreviousExperience": expected_employee_previous,
	"jameahEmployeeProfessionalCertificates": expected_employee_training,
	"jameahStudentPersonalInfo": expected_student_personal,
	"jameahStudentCompanion": expected_student_companion,
	"jameahStudentForeignAddress": expected_student_foreign_address,
	"jameahStudentRelatives": expected_student_relatives,
	"jameahStudentKSAAddress": expected_student_ksa_address,
	"jameahStudentHighSchoolCertificate": expected_student_certificate,
	"jameahStudentContact": expected_student_contact,
	"jameahStudentScholarship": expected_student_scholarship,
	"jameahStudentAcademicDetails": expected_student_academic,
	"jameahStudentAttachments": expected_student_attachments,
}


# ---------------------------------------------------------------- Ministry rules

ARABIC = re.compile(r"^[؀-ۿ\s'’-]+$")
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# The Ministry: names must not contain these words (they belong in other name parts).
FORBIDDEN_NAME_WORDS = {"بنت", "ولد", "بن", "آل"}


def rule_problems(view, row):
	problems = []
	for col, value in row.items():
		if value is None:
			continue
		if col.startswith("Arabic") and col.endswith("Name"):
			if not ARABIC.match(str(value)):
				problems.append(f"{col} has non-Arabic letters")
			elif FORBIDDEN_NAME_WORDS & set(str(value).split()):
				problems.append(f"{col} contains a word the Ministry does not allow (بن/بنت/ولد/آل)")
		if col == "IdentityNumber" and not re.fullmatch(r"\d{9,10}", str(value)):
			problems.append("IdentityNumber is not 9-10 digits")
		if col == "StudentIdentityNumber" and not re.fullmatch(r"\d{4,12}", str(value)):
			problems.append("StudentIdentityNumber is not 4-12 digits")
		if col in ("Email", "EmailAddress") and not EMAIL.match(str(value)):
			problems.append(f"{col} is not a valid e-mail")
		if col in ("BirthDate", "GregorianBirthDate") and str(value) > str(datetime.date.today()):
			problems.append(f"{col} is in the future")
	return problems


# ---------------------------------------------------------------- run

def view_rows(view):
	return frappe.db.sql(f"SELECT * FROM `{view.name}`", as_dict=True)


def row_key(view, row):
	if view.name == "jameahStudentAttachments":
		return None
	return tuple(row[k] for k in view.key)


def compare(view, actual, expected, sample=5):
	result = {"view": view.name, "rows": len(actual), "expected_rows": len(expected), "missing": [], "extra": [], "mismatches": Counter(), "examples": []}
	if view.name == "jameahStudentAttachments":
		# No unique key per row: compare as multisets.
		norm = lambda r: (r["StudentId"], r["AttachmentTitle"], r["AttachmentURL"], r["AttachmentTypeCode"])
		a, e = Counter(norm(r) for r in actual), Counter(norm(r) for r in expected.values())
		result["missing"] = [list(x) for x in (e - a)][:sample]
		result["extra"] = [list(x) for x in (a - e)][:sample]
		result["missing_count"], result["extra_count"] = sum((e - a).values()), sum((a - e).values())
		return result
	by_key = {row_key(view, r): r for r in actual}
	result["duplicate_keys"] = len(actual) - len(by_key)
	missing = [k for k in expected if k not in by_key]
	extra = [k for k in by_key if k not in expected]
	result["missing_count"], result["extra_count"] = len(missing), len(extra)
	result["missing"], result["extra"] = [list(k) for k in missing[:sample]], [list(k) for k in extra[:sample]]
	for k, exp in expected.items():
		act = by_key.get(k)
		if not act:
			continue
		for col, value in exp.items():
			if not same(act.get(col), value):
				result["mismatches"][col] += 1
				if len(result["examples"]) < sample * 4:
					result["examples"].append({"key": list(k), "column": col, "view": str(act.get(col)), "expected": str(value)})
	return result


def run(views=None, verbose=True):
	c = Codes()
	emps = employee_population(c)
	sd = StudentData()
	spec = json.load(open(SPEC))
	report = []
	for view in V.all_views():
		if views and view.name not in views:
			continue
		actual = view_rows(view)
		build = EXPECTED[view.name]
		expected = build(c, emps) if view.name.startswith("jameahEmployee") else build(c, sd)
		r = compare(view, actual, expected)
		# Contract: the spec's columns, in order, plus our record keys.
		columns = [col for col, *_ in view.columns]
		spec_cols = spec.get(view.section, [])
		keys = [col for col, _sql, t, _n in view.columns if t == "Key"]
		r["columns_missing_from_view"] = [x for x in spec_cols if x["column"] not in columns]
		r["columns_not_in_spec"] = [x for x in columns if x not in {s["column"] for s in spec_cols} and x not in keys]
		# Every Lookup value must be an official code of its category.
		bad_codes = Counter()
		for row in actual:
			for col, category in view.categories.items():
				value = row.get(col)
				if value is not None and value not in c.by_category[category]:
					bad_codes[col] += 1
		r["invalid_codes"] = dict(bad_codes)
		mandatory = [s["column"] for s in spec_cols if s["mandatory"]]
		r["mandatory_missing"] = {col: sum(1 for row in actual if row.get(col) is None) for col in mandatory if col in columns}
		r["mandatory_missing"] = {k: v for k, v in r["mandatory_missing"].items() if v}
		rules = Counter()
		for row in actual:
			for p in rule_problems(view.name, row):
				rules[p] += 1
		r["rule_problems"] = dict(rules)
		r["mismatches"] = dict(r["mismatches"])
		if view.name == "jameahStudentAcademicDetails":
			r["gpa_vs_transcript"] = list(GPA_DISAGREEMENTS)
			r["gpa_transcript_ties"] = list(GPA_TIES)
		r["ok"] = not (r["missing_count"] or r["extra_count"] or r["mismatches"] or r["invalid_codes"] or r.get("duplicate_keys") or r.get("gpa_vs_transcript"))
		report.append(r)
		if verbose:
			print(f"{'OK  ' if r['ok'] else 'FAIL'} {view.name:<42} rows={r['rows']:<6} expected={r['expected_rows']:<6} "
				f"missing={r['missing_count']} extra={r['extra_count']} mismatched={sum(r['mismatches'].values())} invalid_codes={sum(bad_codes.values())}")
	return report
