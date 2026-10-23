"""Dated log of every change to Medical HRMS / Jameah, shown in all three project tracking workbooks.

Rule: every change adds a line here (newest first) AND updates the matching rows - with today's date -
in tracker_data.py, testcases_data.py and checklist_data.py. Then run build_all.py.
"""

# (date, area, items, what changed, by)
CHANGELOG = [
	("23 Oct 2026", "Project tracking", "All tasks; HR-04 - HR-06, HR-11, HR-12, HR-28 - HR-30, HR-48, HR-66, HR-70, HR-71, HR-73, JM-03, JM-06, JM-12, JM-13, JM-16, JM-17, B-26, B-34, CL-35",
		"Owners corrected: Abdul Hakeem designed and built Medical HRMS and Jameah and leads every development task. New column 'Assigned to' (with a dropdown) shows who a task was given to: Dinesh (HR-06, and HR-04 at first), Fathir (HR-04, HR-05, HR-70), otherwise Abdul Hakeem; client-side tasks stay with HR, Academic Affairs, the Registrar or the server admin. Wording that credited others for this work removed. Status and Priority shown in clear colours in all three workbooks (Status, Priority, Result and Severity cells only), with a priority legend in the Read Me.", "Abdul Hakeem"),
	("23 Oct 2026", "Project tracking", "HR-72, B-52, B-53",
		"The three check scripts (files, site, server methods) now record their result in the Test Cases workbook (Last automated run: Pass, 23 Oct). The file check found a missing import in the site check; fixed.", "Abdul Hakeem"),
	("23 Oct 2026", "Medical HRMS", "HR-58, HR-69, HR-71 - HR-73, B-45 - B-51, CL-01, CL-30, CL-34 - CL-36, TC-ERR-06 - TC-ERR-09, TC-SEC-10",
		"Every branch merged into develop (ministry-lookup last; employee-applicant recorded as merged without its July files, as decided); develop is now the branch to test and deploy. Full check of every file and page (files, site, server methods by role, unit tests, browser suite with a sweep of every Medical HRMS doctype); checks kept in tests/checks. Fixed: stray files, outdated README and developer guide, QA setup race, refresh-lock test, Ministry code search. HR-69 corrected (employee counts were test hires). Result: 95/95 browser checks (error sweep: 116 pages for HR, 20 for employees), 37/37 unit tests, 23/23 Ministry views, 29 server methods x 3 roles, 0 file and 0 site problems, no Error Log entries.", "Abdul Hakeem"),
	("22 Oct 2026", "Medical HRMS", "HR-58, HR-70, JM-05, JM-19, B-42 – B-44, TC-REC-13, TC-REC-14",
		"develop (Fathir's job application update, PR #2) merged into feature/uat-2026-10-22; conflicts in job_application.py, job-application.html and ar.csv resolved keeping both sides; the Appreciation list restored and the work extension accepted again on the updated form (B-42, B-44); a migrate no longer fails when it overlaps the hourly Jameah refresh (B-43); test output removed from the repository. Re-tested: 95/95 browser checks, 37/37 unit tests, 23/23 Ministry views OK, no Error Log entries. Branch to test and deploy: feature/uat-2026-10-22.", "Abdul Hakeem"),
	("22 Oct 2026", "Medical HRMS", "HR-08, HR-09, HR-19, HR-20, HR-22, HR-68, HR-69, B-36 – B-40, DEC-14, CL-28 – CL-33",
		"Leave made one flow: Leave Plan (employees send it; manager and department head approve) -> Leave Application (only leave the employee holds, with the days left; Apply now from an approved plan) -> Leave Return (asked for when a leave ends; certificate and occupational health only after sick leave). Sick-leave types renamed in pay order (Sick Leave 1 / 2 / 3) by a migration patch. HR Portal Leave section: setup check per company, daily leave counts, yearly setup in order. Arabic for 114 new texts. 5 unit tests and 7 browser tests (LV-01 - LV-07); test cases TC-LV-09 - 17, TC-HRD-06/07. Real company Al Riyada College still needs its leave setup (HR-69). Branch to test and deploy: feature/uat-2026-10-22 (all work to date).", "Abdul Hakeem"),
	("22 Oct 2026", "Testing", "HR-67, B-41", "Browser test suite, QA data scripts and the results helper kept in the repository (tests/e2e); the QA scripts only run on a site named in QA_TEST_SITE. The QA reset no longer leaves the QA HR User without access to its own My Settings (test data only). The leave unit test now attaches a real test file, so it no longer writes 'Error Attaching File' to the Error Log. Full run 22 Oct: 95/95 browser checks, 36/36 unit tests, 23/23 Ministry views OK, no new Error Log entries.", "Abdul Hakeem"),
	("21 Oct 2026", "Medical HRMS + Jameah", "HR-49, HR-50, HR-51, HR-65, JM-14, B-35, DEC-12, DEC-13",
		"Report 'Employees Missing Ministry Data'; data sheet for non-academic staff (download, check, import); unused duplicate applicant "
		"Ministry fields removed; Create Employee dialog asks for every field the Employee form requires; Jameah Faculty views (8) built and "
		"verified (23 views in all). Arabic for the 46 new labels. Documents moved to the project_tracking folder; Checklist workbook added; dates "
		"on every row; HRM_TASK_TRACKER.md marked as superseded.", "Abdul Hakeem"),
	("21 Oct 2026", "Medical HRMS", "HR-66",
		"HR Portal and Employee Portal in the new college portal design (menu, top bar, EN/AR, dark mode); Arabic translations for these pages.", "Abdul Hakeem"),
	("21 Oct 2026", "Medical HRMS + Jameah", "HR-12, HR-31, HR-32, HR-45, HR-46, HR-59 – HR-64, JM-17, JM-18, B-24 – B-34",
		"End-to-end test round 3 with an error sweep of every page: fixes for the errors the client reported (non-Saudi employees, "
		"breadcrumb 'Not permitted', Cost Center pop-up, academic hire e-mail, Holiday List); HR login lands on the HR Dashboard; Ministry GPA "
		"and credit hours from the college's official calculation. Test Report, Test Cases and Task Tracker created.", "Abdul Hakeem"),
	("20 Oct 2026", "Medical HRMS + Jameah", "HR-07 – HR-09, HR-13 – HR-15, HR-19, HR-22, HR-26, HR-36 – HR-44, JM-02 – JM-07, B-12 – B-23",
		"Jameah Employee (5) and Student (10) views built and verified value by value; Academic Presence; browser test round 2 fixes.", "Abdul Hakeem"),
	("19 Oct 2026", "Medical HRMS + Jameah", "HR-02, HR-05, HR-06, HR-24, HR-27, HR-33 – HR-35, JM-01, B-01 – B-11",
		"Browser end-to-end test round 1 and fixes (approvals, recruitment security, Ministry identity rules); Instructor data sheet; Jameah research.", "Abdul Hakeem"),
	("1 Oct 2026", "Medical HRMS", "HR-01 – HR-32", "First HRM task tracker (HRM_TASK_TRACKER.md / .csv).", "Team"),
]
