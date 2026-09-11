# Copyright (c) 2026, Admin and contributors
# For license information, please see license.txt

import uuid

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, get_url


class JobApplicationLink(Document):
	def validate(self):
		if self.valid_from and self.valid_until and get_datetime(self.valid_from) >= get_datetime(self.valid_until):
			frappe.throw(_("Valid Until must be after Valid From."))

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
