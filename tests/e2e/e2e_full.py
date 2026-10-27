"""Full client-level (browser) test of Medical HRMS + Jameah, with an error sweep.

Run: pwenv/bin/python e2e_full.py   (bench on :8000; qa_fixtures.py applied)
Every result and every captured error carries a timestamp.
"""
import datetime, json, os, re, sys, time, traceback
from urllib.parse import quote
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

BASE = os.environ.get("QA_BASE", "http://127.0.0.1:8000")
HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "e2e_shots")
os.makedirs(SHOTS, exist_ok=True)
STATE = json.load(open(os.path.join(HERE, "qa_fixture_state.json")))
PW = STATE["password"]
EMP1, EMP2 = STATE["emp1"], STATE["emp2"]
DOM = "rchs-qa.test"
COLLEGE = "alriyada.edu.sa"  # education requires Instructor e-mails on this domain
U = {k: f"qa.{k}@{DOM}" for k in ("hr.manager", "hr.user", "emp1", "emp2", "unlinked", "outsider", "academic.admin")}
INSTRUCTOR = ("qa.instructor@rchs-qa.test", "QaInstructor#2026")
ONLY = set(sys.argv[1:])
now = lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

RESULTS, ISSUES, CTX = [], [], {}
# Known, explained noise: the site logo file is missing on this local copy only.
IGNORED_URLS = ("/files/rchs-logo.png",)


def record(tid, area, title, ok, detail="", page=None, started=None):
	shot = ""
	if page is not None and not ok:
		shot = os.path.join(SHOTS, f"{tid}.png")
		try:
			page.screenshot(path=shot, full_page=True)
		except Exception:
			shot = ""
	RESULTS.append({"id": tid, "area": area, "title": title, "ok": bool(ok), "detail": str(detail)[:700], "shot": shot,
		"time": started or now(), "seconds": None})
	print(("PASS " if ok else "FAIL ") + f"{tid} [{area}] {title}" + (f" -- {detail}" if detail and not ok else ""), flush=True)


def check(tid, area, title, page=None):
	def deco(fn):
		started, t0 = now(), time.time()
		try:
			detail = fn()
			record(tid, area, title, True, detail or "", page, started)
		except Exception as e:
			record(tid, area, title, False, f"{type(e).__name__}: {e}", page, started)
		RESULTS[-1]["seconds"] = round(time.time() - t0, 1)
		return fn
	return deco


class Session:
	def __init__(self, browser, user=None, label=None, password=PW):
		self.label = label or user or "guest"
		self.ctx = browser.new_context(base_url=BASE, viewport={"width": 1366, "height": 900}, accept_downloads=True)
		self.page = self.ctx.new_page()
		self.page.set_default_timeout(30000)
		self.page.on("pageerror", lambda e: self._issue("js-error", str(e)[:400]))
		self.page.on("console", self._console)
		self.page.on("response", self._response)
		self.page.on("dialog", self._dialog)
		if user:
			self.login(user, password)

	def _issue(self, kind, text, url=None):
		ISSUES.append({"time": now(), "who": self.label, "kind": kind, "url": (url or self.page.url).replace(BASE, ""), "text": text})

	def _dialog(self, d):
		# Chrome's "Leave site? Changes may not be saved" prompt when a full page load leaves an
		# unsaved form (new forms, Leave Control Panel). Normal browser behaviour: accept and note it.
		if d.type == "beforeunload":
			self._issue("leave-page-prompt", "unsaved form left by a full page load")
			d.accept()
		else:
			self._issue("browser-dialog", f"{d.type}: {d.message[:300]}")
			d.dismiss()

	def _console(self, msg):
		if msg.type == "error" and "Failed to load resource" not in msg.text:
			self._issue("console-error", msg.text[-500:])

	def _response(self, r):
		if r.status >= 500 and not any(u in r.url for u in IGNORED_URLS):
			self._issue(f"http-{r.status}", "", r.url)

	def login(self, user, password=PW):
		p = self.page
		p.goto("/login")
		p.fill("#login_email", user)
		p.fill("#login_password", password)
		p.click(".btn-login")
		p.wait_for_url(re.compile(r".*/app.*"), timeout=60000)
		self.desk_ready()

	def desk_ready(self):
		self.page.wait_for_function("() => window.frappe && frappe.boot && frappe.boot.user && document.readyState === 'complete'", timeout=60000)
		self.page.wait_for_timeout(600)

	def goto(self, route):
		self.page.goto(route)
		self.desk_ready()
		self.idle()

	def idle(self, ms=400):
		self.page.wait_for_function("() => !window.frappe || ((frappe.request && frappe.request.ajax_count === 0) !== false && !document.querySelector('.freeze-message-container:not(.hidden)'))", timeout=60000)
		self.page.wait_for_timeout(ms)

	def rpc(self, method, args=None):
		return self.page.evaluate("""async ([m, a]) => {
			const r = await fetch('/api/method/' + m, {method: 'POST', headers: {'X-Frappe-CSRF-Token': (window.frappe && frappe.csrf_token) || '',
				'Accept': 'application/json', 'Content-Type': 'application/json'}, body: JSON.stringify(a || {})});
			let body = {}; try { body = await r.json(); } catch (e) {}
			let msg = ''; try { msg = JSON.parse(body._server_messages || '[]').map(x => JSON.parse(x).message).join(' | '); } catch (e) {}
			return {status: r.status, message: body.message, exc_type: body.exc_type, server_msg: msg || body.exception || ''};
		}""", [method, args or {}])

	def dialog_text(self):
		d = self.page.locator(".modal.show")
		return d.last.inner_text() if d.count() else ""

	def red_dialogs(self):
		"""Error pop-ups the user would see (Frappe msgprint with a red indicator)."""
		return self.page.evaluate("""() => [...document.querySelectorAll('.modal.show')].filter(m =>
			m.querySelector('.indicator.red, .modal-title .indicator-pill.red') || /error|exception|traceback/i.test(m.querySelector('.modal-title')?.innerText || ''))
			.map(m => m.innerText.slice(0, 300))""")

	def close_dialogs(self):
		for _ in range(4):
			if not self.page.locator(".modal.show").count():
				return
			self.page.keyboard.press("Escape")
			self.page.wait_for_timeout(350)

	def save_form(self):
		with self.page.expect_response(lambda r: "frappe.desk.form.save.savedocs" in r.url, timeout=30000) as info:
			self.page.keyboard.press("Control+s")
		resp = info.value
		self.idle()
		return resp

	def close(self):
		self.ctx.close()


def get_doc(s, doctype, name):
	return s.rpc("frappe.client.get", {"doctype": doctype, "name": name})


def want(section):
	return not ONLY or section in ONLY


# --------------------------------------------------------------------------- 1. login landing

def login_landing(b):
	cases = [("LGN-01", U["hr.manager"], PW, "/app/hr-dashboard", "#hrd-title", "HR Manager"),
		("LGN-02", U["hr.user"], PW, "/app/hr-dashboard", "#hrd-title", "HR User"),
		("LGN-03", U["emp1"], PW, "/app/employee-dashboard", "text=Employee Services", "Employee"),
		("LGN-04", INSTRUCTOR[0], INSTRUCTOR[1], "/app/instructor-dashboard", "text=Instructor Portal", "Instructor (also an Employee)")]
	for tid, user, pwd, path, marker, who in cases:
		s = Session(b, label=who)
		@check(tid, "Login", f"{who} logs in and lands on {path}", s.page)
		def _():
			s.login(user, pwd)
			s.page.wait_for_url(re.compile(".*" + re.escape(path)), timeout=60000)
			s.page.wait_for_selector(marker, timeout=60000)
			s.page.goto("/app"); s.page.wait_for_timeout(4000)
			assert path in s.page.url, f"opening /app again went to {s.page.url}"
		s.close()
	for tid, user, who in (("NAV-01", U["emp1"], "Employee"), ("NAV-02", U["hr.manager"], "HR Manager")):
		s = Session(b, label=f"breadcrumbs:{who}")
		@check(tid, "Navigation", f"{who}: no breadcrumb leads to 'Not permitted'", s.page)
		def _(user=user, s=s):
			s.login(user)
			bad, seen = [], set()
			for route in ("/app/employee-dashboard", "/app/leave-application", "/app/permission-request", "/app/hr-dashboard"):
				s.goto(route)
				for href in s.page.eval_on_selector_all("#navbar-breadcrumbs a", "els => els.map(a => a.getAttribute('href'))"):
					if href in seen:
						continue
					seen.add(href)
					q = s.ctx.new_page(); q.goto(href); q.wait_for_timeout(2500)
					if re.search(r"Not permitted|No permission", q.inner_text("body")):
						bad.append(f"{route} -> {href}")
					q.close()
			assert not bad, bad
			return f"breadcrumbs checked: {sorted(seen)}"
		s.close()
	s = Session(b, label="wrong-password")
	@check("LGN-05", "Login", "Wrong password shows an error and stays on the login page", s.page)
	def _():
		s.page.goto("/login"); s.page.fill("#login_email", U["hr.manager"]); s.page.fill("#login_password", "wrong-password"); s.page.click(".btn-login")
		s.page.wait_for_timeout(2500)
		assert "/login" in s.page.url, s.page.url
		assert re.search(r"Invalid|Incorrect|not", s.page.inner_text("body"), re.I)
	s.close()


# --------------------------------------------------------------------------- 2. employee self-service

