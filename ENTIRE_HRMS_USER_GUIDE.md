# Complete Medical College HRMS: User Guide

Welcome to the comprehensive User Guide for the Medical College Human Resource Management System (HRMS). This system integrates standard enterprise HR capabilities with custom Saudi Arabian Ministry of Education (Jameah) compliance requirements and a Learning Management System (LMS) for academic faculty.

---

## 1. Initial System Setup (Administrators & HR Managers)

Before regular users can interact with the system, the foundational data must be established.

### A. Core Company Setup
1. **Company Profile:** Navigate to `Company` and ensure the Medical College's details, default currency (SAR), and standard working hours are set.
2. **Holiday Lists:** Create `Holiday List` records for the academic year and assign them to your company or specific locations.
3. **Leave Types:** Define `Leave Type` records (e.g., Annual Leave, Sick Leave, Unpaid Leave) and set their earning rules.

### B. Jameah Master Data (Compliance)
1. **Ministry Codes:** Navigate to `Jameah Ministry Code`. Use the Data Import tool to upload all Ministry-provided Excel sheets (Nationalities, Job Titles, Degrees, Cities). Ensure the `Code Category` is set correctly for each batch.
2. **Institute Hierarchy:** Build your organizational tree:
   - Create `Jameah Branch` records.
   - Create `Jameah College` and `Jameah Agency` records, linking them to Branches.
   - Create `Jameah Academic Department` records, linking them to Colleges.
3. **Facilities:** Navigate to `Jameah Facility` to add Hospitals, Clinics, Labs, and Classrooms.

---

## 2. Employee Onboarding & Management

When a new staff member or academic faculty joins the institution:

### A. Creating the Employee Record
1. Navigate to **Employee** list and click **Add Employee**.
2. **Standard Details:** Fill in the First Name, Date of Joining, Department, and Designation.
3. **Jameah Compliance Details:**
   - **Jameah Demographics:** Enter the mandatory 4-part names in both Arabic and English.
   - **Jameah Identity:** Select the Identity Type, enter the Number, and choose the Nationality (these pull from the Ministry Codes).
   - **Institute Placement:** Assign the employee to their specific Jameah Branch, College, Academic Department, and Facility.
4. **Qualifications & Experience:** Scroll to the bottom to fill out the Jameah child tables (Academic Qualifications, Work Experience, Training Courses, Publications, Awards).

### B. Faculty / Instructor Setup (LMS Integration)
If the employee is teaching:
1. On the Employee record, locate the **LMS Instructor** link field.
2. If they don't have an Instructor profile yet, create one from this field.
3. The system will mirror their Jameah demographic and institutional placement data onto their Instructor profile for academic reporting.

---

## 3. Daily HR Operations

### A. Attendance Tracking
- **Automated (Biometric):** If integrated with biometric devices, `Employee Checkin` records are automatically created, and `Attendance` logs are generated daily.
- **Manual:** Managers or HR can use the `Attendance Tool` to mark bulk attendance for a department on a given day.
- **Shifts:** Use `Shift Type` and `Shift Assignment` to manage staff working in hospital facilities with rotating schedules.

### B. Leave Management
1. **Application:** Employees log in and create a `Leave Application`, selecting the Leave Type and dates.
2. **Approval Workflow:** The application routes to their designated Leave Approver (usually their Department Head or Dean). The approver reviews and submits the application.
3. **Tracking:** HR can view the `Leave Ledger` to track balances accurately.

---

## 4. Payroll Processing

To process monthly salaries:

1. **Salary Structures:** Ensure every employee is assigned a `Salary Structure` (which defines basic pay, allowances, and deductions) via a `Salary Structure Assignment`.
2. **Payroll Entry:** At the end of the month, the Payroll Manager creates a `Payroll Entry`.
3. **Process:** 
   - Select the date range and department/company.
   - Click **Create Salary Slips**. The system will calculate attendance, deduct unpaid leaves, and generate draft Salary Slips.
4. **Finalize:** Review the draft slips. Once verified, **Submit** the Payroll Entry to finalize the slips and optionally book the accounting journal entries.

---

## 5. Performance, Training & Lifecycle

- **Appraisals:** Use the `Appraisal` module to conduct periodic performance reviews based on predefined templates and goals.
- **Training:** Manage internal training programs using `Training Event` and track employee participation.
- **Lifecycle Events:** Use `Employee Promotion`, `Employee Transfer`, and `Employee Separation` to formally document changes in an employee's status, ensuring a complete historical audit trail.

---
*Note: For specific mapping of Ministry Excel sheets to system fields, please refer to the `JAMEAH_HRMS_IMPLEMENTATION_PLAN.md` and `JAMEAH_HRMS_USER_GUIDE.md`.*
