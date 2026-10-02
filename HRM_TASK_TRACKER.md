# Medical HRMS — Task and Progress Sheet

As of: 1 October 2026  
Environment: local development/test site; not a production readiness certificate.

## Client summary

The HR and employee self-service dashboards, custom request forms, access controls, leave-policy setup and leave-summary features are implemented in the codebase. Local demo leave setup has been completed previously. End-to-end workflow validation, fixes, shared self-service integration into Instructor/HOD dashboards, and Finance integration remain outstanding.

Dinesh is handling job-level setup and employee registration, as confirmed by the team update. His completion status needs confirmation. Abdul Hakeem's dashboard, self-service, leave and permissions ownership follows the supplied team update. Other responsibilities are proposed coordination areas, not confirmed assignments.

## How to read this sheet

- **Implemented** means code or setup exists, not that client acceptance or production testing is complete.
- **Configured locally** refers to the earlier successful demo setup; the database was not re-audited for this document.
- **Partially implemented / gap / planned** explicitly identifies remaining development or verification.
- No completion percentage or delivery dates are invented. Confirm ownership and estimates with the team.
- Earlier test results are historical context: this document review did not run tests, migrations or change application behavior.

The companion [CSV task sheet](HRM_TASK_TRACKER.csv) opens in Excel or can be imported into Google Sheets. It includes priority, evidence, acceptance criteria and source references for every task.

## Task register

| ID | Task / deliverable | Current status | Responsibility | Next action |
|---|---|---|---|---|
| HR-01 | Custom Medical HRMS app and setup scripts | Implemented - verification pending | Team; owner to confirm | Verify clean installation and repeat migration without duplicates or loss of HR edits. |
| HR-02 | Ministry lookup codes and validation | Implemented - verification pending | Team; owner to confirm | Validate complete approved source data and Arabic/English mappings on target site. |
| HR-03 | Institute hierarchy and facility records | Implemented - verification pending | Team; owner to confirm | HR to confirm real hierarchy and all employee placement links. |
| HR-04 | Job-level setup | In progress - owner confirmation needed | Dinesh | Dinesh to confirm implemented scope, remaining tasks and acceptance criteria. |
| HR-05 | Employee registration | In progress - owner confirmation needed | Dinesh | Complete and test required fields, lookup validation and duplicate prevention. |
| HR-06 | Job Applicant to Employee transfer | Specified - implementation confirmation needed | Dinesh; confirm transfer ownership | Confirm conversion implementation; test lookup resolution, required fields and repeat conversion prevention. |
| HR-07 | Qualifications, experience and Ministry profile fields | Implemented - verification pending | Dinesh / HRM team; confirm split | Reconcile legacy child tables with final Ministry mapping and validate real samples. |
| HR-08 | HR dashboard and leave-management shortcuts | Implemented - UAT pending | Abdul Hakeem | Verify HR roles, dashboard counts, routes and medical-year activation. |
| HR-09 | Employee self-service dashboard | Implemented - UAT pending | Abdul Hakeem | Validate full employee journey and responsive layout. |
| HR-10 | Custom workspace styling | Implemented - UAT pending | Abdul Hakeem | Check browser rendering, missing icons, long labels and mobile layout. |
| HR-11 | Self-service in Instructor, HOD and other staff dashboards | Planned | Abdul Hakeem; Education coordination needed | Embed shared request and leave-summary features while retaining role-specific dashboards and permissions. |
| HR-12 | HR roles, workspace visibility and login routing | Implemented - security UAT pending | Abdul Hakeem | Verify employee, HR, Instructor and HOD role combinations and direct URLs. |
| HR-13 | Own-record access and protected employee identity | Implemented - security UAT pending | Abdul Hakeem | Test API/list/form/attachment access across two employees; verify privileged-role exceptions. |
| HR-14 | Customized employee request forms | Implemented - UAT pending | Abdul Hakeem | Test each form's mandatory fields, validation, private attachments and submission. |
| HR-15 | Request details and easier time selection | Implemented - UAT pending | Abdul Hakeem | Verify saved values, midnight/noon handling and complete employee-visible details. |
| HR-16 | Resume drafts and rejected-request resubmission | Gap - implementation/verification needed | Abdul Hakeem | Implement or confirm safe editing/resubmission with history; test against UAT requirements. |
| HR-17 | Employee data correction approval and application | Partially implemented | Abdul Hakeem; HR input needed | Confirm HR review steps and how approved corrections update Employee with an audit trail. |
| HR-18 | Editable migration defaults for leave types and policies | Implemented - migration UAT pending | Abdul Hakeem | Test new and existing sites; confirm final policies with HR. Normal migration intentionally creates drafts. |
| HR-19 | Local demo policy activation and allocations | Configured locally - flow testing pending | Abdul Hakeem | Run end-to-end submission, approval and balance deduction tests; not a production configuration. |
| HR-20 | Medical leave year and pay-stage controls | Implemented - integration UAT pending | Abdul Hakeem; HR policy review needed | Test stage boundaries, cancellations, overlapping requests, year boundaries and payroll behavior. |
| HR-21 | Monthly half-day and remote-work limits | Implemented - integration UAT pending | Abdul Hakeem | Confirm HR-approved limits; test pending/approved totals, cross-month requests and concurrent submissions. |
| HR-22 | Employee balances and monthly usage display | Implemented - UAT pending | Abdul Hakeem | Reconcile displayed balances with leave ledger after approval, rejection and cancellation. |
| HR-23 | Carry-forward, service eligibility and holiday calendar | Partially configured - HR decisions pending | Abdul Hakeem + HR; confirm shared ownership | Confirm official holidays and carry-forward rules; implement/verify expiry controls and 21-to-30-day eligibility handling. |
| HR-24 | Manager, HR and Finance approval routing | Partially implemented - workflow UAT pending | Abdul Hakeem; HR/Finance reviewers needed | Validate each stage and final approver; reconcile Finance Manager versus Accounts Manager and AED labels versus SAR context. |
| HR-25 | Notifications, rejection reasons and audit trail | Verification pending | Abdul Hakeem; HR input needed | Test submit/approve/reject alerts, remarks, terminal-state protection and audit history. |
| HR-26 | Medical licenses, contract renewal and separation | Structures/rules present - UAT pending | HRM team; owner to confirm | Verify renewal/expiry handling, HR-only processes, notice rules and closure. |
| HR-27 | Employee-Instructor structural link | Documented/implemented foundation - verification pending | HRM + Education teams; owners to confirm | Verify actual links, department data and source-of-truth rules on target site. |
| HR-28 | Automatic shared-profile synchronization | Planned - implementation confirmation needed | HRM + Education teams; owners to confirm | Confirm actual automation; define field ownership, update triggers and conflict handling, then test. |
| HR-29 | Payroll inputs and approved benefits handoff | Planned / partial foundations | HRM + Finance teams; owners to confirm | Implement/confirm approved-data handoff, payroll eligibility, salary components and reconciliation. |
| HR-30 | Payroll calculations, accounting and reporting | Pending integration and Finance validation | Finance + HRM teams; owners to confirm | Validate salary slips, partial-pay leave, accounting postings and reports. Medical activation blocks attendance-based payroll pending review. |
| HR-31 | Automated and end-to-end testing | Partially tested - integration pending | Abdul Hakeem; Dinesh for registration | Run integration suite, registration tests and browser UAT; retain results and fix failures. |
| HR-32 | Documentation alignment and client sign-off | Pending | HRM team + HR/Finance reviewers; owners to confirm | Update stale employee Leave Plan/contract instructions, allowance naming and sync claims; complete HR/Finance sign-off before deployment. |

