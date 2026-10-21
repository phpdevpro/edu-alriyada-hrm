import frappe

HR_ROLES = {"HR User", "HR Manager"}
HR_DASHBOARD = "/app/hr-dashboard"
EMPLOYEE_DASHBOARD = "/app/employee-dashboard"


def landing_page(roles):
	if HR_ROLES & roles:
		return HR_DASHBOARD
	if "Employee" in roles:
		return EMPLOYEE_DASHBOARD
	return None


def redirect_hr_users_after_login(login_manager=None):
	"""on_session_creation: Frappe returns this as redirect_to, which the login
	page follows for accounts without Desk access ("No App")."""
	user = frappe.session.user
	if not user or user == "Guest":
		return
	if frappe.cache.hget("redirect_after_login", user):
		return
	target = landing_page(set(frappe.get_roles(user)))
	if target:
		frappe.cache.hset("redirect_after_login", user, target)


def boot_session(bootinfo):
	"""Send HR staff and employees to our dashboards after a Desk login.

	The Education app decides the post-login page: its boot_session stores it
	in bootinfo["role_landing_page"], and its role_landing_redirect.js moves
	the browser there. Its role list has no HR roles, so HR accounts got
	"/app" and stayed on the workspace page. This hook runs after Education's
	(apps run in install order) and fills in our dashboards only when
	Education found no dashboard of its own, so an HR person who is also,
	say, an Instructor keeps the Instructor dashboard.
	"""
	user = frappe.session.user
	if user in ("Guest", "Administrator"):
		return
	current = bootinfo.get("role_landing_page")
	if current and current.startswith("/app/"):
		return
	target = landing_page(set(frappe.get_roles(user)))
	if target:
		bootinfo["role_landing_page"] = target
