// Employee self-service dialogs - new request, request details (reason, history, Edit Draft / Send Again), my requests,
// the leave "what's next" steps - shared by the Employee Portal (page/employee_dashboard) and the My HR card on the
// staff dashboards (staff_hr_card.js, Round 3 HR-11). Loaded on every Desk page (hooks.py app_include_js).
// Labels are built when used, not when this file loads: the translations are not there yet at that point.
window.MhSelfService = (() => {
	const esc = (value) => frappe.utils.escape_html(String(value ?? ""));
	let employee = null; // the signed-in user's Employee record ({name, employee_name, ...}) once a page has loaded it
	const listeners = {}; // key -> callback after a request was sent, saved, deleted

	// [title, doctype, description, icon, tone]; the leave services first, in the order they are used: plan, apply, come back.
	const services = () => [
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
	const isService = (doctype) => services().some((service) => service[1] === doctype);

	const leaveIntro = (doctype) => ({
		"Leave Plan Request": __("Plan when you want to take leave this year. Your manager and then your department head approve the plan. It does not use your balance: when the time comes, open the approved plan here and click Apply now."),
		"Leave Application": __("Only the leave you hold is listed, with the days you have left. Your manager approves the request and HR is informed. For sick leave, tell HR on your first sick day so they can start your sick leave year."),
		"Leave Return Request": __("Choose the leave you are coming back from and the day you returned to work. After sick leave, attach your fitness certificate."),
	})[doctype];

	function onChange(key, callback) {
		listeners[key] = callback;
	}

	function changed() {
		Object.values(listeners).forEach((callback) => callback());
	}

	function notLinked() {
		frappe.msgprint(__("Your user account is not linked to an Employee record. Please contact HR."));
	}

	// Leave types the employee holds, as Select options "Annual Leave (19 days left)".
	function leaveTypeField(field) {
		return frappe.call({ method: "medical_hrms.self_service.my_leave_types" }).then((r) => {
			const choices = r.message || [];
			return choices.length ? Object.assign({}, field, { fieldtype: "Select", options: [{ label: "", value: "" }, ...choices.map((c) => ({ label: c.label, value: c.leave_type }))] }) : null;
		});
	}

	// opts.name: change the employee's own draft; opts.resend_of: send a rejected request again as a new one.
	function newRequest(doctype, prefill, plan, opts) {
		opts = opts || {};
		if (!employee) {
			notLinked();
			return;
		}
		const employeeName = employee.name;
		frappe.call({method: "medical_hrms.self_service.form_schema", args: {doctype}, callback: async (r) => {
			let schema = r.message || [];
			const leaveTypeIndex = schema.findIndex((field) => field.fieldname === "leave_type");
			if (leaveTypeIndex > -1) {
				const select = await leaveTypeField(schema[leaveTypeIndex]);
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
					field.get_query = () => ({filters: {employee: employeeName, status: "Approved", docstatus: 1}});
					field.onchange = () => returnContext(dialog);
				}
			});
			const intro = opts.name ? __("You are changing your draft {0}. Save Draft keeps it for later; Send Request sends it for review.", [opts.name])
				: opts.resend_of ? __("A new request in place of {0}, which was rejected. Change what is needed and send it; HR sees the rejected one with it.", [opts.resend_of])
				: (leaveIntro(doctype) || __("This request is linked to your login automatically. Approval and clearance decisions are handled by HR."));
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
					values[field.fieldname] = hour ? timeTo24Hour(hour, minute, period) : "";
					delete values[`${prefix}_hour`];
					delete values[`${prefix}_minute`];
					delete values[`${prefix}_period`];
				}
				saving = true;
				frappe.call({
					method: "medical_hrms.self_service.save_request",
					args: {doctype, values: JSON.stringify(values), send: send ? 1 : 0, plan: plan || undefined, name: opts.name || undefined, resend_of: opts.resend_of || undefined},
					freeze: true,
					callback: () => { dialog.hide(); frappe.show_alert({message: send ? __("Request sent for review") : __("Draft saved"), indicator: "green"}); changed(); },
					always: () => { saving = false; },
				});
			};
			dialog.show();
			if (prefill) dialog.set_values(dialogValues(prefill, timeFields)).then(() => doctype === "Leave Return Request" && returnContext(dialog));
		}});
	}

	// Leave Return: show when the employee was due back, and ask for the fitness certificate only after sick leave.
	function returnContext(dialog) {
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
	function dialogValues(values, timeFields) {
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

	function timeTo24Hour(hour, minute, period) {
		const hour24 = (Number(hour) % 12) + (period === "PM" ? 12 : 0);
		return `${String(hour24).padStart(2, "0")}:${minute}:00`;
	}

	function showDetails(doctype, name) {
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
			const steps = (data.history || []).map((step) => `<li style="padding:4px 0">${statusPill(step.status)}
				<small class="text-muted" style="margin-inline-start:8px">${esc(step.by)} · ${esc(frappe.datetime.str_to_user(step.on))}</small></li>`).join("");
			const history = steps ? `<h5 style="margin:18px 0 6px">${esc(__("History"))}</h5><ol class="emd-history" style="list-style:none;padding:0;margin:0">${steps}</ol>` : "";
			const actions = [
				data.can_edit ? `<button type="button" class="btn btn-primary btn-sm emd-edit-draft">${esc(__("Edit Draft"))}</button>` : "",
				data.can_edit ? `<button type="button" class="btn btn-default btn-sm emd-delete-draft">${esc(__("Delete Draft"))}</button>` : "",
				data.can_resend ? `<button type="button" class="btn btn-primary btn-sm emd-resend">${esc(doctype === "Leave Application" ? __("Apply Again") : __("Send Again"))}</button>` : "",
			].filter(Boolean).join(" ");
			const dialog = new frappe.ui.Dialog({title: __(doctype), fields: [{fieldtype: "HTML", options: `<p><strong>${esc(data.name)}</strong> ${statusPill(data.status, "emd-detail-status")}</p>
				${reason}${links}${actions ? `<div class="emd-actions" style="display:flex;gap:8px;flex-wrap:wrap;margin:10px 0">${actions}</div>` : ""}${details}${history}`}],
				primary_action_label: __("Close"), primary_action: () => dialog.hide()});
			dialog.$wrapper.on("click", ".emd-open-request", function () { dialog.hide(); showDetails(doctype, $(this).attr("data-name")); });
			// The My Requests list may be open behind: close it too, it would show the old status.
			dialog.$wrapper.on("click", ".emd-edit-draft", () => { closeDialogs(); newRequest(doctype, data.values, null, {name: data.name}); });
			dialog.$wrapper.on("click", ".emd-resend", () => { closeDialogs(); newRequest(doctype, data.values, null, {resend_of: data.name}); });
			dialog.$wrapper.on("click", ".emd-delete-draft", () => frappe.confirm(__("Delete the draft {0}? This cannot be undone.", [data.name]), () =>
				frappe.call({method: "medical_hrms.self_service.delete_draft", args: {doctype, name: data.name}, freeze: true, callback: () => {
					closeDialogs();
					frappe.show_alert({message: __("Draft deleted"), indicator: "green"});
					changed();
				}})));
			dialog.show();
		}});
	}

	function myRequests(doctype) {
		frappe.call({method: "medical_hrms.self_service.my_requests", args: {doctype}, callback: (r) => {
			const rows = (r.message || []).map(row => `<p><button type="button" class="btn btn-link emd-view-request" data-name="${esc(row.name)}">${esc(row.name)}</button> ${statusPill(row.status)}</p>`).join("");
			const list = new frappe.ui.Dialog({title: __("My Requests"), fields: [{fieldtype: "HTML", fieldname: "requests", options: rows || __("No requests yet.")}]});
			list.$wrapper.on("click", ".emd-view-request", function () { showDetails(doctype, $(this).attr("data-name")); });
			list.show();
		}});
	}

	function closeDialogs() {
		[...(frappe.ui.open_dialogs || [])].forEach((d) => d.hide());
	}

	// Dialogs sit outside the portals, so they use Frappe's own indicator colours.
	function statusPill(status, extra) {
		const colour = /^(pending|open)/i.test(status || "") ? "orange" : /approved|completed|issued/i.test(status || "") ? "green"
			: /rejected|cancel|declined/i.test(status || "") ? "red" : /draft/i.test(status || "") ? "gray" : "blue";
		return `<span class="indicator-pill ${colour} ${extra || ""}">${esc(__(status))}</span>`;
	}

	// pending (and Open: a leave waiting for its approver) -> amber, approved / completed / issued -> teal,
	// rejected / cancelled -> rose (the portals' pill tones)
	const statusTone = (status) => /^(pending|open)/i.test(status || "") ? "amber" : (/approved|completed|issued/i.test(status || "") ? "teal" : (/rejected|cancel|declined/i.test(status || "") ? "rose" : ""));

	// One leave "what's next" item (self_service leave_flow) -> {icon, tone, text (HTML), button}; runLeaveStep does its button.
	function leaveStep(s) {
		const k = {
			return_due: { icon: "fa-rotate-left", tone: "amber", text: __("Your leave ended on {0}. Tell HR you are back."), button: __("Send Leave Return") },
			on_leave: { icon: "fa-umbrella-beach", tone: "teal", text: __("On leave until {0}.") },
			plan_approved: { icon: "fa-calendar-check", tone: "sky", text: __("Plan approved for {1}. Apply when the time comes."), button: __("Apply now") },
			waiting: { icon: "fa-hourglass-half", tone: "amber", text: __("Waiting for your manager's approval ({1}).") },
			plan_waiting: { icon: "fa-hourglass-half", tone: "", text: __("Leave plan waiting for approval ({1}).") },
			upcoming: { icon: "fa-calendar-day", tone: "teal", text: __("Approved: starts on {2} ({1}).") },
		}[s.step];
		if (!k) return null;
		const day = (d) => frappe.datetime.str_to_user(d);
		const period = `${esc(__(s.leave_type))}, ${day(s.from_date)} – ${day(s.to_date)}${s.days ? `, ${esc(s.days)} ${__("days")}` : ""}`;
		return Object.assign({}, k, { text: esc(k.text).replace("{0}", day(s.to_date)).replace("{1}", period).replace("{2}", day(s.from_date)) });
	}

	function runLeaveStep(s) {
		if (s.step === "return_due") newRequest("Leave Return Request", { leave_application: s.name });
		if (s.step === "plan_approved") newRequest("Leave Application", { leave_type: s.leave_type, from_date: s.from_date, to_date: s.to_date }, s.name);
	}

	return {
		esc, services, isService, onChange, changed,
		setEmployee: (value) => { employee = value || null; },
		getEmployee: () => employee,
		newRequest, showDetails, myRequests, closeDialogs, statusPill, statusTone, leaveStep, runLeaveStep,
	};
})();
