"""Site check of the app: every hook, scheduler job, override, asset and patch resolves; every Medical HRMS
doctype loads, its links / tables / fetch_from point at real doctypes and fields, its list query works and
each of its newest 25 saved records passes validate (rolled back); custom link fields, the report, the
pages' roles and the workspaces' links. Read-only (everything is rolled back).

    ../../env/bin/python tests/e2e/fx.py tests/checks/site.py
"""
import importlib, json, os
import frappe
from medical_hrms import hooks
bad, ok = [], 0
def resolve(path, where):
	global ok
	try:
		frappe.get_attr(path); ok += 1
	except Exception as e:
		bad.append(f"{where}: {path} -> {type(e).__name__}: {e}")
def walk(value, where):
	if isinstance(value, str):
		if "." in value and not value.endswith((".js", ".css", ".html", ".png", ".svg")) and "/" not in value and " " not in value:
			resolve(value, where)
	elif isinstance(value, (list, tuple)):
		for v in value: walk(v, where)
	elif isinstance(value, dict):
		for k, v in value.items(): walk(v, f"{where}[{k}]")
SKIP = {"app_name", "app_title", "app_publisher", "app_description", "app_email", "app_license", "app_version", "required_apps", "fixtures", "app_include_js", "app_include_css", "web_include_js", "web_include_css", "doctype_js", "doctype_list_js", "page_js", "website_route_rules", "app_logo_url", "add_to_apps_screen", "translated_search_doctypes"}
for name in dir(hooks):
	if name.startswith("_") or name in SKIP: continue
	walk(getattr(hooks, name), name)
# asset paths
app = frappe.get_app_path("medical_hrms")
for key in ("app_include_js", "app_include_css", "web_include_js", "web_include_css"):
	for p in (getattr(hooks, key, None) or []) if not isinstance(getattr(hooks, key, None), str) else [getattr(hooks, key)]:
		rel = p.split("?")[0].replace("/assets/medical_hrms/", "public/")
		if not os.path.exists(os.path.join(app, rel)): bad.append(f"{key}: missing file {p}")
		else: ok += 1
for key in ("doctype_js", "doctype_list_js", "page_js"):
	for dt, files in (getattr(hooks, key, None) or {}).items():
		for p in (files if isinstance(files, list) else [files]):
			if not os.path.exists(os.path.join(app, p)): bad.append(f"{key}[{dt}]: missing file {p}")
			else: ok += 1
		if key != "page_js" and not frappe.db.exists("DocType", dt): bad.append(f"{key}: doctype {dt} not on site")
# patches
for line in open(os.path.join(app, "patches.txt")):
	line = line.split("#")[0].strip()
	if not line or line.startswith("["): continue
	mod = line.split()[0]
	if mod.startswith("execute:"): continue
	try:
		m = importlib.import_module(mod); assert hasattr(m, "execute"), "no execute()"; ok += 1
	except Exception as e: bad.append(f"patches.txt: {mod} -> {e}")
hook_problems, hook_ok = bad, ok

problems, data_issues, ok = [], [], 0
dts = frappe.get_all("DocType", filters={"module": "Medical HRMS"}, fields=["name", "istable", "issingle", "is_submittable", "custom"], order_by="name")
print("doctypes in module:", len(dts), "| child:", sum(d.istable for d in dts), "| single:", sum(d.issingle for d in dts))
def check_fields(dt, fields):
	global ok
	for df in fields:
		ft, opt = df.fieldtype, (df.options or "").strip()
		if ft in ("Link", "Table", "Table MultiSelect") and opt and not frappe.db.exists("DocType", opt):
			problems.append(f"{dt}.{df.fieldname}: {ft} to missing doctype '{opt}'")
		elif ft in ("Table", "Table MultiSelect") and opt and not frappe.db.get_value("DocType", opt, "istable"):
			problems.append(f"{dt}.{df.fieldname}: Table options '{opt}' is not a child doctype")
		elif ft == "Select" and not opt and not df.get("is_custom_field"):
			data_issues.append(f"{dt}.{df.fieldname}: Select with no options")
		if df.fetch_from:
			src, _, target = df.fetch_from.partition(".")
			meta = frappe.get_meta(dt)
			link = meta.get_field(src)
			if not link: problems.append(f"{dt}.{df.fieldname}: fetch_from '{df.fetch_from}' - no field {src}")
			elif link.options and frappe.db.exists("DocType", link.options) and not frappe.get_meta(link.options).has_field(target) and target not in ("name", "owner", "creation", "modified"):
				problems.append(f"{dt}.{df.fieldname}: fetch_from '{df.fetch_from}' - {link.options} has no field {target}")
		ok += 1
