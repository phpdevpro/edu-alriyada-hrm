# Project tracking — Medical HRMS & Jameah

The documents the college, the project owner and the testing team work from. Every row carries a date,
and every change is logged with its date in the **Change Log** sheet of each workbook.

| File | For | What is in it |
|---|---|---|
| `Medical_HRMS_Jameah_Task_Tracker.xlsx` | Everyone | Every task (done, in progress, pending), every bug, every open decision, with status, owner, evidence and dates. |
| `Medical_HRMS_Jameah_Checklist.xlsx` | Project owner, server admin, HR, Academic Affairs | What is left outside the code: deployment steps, live-server checks, decisions, HR data entry, reviews. |
| `Medical_HRMS_Jameah_Test_Cases.xlsx` | Testing team | Step-by-step test cases with expected results, the last automated result, a bug report sheet and test accounts. |

## Rules for updating

1. Every change (code, data, decision) updates the matching rows in **all three** documents where it applies.
2. Every updated row gets today's date (`Last updated`, and `Done on` / `Answered on` where it applies).
3. Every change adds one dated line to the Change Log.

## How to update (developers)

The workbooks are generated from the files in `source/` — edit those, never the `.xlsx` by hand
(a hand edit is lost on the next build):

| File | Holds |
|---|---|
| `source/tracker_data.py` | tasks, bugs, decisions |
| `source/testcases_data.py` | test cases |
| `source/checklist_data.py` | checklist items (with their dates) |
| `source/row_dates.py` | last-updated date of every task, bug, decision and test case |
| `source/changelog.py` | the dated change log (newest first) |
| `source/automated_results.json` | result of the last automated browser run, per test ID (`tests/e2e/write_automated_results.py`), and of each `tests/checks` script (they record themselves) |

Then rebuild all three:

    python3 project_tracking/source/build_all.py

The builders stop with an error if a row has no date. Summary sheets are Excel formulas and calculate
when the file is opened.
