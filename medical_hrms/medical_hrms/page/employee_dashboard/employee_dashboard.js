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

frappe.pages["employee-dashboard"].on_page_show = function () {
	const options = frappe.route_options || {};
	if (options.request && options.name) {
		frappe.route_options = null;
		emdShowRequestDetails(options.request, options.name);
	}
};

const esc = (value) => frappe.utils.escape_html(String(value ?? ""));
let currentEmployee = null;

// [title, doctype, description, icon, tone]
// The leave services first, in the order they are used: plan, apply, come back.
const employeeServices = [
	[__("Leave Plan"), "Leave Plan Request", __("Plan your leave dates for the year; your manager approves the plan"), "fa-calendar-week", "sky"],
	[__("Leave Application"), "Leave Application", __("Apply for leave you hold; your manager approves it"), "fa-calendar-check", ""],
	[__("Leave Return"), "Leave Return Request", __("Tell HR you are back after a leave"), "fa-rotate-left", "violet"],
	[__("Permission Request"), "Permission Request", __("Request short permission or time away"), "fa-clock", ""],
	[__("Remote Work"), "Remote Work Request", __("Request remote work for specific dates"), "fa-laptop-house", "sky"],
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
		const rows = (r.message || []).map(row => `<p><button type="button" class="btn btn-link emd-view-request" data-name="${esc(row.name)}">${esc(row.name)}</button> ${emdStatusPill(row.status)}</p>`).join("");
		const list = new frappe.ui.Dialog({title: __("My Requests"), fields: [{fieldtype: "HTML", fieldname: "requests", options: rows || __("No requests yet.")}]});
		list.$wrapper.on("click", ".emd-view-request", function () { emdShowRequestDetails(doctype, $(this).attr("data-name")); });
		list.show();
	}});
}

const LEAVE_INTRO = {
	"Leave Plan Request": __("Plan when you want to take leave this year. Your manager and then your department head approve the plan. It does not use your balance: when the time comes, open the approved plan here and click Apply now."),
	"Leave Application": __("Only the leave you hold is listed, with the days you have left. Your manager approves the request and HR is informed. For sick leave, tell HR on your first sick day so they can start your sick leave year."),
	"Leave Return Request": __("Choose the leave you are coming back from and the day you returned to work. After sick leave, attach your fitness certificate."),
};

// Leave types the employee holds, as Select options "Annual Leave (19 days left)".
function emdLeaveTypeField(field) {
	return frappe.call({ method: "medical_hrms.self_service.my_leave_types" }).then((r) => {
		const choices = r.message || [];
		return choices.length ? Object.assign({}, field, { fieldtype: "Select", options: [{ label: "", value: "" }, ...choices.map((c) => ({ label: c.label, value: c.leave_type }))] }) : null;
	});
}

// opts.name: change the employee's own draft; opts.resend_of: send a rejected request again as a new one.
function emdNewRequest(doctype, prefill, plan, opts) {
	opts = opts || {};
	if (!currentEmployee) {
		frappe.msgprint(__("Your user account is not linked to an Employee record. Please contact HR."));
		return;
	}
	const employee = currentEmployee.name;
	frappe.call({method: "medical_hrms.self_service.form_schema", args: {doctype}, callback: async (r) => {
		let schema = r.message || [];
		const leaveTypeIndex = schema.findIndex((field) => field.fieldname === "leave_type");
		if (leaveTypeIndex > -1) {
			const select = await emdLeaveTypeField(schema[leaveTypeIndex]);
			if (!select) {
				frappe.msgprint({ title: __("No leave to apply for yet"), message: __("You do not hold any leave yet. HR assigns your annual leave at the start of the leave year; ask HR if it is missing.") });
				return;
			}
			schema = schema.map((field, i) => (i === leaveTypeIndex ? select : field));
		}
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
			if (field.fieldname === "leave_application") {
				field.get_query = () => ({filters: {employee, status: "Approved", docstatus: 1}});
				field.onchange = () => emdReturnContext(dialog);
			}
		});
		const intro = opts.name ? __("You are changing your draft {0}. Save Draft keeps it for later; Send Request sends it for review.", [opts.name])
			: opts.resend_of ? __("A new request in place of {0}, which was rejected. Change what is needed and send it; HR sees the rejected one with it.", [opts.resend_of])
			: (LEAVE_INTRO[doctype] || __("This request is linked to your login automatically. Approval and clearance decisions are handled by HR."));
		const dialog = new frappe.ui.Dialog({
			title: opts.name ? __("Edit Draft: {0}", [__(doctype)]) : opts.resend_of ? __("Send Again: {0}", [__(doctype)]) : __(doctype),
			fields: [{fieldtype: "HTML", options: `<p>${esc(intro)}</p>`}, ...fields],
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
				args: {doctype, values: JSON.stringify(values), send: send ? 1 : 0, plan: plan || undefined, name: opts.name || undefined, resend_of: opts.resend_of || undefined},
				freeze: true,
				callback: () => { dialog.hide(); frappe.show_alert({message: send ? __("Request sent for review") : __("Draft saved"), indicator: "green"}); load_dashboard(); },
				always: () => { saving = false; },
			});
		};
		dialog.show();
		if (prefill) dialog.set_values(emdDialogValues(prefill, timeFields)).then(() => doctype === "Leave Return Request" && emdReturnContext(dialog));
	}});
}

