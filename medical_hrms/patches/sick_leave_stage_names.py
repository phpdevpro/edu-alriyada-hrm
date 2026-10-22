"""Sick leave stages numbered so every list shows them in pay order: 'Sick Leave 1 - Full Pay',
'Sick Leave 2 - 75% Pay', 'Sick Leave 3 - Unpaid'. The rename updates every allocation, application
and ledger entry. The Sick Leave policy gets the matching title (unless HR renamed it) and its rows
the same order. Stages are found by their seed key, so HR's own names are never overwritten twice.
"""
import frappe

from medical_hrms.setup_leave_defaults import GUIDANCE, KEY, NOTES, SICK_POLICY_TITLE, SICK_STAGES

OLD_NAMES = {"sick_full": "Sick Leave - Full Pay", "sick_partial": "Sick Leave - 75 Percent Pay", "sick_unpaid": "Sick Leave - Unpaid"}
OLD_POLICY_TITLE = "Medical HRMS - Medical Leave (Separate Sick Year)"
OLD_MEDICAL_NOTE = ("MEDICAL LEAVE ONLY: sequential sick-pay stages, separate from annual leave. HR must submit this policy and use Activate "
	"Medical Leave Year on the HR dashboard, starting on the first illness date. Do not assign through the annual Leave Control Panel. "
	"The unpaid stage is enforced by medical checks, not a Leave Allocation.")


def execute():
	for key, label, _settings in SICK_STAGES:
		name = frappe.db.get_value("Leave Type", {KEY: key}, "name")
		# Only the starter names are changed; a name HR chose themselves is kept.
		if name == OLD_NAMES[key] and not frappe.db.exists("Leave Type", label):
			frappe.rename_doc("Leave Type", name, label, force=True)
			frappe.db.set_value("Leave Type", label, "leave_type_name", label, update_modified=False)

	policy = frappe.db.get_value("Leave Policy", {KEY: "medical"}, ["name", "title", NOTES], as_dict=True)
	if policy:
		if policy.title == OLD_POLICY_TITLE:
			frappe.db.set_value("Leave Policy", policy.name, "title", SICK_POLICY_TITLE, update_modified=False)
		if policy.get(NOTES) == OLD_MEDICAL_NOTE:
			frappe.db.set_value("Leave Policy", policy.name, NOTES, GUIDANCE["medical"], update_modified=False)
		order = {frappe.db.get_value("Leave Type", {KEY: key}, "name"): i for i, (key, *_rest) in enumerate(SICK_STAGES, 1)}
		for row in frappe.get_all("Leave Policy Detail", filters={"parent": policy.name, "parenttype": "Leave Policy"}, fields=["name", "leave_type"]):
			if row.leave_type in order:
				frappe.db.set_value("Leave Policy Detail", row.name, "idx", order[row.leave_type], update_modified=False)
	frappe.clear_cache()
