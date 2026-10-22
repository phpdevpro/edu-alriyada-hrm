import frappe
from frappe import _
from frappe.utils import add_days, getdate, today
from medical_hrms.monthly_leave_policy import dashboard_summary


REQUEST_DOCTYPES = (
	"Permission Request",
	"Remote Work Request",
	"Leave Plan Request",
	"Leave Application",
	"Leave Return Request",
	"Salary Certificate Request",
	"Pre Approved Overtime Request",
	"Employee Training Request",
	"Children Medical Allowance Request",
	"Company Car Request",
	"Contract Renewal Request",
	"Employee Data Update Request",
)

APPROVED_STATUSES = {"Approved", "Completed", "Issued"}
REJECTED_STATUSES = {"Rejected", "Cancelled", "Declined"}


def _require_employee_access():
	roles = set(frappe.get_roles())
	if frappe.session.user == "Administrator" or roles.intersection({"Employee", "System Manager"}):
		return
	frappe.throw(_("You are not permitted to view the Employee Dashboard."), frappe.PermissionError)


def _get_employee():
	return frappe.db.get_value(
		"Employee",
		{"user_id": frappe.session.user},
		[
			"name",
			"employee_name",
			"designation",
			"department",
			"company",
			"image",
			"status",
		],
		as_dict=True,
	)


def _empty_response():
	user = frappe.get_cached_doc("User", frappe.session.user)
	return {
		"status": "unlinked",
		"message": _("Your user account is not linked to an Employee record. Please contact HR."),
		"user": {
			"full_name": user.full_name or user.first_name or frappe.session.user,
			"email": frappe.session.user,
		},
		"employee": None,
		"stats": {"total": 0, "pending": 0, "approved": 0, "leave_applications": 0},
		"counts": {},
		"recent_requests": [],
	}


def leave_flow(employee):
	"""The employee's leave, as the next step for each item: a return to send, leave in progress or coming up,
	requests waiting for approval, and approved plans not applied for yet."""
	now = getdate(today())
	steps = []
	returned = set(frappe.get_all("Leave Return Request", filters={"employee": employee}, pluck="leave_application"))
	for app in frappe.get_all("Leave Application", filters={"employee": employee, "docstatus": ["<", 2], "status": ["in", ["Open", "Approved"]]},
			fields=["name", "leave_type", "from_date", "to_date", "status", "docstatus", "total_leave_days"], order_by="from_date"):
		start, end = getdate(app.from_date), getdate(app.to_date)
		item = {"leave_type": app.leave_type, "from_date": app.from_date, "to_date": app.to_date, "days": app.total_leave_days, "name": app.name}
		if app.status == "Open":
			steps.append({**item, "step": "waiting", "doctype": "Leave Application"})
		elif app.docstatus == 1 and end < now and app.name not in returned and end >= add_days(now, -60):
			steps.append({**item, "step": "return_due", "doctype": "Leave Application", "back_on": add_days(end, 1)})
		elif app.docstatus == 1 and start <= now <= end:
			steps.append({**item, "step": "on_leave", "doctype": "Leave Application"})
		elif app.docstatus == 1 and start > now:
			steps.append({**item, "step": "upcoming", "doctype": "Leave Application"})
	for plan in frappe.get_all("Leave Plan Request", filters={"employee": employee, "status": ["not in", ["Rejected", "Draft"]], "to_date": [">=", now]},
			fields=["name", "leave_type", "from_date", "to_date", "planned_days", "status", "leave_application"], order_by="from_date"):
		item = {"leave_type": plan.leave_type, "from_date": plan.from_date, "to_date": plan.to_date, "days": plan.planned_days, "name": plan.name, "doctype": "Leave Plan Request"}
		if plan.status == "Approved" and not plan.leave_application:
			steps.append({**item, "step": "plan_approved"})
		elif plan.status.startswith("Pending"):
			steps.append({**item, "step": "plan_waiting", "status": plan.status})
	order = ["return_due", "on_leave", "plan_approved", "waiting", "plan_waiting", "upcoming"]
	steps.sort(key=lambda s: (order.index(s["step"]), str(s["from_date"])))
	return steps


@frappe.whitelist()
def get_dashboard_data():
	_require_employee_access()
	employee = _get_employee()
	if not employee:
		return _empty_response()

	counts = {}
	total = pending = approved = 0
	recent_requests = []

	for doctype in REQUEST_DOCTYPES:
		if not frappe.db.exists("DocType", doctype):
			continue

		rows = frappe.get_all(
			doctype,
			filters={"employee": employee.name},
			fields=["name", "status", "modified"],
			order_by="modified desc",
			limit_page_length=5,
		)
		count = frappe.db.count(doctype, {"employee": employee.name})
		counts[doctype] = count
		total += count

		for row in rows:
			status = row.status or "Draft"
			if status in APPROVED_STATUSES:
				approved += 1
			elif status not in REJECTED_STATUSES:
				pending += 1
			recent_requests.append(
				{
					"doctype": doctype,
					"name": row.name,
					"status": status,
					"modified": row.modified,
				}
			)

	# Calculate status totals across every request, not only the recent rows.
	status_totals = frappe._dict()
	for doctype in counts:
		for row in frappe.get_all(
			doctype,
			filters={"employee": employee.name},
			fields=["status", "count(name) as count"],
			group_by="status",
		):
			status = row.status or "Draft"
			status_totals[status] = status_totals.get(status, 0) + row.count

	approved = sum(status_totals.get(status, 0) for status in APPROVED_STATUSES)
	rejected = sum(status_totals.get(status, 0) for status in REJECTED_STATUSES)
	# Unsent drafts are not waiting on anyone, so they are not "pending".
	pending = max(total - approved - rejected - status_totals.get("Draft", 0), 0)

	recent_requests.sort(key=lambda row: row["modified"], reverse=True)
	recent_requests = recent_requests[:8]

	leave_applications = 0
	if frappe.db.exists("DocType", "Leave Application"):
		leave_applications = frappe.db.count("Leave Application", {"employee": employee.name})

	user = frappe.get_cached_doc("User", frappe.session.user)
	return {
		"status": "success",
		"leave_summary": dashboard_summary(employee.name),
		"leave_flow": leave_flow(employee.name),
		"user": {
			"full_name": user.full_name or user.first_name or employee.employee_name,
			"email": frappe.session.user,
		},
		"employee": employee,
		"stats": {
			"total": total,
			"pending": pending,
			"approved": approved,
			"leave_applications": leave_applications,
		},
		"counts": counts,
		"recent_requests": recent_requests,
	}
