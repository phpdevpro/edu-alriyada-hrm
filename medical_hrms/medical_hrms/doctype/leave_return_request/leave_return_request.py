# Copyright (c) 2026, Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, getdate

CLEARED = ("Cleared for Full Duty", "Cleared for Modified Duty")


class LeaveReturnRequest(Document):
	"""The employee tells HR they are back after a leave. HR reviews, the manager confirms readiness,
	and - after sick leave only - occupational health clears the employee before it is Completed."""

	def validate(self):
		from medical_hrms.medical_leave import medical_types

		leave = frappe.db.get_value("Leave Application", self.leave_application,
			["employee", "status", "docstatus", "from_date", "to_date", "leave_type"], as_dict=True)
		if not leave or leave.employee != self.employee:
			frappe.throw(_("Choose one of this employee's leave applications."))
		if leave.status != "Approved" or leave.docstatus != 1:
			frappe.throw(_("Only an approved leave can be returned from."))
		other = frappe.db.get_value("Leave Return Request", {"leave_application": self.leave_application, "name": ["!=", self.name or ""]}, "name")
		if other:
			frappe.throw(_("A return for this leave was already sent ({0}).").format(other))

		self.leave_type = leave.leave_type
		self.is_sick_leave = 1 if leave.leave_type in medical_types().values() else 0
		self.planned_return_date = add_days(leave.to_date, 1)
		if self.actual_return_date:
			if getdate(self.actual_return_date) < getdate(leave.from_date):
				frappe.throw(_("The return date cannot be before the leave started ({0}).").format(frappe.format(leave.from_date, "Date")))
			self.days_late = max(0, date_diff(self.actual_return_date, self.planned_return_date))

		if not self.is_sick_leave:
			self.occupational_health_clearance = "Not Required"
			if self.status == "Pending Occupational Health":
				frappe.throw(_("Occupational health clearance is only needed after sick leave."))
		else:
			if self.status != "Draft" and not self.fitness_certificate:
				frappe.throw(_("Attach the fitness certificate: it is required when returning from sick leave."))
			if self.status in ("Pending Occupational Health", "Completed") and self.occupational_health_clearance == "Not Required":
				self.occupational_health_clearance = "Pending"
			if self.status == "Completed" and self.occupational_health_clearance not in CLEARED:
				frappe.throw(_("After sick leave, record the occupational health clearance (cleared for full or modified duty) before completing."))