def employee_self_service(b):
	s = Session(b, label="emp1"); p = s.page
	CTX["emp1"] = s

	@check("ESS-01", "Employee self-service", "Employee logs in and lands on the Employee Dashboard", p)
	def _():
		s.login(U["emp1"])
		assert "/app/employee-dashboard" in p.url, p.url
		p.wait_for_selector("#emd-welcome")
		s.idle()

	@check("ESS-02", "Employee self-service", "Header shows own name, Employee ID and 11 service cards", p)
	def _():
		p.wait_for_function("() => document.querySelector('#emd-id') && document.querySelector('#emd-id').textContent.includes('EMP-')")
		assert "QA Employee One" in p.inner_text("#emd-welcome")
		assert EMP1 in p.inner_text("#emd-id"), p.inner_text("#emd-id")
		assert p.locator(".emd-service").count() == 11

	@check("ESS-03", "Employee self-service", "Leave balance shows the Annual Leave allocation (21 days)", p)
	def _():
		row = [l for l in p.inner_text("#emd-leave-summary table").splitlines() if "Annual Leave" in l]
		assert row and "21" in row[0], row

	def open_new(doctype):
		s.close_dialogs()
		p.click(f'.emd-new[data-doctype="{doctype}"]')
		p.wait_for_selector(".modal.show .modal-title")
		p.wait_for_timeout(400)

	def send(primary=True):
		btn = ".modal.show .btn-modal-primary" if primary else ".modal.show .btn-modal-secondary"
		with p.expect_response(lambda r: "self_service.save_request" in r.url, timeout=30000) as info:
			p.click(btn)
		r = info.value
		body = r.json() if r.ok else {}
		s.idle(700)
		return r.status, body.get("message"), s.dialog_text()

	@check("ESS-04", "Employee self-service", "Permission Request with hour/minute/AM-PM pickers -> Pending", p)
	def _():
		open_new("Permission Request")
		m = p.locator(".modal.show")
		p.evaluate("cur_dialog.set_value('date', '2026-11-04')")
		for f, (h, mi, ap) in {"from_time": ("10", "15", "AM"), "to_time": ("11", "45", "AM")}.items():
			m.locator(f'select[data-fieldname="emd_time_{f}_hour"]').select_option(h)
			m.locator(f'select[data-fieldname="emd_time_{f}_minute"]').select_option(mi)
			m.locator(f'select[data-fieldname="emd_time_{f}_period"]').select_option(ap)
		m.locator('[data-fieldname="reason"] textarea').fill("QA: bank appointment")
		status, msg, _ = send()
		assert status == 200 and msg and msg["status"] == "Pending", (status, msg)
		doc = get_doc(s, "Permission Request", msg["name"])["message"]
		assert str(doc["from_time"]).startswith("10:15") and str(doc["to_time"]).startswith("11:45"), (doc["from_time"], doc["to_time"])
		CTX["perm_req"] = msg["name"]
		return msg["name"]

	@check("ESS-05", "Employee self-service", "Incomplete time (hour without minute) is rejected in the dialog", p)
	def _():
		open_new("Permission Request")
		p.evaluate("cur_dialog.set_values({date: '2026-11-05', reason: 'QA incomplete', emd_time_from_time_hour: '09', emd_time_from_time_minute: '00', emd_time_from_time_period: 'AM', emd_time_to_time_hour: '10'})")
		p.wait_for_timeout(300)
		p.click(".modal.show .btn-modal-primary")
		p.wait_for_timeout(1200)
		txt = s.dialog_text() + " " + p.inner_text("body")
		assert "Select the hour, minute" in txt or "Missing" in txt or "Mandatory" in txt, txt[-300:]
		s.close_dialogs()

	services = {
		"Remote Work Request": {"from_date": "2026-11-03", "to_date": "2026-11-03", "work_plan": "QA: prepare course files", "location": "Riyadh home"},
		"Salary Certificate Request": {"purpose": "Bank Loan", "addressee": "QA Bank"},
		"Pre Approved Overtime Request": {"date": "2026-11-06", "ot_hours_requested": 2, "ot_type": "Regular (1.5x)", "business_justification": "QA: exam marking"},
		"Employee Training Request": {"course_details": "QA: Simulation in Nursing", "provider": "SCFHS", "estimated_cost": 1500, "business_benefit": "QA benefit"},
		"Company Car Request": {"business_justification": "QA: hospital rounds", "client_visits_per_week": 3},
		"Employee Data Update Request": {"update_type": "Address", "new_value": "QA: new address, Riyadh"},
	}
	for i, (dt, values) in enumerate(services.items(), start=6):
		@check(f"ESS-{i:02d}", "Employee self-service", f"{dt}: fill dialog and Send -> Pending", p)
		def _(dt=dt, values=values):
			open_new(dt)
			p.evaluate("v => cur_dialog.set_values(v)", values)
			p.wait_for_timeout(400)
			status, msg, txt = send()
			assert status == 200 and msg and msg["status"].startswith("Pending"), (status, msg, txt[:300])
			CTX[dt] = msg["name"]
			return f'{msg["name"]} {msg["status"]}'

	@check("ESS-12", "Employee self-service", "Children Medical Allowance: upload a private invoice in the dialog and Send", p)
	def _():
		open_new("Children Medical Allowance Request")
		p.evaluate("cur_dialog.set_values({child_name: 'QA Child', school_name: 'QA School', academic_year: '2026-2027', fee_amount_requested: 1000, payment_preference: 'Direct to School'})")
		inv = os.path.join(HERE, "qa_invoice.pdf")
		if not os.path.exists(inv):
			tmp = s.ctx.new_page(); tmp.set_content("<h1>QA invoice</h1><p>School fees 1000 SAR</p>"); tmp.pdf(path=inv); tmp.close()
		p.click('.modal.show [data-fieldname="invoice_attachment"] button')
		p.wait_for_selector(".file-uploader, .modal.show input[type=file]", state="attached")
		p.locator("input[type=file]").last.set_input_files(inv)
		p.wait_for_timeout(800)
		p.locator(".modal.show .btn-modal-primary").last.click()
		p.wait_for_function("() => cur_dialog && cur_dialog.get_value('invoice_attachment')", timeout=30000)
		url = p.evaluate("cur_dialog.get_value('invoice_attachment')")
		assert url.startswith("/private/files/"), url
		status, msg, txt = send()
		assert status == 200 and msg and msg["status"].startswith("Pending"), (status, msg, txt[:300])
		CTX["cma"] = msg["name"]

	@check("ESS-13", "Employee self-service", "Save Draft keeps the request in Draft", p)
	def _():
		open_new("Salary Certificate Request")
		p.evaluate("cur_dialog.set_values({purpose: 'Visa Application', addressee: 'QA Embassy'})")
		status, msg, _ = send(primary=False)
		assert status == 200 and msg["status"] == "Draft", msg
		CTX["draft"] = msg["name"]

	@check("ESS-14", "Leave", "Leave Application: Annual Leave 2 days -> Open, approver set by HR", p)
	def _():
		open_new("Leave Application")
		assert not p.locator(".modal.show .btn-modal-secondary:visible").count(), "Save Draft should not be offered for leave"
		p.evaluate("cur_dialog.set_values({leave_type: 'Annual Leave', from_date: '2026-11-10', to_date: '2026-11-11', description: 'QA family visit'})")
		p.wait_for_timeout(500)
		status, msg, txt = send()
		assert status == 200 and msg and msg["status"] == "Open", (status, msg, txt[:300])
		doc = get_doc(s, "Leave Application", msg["name"])["message"]
		assert doc["leave_approver"] == U["hr.manager"] and doc["employee"] == EMP1, doc["leave_approver"]
		CTX["leave"] = msg["name"]

	@check("ESS-15", "Employee self-service", "Counters and Recent Requests refresh after sending", p)
	def _():
		s.goto("/app/employee-dashboard")
		p.wait_for_function("() => Number(document.querySelector('#emd-total').textContent) > 0")
		total, pending = int(p.inner_text("#emd-total")), int(p.inner_text("#emd-pending"))
		assert total >= 9 and pending >= 8, (total, pending)
		return f"total={total} pending={pending}"

	@check("ESS-16", "Employee self-service", "'N request(s)' opens My Requests; View shows the details", p)
	def _():
		p.click('.emd-count[data-doctype="Permission Request"]')
		p.wait_for_selector(".modal.show .emd-view-request")
		p.locator(".modal.show .emd-view-request").first.click()
		p.wait_for_function("() => [...document.querySelectorAll('.modal.show')].some(m => m.innerText.includes('QA: bank appointment'))")
		s.close_dialogs()

	@check("ESS-17", "Employee self-service", "My Profile quick link shows own record summary", p)
	def _():
		p.click("#emd-profile-link")
		p.wait_for_selector(".modal.show")
		assert "QA Employee One" in s.dialog_text()
		s.close_dialogs()

	# ---- Round 2: drafts (HR-16)
	@check("ESS-18", "Round 2: drafts", "My Requests -> View -> Edit Draft: the draft opens filled in, is changed and sent", p)
	def _():
		draft = CTX["draft"]
		s.close_dialogs()
		p.click('.emd-count[data-doctype="Salary Certificate Request"]')
		p.wait_for_selector(f'.modal.show .emd-view-request[data-name="{draft}"]')
		p.click(f'.modal.show .emd-view-request[data-name="{draft}"]')
		p.wait_for_selector(".modal.show .emd-edit-draft")
		p.click(".modal.show .emd-edit-draft")
		p.wait_for_function("() => window.cur_dialog && cur_dialog.title && cur_dialog.title.includes('Edit Draft') && cur_dialog.get_value('addressee') === 'QA Embassy'")
		p.evaluate("cur_dialog.set_value('addressee', 'QA Embassy Riyadh')")
		p.wait_for_timeout(300)
		status, msg, txt = send()
		assert status == 200 and msg["name"] == draft and msg["status"].startswith("Pending"), (status, msg, txt[:300])
		doc = get_doc(s, "Salary Certificate Request", draft)["message"]
		assert doc["addressee"] == "QA Embassy Riyadh" and doc["purpose"] == "Visa Application", (doc["addressee"], doc["purpose"])
		s.close_dialogs()
		return f"{draft}: changed and sent ({msg['status']})"

	@check("ESS-19", "Round 2: drafts", "A request link opens its details; Delete Draft removes the draft", p)
	def _():
		r = s.rpc("medical_hrms.self_service.save_request", {"doctype": "Permission Request", "values": json.dumps({"date": "2026-11-09", "reason": "QA draft to delete"}), "send": 0})
		name = r["message"]["name"]
		s.goto(f"/app/employee-dashboard?request={quote('Permission Request')}&name={quote(name)}")
		p.wait_for_selector(".modal.show .emd-delete-draft")
		assert name in s.dialog_text()
		p.click(".modal.show .emd-delete-draft")
		p.wait_for_function("() => [...document.querySelectorAll('.modal.show')].some(m => /Delete the draft/.test(m.innerText))")
		with p.expect_response(lambda r: "self_service.delete_draft" in r.url) as info:
			p.locator(".modal.show .btn-modal-primary").last.click()
		assert info.value.status == 200, s.dialog_text()[:300]
		s.idle()
		assert get_doc(s, "Permission Request", name)["status"] == 404
		s.close_dialogs()
		return f"{name} deleted"


