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

// Leave requests: counted in the "waiting for review" banner, shown in the Leave section.
const LEAVE_REQUESTS = [
  [__("Leave Plan Request"), "Leave Plan Request"],
  [__("Leave Return Request"), "Leave Return Request"],
];

// Yearly leave setup, in the order it is done: [step title, route, icon, what it is for]
const LEAVE_SETUP = [
  [__("Leave Period"), "leave-period", "fa-calendar", __("Open this year's leave period for each company and tick 'Is Active'.")],
  [__("Holiday List"), "holiday-list", "fa-calendar-day", __("Official holidays and weekends for the year; set it as the company default.")],
  [__("Leave Policy"), "leave-policy", "fa-book", __("Annual leave 21 or 30 days; the Sick Leave policy with its 3 pay stages.")],
  [__("Leave Control Panel"), "leave-control-panel", "fa-sliders", __("Assign the annual leave policy to employees together; this gives them their balance.")],
  [__("Leave Approvers"), "department", "fa-user-check", __("Set who approves leave: on each Department, or on the Employee record.")],
  [__("Monthly Limits"), "hr-settings", "fa-gauge", __("HR Settings > Employee Monthly Limits: half-day leave and work-from-home days per month.")],
];

const LEAVE_MORE = [
  [__("Leave Allocation"), "leave-allocation"], [__("Leave Policy Assignment"), "leave-policy-assignment"], [__("Leave Type"), "leave-type"],
];

const PRESENCE = [
  [__("Faculty Schedules"), "hr-academic-presence/faculty", "fa-person-chalkboard", "", __("Every teaching session by faculty member, room and mode.")],
  [__("Proctor Schedules"), "hr-academic-presence/proctors", "fa-user-shield", "violet", __("Exam supervision assignments by date, time and room.")],
  [__("Students on Campus"), "hr-academic-presence/students", "fa-user-graduate", "sky", __("Expected and present students in each hour of the day.")],
  [__("Faculty After 4 PM"), "hr-academic-presence/after_hours", "fa-moon", "amber", __("Faculty on campus after 4:00 PM each day, teaching or proctoring.")],
];

const JAMEAH = [
  [__("Jameah Data Check"), "jameah-data-check", "fa-clipboard-check", "", __("Gaps, invalid codes and source problems, view by view.")],
  [__("Employees Missing Ministry Data"), "query-report/Employees Missing Ministry Data", "fa-user-xmark", "rose", __("Each employee with Ministry-mandatory data still empty, named as the Employee form field.")],
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
      <a class="mhp-link" href="/app/${esc(encodeURI(route))}">${esc(__("Open", null, "Open a page"))} <i class="fa-solid fa-arrow-right" aria-hidden="true"></i></a></div>
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

    <section class="mhp-section" id="hrd-leave">
      ${MhPortal.sectionHead("fa-umbrella-beach", __("Leave"), __("From the yearly setup to the employee's return, in order: the employee plans, applies, the manager approves, the employee comes back."))}
      <div class="mhp-two" style="margin-bottom:22px">
        <article class="mhp-card" id="hrd-leave-ready"><h3><i class="fa-solid fa-list-check" aria-hidden="true"></i>${esc(__("Leave setup check"))}</h3><p class="mhp-muted">${esc(__("Checking..."))}</p></article>
        <article class="mhp-card"><h3><i class="fa-solid fa-notes-medical" aria-hidden="true"></i>${esc(__("Sick Leave"))}</h3>
          <p>${esc(__("Separate from annual leave. On an employee's first sick day, start their sick leave year: requests then use Sick Leave 1 (30 days, full pay), 2 (60 days, 75% pay) and 3 (30 days, unpaid) in that order."))}</p>
          <p class="mhp-muted" id="hrd-sick-policy"></p>
          <div class="mhp-head-actions"><button class="mhp-btn primary" id="hrd-activate-medical" type="button">${esc(__("Start Sick Leave Year"))}</button><a class="mhp-btn soft" href="/app/leave-policy">${esc(__("Leave Policies"))}</a></div></article>
      </div>
      <h3 class="mhp-card-title" style="font-size:17px">${esc(__("Daily leave work"))}</h3>
      <div class="mhp-grid" id="hrd-leave-work" style="margin-bottom:22px">
        ${leave_work_tile("applications_waiting", __("Leave applications waiting"), __("Waiting for the leave approver."), "leave-application?status=Open", "fa-calendar-check", "amber")}
        ${leave_work_tile("plans_waiting", __("Leave plans waiting"), __("Waiting for the manager or department head."), "leave-plan-request?status=" + encodeURIComponent('["like","Pending%"]'), "fa-calendar-week", "sky")}
        ${leave_work_tile("returns_waiting", __("Leave returns to complete"), __("Employees back from leave; after sick leave, occupational health clears them."), "leave-return-request?status=" + encodeURIComponent('["like","Pending%"]'), "fa-rotate-left", "violet")}
        ${leave_work_tile("on_leave_today", __("On leave today"), __("Approved leave that covers today."), "leave-application?status=Approved&docstatus=1", "fa-umbrella-beach", "")}
      </div>
      <h3 class="mhp-card-title" style="font-size:17px">${esc(__("Yearly setup, in this order"))}</h3>
      <div class="mhp-grid" id="hrd-leave-management">${LEAVE_SETUP.map(([title, route, icon, description], i) => tile(`${i + 1}. ${title}`, route, icon, "", description)).join("")}</div>
      <p class="mhp-muted" style="margin-top:12px">${esc(__("Also:"))} ${LEAVE_MORE.map(([title, route]) => `<a class="mhp-link" href="/app/${route}">${esc(title)}</a>`).join(" · ")}</p>
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
      title: __("Start Sick Leave Year"),
      fields: [
        {fieldtype: "HTML", options: `<p>${__("Enter the employee's first sick day. This opens their sick leave year (one year from that day) with Sick Leave 1 and 2; annual leave is not touched. Check the Sick Leave policy and payroll settings first.")}</p>`},
        {fieldname: "employee", label: __("Employee"), fieldtype: "Link", options: "Employee", reqd: 1, get_query: () => ({filters: {status: "Active"}})},
        {fieldname: "first_sick_date", label: __("First Sick Day"), fieldtype: "Date", reqd: 1},
      ],
      primary_action_label: __("Start Sick Leave Year"),
      primary_action(values) {
        if (saving) return;
        saving = true;
        frappe.call({method: "medical_hrms.medical_leave.activate_year", args: values, freeze: true,
          callback(r) {
            dialog.hide();
            frappe.msgprint(__("Sick leave year started: {0} to {1}.", [r.message.from_date, r.message.to_date]));
            load_leave_overview();
          }, always: () => { saving = false; },
        });
      },
    });
    dialog.show();
  });
}

