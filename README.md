### Medical HRMS

HR app for Al-Riyada College for Health Sciences (RCHS), on Frappe / ERPNext / HRMS v15 with the `education` app.
Customisations live here; the core `hrms` and `education` apps are not modified.

What it contains:

- **Employee Portal** (`/app/employee-dashboard`): 11 self-service requests, the leave flow
  (Leave Plan → Leave Application → Leave Return), balances and monthly limits.
- **HR Portal** (`/app/hr-dashboard`): requests to process, leave setup check and Sick Leave year,
  recruitment, Ministry (Jameah) data, Academic Presence (`/app/hr-academic-presence`).
- **Recruitment**: Job Application Links, the public form `/job-application/<token>` (steps, phone
  country codes, PDF receipt), Employee Job Applicant → Create Employee (+ Instructor / Advisor records).
- **Leave**: editable starter leave types and policies, Sick Leave in 3 pay stages with a separate sick
  year, monthly half-day / work-from-home limits (`setup_leave_defaults.py`, `medical_leave.py`,
  `monthly_leave_policy.py`).
- **Ministry (Jameah)**: Ministry lookup codes on Employee, and 23 read-only database views for the
  Ministry's Jameah agent (Employees 5, Faculty 8, Students 10). See `medical_hrms/jameah/README.md`.
- **Own-record security**: employees see and file only their own requests, records and files.

### Branches and team workflow

- `develop` is the main branch. Every change goes on a branch from `develop`
  (`feature/<name>` or `fix/<name>`) and comes back through a pull request.
- Merge, never rebase, `develop`: it is shared, and a rebase rewrites history the team already has.
- Before a pull request: run the tests below, and update the project tracking documents
  (`project_tracking/`: Task Tracker, Test Cases, Checklist; every changed row dated, plus a
  Change Log line). Rebuild them with `python3 project_tracking/source/build_all.py`.
- The Task Tracker shows the owner of each task (who leads it) and `Assigned to` (who it was given to; the lead picks it from a dropdown).

### Install / deploy

Prerequisites in the bench: `frappe`, `erpnext`, `hrms`, `education`.

```bash
bench get-app <this repo URL> --branch develop     # first time only
bench --site <site> install-app medical_hrms       # first time only
bench --site <site> migrate
bench build --app medical_hrms
bench --site <site> clear-cache && bench restart
```

`migrate` does all the setup (see `after_migrate` in `hooks.py`): Ministry codes, Ministry and Jameah
fields on Employee / Instructor, Jameah doctypes and views, HR permissions, the Employee Self Service
workspace, starter leave records, and the patches in `patches.txt`. Read its output: it must finish
without a traceback.

Do **not** run the old one-off setup scripts that earlier versions of this README listed
(`configure_hrm_request_governance`, `quick_grant_hr_permissions`, `apply_hr_workspace_layout`):
the doctypes now carry their permissions, and `configure_hrm_request_governance` replaces them with
custom permission rows.

After a deploy, check: `bench --site <site> execute medical_hrms.jameah.verify.run` (every view OK).
A long-queue worker and the scheduler must run (the Jameah academic summary refreshes hourly).

### Testing

```bash
# unit tests (run from the bench; site must allow tests, or use the runner in tests/e2e/README.md)
bench --site <site> run-tests --app medical_hrms
# Ministry views, value by value against the source records
bench --site <site> execute medical_hrms.jameah.verify.run
```

Browser end-to-end tests (95 checks, plus an error sweep of every app page, list and form per role):
see `tests/e2e/README.md`. Test sites only.

### Ministry codes from Excel

`medical_hrms.ministry_codes.sync` loads `medical_hrms/data/ministry_codes.csv` on every migrate.
To load a new Ministry workbook:

```bash
bench --site <site> execute medical_hrms.import_ministry_excel_to_jameah_codes.execute --kwargs "{'file_path':'/absolute/path/Ministry Code - (Translated).xlsx'}"
bench --site <site> clear-cache
```

Mapping: sheet tab → `code_category`; column A → `ministry_code`; B → `name_arabic`; C → `name_english`.

### Documents

Current:

- `docs/guides/`: **Installation and Setup Guide** and **User Guide** (PDF) for the server admin, HR, managers,
  employees and testers; HTML sources and `build.py` in `docs/guides/src`.
- `project_tracking/`: Task Tracker, Test Cases, Checklist (with Change Log). The task register.
- `DEVELOPER_SETUP.md`: architecture, approval limits, leave starter records.
- `medical_hrms/jameah/README.md`, `medical_hrms/jameah/VIEWS.md`: Ministry views and their columns.
- `JOB_APPLICANT_TO_EMPLOYEE_TRANSFER_MAPPING.md`: which applicant field goes to which Employee field.
- `tests/e2e/README.md`: browser tests.

Historical (May–Oct 2026, kept for reference; superseded by `project_tracking/`):
`HRM_TASK_TRACKER.md` / `.csv`, `HRM_PROGRESS_SIMPLE.csv`, `ENTIRE_HRMS_USER_GUIDE.md`,
`HRM_APPROVAL_MATRIX.md`, `HRM_HANDOFF_BOUNDARIES.md`, `HRM_OPERATIONS_SOP.md`, `HRM_UAT_SCENARIOS.md`,
`JAMEAH_HRMS_*.md`, and the `HRM ... Integration` HTML documents.

### Troubleshooting: App Not In apps.txt

If installation fails with `App medical_hrms not in apps.txt`, put each app on its own line in
`sites/apps.txt` (frappe, erpnext, payments, education, hrms, medical_hrms), then install and migrate.

### Contributing

`pre-commit` runs ruff, eslint, prettier and pyupgrade:

```bash
cd apps/medical_hrms
pre-commit install
```

### License

mit
