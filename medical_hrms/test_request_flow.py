"""Round 2: drafts, rejection reasons, history, sending again and notifications (request_flow.py,
self_service.py), and linking an Employee on the Instructor form (staff_links.py). Each test rolls back.

	bench --site <site> run-tests --module medical_hrms.test_request_flow
"""
import unittest
from unittest.mock import patch

import frappe

from medical_hrms import self_service
from medical_hrms.request_flow import REASON, RESENT_FROM, validate
from medical_hrms.staff_links import FIELDS, matching_values

C = lambda category, code: f"{category}::{code}"
DT = "Salary Certificate Request"
DOM = "rchs-qa.test"


def make_user(email, roles):
	user = frappe.get_doc(dict(doctype="User", email=email, first_name=email.split("@")[0].replace(".", " ").title(),
		send_welcome_email=0, roles=[{"role": role} for role in roles])).insert(ignore_permissions=True)
	return user.name


def make_employee(user, first_name, identity="1099123471"):
	department = frappe.db.get_value("Department", {"company": "Medical College", "is_group": 0}, "name")
	return frappe.get_doc(dict(
		doctype="Employee", naming_series="HR-EMP-", first_name=first_name, last_name="Flow", status="Active", company="Medical College",
		department=department, branch=frappe.db.get_value("Branch", {}, "name"), date_of_birth="1985-03-14", date_of_joining="2022-09-01",
		gender=C("Gender", "1"), user_id=user,
		custom_jameah_nationality=C("Nationality", "101"), custom_identity_type=C("Identity type", "01"), custom_identity_number=identity,
		custom_ministry_work_city=C("Coding cities and governora", "0202000"), custom_ministry_job_rank=C("Job ranks", "01"),
	)).insert(ignore_permissions=True).name


