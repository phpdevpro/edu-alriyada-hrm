# HRM UAT Scenarios

Use this checklist for HRM sign-off before other teams continue.

## Core Scenarios

1. Employee creates each HR request type successfully.
2. HR approver can view, approve, and reject each request.
3. Rejected request returns with reason and can be resubmitted.
4. Finance-routed requests are visible to Accounts Manager.
5. Approved requests move to terminal status and become read-only for employees.
6. Request timeline (`track_changes`) captures updates.
7. Notifications are sent on submit/approve/reject (manual or workflow alerts).

## Request-Specific UAT

| Request Type | Pass Criteria |
|---|---|
| Employee Training Request | Finance stage appears and final state closes correctly |
| Company Car Request | HR and finance routing both work |
| Children Education Allowance Request | HR Director + Finance sequence works |
| Pre Approved Overtime Request | HR approval and payroll-impact handoff is recorded |
| Salary Certificate Request | HR can issue and close status as Issued |
| Remote Work Request | Manager/Dept approval path executes |
| Permission Request | Pending -> Approved/Rejected works with correct visibility |
| Return From Leave Request | HR, readiness, and completion states are usable |
| Employee Medical License | Renewal/update flow and expiry tracking works |

## Sign-Off

- [ ] HR Manager sign-off complete
- [ ] HR User operational sign-off complete
- [ ] Accounts Manager sign-off for finance-impact flows complete
