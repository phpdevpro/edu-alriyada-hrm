(() => {
const METHOD = "medical_hrms.medical_hrms.page.hr_dashboard.hr_dashboard.";
const esc = (value) => frappe.utils.escape_html(String(value ?? ""));
const slug = (doctype) => frappe.router.slug(doctype);

frappe.pages["hr-dashboard"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    single_column: true,
  });

  $(wrapper).find(".page-head .title-area").remove();
  $(wrapper).find(".page-head-content").remove();

  const allowed = frappe.user.has_role("HR User") || frappe.user.has_role("HR Manager") || frappe.user.has_role("System Manager");
  if (!allowed) {
    $(page.body).html('<div style="padding:24px;font-size:16px;">You are not authorized to view this dashboard.</div>');
    return;
  }

  MhPortal.mount(page, { portal: "hr", active: "dashboard", crumb: __("Dashboard") });
  render_layout(page);
  load_data();
};

// [title, doctype, icon, tone, description]
const REQUESTS = [
  [__("Permission Request"), "Permission Request", "fa-clock", "", __("Short permissions and time away.")],
  [__("Remote Work Request"), "Remote Work Request", "fa-laptop-house", "sky", __("Work-from-home days.")],
  [__("Leave Plan Request"), "Leave Plan Request", "fa-calendar-week", "", __("Planned leave for the year.")],
  [__("Leave Return Request"), "Leave Return Request", "fa-rotate-left", "violet", __("Return from leave and medical clearance.")],
  [__("Salary Certificate Request"), "Salary Certificate Request", "fa-file-invoice", "", __("Official salary certificates.")],
  [__("Pre Approved Overtime Request"), "Pre Approved Overtime Request", "fa-business-time", "amber", __("Overtime approved in advance.")],
  [__("Employee Training Request"), "Employee Training Request", "fa-chalkboard", "sky", __("Courses and professional training.")],
  [__("Children Medical Allowance Request"), "Children Medical Allowance Request", "fa-hand-holding-medical", "rose", __("Medical allowance claims for children.")],
  [__("Company Car Request"), "Company Car Request", "fa-car", "", __("Company vehicles.")],
  [__("Contract Renewal Request"), "Contract Renewal Request", "fa-file-signature", "violet", __("Contract renewals.")],
  [__("Employee Data Update Request"), "Employee Data Update Request", "fa-user-pen", "amber", __("Corrections to personal records.")],
];

const CORE = [
  [__("Leave Application"), "Leave Application", "fa-calendar-check", "", __("Leave requests and approvals.")],
  [__("Attendance Request"), "Attendance Request", "fa-user-check", "sky", __("Attendance corrections.")],
  [__("Expense Claim"), "Expense Claim", "fa-receipt", "amber", __("Expense claims and advances.")],
  [__("Travel Request"), "Travel Request", "fa-plane", "violet", __("Business travel and its costs.")],
  [__("Employee Separation"), "Employee Separation", "fa-door-open", "rose", __("Resignations and exit steps.")],
  [__("Full and Final Statement"), "Full and Final Statement", "fa-file-contract", "", __("Final settlement on leaving.")],
];

const RECORDS = [
  [__("Employees"), "Employee", "fa-users", "", __("Employee master and Ministry fields.")],
  [__("Medical Licenses"), "Employee Medical License", "fa-id-card-clip", "sky", __("Licences and their expiry dates.")],
  [__("Job Application Link"), "Job Application Link", "fa-link", "violet", __("Links applicants use to apply.")],
  [__("Job Applicants"), "Employee Job Applicant", "fa-id-badge", "amber", __("Review applicants and create employees.")],
];

