"""HR view of the academic timetable: faculty and proctor schedules, students
on campus per hour, and faculty on campus after 4 PM.

There is no physical check-in data, so "on campus" means: booked in an
in-person session (Class Meeting room schedule, or an Exam Committee for
proctors), confirmed by Student Class Attendance where it was recorded.
"""
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import getdate, today

HR_ROLES = {"HR User", "HR Manager", "System Manager"}
PRESENT_STATUSES = ("Present", "Late")
ABSENT_STATUSES = ("Absent", "Absent with Excuse")
# Hourly slots shown in the students report; sessions outside are reported.
FIRST_SLOT_HOUR, LAST_SLOT_HOUR = 7, 22
AFTER_HOURS_DEFAULT = "16:00"
MAX_RANGE_DAYS = 62


def _require_hr():
	if frappe.session.user != "Administrator" and not HR_ROLES.intersection(frappe.get_roles()):
		frappe.throw(_("Only HR can view academic schedules and presence."), frappe.PermissionError)


def _date_range(from_date, to_date):
	start = getdate(from_date or today())
	end = getdate(to_date or start)
	if end < start:
		frappe.throw(_("To Date must be on or after From Date."))
	if (end - start).days > MAX_RANGE_DAYS:
		frappe.throw(_("Choose a range of at most {0} days.").format(MAX_RANGE_DAYS))
	return start, end


