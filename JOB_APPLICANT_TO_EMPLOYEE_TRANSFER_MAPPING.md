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

### Parent table mapping

| Source | Destination |
|---|---|
| `Job Applicant.custom_ministry_academic_experience` | `Employee.custom_jameah_experience` |
| Source child DocType: `Job Applicant Academic Experience` | Destination child DocType: `Jameah Work Experience` |

### Child-row field mapping

| Source row field | Destination row field | Transfer notes |
|---|---|---|
| `school_year_history` | `current_academic_year_date` | Direct Gregorian date value |
| `employment_status` | `employment_status` | Direct Ministry Code link |
| `educational_entity` | `institute` | Direct Ministry Code link |
| `work_location` | `location` | Direct Ministry Code link |
| `academic_department` | `academic_department` | Direct Ministry Code link |
| `job_number` | `employee_number` | Direct value |
| `job_rank` | `profession_rank` | Direct Ministry Code link |
| `appointment_to_rank_date` | `hiring_date` | Direct Gregorian date value |
| `job_duties` | `job_duties` | Direct text value |
| `housing` | `accommodation` | Direct Ministry Code link |

Every source row should create one destination row.

The obsolete `company` and `section` fields are not part of the Employee Academic Experience destination table.

## 4. Professional Certificates and Training Courses

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

## 5. Additional Employee Requirements

Creating an Employee requires standard HR information that may not be included in the Ministry child tables. Before inserting Employee, the transfer process or HR confirmation form must supply valid values for fields such as:

- `first_name`
- `company`
- `date_of_joining`
- `date_of_birth`
- `gender`
- `status`

The exact mandatory fields should be checked against the Employee metadata on the target site before insertion.

## 6. Required Lookup Conversions

The following source values cannot always be copied without validation:

| Source value | Required action |
|---|---|
| Ministry employment status | Confirm that it belongs to the `Job status` Ministry category |
| Educational entity | Confirm that it belongs to the `Coding of educational insti` category |
| Work location | Confirm that it belongs to the `Coding cities and governora` category |
| Academic department | Confirm that it belongs to the `Coding academic departments` category |
| Graduation place | Copy to `school_univ` and optionally resolve `custom_ministry_graduate_from` |
| Job Applicant country | Resolve to `custom_jameah_nationality` if this is the agreed nationality source |

Do not silently create Company, Branch, Department, or Ministry Code records during transfer unless HR has explicitly approved that behavior.

## 7. Suggested Child-Table Copy Pattern

```python
for source_row in job_applicant.custom_ministry_academic_experience or []:
	employee.append(
		"custom_jameah_experience",
		{
			"current_academic_year_date": source_row.school_year_history,
			"employment_status": source_row.employment_status,
			"institute": source_row.educational_entity,
			"location": source_row.work_location,
			"academic_department": source_row.academic_department,
			"employee_number": source_row.job_number,
			"profession_rank": source_row.job_rank,
			"hiring_date": source_row.appointment_to_rank_date,
			"job_duties": source_row.job_duties,
			"accommodation": source_row.housing,
		},
	)
```

The same append pattern should be used for Academic Qualifications and Training Courses with their respective destination table fields.

## 8. Transfer Validation Checklist

Before saving the Employee record, confirm that:

- Required Employee fields have values.
- Nationality and identity numbers satisfy the Saudi/non-Saudi validation rules.
- Every Ministry Code link points to a record from the correct code category.
- Company, Branch, and Department links exist.
- All Academic Experience rows were copied into `custom_jameah_experience`.
- All qualification and training rows were copied.
- Special-needs type and the `custom_is_special_needs` checkbox are consistent.
- The transfer cannot create a second Employee from the same Job Applicant.
