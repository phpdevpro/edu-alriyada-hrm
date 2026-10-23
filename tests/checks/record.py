"""Write a check's result where the Test Cases workbook reads it (project_tracking/source/automated_results.json,
key "checks"); then rebuild the workbooks with python3 project_tracking/source/build_all.py."""
import json
import os
from datetime import datetime, timedelta, timezone

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "project_tracking", "source", "automated_results.json")
AST = timezone(timedelta(hours=3))  # the college's time (Asia/Riyadh)


def record(script, ok):
	data = json.load(open(OUT)) if os.path.exists(OUT) else {}
	data.setdefault("checks", {})[f"tests/checks/{script}"] = {
		"result": "Pass" if ok else "Fail", "run_on": datetime.now(AST).strftime("%-d %b %Y %H:%M AST")}
	with open(OUT, "w") as f:
		json.dump(data, f, indent=1)


def record_from(script_file, ok):
	"""For scripts run through fx.py / runpy (no package import): record(<this script's file name>, ok)."""
	record(os.path.basename(script_file), ok)