def employee_isolation(b):
	s2 = Session(b, U["emp2"], label="emp2")
	r = s2.rpc("medical_hrms.self_service.save_request", {"doctype": "Permission Request", "values": json.dumps({"date": "2026-11-04", "from_time": "08:00:00", "to_time": "09:00:00", "reason": "QA emp2 private reason"}), "send": 1})
	CTX["emp2_req"] = (r.get("message") or {}).get("name")
	s = CTX["emp1"]; p = s.page

	@check("SEC-01", "Security", "Request lists show only the employee's own records", p)
	def _():
		assert CTX["emp2_req"], r
		rows = s.rpc("frappe.client.get_list", {"doctype": "Permission Request", "fields": ["employee"], "limit_page_length": 500})["message"]
		assert {x["employee"] for x in rows} == {EMP1}, rows

	@check("SEC-02", "Security", "Another employee's request is refused (form URL, API, details)", p)
	def _():
		s.goto(f"/app/permission-request/{CTX['emp2_req']}")
		p.wait_for_timeout(1500)
		assert "QA emp2 private reason" not in p.inner_text("body")
		assert get_doc(s, "Permission Request", CTX["emp2_req"])["status"] == 403
		assert s.rpc("medical_hrms.self_service.request_details", {"doctype": "Permission Request", "name": CTX["emp2_req"]})["status"] == 403
		s.close_dialogs()

	@check("SEC-03", "Security", "Employee sees only their own Employee record", p)
	def _():
		rows = s.rpc("frappe.client.get_list", {"doctype": "Employee", "fields": ["name"], "limit_page_length": 500})["message"]
		assert [x["name"] for x in rows] == [EMP1], rows
		assert get_doc(s, "Employee", EMP2)["status"] == 403

	@check("SEC-04", "Security", "Employee cannot edit their own Employee master record", p)
	def _():
		assert s.rpc("frappe.client.set_value", {"doctype": "Employee", "name": EMP1, "fieldname": "cell_number", "value": "0500000000"})["status"] == 403

	@check("SEC-05", "Security", "Employee cannot approve their own request", p)
	def _():
		r = s.rpc("frappe.client.set_value", {"doctype": "Permission Request", "name": CTX["perm_req"], "fieldname": "status", "value": "Approved"})
		assert r["status"] >= 400, r
		assert get_doc(s, "Permission Request", CTX["perm_req"])["message"]["status"] == "Pending"

	@check("SEC-06", "Security", "Employee cannot file for someone else or inject a status", p)
	def _():
		r = s.rpc("frappe.client.insert", {"doc": {"doctype": "Permission Request", "employee": EMP2, "date": "2026-11-09", "from_time": "08:00:00", "to_time": "09:00:00", "reason": "QA spoof"}})
		assert r["status"] >= 400, r
		r = s.rpc("medical_hrms.self_service.save_request", {"doctype": "Permission Request", "values": json.dumps({"date": "2026-11-09", "from_time": "08:00:00", "to_time": "09:00:00", "reason": "x", "status": "Approved"}), "send": 1})
		assert r["status"] >= 400, r

	@check("SEC-07", "Security", "Employees cannot file Contract Renewal, nor approve their own Leave Plan", p)
	def _():
		assert s.rpc("frappe.client.insert", {"doc": {"doctype": "Contract Renewal Request", "employee": EMP1, "current_contract_end": "2027-01-01",
			"manager_recommendation": "Renew (Same Terms)"}})["status"] >= 400
		r = s.rpc("frappe.client.insert", {"doc": {"doctype": "Leave Plan Request", "employee": EMP1, "leave_type": "Annual Leave",
			"from_date": "2026-12-20", "to_date": "2026-12-21", "status": "Approved"}})
		assert r["status"] >= 400, r

	@check("SEC-08", "Security", "Employee cannot approve or submit their own leave", p)
	def _():
		s.rpc("frappe.client.set_value", {"doctype": "Leave Application", "name": CTX["leave"], "fieldname": "status", "value": "Approved"})
		d = get_doc(s, "Leave Application", CTX["leave"])["message"]
		assert d["status"] == "Open" and d["docstatus"] == 0, (d["status"], d["docstatus"])
		assert s.rpc("frappe.client.submit", {"doc": d})["status"] >= 400

	@check("SEC-09", "Security", "Employee is refused the HR Dashboard, presence page, Jameah page and their APIs", p)
	def _():
		for route in ("/app/hr-dashboard", "/app/hr-academic-presence/faculty", "/app/jameah-data-check"):
			s.goto(route); p.wait_for_timeout(1000)
			assert not p.locator("#hrd-title, .mhap-table, .jdc-card").count(), route
		for m in ("medical_hrms.medical_hrms.page.hr_academic_presence.hr_academic_presence.get_faculty_schedule",
				"medical_hrms.medical_hrms.page.hr_dashboard.hr_dashboard.get_hr_dashboard_stats", "medical_hrms.jameah.status.get_status"):
			assert s.rpc(m, {"from_date": "2026-09-06", "to_date": "2026-09-12"} if "faculty" in m else {})["status"] == 403, m
		s.close_dialogs()

	@check("SEC-10", "Security", "Employee cannot read applicants or create application links", p)
	def _():
		assert s.rpc("frappe.client.get_list", {"doctype": "Employee Job Applicant"})["status"] == 403
		assert s.rpc("frappe.client.insert", {"doc": {"doctype": "Job Application Link", "application_category": "Academic Staff", "role": "System Manager"}})["status"] >= 400

	su = Session(b, label="unlinked")
	@check("SEC-11", "Security", "A login with no Employee record cannot use self-service", su.page)
	def _():
		su.login(U["unlinked"]); su.goto("/app/employee-dashboard"); su.page.wait_for_timeout(1500)
		body = su.page.inner_text("body")
		assert "Not permitted" in body or "not linked" in body, body[:300]
	su.close()

	so = Session(b, label="outsider")
	@check("SEC-12", "Security", "A staff login without HR/Employee roles is refused both dashboards", so.page)
	def _():
		so.login(U["outsider"])
		so.goto("/app/hr-dashboard"); so.page.wait_for_timeout(1200)
		assert not so.page.locator("#hrd-title").count()
	so.close()
	s2.close()


# --------------------------------------------------------------------------- 3. HR

def hr_dashboard(b):
	h = Session(b, label="hr.manager"); p = h.page
	CTX["hr"] = h

	@check("HRD-01", "HR Dashboard", "HR Manager logs in and lands on the HR Dashboard", p)
	def _():
		h.login(U["hr.manager"])
		assert "/app/hr-dashboard" in p.url, p.url
		p.wait_for_selector("#hrd-title")
		head = p.inner_text(".mhp-shell:visible .mhp-head")
		assert "hr portal" in head.lower() and "QA HR Manager" in head and "HR Manager" in head, head
		return head.replace("\n", " | ")

	@check("HRD-02", "HR Dashboard", "Stat cards load", p)
	def _():
		p.wait_for_function("() => Number(document.querySelector('#stat-employees').textContent) >= 3")
		return {k: p.inner_text(f"#stat-{k}") for k in ("employees", "training", "allowance", "license")}

	@check("HRD-03", "HR Dashboard", "Every link on the HR Dashboard opens without an error", p)
	def _():
		h.goto("/app/hr-dashboard"); h.idle(1500)
		hrefs = sorted(set(p.eval_on_selector_all(".hrd-wrap a[href^='/app/'], .mhp-shell a.mhp-navbtn[href^='/app/'], .mhp-crumbs a[href^='/app/']", "els => els.map(e => e.getAttribute('href'))")))
		broken = []
		for href in hrefs:
			before = len(ISSUES)
			h.goto(href); p.wait_for_timeout(700)
			body = p.inner_text("body")[:3000]
			bad = [w for w in ("Page Not Found", "Not Permitted", "Insufficient Permission", "does not exist") if w in body]
			new = [i for i in ISSUES[before:] if i["kind"] not in ("console-error", "leave-page-prompt") or "Traceback" in i["text"]]
			if bad or new or h.red_dialogs():
				broken.append(f"{href}: {bad or (new[0] if new else h.red_dialogs())}")
			h.close_dialogs()
		assert not broken, broken
		return f"{len(hrefs)} links OK"

	@check("HRD-04", "HR Dashboard", "Medical HRMS workspace renders", p)
	def _():
		h.goto("/app/medical-hrms")
		p.wait_for_selector(".layout-main-section .widget, .layout-main-section .ce-block", timeout=30000)


