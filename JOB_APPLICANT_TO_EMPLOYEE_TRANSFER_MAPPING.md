# Job Applicant to Employee Data Transfer Mapping

## Purpose

This document defines how data collected in `Job Applicant` must be transferred to `Employee` after HR confirms the applicant.

The transfer process should:

1. Create the new `Employee` document.
2. Map the Job Applicant personal-information fields to Employee fields.
3. Copy child-table rows into the correct Employee child tables.
4. Resolve values for fields that link to master records such as Company, Branch, Department, and Jameah Ministry Code.
5. Save the source Job Applicant reference on Employee when a suitable reference field is available.

## 1. Personal Information

| Job Applicant source field | Employee destination field | Transfer notes |
|---|---|---|
| `custom_ministry_special_needs_type` | `custom_ministry_special_needs_type` | Direct Ministry Code link |
| `custom_ministry_identity_number` | `custom_identity_number` | Direct value |
| `custom_ministry_place_of_birth` | `custom_ministry_place_of_birth` | Direct Ministry Code link |
| `custom_ministry_origin_id_number` | `custom_original_home_id_number` | Direct value |
| `custom_ministry_religion` | `custom_ministry_religion` | Direct Ministry Code link |
| `custom_ministry_business_city` | `custom_ministry_work_city` | Direct Ministry Code link |
| `custom_ministry_zip_code` | `custom_zip_code` | Direct value |

When `custom_ministry_special_needs_type` contains a value, the transfer must also set:

```python
employee.custom_is_special_needs = 1
```

Otherwise, set `custom_is_special_needs` to `0`.

## 2. Academic Qualifications

### Parent table mapping

| Source | Destination |
|---|---|
| `Job Applicant.custom_ministry_academic_qualifications` | `Employee.education` |
| Source child DocType: `Job Applicant Academic Qualification` | Destination child DocType: `Employee Education` |

### Child-row field mapping

| Source row field | Destination row field | Transfer notes |
|---|---|---|
| `subspecialty` | `custom_ministry_minor` | Direct Ministry Code link |
| `appreciation` | `custom_ministry_assessment_type` | Direct Ministry Code link |
| `graduation_rate` | `class_per` | Copy the numeric rate |
| `rate_type` | `custom_ministry_gpa_type` | Direct Ministry Code link |
| `study_system` | `custom_ministry_study_type` | Direct Ministry Code link |
| `graduation_place` | `school_univ` | Copy the text value |
| `college` | `custom_ministry_faculty` | Direct Ministry Code link |
| `qualification_date` | `custom_date_of_scientific_degree` | Direct date value |
| `city` | `custom_ministry_city` | Direct Ministry Code link |

If `graduation_place` can be matched to a `Jameah Ministry Code`, also populate `custom_ministry_graduate_from` with the matching Ministry Code record.

## 3. Academic Experience

### Source table

```text
Job Applicant.custom_ministry_academic_experience
```

Source child DocType: `Job Applicant Academic Experience`.

Academic Experience is a child table on Job Applicant, while the corresponding current-employment information is stored as fields on Employee. The transfer should select the latest or HR-confirmed Academic Experience row.

| Source row field | Employee destination field | Transfer notes |
|---|---|---|
| `school_year_history` | `custom_school_year_history` | Direct value |
| `employment_status` | `status` | Convert the Ministry Code to a valid Employee status |
| `educational_entity` | `company` | Resolve to an existing `Company` record |
| `work_location` | `branch` | Resolve to an existing `Branch` record |
| `academic_department` | `department` | Resolve to an existing `Department` record |
| `job_number` | `employee_number` | Direct value |
| `job_rank` | `custom_ministry_job_rank` | Direct Ministry Code link |
| `appointment_to_rank_date` | `custom_date_of_appointment_to_rank` | Direct date value |
| `job_duties` | `custom_job_duties` | Direct text value |
| `housing` | `custom_ministry_accommodation` | Direct Ministry Code link |

