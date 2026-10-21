"""Per-student academic aggregates for jameahStudentAcademicDetails.

Credit hours and GPA (Education's official calculations, see
official_credit_hours and official_gpas), latest enrollment and latest
registered term come from Education tables with no index on the student
(90,000+ grade rows), so computing them inside the view takes too long. They are refreshed into
jameah_student_summary instead (hourly, after migrate, or on demand) and the
view joins that table. Values can therefore lag new grades by up to an hour.
"""
import frappe
from frappe.utils import now_datetime

TABLE = "jameah_student_summary"

# Fallback credit hours for an Education version without utils/credit_hours.py,
# following the old transcript (education.helper.get_transcript_summary):
# a plan course counts as passed when its latest grade result is Pass (or, with no
# result, when the plan row says Passed); bridging-equivalent courses are transferred hours.
CREDITS = """(
	SELECT sp.student,
		SUM(l.credit) AS required,
		SUM(CASE WHEN gr.final_result = 'Pass' OR (gr.final_result IS NULL AND l.status = 'Passed') THEN l.credit ELSE 0 END) AS earned,
		SUM(CASE WHEN gr.final_result IS NULL AND l.status = 'Registered' THEN l.credit ELSE 0 END) AS registered
	FROM `tabStudent Plan` sp
	JOIN `tabStudent Plan List` l ON l.parent = sp.name AND l.parenttype = 'Student Plan' AND l.parentfield = 'student_plan_list'
	LEFT JOIN (
		SELECT student_id, course,
			NULLIF(SUBSTRING_INDEX(GROUP_CONCAT(IFNULL(final_result, '') ORDER BY creation DESC SEPARATOR '\\n'), '\\n', 1), '') AS final_result
		FROM `tabGrade Assessment Results` GROUP BY student_id, course
	) gr ON gr.student_id = sp.student AND gr.course = l.course
	GROUP BY sp.student
) cr ON cr.student = s.name
LEFT JOIN (SELECT student, SUM(IFNULL(calc_hours, 0)) AS hours FROM `tabStudent Bridging Course` GROUP BY student) tr ON tr.student = s.name"""

# Fallback cumulative GPA for an Education version without utils/gpa.py (the
# old transcript rule, course_registration_monitoring._bulk_cumulative_gpa): every grade result of a
# course on the student's latest study plan, weighted by the course's credit
# hours, bridging-equivalent courses excluded. No graded credits -> NULL, not 0.
# Exact decimal average rounded half up (4.325 -> 4.33); the transcript adds up
# in floating point, so at exact ties like this it can show 0.01 less.
GPA = """(
	SELECT x.student, ROUND(SUM(x.points * x.hrs) / SUM(x.hrs), 2) AS gpa
	FROM (
		SELECT g.student_id AS student, g.points, ch.hrs
		FROM `tabGrade Assessment Results` g
		JOIN (
			SELECT student, SUBSTRING_INDEX(GROUP_CONCAT(study_plan ORDER BY creation DESC SEPARATOR '\\n'), '\\n', 1) AS study_plan
			FROM `tabProgram Enrollment` WHERE IFNULL(study_plan, '') != '' GROUP BY student
		) lp ON lp.student = g.student_id
		JOIN `tabCourse Curriculum Definition` ccd ON ccd.course = g.course
		JOIN `tabAcademic Level Course` alc ON alc.parent = lp.study_plan AND alc.parentfield = 'course_level' AND alc.level_course = ccd.name
		JOIN (
			SELECT parent, SUM(CASE WHEN IFNULL(class_type, '') != '' THEN COALESCE(NULLIF(credit_hours, 0), contact_hours, 0) ELSE 0 END) AS hrs
			FROM `tabCourse Class Type` WHERE parenttype = 'Course Curriculum Definition' GROUP BY parent
		) ch ON ch.parent = ccd.name
		LEFT JOIN (SELECT DISTINCT student, equivalent_course FROM `tabStudent Bridging Course`) b
			ON b.student = g.student_id AND b.equivalent_course = ccd.course
		WHERE b.student IS NULL
	) x
	GROUP BY x.student HAVING SUM(x.hrs) > 0
) gp ON gp.student = s.name"""

# Latest submitted Program Enrollment, and the latest term with course registrations.
LATEST = """(
	SELECT student, SUBSTRING_INDEX(GROUP_CONCAT(name ORDER BY enrollment_date DESC, creation DESC SEPARATOR '\\n'), '\\n', 1) AS enrollment
	FROM `tabProgram Enrollment` WHERE docstatus = 1 GROUP BY student
) le ON le.student = s.name
LEFT JOIN (
	SELECT sce.student,
		SUBSTRING_INDEX(GROUP_CONCAT(t.name ORDER BY t.term_start_date DESC, t.name DESC SEPARATOR '\\n'), '\\n', 1) AS term
	FROM `tabStudent Course Enrollment` sce JOIN `tabAcademic Term` t ON t.name = sce.academic_term
	WHERE sce.docstatus < 2 GROUP BY sce.student
) lt ON lt.student = s.name"""