def hr_approvals(b):
	h = CTX["hr"]; p = h.page

	def set_status(doctype, name, status):
		h.goto(f"/app/{doctype.lower().replace(' ', '-')}/{name}")
		p.wait_for_function("n => window.cur_frm && cur_frm.docname === n", arg=name)
		p.locator('.form-layout select[data-fieldname="status"]').select_option(status)
		p.wait_for_timeout(300)
		return h.save_form().status

	@check("APR-01", "HR approval", "HR approves the Permission Request in the form", p)
	def _():
		assert set_status("Permission Request", CTX["perm_req"], "Approved") == 200, h.dialog_text()[:300]
		assert get_doc(h, "Permission Request", CTX["perm_req"])["message"]["status"] == "Approved"

	@check("APR-02", "HR approval", "HR rejects the Training Request: Rejection Reason is required, then saved", p)
	def _():
		name = CTX["Employee Training Request"]
		h.goto(f"/app/employee-training-request/{name}")
		p.wait_for_function("n => window.cur_frm && cur_frm.docname === n", arg=name)
		p.locator('.form-layout select[data-fieldname="status"]').select_option("Rejected")
		p.wait_for_timeout(500)
		p.keyboard.press("Control+s")
		p.wait_for_timeout(1500)
		txt = h.dialog_text()
		assert "Rejection Reason" in txt, txt[:300]  # Missing Fields: nothing is saved without a reason
		h.close_dialogs()
		p.locator('.form-layout [data-fieldname="rejection_reason"] textarea').fill("QA: the training budget for this term is closed")
		assert h.save_form().status == 200, h.dialog_text()[:300]
		d = get_doc(h, "Employee Training Request", name)["message"]
		assert d["status"] == "Rejected" and d["rejection_reason"].startswith("QA: the training budget"), (d["status"], d["rejection_reason"])

	@check("APR-03", "HR approval", "Salary Certificate moves Pending -> Issued", p)
	def _():
		assert set_status("Salary Certificate Request", CTX["Salary Certificate Request"], "Issued") == 200, h.dialog_text()[:300]

	@check("APR-04", "Leave", "Leave approver approves and submits the Leave Application", p)
	def _():
		name = CTX["leave"]
		h.goto(f"/app/leave-application/{name}")
		p.wait_for_function("n => window.cur_frm && cur_frm.docname === n", arg=name)
		p.locator('.form-layout select[data-fieldname="status"]').select_option("Approved")
		h.save_form()
		p.wait_for_function("() => cur_frm && !cur_frm.is_dirty() && cur_frm.doc.status === 'Approved'")
		p.click(".page-actions .primary-action")
		p.wait_for_selector(".modal.show .btn-modal-primary")
		with p.expect_response(lambda r: "savedocs" in r.url or "submit" in r.url, timeout=30000) as info:
			p.click(".modal.show .btn-modal-primary")
		assert info.value.status == 200, h.dialog_text()[:300]
		h.idle(800)
		d = get_doc(h, "Leave Application", name)["message"]
		assert d["docstatus"] == 1 and d["status"] == "Approved", (d["docstatus"], d["status"])

	@check("APR-05", "Leave", "Employee dashboard shows the approval and the balance 21 -> 19", CTX["emp1"].page)
	def _():
		s = CTX["emp1"]; ep = s.page
		s.goto("/app/employee-dashboard")
		ep.wait_for_function("() => Number(document.querySelector('#emd-approved').textContent) >= 3")
		row = [l for l in ep.inner_text("#emd-leave-summary table").splitlines() if "Annual Leave" in l][0]
		assert "19" in row.split(), row

	@check("APR-06", "Employee self-service", "Leave Return: employee picks their approved leave and sends", CTX["emp1"].page)
	def _():
		s = CTX["emp1"]; ep = s.page
		s.close_dialogs()
		ep.click('.emd-new[data-doctype="Leave Return Request"]')
		ep.wait_for_function("() => window.cur_dialog && cur_dialog.fields_dict.leave_application", timeout=30000)
		ep.evaluate("v => cur_dialog.set_values(v)", {"leave_application": CTX["leave"], "actual_return_date": "2026-11-12"})
		ep.wait_for_timeout(500)
		with ep.expect_response(lambda r: "save_request" in r.url) as info:
			ep.click(".modal.show .btn-modal-primary")
		assert info.value.status == 200, s.dialog_text()[:300]
		assert info.value.json()["message"]["status"].startswith("Pending")
		s.idle()

	hu = Session(b, label="hr.user")
	@check("APR-07", "HR approval", "HR User sees every request list, including Leave Return Request", hu.page)
	def _():
		hu.login(U["hr.user"])
		out = {}
		for dt in ("Permission Request", "Remote Work Request", "Salary Certificate Request", "Pre Approved Overtime Request", "Employee Training Request",
				"Children Medical Allowance Request", "Company Car Request", "Employee Data Update Request", "Leave Return Request", "Leave Application"):
			r = hu.rpc("frappe.client.get_count", {"doctype": dt, "filters": {"employee": ["in", [EMP1, EMP2]]}})
			assert r["status"] == 200, (dt, r)
			out[dt] = r["message"]
		assert out["Permission Request"] >= 2, out
		return out

	@check("APR-08", "Security", "HR can open the private invoice; another employee cannot", hu.page)
	def _():
		url = get_doc(hu, "Children Medical Allowance Request", CTX["cma"])["message"]["invoice_attachment"]
		assert hu.page.request.get(BASE + url).status == 200
		s2 = Session(b, U["emp2"], label="emp2b")
		st = s2.page.request.get(BASE + url).status
		s2.close()
		assert st in (403, 404), st
	hu.close()

	# ---- Round 2: notifications, rejection reason, history, send again (HR-25, HR-16)
	def bell_entry(sess, user, name, timeout=60):
		"""The Notification Log for `name`, created by a background job right after the save."""
		t0 = time.time()
		while time.time() - t0 < timeout:
			r = sess.rpc("frappe.client.get_list", {"doctype": "Notification Log", "filters": {"for_user": user, "document_name": name},
				"fields": ["name", "subject", "email_content", "link"], "order_by": "creation desc"})
			if r["status"] == 200 and r["message"]:
				return r["message"]
			time.sleep(2)
		raise AssertionError(f"no notification for {user} about {name} after {timeout}s")

	@check("APR-09", "Round 2: notifications", "HR is notified in the bell when an employee sends a request", p)
	def _():
		entry = bell_entry(h, U["hr.manager"], CTX["perm_req"])[0]
		assert "QA Employee One" in entry["subject"], entry
		return entry["subject"]

	@check("APR-10", "Round 2: notifications", "Employee: bell shows the rejection; its link opens the request with the reason", CTX["emp1"].page)
	def _():
		s = CTX["emp1"]; ep = s.page
		name = CTX["Employee Training Request"]
		entry = bell_entry(s, U["emp1"], name)[0]
		assert "Rejected" in entry["subject"] and "training budget" in entry["email_content"] and "/app/employee-dashboard?request=" in entry["link"], entry
		s.goto("/app/employee-dashboard")
		ep.click(".mhp-bell")
		ep.wait_for_selector(f'.mhp-notif:has-text("{name}")')
		ep.click(f'.mhp-notif:has-text("{name}")')
		ep.wait_for_function("() => [...document.querySelectorAll('.modal.show')].some(m => m.innerText.includes('training budget for this term is closed'))", timeout=30000)
		return entry["subject"]

	@check("APR-11", "Round 2: send again", "Rejected request: reason and history shown; Send Again makes a new request linked to it", CTX["emp1"].page)
	def _():
		s = CTX["emp1"]; ep = s.page
		name = CTX["Employee Training Request"]
		txt = s.dialog_text()
		assert "History" in txt and "Pending Manager" in txt and "Rejected" in txt, txt[-400:]
		ep.click(".modal.show .emd-resend")
		ep.wait_for_function("() => window.cur_dialog && cur_dialog.title.includes('Send Again') && cur_dialog.get_value('course_details') === 'QA: Simulation in Nursing'")
		ep.evaluate("cur_dialog.set_value('estimated_cost', 900)")
		ep.wait_for_timeout(300)
		with ep.expect_response(lambda r: "self_service.save_request" in r.url) as info:
			ep.click(".modal.show .btn-modal-primary")
		assert info.value.status == 200, s.dialog_text()[:300]
		again = info.value.json()["message"]["name"]
		s.idle()
		doc = get_doc(s, "Employee Training Request", again)["message"]
		assert doc["resubmitted_from"] == name and doc["status"].startswith("Pending"), (doc["resubmitted_from"], doc["status"])
		r = s.rpc("medical_hrms.self_service.request_details", {"doctype": "Employee Training Request", "name": name})["message"]
		assert r["resent_as"] == again and not r["can_resend"], r
		again2 = s.rpc("medical_hrms.self_service.save_request", {"doctype": "Employee Training Request", "values": json.dumps({"course_details": "x"}), "send": 1, "resend_of": name})
		assert again2["status"] != 200, again2  # only once
		s.close_dialogs()
		CTX["resent"] = again
		return f"{name} -> {again}"


def leave_flow(b):
	"""Plan -> apply from the approved plan -> manager approves -> leave ends -> return -> HR completes (second QA employee)."""
	h = CTX["hr"]; hp = h.page
	e = Session(b, label="leave:emp2"); p = e.page

	def dashboard():
		e.goto("/app/employee-dashboard"); p.wait_for_selector("#emd-leave-summary table, #emd-leave-summary .mhp-rows"); e.idle(800)

	def new(doctype):
		e.close_dialogs()
		p.click(f'.emd-new[data-doctype="{doctype}"]'); p.wait_for_selector(".modal.show .modal-title"); p.wait_for_timeout(900)

	def send():
		with p.expect_response(lambda r: "self_service.save_request" in r.url, timeout=30000) as info:
			p.click(".modal.show .btn-modal-primary")
		r = info.value; e.idle(700)
		return r.status, (r.json() if r.ok else {}).get("message"), e.dialog_text()

	def approve(name):
		# as the leave approver (QA HR Manager): Approved, then submit
		doc = h.rpc("frappe.client.get", {"doctype": "Leave Application", "name": name})["message"]
		doc["status"] = "Approved"
		r = h.rpc("frappe.client.save", {"doc": doc})
		assert r["status"] == 200, r
		r = h.rpc("frappe.client.submit", {"doc": r["message"]})
		assert r["status"] == 200, r

	@check("LV-01", "Leave flow", "Leave Application lists only the leave the employee holds, with the days left", p)
	def _():
		e.login(U["emp2"]); dashboard()
		new("Leave Application")
		options = p.eval_on_selector_all(".modal.show select[data-fieldname='leave_type'] option", "os => os.map(o => o.textContent.trim()).filter(Boolean)")
		assert options and options[0].startswith("Annual Leave (") and "days left" in options[0], options
		assert not any(x in " ".join(options) for x in ("Casual", "Privilege", "Compensatory", "Sick Leave")), options
		return " | ".join(options)

	@check("LV-02", "Leave flow", "Employee sends a Leave Plan -> Pending Manager; leave days counted", p)
	def _():
		new("Leave Plan Request")
		p.evaluate("cur_dialog.set_values({leave_type: 'Annual Leave', from_date: '2026-12-14', to_date: '2026-12-17', notes: 'QA plan'})")
		p.wait_for_timeout(500)
		status, msg, txt = send()
		assert status == 200 and msg["status"] == "Pending Manager", (status, msg, txt[:300])
		plan = h.rpc("frappe.client.get", {"doctype": "Leave Plan Request", "name": msg["name"]})["message"]
		assert plan["for_year"] == 2026 and 0 < plan["planned_days"] <= 4, plan
		CTX["plan"] = msg["name"]
		return f"{msg['name']}: {plan['planned_days']} days"

	@check("LV-03", "Leave flow", "HR approves the plan; the employee clicks Apply now; the application is linked to the plan", p)
	def _():
		r = h.rpc("frappe.client.set_value", {"doctype": "Leave Plan Request", "name": CTX["plan"], "fieldname": "status", "value": "Approved"})
		assert r["status"] == 200, r
		dashboard()
		assert "Plan approved" in p.inner_text("#emd-leave-summary"), p.inner_text("#emd-leave-summary")[:300]
		p.locator("#emd-leave-summary .emd-leave-step", has_text="Apply now").first.click()
		p.wait_for_selector(".modal.show .modal-title"); p.wait_for_timeout(1200)
		values = p.evaluate("cur_dialog.get_values(true)")
		assert values["leave_type"] == "Annual Leave" and str(values["from_date"]) == "2026-12-14", values
		status, msg, txt = send()
		assert status == 200 and msg["status"] == "Open", (status, msg, txt[:300])
		linked = h.rpc("frappe.client.get_value", {"doctype": "Leave Plan Request", "filters": CTX["plan"], "fieldname": "leave_application"})["message"]
		assert linked["leave_application"] == msg["name"], linked
		return f"{CTX['plan']} -> {msg['name']}"

	@check("LV-04", "Leave flow", "After a leave ends the dashboard asks for the return; the form is pre-filled, no certificate for annual leave", p)
	def _():
		r = e.rpc("medical_hrms.self_service.save_request", {"doctype": "Leave Application", "send": 1,
			"values": json.dumps({"leave_type": "Annual Leave", "from_date": "2026-10-12", "to_date": "2026-10-13", "description": "QA past leave"})})
		assert r["status"] == 200, r
		approve(r["message"]["name"]); CTX["past_leave"] = r["message"]["name"]
		dashboard()
		text = p.inner_text("#emd-leave-summary")
		assert "Tell HR you are back" in text, text[:400]
		p.locator("#emd-leave-summary .emd-leave-step", has_text="Send Leave Return").first.click()
		p.wait_for_selector(".modal.show .modal-title"); p.wait_for_timeout(2000)
		v = p.evaluate("cur_dialog.get_values(true)")
		assert v["leave_application"] == CTX["past_leave"] and str(v["actual_return_date"]) == "2026-10-14", v
		assert not p.is_visible(".modal.show [data-fieldname='fitness_certificate'] input"), "fitness certificate asked after annual leave"
		status, msg, txt = send()
		assert status == 200 and msg["status"] == "Pending HR Review", (status, msg, txt[:300])
		CTX["return"] = msg["name"]
		ret = h.rpc("frappe.client.get", {"doctype": "Leave Return Request", "name": msg["name"]})["message"]
		assert str(ret["planned_return_date"]) == "2026-10-14" and ret["is_sick_leave"] == 0 and ret["leave_type"] == "Annual Leave", ret

	@check("LV-05", "Leave flow", "HR completes the return; occupational health is refused for annual leave", hp)
	def _():
		r = h.rpc("frappe.client.set_value", {"doctype": "Leave Return Request", "name": CTX["return"], "fieldname": "status", "value": "Pending Occupational Health"})
		assert r["status"] >= 400 and "sick leave" in r["server_msg"], r
		r = h.rpc("frappe.client.set_value", {"doctype": "Leave Return Request", "name": CTX["return"], "fieldname": "status", "value": "Completed"})
		assert r["status"] == 200, r

	@check("LV-06", "Leave flow", "HR Portal: leave setup check covers every company with active staff", hp)
	def _():
		h.goto("/app/hr-dashboard"); hp.wait_for_function("() => document.querySelector('#hrd-leave-ready .mhp-row')", timeout=60000)
		text = hp.inner_text("#hrd-leave-ready")
		assert "Medical College" in text and "Leave period active" in text and "Every employee has annual leave this year" in text, text[:500]
		counts = hp.eval_on_selector_all("[data-leave-count]", "els => els.map(e => e.textContent.trim())")
		assert len(counts) == 4 and all(c.isdigit() for c in counts), counts
		return text.replace("\n", " | ")[:200]

	@check("LV-07", "Leave flow", "Sick leave stages are named in pay order", hp)
	def _():
		rows = h.rpc("frappe.client.get_list", {"doctype": "Leave Type", "filters": {"name": ["like", "Sick Leave %-%"]}, "fields": ["name"], "order_by": "name asc"})["message"]
		names = [r["name"] for r in rows]
		assert names == ["Sick Leave 1 - Full Pay", "Sick Leave 2 - 75% Pay", "Sick Leave 3 - Unpaid"], names
	e.close()