// Leave Return: show when the employee was due back, and ask for the fitness certificate only after sick leave.
function emdReturnContext(dialog) {
	const leave = dialog.get_value("leave_application");
	if (!leave || !dialog.fields_dict.fitness_certificate) return;
	frappe.call({ method: "medical_hrms.self_service.leave_return_context", args: { leave_application: leave } }).then((r) => {
		const c = r.message || {};
		dialog.set_df_property("fitness_certificate", "reqd", c.is_sick_leave ? 1 : 0);
		dialog.set_df_property("fitness_certificate", "hidden", c.is_sick_leave ? 0 : 1);
		dialog.set_df_property("actual_return_date", "description", __("You were due back on {0}.", [frappe.datetime.str_to_user(c.expected_back_on)]));
		if (!dialog.get_value("actual_return_date")) dialog.set_value("actual_return_date", c.expected_back_on);
	});
}

// Saved values -> dialog values: a time "14:30:00" fills the hour / minute / AM-PM pickers.
function emdDialogValues(values, timeFields) {
	const out = {};
	Object.entries(values || {}).forEach(([fieldname, value]) => {
		if (value === null || value === undefined || value === "") return;
		if (!timeFields.some((field) => field.fieldname === fieldname)) {
			out[fieldname] = value;
			return;
		}
		const [hour, minute] = String(value).split(":").map(Number);
		const prefix = `emd_time_${fieldname}`;
		out[`${prefix}_hour`] = String(hour % 12 || 12).padStart(2, "0");
		out[`${prefix}_minute`] = String(minute || 0).padStart(2, "0");
		out[`${prefix}_period`] = hour >= 12 ? "PM" : "AM";
	});
	return out;
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
		const openLink = (other) => `<button type="button" class="btn btn-link btn-xs emd-open-request" data-name="${esc(other)}" style="padding:0;vertical-align:baseline">${esc(other)}</button>`;
		const reason = data.rejection_reason ? `<div class="alert alert-danger emd-reason" style="margin:10px 0"><b>${esc(__("Rejection reason"))}</b><div style="white-space:pre-wrap;margin-top:4px">${esc(data.rejection_reason)}</div></div>` : "";
		const links = [
			data.resubmitted_from ? __("Sent again in place of {0}, which was rejected.", [openLink(data.resubmitted_from)]) : "",
			data.resent_as ? __("Sent again as {0}.", [openLink(data.resent_as)]) : "",
		].filter(Boolean).map((text) => `<p class="emd-resend-link">${text}</p>`).join("");
		const steps = (data.history || []).map((step) => `<li style="padding:4px 0">${emdStatusPill(step.status)}
			<small class="text-muted" style="margin-left:8px">${esc(step.by)} · ${esc(frappe.datetime.str_to_user(step.on))}</small></li>`).join("");
		const history = steps ? `<h5 style="margin:18px 0 6px">${esc(__("History"))}</h5><ol class="emd-history" style="list-style:none;padding:0;margin:0">${steps}</ol>` : "";
		const actions = [
			data.can_edit ? `<button type="button" class="btn btn-primary btn-sm emd-edit-draft">${esc(__("Edit Draft"))}</button>` : "",
			data.can_edit ? `<button type="button" class="btn btn-default btn-sm emd-delete-draft">${esc(__("Delete Draft"))}</button>` : "",
			data.can_resend ? `<button type="button" class="btn btn-primary btn-sm emd-resend">${esc(doctype === "Leave Application" ? __("Apply Again") : __("Send Again"))}</button>` : "",
		].filter(Boolean).join(" ");
		const dialog = new frappe.ui.Dialog({title: __(doctype), fields: [{fieldtype: "HTML", options: `<p><strong>${esc(data.name)}</strong> ${emdStatusPill(data.status, "emd-detail-status")}</p>
			${reason}${links}${actions ? `<div class="emd-actions" style="display:flex;gap:8px;flex-wrap:wrap;margin:10px 0">${actions}</div>` : ""}${details}${history}`}],
			primary_action_label: __("Close"), primary_action: () => dialog.hide()});
		dialog.$wrapper.on("click", ".emd-open-request", function () { dialog.hide(); emdShowRequestDetails(doctype, $(this).attr("data-name")); });
		// The My Requests list may be open behind: close it too, it would show the old status.
		dialog.$wrapper.on("click", ".emd-edit-draft", () => { emdCloseDialogs(); emdNewRequest(doctype, data.values, null, {name: data.name}); });
		dialog.$wrapper.on("click", ".emd-resend", () => { emdCloseDialogs(); emdNewRequest(doctype, data.values, null, {resend_of: data.name}); });
		dialog.$wrapper.on("click", ".emd-delete-draft", () => frappe.confirm(__("Delete the draft {0}? This cannot be undone.", [data.name]), () =>
			frappe.call({method: "medical_hrms.self_service.delete_draft", args: {doctype, name: data.name}, freeze: true, callback: () => {
				emdCloseDialogs();
				frappe.show_alert({message: __("Draft deleted"), indicator: "green"});
				load_dashboard();
			}})));
		dialog.show();
	}});
}

