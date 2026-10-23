"""Ministry (Jameah) views: end-to-end tests. Each test rolls back its data.

	bench --site <site> run-tests --module medical_hrms.jameah.test_jameah
"""
import unittest

import frappe

from medical_hrms.jameah import code_map, verify, views

C = lambda category, code: f"{category}::{code}"
EMPLOYEE_VIEWS = [v.name for v in views.employee_views()]


def make_employee(**values):
	doc = dict(
		doctype="Employee", naming_series="HR-EMP-", first_name="Test", status="Active", company="Al Riyada College",
		department="Human Resources", branch="Main Riyadh Campus Branch", date_of_birth="1985-03-14", date_of_joining="2022-09-01",
		gender=C("Gender", "1"), custom_jameah_nationality=C("Nationality", "101"), custom_identity_type=C("Identity type", "01"),
		custom_ministry_work_city=C("Coding cities and governora", "0202000"), custom_ministry_job_rank=C("Job ranks", "01"),
	)
	doc.update(values)
	return frappe.get_doc(doc).insert(ignore_permissions=True)


def view_rows(name, **filters):
	where = " AND ".join(f"`{k}` = %({k})s" for k in filters) or "1=1"
	return frappe.db.sql(f"SELECT * FROM `{name}` WHERE {where}", filters, as_dict=True)