const LEAVE = [
  [__("Leave Policy"), "leave-policy", "fa-book", __("The starter policies allocate annual leave only. Medical leave has a separate sick-year basis.")],
  [__("Leave Policy Assignment"), "leave-policy-assignment", "fa-user-tag", __("Assign a shared policy to employees and track its effective dates.")],
  [__("Leave Control Panel"), "leave-control-panel", "fa-sliders", __("Assign leave policies to multiple employees together.")],
  [__("Leave Allocation"), "leave-allocation", "fa-scale-balanced", __("Review each employee’s allocated days and carry-forward balances.")],
  [__("Leave Type"), "leave-type", "fa-tags", __("Manage the leave categories used in your policies.")],
  [__("Leave Period"), "leave-period", "fa-calendar", __("Define the dates of your organization’s leave year.")],
  [__("Monthly Limits"), "hr-settings", "fa-gauge", __("Open HR Settings → Employee Monthly Limits to configure half-day and work-from-home limits.")],
];

const PRESENCE = [
  [__("Faculty Schedules"), "hr-academic-presence/faculty", "fa-person-chalkboard", "", __("Every teaching session by faculty member, room and mode.")],
  [__("Proctor Schedules"), "hr-academic-presence/proctors", "fa-user-shield", "violet", __("Exam supervision assignments by date, time and room.")],
  [__("Students on Campus"), "hr-academic-presence/students", "fa-user-graduate", "sky", __("Expected and present students in each hour of the day.")],
  [__("Faculty After 4 PM"), "hr-academic-presence/after_hours", "fa-moon", "amber", __("Faculty on campus after 4:00 PM each day, teaching or proctoring.")],
];

const JAMEAH = [
  [__("Jameah Data Check"), "jameah-data-check", "fa-clipboard-check", "", __("Gaps, invalid codes and source problems, view by view.")],
  [__("Code Map"), "jameah-code-map", "fa-right-left", "violet", __("College values matched to official Ministry codes.")],
  [__("Jameah Settings"), "jameah-settings", "fa-gear", "amber", __("Institution codes used by the Ministry views.")],
];

function tile(title, route, icon, tone, description, doctype) {
  const counts = doctype ? `<span class="mhp-pill hrd-pending" title="${esc(__("Waiting for a decision"))}"><span data-pending-for="${esc(doctype)}">0</span> ${esc(__("pending"))}</span>
    <span class="mhp-pill"><span class="hrd-count" data-count-for="${esc(doctype)}">0</span> ${esc(__("total"))}</span>` : "";
  return `<article class="mhp-tile">
    <div class="mhp-tile-top"><span class="mhp-tile-icon ${esc(tone)}"><i class="fa-solid ${esc(icon)}" aria-hidden="true"></i></span>
      <div><h4>${esc(title)}</h4><p>${esc(description)}</p></div></div>
    <div class="mhp-tile-foot"><div class="mhp-stack" style="flex-direction:row;gap:6px;flex-wrap:wrap">${counts}</div>
      <a class="mhp-link" href="/app/${esc(route)}">${esc(__("Open", null, "Open a page"))} <i class="fa-solid fa-arrow-right" aria-hidden="true"></i></a></div>
  </article>`;
}

// withCounts: only the request types have pending / total figures (get_hr_doctype_counts).
const doctypeTiles = (items, withCounts) => items.filter(([, doctype]) => frappe.model.can_read(doctype))
  .map(([title, doctype, icon, tone, description]) => tile(title, slug(doctype), icon, tone, description, withCounts ? doctype : null)).join("");

