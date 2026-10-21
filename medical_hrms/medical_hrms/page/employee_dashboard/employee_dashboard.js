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

	MhPortal.mount(page, { portal: "employee", active: "dashboard", crumb: __("Dashboard") });
	MhPortal.on("new-request", (doctype) => emdNewRequest(doctype));
	MhPortal.on("profile", () => emdShowProfile());
	render_layout(page);
	load_dashboard(true);
};

const esc = (value) => frappe.utils.escape_html(String(value ?? ""));
let currentEmployee = null;

// [title, doctype, description, icon, tone]
const employeeServices = [
	[__("Permission Request"), "Permission Request", __("Request short permission or time away"), "fa-clock", ""],
	[__("Remote Work"), "Remote Work Request", __("Request remote work for specific dates"), "fa-laptop-house", "sky"],
	[__("Request Leave"), "Leave Application", __("Apply for leave and track your approval"), "fa-calendar-check", ""],
	[__("Return from Leave"), "Leave Return Request", __("Confirm your return and medical clearance"), "fa-rotate-left", "violet"],
	[__("Salary Certificate"), "Salary Certificate Request", __("Request an official salary certificate"), "fa-file-invoice", ""],
	[__("Overtime"), "Pre Approved Overtime Request", __("Request overtime pre-approval"), "fa-business-time", "amber"],
	[__("Training"), "Employee Training Request", __("Request professional training"), "fa-chalkboard", "sky"],
	[__("Medical Allowance"), "Children Medical Allowance Request", __("Submit a child medical allowance claim"), "fa-hand-holding-medical", "rose"],
	[__("Company Car"), "Company Car Request", __("Request a company vehicle"), "fa-car", ""],
	[__("Update My Data"), "Employee Data Update Request", __("Request a personal-record correction"), "fa-user-pen", "amber"],
];

function render_layout(page) {
	const name = frappe.session.user_fullname || frappe.session.user;
	const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map((s) => s[0].toUpperCase()).join("");
	const $wrap = $('<div class="emd-wrap"></div>');
	$wrap.append(MhPortal.head({
		initials, iconId: "emd-avatar", eyebrow: __("Employee Portal"), title: name, titleId: "emd-welcome",
		meta: [
			{ icon: "fa-building", text: __("Department: —"), id: "emd-department" },
			{ icon: "fa-envelope", text: frappe.session.user },
			{ icon: "fa-id-card", text: __("Employee: —"), id: "emd-id" },
			{ icon: "fa-briefcase", text: __("Designation: —"), id: "emd-role" },
		],
	}));
	$wrap.append(`
		<div id="emd-alert"></div>
		<div id="emd-banner"></div>
		<section class="mhp-section">
			${MhPortal.sectionHead("fa-chart-line", __("Today at a Glance"), __("Your requests and leave at a glance."))}
			<div class="mhp-stats">
				${MhPortal.stat({ id: "emd-total", icon: "fa-folder-open", label: __("My Requests"), note: __("All requests you sent") })}
				${MhPortal.stat({ id: "emd-pending", icon: "fa-hourglass-half", tone: "amber", label: __("Pending"), note: __("Waiting for a decision") })}
				${MhPortal.stat({ id: "emd-approved", icon: "fa-circle-check", tone: "sky", label: __("Approved"), note: __("Approved, completed or issued") })}
				${MhPortal.stat({ id: "emd-leave", icon: "fa-calendar-check", tone: "violet", label: __("Leave Applications"), note: __("Leave you applied for") })}
			</div>
		</section>
		<section class="mhp-section">
			<div class="mhp-card" id="emd-leave-summary" aria-live="polite"><div class="mhp-empty"><i class="fa-solid fa-umbrella-beach"></i>${esc(__("Loading your leave balances..."))}</div></div>
		</section>
		<section class="mhp-section">
			${MhPortal.sectionHead("fa-grip", __("Employee Services"), __("Create and track your HR requests."))}
			<div class="mhp-grid" id="emd-services"></div>
		</section>
		<section class="mhp-section mhp-two">
			<div class="mhp-card" id="emd-recent-card"><h3><i class="fa-solid fa-list-check" aria-hidden="true"></i>${esc(__("Recent Requests"))}</h3><div id="emd-recent" class="mhp-rows"></div></div>
			<div class="mhp-card"><h3><i class="fa-solid fa-link" aria-hidden="true"></i>${esc(__("Quick Links"))}</h3><div class="mhp-stack">
				<a class="mhp-quick" id="emd-my-leave" href="#"><span>${esc(__("My Leave Applications"))}</span><i class="fa-solid fa-arrow-right"></i></a>
				<a class="mhp-quick" href="/app/attendance-request"><span>${esc(__("Attendance Requests"))}</span><i class="fa-solid fa-arrow-right"></i></a>
				<a class="mhp-quick" href="/app/expense-claim"><span>${esc(__("Expense Claims"))}</span><i class="fa-solid fa-arrow-right"></i></a>
				<a class="mhp-quick" id="emd-profile-link" href="/app/employee"><span>${esc(__("My Employee Profile"))}</span><i class="fa-solid fa-arrow-right"></i></a>
			</div></div>
		</section>`);
	$(page.body).html($wrap);
}

