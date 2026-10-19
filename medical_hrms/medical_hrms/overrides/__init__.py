import frappe

# HRM_APPROVAL_MATRIX.md routes financial approval to Accounts Manager, while
# the Education app's finance team uses Finance Manager. Either may give
# finance approval; configure_hrm_request_governance grants both access.
FINANCE_APPROVER_ROLES = ("Finance Manager", "Accounts Manager")


def has_any_role(*roles):
	return frappe.session.user == "Administrator" or bool(set(roles) & set(frappe.get_roles()))