function render_layout(page) {
  const name = frappe.session.user_fullname || frappe.session.user;
  const role = frappe.user.has_role("HR Manager") ? __("HR Manager") : __("HR User");
  const company = frappe.defaults.get_user_default("Company") || frappe.defaults.get_global_default("company") || "";
  const image = (frappe.user_info(frappe.session.user) || {}).image;
  const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map((s) => s[0].toUpperCase()).join("");

  const $wrap = $('<div class="hrd-wrap"></div>');
  $wrap.append(MhPortal.head({
    image, initials, eyebrow: __("HR Portal"), title: name, titleId: "hrd-title",
    meta: [{ icon: "fa-user-tie", text: role, id: "hrd-user-role" }, { icon: "fa-envelope", text: frappe.session.user, id: "hrd-user-email" },
      ...(company ? [{ icon: "fa-building", text: company }] : [])],
  }));
  $wrap.append('<div id="hrd-banner"></div>');
  $wrap.append(`
    <section class="mhp-section">
      ${MhPortal.sectionHead("fa-chart-line", __("Today at a Glance"), __("Headcount, requests waiting for a decision and licences on file."))}
      <div class="mhp-stats">
        ${MhPortal.stat({ id: "stat-employees", icon: "fa-users", label: __("Total Employees"), note: __("Employee records") })}
        ${MhPortal.stat({ id: "stat-training", icon: "fa-chalkboard", tone: "amber", label: __("Pending Training"), note: __("Training requests waiting") })}
        ${MhPortal.stat({ id: "stat-allowance", icon: "fa-hand-holding-medical", tone: "violet", label: __("Pending Allowance"), note: __("Medical allowance claims waiting") })}
        ${MhPortal.stat({ id: "stat-license", icon: "fa-id-card-clip", tone: "sky", label: __("Active Licenses"), note: __("Medical licences in force") })}
      </div>
    </section>

    <section class="mhp-section">
      ${MhPortal.sectionHead("fa-inbox", __("Employee Requests"), __("Requests employees send from their portal. The amber figure is how many wait for a decision."))}
      <div class="mhp-grid" id="hrd-requests-grid">${doctypeTiles(REQUESTS, true)}</div>
    </section>

    <section class="mhp-section">
      ${MhPortal.sectionHead("fa-umbrella-beach", __("Leave Management"), __("Define a shared policy, assign it to employees, and track individual balances."))}
      <div class="mhp-grid wide" style="margin-bottom:18px">
        <article class="mhp-card"><h3><i class="fa-solid fa-sun" aria-hidden="true"></i>${esc(__("Annual Leave"))}</h3><p>${esc(__("The 21-day and 30-day draft policies cover annual leave only. Assign the appropriate policy after checking service length and contract terms."))}</p><a class="mhp-btn soft" href="/app/leave-policy">${esc(__("Review Annual Policies"))}</a></article>
        <article class="mhp-card"><h3><i class="fa-solid fa-notes-medical" aria-hidden="true"></i>${esc(__("Medical / Sick Leave"))}</h3><p>${esc(__("Separate from annual leave. Review and submit the Medical Leave policy, then activate each employee’s sick year from the first illness date. Requests must stay within the configured pay stages."))}</p>
          <div class="mhp-head-actions"><a class="mhp-btn soft" href="/app/leave-policy">${esc(__("Review Medical Policy"))}</a><button class="mhp-btn primary" id="hrd-activate-medical" type="button">${esc(__("Activate Medical Leave Year"))}</button></div></article>
        <article class="mhp-card"><h3><i class="fa-solid fa-mug-hot" aria-hidden="true"></i>${esc(__("Casual Leave"))}</h3><p>${esc(__("No default casual-leave allowance has been assigned. This is a separate company-policy decision, not part of the 21 annual days. Monthly short-permission rules are also separate."))}</p><a class="mhp-btn soft" href="/app/hr-settings">${esc(__("Review Company Settings"))}</a></article>
      </div>
      <div class="mhp-grid" id="hrd-leave-management">${LEAVE.map(([title, route, icon, description]) => tile(title, route, icon, "", description)).join("")}</div>
    </section>

    <section class="mhp-section">
      ${MhPortal.sectionHead("fa-briefcase", __("HR Transactions"), __("Leave, attendance, expenses, travel and leaving."))}
      <div class="mhp-grid" id="hrd-core-grid">${doctypeTiles(CORE)}</div>
    </section>

    <section class="mhp-section">
      ${MhPortal.sectionHead("fa-folder-open", __("Records & Hiring"), __("Employee records, medical licences and recruitment."))}
      <div class="mhp-grid" id="hrd-compliance-grid">${doctypeTiles(RECORDS)}</div>
    </section>

    <section class="mhp-section" aria-labelledby="hrd-academic-heading">
      ${MhPortal.sectionHead("fa-chalkboard-user", __("Academic Schedules & Presence"), __("Faculty and proctor timetables, and who is on campus, from the class timetables and recorded attendance."))}
      <div class="mhp-grid">${PRESENCE.map(([title, route, icon, tone, description]) => tile(title, route, icon, tone, description)).join("")}</div>
    </section>

    <section class="mhp-section" aria-labelledby="hrd-jameah-heading">
      ${MhPortal.sectionHead("fa-building-columns", __("Ministry (Jameah) Data"), __("What the Ministry views send for employees and students, and what still needs a code or a correction."))}
      <div class="mhp-grid">${JAMEAH.map(([title, route, icon, tone, description]) => tile(title, route, icon, tone, description)).join("")}</div>
    </section>`);
  $(page.body).html($wrap);

  $("#hrd-activate-medical").toggle(frappe.session.user === "Administrator" || frappe.user.has_role("HR Manager") || frappe.user.has_role("System Manager")).on("click", () => {
    let saving = false;
    const dialog = new frappe.ui.Dialog({
      title: __("Activate Medical Leave Year"),
      fields: [
        {fieldtype: "HTML", options: `<p>${__("Confirm the first illness date. This creates separate medical allocations for one year, without changing annual leave. Review the medical policy, leave types and payroll settings first.")}</p>`},
        {fieldname: "employee", label: __("Employee"), fieldtype: "Link", options: "Employee", reqd: 1, get_query: () => ({filters: {status: "Active"}})},
        {fieldname: "first_sick_date", label: __("First Sick-leave Date"), fieldtype: "Date", reqd: 1},
      ],
      primary_action_label: __("Activate Medical Year"),
      primary_action(values) {
        if (saving) return;
        saving = true;
        frappe.call({method: "medical_hrms.medical_leave.activate_year", args: values, freeze: true,
          callback(r) {
            dialog.hide();
            frappe.msgprint(__("Medical leave year activated: {0} to {1}.", [r.message.from_date, r.message.to_date]));
          }, always: () => { saving = false; },
        });
      },
    });
    dialog.show();
  });
}

