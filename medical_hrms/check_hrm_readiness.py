import frappe


REQUEST_DOCTYPES = [
    "Employee Data Update Request",
    "Contract Renewal Request",
    "Leave Plan Request",
    "Employee Training Request",
    "Company Car Request",
    "Children Education Allowance Request",
    "Salary Certificate Request",
    "Pre Approved Overtime Request",
    "Return From Leave Request",
    "Remote Work Request",
    "Permission Request",
    "Employee Medical License",
]

FINANCE_DOCTYPES = {
    "Employee Training Request",
    "Company Car Request",
    "Children Education Allowance Request",
    "Pre Approved Overtime Request",
}


def _has_role_permission(dt_doc, role_name: str):
    return any((p.role == role_name and p.read) for p in dt_doc.permissions)


def execute():
    results = {
        "workspace": {},
        "permissions": {},
        "data_counts": {},
    }

    workspace_name = "Medical HRMS"
    if frappe.db.exists("Workspace", workspace_name):
        ws = frappe.get_doc("Workspace", workspace_name)
        ws_roles = [r.role for r in ws.roles]
        results["workspace"] = {
            "exists": True,
            "public": int(ws.public),
            "roles": ws_roles,
        }
    else:
        results["workspace"] = {"exists": False}

    for dt in REQUEST_DOCTYPES:
        if not frappe.db.exists("DocType", dt):
            results["permissions"][dt] = {"exists": False}
            continue

        dt_doc = frappe.get_doc("DocType", dt)
        roles = [p.role for p in dt_doc.permissions]
        has_hr_user = _has_role_permission(dt_doc, "HR User")
        has_hr_manager = _has_role_permission(dt_doc, "HR Manager")
        has_accounts = _has_role_permission(dt_doc, "Accounts Manager")
        results["permissions"][dt] = {
            "exists": True,
            "permission_rows": len(dt_doc.permissions),
            "roles": roles,
            "has_hr_user": has_hr_user,
            "has_hr_manager": has_hr_manager,
            "has_accounts_manager": has_accounts,
            "finance_expected": dt in FINANCE_DOCTYPES,
        }

    for dt in [
        "Jameah Ministry Code",
        "Jameah Branch",
        "Jameah Agency",
        "Jameah Deanery",
        "Jameah College",
        "Jameah Academic Department",
        "Jameah Facility",
        "Employee",
        "Instructor",
    ]:
        results["data_counts"][dt] = frappe.db.count(dt)

    print("HRM Readiness Check")
    print("-------------------")
    print(f"Workspace exists: {results['workspace'].get('exists')}")
    if results["workspace"].get("exists"):
        print(f"Workspace public: {results['workspace'].get('public')}")
        print(f"Workspace roles: {', '.join(results['workspace'].get('roles', []))}")

    print("\nPermissions")
    for dt, info in results["permissions"].items():
        if not info.get("exists"):
            print(f"- {dt}: MISSING")
            continue

        line = (
            f"- {dt}: rows={info['permission_rows']}, "
            f"HR User={info['has_hr_user']}, HR Manager={info['has_hr_manager']}"
        )
        if info["finance_expected"]:
            line += f", Accounts Manager={info['has_accounts_manager']}"
        print(line)

    print("\nData Counts")
    for dt, count in results["data_counts"].items():
        print(f"- {dt}: {count}")

    return results
