"""What happens to an employee request after it is sent (Round 2: HR-16, HR-25).

- Rejected needs a reason (rejection_reason); the employee sees it on the Employee Portal.
- Every status change is kept (track_changes) and shown to the employee as the request's history.
- Notifications - the bell on the portals, and an e-mail when the outgoing mail account works: HR when an
  employee sends a request; the employee when HR moves it to another step, approves or rejects it.
  Leave Application keeps HRMS's own e-mails (HR Settings > Leave Approval / Leave Status Notification Template).
- A rejected request can be sent again once, as a new request linked to it (resubmitted_from).
"""
import frappe
from frappe import _
from frappe.utils import get_fullname, get_url

from medical_hrms.employee_permissions import EMPLOYEE_REQUEST_DOCTYPES

REASON = "rejection_reason"
RESENT_FROM = "resubmitted_from"
HR_ROLES = ("HR User", "HR Manager")
# Request types with a Rejected step (fields in their own DocType JSON), and Leave Application (custom fields, setup below).
REJECTABLE = (
	"Permission Request", "Remote Work Request", "Leave Plan Request", "Salary Certificate Request",
	"Pre Approved Overtime Request", "Employee Training Request", "Children Medical Allowance Request",
	"Company Car Request", "Contract Renewal Request", "Leave Application",
)
# Contract Renewal is filed and followed by HR, so it sends nothing.
NOTIFIED = tuple(dt for dt in EMPLOYEE_REQUEST_DOCTYPES if dt != "Contract Renewal Request")


def setup():
	"""Leave Application (HRMS): the same rejection reason and resend link, and its status changes kept for the history."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	from frappe.custom.doctype.property_setter.property_setter import make_property_setter

	create_custom_fields({"Leave Application": [
		{"fieldname": REASON, "fieldtype": "Small Text", "label": "Rejection Reason", "insert_after": "status",
			"depends_on": "eval:doc.status=='Rejected'", "mandatory_depends_on": "eval:doc.status=='Rejected'",
			"description": "Required when you reject. The employee sees it on the Employee Portal.", "translatable": 0},
		{"fieldname": RESENT_FROM, "fieldtype": "Link", "options": "Leave Application", "label": "Sent Again From",
			"insert_after": REASON, "read_only": 1, "no_copy": 1, "depends_on": f"eval:doc.{RESENT_FROM}",
			"description": "The rejected application this one replaces."},
	]}, update=True)
	make_property_setter("Leave Application", None, "track_changes", 1, "Check", for_doctype=True, validate_fields_for_doctype=False)
	frappe.clear_cache(doctype="Leave Application")


# --------------------------------------------------------------------------- validation

def validate(doc, method=None):
	"""validate hook for REJECTABLE."""
	if doc.status == "Rejected" and not (doc.get(REASON) or "").strip():
		frappe.throw(_("Give the reason for the rejection in Rejection Reason. The employee sees it."), title=_("Rejection Reason Missing"))
	if doc.status != "Rejected" and doc.get(REASON) and doc.has_value_changed("status"):
		doc.set(REASON, None)  # set back from Rejected: the old reason no longer applies
	if doc.get(RESENT_FROM) and (doc.is_new() or doc.has_value_changed(RESENT_FROM)):
		check_resend(doc.doctype, doc.get(RESENT_FROM), doc.employee, doc.name)


def check_resend(doctype, original, employee, new_name=None):
	"""A request can only be sent again from the same employee's rejected request, and only once."""
	row = frappe.db.get_value(doctype, original, ["employee", "status"], as_dict=True)
	if not row or row.employee != employee or row.status != "Rejected":
		frappe.throw(_("Only a rejected request of the same employee can be sent again."), frappe.PermissionError)
	again = frappe.db.get_value(doctype, {RESENT_FROM: original, "name": ["!=", new_name or ""]}, "name")
	if again:
		frappe.throw(_("{0} was already sent again as {1}.").format(original, again))


# --------------------------------------------------------------------------- history

def history(doc):
	"""The request's steps for the employee, oldest first: [{status, on, by}]. The first step is when it was
	saved (as a draft, or sent); then every status change recorded by track_changes."""
	changes = []
	for version in frappe.get_all("Version", filters={"ref_doctype": doc.doctype, "docname": doc.name},
			fields=["owner", "creation", "data"], order_by="creation asc"):
		data = frappe.parse_json(version.data or "{}") or {}
		for field, old, new in data.get("changed") or []:
			if field == "status" and old != new:
				changes.append((old, new, version.creation, version.owner))
	first = changes[0][0] if changes else doc.status
	steps = [{"status": first, "on": doc.creation, "by": get_fullname(doc.owner)}]
	steps += [{"status": new, "on": on, "by": get_fullname(by)} for old, new, on, by in changes]
	return steps


def resent_as(doc):
	return frappe.db.get_value(doc.doctype, {RESENT_FROM: doc.name}, "name") if doc.meta.has_field(RESENT_FROM) else None


# --------------------------------------------------------------------------- notifications

def notify(doc, method=None):
	"""on_update hook for NOTIFIED: HR hears about a newly sent request, the employee about every later step."""
	if frappe.flags.in_import or frappe.flags.in_patch:
		return
	before = doc.get_doc_before_save()
	old = before.status if before else None
	if old == doc.status:
		return
	label, employee_name = _(doc.doctype), doc.get("employee_name") or doc.employee
	if doc.status.startswith("Pending") and old in (None, "Draft"):
		users = [u for u in hr_users() if u != frappe.session.user]
		send(users, doc, _("New {0} from {1} ({2})").format(label, employee_name, doc.name),
			_("{0} sent a {1}. Open it to review the next step.").format(employee_name, label), link=None)
		return
	if old in (None, "Draft"):
		return  # drafts are the employee's own business
	user = frappe.db.get_value("Employee", doc.employee, "user_id")
	if not user or user == frappe.session.user:
		return
	subject = _("Your {0} {1} is now {2}").format(label, doc.name, _(doc.status))
	body = _("Rejection reason: {0}").format(doc.get(REASON)) if doc.status == "Rejected" and doc.get(REASON) else subject
	send([user], doc, subject, body, link=portal_link(doc))


def send(users, doc, subject, body, link=None):
	"""Bell entries (Notification Log), e-mailed by Frappe when the user's notification settings allow it.
	Queued after the commit, so a save that is rolled back (an error later in the save, a test) notifies nobody."""
	if not users or frappe.flags.in_install or frappe.flags.in_migrate:
		return
	frappe.enqueue("frappe.desk.doctype.notification_log.notification_log.make_notification_logs", queue="short", enqueue_after_commit=True,
		users=sorted(set(users)), doc=frappe._dict({
			"type": "",  # "" = Default: e-mailed too (an Alert would only show in the bell)
			"document_type": doc.doctype, "document_name": doc.name, "subject": frappe.utils.escape_html(subject),
			"email_content": frappe.utils.escape_html(body), "from_user": frappe.session.user, "link": link,
		}))


def hr_users():
	users = set(frappe.get_all("Has Role", filters={"role": ["in", HR_ROLES], "parenttype": "User"}, pluck="parent")) - {"Administrator", "Guest"}
	return frappe.get_all("User", filters={"name": ["in", list(users)], "enabled": 1, "user_type": "System User"}, pluck="name") if users else []


def portal_link(doc):
	"""Opens the request's details on the Employee Portal (employee_dashboard.js reads these route options)."""
	from urllib.parse import urlencode
	return get_url("/app/employee-dashboard?" + urlencode({"request": doc.doctype, "name": doc.name}))