const setMeta = (id, text) => $(`#${id} .mhp-meta-text`).text(text);

function render_services(counts) {
	const html = employeeServices.map(([title, doctype, description, icon, tone]) => `
		<article class="mhp-tile emd-service">
			<div class="mhp-tile-top"><span class="mhp-tile-icon ${esc(tone)}"><i class="fa-solid ${esc(icon)}" aria-hidden="true"></i></span><div><h4>${esc(title)}</h4><p>${esc(description)}</p></div></div>
			<div class="mhp-tile-foot"><button type="button" class="mhp-textbtn emd-count" data-doctype="${esc(doctype)}">${esc(__("{0} request(s)", [counts[doctype] || 0]))}</button><button type="button" class="mhp-btn primary sm emd-new" data-doctype="${esc(doctype)}"><i class="fa-solid fa-plus" aria-hidden="true"></i>${esc(__("New Request"))}</button></div>
		</article>`).join("");
	$("#emd-services").html(html);
	$("#emd-my-leave").off("click").on("click", event => {
		event.preventDefault();
		emdMyRequests("Leave Application");
	});
	$(".emd-count").on("click", function () { emdMyRequests($(this).data("doctype")); });
	$(".emd-new").on("click", function () { emdNewRequest($(this).data("doctype")); });
}

function emdMyRequests(doctype) {
	frappe.call({method: "medical_hrms.self_service.my_requests", args: {doctype}, callback: (r) => {
		const rows = (r.message || []).map(row => `<p><button type="button" class="btn btn-link emd-view-request" data-name="${esc(row.name)}">${esc(row.name)}</button> — ${esc(row.status)}</p>`).join("");
		const list = new frappe.ui.Dialog({title: __("My Requests"), fields: [{fieldtype: "HTML", fieldname: "requests", options: rows || __("No requests yet.")}]});
		list.$wrapper.on("click", ".emd-view-request", function () { emdShowRequestDetails(doctype, $(this).attr("data-name")); });
		list.show();
	}});
}

function emdNewRequest(doctype) {
	if (!currentEmployee) {
		frappe.msgprint(__("Your user account is not linked to an Employee record. Please contact HR."));
		return;
	}
	const employee = currentEmployee.name;
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
}

function emdTimeTo24Hour(hour, minute, period) {
	const hour24 = (Number(hour) % 12) + (period === "PM" ? 12 : 0);
	return `${String(hour24).padStart(2, "0")}:${minute}:00`;
}

