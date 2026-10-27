"""QA logins and employees for the browser tests (domain rchs-qa.test; removed by qa_cleanup.py)."""
import os as _os
# Creates / deletes test logins with known passwords: only on a site named explicitly as a test site.
if _os.environ.get("QA_TEST_SITE") != frappe.local.site:
	raise SystemExit(f"Refusing to run on {frappe.local.site}: set QA_TEST_SITE={frappe.local.site} if this is a test site (never production).")

import json
import os
from frappe.desk.doctype.notification_settings.notification_settings import create_notification_settings
from frappe.utils.password import update_password

PW = "QaTest#2026!"
DOM = "rchs-qa.test"
USERS = {
	f"qa.hr.manager@{DOM}": ("QA HR Manager", ["HR Manager", "HR User", "Employee"]),
	f"qa.hr.user@{DOM}": ("QA HR User", ["HR User"]),
	f"qa.emp1@{DOM}": ("QA Employee One", ["Employee"]),
	f"qa.emp2@{DOM}": ("QA Employee Two", ["Employee"]),
	f"qa.unlinked@{DOM}": ("QA Unlinked", ["Employee"]),
	f"qa.outsider@{DOM}": ("QA Outsider", ["Academics User"] if frappe.db.exists("Role", "Academics User") else []),
	# edits Instructor records and reads Employees: links an Employee on the Instructor form (B-26)
	f"qa.academic.admin@{DOM}": ("QA Academic Admin", ["Education Manager", "HR User"]),
	# Round 3 (HR-11), the My HR card on the staff dashboards: a head of department and a dean with an Employee record,
	# and an instructor login without one (no card)
	f"qa.hod@{DOM}": ("QA Head Nursing", ["Head of Nursing Department", "Instructor", "Employee"]),
	f"qa.dean@{DOM}": ("QA Dean", ["Dean", "Employee"]),
	f"qa.staff.nolink@{DOM}": ("QA Staff Nolink", ["Instructor"]),
}
for email, (full, roles) in USERS.items():
	if not frappe.db.exists("User", email):
		first, _, last = full.partition(" ")
		frappe.get_doc({"doctype": "User", "email": email, "first_name": first, "last_name": last,
			"send_welcome_email": 0, "user_type": "System User", "enabled": 1}).insert(ignore_permissions=True)
	u = frappe.get_doc("User", email)
	u.set("roles", [])
	for r in roles:
		u.append("roles", {"role": r})
	u.save(ignore_permissions=True)
	update_password(email, PW)
	# Notifications show in the bell only: this copy cannot send e-mail (B-25), so do not queue any for test logins.
	create_notification_settings(email)
	frappe.db.set_value("Notification Settings", email, "enable_email_notifications", 0)

C = lambda cat, code: f"{cat}::{code}"
out = {}
for key, last, idno in (("emp1", "One", "1099000001"), ("emp2", "Two", "1099000002"), ("hod", "Head", "1099000004"), ("dean", "Dean", "1099000005")):
	email = f"qa.{key}@{DOM}"
	name = frappe.db.get_value("Employee", {"user_id": email})
	if not name:
		e = frappe.get_doc(dict(doctype="Employee", naming_series="HR-EMP-", first_name="QA Employee", last_name=last, status="Active",
			company="Medical College", department="Internal Medicine - MC", branch="Main Riyadh Campus Branch", designation="Assistant Professor",
			date_of_birth="1988-05-12", date_of_joining="2024-01-01", gender=C("Gender", "1"), holiday_list="Medical HRMS Demo Weekends 2026-2027",
			custom_jameah_nationality=C("Nationality", "101"), custom_identity_type=C("Identity type", "01"), custom_identity_number=idno,
			custom_ministry_work_city=C("Coding cities and governora", "0202000"), custom_ministry_job_rank=C("Job ranks", "01"),
			leave_approver=f"qa.hr.manager@{DOM}", user_id=email))
		e.insert(ignore_permissions=True)
		name = e.name
	out[key] = name
	if not frappe.db.exists("Leave Allocation", {"employee": name, "leave_type": "Annual Leave", "docstatus": 1}):
		la = frappe.get_doc({"doctype": "Leave Allocation", "employee": name, "leave_type": "Annual Leave",
			"from_date": "2026-01-01", "to_date": "2026-12-31", "new_leaves_allocated": 21})
		la.insert(ignore_permissions=True)
		la.submit()
out["password"] = PW
out["users"] = list(USERS)
print(json.dumps(out))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "qa_fixture_state.json"), "w").write(json.dumps(out))