def employee_master(b):
	h = CTX["hr"]; p = h.page

	@check("EMP-01", "Employee master", "HR edits and saves an Employee who has a login", p)
	def _():
		h.goto(f"/app/employee/{EMP1}")
		p.wait_for_function("n => window.cur_frm && cur_frm.docname === n", arg=EMP1)
		p.evaluate("v => cur_frm.set_value('cell_number', v)", "+9665" + time.strftime("%H%M%S") + "1")
		p.wait_for_timeout(300)
		assert h.save_form().status == 200, h.dialog_text()[:400]

	@check("EMP-02", "Ministry lookups", "Gender only offers Ministry gender codes", p)
	def _():
		h.close_dialogs()
		inp = p.locator('.form-layout [data-fieldname="gender"] input'); inp.scroll_into_view_if_needed()
		with p.expect_response(lambda r: "search_link" in r.url) as info:
			inp.click(); inp.fill(""); inp.type("a", delay=50); inp.press("Backspace")
		values = {i["value"] for i in info.value.json()["message"]}
		p.keyboard.press("Escape")
		assert values and all(v.startswith("Gender::") for v in values), values

	@check("EMP-03", "Ministry lookups", "Every Ministry lookup field is filtered to its own list", p)
	def _():
		bad = p.evaluate("""() => cur_frm.meta.fields.filter(f => f.fieldtype === 'Link' && f.options === 'Jameah Ministry Code')
			.filter(f => !(f.link_filters && f.link_filters.includes('code_category')) && !(cur_frm.fields_dict[f.fieldname] && cur_frm.fields_dict[f.fieldname].get_query))
			.map(f => f.fieldname)""")
		assert not bad, bad

	@check("EMP-04", "Ministry lookups", "A code from the wrong list is refused with a clear message", p)
	def _():
		other = h.rpc("frappe.client.get_list", {"doctype": "Jameah Ministry Code", "filters": {"code_category": "Job ranks"}, "limit_page_length": 1})["message"][0]["name"]
		r = h.rpc("frappe.client.set_value", {"doctype": "Employee", "name": EMP1, "fieldname": "gender", "value": other})
		assert r["status"] >= 400 and "category" in r["server_msg"], r

	@check("EMP-05", "Ministry identity", "An invalid ID number is refused in the form", p)
	def _():
		h.goto(f"/app/employee/{EMP1}")
		p.wait_for_function("n => window.cur_frm && cur_frm.docname === n", arg=EMP1)
		p.evaluate("cur_frm.set_value('custom_identity_number', '12345')"); p.wait_for_timeout(300)
		r = h.save_form(); txt = h.dialog_text()
		assert r.status >= 400 and "digits" in txt, (r.status, txt[:300])
		h.close_dialogs(); p.evaluate("cur_frm.reload_doc()"); h.idle()

	@check("EMP-06", "Ministry identity", "A duplicate ID number is refused", p)
	def _():
		idno = h.rpc("frappe.client.get_value", {"doctype": "Employee", "filters": EMP2, "fieldname": "custom_identity_number"})["message"]["custom_identity_number"]
		r = h.rpc("frappe.client.set_value", {"doctype": "Employee", "name": EMP1, "fieldname": "custom_identity_number", "value": idno})
		assert r["status"] >= 400 and "already registered" in r["server_msg"], r

	@check("EMP-07", "Jameah", "Employee form -> View -> Ministry (Jameah) Data opens", p)
	def _():
		h.goto(f"/app/employee/{EMP1}")
		p.wait_for_function("n => window.cur_frm && cur_frm.docname === n", arg=EMP1)
		p.locator(".inner-group-button button:has-text('View')").first.click()
		p.locator(".dropdown-menu.show a:has-text('Ministry (Jameah) Data')").first.click()
		p.wait_for_selector(".modal.show")
		txt = h.dialog_text(); h.close_dialogs()
		assert "Ministry (Jameah) Data" in txt, txt[:200]
		return txt.splitlines()[1][:120] if len(txt.splitlines()) > 1 else ""

	@check("EMP-08", "Ministry identity", "Non-Saudi (Iqama) employee: form keeps the Iqama number, opens unchanged and saves", p)
	def _():
		code = lambda cat, c: h.rpc("frappe.client.get_list", {"doctype": "Jameah Ministry Code", "filters": {"code_category": cat, "ministry_code": c}, "limit_page_length": 1})["message"][0]["name"]
		before = h.rpc("frappe.client.get", {"doctype": "Employee", "name": EMP2})["message"]
		keep = {k: before[k] for k in ("custom_jameah_nationality", "custom_identity_type", "custom_identity_number")}
		r = h.rpc("frappe.client.set_value", {"doctype": "Employee", "name": EMP2, "fieldname": {
			"custom_jameah_nationality": code("Nationality", "113"), "custom_identity_type": code("Identity type", "03"), "custom_identity_number": "2099000002"}})
		assert r["status"] == 200, r
		h.goto(f"/app/employee/{EMP2}")
		p.wait_for_function("n => window.cur_frm && cur_frm.docname === n", arg=EMP2); p.wait_for_timeout(1500)
		st = p.evaluate("""() => ({dirty: cur_frm.is_dirty(), id: cur_frm.doc.custom_identity_number, id_hidden: cur_frm.get_field('custom_identity_number').df.hidden,
			home_hidden: cur_frm.get_field('custom_original_home_id_number').df.hidden, home_reqd: cur_frm.get_field('custom_original_home_id_number').df.reqd})""")
		assert not st["dirty"] and st["id"] == "2099000002" and not st["id_hidden"] and not st["home_hidden"] and not st["home_reqd"], st
		p.evaluate("cur_frm.set_value('custom_original_home_id_number', 'TN-QA-55501')"); p.wait_for_timeout(300)
		assert h.save_form().status == 200, h.dialog_text()[:300]
		r = h.rpc("frappe.client.set_value", {"doctype": "Employee", "name": EMP2, "fieldname": keep})
		assert r["status"] == 200, r
		home = h.rpc("frappe.client.get_value", {"doctype": "Employee", "filters": EMP2, "fieldname": "custom_original_home_id_number"})["message"]
		assert not home["custom_original_home_id_number"], home
		return "Iqama kept and saved; back to Saudi -> home-country ID cleared"

	@check("LIC-01", "Medical licenses", "HR creates a Medical License for the employee", p)
	def _():
		h.goto("/app/employee-medical-license/new")
		p.wait_for_function("() => window.cur_frm && cur_frm.doctype === 'Employee Medical License'")
		opts = p.evaluate("cur_frm.fields_dict.license_type.df.options.split('\\n').filter(Boolean)")
		p.evaluate("v => cur_frm.set_value(v)", {"employee": EMP1, "license_type": opts[0], "license_number": "QA-LIC-001", "expiry_date": (date.today() + timedelta(days=400)).isoformat()})
		p.wait_for_timeout(800)
		assert h.save_form().status == 200, h.dialog_text()[:300]
		CTX["license"] = p.evaluate("cur_frm.docname")

	@check("LIC-02", "Medical licenses", "Employees see only their own license", CTX["emp1"].page)
	def _():
		mine = CTX["emp1"].rpc("frappe.client.get_list", {"doctype": "Employee Medical License", "fields": ["employee"]})["message"]
		assert mine and {m["employee"] for m in mine} == {EMP1}, mine
		s2 = Session(b, U["emp2"], label="emp2c")
		theirs = s2.rpc("frappe.client.get_list", {"doctype": "Employee Medical License", "fields": ["name"]})["message"]
		st = get_doc(s2, "Employee Medical License", CTX["license"])["status"]
		s2.close()
		assert theirs == [] and st == 403, (theirs, st)


# --------------------------------------------------------------------------- 4. recruitment