function emdShowRequestDetails(doctype, name) {
	frappe.call({method: "medical_hrms.self_service.request_details", args: {doctype, name}, freeze: true, callback: (r) => {
		const data = r.message;
		if (!data) return;
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

function emdShowProfile() {
	const employee = currentEmployee;
	if (!employee) {
		frappe.msgprint(__("Your user account is not linked to an Employee record. Please contact HR."));
		return;
	}
	frappe.msgprint({title: __("My Profile"), message: `<p>${esc(employee.employee_name)}</p><p>${esc(employee.designation || "")} · ${esc(employee.department || "")}</p><p>${esc(employee.company || "")}</p><p>${esc(__("Use Update My Data to request a correction from HR."))}</p>`});
}

const statusTone = (status) => /^pending/i.test(status || "") ? "amber" : (/approved|completed|issued/i.test(status || "") ? "teal" : (/rejected|cancel|declined/i.test(status || "") ? "rose" : ""));

function render_recent(rows) {
	if (!rows.length) {
		$("#emd-recent").html(`<div class="mhp-empty"><i class="fa-regular fa-folder-open"></i>${esc(__("No requests yet. Choose a service above to get started."))}</div>`);
		return;
	}
	$("#emd-recent").html(rows.map((row) => `
		<div class="mhp-row emd-recent-row">
			<div><b>${esc(__(row.doctype))}</b><small>${esc(row.name)} · ${frappe.datetime.comment_when(row.modified)}</small>${employeeServices.some(service => service[1] === row.doctype) ? `<div><button type="button" class="mhp-textbtn emd-recent-details" data-doctype="${esc(row.doctype)}" data-name="${esc(row.name)}">${esc(__("View details"))}</button></div>` : ""}</div>
			<span class="mhp-pill ${statusTone(row.status)} emd-status">${esc(__(row.status))}</span>
		</div>`).join(""));
	$("#emd-recent .emd-recent-details").on("click", function () {
		emdShowRequestDetails($(this).attr("data-doctype"), $(this).attr("data-name"));
	});
}

function render_banner(data) {
	const pending = (data.recent_requests || []).filter((row) => /^pending/i.test(row.status || ""));
	const balances = Object.entries((data.leave_summary && data.leave_summary.balances) || {});
	const annual = balances.find(([type]) => /annual/i.test(type)) || balances[0];
	const leaveText = annual ? __("{0}: {1} days left", [annual[0], annual[1].remaining_leaves]) : __("No leave allocation yet - contact HR to set your entitlement.");
	const count = (data.stats && data.stats.pending) || 0;
	const body = pending.length ? `<div class="mhp-rows">${pending.map((row) => `<div class="mhp-row"><div><b>${esc(__(row.doctype))}</b><small>${esc(row.name)} · ${frappe.datetime.comment_when(row.modified)}</small></div><span class="mhp-pill amber">${esc(__(row.status))}</span></div>`).join("")}</div>` : "";
	$("#emd-banner").html(MhPortal.banner(count ? {
		icon: "fa-hourglass-half", tone: "warn",
		title: count === 1 ? __("1 of your requests is waiting for a decision") : __("{0} of your requests are waiting for a decision", [count]),
		text: leaveText, body,
	} : { icon: "fa-mug-hot", title: __("Nothing waiting for a decision"), text: leaveText }));
}

function load_dashboard(first) {
	frappe.call({
		method: "medical_hrms.medical_hrms.page.employee_dashboard.employee_dashboard.get_dashboard_data",
		freeze: true,
		callback(r) {
			const data = r.message || {};
			const user = data.user || {};
			$("#emd-welcome").text(user.full_name || __("Employee"));
			if (data.status !== "success" || !data.employee) {
				currentEmployee = null;
				$("#emd-alert").html(`<div class="mhp-alert emd-message">${esc(data.message || __("Employee profile not found."))}</div>`);
				$("#emd-leave-summary").html(`<div class="mhp-empty"><i class="fa-solid fa-user-slash"></i>${esc(__("No employee record is linked to your login."))}</div>`);
				render_services({});
				render_recent([]);
				$(".emd-new").prop("disabled", true);
				return;
			}

			const employee = currentEmployee = data.employee;
			const stats = data.stats || {};
			$("#emd-welcome").text(employee.employee_name || user.full_name || __("Employee"));
			if (employee.image) $("#emd-avatar").html(`<img src="${esc(employee.image)}" alt="" onerror="this.remove()">`);
			setMeta("emd-id", __("Employee: {0}", [employee.name]));
			setMeta("emd-role", __("Designation: {0}", [employee.designation || "—"]));
			setMeta("emd-department", __("Department: {0}", [employee.department || "—"]));
			$("#emd-total").text(stats.total || 0);
			$("#emd-pending").text(stats.pending || 0);
			$("#emd-approved").text(stats.approved || 0);
			$("#emd-leave").text(stats.leave_applications || 0);
			emdRenderLeaveSummary(data.leave_summary);
			render_banner(data);
			$("#emd-profile-link").attr("href", "#").off("click").on("click", (event) => {
				event.preventDefault();
				emdShowProfile();
			});
			render_services(data.counts || {});
			render_recent(data.recent_requests || []);
			if (first) MhPortal.runPending();
		},
	});
}

function emdRenderLeaveSummary(summary) {
	if (!summary) return;
	const rows = Object.entries(summary.balances || {}).map(([type, balance]) => `<tr><td>${esc(type)}</td><td class="num">${esc(balance.total_leaves)}</td><td class="num">${esc(balance.leaves_taken)}</td><td class="num">${esc(balance.leaves_pending_approval)}</td><td class="num"><b>${esc(balance.remaining_leaves)}</b></td></tr>`).join("");
	const monthly = (label, usage) => {
		const used = usage.used === null ? __("Holiday calendar setup needed") : `${usage.used} ${__("used / pending")}`;
		const limit = usage.limit === null ? __("Monthly limit not enabled") : `${usage.limit} ${__("allowed")}${usage.used === null ? "" : ` · ${Math.max(0, usage.limit - usage.used)} ${__("remaining")}`}`;
		return `<div class="mhp-row"><div><b>${esc(label)}</b><small>${esc(used)}</small></div><span class="mhp-pill">${esc(limit)}</span></div>`;
	};
	$("#emd-leave-summary").html(`
		<h3><i class="fa-solid fa-umbrella-beach" aria-hidden="true"></i>${__("My Leave Balances")}</h3>
		${rows ? `<div class="mhp-tablewrap"><table class="mhp-table"><thead><tr><th>${__("Leave Type")}</th><th class="num">${__("Allocated")}</th><th class="num">${__("Taken")}</th><th class="num">${__("Pending")}</th><th class="num">${__("Balance")}</th></tr></thead><tbody>${rows}</tbody></table></div>` : `<p>${__("No active leave allocations. Contact HR to configure your entitlement.")}</p>`}
		<p class="mhp-muted" style="margin:10px 0 18px">${__("Balances follow your active allocations; pending requests are shown separately.")}</p>
		<h3 style="font-size:16px"><i class="fa-solid fa-calendar-days" aria-hidden="true"></i>${__("Monthly Usage")} — ${esc(summary.month)}</h3>
		<div class="mhp-rows">${monthly(summary.half_day.leave_type ? `${__("Half-day requests")} (${summary.half_day.leave_type})` : __("Half-day requests"), summary.half_day)}${monthly(__("Work-from-home working days"), summary.remote_work)}</div>`);
}
})();