If Job Applicant contains multiple Academic Experience rows, HR must identify which row represents the employee's current appointment. Other historical rows may be retained in a history table if required.

## 4. Previous Experience

### Parent table mapping

| Source | Destination |
|---|---|
| `Job Applicant.custom_ministry_previous_experience` | `Employee.custom_jameah_experience` |
| Source child DocType: `Job Applicant Previous Experience` | Destination child DocType: `Jameah Work Experience` |

### Child-row field mapping

| Source row field | Destination row field | Transfer notes |
|---|---|---|
| `job_title` | `designation` | Direct value |
| `organization_name` | `company` | Direct value |
| `city` | `city` | Direct Ministry Code link |
| `country` | `country` | Direct Ministry Code link |
| `college_administration` | `college_administration` | Direct value |
| `section` | `section` | Direct value |
| `start_date` | `start_date` | Direct date value |
| `end_date` | `end_date` | Direct date value |
| `job_duties` | `job_duties` | Direct text value |

Every source row should create one destination row.

## 5. Professional Certificates and Training Courses

### Parent table mapping

| Source | Destination |
|---|---|
| `Job Applicant.custom_ministry_training_courses` | `Employee.custom_jameah_training` |
| Source child DocType: `Job Applicant Training Course` | Destination child DocType: `Jameah Training Course` |

### Child-row field mapping

| Source row field | Destination row field | Transfer notes |
|---|---|---|
| `course_type` | `course_type` | Direct value |
| `course_date` | `date` | Direct date value |
| `city` | `city` | Direct Ministry Code link |
| `country` | `country` | Direct Ministry Code link |

Every source row should create one destination row.

## 6. Additional Employee Requirements

Creating an Employee requires standard HR information that may not be included in the Ministry child tables. Before inserting Employee, the transfer process or HR confirmation form must supply valid values for fields such as:

- `first_name`
- `company`
- `date_of_joining`
- `date_of_birth`
- `gender`
- `status`

The exact mandatory fields should be checked against the Employee metadata on the target site before insertion.

## 7. Required Lookup Conversions

The following source values cannot always be copied without validation:

| Source value | Required action |
|---|---|
| Ministry employment status | Convert to one of the valid Employee `status` options |
| Educational entity | Find or create the corresponding `Company` according to the agreed master-data policy |
| Work location | Find the corresponding `Branch` |
| Academic department | Find the corresponding `Department` |
| Graduation place | Copy to `school_univ` and optionally resolve `custom_ministry_graduate_from` |
| Job Applicant country | Resolve to `custom_jameah_nationality` if this is the agreed nationality source |

Do not silently create Company, Branch, Department, or Ministry Code records during transfer unless HR has explicitly approved that behavior.

## 8. Suggested Child-Table Copy Pattern

```python
for source_row in job_applicant.custom_ministry_previous_experience or []:
	employee.append(
		"custom_jameah_experience",
		{
			"designation": source_row.job_title,
			"company": source_row.organization_name,
			"city": source_row.city,
			"country": source_row.country,
			"college_administration": source_row.college_administration,
			"section": source_row.section,
			"start_date": source_row.start_date,
			"end_date": source_row.end_date,
			"job_duties": source_row.job_duties,
		},
	)
```

The same append pattern should be used for Academic Qualifications and Training Courses with their respective destination table fields.

## 9. Transfer Validation Checklist

Before saving the Employee record, confirm that:

- Required Employee fields have values.
- Nationality and identity numbers satisfy the Saudi/non-Saudi validation rules.
- Every Ministry Code link points to a record from the correct code category.
- Company, Branch, and Department links exist.
- The correct Academic Experience row was selected as the current appointment.
- All qualification, previous-experience, and training rows were copied.
- Special-needs type and the `custom_is_special_needs` checkbox are consistent.
- The transfer cannot create a second Employee from the same Job Applicant.