@unittest.skipUnless(frappe.db and frappe.db.exists("Company", "Al Riyada College"), "needs the RCHS company")
class TestJameahEmployeeViews(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("Jameah Settings", "employee_company", "Al Riyada College")
		self.employee = make_employee(
			custom_first_name_ar="خالد", custom_second_name_ar="سعد", custom_third_name_ar="عبدالله", custom_last_name_ar="الزهراني",
			custom_first_name_en="Khalid", custom_second_name_en="Saad", custom_third_name_en="Abdullah", custom_last_name_en="Alzahrani",
			custom_identity_number="1099123456", marital_status="Married", custom_ministry_religion=C("Religions", "1"),
			personal_email="khalid.qa@rchs-qa.test", cell_number="+966-500-111-222", custom_work_telephone_number="012-600-2222",
			custom_jameah_qualifications=[dict(
				is_last_academic_data_record=1, degree=C("Coding of academic degrees", "4"), specialization=C("Specialization Coding Guide", "KL01"),
				assessment_type=C("Student Evaluation Coding", "3"), gpa=4.6, gpa_type=C("Cumulative GPA", "1"), study_type=C("Study type coding", "0"),
				institute="King Abdulaziz University", faculty="College of Nursing", qualification_date="2014-06-15", graduation_year=2014,
				city="Jeddah", country=C("Nationality", "101"))],
			custom_jameah_experience=[dict(
				is_latest_work_experience_record=1, current_academic_year_date="2025-09-01", employment_status_code=C("Job status", "11"),
				institute_code=C("Coding of educational insti", "P18"), location_code=C("Coding cities and governora", "0202000"),
				section_code=C("Coding academic departments", "KL03"), profession_rank_code=C("Job ranks", "01"))],
		)

	def tearDown(self):
		frappe.db.rollback()

	def test_codes_not_record_names(self):
		row = view_rows("jameahEmployeePersonalInfo", EmployeeId=self.employee.name)[0]
		self.assertEqual(row.NationalityCode, "101")
		self.assertEqual(row.IdentityTypeCode, "01")
		self.assertEqual(row.IsMaleGender, 1)
		self.assertEqual(row.MaritalStatusCode, "1")
		self.assertEqual(row.ReligionCode, "1")
		self.assertEqual(row.MobileNumber, "966500111222")
		self.assertEqual(row.WorkTelephoneNumber, "0126002222")
		self.assertEqual(row.ArabicFourthName, "الزهراني")
		q = view_rows("jameahEmployeeAcademicQualifications", EmployeeId=self.employee.name)[0]
		self.assertEqual((q.ScientificDegreeCode, q.MajorCode, q.AssessmentTypeCode, q.CountryCode), ("4", "KL01", "3", "101"))
		x = view_rows("jameahEmployeeAcademicExperience", EmployeeId=self.employee.name)[0]
		self.assertEqual((x.InstituteCode, x.EmploymentStatusCode, x.SectionCode), ("P18", "11", "KL03"))

	def test_wrong_category_or_unknown_code_is_sent_empty(self):
		frappe.db.set_value("Employee", self.employee.name, {"custom_jameah_nationality": C("Gender", "1"), "custom_ministry_religion": "Religions::NOPE"})
		row = view_rows("jameahEmployeePersonalInfo", EmployeeId=self.employee.name)[0]
		self.assertIsNone(row.NationalityCode)
		self.assertIsNone(row.ReligionCode)
		old = self.employee.custom_jameah_qualifications[0].name
		frappe.db.set_value("Jameah Academic Qualification", old, "assessment_type", C("Cumulative GPA", "1"))
		self.assertIsNone(view_rows("jameahEmployeeAcademicQualifications", RecordId=old)[0].AssessmentTypeCode)

	def test_teaching_staff_other_company_and_instructor_rows_excluded(self):
		faculty = make_employee(first_name="Faculty", custom_identity_number="1099123457",
			custom_jameah_training=[dict(course_name="Not reported", country=C("Nationality", "101"))])
		instructor = frappe.db.get_value("Instructor", {"employee": ["is", "not set"]}, "name")
		frappe.db.set_value("Instructor", instructor, "employee", faculty.name)
		other = make_employee(first_name="Other", company="Medical College", department="Internal Medicine - MC", custom_identity_number="1099123458")
		instructor_rows = set(frappe.get_all("Jameah Training Course", filters={"parenttype": "Instructor"}, pluck="name"))
		for name in EMPLOYEE_VIEWS:
			rows = view_rows(name)
			ids = {r.EmployeeId for r in rows}
			self.assertNotIn(faculty.name, ids, name)
			self.assertNotIn(other.name, ids, name)
			self.assertFalse({r.get("RecordId") for r in rows} & instructor_rows, name)
		self.assertTrue(view_rows("jameahEmployeePersonalInfo", EmployeeId=self.employee.name))

	def test_views_match_source_records(self):
		for result in verify.run(views=EMPLOYEE_VIEWS, verbose=False):
			self.assertTrue(result["ok"], (result["view"], result["mismatches"], result["examples"][:3], result["missing"], result["extra"]))
			self.assertFalse(result["invalid_codes"], result["view"])


FACULTY_VIEWS = [v.name for v in views.faculty_views()]


def bare_instructor(status="Active"):
	"""An Instructor with no Employee and no Jameah rows of its own."""
	return frappe.db.sql("""SELECT i.name FROM tabInstructor i WHERE i.status = %s AND IFNULL(i.employee, '') = ''
		AND NOT EXISTS (SELECT 1 FROM `tabJameah Academic Qualification` q WHERE q.parenttype = 'Instructor' AND q.parent = i.name)
		AND NOT EXISTS (SELECT 1 FROM `tabJameah Work Experience` x WHERE x.parenttype = 'Instructor' AND x.parent = i.name)
		AND NOT EXISTS (SELECT 1 FROM tabEmployee e WHERE e.user_id = i.email OR e.company_email = i.email)
		ORDER BY i.name LIMIT 1""", status)[0][0]


@unittest.skipUnless(frappe.db and frappe.db.exists("Company", "Al Riyada College") and frappe.db.table_exists("Instructor"), "needs the RCHS company and Instructors")
class TestJameahFacultyViews(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("Jameah Settings", "employee_company", "Al Riyada College")
		self.employee = make_employee(
			first_name="Faculty", custom_first_name_ar="سارة", custom_last_name_ar="الحربي", custom_identity_number="1099123460",
			custom_jameah_qualifications=[dict(
				is_last_academic_data_record=1, degree=C("Coding of academic degrees", "4"), specialization=C("Specialization Coding Guide", "KL01"),
				assessment_type=C("Student Evaluation Coding", "3"), gpa=4.6, gpa_type=C("Cumulative GPA", "1"), study_type=C("Study type coding", "0"),
				institute="King Abdulaziz University", faculty="College of Nursing", qualification_date="2014-06-15", graduation_year=2014,
				city="Jeddah", country=C("Nationality", "101"))],
			custom_jameah_experience=[dict(
				is_latest_work_experience_record=1, current_academic_year_date="2025-09-01", employment_status_code=C("Job status", "11"),
				institute_code=C("Coding of educational insti", "P18"), location_code=C("Coding cities and governora", "0202000"),
				section_code=C("Coding academic departments", "KL03"), profession_rank_code=C("Job ranks", "01"))],
		)
		self.instructor = bare_instructor()
		frappe.db.set_value("Instructor", self.instructor, {"employee": self.employee.name, "custom_identity_number": "", "custom_jameah_nationality": None,
			"custom_first_name_ar": "", "custom_last_name_ar": "", "instructor_faculty_ranking": "Lecturer"})

	def tearDown(self):
		frappe.db.rollback()

	def test_sent_once_as_faculty_with_employee_data(self):
		self.assertFalse(view_rows("jameahEmployeePersonalInfo", EmployeeId=self.employee.name))
		row = view_rows("jameahFacultyPersonalInfo", FacultyId=self.instructor)[0]
		self.assertEqual((row.IdentityNumber, row.NationalityCode, row.ArabicFirstName, row.ArabicFourthName), ("1099123460", "101", "سارة", "الحربي"))
		self.assertEqual(str(row.BirthDate), "1985-03-14")

	def test_employee_rows_when_instructor_has_none(self):
		q = view_rows("jameahFacultyAcademicQualification", FacultyId=self.instructor)
		self.assertEqual([r.RecordId for r in q], [self.employee.custom_jameah_qualifications[0].name])
		self.assertEqual((q[0].ScientificDegreeCode, q[0].RatingCode), ("4", "3"))
		x = view_rows("jameahFacultyAcademicExperience", FacultyId=self.instructor)
		self.assertEqual(len(x), 1)
		# A Job rank is not an Academic rank: the Instructor's faculty ranking (Lecturer = 14) is sent instead.
		self.assertEqual((x[0].InstituteCode, x[0].AcademicRankCode), ("P18", "14"))

	def test_current_position_built_from_instructor(self):
		other = bare_instructor()  # the setUp instructor now has an Employee, so this is another one
		frappe.db.set_value("Instructor", other, {"instructor_faculty_ranking": "Assistant Professor", "instructor_start_date": "2019-09-01"})
		x = view_rows("jameahFacultyAcademicExperience", FacultyId=other)
		self.assertEqual(len(x), 1)
		self.assertEqual((x[0].RecordId, x[0].IsLatestWorkExperienceRecord, x[0].AcademicRankCode, str(x[0].StartWorkingDate)), (other, 1, "13", "2019-09-01"))

	def test_former_faculty_not_sent(self):
		left = frappe.db.get_value("Instructor", {"status": "Left"}, "name")
		if not left:
			self.skipTest("no Left instructor")
		for name in FACULTY_VIEWS:
			self.assertFalse(view_rows(name, FacultyId=left), name)

	def test_views_match_source_records(self):
		for result in verify.run(views=FACULTY_VIEWS, verbose=False):
			self.assertTrue(result["ok"], (result["view"], result["mismatches"], result["examples"][:3], result["missing"], result["extra"]))
			self.assertFalse(result["invalid_codes"], result["view"])


class TestJameahCodeMap(unittest.TestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_meaning_must_agree_before_a_code_is_trusted(self):
		candidates = [frappe._dict(ministry_code="1", name_english="married", name_arabic="متزوج"),
			frappe._dict(ministry_code="2", name_english="bachelor", name_arabic="أعزب")]
		self.assertEqual(code_map.match(candidates, "2", ["Single", "أعزب"]), ("2", "Code and name"))
		# Right code number, wrong meaning: not trusted.
		code, _suggestion = code_map.match(candidates, "1", ["Single"])
		self.assertIsNone(code)

	def test_ambiguous_city_is_not_guessed(self):
		cities = [frappe._dict(ministry_code="0202000", name_english="Jeddah", name_arabic="جدة"),
			frappe._dict(ministry_code="0701005", name_english="Jeddah", name_arabic="جدة")]
		self.assertIsNone(code_map.match(cities, "90", ["Jeddah"])[0])

	def test_code_must_belong_to_the_rows_category(self):
		row = frappe.get_doc({"doctype": "Jameah Code Map", "source_doctype": "Test", "source_value": "X", "code_category": "Religions",
			"jameah_code": C("Gender", "1"), "status": "Verified"})
		self.assertRaises(frappe.ValidationError, row.insert)

	def test_settings_reject_code_from_wrong_list(self):
		settings = frappe.get_single("Jameah Settings")
		settings.college = C("Gender", "1")
		self.assertRaises(frappe.ValidationError, settings.save)


class TestJameahSummaryRefresh(unittest.TestCase):
	def test_second_refresh_is_skipped_while_one_runs(self):
		from frappe.database import get_db

		from medical_hrms.jameah import summary

		lock = f"{frappe.conf.db_name}:{summary.TABLE}"[:64]
		if not frappe.db.sql("SELECT IS_FREE_LOCK(%s)", lock)[0][0]:
			self.skipTest("a real summary refresh is running (it holds the lock)")
		# Another connection (as the hourly job would be) holds the rebuild lock.
		other = get_db(host=frappe.conf.db_host, user=frappe.conf.db_user or frappe.conf.db_name, password=frappe.conf.db_password,
			port=frappe.conf.db_port, cur_db_name=frappe.conf.db_name, socket=frappe.conf.db_socket)
		try:
			self.assertEqual(other.sql("SELECT GET_LOCK(%s, 0)", lock)[0][0], 1)
			before = frappe.db.get_single_value("Jameah Settings", "academic_summary_refreshed_on")
			self.assertIsNone(summary.refresh())
			self.assertEqual(frappe.db.get_single_value("Jameah Settings", "academic_summary_refreshed_on"), before)
		finally:
			other.sql("SELECT RELEASE_LOCK(%s)", lock)
			other.close()
