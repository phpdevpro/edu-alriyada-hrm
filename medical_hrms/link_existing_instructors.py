"""Create and link Employee records for existing Active Instructors.

Instructors created before recruitment conversion existed have no Employee,
so they get no HR self-service and HR can't manage them. For each Active
Instructor without an Employee this creates one (same field mapping as
recruitment conversion), links Instructor.employee and any Academic Advisor
with the same email, and gives the login the Employee role.

Dry run by default: every record is attempted inside a savepoint that is
rolled back, and a report of what would succeed or fail is printed.

    bench --site <site> execute medical_hrms.link_existing_instructors.execute
    bench --site <site> execute medical_hrms.link_existing_instructors.execute --kwargs "{'commit': 1}"
"""
from collections import Counter

import frappe
from frappe.utils import getdate

from medical_hrms.medical_hrms.recruitment.job_application import (
	INSTRUCTOR_CHILD_TABLE_FIELDNAMES,
	_copy_matching_child_tables,
	_copy_matching_scalar_fields,
	_ensure_user_role,
	get_default_company,
	split_full_name,
)

# Instructor-only or differently-typed fields; everything else with an
# identical fieldname (the Jameah custom fields) is copied across.
SKIP_FIELDS = {
	"name", "owner", "creation", "modified", "modified_by", "docstatus", "idx",
	"naming_series", "doctype", "status", "gender", "department", "employee",
	"amended_from",
}


def _ministry_gender(label):
	"""Instructor.gender holds a Gender Edu label; Employee.gender a Ministry code."""
	if not label:
		return None
	return frappe.db.get_value("Jameah Ministry Code", {"code_category": "Gender", "name_english": label}, "name")


def _core_department(department_edu, company):
	"""Department Edu and core Department share their department_name label."""
	if not department_edu:
		return None
	label = frappe.db.get_value("Department Edu", department_edu, "department_name") or department_edu
	return frappe.db.get_value("Department", {"department_name": label, "company": company}, "name")


def _build_employee(instructor, company):
	employee = frappe.new_doc("Employee")
	first_name, last_name = split_full_name(instructor.instructor_name)
	employee.first_name = instructor.get("custom_first_name_en") or first_name or instructor.instructor_name
	employee.last_name = instructor.get("custom_last_name_en") or last_name
	employee.employee_name = instructor.instructor_name
	employee.company = company
	employee.status = "Active"
	employee.employee_number = instructor.employee_no
	employee.date_of_joining = (
		instructor.instructor_appoinment_date or instructor.instructor_start_date or getdate(instructor.creation)
	)
	employee.gender = _ministry_gender(instructor.gender)
	employee.department = _core_department(instructor.department, company)
	employee.cell_number = instructor.mobile_no
	employee.company_email = instructor.email
	employee.personal_email = instructor.personal_email_id
	_copy_matching_scalar_fields(instructor, employee, SKIP_FIELDS)
	_copy_matching_child_tables(instructor, employee, INSTRUCTOR_CHILD_TABLE_FIELDNAMES)
	# Ministry fields the Instructor never captured (e.g. date of birth) are
	# left for HR to complete, as with recruitment conversion.
	employee.flags.ignore_mandatory = True
	return employee


def _link_one(instructor, company, commit):
	user = instructor.email if instructor.email and frappe.db.exists("User", instructor.email) else None
	existing = frappe.db.get_value("Employee", {"user_id": user}, "name") if user else None
	if existing:
		employee_name = existing
	else:
		employee = _build_employee(instructor, company)
		employee.insert(ignore_permissions=True)
		employee_name = employee.name
		if user:
			# Raw write, as in recruitment: Employee.on_update would sync the
			# Ministry gender code onto User.gender, which links to Gender.
			frappe.db.set_value("Employee", employee_name, "user_id", user)

	frappe.db.set_value("Instructor", instructor.name, "employee", employee_name)
	advisor = frappe.db.get_value("Academic Advisor", {"email": instructor.email, "employee": ["is", "not set"]}, "name")
	if advisor:
		frappe.db.set_value("Academic Advisor", advisor, "employee", employee_name)
	# Changing a User's roles runs User hooks; only do it for real.
	if user and commit:
		_ensure_user_role(user, "Employee")
	return "linked existing Employee" if existing else "created Employee"


def execute(commit=0, limit=None):
	commit = int(commit)
	company = get_default_company()
	if not company:
		frappe.throw("Set a default Company first.")

	names = frappe.get_all(
		"Instructor",
		filters={"status": "Active", "employee": ["is", "not set"]},
		pluck="name",
		order_by="name",
		limit=int(limit) if limit else None,
	)
	outcomes, failures = Counter(), Counter()
	examples = {}
	for name in names:
		instructor = frappe.get_doc("Instructor", name)
		frappe.db.savepoint("link_instructor")
		try:
			outcome = _link_one(instructor, company, commit)
		except Exception as error:
			frappe.db.rollback(save_point="link_instructor")
			reason = frappe.utils.strip_html(str(error)).split("\n")[0][:120] or type(error).__name__
			failures[reason] += 1
			examples.setdefault(reason, name)
		else:
			outcomes[outcome] += 1
			if commit:
				frappe.db.commit()
			else:
				frappe.db.rollback(save_point="link_instructor")
		finally:
			frappe.local.message_log = []

	if not commit:
		frappe.db.rollback()

	mode = "COMMITTED" if commit else "DRY RUN (nothing saved)"
	print(f"\n{mode}: {len(names)} Active Instructors without an Employee, company {company}")
	for outcome, count in outcomes.items():
		print(f"  OK    {count:4}  {outcome}")
	for reason, count in failures.most_common():
		print(f"  FAIL  {count:4}  {reason}  (e.g. {examples[reason]})")
	return {"total": len(names), "ok": dict(outcomes), "failed": dict(failures)}
