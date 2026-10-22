# Browser end-to-end tests (Medical HRMS + Jameah)

A real browser (Playwright, headless Chromium) works through every HR and employee function,
recruitment, Academic Presence, the Jameah pages, the HR / Employee Portal, and an error sweep of
every reachable page per role. Each check records pass / fail with the time; every error pop-up,
script error and server error is captured with its time and page.

**Test sites only.** `qa_fixtures.py` creates QA logins with known passwords (`@rchs-qa.test`), so it
and `qa_cleanup.py` refuse to run unless the site is named in `QA_TEST_SITE`. Never on production.

## Setup (once)

    python3 -m venv ~/.qa-venv && ~/.qa-venv/bin/pip install playwright && ~/.qa-venv/bin/playwright install chromium

## Run (bench running on :8000)

    cd apps/medical_hrms
    export QA_TEST_SITE=site1.local
    QA_COMMIT=1 ../../env/bin/python tests/e2e/fx.py tests/e2e/qa_fixtures.py      # QA logins, employees, leave
    ~/.qa-venv/bin/python tests/e2e/e2e_full.py                                    # all sections (~17 min)
    ~/.qa-venv/bin/python tests/e2e/e2e_full.py recruitment jameah_pages            # or chosen sections
    python3 tests/e2e/write_automated_results.py && python3 project_tracking/source/build_all.py
    QA_CLEAN=all QA_COMMIT=1 ../../env/bin/python tests/e2e/fx.py tests/e2e/qa_cleanup.py   # remove QA data

Results: `tests/e2e/e2e_full_results.json` (and screenshots of failures in `tests/e2e/e2e_shots/`),
not committed. `QA_BASE` changes the site address, `QA_SITE` the site.

Unit tests and the Ministry view check run separately:

    bench --site site1.local run-tests --module medical_hrms.jameah.test_jameah
    bench --site site1.local execute medical_hrms.jameah.verify.run
