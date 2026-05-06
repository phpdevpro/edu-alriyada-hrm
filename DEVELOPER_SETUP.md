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
*Generated for the Medical College HRMS Project.*