for d in dts:
	try:
		meta = frappe.get_meta(d.name)
	except Exception as e:
		problems.append(f"{d.name}: meta does not load: {e}"); continue
	check_fields(d.name, meta.fields)
	if not d.istable and not meta.permissions:
		problems.append(f"{d.name}: no permission rows")
	if d.istable or d.issingle: continue
	try:
		names = frappe.get_all(d.name, pluck="name", limit=25, order_by="modified desc")
	except Exception as e:
		problems.append(f"{d.name}: list query fails: {e}"); continue
	try:
		frappe.new_doc(d.name)
	except Exception as e:
		problems.append(f"{d.name}: new_doc fails: {e}")
	for n in names:
		frappe.db.savepoint("chk")
		try:
			doc = frappe.get_doc(d.name, n)
			if doc.docstatus == 0:
				doc.run_method("validate")
		except frappe.ValidationError as e:
			data_issues.append(f"{d.name} {n}: {type(e).__name__}: {frappe.utils.strip_html(str(e))[:160]}")
		except Exception as e:
			problems.append(f"{d.name} {n}: {type(e).__name__}: {e} @ {traceback.format_exc().splitlines()[-3].strip()[:160]}")
		finally:
			frappe.db.rollback(save_point="chk"); frappe.local.message_log = []
# custom fields our app adds to other doctypes
cfs = frappe.get_all("Custom Field", filters={"fieldtype": ["in", ["Link", "Table", "Table MultiSelect"]]}, fields=["dt", "fieldname", "fieldtype", "options"])
for cf in cfs:
	if cf.options and not frappe.db.exists("DocType", cf.options.strip()):
		problems.append(f"Custom Field {cf.dt}.{cf.fieldname}: {cf.fieldtype} to missing doctype '{cf.options}'")
print("custom link/table fields checked:", len(cfs))
# reports
for r in frappe.get_all("Report", filters={"module": "Medical HRMS"}, fields=["name", "report_type", "ref_doctype"]):
	try:
		rep = frappe.get_doc("Report", r.name)
		if r.report_type == "Script Report":
			cols, rows = rep.get_data(filters={}, limit=50, as_dict=True)[:2] if False else rep.execute_script_report({})[:2]
			print(f"report {r.name}: {len(rows)} rows, {len(cols)} columns")
		ok += 1
	except Exception as e:
		problems.append(f"Report {r.name}: {type(e).__name__}: {e}")
# pages and workspace links
for p in frappe.get_all("Page", filters={"module": "Medical HRMS"}, fields=["name"]):
	roles = frappe.get_all("Has Role", filters={"parent": p.name, "parenttype": "Page"}, pluck="role")
	missing = [r for r in roles if not frappe.db.exists("Role", r)]
	print(f"page {p.name}: roles {roles}" + (f" MISSING {missing}" if missing else ""))
	if missing: problems.append(f"Page {p.name}: roles not on site {missing}")
for w in frappe.get_all("Workspace", filters={"module": "Medical HRMS"}, pluck="name"):
	ws = frappe.get_doc("Workspace", w)
	for l in list(ws.links) + list(ws.shortcuts):
		t, n = (l.get("link_type") or l.get("type")), (l.get("link_to"))
		if t in ("DocType", "Report", "Page") and n and not frappe.db.exists(t, n):
			problems.append(f"Workspace {w}: {t} '{n}' not found ({l.get('label')})")
	print(f"workspace {w}: {len(ws.links)} links, {len(ws.shortcuts)} shortcuts")
print("field/record checks:", ok)
problems = hook_problems + problems
print("hooks, assets, patches resolved:", hook_ok)
print("\nPROBLEMS (code / schema):", len(problems)); print("\n".join(problems))
print("\nDATA ISSUES (validation refused on existing records):", len(data_issues)); print("\n".join(sorted(set(data_issues))[:60]))
if problems:
	raise SystemExit(1)
