import frappe


def redirect_hr_users_after_login(login_manager=None):
	user = frappe.session.user
	if not user or user == "Guest":
		return

	roles = set(frappe.get_roles(user))
	if frappe.cache.hget("redirect_after_login", user):
		return

	if {"HR User", "HR Manager"} & roles:
		frappe.cache.hset("redirect_after_login", user, "/app/hr-dashboard")
	elif "Employee" in roles:
		frappe.cache.hset("redirect_after_login", user, "/app/employee-dashboard")
