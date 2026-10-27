"""Every whitelisted server method of the app, called over HTTP as a logged-out visitor, an employee and an
HR User: HR-only methods must refuse employees and visitors, login-only methods must refuse visitors, and
nothing may answer with a server error (500). Test sites only: needs the QA logins (qa_fixtures.py) and a
running bench. Creates two Draft requests for the QA employee (removed by qa_cleanup.py).

    python3 tests/checks/api_methods.py
"""
import json, os, sys
import requests
BASE = os.environ.get("QA_BASE", "http://127.0.0.1:8000")
PW = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "e2e", "qa_fixture_state.json")))["password"]
M = "medical_hrms."
HR_ONLY = {
 "employee_data_sheet.export_sheet": {}, "employee_data_sheet.import_sheet": {"file": "/private/files/none.xlsx", "commit": 0},
 "jameah.status.get_status": {}, "jameah.status.employee_view_rows": {"employee": "HR-EMP-00005"}, "jameah.summary.refresh_now": None,
 "medical_hrms.page.hr_academic_presence.hr_academic_presence.get_faculty_schedule": {"from_date": "2026-10-18", "to_date": "2026-10-22"},
 "medical_hrms.page.hr_academic_presence.hr_academic_presence.get_proctor_schedule": {"from_date": "2026-10-18", "to_date": "2026-10-22"},
 "medical_hrms.page.hr_academic_presence.hr_academic_presence.get_students_presence": {"on_date": "2026-10-21"},
 "medical_hrms.page.hr_academic_presence.hr_academic_presence.get_faculty_after_hours": {"from_date": "2026-10-18", "to_date": "2026-10-22"},
 "medical_hrms.page.hr_dashboard.hr_dashboard.get_logged_in_user_details": {}, "medical_hrms.page.hr_dashboard.hr_dashboard.get_hr_dashboard_stats": {},
 "medical_hrms.page.hr_dashboard.hr_dashboard.get_hr_doctype_counts": {}, "medical_hrms.page.hr_dashboard.hr_dashboard.get_leave_overview": {},
 "medical_hrms.recruitment.job_application.accept_application": {"job_applicant": "APP-NONE"},
 "medical_hrms.recruitment.job_application.reject_application": {"job_applicant": "APP-NONE"},
 "medical_hrms.recruitment.job_application.create_employee_from_applicant": {"job_applicant": "APP-NONE"},
 "medical_leave.activate_year": {"employee": "HR-EMP-NONE", "first_sick_date": "2026-10-01"},
 "medical_hrms.doctype.job_application_link.job_application_link.get_hireable_roles": {},
 "staff_links.values_from_employee": {"doctype": "Instructor", "employee": "HR-EMP-NONE"},
}
EMPLOYEE = {
 "medical_hrms.page.employee_dashboard.employee_dashboard.get_dashboard_data": {},
 "medical_hrms.doctype.employee_data_update_request.employee_data_update_request.create_my_request": {"update_type": "Address", "new_value": "QA api sweep", "send": 0},
 "self_service.form_schema": {"doctype": "Permission Request"}, "self_service.my_leave_types": {},
 "self_service.leave_return_context": {"leave_application": "HR-LAP-NONE"},
 "self_service.save_request": {"doctype": "Salary Certificate Request", "values": json.dumps({"purpose": "QA api sweep", "addressee": "QA"}), "send": 0},
 "self_service.my_requests": {"doctype": "Permission Request"}, "self_service.request_details": {"doctype": "Permission Request", "name": "NONE"},
 "self_service.delete_draft": {"doctype": "Salary Certificate Request", "name": "NONE"},
 "ministry_lookup_query.get_ministry_codes": {"doctype": "Jameah Ministry Code", "txt": "", "searchfield": "name", "start": 0, "page_len": 5, "filters": json.dumps({"code_category": "Gender"})},
}
GUEST = {"medical_hrms.recruitment.job_application.submit_application": {"data": "{}", "token": "nope"},
	"medical_hrms.recruitment.receipt.download_receipt": {"name": "APP-NONE", "key": "bad"}}
# Every whitelisted method in the code must be listed above, so a new one cannot go untested.
import ast, pathlib
APP = pathlib.Path(__file__).resolve().parents[2]
found = set()
for path in (APP / "medical_hrms").rglob("*.py"):
	try:
		tree = ast.parse(path.read_text(encoding="utf-8"))
	except SyntaxError:
		continue
	module = ".".join(path.relative_to(APP).with_suffix("").parts)
	for node in tree.body:
		if isinstance(node, ast.FunctionDef) and any("whitelist" in ast.unparse(d) for d in node.decorator_list):
			found.add(f"{module}.{node.name}"[len(M):])
unlisted = sorted(found - set(HR_ONLY) - set(EMPLOYEE) - set(GUEST))


def session(user):
	s = requests.Session()
	if user:
		r = s.post(BASE + "/api/method/login", data={"usr": user, "pwd": PW}); assert r.ok, (user, r.status_code)
	return s
def call(s, m, args):
	r = s.post(f"{BASE}/api/method/{M}{m}", data=args or {})
	try: msg = r.json()
	except Exception: msg = {}
	exc = (msg.get("exc_type") or "")
	text = ""
	if msg.get("_server_messages"):
		try: text = json.loads(json.loads(msg["_server_messages"])[0]).get("message", "")[:90]
		except Exception: pass
	return r.status_code, exc, text
bugs = []
for who, user in (("guest", None), ("employee", "qa.emp1@rchs-qa.test"), ("hr.user", "qa.hr.user@rchs-qa.test")):
	s = session(user)
	print(f"\n===== as {who}")
	for group, methods in (("HR-only", HR_ONLY), ("employee", EMPLOYEE), ("public", GUEST)):
		for m, args in methods.items():
			if args is None and who == "hr.user": continue
			st, exc, text = call(s, m, args or {})
			expect_refused = (who == "guest" and group != "public") or (who == "employee" and group == "HR-only")
			verdict = "ok"
			if st >= 500: verdict = "BUG 500"
			elif expect_refused and st == 200: verdict = "BUG not refused"
			elif expect_refused and st not in (401, 403): verdict = f"check ({st})"
			if verdict != "ok": bugs.append(f"{who}: {m} -> {st} {exc} {text}")
			print(f"{verdict:16} {st} {exc:22} {m.split('.')[-1]:32} {text}")
bugs += [f"not covered by this check (add it to HR_ONLY, EMPLOYEE or GUEST): {m}" for m in unlisted]
print(f"\n{len(found)} whitelisted methods in the code; TO REVIEW:", len(bugs)); print("\n".join(bugs))


def _record(ok):
	"""Result for the Test Cases workbook (tests/checks/record.py)."""
	import importlib.util
	spec = importlib.util.spec_from_file_location("checks_record", os.path.join(os.path.dirname(os.path.abspath(__file__)), "record.py"))
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	module.record_from(__file__, ok)


_record(not bugs)
sys.exit(1 if bugs else 0)