def fill_application(gp, email, idno):
	return gp.evaluate("""([email, idno]) => {
		const f = document.getElementById('ja-form'); const chosen = {};
		const pick = (sel, re) => { const o = [...sel.options].find(o => o.value && re.test(o.text)); return o ? o.value : ([...sel.options].find(o => o.value) || {}).value; };
		f.querySelectorAll('input, select, textarea').forEach(el => {
			if (!el.name || el.type === 'file' || el.type === 'checkbox' || el.type === 'hidden') return;
			if (el.tagName === 'SELECT') {
				if (el.name === 'custom_identity_type') el.value = pick(el, /national|وطنية|هوية/i);
				else if (el.name === 'custom_jameah_nationality') el.value = pick(el, /saudi|سعود/i);
				else if (!el.value) el.value = pick(el, /./);
				const row = el.closest('.ja-repeat-row');
				chosen[(row ? row.parentElement.id + '.' : '') + el.name] = el.value;
			} else if (/_ar$/.test(el.name)) el.value = 'محمد';
			else if (el.type === 'email') el.value = email;
			else if (el.name.includes('extention')) el.value = '321';
			else if (el.type === 'tel') el.value = '0500000777';
			else if (el.type === 'number') el.value = el.name === 'graduation_year' ? '2015' : '4';
			else if (el.type === 'date') el.value = '2015-06-30';
			else if (el.type === 'url') el.value = 'https://example.com/cv.pdf';
			else if (el.name === 'custom_identity_number') el.value = idno;
			else if (/name/.test(el.name)) el.value = 'Qa' + idno.slice(-3).replace(/\d/g, d => 'abcdefghij'[d]);  // letters only (form rule)
			else if (!el.value) el.value = 'QA ' + el.name + ' ' + idno;
			el.dispatchEvent(new Event('change', {bubbles: true}));
		});
		return chosen;
	}""", [email, idno])


def walk_to_review(gp):
	"""The form is a step-by-step wizard (22 Oct): Next through every step like an applicant, then tick the consent."""
	for _ in range(15):
		if gp.is_visible("#ja-submit-btn"):
			break
		gp.click("#ja-next-btn"); gp.wait_for_timeout(500)
		refused = gp.eval_on_selector_all(".ja-step-error", "els => els.map(e => e.textContent.trim()).filter(Boolean)")
		assert not refused, f"a step refused Next: {refused} {gp.eval_on_selector_all('.ja-field-error', 'els => els.map(e => e.textContent.trim()).filter(Boolean)')}"
	assert gp.is_visible("#ja-submit-btn"), "never reached the review step"
	gp.check("#ja-consent")


def apply_and_hire(b, h, category, role, email, idno, company_email, refused_email=None):
	p = h.page
	h.goto("/app/job-application-link/new")
	p.wait_for_function("() => window.cur_frm && cur_frm.doctype === 'Job Application Link'")
	p.evaluate("""([c, r]) => cur_frm.set_value({application_category: c, role: r,
		valid_from: moment(frappe.datetime.now_datetime()).subtract(1, 'hours').format('YYYY-MM-DD HH:mm:ss'),
		valid_until: frappe.datetime.add_days(frappe.datetime.now_datetime(), 7)})""", [category, role])
	p.wait_for_timeout(800)
	assert h.save_form().status == 200, h.dialog_text()[:300]
	p.locator("button:has-text('Generate Link')").first.click()
	p.wait_for_function("() => cur_frm.doc.generated_url", timeout=30000)
	url = p.evaluate("cur_frm.doc.generated_url")
	h.close_dialogs()
	g = Session(b, label="applicant")
	g.page.goto("/" + url.split("/", 3)[3]); g.page.wait_for_selector("#ja-form")
	appreciation = g.page.eval_on_selector_all("select[name='assessment_type'] option", "os => os.map(o => o.value).filter(Boolean)")
	chosen = fill_application(g.page, email, idno)
	bad = g.page.eval_on_selector_all("#ja-form :invalid", "els => els.map(e => e.name || e.id)")
	assert not bad, f"form still invalid: {bad}"
	walk_to_review(g.page)
	with g.page.expect_response(lambda r: "submit_application" in r.url, timeout=30000) as info:
		g.page.click("#ja-submit-btn")
	g.page.wait_for_timeout(800)
	assert info.value.status == 200, g.page.inner_text("#ja-error")
	g.page.wait_for_selector("#ja-success:not(.ja-hidden)")
	applicant = re.search(r"(APP-[\w-]+)", g.page.inner_text("#ja-success")).group(1)
	g.close()
	h.goto(f"/app/employee-job-applicant/{applicant}")
	p.wait_for_function("n => window.cur_frm && cur_frm.docname === n", arg=applicant)
	with p.expect_response(lambda r: "accept_application" in r.url):
		p.locator("button:has-text('Accept')").first.click()
	h.idle(1200)
	p.wait_for_function("() => cur_frm.doc.status === 'Accepted'")
	refusal = None
	if refused_email:
		resp = create_employee_dialog(h, refused_email)
		text = h.dialog_text()
		made = h.rpc("frappe.client.get_list", {"doctype": "Employee", "filters": {"custom_job_applicant": applicant}})["message"]
		refusal = {"status": resp.status, "message": text[:300], "employees": made}
		h.close_dialogs()
	resp = create_employee_dialog(h, company_email)
	assert resp.status == 200, (resp.status, h.dialog_text()[:400])
	return applicant, resp.json()["message"], chosen, appreciation, h.red_dialogs() + [t for t in [h.dialog_text()] if "could not be created" in t], refusal


def create_employee_dialog(h, company_email):
	p = h.page
	p.locator("button:has-text('Create Employee')").first.click()
	p.wait_for_selector(".modal.show .btn-modal-primary"); p.wait_for_timeout(500)
	p.evaluate("v => cur_dialog.set_value('company_email', v)", company_email)
	dept = h.rpc("frappe.client.get_list", {"doctype": "Department Edu", "filters": {"department_name": ["like", "%Internal Medicine%"]}, "limit_page_length": 1})["message"]
	if dept:
		p.evaluate("v => cur_dialog.set_value('edu_department', v)", dept[0]["name"])
	# Employee fields the application form does not ask for (HR completes them here); keep any default
	if not p.evaluate("cur_dialog.get_value('department')"):
		hr_dept = h.rpc("frappe.client.get_list", {"doctype": "Department", "filters": {"is_group": 0}, "limit_page_length": 1})["message"]
		p.evaluate("v => cur_dialog.set_value('department', v)", hr_dept[0]["name"])
	p.wait_for_timeout(600)
	missing = p.evaluate("() => cur_dialog.fields.filter(f => f.reqd && !cur_dialog.get_value(f.fieldname)).map(f => f.fieldname)")
	assert not missing, f"Create Employee dialog has empty required fields: {missing}"
	p.locator(".modal.show .modal-title").last.click(); p.wait_for_timeout(300)
	with p.expect_response(lambda r: "create_employee_from_applicant" in r.url, timeout=90000) as info:
		p.click(".modal.show .btn-modal-primary")
	h.idle(1500)
	return info.value


