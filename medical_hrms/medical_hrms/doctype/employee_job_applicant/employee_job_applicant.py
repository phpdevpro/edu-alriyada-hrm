# Copyright (c) 2026, Admin and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class EmployeeJobApplicant(Document):
	def validate(self):
		if self.application_category == "Academic Staff" and not self.academic_qualifications:
			frappe.throw(_("Academic Qualifications are required for Academic Staff applicants."))
