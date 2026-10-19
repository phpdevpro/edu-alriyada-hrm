# Copyright (c) 2026, Admin and contributors
# For license information, please see license.txt

import uuid

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, get_url

from medical_hrms.medical_hrms.recruitment.job_application import validate_hireable_role

NON_ACADEMIC_CATEGORY = "Non-Academic / Other Staff"
NON_ACADEMIC_ROLE = "Employee"


class JobApplicationLink(Document):
	def validate(self):
		if self.valid_from and self.valid_until and get_datetime(self.valid_from) >= get_datetime(self.valid_until):
			frappe.throw(_("Valid Until must be after Valid From."))

		# Non-Academic / Other Staff links always apply under the generic
		# "Employee" Role - the UI locks the field for this category (see
		# job_application_link.js), but that's a convenience only; enforce it
		# here too so it can't be bypassed via the API or a bulk edit.
		if self.application_category == NON_ACADEMIC_CATEGORY:
			self.role = NON_ACADEMIC_ROLE
		validate_hireable_role(self.role)

	@frappe.whitelist()
	def generate_link(self):
		frappe.has_permission("Job Application Link", "write", self.name, throw=True)
		if not self.valid_from or not self.valid_until:
			frappe.throw(_("Please set Valid From and Valid Until before generating the link."))

		token = self._generate_unique_token()
		self.generated_token = token
		self.generated_url = get_url(f"/job-application/{token}")
		self.save(ignore_permissions=True)
		return {"token": self.generated_token, "url": self.generated_url}

	def _generate_unique_token(self):
		for _attempt in range(5):
			token = uuid.uuid4().hex
			if not frappe.db.exists("Job Application Link", {"generated_token": token}):
				return token
		frappe.throw(_("Unable to generate a unique token. Please try again."))
