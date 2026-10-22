"""Leave flow: plan -> apply -> return. Each test rolls back its data.

	bench --site <site> run-tests --module medical_hrms.test_leave_flow
"""
import unittest
from unittest.mock import patch

import frappe
from frappe.utils import add_days, getdate, today

C = lambda category, code: f"{category}::{code}"


def holiday_list_for_today():
	return frappe.db.get_value("Holiday List", {"from_date": ["<=", today()], "to_date": [">=", today()]}, "name")


def working_days(calendar, start, count, step=1):
	"""`count` consecutive working days (no holiday in `calendar`) found walking from `start`."""
	holidays = {getdate(d) for d in frappe.get_all("Holiday", filters={"parent": calendar}, pluck="holiday_date")}
	day, run = getdate(start), []
	while len(run) < count:
		run = run + [day] if day not in holidays else []
		day = add_days(day, step)
	return sorted(run)


@unittest.skipUnless(frappe.db and frappe.db.exists("Company", "Medical College") and holiday_list_for_today(), "needs a company and a holiday list covering today")
class TestLeaveFlow(unittest.TestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)  # runs even when setUp fails
		frappe.set_user("Administrator")
		self.calendar = holiday_list_for_today()
		department = frappe.db.get_value("Department", {"company": "Medical College", "is_group": 0}, "name")
		self.employee = frappe.get_doc(dict(
			doctype="Employee", naming_series="HR-EMP-", first_name="Leave", last_name="Flow", status="Active", company="Medical College",
			department=department, branch=frappe.db.get_value("Branch", {}, "name"), date_of_birth="1985-03-14", date_of_joining="2022-09-01",
			holiday_list=holiday_list_for_today(), leave_approver="Administrator", gender=C("Gender", "1"),
			custom_jameah_nationality=C("Nationality", "101"), custom_identity_type=C("Identity type", "01"), custom_identity_number="1099123470",
			custom_ministry_work_city=C("Coding cities and governora", "0202000"), custom_ministry_job_rank=C("Job ranks", "01"),
		)).insert(ignore_permissions=True).name
		year = getdate(today()).year
		allocation = frappe.get_doc(dict(doctype="Leave Allocation", employee=self.employee, leave_type="Annual Leave",
			from_date=f"{year}-01-01", to_date=f"{year}-12-31", new_leaves_allocated=10)).insert(ignore_permissions=True)
		allocation.submit()
		past = working_days(self.calendar, add_days(today(), -3), 2, step=-1)
		self.leave = self.approved_leave(past[0], past[1])

	def approved_leave(self, start, end):
		leave = frappe.get_doc(dict(doctype="Leave Application", employee=self.employee, leave_type="Annual Leave", from_date=start, to_date=end,
			leave_approver="Administrator", status="Approved", company="Medical College")).insert(ignore_permissions=True)
		leave.submit()
		return leave

	def leave_return(self, **values):
		return frappe.get_doc(dict(doctype="Leave Return Request", employee=self.employee, leave_application=self.leave.name,
			actual_return_date=add_days(today(), -2), status="Pending HR Review", **values))

	def test_return_after_annual_leave(self):
		doc = self.leave_return().insert(ignore_permissions=True)
		self.assertEqual(getdate(doc.planned_return_date), getdate(add_days(self.leave.to_date, 1)))
		self.assertEqual(doc.days_late, max(0, (getdate(doc.actual_return_date) - getdate(doc.planned_return_date)).days))
		self.assertEqual((doc.is_sick_leave, doc.occupational_health_clearance, doc.leave_type), (0, "Not Required", "Annual Leave"))
		doc.status = "Pending Occupational Health"
		self.assertRaises(frappe.ValidationError, doc.save, ignore_permissions=True)
		doc.reload()
		doc.status = "Completed"
		doc.save(ignore_permissions=True)

	def fitness_certificate(self):
		"""A real private file (an unknown path makes Frappe log 'Error Attaching File'); the rollback removes it from disk."""
		return frappe.get_doc(dict(doctype="File", file_name="qa-fitness.txt", is_private=1, content=b"QA fitness certificate")).insert(ignore_permissions=True).file_url

	def test_return_after_sick_leave_needs_certificate_and_clearance(self):
		with patch("medical_hrms.medical_leave.medical_types", return_value={"sick_full": "Annual Leave"}):
			self.assertRaises(frappe.ValidationError, self.leave_return().insert, ignore_permissions=True)
			doc = self.leave_return(fitness_certificate=self.fitness_certificate()).insert(ignore_permissions=True)
			self.assertEqual(doc.is_sick_leave, 1)
			doc.status = "Completed"
			self.assertRaises(frappe.ValidationError, doc.save, ignore_permissions=True)
			doc.reload()
			doc.status, doc.occupational_health_clearance = "Completed", "Cleared for Full Duty"
			doc.save(ignore_permissions=True)

	def test_one_return_per_leave_and_only_after_approval(self):
		self.leave_return().insert(ignore_permissions=True)
		self.assertRaises(frappe.ValidationError, self.leave_return().insert, ignore_permissions=True)
		day = working_days(self.calendar, add_days(today(), 20), 1)[0]
		open_leave = frappe.get_doc(dict(doctype="Leave Application", employee=self.employee, leave_type="Annual Leave", from_date=day,
			to_date=day, leave_approver="Administrator", status="Open", company="Medical College")).insert(ignore_permissions=True)
		doc = self.leave_return()
		doc.leave_application = open_leave.name
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_leave_plan(self):
		start = working_days(self.calendar, add_days(today(), 30), 1)[0]
		plan = frappe.get_doc(dict(doctype="Leave Plan Request", employee=self.employee, leave_type="Annual Leave",
			from_date=start, to_date=add_days(start, 3), status="Pending Manager")).insert(ignore_permissions=True)
		self.assertEqual(plan.for_year, getdate(start).year)
		self.assertTrue(0 < plan.planned_days <= 4)
		overlap = frappe.get_doc(dict(doctype="Leave Plan Request", employee=self.employee, leave_type="Annual Leave",
			from_date=add_days(start, 2), to_date=add_days(start, 5), status="Pending Manager"))
		self.assertRaises(frappe.ValidationError, overlap.insert, ignore_permissions=True)
		backwards = frappe.get_doc(dict(doctype="Leave Plan Request", employee=self.employee, leave_type="Annual Leave",
			from_date=add_days(start, 10), to_date=add_days(start, 9), status="Draft"))
		self.assertRaises(frappe.ValidationError, backwards.insert, ignore_permissions=True)

	def test_leave_choices_only_held_leave(self):
		from medical_hrms.self_service import leave_choices

		choices = leave_choices(self.employee)
		types = [c["leave_type"] for c in choices]
		self.assertEqual(types[0], "Annual Leave")
		self.assertIn("days left", choices[0]["label"])
		self.assertFalse({"Casual Leave", "Privilege Leave", "Compensatory Off", "Sick Leave 1 - Full Pay"} & set(types))
		# unpaid leave is always offered, last
		self.assertEqual(frappe.db.get_value("Leave Type", types[-1], "is_lwp"), 1)
