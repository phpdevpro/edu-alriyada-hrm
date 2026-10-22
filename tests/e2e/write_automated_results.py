"""Copy the last browser run into the Test Cases workbook data.

    python3 tests/e2e/write_automated_results.py [results.json ...]   # default: e2e_full_results.json here
    python3 project_tracking/source/build_all.py

Later files win when the same check appears twice (e.g. a section re-run after a test fix).
"""
import json
import os
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "project_tracking", "source", "automated_results.json")
# Run times are the test machine's clock; QA_UTC_OFFSET is its offset from the college (AST, UTC+3) in minutes.
OFFSET = int(os.environ.get("QA_UTC_OFFSET", "150"))

files = sys.argv[1:] or [os.path.join(HERE, "e2e_full_results.json")]
results, started = {}, None
for f in files:
	run = json.load(open(f))
	started = started or run["started"]
	for r in run["results"]:
		results[r["id"]] = "Pass" if r["ok"] else "Fail"
when = datetime.strptime(started, "%Y-%m-%d %H:%M:%S") - timedelta(minutes=OFFSET)
passed = sum(v == "Pass" for v in results.values())
out = {"run_on": f"{when:%-d %b %Y %H:%M} AST", "summary": f"{passed}/{len(results)} browser checks passed", "results": dict(sorted(results.items()))}
json.dump(out, open(OUT, "w"), indent=1)
print(out["run_on"], out["summary"])
