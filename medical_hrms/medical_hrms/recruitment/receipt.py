# Copyright (c) 2026, Admin and contributors
# For license information, please see license.txt

"""Application receipt: a branded PDF the applicant downloads after submitting the public form.

The PDF is rendered from the saved Employee Job Applicant record (not from anything the browser
sends), and the download link is protected by a key that only the submit response carries.
"""

import base64
import hashlib
import hmac
import io
import mimetypes
import os
from html import escape

import frappe
from frappe import _
from frappe.utils import formatdate, get_datetime
from frappe.utils.password import get_encryption_key

APPLICANT_DOCTYPE = "Employee Job Applicant"
CODE_DOCTYPE = "Jameah Ministry Code"
PUBLIC_DIR = frappe.get_app_path("medical_hrms", "public")
LOGO_PATH = ("education", "public", "images", "rchs-logo.png")
ARABIC_LETTERS = range(0x0600, 0x0700)


def receipt_key(name):
	"""Per-record secret for the download link; nothing is stored, it is derived from the site key."""
	secret = get_encryption_key().encode()
	return hmac.new(secret, f"job-receipt:{name}".encode(), hashlib.sha256).hexdigest()[:32]


@frappe.whitelist(allow_guest=True)
def download_receipt(name=None, key=None, lang=None):
	if not name or not key or not hmac.compare_digest(str(key), receipt_key(name)):
		frappe.throw(_("This download link is not valid."), frappe.PermissionError)
	if not frappe.db.exists(APPLICANT_DOCTYPE, name):
		frappe.throw(_("Application not found."), frappe.DoesNotExistError)
	if lang in ("en", "ar"):
		frappe.local.lang = lang

	doc = frappe.get_doc(APPLICANT_DOCTYPE, name)
	frappe.local.response.filename = f"Application-{name}.pdf"
	frappe.local.response.filecontent = render_pdf(doc)
	frappe.local.response.type = "pdf"


# ---------------------------------------------------------------- data helpers


def _has_arabic(text):
	return any(ord(ch) in ARABIC_LETTERS for ch in (text or ""))


def _numeric_only(text):
	return all(ch.isdigit() or ch in " .-" for ch in (text or ""))


def code_label(code_name, arabic_ui):
	"""Readable name for a Jameah Ministry Code (same rules as the public form)."""
	if not code_name:
		return ""
	row = frappe.db.get_value(
		CODE_DOCTYPE, code_name, ["name_english", "name_arabic", "ministry_code"], as_dict=True
	)
	if not row:
		return code_name
	en = (row.name_english or "").strip()
	ar = (row.name_arabic or "").strip()
	if ar.lower() in ("undefined", "null"):
		ar = _("Not specified")
	ident = (row.ministry_code or code_name.split("::")[-1]).strip().lower()
	en_missing = not en or _numeric_only(en) or en.lower() == ident
	ar_missing = not ar or _numeric_only(ar) or ar.lower() == ident
	if arabic_ui and _has_arabic(ar):
		return ar
	if not en_missing:
		return en
	if not ar_missing:
		return ar
	return en or ar or code_name


def _join(doc, fields):
	return " ".join((doc.get(f) or "").strip() for f in fields if (doc.get(f) or "").strip())


def _fmt_date(value):
	return formatdate(value) if value else ""


def _qr_data_uri(text):
	try:
		import qrcode
		import qrcode.image.svg

		image = qrcode.make(text, image_factory=qrcode.image.svg.SvgPathImage, box_size=8, border=0)
		buffer = io.BytesIO()
		image.save(buffer)
		return "data:image/svg+xml;base64," + base64.b64encode(buffer.getvalue()).decode()
	except Exception:
		return ""


def _logo_data_uri():
	path = frappe.get_app_path(LOGO_PATH[0], *LOGO_PATH[1:])
	if not os.path.exists(path):
		return ""
	mime = mimetypes.guess_type(path)[0] or "image/png"
	with open(path, "rb") as handle:
		return f"data:{mime};base64," + base64.b64encode(handle.read()).decode()


# ---------------------------------------------------------------- rendering


