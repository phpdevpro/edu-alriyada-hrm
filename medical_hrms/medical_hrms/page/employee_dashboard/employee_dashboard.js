(() => {
frappe.pages["employee-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, single_column: true });
	$(wrapper).find(".page-head .title-area, .page-head-content").remove();

	const allowed =
		frappe.session.user === "Administrator" ||
		frappe.user.has_role("Employee") ||
		frappe.user.has_role("System Manager");
	if (!allowed) {
		$(page.body).html('<div class="emd-message">You are not authorized to view this dashboard.</div>');
		return;
	}

	render_layout(page);
	load_dashboard();
};

const employeeServices = [
	["Permission Request", "Permission Request", "Request short permission or time away", "clock"],
	["Remote Work", "Remote Work Request", "Request remote work for specific dates", "laptop"],
	["Request Leave", "Leave Application", "Apply for leave and track your approval", "calendar"],
	["Return from Leave", "Return from Leave Request", "Confirm your return and medical clearance", "refresh-cw"],
	["Salary Certificate", "Salary Certificate Request", "Request an official salary certificate", "file-text"],
	["Overtime", "Pre Approved Overtime Request", "Request overtime pre-approval", "clock"],
	["Training", "Employee Training Request", "Request professional training", "book-open"],
	["Medical Allowance", "Children Medical Allowance Request", "Submit a child medical allowance claim", "heart"],
	["Company Car", "Company Car Request", "Request a company vehicle", "truck"],
	["Update My Data", "Employee Data Update Request", "Request a personal-record correction", "edit-3"],
];

function render_layout(page) {
	$(page.body).html(`
		<style>
			.emd-wrap { max-width: 1280px; margin: 0 auto; padding: 18px 10px 40px; color: #172033; }
			.emd-hero { position: relative; overflow: hidden; background: linear-gradient(125deg,#0b5671,#087f8c 58%,#25a18e); color:#fff; border-radius:22px; padding:30px 34px; box-shadow:0 16px 35px rgba(8,83,105,.22); }
			.emd-hero:after { content:""; position:absolute; width:260px; height:260px; border-radius:50%; right:-70px; top:-130px; background:rgba(255,255,255,.1); }
			.emd-hero h1 { color:#fff; margin:0 0 7px; font-size:35px; font-weight:750; }
			.emd-hero p { margin:0; font-size:16px; opacity:.92; }
			.emd-profile { display:flex; flex-wrap:wrap; gap:10px 22px; margin-top:18px; font-size:14px; }
			.emd-profile span { background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.2); border-radius:999px; padding:6px 11px; }
			.emd-stats { display:grid; grid-template-columns:repeat(4,minmax(180px,1fr)); gap:15px; margin:20px 0 28px; }
			.emd-stat { background:#fff; border:1px solid #e3eaf0; border-radius:15px; padding:19px 20px; box-shadow:0 6px 15px rgba(15,35,55,.06); }
			.emd-stat strong { display:block; font-size:32px; line-height:1.1; color:#0b6573; }
			.emd-stat span { display:block; margin-top:6px; color:#667085; font-size:13px; font-weight:600; text-transform:uppercase; letter-spacing:.35px; }
			.emd-heading { display:flex; justify-content:space-between; align-items:end; gap:12px; margin:0 0 14px; }
			.emd-heading h2 { margin:0; color:#172033; font-size:25px; font-weight:750; }
			.emd-heading p { margin:4px 0 0; color:#667085; }
			.emd-services { display:grid; grid-template-columns:repeat(3,minmax(250px,1fr)); gap:15px; }
			.emd-service { background:#fff; border:1px solid #e0e8ee; border-radius:16px; padding:19px; min-height:155px; display:flex; flex-direction:column; justify-content:space-between; transition:.18s ease; }
			.emd-service:hover { transform:translateY(-2px); box-shadow:0 10px 24px rgba(15,35,55,.09); border-color:#9dd8d2; }
			.emd-service-top { display:flex; gap:12px; }
			.emd-icon { width:38px; height:38px; flex:0 0 38px; display:grid; place-items:center; border-radius:11px; background:#e8f8f5; color:#087f70; }
			.emd-service h3 { margin:0 0 5px; font-size:17px; color:#172033; }
			.emd-service p { margin:0; color:#667085; font-size:13px; line-height:1.45; }
			.emd-actions { display:flex; align-items:center; justify-content:space-between; margin-top:16px; }
			.emd-count { color:#087f70; font-size:12px; font-weight:650; }
			.emd-new { border:0; border-radius:999px; padding:7px 13px; background:#0b7285; color:#fff; font-weight:650; font-size:12px; }
			.emd-new:hover { background:#095d6d; }
			.emd-lower { display:grid; grid-template-columns:1.5fr 1fr; gap:18px; margin-top:28px; }
			.emd-panel { background:#fff; border:1px solid #e0e8ee; border-radius:16px; padding:20px; }
			.emd-panel h2 { margin:0 0 14px; font-size:20px; }
			.emd-recent-row { display:grid; grid-template-columns:1fr auto; gap:8px; padding:12px 0; border-bottom:1px solid #edf1f4; text-decoration:none; color:inherit; }
			.emd-recent-row:last-child { border-bottom:0; }
			.emd-recent-row strong { display:block; font-size:14px; color:#253047; }
			.emd-recent-row small { color:#7a8495; }
			.emd-status { align-self:center; border-radius:999px; padding:4px 9px; background:#f1f5f7; color:#4b596b; font-size:11px; font-weight:650; }
			.emd-links { display:grid; gap:10px; }
			.emd-link { display:flex; justify-content:space-between; padding:11px 13px; border-radius:10px; background:#f6f9fa; color:#0b6573; text-decoration:none; font-weight:650; }
			.emd-message { margin:20px; padding:20px; border-radius:12px; background:#fff7e6; border:1px solid #ffd591; color:#7c4a03; }
			.emd-empty { color:#7a8495; padding:16px 0; }
			@media(max-width:1050px){.emd-stats{grid-template-columns:repeat(2,1fr)}.emd-services{grid-template-columns:repeat(2,1fr)}}
			@media(max-width:700px){.emd-hero{padding:24px}.emd-hero h1{font-size:28px}.emd-stats,.emd-services,.emd-lower{grid-template-columns:1fr}}
		</style>
		<div class="emd-wrap">
			<section class="emd-hero">
				<h1 id="emd-welcome">Welcome</h1>
				<p>Your Medical HR self-service center for requests, leave, records, and benefits.</p>
				<div class="emd-profile">
					<span id="emd-id">Employee: —</span><span id="emd-role">Designation: —</span><span id="emd-department">Department: —</span>
				</div>
			</section>
			<div id="emd-alert"></div>
			<section class="emd-stats">
				<div class="emd-stat"><strong id="emd-total">0</strong><span>My Requests</span></div>
				<div class="emd-stat"><strong id="emd-pending">0</strong><span>Pending</span></div>
				<div class="emd-stat"><strong id="emd-approved">0</strong><span>Approved</span></div>
				<div class="emd-stat"><strong id="emd-leave">0</strong><span>Leave Applications</span></div>
			</section>
			<section class="emd-panel" id="emd-leave-summary" style="margin-bottom:24px" aria-live="polite"></section>
			<div class="emd-heading"><div><h2>Employee Services</h2><p>Create and track your HR requests.</p></div></div>
			<section class="emd-services" id="emd-services"></section>
			<section class="emd-lower">
				<div class="emd-panel"><h2>Recent Requests</h2><div id="emd-recent"></div></div>
				<div class="emd-panel"><h2>Quick Links</h2><div class="emd-links">
					<a class="emd-link" id="emd-my-leave" href="#">My Leave Applications <span>→</span></a>
					<a class="emd-link" href="/app/attendance-request">Attendance Requests <span>→</span></a>
					<a class="emd-link" href="/app/expense-claim">Expense Claims <span>→</span></a>
					<a class="emd-link" id="emd-profile-link" href="/app/employee">My Employee Profile <span>→</span></a>
				</div></div>
			</section>
		</div>
	`);
}

function render_services(counts, employee) {
	const html = employeeServices.map(([title, doctype, description, icon]) => `
		<article class="emd-service">
			<div class="emd-service-top"><span class="emd-icon">${frappe.utils.icon(icon, "sm")}</span><div><h3>${frappe.utils.escape_html(title)}</h3><p>${frappe.utils.escape_html(description)}</p></div></div>
			<div class="emd-actions"><button class="btn btn-link emd-count" data-doctype="${frappe.utils.escape_html(doctype)}">${counts[doctype] || 0} request(s)</button><button class="emd-new" data-doctype="${frappe.utils.escape_html(doctype)}">New Request</button></div>
		</article>`).join("");
	$("#emd-services").html(html);
	$("#emd-my-leave").off("click").on("click", event => {
		event.preventDefault();
		$('.emd-count[data-doctype="Leave Application"]').trigger("click");
	});
	$(".emd-count").on("click", function () {
		const doctype = $(this).data("doctype");
		frappe.call({method: "medical_hrms.self_service.my_requests", args: {doctype}, callback: (r) => {
			const rows = (r.message || []).map(row => `<p><button type="button" class="btn btn-link emd-view-request" data-name="${frappe.utils.escape_html(row.name)}">${frappe.utils.escape_html(row.name)}</button> — ${frappe.utils.escape_html(row.status)}</p>`).join("");
			const list = new frappe.ui.Dialog({title: __("My Requests"), fields: [{fieldtype: "HTML", fieldname: "requests", options: rows || __("No requests yet.")}]});
			list.$wrapper.on("click", ".emd-view-request", function () { emdShowRequestDetails(doctype, $(this).attr("data-name")); });
			list.show();
		}});
	});
	$(".emd-new").on("click", function () {
		const doctype = $(this).data("doctype");
		frappe.call({method: "medical_hrms.self_service.form_schema", args: {doctype}, callback: (r) => {
			const schema = r.message || [];
			const timeFields = schema.filter(field => field.fieldtype === "Time");
			const fields = schema.flatMap(field => {
				if (field.fieldtype !== "Time") return [field];
				const prefix = `emd_time_${field.fieldname}`;
				return [
					{fieldtype: "Section Break", label: __(field.label)},
					{fieldname: `${prefix}_hour`, label: __("Hour"), fieldtype: "Select", options: ["", ...Array.from({length: 12}, (_, i) => String(i + 1).padStart(2, "0"))], reqd: field.reqd},
					{fieldtype: "Column Break"},
					{fieldname: `${prefix}_minute`, label: __("Minute"), fieldtype: "Select", options: ["", ...Array.from({length: 60}, (_, i) => String(i).padStart(2, "0"))], reqd: field.reqd},
					{fieldtype: "Column Break"},
					{fieldname: `${prefix}_period`, label: __("AM / PM"), fieldtype: "Select", options: ["", "AM", "PM"], reqd: field.reqd},
					{fieldtype: "Section Break"},
				];
			});
			fields.forEach(field => {
				if (field.fieldtype === "Attach") field.options = {restrictions: {allow_public: false}};
				if (field.fieldname === "leave_application") field.get_query = () => ({filters: {employee}});
			});
			const dialog = new frappe.ui.Dialog({
				title: __(doctype),
				fields: [{fieldtype: "HTML", options: `<p>${__("This request is linked to your login automatically. Approval and clearance decisions are handled by HR.")}</p>${doctype === "Leave Application" ? `<p>${__("Annual and medical/sick leave use separate entitlements. Select the correct leave type; ask HR which medical pay category applies. No default casual-leave allowance is included.")}</p>` : ""}`}, ...fields],
				primary_action_label: __("Send Request"),
				primary_action: () => save(true),
				secondary_action_label: doctype === "Leave Application" ? undefined : __("Save Draft"),
				secondary_action: doctype === "Leave Application" ? undefined : () => save(false),
			});
			let saving = false;
			const save = (send) => {
				const values = dialog.get_values();
				if (!values || saving) return;
				for (const field of timeFields) {
					const prefix = `emd_time_${field.fieldname}`;
					const hour = values[`${prefix}_hour`];
					const minute = values[`${prefix}_minute`];
					const period = values[`${prefix}_period`];
					if ((hour || minute || period) && !(hour && minute && period)) {
						frappe.msgprint(__("Select the hour, minute, and AM/PM for {0}.", [__(field.label)]));
						return;
					}
					values[field.fieldname] = hour ? emdTimeTo24Hour(hour, minute, period) : "";
					delete values[`${prefix}_hour`];
					delete values[`${prefix}_minute`];
					delete values[`${prefix}_period`];
				}
				saving = true;
				frappe.call({
					method: "medical_hrms.self_service.save_request",
					args: {doctype, values: JSON.stringify(values), send: send ? 1 : 0},
					freeze: true,
					callback: () => { dialog.hide(); frappe.show_alert({message: send ? __("Request sent for review") : __("Draft saved"), indicator: "green"}); load_dashboard(); },
					always: () => { saving = false; },
				});
			};
			dialog.show();
		}});
	});
}

function emdTimeTo24Hour(hour, minute, period) {
	const hour24 = (Number(hour) % 12) + (period === "PM" ? 12 : 0);
	return `${String(hour24).padStart(2, "0")}:${minute}:00`;
}

function emdShowRequestDetails(doctype, name) {
	frappe.call({method: "medical_hrms.self_service.request_details", args: {doctype, name}, freeze: true, callback: (r) => {
		const data = r.message;
		if (!data) return;
		const esc = value => frappe.utils.escape_html(String(value ?? ""));
		const details = data.fields.map(field => {
			let value = field.value;
			if (field.fieldtype === "Check") value = Number(value) ? __("Yes") : __("No");
			let content = esc(value === null || value === "" ? "—" : value);
			if (field.fieldtype === "Attach" && /^\/(private\/)?files\//.test(value || "")) {
				content = `<a href="${esc(value)}" target="_blank" rel="noopener noreferrer">${esc(__("View attachment"))}</a>`;
			}
			return `<div style="padding:12px 0;border-bottom:1px solid var(--border-color)"><div class="text-muted small">${esc(__(field.label))}</div><div style="white-space:pre-wrap;overflow-wrap:anywhere;margin-top:4px">${content}</div></div>`;
		}).join("");
		const dialog = new frappe.ui.Dialog({title: __(doctype), fields: [{fieldtype: "HTML", options: `<p><strong>${esc(data.name)}</strong> — ${esc(__(data.status))}</p>${details}`}], primary_action_label: __("Close"), primary_action: () => dialog.hide()});
		dialog.show();
	}});
}

function render_recent(rows) {
	if (!rows.length) {
		$("#emd-recent").html('<div class="emd-empty">No requests yet. Choose a service above to get started.</div>');
		return;
	}
	$("#emd-recent").html(rows.map((row) => `
		<div class="emd-recent-row">
			<div><strong>${frappe.utils.escape_html(row.doctype)}</strong><small>${frappe.utils.escape_html(row.name)} · ${frappe.datetime.comment_when(row.modified)}</small>${employeeServices.some(service => service[1] === row.doctype) ? `<button type="button" class="btn btn-link emd-recent-details" data-doctype="${frappe.utils.escape_html(row.doctype)}" data-name="${frappe.utils.escape_html(row.name)}">${__("View details")}</button>` : ""}</div>
			<span class="emd-status">${frappe.utils.escape_html(row.status)}</span>
		</div>`).join(""));
	$("#emd-recent .emd-recent-details").on("click", function () {
		emdShowRequestDetails($(this).attr("data-doctype"), $(this).attr("data-name"));
	});
}

function load_dashboard() {
	frappe.call({
		method: "medical_hrms.medical_hrms.page.employee_dashboard.employee_dashboard.get_dashboard_data",
		freeze: true,
		callback(r) {
			const data = r.message || {};
			const user = data.user || {};
			$("#emd-welcome").text(`Welcome, ${user.full_name || "Employee"}`);
			if (data.status !== "success" || !data.employee) {
				$("#emd-alert").html(`<div class="emd-message">${frappe.utils.escape_html(data.message || "Employee profile not found.")}</div>`);
				render_services({}, null);
				$(".emd-new").prop("disabled", true);
				return;
			}

			const employee = data.employee;
			const stats = data.stats || {};
			$("#emd-id").text(`Employee: ${employee.name}`);
			$("#emd-role").text(`Designation: ${employee.designation || "—"}`);
			$("#emd-department").text(`Department: ${employee.department || "—"}`);
			$("#emd-total").text(stats.total || 0);
			$("#emd-pending").text(stats.pending || 0);
			$("#emd-approved").text(stats.approved || 0);
			$("#emd-leave").text(stats.leave_applications || 0);
			emdRenderLeaveSummary(data.leave_summary);
			$("#emd-profile-link").attr("href", "#").off("click").on("click", (event) => {
				event.preventDefault();
				const esc = frappe.utils.escape_html;
				frappe.msgprint({title: __("My Profile"), message: `<p>${esc(employee.employee_name)}</p><p>${esc(employee.designation || "")} · ${esc(employee.department || "")}</p><p>${esc(employee.company || "")}</p><p>Use Update My Data to request a correction from HR.</p>`});
			});
			render_services(data.counts || {}, employee.name);
			render_recent(data.recent_requests || []);
		},
	});
}

function emdRenderLeaveSummary(summary) {
	if (!summary) return;
	const esc = value => frappe.utils.escape_html(String(value ?? ""));
	const rows = Object.entries(summary.balances || {}).map(([type, balance]) => `<tr><td>${esc(type)}</td><td>${esc(balance.total_leaves)}</td><td>${esc(balance.leaves_taken)}</td><td>${esc(balance.leaves_pending_approval)}</td><td>${esc(balance.remaining_leaves)}</td></tr>`).join("");
	const monthly = (label, usage) => {
		const used = usage.used === null ? __("Holiday calendar setup needed") : `${usage.used} ${__("used / pending")}`;
		const limit = usage.limit === null ? __("Monthly limit not enabled") : `${usage.limit} ${__("allowed")}${usage.used === null ? "" : ` · ${Math.max(0, usage.limit - usage.used)} ${__("remaining")}`}`;
		return `<p><strong>${esc(label)}</strong>: ${esc(used)} · ${esc(limit)}</p>`;
	};
	$("#emd-leave-summary").html(`<h2>${__("My Leave Balances")}</h2>${rows ? `<div style="overflow-x:auto"><table class="table"><thead><tr><th>${__("Leave Type")}</th><th>${__("Allocated")}</th><th>${__("Taken")}</th><th>${__("Pending")}</th><th>${__("Balance")}</th></tr></thead><tbody>${rows}</tbody></table></div>` : `<p>${__("No active leave allocations. Contact HR to configure your entitlement.")}</p>`}<p class="text-muted">${__("Balances follow your active allocations; pending requests are shown separately.")}</p><h3>${__("Monthly Usage")} — ${esc(summary.month)}</h3>${monthly(summary.half_day.leave_type ? `${__("Half-day requests")} (${summary.half_day.leave_type})` : __("Half-day requests"), summary.half_day)}${monthly(__("Work-from-home working days"), summary.remote_work)}`);
}
})();
