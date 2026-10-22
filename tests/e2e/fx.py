"""Run a script inside the site, connected as Administrator. Rolls back unless QA_COMMIT=1.

    <bench>/env/bin/python tests/e2e/fx.py tests/e2e/qa_fixtures.py

QA_SITE (default site1.local) picks the site; QA_BENCH the bench folder (default: four levels up).
"""
import os
import runpy
import sys

SCRIPT = os.path.abspath(sys.argv[1])  # before the chdir below
BENCH = os.environ.get("QA_BENCH") or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
os.chdir(os.path.join(BENCH, "sites"))
import frappe  # noqa: E402

frappe.init(site=os.environ.get("QA_SITE", "site1.local"), sites_path=".")
frappe.connect()
frappe.set_user("Administrator")
try:
	runpy.run_path(SCRIPT, init_globals={"frappe": frappe}, run_name="__main__")
finally:
	frappe.db.commit() if os.environ.get("QA_COMMIT") else frappe.db.rollback()
	frappe.destroy()