@unittest.skipUnless(frappe.db and frappe.db.exists("Company", "Medical College"), "needs the Medical College company")
class TestRequestFlow(unittest.TestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)  # runs even when setUp fails
		self.addCleanup(frappe.set_user, "Administrator")
		frappe.set_user("Administrator")
		# Notifications are queued after the commit; run them straight away instead. Their e-mails are Frappe's job
		# (sending one now would commit the test data), so only the bell entries are checked here.
		run_now = lambda method, **kwargs: frappe.get_attr(method)(**{k: v for k, v in kwargs.items() if k not in ("enqueue_after_commit", "now", "queue")})
		for target, replacement in (("frappe.enqueue", run_now), ("frappe.desk.doctype.notification_log.notification_log.send_notification_email", None)):
			patcher = patch(target, replacement) if replacement else patch(target)
			patcher.start()
			self.addCleanup(patcher.stop)
		self.user = make_user(f"qa.flow.employee@{DOM}", ["Employee"])
		self.employee = make_employee(self.user, "Request")
		self.hr = make_user(f"qa.flow.hr@{DOM}", ["HR User"])

	def as_employee(self):
		frappe.set_user(self.user)

	def as_hr(self, doc, status, reason=None):
		frappe.set_user("Administrator")
		doc = frappe.get_doc(doc.doctype, doc.name)
		doc.status = status
		doc.set(REASON, reason)
		doc.save(ignore_version=False)  # tests skip versions by default; the history needs them
		return doc

	def send(self, **extra):
		self.as_employee()
		return self_service.save_request(DT, frappe.as_json({"purpose": "Bank Loan", "addressee": "QA Bank", **extra}), send=1)

	def bell(self, user):
		return frappe.get_all("Notification Log", filters={"for_user": user}, fields=["subject", "email_content", "link", "document_name"], order_by="creation desc")

	def test_rejecting_needs_a_reason(self):
		doc = frappe.get_doc(DT, self.send()["name"])
		self.assertRaises(frappe.ValidationError, self.as_hr, doc, "Rejected")
		doc = self.as_hr(doc, "Rejected", "Addressee missing")
		self.assertEqual(doc.get(REASON), "Addressee missing")
		doc = self.as_hr(doc, "Pending HR", doc.get(REASON))  # set back: the old reason no longer applies
		self.assertFalse(doc.get(REASON))

	def test_employee_cannot_write_the_reason(self):
		self.as_employee()
		doc = frappe.get_doc({"doctype": DT, "employee": self.employee, "purpose": "Bank Loan", "status": "Draft", REASON: "self-made"})
		self.assertRaises(frappe.PermissionError, doc.insert)

	def test_draft_change_send_and_delete(self):
		self.as_employee()
		name = self_service.save_request(DT, frappe.as_json({"purpose": "Bank Loan", "addressee": "First"}), send=0)["name"]
		self_service.save_request(DT, frappe.as_json({"purpose": "Visa Application", "addressee": "Second"}), send=0, name=name)
		doc = frappe.get_doc(DT, name)
		self.assertEqual((doc.status, doc.purpose, doc.addressee), ("Draft", "Visa Application", "Second"))
		self.assertTrue(self_service.request_details(DT, name)["can_edit"])
		self.assertTrue(self_service.save_request(DT, frappe.as_json({"purpose": "Visa Application", "addressee": "Second"}), send=1, name=name)["status"].startswith("Pending"))
		self.assertRaises(frappe.PermissionError, self_service.save_request, DT, frappe.as_json({"purpose": "Bank Loan"}), 0, None, name)
		self.assertRaises(frappe.PermissionError, self_service.delete_draft, DT, name)
		draft = self_service.save_request(DT, frappe.as_json({"purpose": "Bank Loan"}), send=0)["name"]
		self_service.delete_draft(DT, draft)
		self.assertFalse(frappe.db.exists(DT, draft))

	def test_send_again_once_with_history(self):
		original = frappe.get_doc(DT, self.send()["name"])
		self.as_hr(original, "Rejected", "Wrong addressee")
		self.as_employee()
		details = self_service.request_details(DT, original.name)
		self.assertEqual((details["rejection_reason"], details["can_resend"], details["values"]["addressee"]), ("Wrong addressee", True, "QA Bank"))
		self.assertEqual([step["status"] for step in details["history"]], ["Pending Manager", "Rejected"])
		again = self_service.save_request(DT, frappe.as_json({"purpose": "Bank Loan", "addressee": "QA Bank Riyadh"}), send=1, resend_of=original.name)["name"]
		self.assertEqual(frappe.db.get_value(DT, again, RESENT_FROM), original.name)
		self.assertRaises(frappe.ValidationError, self_service.save_request, DT, frappe.as_json({"purpose": "Bank Loan"}), 1, None, None, original.name)
		details = self_service.request_details(DT, original.name)
		self.assertEqual((details["resent_as"], details["can_resend"]), (again, False))
		self.assertEqual(self_service.request_details(DT, again)["resubmitted_from"], original.name)

	def test_only_own_rejected_requests_can_be_sent_again(self):
		pending = self.send()["name"]
		self.assertRaises(frappe.PermissionError, self_service.save_request, DT, frappe.as_json({"purpose": "Bank Loan"}), 1, None, None, pending)
		frappe.set_user("Administrator")
		other = make_employee(make_user(f"qa.flow.other@{DOM}", ["Employee"]), "Other", identity="1099123489")
		theirs = frappe.get_doc({"doctype": DT, "employee": other, "purpose": "Bank Loan", "status": "Rejected", REASON: "No"}).insert(ignore_permissions=True)
		self.as_employee()
		self.assertRaises(frappe.PermissionError, self_service.save_request, DT, frappe.as_json({"purpose": "Bank Loan"}), 1, None, None, theirs.name)
		self.assertRaises(frappe.PermissionError, self_service.request_details, DT, theirs.name)

	def test_notifications(self):
		name = self.send()["name"]
		self.assertTrue(any(n.document_name == name and "Request Flow" in n.subject for n in self.bell(self.hr)), self.bell(self.hr))
		doc = frappe.get_doc(DT, name)
		self.assertFalse(self.bell(self.user))  # nothing for the employee's own sending
		self.as_hr(doc, "Pending HR")
		self.as_hr(doc, "Rejected", "Addressee missing")
		mine = [n for n in self.bell(self.user) if n.document_name == name]
		self.assertEqual(len(mine), 2)
		self.assertIn("Addressee missing", mine[0].email_content)
		self.assertIn("/app/employee-dashboard?request=Salary+Certificate+Request&name=", mine[0].link)

	def test_drafts_send_nothing(self):
		self.as_employee()
		self_service.save_request(DT, frappe.as_json({"purpose": "Bank Loan"}), send=0)
		self.assertFalse([n for n in self.bell(self.hr)])

	def test_leave_application_needs_a_reason_too(self):
		meta = frappe.get_meta("Leave Application")
		self.assertTrue(meta.has_field(REASON) and meta.has_field(RESENT_FROM) and meta.track_changes)
		doc = frappe.get_doc({"doctype": "Leave Application", "employee": self.employee, "status": "Rejected"})
		self.assertRaises(frappe.ValidationError, validate, doc)


class TestInstructorEmployeeLink(unittest.TestCase):
	"""B-26: picking an Employee on the Instructor form no longer copies values the form's own lists do not have."""

	def setUp(self):
		self.addCleanup(frappe.db.rollback)
		frappe.set_user("Administrator")

	def test_copies_switched_off(self):
		for doctype, fields in FIELDS.items():
			if not frappe.db.exists("DocType", doctype):
				continue
			for field in fields:
				self.assertFalse(frappe.get_meta(doctype).get_field(field).fetch_from, (doctype, field))

	def test_linking_an_employee_saves_with_matching_values(self):
		employee = frappe.db.get_value("Employee", {"gender": ["like", "Gender::%"], "department": ["is", "set"]}, ["name", "department"], as_dict=True)
		instructor = frappe.db.get_value("Instructor", {"employee": ["is", "not set"]}, "name")
		if not (employee and instructor):
			self.skipTest("needs an Employee with a Ministry gender and an Instructor without an Employee")
		frappe.db.set_value("Instructor", {"employee": employee.name}, "employee", None)  # free the employee (rolled back)
		doc = frappe.get_doc("Instructor", instructor)
		doc.employee, doc.gender, doc.department = employee.name, None, None
		doc.save()
		expected = matching_values("Instructor", employee.name)
		self.assertEqual(doc.gender, expected.get("gender"))
		self.assertEqual(doc.department, expected.get("department"))
		self.assertTrue(frappe.db.exists("Gender Edu", doc.gender))