function emdCloseDialogs() {
	[...(frappe.ui.open_dialogs || [])].forEach((d) => d.hide());
}

function emdShowProfile() {
	const employee = currentEmployee;
	if (!employee) {
		frappe.msgprint(__("Your user account is not linked to an Employee record. Please contact HR."));
		return;
	}
	frappe.msgprint({title: __("My Profile"), message: `<p>${esc(employee.employee_name)}</p><p>${esc(employee.designation || "")} · ${esc(employee.department || "")}</p><p>${esc(employee.company || "")}</p><p>${esc(__("Use Update My Data to request a correction from HR."))}</p>`});
}

// Dialogs sit outside the portal, so they use Frappe's own indicator colours.
const emdStatusPill = (status, extra) => {
	const colour = /^(pending|open)/i.test(status || "") ? "orange" : /approved|completed|issued/i.test(status || "") ? "green"
		: /rejected|cancel|declined/i.test(status || "") ? "red" : /draft/i.test(status || "") ? "gray" : "blue";
	return `<span class="indicator-pill ${colour} ${extra || ""}">${esc(__(status))}</span>`;
};

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
			emdRenderLeaveSummary(data.leave_summary, data.leave_flow);
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

// What the employee should do next with their leave, one line per item, with the button for that step.
const LEAVE_STEP = {
	return_due: { icon: "fa-rotate-left", tone: "amber", text: __("Your leave ended on {0}. Tell HR you are back."), button: __("Send Leave Return") },
	on_leave: { icon: "fa-umbrella-beach", tone: "teal", text: __("On leave until {0}.") },
	plan_approved: { icon: "fa-calendar-check", tone: "sky", text: __("Plan approved for {1}. Apply when the time comes."), button: __("Apply now") },
	waiting: { icon: "fa-hourglass-half", tone: "amber", text: __("Waiting for your manager's approval ({1}).") },
	plan_waiting: { icon: "fa-hourglass-half", tone: "", text: __("Leave plan waiting for approval ({1}).") },
	upcoming: { icon: "fa-calendar-day", tone: "teal", text: __("Approved: starts on {2} ({1}).") },
};

