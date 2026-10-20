"""What the Ministry would receive right now: gaps, codes to review, settings, data problems.

Fast SQL over the views (seconds), for the Jameah Data Check page. The full
value-by-value comparison is verify.run (run from the console / tests).
"""
import json
import os

import frappe

from medical_hrms.jameah import views as V

ROLES = ("HR Manager", "HR User", "Education Manager", "System Manager")
SPEC = json.load(open(os.path.join(os.path.dirname(__file__), "spec_columns.json")))

# Mandatory only for graduates (Ministry: "mandatory when the academic status is graduate").
GRADUATE_ONLY = {"GrantedScientificDegreeId", "GraduationYear", "GraduationSemesterTypeId", "GraduationDate"}
# Settings each view needs; empty ones are listed as actions.
SETTINGS = [
	("institute", "Educational Institution (UniversityId)"),
	("college", "College (AdmissionCollegeId / CurrentCollegeId)"),
	("study_country", "Country of Study"),
	("study_location_city", "Study Location City"),
	("regular_study_type", "Study Type for Regular Students"),
	("bridging_study_type", "Study Type for Bridging Students"),
	("gpa_type", "GPA Type"),
	("program_period", "Program Duration"),
	("program_period_unit", "Program Duration Unit"),
	("employee_company", "Company Reported as Employees"),
]


def _count(sql, params=None):
	return frappe.db.sql(sql, params or {})[0][0]


def view_status(view):
	columns = {c[0] for c in view.columns}
	spec = SPEC.get(view.section, [])
	rows = _count(f"SELECT COUNT(*) FROM `{view.name}`")
	missing = []
	graduated = view.name == "jameahStudentAcademicDetails"
	for s in spec:
		col = "RegistrationStatusId" if s["column"] == "RegisrationStatusId" else s["column"]
		if not s["mandatory"] or col not in columns:
			continue
		where = f"`{col}` IS NULL"
		if graduated and col in GRADUATE_ONLY:
			where += " AND `AcademicStatusId` = '6'"
		n = _count(f"SELECT COUNT(*) FROM `{view.name}` WHERE {where}")
		if n:
			note = next((c[3] for c in view.columns if c[0] == col), "")
			missing.append({"column": col, "english": s["english"], "missing": n, "note": note,
				"scope": "graduates" if graduated and col in GRADUATE_ONLY else "all rows"})
	invalid = 0
	for col, category in view.categories.items():
		invalid += _count(
			f"SELECT COUNT(*) FROM `{view.name}` v LEFT JOIN `tabJameah Ministry Code` c "
			f"ON c.code_category = %(cat)s AND c.ministry_code = v.`{col}` WHERE v.`{col}` IS NOT NULL AND c.name IS NULL", {"cat": category})
	return {"view": view.name, "section": view.section, "rows": rows, "mandatory_missing": missing, "invalid_codes": invalid}


