# Browser end-to-end tests (Medical HRMS + Jameah)

A real browser (Playwright, headless Chromium) works through every HR and employee function,
recruitment, Academic Presence, the Jameah pages, the HR / Employee Portal, and an error sweep of
every reachable page per role: for HR Manager and HR User every Medical HRMS doctype (list, new form and its
newest saved record), the four pages, the report and both workspaces; for employees their own request lists. Each check records pass / fail with the time; every error pop-up,
script error and server error is captured with its time and page.

**Test sites only.** `qa_fixtures.py` creates QA logins with known passwords (`@rchs-qa.test`), so it
and `qa_cleanup.py` refuse to run unless the site is named in `QA_TEST_SITE`. Never on production.

## Setup (once)

    python3 -m venv ~/.qa-venv && ~/.qa-venv/bin/pip install playwright && ~/.qa-venv/bin/playwright install chromium

## Run (bench running on :8000)

    cd apps/medical_hrms
    export QA_TEST_SITE=site1.local
    QA_COMMIT=1 ../../env/bin/python tests/e2e/fx.py tests/e2e/qa_fixtures.py      # QA logins, employees, leave
    ~/.qa-venv/bin/python tests/e2e/e2e_full.py                                    # all sections (~20 min)
    ~/.qa-venv/bin/python tests/e2e/e2e_full.py recruitment jameah_pages            # or chosen sections
    python3 tests/e2e/write_automated_results.py && python3 project_tracking/source/build_all.py
    QA_CLEAN=all QA_COMMIT=1 ../../env/bin/python tests/e2e/fx.py tests/e2e/qa_cleanup.py   # remove QA data

Results: `tests/e2e/e2e_full_results.json` (and screenshots of failures in `tests/e2e/e2e_shots/`),
not committed. `QA_BASE` changes the site address, `QA_SITE` the site.

Unit tests and the Ministry view check run separately:

    bench --site site1.local run-tests --module medical_hrms.jameah.test_jameah
    bench --site site1.local execute medical_hrms.jameah.verify.run

## Notes

- Start a full run just after the hourly Jameah academic summary refresh has finished (Scheduled Job
  `summary.refresh`): while it runs (10-13 minutes on an 8 GB machine) pages load slowly and checks time out.
- `qa_cleanup.py` runs the follow-up jobs of its deletions at once (shares, versions, linked Contacts).
  Left to the background worker they ran a few seconds later and changed the QA users that
  `qa_fixtures.py` had just created again.
- Notifications (Round 2) are made by a background worker after each save; the tests poll for them. The QA
  logins have e-mail notifications switched off, but non-QA HR logins on a copy still get e-mails queued; a copy
  that cannot send e-mail (B-25) logs "Failed to decrypt key Email Account.Notifications.password" for each.
  Leave applications also queue HRMS's leave e-mails (to the QA leave approver and employee), with the same error.
  `qa_cleanup.py` removes the QA records' notifications and stops their unsent e-mails (status Error, not deleted:
  the e-mail job may be sending them at that moment).
- `qa.academic.admin` (Education Manager + HR User) links an Employee on the Instructor form (REC-11, B-26);
  it cannot read the Gender Edu list, so the server fills Gender on save.
- The application form is a step-by-step wizard: `walk_to_review()` clicks Next through the steps and ticks
  the consent, like an applicant. English names must be letters only.
- `staff_hr` (Round 3, HR-11) checks the My HR card on the education dashboards with `qa.instructor` (kept),
  `qa.hod` (Head of Nursing Department + Instructor, with an Employee record and annual leave), `qa.dean` (Dean)
  and `qa.staff.nolink` (Instructor without an Employee record: no card). SHR-08 switches the language to Arabic
  from the dashboard's top bar and back to English.