function emdLeaveSteps(steps) {
	if (!steps.length) return `<p class="mhp-muted">${__("Nothing to do: no leave in progress or waiting. Use Leave Plan or Leave Application below to plan or apply.")}</p>`;
	const day = (d) => frappe.datetime.str_to_user(d);
	return `<div class="mhp-rows">${steps.map((s, i) => {
		const k = LEAVE_STEP[s.step];
		const period = `${esc(__(s.leave_type))}, ${day(s.from_date)} – ${day(s.to_date)}${s.days ? `, ${esc(s.days)} ${__("days")}` : ""}`;
		const text = esc(k.text).replace("{0}", day(s.to_date)).replace("{1}", period).replace("{2}", day(s.from_date));
		return `<div class="mhp-row"><div style="display:flex;gap:12px;align-items:flex-start"><span class="mhp-tile-icon ${k.tone}" style="width:34px;height:34px;font-size:14px"><i class="fa-solid ${k.icon}" aria-hidden="true"></i></span>
			<div><b>${text}</b><small>${esc(s.name)}</small></div></div>
			${k.button ? `<button type="button" class="mhp-btn primary sm emd-leave-step" data-i="${i}">${esc(k.button)}</button>` : ""}</div>`;
	}).join("")}</div>`;
}

function emdRenderLeaveSummary(summary, steps) {
	if (!summary) return;
	steps = steps || [];
	const rows = Object.entries(summary.balances || {}).map(([type, balance]) => `<tr><td>${esc(__(type))}</td><td class="num">${esc(balance.total_leaves)}</td><td class="num">${esc(balance.leaves_taken)}</td><td class="num">${esc(balance.leaves_pending_approval)}</td><td class="num"><b>${esc(balance.remaining_leaves)}</b></td></tr>`).join("");
	const limit = (label, usage) => {
		if (usage.limit === null) return "";
		const text = usage.used === null ? __("HR has not set up the holiday calendar yet") : __("{0} of {1} used this month", [usage.used, usage.limit]);
		return `<div class="mhp-row"><div><b>${esc(label)}</b><small>${esc(text)}</small></div><span class="mhp-pill ${usage.used !== null && usage.used >= usage.limit ? "amber" : "teal"}">${esc(usage.used === null ? "—" : __("{0} left", [Math.max(0, usage.limit - usage.used)]))}</span></div>`;
	};
	const limits = limit(__("Half-day leave"), summary.half_day) + limit(__("Work from home (days)"), summary.remote_work);
	$("#emd-leave-summary").html(`
		<h3><i class="fa-solid fa-umbrella-beach" aria-hidden="true"></i>${__("My Leave")}</h3>
		<h4 class="mhp-card-title" style="font-size:15px;margin:4px 0 8px">${__("What's next")}</h4>
		${emdLeaveSteps(steps)}
		<h4 class="mhp-card-title" style="font-size:15px;margin:22px 0 8px">${__("Balances")}</h4>
		${rows ? `<div class="mhp-tablewrap"><table class="mhp-table"><thead><tr><th>${__("Leave Type")}</th><th class="num">${__("Allocated")}</th><th class="num">${__("Taken")}</th><th class="num">${__("Waiting for approval")}</th><th class="num">${__("Left")}</th></tr></thead><tbody>${rows}</tbody></table></div>` : `<p>${__("No leave assigned to you yet. HR assigns annual leave at the start of the leave year.")}</p>`}
		${limits ? `<h4 class="mhp-card-title" style="font-size:15px;margin:22px 0 8px">${__("This month's limits")} — ${esc(summary.month)}</h4><div class="mhp-rows">${limits}</div>` : ""}`);
	$("#emd-leave-summary .emd-leave-step").on("click", function () {
		const s = steps[Number($(this).attr("data-i"))];
		if (s.step === "return_due") emdNewRequest("Leave Return Request", { leave_application: s.name });
		if (s.step === "plan_approved") emdNewRequest("Leave Application", { leave_type: s.leave_type, from_date: s.from_date, to_date: s.to_date }, s.name);
	});
}
})();