function render_banner(pending) {
  const waiting = REQUESTS.map(([title, doctype]) => [title, doctype, pending[doctype] || 0]).filter(([, , n]) => n > 0);
  const total = waiting.reduce((n, [, , count]) => n + count, 0);
  const body = waiting.length ? `<div class="mhp-rows">${waiting.map(([title, doctype, count]) => `
    <div class="mhp-row"><div><b>${esc(title)}</b><small>${esc(__("{0} waiting for a decision", [count]))}</small></div>
      <a class="mhp-link" href="/app/${slug(doctype)}?status=${encodeURIComponent("[\"like\",\"Pending%\"]")}">${esc(__("Review"))} <i class="fa-solid fa-arrow-right" aria-hidden="true"></i></a></div>`).join("")}</div>` : "";
  $("#hrd-banner").html(MhPortal.banner(total ? {
    icon: "fa-inbox", tone: "warn",
    title: total === 1 ? __("1 request is waiting for review") : __("{0} requests are waiting for review", [total]),
    text: __("Open the list below to see each type"), body,
  } : {
    icon: "fa-circle-check", title: __("No requests waiting for review"), text: __("Everything employees sent has a decision."),
  }));
}

function load_data() {
  frappe.call({
    method: METHOD + "get_hr_dashboard_stats",
    callback: function (r) {
      const s = r?.message?.stats || {};
      $("#stat-employees").text(s.total_employees ?? 0);
      $("#stat-training").text(s.pending_training_requests ?? 0);
      $("#stat-allowance").text(s.pending_allowance_requests ?? 0);
      $("#stat-license").text(s.expiring_medical_licenses ?? 0);
    },
  });

  frappe.call({
    method: METHOD + "get_hr_doctype_counts",
    callback: function (r) {
      const counts = r?.message?.counts || {};
      const pending = r?.message?.pending || {};
      Object.keys(counts).forEach((dt) => {
        $(`[data-count-for="${dt}"]`).text(counts[dt] ?? 0);
        $(`[data-pending-for="${dt}"]`).text(pending[dt] ?? 0).closest(".hrd-pending").toggleClass("amber", (pending[dt] || 0) > 0);
      });
      render_banner(pending);
    },
  });
}
})();