function leave_work_tile(key, title, description, route, icon, tone) {
  return `<article class="mhp-tile">
    <div class="mhp-tile-top"><span class="mhp-tile-icon ${esc(tone)}"><i class="fa-solid ${esc(icon)}" aria-hidden="true"></i></span>
      <div><h4>${esc(title)}</h4><p>${esc(description)}</p></div></div>
    <div class="mhp-tile-foot"><span class="mhp-pill" data-leave-count="${esc(key)}">…</span>
      <a class="mhp-link" href="/app/${route}">${esc(__("Open", null, "Open a page"))} <i class="fa-solid fa-arrow-right" aria-hidden="true"></i></a></div>
  </article>`;
}

// One line per check: ok, or what is missing and where to fix it.
function render_leave_overview(d) {
  Object.entries(d.counts || {}).forEach(([key, n]) => $(`[data-leave-count="${key}"]`).text(n).toggleClass("amber", n > 0 && key !== "on_leave_today"));
  const check = (ok, text, fix) => `<div class="mhp-row"><div style="display:flex;gap:10px;align-items:flex-start">
    <i class="fa-solid ${ok ? "fa-circle-check" : "fa-circle-exclamation"}" style="color:var(${ok ? "--success" : "--warning"});margin-top:3px" aria-hidden="true"></i><span>${esc(text)}</span></div>
    ${ok || !fix ? "" : `<a class="mhp-link" href="/app/${fix}">${esc(__("Fix"))} <i class="fa-solid fa-arrow-right" aria-hidden="true"></i></a>`}</div>`;
  const rows = (d.companies || []).map((c) => `<p style="margin:10px 0 2px"><b>${esc(c.company)}</b> <span class="mhp-muted">· ${esc(__("{0} active employees", [c.employees]))}</span></p><div class="mhp-rows">
    ${check(!!c.period, c.period ? __("Leave period active: {0} to {1}", [frappe.datetime.str_to_user(c.period.from_date), frappe.datetime.str_to_user(c.period.to_date)]) : __("No active leave period for today"), "leave-period")}
    ${check(!c.without_holiday_list, c.without_holiday_list ? __("{0} employees have no holiday list covering today", [c.without_holiday_list]) : __("Holiday list set for everyone"), "holiday-list")}
    ${check(!c.without_approver, c.without_approver ? __("{0} employees have no leave approver", [c.without_approver]) : __("Every employee has a leave approver"), "department")}
    ${check(!c.without_annual_leave, c.without_annual_leave ? __("{0} employees have no annual leave this year", [c.without_annual_leave]) : __("Every employee has annual leave this year"), "leave-control-panel")}
  </div>`).join("");
  const sick = d.sick_policy;
  $("#hrd-sick-policy").text(sick ? (sick.docstatus === 1 ? __("Policy: {0} (submitted)", [sick.title]) : __("Policy {0} is a draft: submit it before starting a sick leave year.", [sick.title])) : __("No Sick Leave policy found."));
  $("#hrd-leave-ready").html(`<h3><i class="fa-solid fa-list-check" aria-hidden="true"></i>${esc(__("Leave setup check"))}</h3>${rows || `<p class="mhp-muted">${esc(__("No active employees."))}</p>`}`);
}

function render_banner(pending) {
  const waiting = [...REQUESTS, ...LEAVE_REQUESTS].map(([title, doctype]) => [title, doctype, pending[doctype] || 0]).filter(([, , n]) => n > 0);
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

function load_leave_overview() {
  frappe.call({ method: METHOD + "get_leave_overview", callback: (r) => render_leave_overview(r.message || {}) });
}

function load_data() {
  load_leave_overview();
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
