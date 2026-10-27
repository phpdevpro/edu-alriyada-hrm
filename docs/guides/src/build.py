"""Build the PDF guides from the HTML sources in this folder.

    <python with playwright>/bin/python docs/guides/src/build.py

Needs Playwright with Chromium (the same setup as the browser tests: tests/e2e/README.md). Writes the PDFs in
docs/guides: Installation and Setup Guide, User Guide, and one "What's New" document per testing round.
Screenshots are in docs/guides/images (taken from the test site with QA test data only).
"""
import os

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
GUIDES = [
	("installation.html", "Medical_HRMS_Jameah_Installation_Guide.pdf", "Installation and Setup Guide"),
	("user.html", "Medical_HRMS_Jameah_User_Guide.pdf", "User Guide"),
	# one short document per testing round: only that round's changes and its test cases
	("round2.html", "Medical_HRMS_Round_2_Whats_New.pdf", "Round 2: What's New"),
	("round3.html", "Medical_HRMS_Round_3_Whats_New.pdf", "Round 3: What's New"),
]
FOOTER = """<div style="width:100%; padding:0 15mm; font-family:'Ubuntu Sans','DejaVu Sans',sans-serif; font-size:7.5pt; color:#5d6b66;
	display:flex; justify-content:space-between;"><span>Medical HRMS &amp; Jameah · {title} · 27 Oct 2026</span>
	<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>"""

with sync_playwright() as pw:
	browser = pw.chromium.launch()
	page = browser.new_page()
	for source, target, title in GUIDES:
		page.goto("file://" + os.path.join(HERE, source))
		page.wait_for_load_state("networkidle")
		page.evaluate("document.fonts.ready")
		options = dict(path=os.path.join(OUT, target), prefer_css_page_size=True, print_background=True,
			display_header_footer=True, header_template="<div></div>", footer_template=FOOTER.format(title=title))
		try:
			page.pdf(**options, outline=True, tagged=True)  # bookmarks for the headings (newer Playwright)
		except TypeError:
			page.pdf(**options)
		print("written", target)
	browser.close()