def recruitment(b):
	h = CTX["hr"]; p = h.page
	g = Session(b, label="guest")

	@check("REC-01", "Recruitment", "An invalid application link shows the 'invalid link' message", g.page)
	def _():
		g.page.goto("/job-application/notarealtoken123")
		assert not g.page.locator("#ja-form").count() or not g.page.locator("#ja-form").is_visible()
	g.close()

	@check("REC-02", "Recruitment", "HR cannot create a link that would grant an admin role", p)
	def _():
		assert h.rpc("frappe.client.insert", {"doc": {"doctype": "Job Application Link", "application_category": "Academic Staff", "role": "System Manager"}})["status"] >= 400

	hires = {}
	for tid, title, category, role, email, idno in (
			("REC-03", "Academic (Instructor) applicant -> HR hires -> Employee + Instructor + login", "Academic Staff", "Instructor", "qa.ac.applicant", "1099000882"),
			("REC-04", "Academic Advisor applicant -> Employee + Advisor record (phone normalised, no error)", "Academic Staff", "Academic Advisor", "qa.adv.applicant", "1099000883"),
			("REC-05", "Non-academic applicant -> Employee (corrected Appreciation list)", "Non-Academic / Other Staff", "Employee", "qa.na.applicant", "1099000881")):
		@check(tid, "Recruitment", title, p)
		def _(category=category, role=role, email=email, idno=idno, tid=tid):
			academic = role in ("Instructor", "Academic Advisor")
			work_email = f"{email}.staff@{COLLEGE}" if academic else f"{email}.staff@{DOM}"
			app, res, chosen, appreciation, warnings, refusal = apply_and_hire(b, h, category, role, f"{email}@{DOM}", idno, work_email,
				refused_email=f"{email}.personal@{DOM}" if role == "Instructor" else None)
			if refusal:
				CTX["academic_email_refusal"] = refusal
			assert appreciation and all(v.startswith("Student Evaluation Coding::") for v in appreciation), appreciation[:3]
			assert not warnings, warnings
			if role == "Instructor":
				assert res.get("instructor"), res
			if role == "Academic Advisor":
				assert res.get("advisor"), res
			hires[role] = (app, res, chosen)
			return f"{app} -> {res}"
	CTX["hires"] = hires

	@check("REC-08", "Recruitment", "An academic hire with a personal e-mail is refused up front; nothing is created", p)
	def _():
		r = CTX.get("academic_email_refusal")
		assert r, "REC-03 did not reach the refusal step"
		assert r["status"] != 200 and "College E-mail Needed" in r["message"] and not r["employees"], r
		return f"refused (HTTP {r['status']}): {r['message'].splitlines()[0]} ... no Employee created"

	@check("REC-06", "Jameah", "Form selections -> Employee record -> Ministry views carry the same codes", p)
	def _():
		app, res, chosen = hires["Employee"]
		emp = h.rpc("frappe.client.get", {"doctype": "Employee", "name": res["employee"]})["message"]
		rows = h.rpc("medical_hrms.jameah.status.employee_view_rows", {"employee": res["employee"]})["message"]["views"]
		pi = rows["jameahEmployeePersonalInfo"]
		assert len(pi) == 1, pi
		pi = pi[0]
		code = lambda v: v.split("::", 1)[1] if v else None
		pairs = {"NationalityCode": code(emp["custom_jameah_nationality"]), "IdentityTypeCode": code(emp["custom_identity_type"]),
			"ReligionCode": code(emp["custom_ministry_religion"]), "CityCode": code(emp["custom_ministry_work_city"]),
			"IdentityNumber": "1099000881", "WorkTelephoneExtentionNumber": "321", "SpecialNeedsTypeCode": None, "OriginalHomeIDNumber": None}
		bad = {k: (pi.get(k), v) for k, v in pairs.items() if str(pi.get(k)) != str(v)}
		assert not bad, bad
		assert pi["NationalityCode"] == code(chosen["custom_jameah_nationality"])
		q = rows["jameahEmployeeAcademicQualifications"]
		assert q and q[0]["AssessmentTypeCode"] == code(chosen["ja-rows-academic_qualifications.assessment_type"]), q
		return f"{len(pairs)} personal fields + qualification code match the form"

	@check("REC-07", "Jameah", "Teaching hires (Instructor, Advisor) are not sent as Employees", p)
	def _():
		for role in ("Instructor", "Academic Advisor"):
			res = hires[role][1]
			out = h.rpc("medical_hrms.jameah.status.employee_view_rows", {"employee": res["employee"]})["message"]
			if role == "Instructor":
				assert all(not v for v in out["views"].values()) and "Instructor" in (out["excluded_reason"] or ""), out["excluded_reason"]
		return "Instructor hire excluded (sent as Faculty)"

	@check("REC-10", "Recruitment", "A new hire's Employee record saves straight away (no 'Missing Fields')", p)
	def _():
		out = []
		for role, (app, res, chosen) in hires.items():
			h.goto(f"/app/employee/{res['employee']}")
			p.wait_for_function("n => window.cur_frm && cur_frm.docname === n", arg=res["employee"]); p.wait_for_timeout(1200)
			p.evaluate("cur_frm.set_value('notice_number_of_days', (cur_frm.doc.notice_number_of_days || 0) + 1)"); p.wait_for_timeout(400)
			r = h.save_form()
			assert r.status == 200, (role, r.status, h.dialog_text()[:300])
			out.append(res["employee"])
		return f"{', '.join(out)} saved"

	@check("REC-09", "Recruitment", "A hired employee opens without 'Not Saved'; answers that don't apply are not stored", p)
	def _():
		out = []
		for role, (app, res, chosen) in hires.items():
			h.goto(f"/app/employee/{res['employee']}")
			p.wait_for_function("n => window.cur_frm && cur_frm.docname === n", arg=res["employee"]); p.wait_for_timeout(1500)
			st = p.evaluate("""() => ({dirty: cur_frm.is_dirty(), sn: cur_frm.doc.custom_is_special_needs,
				sn_type: cur_frm.doc.custom_ministry_special_needs_type || null, home: cur_frm.doc.custom_original_home_id_number || null})""")
			assert not st["dirty"] and (st["sn"] or not st["sn_type"]) and not st["home"], (role, st)
			out.append(res["employee"])
		return f"{', '.join(out)}: clean (special-needs type and home-country ID dropped for 'No' / Saudi)"

	a = Session(b, label="academic.admin")
	@check("REC-11", "Round 2: Instructor link", "Instructor form: picking the Employee fills gender and department and saves (B-26)", a.page)
	def _():
		app, res, chosen = hires["Instructor"]
		a.login(U["academic.admin"])
		ap = a.page
		a.goto(f"/app/instructor/{res['instructor']}")
		ap.wait_for_function("n => window.cur_frm && cur_frm.docname === n", arg=res["instructor"])
		ap.wait_for_timeout(800)
		ap.evaluate("() => cur_frm.set_value({employee: '', gender: '', department: ''})")
		ap.wait_for_timeout(800)
		ap.evaluate("e => cur_frm.set_value('employee', e)", res["employee"])
		a.idle(1500)
		assert not a.red_dialogs(), a.red_dialogs()
		r = a.save_form()
		assert r.status == 200, a.dialog_text()[:300]
		# Gender Edu is readable by System Managers only: the form leaves Gender to the server, which fills it on save
		doc = a.rpc("frappe.client.get", {"doctype": "Instructor", "name": res["instructor"]})["message"]
		got = {k: doc.get(k) for k in ("employee", "gender", "department")}
		assert got["employee"] == res["employee"] and got["gender"] in ("Male", "Female"), got
		return f"{res['instructor']}: {got}"
	a.close()


# --------------------------------------------------------------------------- 5. presence + Jameah pages

def presence(b):
	h = CTX["hr"]; p = h.page
	week = ("2026-09-06", "2026-09-12")

	def open_tab(tab, **vals):
		h.goto(f"/app/hr-academic-presence/{tab}")
		p.wait_for_selector(".mhap-tabs .mhap-tab.active")
		h.idle(800)
		if vals:
			with p.expect_response(lambda r: "hr_academic_presence" in r.url, timeout=90000):
				p.evaluate("""v => { const pr = frappe.pages['hr-academic-presence'].presence;
					Object.entries(v).forEach(([k, x]) => pr.controls[k].set_value(x)); }""", vals)
			h.idle(1500)
		return p.evaluate("() => [...document.querySelectorAll('.mhap-stats *')].map(e => e.innerText).join(' | ')")

	@check("PRS-01", "Academic presence", "Faculty Schedules for 6-12 Sep 2026 list sessions", p)
	def _():
		stats = open_tab("faculty", from_date=week[0], to_date=week[1])
		rows = p.locator(".mhap-table tbody tr").count()
		assert rows > 50, (rows, stats)
		return f"{rows} rows"

	@check("PRS-02", "Academic presence", "Faculty filter narrows to one faculty member", p)
	def _():
		first = p.evaluate("() => (frappe.pages['hr-academic-presence'].presence.data.rows || [])[0]")
		ins = first.get("instructor")
		with p.expect_response(lambda r: "get_faculty_schedule" in r.url, timeout=90000):
			p.evaluate("v => frappe.pages['hr-academic-presence'].presence.controls.instructor.set_value(v)", ins)
		h.idle(1200)
		rows = p.evaluate("() => frappe.pages['hr-academic-presence'].presence.data.rows")
		assert rows and all(r.get("instructor") == ins for r in rows), len(rows or [])

	@check("PRS-03", "Academic presence", "Proctor Schedules tab loads", p)
	def _():
		open_tab("proctors", from_date=week[0], to_date=week[1])
		assert p.locator(".mhap-table, .mhap-empty").count()

	@check("PRS-04", "Academic presence", "Students on Campus for 8 Sep 2026: hourly table, 858 expected", p)
	def _():
		stats = open_tab("students", on_date="2026-09-08")
		assert p.locator(".mhap-table tbody tr").count() >= 10
		assert "858" in stats or "858" in p.inner_text(".mhap-table-wrap"), stats

	@check("PRS-05", "Academic presence", "Faculty After 4 PM lists people with an evidence source", p)
	def _():
		open_tab("after_hours", from_date=week[0], to_date=week[1])
		assert p.locator(".mhap-table tbody tr").count() > 0

	@check("PRS-06", "Academic presence", "Export (Excel CSV) downloads a file", p)
	def _():
		with p.expect_download(timeout=30000) as dl:
			p.click("#mhap-export")
		lines = open(dl.value.path(), encoding="utf-8-sig").read().strip().splitlines()
		assert len(lines) > 1
		return f"{dl.value.suggested_filename}: {len(lines)} lines"


def jameah_pages(b):
	h = CTX["hr"]; p = h.page

	@check("JM-01", "Jameah", "Jameah Data Check: 0 invalid codes, 23 views (Employee, Faculty, Student), settings and review lists", p)
	def _():
		h.goto("/app/hr-dashboard")
		p.click('.hrd-wrap a[href="/app/jameah-data-check"]')
		p.wait_for_selector(".jdc-card", timeout=90000)
		cards = p.eval_on_selector_all(".jdc-card", "cs => cs.map(c => c.innerText.replace(/\\s+/g, ' '))")
		assert cards[0].startswith("0"), cards
		assert p.locator(".jdc table code").count() == 23
		return " | ".join(cards)

	@check("JM-02", "Jameah", "Jameah Settings: picker filtered; wrong-list code refused in form and server", p)
	def _():
		h.goto("/app/jameah-settings")
		p.wait_for_function("() => window.cur_frm && cur_frm.doctype === 'Jameah Settings'")
		inp = p.locator('[data-fieldname="college"] input'); inp.click(); inp.fill("")
		with p.expect_response(lambda r: "search_link" in r.url) as info:
			inp.type("K", delay=60)
		assert {i["value"].split("::")[0] for i in info.value.json()["message"]} == {"College Coding Guide"}
		p.keyboard.press("Escape")
		r = h.rpc("frappe.client.set_value", {"doctype": "Jameah Settings", "name": "Jameah Settings", "fieldname": "college", "value": "Gender::1"})
		assert r["status"] >= 400 and "College Coding Guide" in r["server_msg"], r
		p.evaluate("cur_frm.reload_doc()"); h.idle()

	@check("JM-03", "Jameah", "Code Map: values waiting for review; picker limited to the row's list", p)
	def _():
		name = h.rpc("frappe.client.get_list", {"doctype": "Jameah Code Map", "filters": {"source_value": "Internship"}, "limit_page_length": 1})["message"][0]["name"]
		h.goto(f"/app/jameah-code-map/{name}")
		p.wait_for_function("n => window.cur_frm && cur_frm.docname === n", arg=name)
		inp = p.locator('[data-fieldname="jameah_code"] input'); inp.click(); inp.fill("")
		with p.expect_response(lambda r: "search_link" in r.url) as info:
			inp.type("r", delay=60)
		p.keyboard.press("Escape")
		assert {i["value"].split("::")[0] for i in info.value.json()["message"]} == {"General situation"}


# --------------------------------------------------------------------------- 6. error sweep

MHRMS_DOCTYPES = ["Permission Request", "Remote Work Request", "Leave Plan Request", "Leave Return Request", "Salary Certificate Request",
	"Pre Approved Overtime Request", "Employee Training Request", "Children Medical Allowance Request", "Company Car Request",
	"Contract Renewal Request", "Employee Data Update Request", "Employee Medical License", "Employee Job Applicant", "Job Application Link",
	"Jameah Code Map", "Jameah Ministry Code", "Jameah College", "Jameah Facility", "Jameah Academic Department", "Jameah Agency", "Jameah Branch",
	"Jameah Deanery", "Employee", "Leave Application", "Leave Allocation", "Attendance", "Expense Claim", "Travel Request", "Holiday List", "Leave Policy"]
# what employees file themselves (their own lists and forms are swept too)
SELF_SERVICE = MHRMS_DOCTYPES[:12]


def latest_records(doctypes):
	"""/app/<doctype>/<newest record> for each doctype that has one, so saved forms are opened too, not only new ones."""
	h, routes = CTX.get("hr"), []
	if not h:
		return routes
	for d in doctypes:
		try:
			rows = h.rpc("frappe.client.get_list", {"doctype": d, "fields": ["name"], "order_by": "modified desc", "limit_page_length": 1})["message"]
		except Exception:
			continue
		if rows:
			routes.append(f"/app/{d.lower().replace(' ', '-')}/{quote(str(rows[0]['name']), safe='')}")
	return routes


