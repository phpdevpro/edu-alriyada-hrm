"""HR view of the academic timetable: faculty and proctor schedules, students
on campus per hour, and faculty on campus after 4 PM.

Evidence of being on campus, strongest first:
1. Attendance-device logs (HRMS Employee Checkin), when devices are connected.
2. Student Class Attendance recorded for the class that day.
3. The timetable: in-person Class Meeting sessions and Exam Committees.

Regular classes don't run on official days off (HR Settings > Academic
Holiday List) or during academic-calendar events whose type is marked
"Suspends Regular Classes" (see medical_hrms.academic_presence_setup).
"""
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import add_days, getdate, strip_html, today

from medical_hrms.academic_presence_setup import AFTER_HOURS_FIELD, HOLIDAY_LIST_FIELD, SUSPENDS_FIELD

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


def academic_holiday_list():
	"""HR Settings > Academic Holiday List, else the default company's list."""
	holiday_list = frappe.db.get_single_value("HR Settings", HOLIDAY_LIST_FIELD)
	if not holiday_list:
		company = frappe.db.get_single_value("Global Defaults", "default_company")
		holiday_list = company and frappe.db.get_value("Company", company, "default_holiday_list")
	return holiday_list


def _days_off(start, end):
	"""Dates without regular classes in [start, end].

	Returns ({date: reason} for the whole college, from the academic Holiday
	List; {academic_term: {date: reason}} from academic-calendar events
	whose type suspends regular classes)."""
	holiday_list = academic_holiday_list()
	college = {}
	if holiday_list:
		for row in frappe.get_all("Holiday", filters={"parent": holiday_list, "holiday_date": ["between", [start, end]]},
				fields=["holiday_date", "description", "weekly_off"]):
			college[row.holiday_date] = _("Weekly off") if row.weekly_off else (strip_html(row.description or "").strip() or _("Holiday"))

	by_term = {}
	if frappe.db.has_column("Academic Event Type", SUSPENDS_FIELD):
		for event in frappe.db.sql(f"""
			select ac.academic_term, e.start_date, e.end_date, e.title
			from `tabAcademic Calendar Event` e
			join `tabAcademic Calendar` ac on ac.name = e.parent
			join `tabAcademic Event Type` et on et.name = e.event_type
			where et.`{SUSPENDS_FIELD}` = 1 and e.start_date <= %(end)s and ifnull(e.end_date, e.start_date) >= %(start)s
		""", {"start": start, "end": end}, as_dict=True):
			day, last = max(start, event.start_date), min(end, event.end_date or event.start_date)
			while day <= last:
				by_term.setdefault(event.academic_term, {})[day] = event.title
				day = add_days(day, 1)
	return college, by_term


