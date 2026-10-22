"""Remove QA test data. QA_CLEAN=all also removes the QA users, employees and allocations.

Safety: every lookup is keyed on a non-empty list of QA identifiers; an empty
list returns nothing (never `in [""]`, which matches empty-string columns).
KEEP: logins that stay for the user (the test instructor).
"""
import os as _os
# Creates / deletes test logins with known passwords: only on a site named explicitly as a test site.
if _os.environ.get("QA_TEST_SITE") != frappe.local.site:
	raise SystemExit(f"Refusing to run on {frappe.local.site}: set QA_TEST_SITE={frappe.local.site} if this is a test site (never production).")

import os

from frappe.model import delete_doc as _delete_doc

# Frappe removes a deleted document's shares, versions and comments in a background job after commit.
# Run it now instead: run later, it removes the self-share of a QA user that qa_fixtures creates again
# straight after (that user then cannot open their own My Settings / profile).
_enqueue = frappe.enqueue


def _enqueue_now(method, **kwargs):
	if method == "frappe.model.delete_doc.delete_dynamic_links":
		return _delete_doc.delete_dynamic_links(kwargs["doctype"], kwargs["name"])
	return _enqueue(method, **kwargs)


frappe.enqueue = _enqueue_now

DOM = "rchs-qa.test"
ALL = os.environ.get("QA_CLEAN") == "all"
KEEP = {f"qa.instructor@{DOM}"}
removed = {}


def names(doctype, field, values, **extra):
	values = [v for v in values if v]
	if not values:
		return []
	return frappe.get_all(doctype, filters={field: ["in", values], **extra}, pluck="name")


def drop(doctype, docnames):
	for n in docnames:
		if not frappe.db.exists(doctype, n):
			continue  # already removed with its parent / linked record
		d = frappe.get_doc(doctype, n)
		if d.docstatus == 1:
			d.flags.ignore_permissions = True
			d.cancel()
		frappe.delete_doc(doctype, n, force=True, ignore_permissions=True, delete_permanently=True)
		removed[doctype] = removed.get(doctype, 0) + 1


qa_users = [u for u in frappe.get_all("User", filters={"name": ["like", f"%@{DOM}"]}, pluck="name") if u not in KEEP]
qa_emps = names("Employee", "user_id", qa_users)
applicants = frappe.get_all("Employee Job Applicant", filters={"email_id": ["like", f"%@{DOM}"]}, pluck="name")
hired = names("Employee", "custom_job_applicant", applicants)
emps = list(dict.fromkeys(qa_emps + hired))
for e in emps:
	d = frappe.db.get_value("Employee", e, ["user_id", "custom_job_applicant"], as_dict=True)
	assert (d.user_id or "").endswith("@" + DOM) or d.custom_job_applicant in applicants, f"refusing to touch {e}"

for dt in ("Leave Return Request", "Permission Request", "Remote Work Request", "Leave Plan Request", "Salary Certificate Request",
		"Pre Approved Overtime Request", "Employee Training Request", "Children Medical Allowance Request",
		"Company Car Request", "Contract Renewal Request", "Employee Data Update Request", "Employee Medical License"):
	drop(dt, names(dt, "employee", emps))
drop("Leave Application", names("Leave Application", "employee", emps))
for n in names("Leave Ledger Entry", "employee", emps, transaction_type="Leave Application"):
	frappe.db.delete("Leave Ledger Entry", {"name": n})
drop("Job Application Link", names("Job Application Link", "owner", qa_users))
hired_users = [u for u in frappe.get_all("Employee", filters={"name": ["in", hired]}, pluck="user_id") if u] if hired else []
drop("Instructor", names("Instructor", "employee", hired))
drop("Academic Advisor", names("Academic Advisor", "employee", hired))
drop("Employee", hired)
drop("Employee Job Applicant", applicants)
drop("File", names("File", "owner", qa_users))
if ALL:
	for n in names("Leave Ledger Entry", "employee", qa_emps):
		frappe.db.delete("Leave Ledger Entry", {"name": n})
	for n in names("Leave Allocation", "employee", qa_emps):
		frappe.db.delete("Leave Allocation", {"name": n})
	for e in qa_emps:
		if frappe.db.exists("Employee", e):
			frappe.db.set_value("Employee", e, "user_id", None, update_modified=False)
	drop("Employee", qa_emps)
# academic QA hires get a college login (qa.<x>.staff@alriyada.edu.sa), only taken from hired QA applicants
qa_login = lambda u: u.endswith("@" + DOM) or (u.startswith("qa.") and u.endswith(".staff@alriyada.edu.sa") and u in hired_users)
for u in set(hired_users + (qa_users if ALL else [])):
	assert qa_login(u) and u not in KEEP, f"refusing to delete user {u}"
	if frappe.db.exists("User", u):
		frappe.delete_doc("User", u, force=True, ignore_permissions=True, delete_permanently=True)
		removed["User"] = removed.get("User", 0) + 1
print("removed:", removed)
