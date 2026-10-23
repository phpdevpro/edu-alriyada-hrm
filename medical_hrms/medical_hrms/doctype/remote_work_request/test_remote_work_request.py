# Copyright (c) 2026, Admin and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from medical_hrms.medical_hrms.doctype.remote_work_request.remote_work_request import request_days


class TestRemoteWorkRequest(FrappeTestCase):
	def test_calendar_days_without_a_holiday_list(self):
		# dates no holiday list covers yet: calendar days, both ends counted
		employee = frappe.db.get_value("Employee", {"status": "Active"}, "name")
		if not employee:
			self.skipTest("needs an active employee")
		self.assertEqual(request_days(employee, "2099-11-03", "2099-11-03"), 1)
		self.assertEqual(request_days(employee, "2099-11-03", "2099-11-05"), 3)

	def test_working_days_skip_holidays(self):
		employee = frappe.db.get_value("Employee", {"status": "Active", "holiday_list": ["is", "set"]}, ["name", "holiday_list"], as_dict=True)
		if not employee:
			self.skipTest("needs an active employee with a holiday list")
		bounds = frappe.db.get_value("Holiday List", employee.holiday_list, ["from_date", "to_date"], as_dict=True)
		holiday = frappe.db.get_value("Holiday", {"parent": employee.holiday_list, "holiday_date": ["between", [bounds.from_date, frappe.utils.add_days(bounds.to_date, -7)]]}, "holiday_date")
		if not holiday:
			self.skipTest("holiday list has no holidays")
		week = (holiday, frappe.utils.add_days(holiday, 6))
		holidays = frappe.db.count("Holiday", {"parent": employee.holiday_list, "holiday_date": ["between", list(week)]})
		self.assertEqual(request_days(employee.name, *week), 7 - holidays)

	def test_to_date_before_from_date_is_refused(self):
		doc = frappe.get_doc({"doctype": "Remote Work Request", "employee": "NO-SUCH-EMPLOYEE", "from_date": "2026-11-05", "to_date": "2026-11-03"})
		self.assertRaises(frappe.ValidationError, doc.validate)
