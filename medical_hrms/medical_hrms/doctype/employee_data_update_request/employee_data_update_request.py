# Copyright (c) 2026, Admin and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EmployeeDataUpdateRequest(Document):
	def validate(self):
		from medical_hrms.employee_permissions import get_employee_for_user

		roles = set(frappe.get_roles())
		if frappe.session.user == "Administrator" or roles.intersection({"HR User", "HR Manager", "System Manager"}):
			return
		employee = get_employee_for_user()
		if "Employee" not in roles or not employee:
			frappe.throw("Your login must be linked to an Employee record.", frappe.PermissionError)
		if self.employee and self.employee != employee:
			frappe.throw("You can only request changes to your own details.", frappe.PermissionError)
		self.employee = employee
		previous = self.get_doc_before_save()
		if previous and previous.status != "Draft":
			frappe.throw("This request has been sent to HR and can no longer be edited.", frappe.PermissionError)
		if self.status not in ("Draft", "Pending Manager Acknowledgment"):
			frappe.throw("Only HR can update the approval status.", frappe.PermissionError)
		if previous and previous.employee != employee:
			frappe.throw("You cannot change the employee on this request.", frappe.PermissionError)


@frappe.whitelist()
def create_my_request(update_type, new_value, send=False):
	"""Small employee-facing API; identity and status never come from form fields."""
	from frappe.utils import cint
	from medical_hrms.employee_permissions import get_employee_for_user

	if "Employee" not in frappe.get_roles():
		frappe.throw("Employee access is required.", frappe.PermissionError)
	employee = get_employee_for_user()
	if not employee:
		frappe.throw("Please ask HR to link your login to your Employee record.")
	if update_type not in {"Name Spelling", "Address", "Emergency Contact", "Marital Status"}:
		frappe.throw("Choose a valid correction type.")
	if not isinstance(new_value, str) or not new_value.strip() or len(new_value) > 4000:
		frappe.throw("Enter the corrected details (up to 4,000 characters).")
	doc = frappe.get_doc({
		"doctype": "Employee Data Update Request", "employee": employee,
		"update_type": update_type, "new_value": new_value.strip(),
		"status": "Pending Manager Acknowledgment" if cint(send) else "Draft",
	})
	doc.insert()
	return {"name": doc.name, "status": doc.status}
