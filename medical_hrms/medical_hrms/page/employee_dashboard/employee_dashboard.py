import frappe
from frappe import _
from medical_hrms.monthly_leave_policy import dashboard_summary


REQUEST_DOCTYPES = (
	"Permission Request",
	"Remote Work Request",
	"Leave Application",
	"Return from Leave Request",
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
	pending = max(total - approved - rejected, 0)

	recent_requests.sort(key=lambda row: row["modified"], reverse=True)
	recent_requests = recent_requests[:8]

	leave_applications = 0
	if frappe.db.exists("DocType", "Leave Application"):
		leave_applications = frappe.db.count("Leave Application", {"employee": employee.name})

	user = frappe.get_cached_doc("User", frappe.session.user)
	return {
		"status": "success",
		"leave_summary": dashboard_summary(employee.name),
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
