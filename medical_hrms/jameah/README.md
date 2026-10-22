# Ministry (Jameah) views — Employees, Faculty and Students

Database views the Ministry of Education's Jameah agent reads, one per section of
`education/MINISTRY_FIELD_MAPPING.html` (Student 1–10, Employee 5, Faculty 8 sections), with the
spec's column names. Owned by `medical_hrms`; nothing in the Education app is changed.
The Education app's own `viewJameah*` views are left as they are; ours are named
`jameah…` (lowercase j) so the two never collide.

| View | One row per |
|---|---|
| `jameahEmployeePersonalInfo` | employee |
| `jameahEmployeeAcademicQualifications` / `…AcademicExperience` / `…PreviousExperience` / `…ProfessionalCertificates` | Jameah child-table row |
| `jameahFacultyPersonalInfo` | active Instructor |
| `jameahFacultyResearch` / `…AcademicQualification` / `…PreviousExperience` / `…ProfessionalCertificates` / `…Awards` | Jameah child-table row of the Instructor (else of their Employee record) |
| `jameahFacultyAcademicExperience` | Jameah Work Experience row; one current position from the Instructor record when there is none |
| `jameahFacultyAttachments` | Instructor photo |
| `jameahStudentPersonalInfo`, `…KSAAddress`, `…Contact`, `…Scholarship` | student |
| `jameahStudentCompanion`, `…Relatives`, `…HighSchoolCertificate` | guardian / sibling / certificate row |
| `jameahStudentForeignAddress` | student with a foreign (Student Non Saudi) address |
| `jameahStudentAcademicDetails` | submitted Program Enrollment |
| `jameahStudentAttachments` | uploaded student document |

Column-by-column sources: [VIEWS.md](VIEWS.md) (generated from `views.py`).

## Rules

- **Codes, not names.** Lookup columns carry the bare Ministry code (`101`). A code is
  sent only if it is in the official list (`tabJameah Ministry Code`) for that column's
  category; anything else is sent as NULL, never guessed.
- **Education masters go through the Code Map.** Their own code columns are not all
  Ministry codes (every City has `90`, Religion uses `REL001`), so each value is mapped in
  **Jameah Code Map**. Rows are Verified automatically only when the stored code and the
  name agree with the official list, or the name matches exactly one entry; the reviewed
  exceptions are in `code_map.REVIEWED`. Everything else waits for a person.
- **Faculty** = active Instructors (Left ones are former faculty). Personal data comes from
  the Instructor's Jameah fields, else from the Employee record of the same person (linked,
  or same e-mail) - those Employees are not in the Employee views, so each person is sent
  once. Child sections use the Instructor's Jameah rows, else the Employee's (a hire's rows
  come from the job application). Faculty Ranking / Status / Contract Type go through the
  Code Map. Columns the college system does not record (research type and status, ISBN,
  academic sub-level, included specialization, course type ...) are sent as NULL.
  Column names follow the Ministry document exactly, including its spellings
  `EnglishFourhtName` and `Summury`.
- **Jameah Settings** holds institution values (UniversityId P18, college code, study
  types, programme duration…). An empty setting is sent as NULL.
- **Employees** = the configured company only, and never teaching staff (an Instructor
  points at them, by link or e-mail): the Ministry receives those as Faculty. The Jameah
  child tables are shared with Instructor, so every Employee view filters
  `parenttype = 'Employee'`.
- Integer columns (phones, IDs) are digits only; dates before 1920 (placeholders such as
  1900-01-01, zero dates) are sent as NULL.
- **Academic figures** (credit hours, GPA, latest enrollment/term) come from
  `jameah_student_summary`, rebuilt hourly (long queue, ~7 minutes), after every migrate,
  and from the Jameah Data Check page. GPA and credit hours are Education's official figures
  (`education/utils/gpa.py`, `education/utils/credit_hours.py`, what the transcript shows);
  older Education versions without those modules fall back to the SQL in `summary.py`.

## Checking the data

- **Jameah Data Check** page (`/app/jameah-data-check`, HR / Education Manager): invalid
  codes, mandatory gaps, values waiting for a code, empty settings, source problems.
- **Employee form → View → Ministry (Jameah) Data**: what is sent for one employee.
- Full value-by-value comparison of every view with the source records (Python rebuild,
  independent of the SQL; GPA and credit hours against Education's official figures):

      bench --site <site> execute medical_hrms.jameah.verify.run

- Tests: `bench --site <site> run-tests --module medical_hrms.jameah.test_jameah`

## Giving the Ministry agent access

    bench --site <site> execute medical_hrms.jameah.views.grant_statements

prints `CREATE USER` / `GRANT SELECT` statements for a read-only account limited to these
views (they run with their definer's rights, so the account cannot read any ERP table).
Run them as the MariaDB administrator with a strong password.

## Files

`views.py` view definitions · `code_map.py` crosswalk · `summary.py` academic figures ·
`verify.py` independent check · `status.py` Data Check page API · `spec_columns.json`
spec columns (from the HTML) · `hijri_new_years.json` 1 Muharram dates 1400–1480 AH
(Umm al-Qura, generated with the `hijridate` library).
