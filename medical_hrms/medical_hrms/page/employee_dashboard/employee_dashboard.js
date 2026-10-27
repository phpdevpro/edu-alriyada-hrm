(() => {
// The request dialogs, the leave steps and the status pills are shared with the My HR card on the staff dashboards:
// public/js/self_service.js (MhSelfService).
const SS = MhSelfService;
const esc = SS.esc;
let stale = false; // a request changed while this page was not showing: reload when it shows again

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
	MhPortal.on("new-request", (doctype) => SS.newRequest(doctype));
	MhPortal.on("profile", () => emdShowProfile());
	SS.onChange("employee-dashboard", () => {
		if (frappe.get_route_str() === "employee-dashboard") load_dashboard();
		else stale = true;
	});
	render_layout(page);
	load_dashboard(true);
};

frappe.pages["employee-dashboard"].on_page_show = function () {
	if (stale) {
		stale = false;
		load_dashboard();
	}
	const options = frappe.route_options || {};
	if (options.request && options.name) {
		frappe.route_options = null;
		SS.showDetails(options.request, options.name);
	}
};

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
	const html = SS.services().map(([title, doctype, description, icon, tone]) => `
		<article class="mhp-tile emd-service">
			<div class="mhp-tile-top"><span class="mhp-tile-icon ${esc(tone)}"><i class="fa-solid ${esc(icon)}" aria-hidden="true"></i></span><div><h4>${esc(title)}</h4><p>${esc(description)}</p></div></div>
			<div class="mhp-tile-foot"><button type="button" class="mhp-textbtn emd-count" data-doctype="${esc(doctype)}">${esc(__("{0} request(s)", [counts[doctype] || 0]))}</button><button type="button" class="mhp-btn primary sm emd-new" data-doctype="${esc(doctype)}"><i class="fa-solid fa-plus" aria-hidden="true"></i>${esc(__("New Request"))}</button></div>
		</article>`).join("");
	$("#emd-services").html(html);
	$("#emd-my-leave").off("click").on("click", event => {
		event.preventDefault();
		SS.myRequests("Leave Application");
	});
	$(".emd-count").on("click", function () { SS.myRequests($(this).data("doctype")); });
	$(".emd-new").on("click", function () { SS.newRequest($(this).data("doctype")); });
}

function emdShowProfile() {
	const employee = SS.getEmployee();
	if (!employee) {
		frappe.msgprint(__("Your user account is not linked to an Employee record. Please contact HR."));
		return;
	}
	frappe.msgprint({title: __("My Profile"), message: `<p>${esc(employee.employee_name)}</p><p>${esc(employee.designation || "")} · ${esc(employee.department || "")}</p><p>${esc(employee.company || "")}</p><p>${esc(__("Use Update My Data to request a correction from HR."))}</p>`});
}

function render_recent(rows) {
	if (!rows.length) {
		$("#emd-recent").html(`<div class="mhp-empty"><i class="fa-regular fa-folder-open"></i>${esc(__("No requests yet. Choose a service above to get started."))}</div>`);
		return;
	}
	$("#emd-recent").html(rows.map((row) => `
		<div class="mhp-row emd-recent-row">
			<div><b>${esc(__(row.doctype))}</b><small>${esc(row.name)} · ${frappe.datetime.comment_when(row.modified)}</small>${SS.isService(row.doctype) ? `<div><button type="button" class="mhp-textbtn emd-recent-details" data-doctype="${esc(row.doctype)}" data-name="${esc(row.name)}">${esc(__("View details"))}</button></div>` : ""}</div>
			<span class="mhp-pill ${SS.statusTone(row.status)} emd-status">${esc(__(row.status))}</span>
		</div>`).join(""));
	$("#emd-recent .emd-recent-details").on("click", function () {
		SS.showDetails($(this).attr("data-doctype"), $(this).attr("data-name"));
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
				SS.setEmployee(null);
				$("#emd-alert").html(`<div class="mhp-alert emd-message">${esc(data.message || __("Employee profile not found."))}</div>`);
				$("#emd-leave-summary").html(`<div class="mhp-empty"><i class="fa-solid fa-user-slash"></i>${esc(__("No employee record is linked to your login."))}</div>`);
				render_services({});
				render_recent([]);
				$(".emd-new").prop("disabled", true);
				return;
			}

			const employee = data.employee;
			SS.setEmployee(employee);
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
function emdLeaveSteps(steps) {
	if (!steps.length) return `<p class="mhp-muted">${__("Nothing to do: no leave in progress or waiting. Use Leave Plan or Leave Application below to plan or apply.")}</p>`;
	return `<div class="mhp-rows">${steps.map((s, i) => {
		const k = SS.leaveStep(s);
		if (!k) return "";
		return `<div class="mhp-row"><div style="display:flex;gap:12px;align-items:flex-start"><span class="mhp-tile-icon ${k.tone}" style="width:34px;height:34px;font-size:14px"><i class="fa-solid ${k.icon}" aria-hidden="true"></i></span>
			<div><b>${k.text}</b><small>${esc(s.name)}</small></div></div>
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
		SS.runLeaveStep(steps[Number($(this).attr("data-i"))]);
	});
}
})();