def _as_time(value):
	"""DB TIME comes back as timedelta; normalise to minutes since midnight."""
	if isinstance(value, timedelta):
		return int(value.total_seconds() // 60)
	if isinstance(value, str):
		hours, minutes = value.split(":")[:2]
		return int(hours) * 60 + int(minutes)
	return value.hour * 60 + value.minute


def _hhmm(minutes):
	return f"{minutes // 60:02d}:{minutes % 60:02d}"


WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def _sessions(start, end, instructor=None, in_person_only=False):
	"""Teaching sessions on each date in [start, end].

	A Class Meeting's room-schedule row is a WEEKLY slot: it repeats every
	week on its `day`, from its `date` (first occurrence) until the class's
	academic term ends. Holidays in the academic calendar are not removed.
	"""
	conditions = ["cm.docstatus = 1", "ifnull(rs.date, '1900-01-01') <= %(end)s",
		"(at.term_end_date is null or at.term_end_date >= %(start)s)"]
	if instructor:
		conditions.append("cm.instructor = %(instructor)s")
	if in_person_only:
		conditions.append("ifnull(rs.is_online, 0) = 0")
	slots = frappe.db.sql(f"""
		select rs.date as first_date, rs.day, rs.from_time, rs.to_time, rs.room, ifnull(rs.is_online, 0) as is_online,
			cm.name as class_meeting, cm.class_name, cm.instructor, cm.instructor_name,
			c.course, c.course_code, c.class_type, ins.email as instructor_email,
			at.term_start_date, at.term_end_date
		from `tabRoom Schedule` rs
		join `tabClass Meeting` cm on cm.name = rs.parent and rs.parenttype = 'Class Meeting'
		left join `tabClass` c on c.name = cm.class_name
		left join `tabAcademic Term` at on at.name = c.academic_term
		left join `tabInstructor` ins on ins.name = cm.instructor
		where {' and '.join(conditions)}
	""", {"start": start, "end": end, "instructor": instructor}, as_dict=True)

	sessions = []
	for slot in slots:
		if slot.day not in WEEKDAYS:
			continue
		weekday = WEEKDAYS.index(slot.day)
		first = max(d for d in (start, slot.first_date, slot.term_start_date) if d)
		last = min(d for d in (end, slot.term_end_date) if d)
		current = first + timedelta(days=(weekday - first.weekday()) % 7)
		while current <= last:
			session = frappe._dict(slot, date=current)
			session.start, session.finish = _as_time(slot.from_time), _as_time(slot.to_time)
			session.time = f"{_hhmm(session.start)} – {_hhmm(session.finish)}"
			session.mode = _("Online") if slot.is_online else _("On campus")
			sessions.append(session)
			current += timedelta(days=7)
	sessions.sort(key=lambda s: (s.date, s.start, s.instructor_name or ""))
	return sessions


# ---------------------------------------------------------------- 1. faculty

@frappe.whitelist()
def get_faculty_schedule(from_date=None, to_date=None, instructor=None):
	_require_hr()
	start, end = _date_range(from_date, to_date)
	sessions = _sessions(start, end, instructor)
	hours = sum((s.finish - s.start) for s in sessions) / 60
	return {
		"rows": [{
			"date": s.date, "day": s.day, "time": s.time, "instructor": s.instructor,
			"instructor_name": s.instructor_name, "course": s.course_code or s.course,
			"class_name": s.class_name, "class_type": s.class_type, "room": s.room or "",
			"mode": s.mode,
		} for s in sessions],
		"summary": {
			"sessions": len(sessions),
			"instructors": len({s.instructor for s in sessions}),
			"teaching_hours": round(hours, 1),
			"on_campus_sessions": sum(1 for s in sessions if not s.is_online),
		},
	}


# ---------------------------------------------------------------- 2. proctors

def _proctor_assignments(start, end):
	return frappe.db.sql("""
		select ec.name as committee, ec.exam_date, ec.from_time, ec.to_time, ec.room,
			ec.academic_term, e.exam_class, e.exam_type, c.course_code,
			tp.proctor as proctor_user, coalesce(pc.proctor_name, tp.proctor_name) as proctor_name,
			coalesce(pc.proctor_email, tp.proctor_email) as proctor_email
		from `tabExam Committee` ec
		join `tabExam Proctor Child` pc on pc.parent = ec.name and pc.parenttype = 'Exam Committee'
		left join `tabTerm Proctor` tp on tp.name = pc.proctor
		left join `tabExam` e on e.name = ec.exam
		left join `tabClass` c on c.name = e.exam_class
		where ec.docstatus < 2 and ec.exam_date between %(start)s and %(end)s
		order by ec.exam_date, ec.from_time, proctor_name
	""", {"start": start, "end": end}, as_dict=True)


@frappe.whitelist()
def get_proctor_schedule(from_date=None, to_date=None):
	_require_hr()
	start, end = _date_range(from_date, to_date)
	rows = _proctor_assignments(start, end)
	for row in rows:
		row.time = f"{_hhmm(_as_time(row.from_time))} – {_hhmm(_as_time(row.to_time))}" if row.from_time and row.to_time else ""
	return {
		"rows": [{
			"date": r.exam_date, "time": r.time, "proctor_name": r.proctor_name or r.proctor_user,
			"proctor_email": r.proctor_email, "exam": r.course_code or r.exam_class or "", "exam_type": r.exam_type or "",
			"room": r.room or "", "committee": r.committee,
		} for r in rows],
		"summary": {
			"assignments": len(rows),
			"proctors": len({r.proctor_user or r.proctor_name for r in rows}),
			"committees": len({r.committee for r in rows}),
		},
	}


# ------------------------------------------------- 3. students on campus/hour

def _active_rosters(classes):
	"""{class: {students}} for registered (not dropped) enrollments."""
	rosters = {c: set() for c in classes}
	if not classes:
		return rosters
	for row in frappe.db.sql("""
		select enrolled_class, student from `tabStudent Course Enrollment`
		where enrolled_class in %(classes)s and docstatus < 2
			and ifnull(enrollment_status, '') like 'Registered%%'
	""", {"classes": tuple(classes)}, as_dict=True):
		rosters[row.enrolled_class].add(row.student)
	return rosters


def _attendance(classes, on_date):
	"""{class: {student: status}} recorded for that date."""
	marks = {c: {} for c in classes}
	if not classes:
		return marks
	for row in frappe.db.sql("""
		select class_info, student, status from `tabStudent Class Attendance`
		where class_info in %(classes)s and date = %(date)s and docstatus < 2
	""", {"classes": tuple(classes), "date": on_date}, as_dict=True):
		marks[row.class_info][row.student] = row.status
	return marks


@frappe.whitelist()
def get_students_presence(on_date=None):
	_require_hr()
	on_date = getdate(on_date or today())
	sessions = _sessions(on_date, on_date, in_person_only=True)
	classes = sorted({s.class_name for s in sessions if s.class_name})
	rosters, marks = _active_rosters(classes), _attendance(classes, on_date)

	slots, outside = [], []
	for hour in range(FIRST_SLOT_HOUR, LAST_SLOT_HOUR):
		slot_start, slot_end = hour * 60, (hour + 1) * 60
		active = [s for s in sessions if s.start < slot_end and s.finish > slot_start]
		expected, present, absent, unrecorded = set(), set(), set(), set()
		for session in active:
			for student in rosters.get(session.class_name, ()):
				expected.add(student)
				status = marks[session.class_name].get(student)
				if status in PRESENT_STATUSES:
					present.add(student)
				elif status in ABSENT_STATUSES:
					absent.add(student)
				else:
					unrecorded.add(student)
		# A student is present in the hour if present in any class then.
		absent -= present
		unrecorded -= present | absent
		recorded = len(present) + len(absent)
		slots.append({
			"slot": f"{_hhmm(slot_start)} – {_hhmm(slot_end)}",
			"sessions": len(active),
			"expected": len(expected),
			"present": len(present),
			"absent": len(absent),
			"not_recorded": len(unrecorded),
			"attendance_rate": round(100 * len(present) / recorded, 1) if recorded else None,
		})
	for session in sessions:
		if session.start < FIRST_SLOT_HOUR * 60 or session.finish > LAST_SLOT_HOUR * 60:
			outside.append({"class_name": session.class_name, "time": session.time, "instructor_name": session.instructor_name})

	busiest = max(slots, key=lambda s: s["present"], default=None)
	return {
		"date": on_date,
		"slots": [s for s in slots if s["sessions"]] or [],
		"summary": {
			"in_person_sessions": len(sessions),
			"students_expected": len(set().union(*rosters.values())) if rosters else 0,
			"students_present": len({st for c in classes for st, status in marks[c].items() if status in PRESENT_STATUSES}),
			"busiest_slot": busiest["slot"] if busiest and busiest["present"] else None,
		},
		"outside_hours": outside,
	}


# -------------------------------------------------- 4. faculty after 4 PM

@frappe.whitelist()
def get_faculty_after_hours(from_date=None, to_date=None, after="16:00"):
	"""Faculty on campus after a cut-off time, per day: in-person teaching
	that ends after it, plus exam proctoring that ends after it."""
	_require_hr()
	start, end = _date_range(from_date, to_date)
	cutoff = _as_time(after or AFTER_HOURS_DEFAULT)

	people = {}

	def entry(on_date, key, name, email):
		return people.setdefault((on_date, key), {
			"date": on_date, "name": name, "email": email or "", "activities": [],
			"last_leave": 0, "confirmed": False,
		})

	late_sessions = [s for s in _sessions(start, end, in_person_only=True) if s.finish > cutoff]
	taken = set()
	if late_sessions:
		taken = {(r.class_info, r.date) for r in frappe.db.sql("""
			select distinct class_info, date from `tabStudent Class Attendance`
			where class_info in %(classes)s and date between %(start)s and %(end)s and docstatus < 2
		""", {"classes": tuple({s.class_name for s in late_sessions}), "start": start, "end": end}, as_dict=True)}
	for s in late_sessions:
		item = entry(s.date, s.instructor_email or s.instructor, s.instructor_name, s.instructor_email)
		item["activities"].append(" ".join(filter(None, (_("Teaching"), s.course_code or s.class_name, s.time, s.room))))
		item["last_leave"] = max(item["last_leave"], s.finish)
		# Attendance recorded for that class that day confirms the session ran.
		item["confirmed"] = item["confirmed"] or (s.class_name, s.date) in taken

	for p in _proctor_assignments(start, end):
		if not p.to_time or _as_time(p.to_time) <= cutoff:
			continue
		item = entry(p.exam_date, p.proctor_email or p.proctor_user, p.proctor_name or p.proctor_user, p.proctor_email)
		time = f"{_hhmm(_as_time(p.from_time))} – {_hhmm(_as_time(p.to_time))}"
		item["activities"].append(" ".join(filter(None, (_("Proctoring"), p.course_code or p.exam_class, time, p.room))))
		item["last_leave"] = max(item["last_leave"], _as_time(p.to_time))

	rows = sorted(people.values(), key=lambda r: (r["date"], -r["last_leave"], r["name"] or ""))
	for row in rows:
		row["until"] = _hhmm(row["last_leave"])
		row["activities"] = "; ".join(row["activities"])
		row["status"] = _("Confirmed by attendance") if row["confirmed"] else _("Scheduled")
		del row["last_leave"], row["confirmed"]
	days = {}
	for row in rows:
		days[row["date"]] = days.get(row["date"], 0) + 1
	return {
		"rows": rows,
		"cutoff": _hhmm(cutoff),
		"summary": {
			"people": len({r["email"] or r["name"] for r in rows}),
			"person_days": len(rows),
			"busiest_day": max(days, key=days.get) if days else None,
		},
	}