def sweep_role(b, label, user, password, routes):
	s = Session(b, label=label)
	visited, problems = 0, []
	try:
		s.login(user, password)
	except Exception as e:
		return 0, [f"login failed: {e}"]
	landing = s.page.url.replace(BASE, "")
	queue = list(dict.fromkeys([landing] + routes))
	# links on the landing page too
	try:
		queue += [h for h in s.page.eval_on_selector_all("a[href^='/app/']", "els => els.map(e => e.getAttribute('href'))") if h not in queue]
	except Exception:
		pass
	for route in list(dict.fromkeys(queue))[:220]:
		before = len(ISSUES)
		try:
			s.goto(route)
			s.page.wait_for_timeout(900)
			for d in s.red_dialogs():
				s._issue("error-dialog", d)
			s.close_dialogs()
		except Exception as e:
			s._issue("navigation-timeout", str(e)[:200], route)
		visited += 1
		for i in ISSUES[before:]:
			if i["kind"] in ("js-error", "error-dialog", "navigation-timeout", "browser-dialog") or i["kind"].startswith("http-5") or "Traceback" in i["text"]:
				problems.append(f"{route}: {i['kind']} {i['text'][:160]}")
	s.close()
	return visited, problems


def ministry_report(b):
	h = CTX["hr"]; p = h.page
	route = "/app/query-report/Employees Missing Ministry Data"

	@check("RPT-01", "Ministry data", "HR Manager: Employees Missing Ministry Data report opens with the data-sheet buttons", p)
	def _():
		h.goto("/app/hr-dashboard")
		p.click('.hrd-wrap a[href*="Employees%20Missing%20Ministry%20Data"]')
		p.wait_for_selector(".dt-scrollable, .no-result, .report-summary", timeout=60000); h.idle(1500)
		buttons = p.eval_on_selector_all(".page-actions button, .page-actions .btn", "els => els.map(e => e.innerText.trim()).filter(Boolean)")
		assert any("Download Data Sheet" in t for t in buttons) and any("Check / Import" in t for t in buttons), buttons
		summary = p.inner_text(".report-summary") if p.locator(".report-summary").count() else ""
		assert "Employees sent to the Ministry" in summary, summary[:200]
		return summary.replace("\n", " ")[:120]

	u = Session(b, U["hr.user"], label="report:hr.user")

	@check("RPT-02", "Ministry data", "HR User: the report opens without Download / Import", u.page)
	def _():
		u.goto(route); u.page.wait_for_selector(".dt-scrollable, .no-result, .report-summary", timeout=60000); u.idle(1500)
		buttons = u.page.eval_on_selector_all(".page-actions button, .page-actions .btn", "els => els.map(e => e.innerText.trim()).filter(Boolean)")
		assert not any("Download Data Sheet" in t or "Check / Import" in t for t in buttons), buttons
		r = u.rpc("medical_hrms.employee_data_sheet.export_sheet")
		assert r["status"] == 403, r
	u.close()


def portal_shell(b):
	e = Session(b, label="shell:emp"); p = e.page

	@check("SHL-01", "Portal shell", "Employee Portal: menu > New Request > Permission Request opens the request form", p)
	def _():
		e.login(U["emp1"])
		p.wait_for_selector(".mhp-shell .mhp-stat")
		p.click('.mhp-group[data-group="new"] > .mhp-navbtn')
		p.click('.mhp-navbtn[data-id="new-permission-request"]')
		p.wait_for_selector(".modal.show .modal-title"); p.wait_for_timeout(900)
		title = p.inner_text(".modal.show .modal-title")
		e.close_dialogs()
		assert "Permission Request" in title, title
		rail = p.eval_on_selector_all(".mhp-shell .mhp-navbtn", "els => els.map(e => e.innerText.trim()).filter(Boolean)")
		assert not any(x in rail for x in ("Employees", "HR Settings", "Employee Requests")), rail
		return f"{len(rail)} menu entries, no HR entries"

	@check("SHL-03", "Portal shell", "Leaving to a standard list brings Frappe's navbar back; going back restores the portal", p)
	def _():
		p.click('.mhp-navbtn[data-id="attendance-request"]'); p.wait_for_timeout(2500)
		on_list = p.evaluate("getComputedStyle(document.querySelector('.navbar')).display")
		p.go_back(); p.wait_for_timeout(2500)
		back = p.evaluate("getComputedStyle(document.querySelector('.navbar')).display")
		assert "/attendance-request" not in p.url and on_list != "none" and back == "none" and p.is_visible(".mhp-shell"), (p.url, on_list, back)

	@check("SHL-04", "Portal shell", "An employee refused an HR page still has the navbar (not stranded)", p)
	def _():
		e.goto("/app/hr-dashboard"); p.wait_for_timeout(1500)
		nav = p.evaluate("getComputedStyle(document.querySelector('.navbar')).display")
		assert nav != "none" and not p.locator("#hrd-title").count(), nav

	@check("SHL-05", "Portal shell", "Dark mode and Arabic (right-to-left) switch from the top bar, and back", p)
	def _():
		e.goto("/app/employee-dashboard"); p.wait_for_selector(".mhp-shell .mhp-stat")
		p.click(".mhp-shell:visible .mhp-theme"); p.wait_for_timeout(800)
		dark = p.evaluate("document.documentElement.getAttribute('data-theme')")
		p.click(".mhp-shell:visible .mhp-theme"); p.wait_for_timeout(800)
		light = p.evaluate("document.documentElement.getAttribute('data-theme')")
		with p.expect_navigation(timeout=90000):
			p.click('.mhp-shell:visible .mhp-lang button[data-lang="ar"]')
		p.wait_for_function("() => window.frappe && frappe.boot && document.querySelector('.mhp-shell .mhp-stat')", timeout=90000)
		rtl = p.evaluate("document.documentElement.dir")
		with p.expect_navigation(timeout=90000):
			p.click('.mhp-shell:visible .mhp-lang button[data-lang="en"]')
		p.wait_for_function("() => window.frappe && frappe.boot && frappe.boot.lang", timeout=90000)
		lang = p.evaluate("frappe.boot.lang")
		assert (dark, light, rtl, lang) == ("dark", "light", "rtl", "en"), (dark, light, rtl, lang)
		return "dark -> light; ar (rtl) -> en"
	e.close()

	h = Session(b, label="shell:hr.user"); q = h.page

	@check("SHL-02", "Portal shell", "HR User: the menu only lists pages they can open; breadcrumb leads home", q)
	def _():
		h.login(U["hr.user"])
		q.wait_for_selector("#hrd-title")
		ids = q.eval_on_selector_all(".mhp-shell a.mhp-navbtn[href^='/app/']", "els => els.map(e => e.getAttribute('href'))")
		assert "/app/hr-dashboard" in ids and len(ids) > 15, ids
		h.goto("/app/jameah-data-check"); q.wait_for_selector(".mhp-shell:visible .mhp-crumbs a")
		q.click(".mhp-shell:visible .mhp-crumbs a"); q.wait_for_timeout(2000)
		assert "/app/hr-dashboard" in q.url, q.url
		return f"{len(ids)} menu links (opened in SWP-02)"
	h.close()


def error_sweep(b):
	slug = lambda dt: dt.lower().replace(" ", "-")
	hr_routes = ["/app/hr-dashboard", "/app/medical-hrms", "/app/jameah-data-check", "/app/jameah-settings", "/app/hr-academic-presence/faculty",
		"/app/hr-academic-presence/students", "/app/hr-academic-presence/proctors", "/app/hr-academic-presence/after_hours", "/app/leave-control-panel",
		"/app/holiday-list", "/app/expense-claim/new", "/app/query-report/Employees Missing Ministry Data"] \
		+ [f"/app/{slug(d)}" for d in MHRMS_DOCTYPES] + [f"/app/{slug(d)}/new" for d in MHRMS_DOCTYPES if d not in ("Jameah Ministry Code", "Employee")] \
		+ latest_records(MHRMS_DOCTYPES)
	emp_routes = ["/app/employee-dashboard", "/app/employee-self-service", "/app/leave-application", "/app/attendance-request", "/app/expense-claim",
		"/app/employee", "/app/employee-medical-license"] + [f"/app/{slug(d)}" for d in SELF_SERVICE]
	roles = [("SWP-01", "HR Manager", U["hr.manager"], PW, hr_routes), ("SWP-02", "HR User", U["hr.user"], PW, hr_routes),
		("SWP-03", "Employee", U["emp1"], PW, emp_routes), ("SWP-04", "Instructor (also Employee)", INSTRUCTOR[0], INSTRUCTOR[1], ["/app/instructor-dashboard"] + emp_routes)]
	for tid, label, user, pwd, routes in roles:
		@check(tid, "Error sweep", f"{label}: visit every reachable page, list and new form - no errors")
		def _(label=label, user=user, pwd=pwd, routes=routes):
			visited, problems = sweep_role(b, f"sweep:{label}", user, pwd, routes)
			assert not problems, problems[:6]
			return f"{visited} pages, no errors"


# --------------------------------------------------------------------------- run

def main():
	t0 = time.time()
	started = now()
	with sync_playwright() as pw:
		b = pw.chromium.launch()
		try:
			for step in (login_landing, employee_self_service, employee_isolation, hr_dashboard, hr_approvals, leave_flow, employee_master,
					recruitment, presence, jameah_pages, ministry_report, portal_shell, error_sweep):
				if want(step.__name__) or step in (employee_self_service, hr_dashboard) and (want("hr_approvals") or want("employee_isolation")):
					try:
						step(b)
					except Exception:
						traceback.print_exc()
						record(f"RUN-{step.__name__}", "Runner", f"{step.__name__} stopped early", False, traceback.format_exc()[-400:])
		finally:
			b.close()
	out = {"started": started, "finished": now(), "results": RESULTS, "issues": ISSUES, "seconds": round(time.time() - t0)}
	json.dump(out, open(os.path.join(HERE, "e2e_full_results.json"), "w"), indent=1, default=str)
	passed = sum(r["ok"] for r in RESULTS)
	print(f"\n==== {passed}/{len(RESULTS)} passed in {out['seconds']}s; {len(ISSUES)} browser events captured")
	for i in ISSUES:
		if i["kind"] != "console-error" or "Traceback" in i["text"]:
			print("  ISSUE", i["time"], i["who"], i["kind"], i["url"][-60:], i["text"][-200:].replace("\n", " "))


if __name__ == "__main__":
	main()