def _sessions(start, end, instructor=None, in_person_only=False, skipped=None):
	"""Teaching sessions on each date in [start, end].

	A Class Meeting's room-schedule row is a WEEKLY slot: it repeats every
	week on its `day`, from its `date` (first occurrence) until the class's
	academic term ends, except on days off (see _days_off). Pass a dict as
	`skipped` to collect {date: reason} for the dates that were left out.
	"""
	college_off, term_off = _days_off(start, end)
	conditions = ["cm.docstatus = 1", "ifnull(rs.date, '1900-01-01') <= %(end)s",
		"(at.term_end_date is null or at.term_end_date >= %(start)s)"]
	if instructor:
		conditions.append("cm.instructor = %(instructor)s")
	if in_person_only:
		conditions.append("ifnull(rs.is_online, 0) = 0")
	slots = frappe.db.sql(f"""
		select rs.date as first_date, rs.day, rs.from_time, rs.to_time, rs.room, ifnull(rs.is_online, 0) as is_online,
			cm.name as class_meeting, cm.class_name, cm.instructor, cm.instructor_name,
			c.course, c.course_code, c.class_type, c.academic_term, ins.email as instructor_email,
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
			reason = college_off.get(current) or term_off.get(slot.academic_term, {}).get(current)
			if reason:
				if skipped is not None:
					skipped[current] = reason
				current += timedelta(days=7)
				continue
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
	skipped = {}
	sessions = _sessions(start, end, instructor, skipped=skipped)
	hours = sum((s.finish - s.start) for s in sessions) / 60
	return {
		"days_off": [{"date": d, "reason": r} for d, r in sorted(skipped.items())],
		"holiday_list_missing": not academic_holiday_list(),
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
	skipped = {}
	sessions = _sessions(on_date, on_date, in_person_only=True, skipped=skipped)
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
		"days_off": [{"date": d, "reason": r} for d, r in sorted(skipped.items())],
		"holiday_list_missing": not academic_holiday_list(),
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

def _faculty_employees():
	"""{instructor email: employee} for faculty linked to an Employee, either
	through Instructor.employee or Employee.user_id = the faculty login."""
	links = {}
	for row in frappe.db.sql("""
		select i.email, coalesce(i.employee, e.name) as employee
		from `tabInstructor` i
		left join `tabEmployee` e on e.user_id = i.email
		where ifnull(i.email, '') != '' and coalesce(i.employee, e.name) is not null
	""", as_dict=True):
		links[row.email] = row.employee
	return links


def _device_logs(employees, start, end):
	"""{(employee, date): [minutes, ...]} from attendance devices (HRMS
	Employee Checkin, filled by the devices through
	hrms...employee_checkin.add_log_based_on_employee_field)."""
	logs = {}
	if not employees:
		return logs
	for row in frappe.db.sql("""
		select employee, time from `tabEmployee Checkin`
		where employee in %(employees)s and time >= %(start)s and time < %(end)s
	""", {"employees": tuple(employees), "start": start, "end": add_days(end, 1)}, as_dict=True):
		logs.setdefault((row.employee, row.time.date()), []).append(row.time.hour * 60 + row.time.minute)
	return logs


def after_hours_cutoff():
	return _as_time(frappe.db.get_single_value("HR Settings", AFTER_HOURS_FIELD) or AFTER_HOURS_DEFAULT)


@frappe.whitelist()
def get_faculty_after_hours(from_date=None, to_date=None, after=None):
	"""Faculty on campus after the cut-off (HR Settings, default 16:00), per
	day. Device logs decide when they exist; otherwise in-person teaching or
	proctoring that ends after the cut-off, confirmed by class attendance."""
	_require_hr()
	start, end = _date_range(from_date, to_date)
	cutoff = _as_time(after) if after else after_hours_cutoff()
	employee_of = _faculty_employees()
	names = dict(frappe.db.sql("select email, instructor_name from `tabInstructor` where ifnull(email, '') != ''"))

	people = {}

	def entry(on_date, email, name):
		return people.setdefault((on_date, email or name), {
			"date": on_date, "name": name or names.get(email) or email, "email": email or "",
			"activities": [], "scheduled_until": 0, "confirmed": False,
		})

	late_sessions = [s for s in _sessions(start, end, in_person_only=True) if s.finish > cutoff]
	taken = set()
	if late_sessions:
		taken = {(r.class_info, r.date) for r in frappe.db.sql("""
			select distinct class_info, date from `tabStudent Class Attendance`
			where class_info in %(classes)s and date between %(start)s and %(end)s and docstatus < 2
		""", {"classes": tuple({s.class_name for s in late_sessions}), "start": start, "end": end}, as_dict=True)}
	for s in late_sessions:
		item = entry(s.date, s.instructor_email, s.instructor_name)
		item["activities"].append(" ".join(filter(None, (_("Teaching"), s.course_code or s.class_name, s.time, s.room))))
		item["scheduled_until"] = max(item["scheduled_until"], s.finish)
		# Attendance recorded for that class that day confirms the session ran.
		item["confirmed"] = item["confirmed"] or (s.class_name, s.date) in taken

	for p in _proctor_assignments(start, end):
		if not p.to_time or _as_time(p.to_time) <= cutoff:
			continue
		item = entry(p.exam_date, p.proctor_email or p.proctor_user, p.proctor_name)
		time = f"{_hhmm(_as_time(p.from_time))} – {_hhmm(_as_time(p.to_time))}"
		item["activities"].append(" ".join(filter(None, (_("Proctoring"), p.course_code or p.exam_class, time, p.room))))
		item["scheduled_until"] = max(item["scheduled_until"], _as_time(p.to_time))

	logs = _device_logs(set(employee_of.values()), start, end)
	email_of = {employee: email for email, employee in employee_of.items()}
	# Faculty the devices saw after the cut-off without anything scheduled.
	for (employee, on_date), times in logs.items():
		email = email_of.get(employee)
		if email and max(times) > cutoff and (on_date, email) not in people:
			entry(on_date, email, None)["activities"].append(_("No class or exam scheduled"))

	rows = []
	for item in people.values():
		times = logs.get((employee_of.get(item["email"]), item["date"]))
		if times:
			left = max(times)
			item["source"] = _("Attendance device")
			item["until"] = _hhmm(left)
			if left > cutoff:
				item["status"] = _("On campus (device), last log {0}").format(_hhmm(left))
			else:
				item["status"] = _("Left at {0} (device), before the scheduled end").format(_hhmm(left))
		else:
			item["source"] = _("Class attendance") if item["confirmed"] else _("Timetable")
			item["until"] = _hhmm(item["scheduled_until"])
			item["status"] = _("Confirmed by attendance") if item["confirmed"] else _("Scheduled")
			if logs and employee_of.get(item["email"]):
				# Devices are in use, but this person has no log that day.
				item["status"] += " · " + _("no device log (missed punch?)")
		item["activities"] = "; ".join(item["activities"])
		del item["scheduled_until"], item["confirmed"]
		rows.append(item)
	# Each day, latest on campus first ("HH:MM" sorts as text).
	rows.sort(key=lambda r: r["until"], reverse=True)
	rows.sort(key=lambda r: r["date"])

	days = {}
	for row in rows:
		days[row["date"]] = days.get(row["date"], 0) + 1
	return {
		"rows": rows,
		"cutoff": _hhmm(cutoff),
		"devices_connected": bool(logs),
		"summary": {
			"people": len({r["email"] or r["name"] for r in rows}),
			"person_days": len(rows),
			"busiest_day": max(days, key=days.get) if days else None,
		},
	}