def render_pdf(doc):
	from weasyprint import HTML

	def fetch(url, *args, **kwargs):
		# only inline data and our own bundled fonts may be loaded
		from weasyprint import default_url_fetcher

		if url.startswith("data:") or url.startswith("file://" + PUBLIC_DIR):
			return default_url_fetcher(url, *args, **kwargs)
		raise ValueError("External resources are not allowed in the receipt")

	html = build_html(doc)
	return HTML(string=html, base_url=PUBLIC_DIR + "/", url_fetcher=fetch).write_pdf()


def _rows(doc, table, columns, arabic_ui, code_cols=()):
	out = []
	for row in doc.get(table) or []:
		cells = []
		for col in columns:
			value = row.get(col)
			if col in code_cols:
				value = code_label(value, arabic_ui)
			elif col.endswith("date") or col in ("date",):
				value = _fmt_date(value)
			cells.append(escape(str(value)) if value not in (None, "") else "")
		if any(cells):
			out.append(cells)
	return out


def _list_card(title, icon, header, rows):
	if not rows:
		return ""
	head = "".join(f"<th>{escape(h)}</th>" for h in header)
	body = "".join("<tr>" + "".join(f"<td>{c or '&mdash;'}</td>" for c in r) + "</tr>" for r in rows)
	return (
		f'<div class="card"><div class="card-title"><span class="ico">{icon}</span>{escape(title)}'
		f'<span class="count">{len(rows)}</span></div>'
		f'<table class="list"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
	)


ICON_PATHS = {
	'user': '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
	'brief': '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
	'book': '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
	'award': '<circle cx="12" cy="8" r="7"/><path d="M8.2 13.9 7 23l5-3 5 3-1.2-9.1"/>',
	'check': '<path d="M20 6 9 17l-5-5"/>',
	'mail': '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>',
	'eye': '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z"/><circle cx="12" cy="12" r="3"/>',
}


def icon(name, color="#054C82", width=2):
	return (
		'<svg viewBox="0 0 24 24" width="100%" height="100%" fill="none" stroke="' + color + '" '
		'stroke-width="' + str(width) + '" stroke-linecap="round" stroke-linejoin="round">' + ICON_PATHS[name] + '</svg>'
	)


