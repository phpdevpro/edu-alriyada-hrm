const EMD_SHEET = "medical_hrms.employee_data_sheet.";

frappe.query_reports["Employees Missing Ministry Data"] = {
	filters: [
		{ fieldname: "department", label: __("Academic Department"), fieldtype: "Link", options: "Department" },
		{ fieldname: "show_complete", label: __("Show complete employees too"), fieldtype: "Check", default: 0 },
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "missing_count" && data) {
			value = `<span style="font-weight:600;color:${data.missing_count ? "var(--red-600)" : "var(--green-600)"}">${value}</span>`;
		}
		return value;
	},
	onload(report) {
		// The data sheet writes Employee records: HR Manager only (employee_data_sheet._require_hr_manager).
		if (!(frappe.session.user === "Administrator" || frappe.user.has_role("HR Manager"))) return;
		report.page.add_inner_button(__("Download Data Sheet"), () =>
			frappe.call({ method: EMD_SHEET + "export_sheet", freeze: true, freeze_message: __("Preparing the sheet...") }).then((r) => {
				const m = r.message || {};
				frappe.show_alert({ message: __("{0} employees, {1} required cells empty", [m.employees, m.missing_cells]), indicator: "green" });
				window.open(m.file_url);
			}));
		report.page.add_inner_button(__("Check / Import Data Sheet"), () => emd_import_dialog(report));
	},
};

function emd_import_dialog(report) {
	const dialog = new frappe.ui.Dialog({
		title: __("Check / Import Data Sheet"),
		fields: [
			{ fieldtype: "HTML", options: `<p>${__("Upload the filled sheet. Check first: nothing is saved and you get a result sheet with each row's status. Then import.")}</p>` },
			{ fieldname: "file", fieldtype: "Attach", label: __("Filled Data Sheet (.xlsx)"), reqd: 1, options: { restrictions: { allowed_file_types: [".xlsx"], allow_public: false } } },
			{ fieldname: "result", fieldtype: "HTML" },
		],
		primary_action_label: __("Check (nothing is saved)"),
		primary_action: (values) => run(values.file, 0),
		secondary_action_label: __("Import"),
		secondary_action: () => {
			const file = dialog.get_value("file");
			if (!file) return frappe.msgprint(__("Attach the filled sheet first."));
			frappe.confirm(__("Save the changes in this sheet to the Employee records?"), () => run(file, 1));
		},
	});
	function run(file, commit) {
		frappe.call({ method: EMD_SHEET + "import_sheet", args: { file, commit }, freeze: true, freeze_message: commit ? __("Importing...") : __("Checking...") }).then((r) => {
			const m = r.message || {};
			const counts = Object.entries(m.counts || {}).map(([k, v]) => `<b>${frappe.utils.escape_html(__(k))}</b>: ${v}`).join(" · ") || __("No rows found");
			dialog.fields_dict.result.$wrapper.html(`<div class="alert ${commit ? "alert-success" : "alert-info"}" style="margin-top:8px">
				<p>${commit ? __("Imported.") : __("Checked - nothing was saved.")} ${counts}</p>
				<a href="${encodeURI(m.result_file)}" target="_blank" rel="noopener">${__("Open the result sheet")}</a></div>`);
			if (commit) report.refresh();
		});
	}
	dialog.show();
}
