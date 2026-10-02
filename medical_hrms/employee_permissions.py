import frappe


EMPLOYEE_REQUEST_DOCTYPES = (
	"Permission Request",
	"Remote Work Request",
	"Leave Plan Request",
	"Return from Leave Request",
	"Salary Certificate Request",
	"Pre Approved Overtime Request",
	"Employee Training Request",
	"Children Medical Allowance Request",
	"Company Car Request",
	"Contract Renewal Request",
	"Employee Data Update Request",
)


def get_employee_for_user(user=None):
	user = user or frappe.session.user
	return frappe.db.get_value("Employee", {"user_id": user}, "name")


def get_employee_request_query_condition(user=None):
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if user == "Administrator" or roles.intersection({"HR User", "HR Manager", "System Manager"}):
		return ""
	if "Employee" not in roles:
		return "1=0"

	employee = get_employee_for_user(user)
	if not employee:
		return "1=0"
	return f"`employee` = {frappe.db.escape(employee)}"


def has_employee_request_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if user == "Administrator" or roles.intersection({"HR User", "HR Manager", "System Manager"}):
		return None
	if "Employee" not in roles:
		return False

	employee = get_employee_for_user(user)
	if not employee:
		return False
	if not doc:
		return True
	return (doc.is_new() and not doc.get("employee")) or doc.get("employee") == employee


def get_own_employee_query_condition(user=None):
	user = user or frappe.session.user
	if user == "Administrator" or set(frappe.get_roles(user)).intersection({"HR User", "HR Manager", "System Manager"}):
		return ""
	# Do not override other staff roles' existing permissions.
	if "Employee" not in frappe.get_roles(user):
		return ""
	return f"`tabEmployee`.`user_id` = {frappe.db.escape(user)}"


def has_own_employee_permission(doc, user=None, permission_type=None, ptype=None):
	user = user or frappe.session.user
	if user == "Administrator" or set(frappe.get_roles(user)).intersection({"HR User", "HR Manager", "System Manager"}):
		return None
	if "Employee" not in frappe.get_roles(user):
		return None
	if (ptype or permission_type) in {"write", "create", "delete", "submit", "cancel", "amend", "share"}:
		return False
	return doc.get("user_id") == user if doc else True


def _is_self_service_user(user):
	roles = set(frappe.get_roles(user))
	return user != "Administrator" and "Employee" in roles and not roles.intersection({
		"HR User", "HR Manager", "System Manager", "Accounts User", "Accounts Manager",
		"Leave Approver", "Expense Approver",
	})


def get_self_service_query_condition(user=None):
	user = user or frappe.session.user
	if not _is_self_service_user(user):
		return ""
	return get_employee_request_query_condition(user)


def has_self_service_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if not _is_self_service_user(user):
		return None
	return has_employee_request_permission(doc, user, permission_type)
