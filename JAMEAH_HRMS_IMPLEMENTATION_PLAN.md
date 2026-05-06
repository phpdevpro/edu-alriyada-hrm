# Jameah HRMS Implementation Plan

## Objective
To strictly map the standard Frappe `Instructor` and `Employee` Doctypes to the mandatory Saudi Arabian Ministry of Education (Jameah) data dictionary, ensuring full compliance and capturing all requested Faculty data points.

## Phase 1: Master Data (Lookups)
The Ministry mapping heavily relies on predefined lookup lists.
- **Action:** Utilize the newly created `Jameah Ministry Code` Doctype.
- **Mapping:** Fields defined as "Lookup" (e.g., Gender, Nationality, Social Status, Academic Degrees) will be implemented as `Link` fields pointing to `Jameah Ministry Code`.
- **Filtering:** Filters will be applied so that dropdowns only display codes relevant to their category (e.g., `category = 'Nationality'`).

## Phase 2: Core Field Injection (Personal Information)
The mapping requires extensive demographic and identity tracking.
- **Action:** Inject over 30 custom fields into the `Instructor` and `Employee` Doctypes via a Python setup script.
- **Structure:** 
  - **Jameah Demographics:** 4-part names in both English and Arabic.
  - **Jameah Identity:** Civil registry/Identity number, Type of special needs, Date/Place of birth.
  - **Jameah Contact Info:** Postal address, City code, Mobile/Work numbers.

## Phase 3: Exact Child Table Creation
The mapping requires 7 specific sub-tables for Faculty members. We will create Doctypes (set as `istable = 1`) matching the exact names and fields from the specification:
1. `Instructor Research Publication` (15+ fields)
2. `Instructor Academic Qualification` (19 fields)
3. `Instructor Academic Experience` (17 fields)
4. `Instructor Previous Experience` (9 fields)
5. `Instructor Training Course` (8 fields)
6. `Instructor Award` (3 fields)
7. `Instructor Attachment` (3 fields)

## Phase 4: Employee & Instructor Synchronization Strategy
- Because the system acts as an HRMS, core HR operations occur on the `Employee` record, while academic functions occur on the `Instructor` record.
- **Action:** Mirror the Jameah fields and child tables across both Doctypes to ensure data availability regardless of which module (HR vs. Education) is being accessed. (A future automation script can be written to keep them in sync if requested).
