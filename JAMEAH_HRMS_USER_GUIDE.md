# Jameah HRMS: User Guide

Welcome to the Medical College HRMS. This system has been heavily customized to comply with the Saudi Arabian Ministry of Education (Jameah) data requirements.

## 1. System Setup (To be done first)

Before adding employees or instructors, the System Administrator must populate the Master Data lists.

### A. Importing Ministry Codes
1. Navigate to **Jameah Ministry Code** in the search bar.
2. Click **Add Jameah Ministry Code**.
3. Use the Frappe Data Import tool to upload your Excel sheets here. 
   - Ensure you define the `Code Category` (e.g., "Nationality", "Gender", "City", "Degree") so dropdowns filter correctly later.

### B. Setting up the Institute Hierarchy
Build your organizational tree from the top down:
1. Navigate to **Jameah Branch** and add your main branches.
2. Navigate to **Jameah College** and **Jameah Agency** and link them to their respective Branches.
3. Navigate to **Jameah Deanery** and link it to an Agency.
4. Navigate to **Jameah Academic Department** and link it to a College.
5. Navigate to **Jameah Facility** (Hospitals, Clinics, Labs) and set them up, linking them to Colleges/Branches if applicable.

## 2. Managing Employees and Instructors

When a new staff member or academic faculty joins the college:

1. Navigate to the **Employee** list and click **Add Employee**.
2. **Core Demographics:** Scroll down to the **Jameah Demographics** section. You must fill out the 4-part names in both English and Arabic.
3. **Identity Details:** Fill out the **Jameah Identity Details** section. The dropdowns here (like Nationality or Identity Issue Place) pull directly from the `Jameah Ministry Code` table you populated in Step 1.
4. **Institute Placement:** Scroll to the **Jameah Institute Placement** section to assign the employee to their specific Branch, College, Department, and Facility.
5. **Child Tables:** Add the employee's Qualifications, Past Experience, Training Courses, Publications, and Awards using the sub-tables at the bottom of the form.

## 3. LMS Integration (Instructors)
If the employee is an academic teaching a course:
1. Ensure the `LMS Instructor` field on the Employee profile is populated.
2. You can navigate to their **Instructor** profile in the Education module. All Jameah demographic and institutional fields are mirrored there for consistency across the academic and HR modules.
