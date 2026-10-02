# Medical College HRMS - Developer Setup Guide

This document outlines the steps to set up and run the customized `medical_hrms` application alongside the standard Frappe `hrms` and `education` modules. 
This system implements the 18 enterprise-grade workflows required for the Medical College.

## 1. Prerequisites
Ensure you have a standard Frappe bench installed with the following apps already downloaded:
- `frappe` (Framework)
- `erpnext` (Core ERP)
- `hrms` (Standard HR)
- `education` (LMS Module - used for Instructors)

## 2. Architecture Overview
We have deliberately avoided modifying the core `hrms` app. Instead, we created a custom app named **`medical_hrms`**. 
This app contains:
*   **Custom Doctypes:** To handle pre-approvals and medical-specific requests not found in standard Frappe.
*   **Python Hooks (`doc_events`):** To enforce financial limits, team absence thresholds, and notice periods natively over standard HRMS doctypes.
*   **Cross-App Links:** Links HR `Employee` profiles directly to LMS `Instructor` profiles.

## 3. Pulling the Custom App (If using Git)
If the `medical_hrms` app is hosted on a repository, fetch it to your local bench:
```bash
cd frappe-bench
bench get-app https://github.com/your-org/medical_hrms.git
```
*(Note: If you are working on the same machine where this was just generated, the app is already in the `apps/` directory).*

## 4. Installing the App on your Site
Once the app is on your bench, install it onto your specific site (e.g., `site1.local`):

```bash
bench --site site1.local install-app medical_hrms
```

## 5. Applying Migrations
To ensure all the new JSON schemas (Doctypes) and database columns are created correctly:

```bash
bench --site site1.local migrate
```

## 6. Clearing the Cache
Clear the cache to register the new `hooks.py` events:

```bash
bench --site site1.local clear-cache
bench restart
```

## 7. Verifying the Setup
Log into the Frappe Desk (usually `http://site1.local:8000`).
1. Go to the **Employee** List. Open any Employee. You should now see a new field called **"LMS Instructor"** located right after the User ID.
2. Search for **"Employee Medical License"** in the awesome bar. This new tracking system should be available.
3. Search for **"Return from Leave Request"**, **"Children Education Allowance"**, or **"Pre Approved Overtime Request"**.

## 8. Role Setup for Workflows
The python validation hooks (`apps/medical_hrms/medical_hrms/medical_hrms/overrides/`) rely on standard role names to authorize high-value requests. 
Make sure you create/assign these exact Role names to your managers in Frappe:
- `Department Head` (For training > 10k, Travel > 15k, Expenses > 5k)
- `HR Manager` (For training > 30k)
- `Finance Manager` (For training > 50k, Travel > 50k, Expenses > 20k, Company Cars)

## 9. Development & Modification
If you need to tweak the financial limits or add new validation rules:
1. Open `apps/medical_hrms/medical_hrms/medical_hrms/overrides/`
2. Modify the python scripts (e.g., `expense_claim.py`, `education_allowance.py`).
3. If you add new hooks, remember to declare them in `apps/medical_hrms/medical_hrms/hooks.py` under the `doc_events` dictionary.

---
## Editable leave starter records

Install and migration hooks run `medical_hrms.setup_leave_defaults.execute`.
It creates missing annual, full-pay sick, 75%-pay sick, unpaid sick, and unpaid
leave categories, plus draft 21-day and 30-day annual-leave policies. Existing
`Annual`/`Annual Leave` categories are reused without changing their settings.
Hidden seed keys preserve HR changes even when a type or policy is renamed.
Do not export these records as overwriting fixtures.

Where a company has no overlapping Leave Period for the current calendar year,
an **inactive** January–December starter period is created. HR must confirm the
correct dates. Policies remain drafts; HR reviews and submits them, then uses
Leave Control Panel for bulk assignments. No employee allocations, leave
balances, role assignments, approvals, or active periods are created automatically.
If an existing annual type's allocation ceiling is lower than a proposed policy,
that policy is skipped with a message rather than overriding HR's ceiling.

These are starter records, not a complete Saudi compliance implementation.
HR must confirm sector/contract applicability, holiday counting, carry-forward
approvals and deadlines, and service-length eligibility. The 21/30-day policies
do not automatically switch at a service anniversary. Sick categories are not
included in annual policy allocations. A separate draft Medical Leave policy
defines 30 full-pay, 60 partial-pay and 30 unpaid days. HR must submit it and use
**HR Dashboard → Activate Medical Leave Year** with the first illness date.
Standard Leave Policy Assignment is intentionally blocked for this policy,
because it uses annual periods and conflicts with an existing annual assignment.

Activation creates only full-pay and partial-pay allocations for one year from
that date (unpaid leave cannot have a native allocation). It records the HR actor
and date in allocation comments and rejects duplicate/overlapping cycles.
All medical types must include holidays and have carry-forward/earned leave
disabled; existing type settings are not silently changed. Server checks include
pending and approved requests, enforce stage order and total limits (including
unpaid days), reject overlapping requests, and require splitting at stage/year
boundaries. Cancelling/rejecting/changing earlier leave cannot leave a later
request in an invalid pay stage; HR must adjust dependent requests first.

Activation is blocked for attendance-based payroll: the installed version's
partial-pay calculation needs separate payroll review. Leave-based payroll uses
the existing 0.75 fraction; this is not a change to payroll formulas. Medical
certification remains HR's responsibility. No medical years are activated during
migration. Monthly half-day/WFH settings remain a separate, opt-in company rule in HR
Settings; migration does not enable them.

*Generated for the Medical College HRMS Project.*