def build_html(doc):
	lang = (frappe.local.lang or "en").lower()
	ar = lang.startswith("ar")
	direction = "rtl" if ar else "ltr"

	name_en = _join(doc, ["custom_first_name_en", "custom_second_name_en", "custom_third_name_en", "custom_last_name_en"])
	name_ar = _join(doc, ["custom_first_name_ar", "custom_second_name_ar", "custom_third_name_ar", "custom_last_name_ar"])
	display_name = (name_ar if ar and name_ar else name_en) or doc.applicant_name or ""
	submitted = get_datetime(doc.creation).strftime("%d %b %Y, %H:%M")

	phone = doc.phone_number or ""
	salary = ""
	if doc.expected_salary:
		salary = f"{doc.expected_salary:,.2f} {doc.currency or ''}".strip()

	def pair(label, value, required=False):
		if not value and not required:
			return ""
		shown = f"<bdi>{escape(str(value))}</bdi>" if value else "&mdash;"
		return f"<tr><th>{escape(label)}</th><td>{shown}</td></tr>"

	person = "".join(
		[
			pair(_("Name (English)"), name_en, True),
			pair(_("Name (Arabic)"), name_ar),
			pair(_("Email"), doc.email_id, True),
			pair(_("Phone"), phone, True),
			pair(_("Date of Birth"), _fmt_date(doc.date_of_birth)),
			pair(_("Gender"), code_label(doc.gender, ar)),
			pair(_("Nationality"), code_label(doc.custom_jameah_nationality, ar)),
			pair(_("Identity Number"), doc.custom_identity_number or doc.nic_passport),
			pair(_("Expected Salary"), salary),
		]
	)

	qualifications = _list_card(
		_("Academic Qualifications"),
		icon("book"),
		[_("Academic Qualification"), _("General Specialization"), _("Graduation Place"), _("Graduation Year (AD)")],
		_rows(doc, "academic_qualifications", ["degree", "specialization", "institute", "graduation_year"], ar, ("degree", "specialization")),
	)
	work_rows = _rows(doc, "academic_work_experience", ["designation", "institute_code", "start_date", "end_date"], ar, ("institute_code",))
	work_rows += _rows(doc, "previous_work_experience", ["profession", "organization_name", "start_work_date", "end_work_date"], ar)
	experience = _list_card(
		_("Work Experience"),
		icon("brief"),
		[_("Job Title"), _("Organization"), _("Start Date"), _("End of Work Date")],
		work_rows,
	)
	extras = _list_card(
		_("Courses, research and awards"),
		icon("award"),
		[_("Title"), _("Provider"), _("Type")],
		[[c[0], c[1], _("Course")] for c in _rows(doc, "professional_certificates_training", ["course_name", "provider"], ar)]
		+ [[c[0], c[1], _("Publication")] for c in _rows(doc, "research_publications", ["title", "journal"], ar)]
		+ [[c[0], c[1], _("Award")] for c in _rows(doc, "awards", ["award_name", "organization"], ar)],
	)

	logo = _logo_data_uri()
	qr = _qr_data_uri(doc.name)
	role = _(doc.role) if doc.role else _("General application")
	category = _(doc.application_category) if doc.application_category else ""

	steps = [
		(icon("check", "#fff", 2.6), _("Application received"), _("Your application is in our system.")),
		(icon("eye", "#fff", 2.2), _("HR review"), _("We check your details and qualifications.")),
		(icon("mail", "#fff", 2.2), _("We contact you"), _("You will hear from us at the email you provided.")),
	]
	steps_html = "".join(
		f'<td class="step"><div class="step-ico">{i}</div><div class="step-t">{escape(t)}</div><div class="step-d">{escape(d)}</div></td>'
		for i, t, d in steps
	)

	css = _css(direction)
	return f"""<!doctype html>
<html lang="{lang}" dir="{direction}"><head><meta charset="utf-8"><title>{escape(doc.name)}</title><style>{css}</style></head>
<body>
<div class="hero">
	<svg class="mark" viewBox="0 0 520 520" fill="none"><path d="M100 260C100 176 168 108 252 108C300 108 342 130 368 166" stroke="#fff" stroke-width="10" stroke-linecap="round"/><path d="M420 260C420 344 352 412 268 412C220 412 178 390 152 354" stroke="#fff" stroke-width="10" stroke-linecap="round"/><circle cx="260" cy="260" r="150" stroke="#fff" stroke-width="2" stroke-dasharray="2 10"/></svg>
	<table class="brand"><tr>
		<td class="logo-cell">{f'<img class="logo" src="{logo}">' if logo else ''}</td>
		<td><div class="wm">RCHS</div><div class="wm-sub">Al-Riyada College for Health Sciences</div><div class="wm-sub ar">كلية الريادة للعلوم الصحية</div></td>
		<td class="doc-title"><div class="doc-eyebrow">{escape(_("Application receipt"))}</div><div class="doc-name">{escape(_("Employee Job Application"))}</div></td>
	</tr></table>
</div>

<div class="wrap">
	<div class="ref-card"><table><tr>
		<td class="ref-main">
			<div class="seal">{icon("check", "#0b7a71", 3)}</div>
			<div class="ref-head">{escape(_("Application submitted!"))}</div>
			<div class="ref-sub">{escape(_("Thank you for applying. Our HR team will review your application and contact you by email."))}</div>
		</td>
		<td class="ref-side">
			<div class="ref-label">{escape(_("Reference"))}</div>
			<div class="ref-code"><bdi>{escape(doc.name)}</bdi></div>
			<div class="ref-date">{escape(_("Submitted on"))} <bdi>{escape(submitted)}</bdi></div>
			{f'<img class="qr" src="{qr}">' if qr else ''}
		</td>
	</tr></table></div>

	<div class="apply">
		<div class="apply-label">{escape(_("You are applying for"))}</div>
		<div class="apply-role">{escape(role)}</div>
		{f'<span class="chip">{escape(category)}</span>' if category else ''}
		<span class="chip soft">{escape(_("Status"))}: {escape(_(doc.status or "Pending"))}</span>
	</div>

	<div class="card"><div class="card-title"><span class="ico">{icon("user")}</span>{escape(_("Applicant"))}</div>
		<div class="who">{escape(display_name)}</div>
		<table class="kv">{person}</table></div>

	{qualifications}
	{experience}
	{extras}

	<div class="card next"><div class="card-title">{escape(_("What happens next"))}</div>
		<table class="steps"><tr>{steps_html}</tr></table></div>

	<div class="note">{escape(_("Keep this file and your reference number for your records."))}<br>
	{escape(_("Your details are private and are only seen by the HR department."))}</div>
</div>
</body></html>"""