def ensure_table():
	frappe.db.sql_ddl(f"""CREATE TABLE IF NOT EXISTS `{TABLE}` (
		student VARCHAR(140) NOT NULL PRIMARY KEY,
		has_plan TINYINT NOT NULL DEFAULT 0,
		required DECIMAL(21, 9) NULL,
		earned DECIMAL(21, 9) NULL,
		registered DECIMAL(21, 9) NULL,
		transferred DECIMAL(21, 9) NULL,
		gpa DECIMAL(6, 2) NULL,
		latest_enrollment VARCHAR(140) NULL,
		latest_term VARCHAR(140) NULL,
		refreshed_on DATETIME(6) NOT NULL
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")


def official_gpas(student_ids):
	"""The college's official cumulative GPA, {student: gpa or None}, or None
	when this Education version has no central GPA module.

	Education's utils/gpa.py is "the one place a student's GPA is calculated"
	(retakes, superseded fails, XF/W exclusions, legacy baselines...); the
	Ministry must get the same number as the transcript, so it is not
	re-implemented here. No counted credits -> None (not 0.00)."""
	try:
		from education.education.utils.gpa import get_gpa_breakdown
	except ImportError:
		return None
	return {sid: (b["gpa"] if b["credits"] else None) for sid, b in get_gpa_breakdown(student_ids).items()}


def official_credit_hours(student_ids):
	"""Education's official credit-hour figures, {student: {...} or None (no
	Student Plan)}, or None when this Education version has no central module.

	utils/credit_hours.py is "the one place a student's credit-hour figures are
	calculated" (the dashboard and My Transcript read it): required, earned and
	bridged hours over the current Study Plan. registered = credit hours of the
	student's live course registrations in the current term."""
	try:
		from education.education.utils.credit_hours import get_plan_hours, get_term_registered_hours
	except ImportError:
		return None
	term = frappe.db.get_single_value("Education Settings", "current_academic_term")
	out = {}
	for sid in student_ids:
		plan = get_plan_hours(sid)
		out[sid] = plan and {
			"required": plan["hours_required"], "earned": plan["hours_earned"], "transferred": plan["hours_bridged"],
			"registered": get_term_registered_hours(sid, term)["hours"] if term else 0,
		}
	return out


def refresh():
	"""Rebuild the summary in one transaction, so readers never see a half-built table."""
	ensure_table()
	now = now_datetime()
	frappe.db.sql(f"DELETE FROM `{TABLE}`")
	frappe.db.sql(f"""INSERT INTO `{TABLE}`
		(student, has_plan, required, earned, registered, transferred, gpa, latest_enrollment, latest_term, refreshed_on)
		SELECT s.name, cr.student IS NOT NULL, cr.required, cr.earned, cr.registered, tr.hours, gp.gpa, le.enrollment, lt.term, %(now)s
		FROM `tabStudent` s
		LEFT JOIN {CREDITS}
		LEFT JOIN {GPA}
		LEFT JOIN {LATEST}""", {"now": now})
	students = frappe.get_all("Student", pluck="name")
	hours = official_credit_hours(students)
	for student, h in (hours or {}).items():
		if h:
			frappe.db.sql(f"""UPDATE `{TABLE}` SET has_plan = 1, required = %(required)s, earned = %(earned)s,
				registered = %(registered)s, transferred = %(transferred)s WHERE student = %(student)s""", {**h, "student": student})
		else:
			frappe.db.sql(f"UPDATE `{TABLE}` SET has_plan = 0, required = NULL, earned = NULL, registered = NULL, transferred = NULL WHERE student = %s", student)
	official = official_gpas(students)
	if official is not None:
		frappe.db.sql(f"UPDATE `{TABLE}` SET gpa = NULL")
		for student, gpa in official.items():
			if gpa is not None:
				frappe.db.sql(f"UPDATE `{TABLE}` SET gpa = %s WHERE student = %s", (gpa, student))
	frappe.db.set_single_value("Jameah Settings", "academic_summary_refreshed_on", now)
	frappe.db.commit()
	return frappe.db.sql(f"SELECT COUNT(*) FROM `{TABLE}`")[0][0]


@frappe.whitelist()
def refresh_now():
	frappe.only_for(("HR Manager", "Education Manager", "System Manager"))
	frappe.enqueue("medical_hrms.jameah.summary.refresh", queue="long", timeout=1800, job_id="jameah_summary_refresh", deduplicate=True)
	return "queued"
