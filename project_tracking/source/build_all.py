"""Rebuild the three project tracking workbooks: Task Tracker, Test Cases, Checklist.

    python3 project_tracking/source/build_all.py

Before running: update the data files (tracker_data.py, testcases_data.py, checklist_data.py),
the dates in row_dates.py and add a line to changelog.py. Needs openpyxl.
"""
import os
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
for script in ("build_tracker.py", "build_testcases.py", "build_checklist.py"):
	runpy.run_path(os.path.join(HERE, script), run_name="__main__")
