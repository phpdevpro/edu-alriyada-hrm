# Copyright (c) 2026, Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, getdate


class LeavePlanRequest(Document):
	"""An employee's planned leave for the year: approved by the manager and the department head.
	It uses no leave balance; when the time comes the employee applies for it (Apply now on the
	Employee Portal), and the leave application is linked here."""

	def validate(self):
		if getdate(self.to_date) < getdate(self.from_date):
			frappe.throw(_("To Date cannot be before From Date."))
		self.for_year = getdate(self.from_date).year
		self.planned_days = self.leave_days()
		overlap = frappe.db.get_value("Leave Plan Request", {
			"employee": self.employee, "name": ["!=", self.name or ""], "status": ["!=", "Rejected"],
			"from_date": ["<=", self.to_date], "to_date": [">=", self.from_date]}, "name")
		if overlap:
			frappe.throw(_("These dates overlap another leave plan ({0}).").format(overlap))
		if self.leave_application:
			application = frappe.db.get_value("Leave Application", self.leave_application, "employee")
			if application != self.employee:
				frappe.throw(_("The linked leave application belongs to another employee."))

	def leave_days(self):
		"""Working days as the leave application will count them; calendar days when HR has not set up a holiday list yet."""
		from hrms.hr.doctype.leave_application.leave_application import get_number_of_leave_days

		try:
			return get_number_of_leave_days(self.employee, self.leave_type, self.from_date, self.to_date)
		except frappe.ValidationError:
			frappe.clear_last_message()
			return date_diff(self.to_date, self.from_date) + 1