## Review findings that affect scope

1. **Do not equate planned workflows with completed integration.** The Finance roadmap explicitly marks payroll integration as planned; a standard HRMS feature described in a guide does not prove this project's configuration works end to end.
2. **Employee-Instructor link is not full synchronization.** The implementation plan calls automatic synchronization future work, while user guides describe mirroring. Confirm and align documentation before promising synchronization.
3. **Approval configuration needs reconciliation.** The approval matrix and governance script refer to Accounts Manager, while selected amount-validation hooks use Finance Manager and AED messages. Confirm intended roles, company currency and approval thresholds.
4. **Employee-facing scope has changed.** Older approval documentation permits employee Leave Plan and Contract Renewal submissions; current self-service code treats these as HR-managed. Update the documents.
5. **Allowance naming needs HR clarification.** Current code exposes Children Medical Allowance, but some fields and older documents refer to school fees/education allowance. Confirm the intended benefit before acceptance.
6. **Local leave setup is separate from migration defaults.** Migration creates editable starter records/draft policies; the explicit local demo script activates the demo setup. The demo calendar is weekends only, not a verified official holiday calendar.
7. **Production policy and payroll review are still required.** Carry-forward deadlines, service-length eligibility, official holidays and medical partial-pay payroll behavior are not a fully verified compliance implementation.

## Documents reviewed

- [Completed work](JAMEAH_HRMS_COMPLETED_WORK.md)
- [Implementation plan](JAMEAH_HRMS_IMPLEMENTATION_PLAN.md)
- [Developer setup](DEVELOPER_SETUP.md) and [README](README.md)
- [Entire HRMS user guide](ENTIRE_HRMS_USER_GUIDE.md) and [Jameah user guide](JAMEAH_HRMS_USER_GUIDE.md)
- [Job Applicant to Employee mapping](JOB_APPLICANT_TO_EMPLOYEE_TRANSFER_MAPPING.md)
- [Approval matrix](HRM_APPROVAL_MATRIX.md), [handoff boundaries](HRM_HANDOFF_BOUNDARIES.md), [operations SOP](HRM_OPERATIONS_SOP.md), [UAT scenarios](HRM_UAT_SCENARIOS.md)
- [Finance/Education integration](<HRM Integration Document - Finance and Education.html>) and its summary copy
- [Education integration](<HRM and Education Module Integration.html>)
- [Finance integration roadmap](<HRM and Finance Module Integration Roadmap.html>)

The related setup scripts, hooks, dashboard files, request APIs, permission checks and approval validation code were cross-checked where cited in the CSV. Older documents are treated as requirements or historical descriptions when they conflict with current code.