def data_problems():
	"""Source-data issues the views cannot fix (they are reported, never altered)."""
	q = _count
	return [p for p in [
		("Students whose birth date is a placeholder (before 1920)", q("SELECT COUNT(*) FROM tabStudent WHERE date_of_birth < '1920-01-01'")),
		("Program Enrollments with no real enrollment date", q("SELECT COUNT(*) FROM `tabProgram Enrollment` WHERE docstatus = 1 AND (enrollment_date IS NULL OR enrollment_date < '1920-01-01')")),
		("Graduated students without a Graduate Document (no graduation term)",
			q("SELECT COUNT(*) FROM tabStudent s WHERE s.original_status = 'Graduated' AND NOT EXISTS (SELECT 1 FROM `tabGraduate Document` g WHERE g.student = s.name)")),
		("Graduated students still marked 'Enrolled' for the current year",
			q("SELECT COUNT(*) FROM tabStudent WHERE original_status = 'Graduated' AND current_year_status LIKE 'مسجل%%'")),
		("Students on a study plan with no total credits (Requested/Remaining hours unknown)",
			q("SELECT COUNT(DISTINCT pe.student) FROM `tabProgram Enrollment` pe JOIN `tabStudy Plan` sp ON sp.name = pe.study_plan WHERE pe.docstatus = 1 AND IFNULL(sp.total_credits, 0) = 0")),
		("Guardian / relative / certificate rows whose student no longer exists",
			q("SELECT (SELECT COUNT(*) FROM `tabStudent Guardian` g LEFT JOIN tabStudent s ON s.name = g.parent WHERE g.parenttype = 'Student' AND s.name IS NULL)"
				" + (SELECT COUNT(*) FROM `tabStudent Sibling` g LEFT JOIN tabStudent s ON s.name = g.parent WHERE g.parenttype = 'Student' AND s.name IS NULL)"
				" + (SELECT COUNT(*) FROM `tabStudent Certificate` g LEFT JOIN tabStudent s ON s.name = g.parent WHERE g.parenttype = 'Student' AND s.name IS NULL)")),
		("Program Enrollments whose student no longer exists",
			q("SELECT COUNT(*) FROM `tabProgram Enrollment` pe LEFT JOIN tabStudent s ON s.name = pe.student WHERE pe.docstatus = 1 AND s.name IS NULL")),
		("Relative addresses recorded outside Saudi Arabia (check: likely a data-migration default)",
			q("SELECT COUNT(*) FROM `tabStudent Sibling` sb JOIN `tabAddress Edu` a ON a.name = sb.address WHERE a.country NOT IN ('Saudi Arabia', '')")),
		("Employees with Ministry codes from the wrong list (sent as empty)",
			q("SELECT COUNT(*) FROM tabEmployee e LEFT JOIN `tabJameah Ministry Code` c ON c.name = e.custom_jameah_nationality AND c.code_category = 'Nationality' WHERE IFNULL(e.custom_jameah_nationality, '') != '' AND c.name IS NULL")),
		("Employee qualifications with 'Appreciation' from the old GPA-system list (sent as empty)",
			q("SELECT COUNT(*) FROM `tabJameah Academic Qualification` WHERE parenttype = 'Employee' AND assessment_type LIKE 'Cumulative GPA::%%'")),
	] if p[1]]


@frappe.whitelist()
def get_status():
	frappe.only_for(ROLES)
	settings = frappe.get_single("Jameah Settings")
	views = [view_status(v) for v in V.all_views()]
	review = frappe.get_all("Jameah Code Map", filters={"status": "Needs Review", "usage_count": [">", 0]},
		fields=["name", "source_doctype", "source_value", "code_category", "usage_count", "suggestion"], order_by="usage_count desc")
	return {
		"views": views,
		"needs_review": review,
		"settings_missing": [label for field, label in SETTINGS if not settings.get(field)],
		"data_problems": [{"problem": p, "count": n} for p, n in data_problems()],
		"summary_refreshed_on": settings.academic_summary_refreshed_on,
		"teaching_staff_excluded": _count("SELECT COUNT(*) FROM tabEmployee e WHERE EXISTS (SELECT 1 FROM tabInstructor i WHERE i.employee = e.name)"),
	}


@frappe.whitelist()
def employee_view_rows(employee):
	"""Rows the Employee views send for one employee (HR's preview on the Employee form)."""
	frappe.only_for(("HR Manager", "HR User", "System Manager"))
	frappe.has_permission("Employee", "read", employee, throw=True)
	out = {"views": {}, "excluded_reason": None}
	for view in V.employee_views():
		out["views"][view.name] = frappe.db.sql(f"SELECT * FROM `{view.name}` WHERE EmployeeId = %s", employee, as_dict=True)
	if not out["views"]["jameahEmployeePersonalInfo"]:
		company = frappe.db.get_single_value("Jameah Settings", "employee_company")
		e = frappe.db.get_value("Employee", employee, ["company", "user_id", "company_email"], as_dict=True)
		teaching = frappe.db.sql(
			"SELECT name FROM tabInstructor WHERE employee = %(e)s OR (%(u)s != '' AND email = %(u)s) OR (%(c)s != '' AND email = %(c)s) LIMIT 1",
			{"e": employee, "u": e.user_id or "", "c": e.company_email or ""})
		if teaching:
			out["excluded_reason"] = f"Not sent as an Employee: linked to Instructor {teaching[0][0]}, so the Ministry receives this person as Faculty."
		elif company and e.company != company:
			out["excluded_reason"] = f"Not sent: the Ministry views report employees of {company} only (Jameah Settings)."
	return out
