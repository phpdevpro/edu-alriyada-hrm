"""Per-student academic aggregates for jameahStudentAcademicDetails.

Credit hours, GPA, latest enrollment and latest registered term come from
Education tables with no index on the student (90,000+ grade rows), so
computing them inside the view takes ~30 seconds. They are refreshed into
jameah_student_summary instead (hourly, after migrate, or on demand) and the
view joins that table. Values can therefore lag new grades by up to an hour.
"""
import frappe
from frappe.utils import now_datetime

TABLE = "jameah_student_summary"

# Student credit hours, following the transcript (education.helper.get_transcript_summary):
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

# Cumulative GPA as the transcript computes it (education's
# course_registration_monitoring._bulk_cumulative_gpa): every grade result of a
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
	frappe.db.set_single_value("Jameah Settings", "academic_summary_refreshed_on", now)
	frappe.db.commit()
	return frappe.db.sql(f"SELECT COUNT(*) FROM `{TABLE}`")[0][0]


@frappe.whitelist()
def refresh_now():
	frappe.only_for(("HR Manager", "Education Manager", "System Manager"))
	frappe.enqueue("medical_hrms.jameah.summary.refresh", queue="long", timeout=1800, job_id="jameah_summary_refresh", deduplicate=True)
	return "queued"