def _css(direction):
	start, end = ("left", "right") if direction == "ltr" else ("right", "left")
	fonts = """
@font-face{font-family:'Inter';font-weight:400;src:url('fonts/inter-latin-400-normal.woff')}
@font-face{font-family:'Inter';font-weight:600;src:url('fonts/inter-latin-600-normal.woff')}
@font-face{font-family:'Inter';font-weight:700;src:url('fonts/inter-latin-700-normal.woff')}
@font-face{font-family:'Space Grotesk';font-weight:600;src:url('fonts/space-grotesk-latin-600-normal.woff')}
@font-face{font-family:'Space Grotesk';font-weight:700;src:url('fonts/space-grotesk-latin-700-normal.woff')}
@font-face{font-family:'Plex Arabic';font-weight:400;src:url('fonts/ibm-plex-sans-arabic-arabic-400-normal.woff')}
@font-face{font-family:'Plex Arabic';font-weight:600;src:url('fonts/ibm-plex-sans-arabic-arabic-600-normal.woff')}
@font-face{font-family:'Plex Arabic';font-weight:700;src:url('fonts/ibm-plex-sans-arabic-arabic-700-normal.woff')}
"""
	return fonts + f"""
@page {{ size: A4; margin: 14mm 0 18mm 0;
  @bottom-center {{ content: "RCHS  \\00b7  " counter(page) " / " counter(pages); font: 600 8pt 'Inter','Plex Arabic',sans-serif; color:#5C7488; }} }}
@page :first {{ margin-top: 0; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; font-family:'Inter','Plex Arabic',sans-serif; font-size:9.5pt; color:#0A2036; direction:{direction}; }}
.hero {{ position:relative; overflow:hidden; background:linear-gradient(160deg,#0769B2 0%,#054C82 58%,#062741 100%); color:#fff; padding:13mm 16mm 26mm; }}
.hero .mark {{ position:absolute; {end}:-30mm; top:-24mm; width:120mm; height:120mm; opacity:.10; }}
table {{ border-collapse:collapse; }}
.brand {{ width:100%; position:relative; }}
.brand td {{ vertical-align:middle; }}
.logo-cell {{ width:20mm; }}
.logo {{ width:16mm; height:16mm; background:#fff; border-radius:4mm; padding:1.6mm; }}
.wm {{ font:700 20pt 'Space Grotesk','Inter',sans-serif; letter-spacing:.05em; }}
.wm-sub {{ font-size:8.5pt; opacity:.8; margin-top:.5mm; }}
.wm-sub.ar {{ font-family:'Plex Arabic',sans-serif; }}
.doc-title {{ text-align:{end}; }}
.doc-eyebrow {{ font:600 8pt 'Space Grotesk','Plex Arabic',sans-serif; letter-spacing:.14em; text-transform:uppercase; color:#DFF5F2; }}
.doc-name {{ font:700 13pt 'Space Grotesk','Plex Arabic',sans-serif; margin-top:1mm; }}
.wrap {{ padding:0 16mm; }}
.ref-card {{ margin-top:-17mm; position:relative; background:#fff; border:1px solid #E1EAF2; border-radius:4mm; padding:6mm 7mm; }}
.ref-card table {{ width:100%; }}
.ref-card td {{ vertical-align:top; }}
.ref-main {{ width:58%; }}
.seal {{ width:12mm; height:12mm; border-radius:50%; background:#DFF5F2; border:1.1mm solid #13AFA3; padding:1.7mm; }}
.ref-head {{ font:700 16pt 'Space Grotesk','Plex Arabic',sans-serif; margin-top:3mm; color:#0A2036; }}
.ref-sub {{ color:#5C7488; margin-top:1.5mm; line-height:1.55; }}
.ref-side {{ text-align:center; background:#F3F8FC; border:1px dashed #0769B2; border-radius:3mm; padding:4mm; }}
.ref-label {{ font:600 7.5pt 'Space Grotesk','Plex Arabic',sans-serif; letter-spacing:.14em; text-transform:uppercase; color:#5C7488; }}
.ref-code {{ font:700 15pt 'Space Grotesk','Inter',sans-serif; color:#054C82; margin:1.5mm 0; direction:ltr; }}
.ref-date {{ font-size:8pt; color:#5C7488; }}
.qr {{ width:22mm; height:22mm; margin-top:3mm; }}
.apply {{ margin-top:5mm; border-radius:4mm; padding:5mm 7mm; color:#fff; background:linear-gradient(135deg,#054C82,#0769B2); border-{start}:2mm solid #5eead4; }}
.apply-label {{ font:700 7.5pt 'Space Grotesk','Plex Arabic',sans-serif; letter-spacing:.14em; text-transform:uppercase; color:#a7f3e6; }}
.apply-role {{ font:700 17pt 'Space Grotesk','Plex Arabic',sans-serif; margin:1.5mm 0 2.5mm; }}
.chip {{ display:inline-block; background:#fff; color:#054C82; border-radius:6mm; padding:.8mm 3.5mm; font-weight:700; font-size:8pt; margin-{end}:2mm; }}
.chip.soft {{ background:rgba(255,255,255,.18); color:#fff; }}
.card {{ margin-top:5mm; border:1px solid #E1EAF2; border-radius:4mm; padding:5mm 6mm; page-break-inside:avoid; }}
.card-title {{ font:700 9pt 'Space Grotesk','Plex Arabic',sans-serif; letter-spacing:.06em; text-transform:uppercase; color:#054C82; margin-bottom:3mm; }}
.card-title .ico {{ display:inline-block; width:5mm; height:5mm; border-radius:1.6mm; background:#E8F1F9; padding:1mm; vertical-align:middle; margin-{end}:2mm; }}
.count {{ margin-{start}:2mm; background:#DFF5F2; color:#0b7a71; border-radius:4mm; padding:.4mm 2.2mm; font-size:7.5pt; }}
.who {{ font:700 14pt 'Space Grotesk','Plex Arabic',sans-serif; margin-bottom:2.5mm; }}
.kv {{ width:100%; }}
.kv th, .kv td {{ padding:1.9mm 0; border-top:1px solid #EEF3F8; text-align:start; vertical-align:top; }}
.kv th {{ width:34%; color:#5C7488; font-weight:600; font-size:8.5pt; }}
.list {{ width:100%; }}
.list th {{ text-align:start; font-size:7.5pt; color:#5C7488; text-transform:uppercase; letter-spacing:.05em; padding:0 2mm 1.6mm 0; border-bottom:1.5px solid #E1EAF2; }}
.list td {{ padding:2mm 2mm 2mm 0; border-bottom:1px solid #EEF3F8; font-size:9pt; vertical-align:top; }}
.next {{ background:#F8FBFE; }}
.steps {{ width:100%; table-layout:fixed; }}
.step {{ vertical-align:top; padding-{end}:4mm; }}
.step-ico {{ width:8mm; height:8mm; border-radius:50%; background:#0769B2; padding:1.9mm; margin-bottom:2mm; }}
.step-t {{ font-weight:700; font-size:9.5pt; }}
.step-d {{ color:#5C7488; font-size:8.5pt; margin-top:.8mm; line-height:1.45; }}
.note {{ margin:6mm 0 0; padding-top:4mm; border-top:1px solid #E1EAF2; color:#5C7488; font-size:8.5pt; line-height:1.7; text-align:center; }}
"""
