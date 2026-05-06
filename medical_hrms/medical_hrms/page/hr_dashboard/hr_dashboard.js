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

  render_layout(page);
  load_data();
};

function render_layout(page) {
  $(page.body).html(`
    <style>
      .hrd-wrap { max-width: 1320px; margin: 0 auto; padding: 16px 8px 36px; }
      .hrd-hero {
        background: linear-gradient(135deg, #0f766e 0%, #14b8a6 100%);
        color: #fff;
        border-radius: 20px;
        padding: 28px 34px;
        box-shadow: 0 14px 24px rgba(0,0,0,.12);
        margin-bottom: 24px;
      }
      .hrd-hero h1 { margin: 0 0 6px; font-size: 40px; font-weight: 700; color:#fff; }
      .hrd-hero p { margin: 0; opacity: .95; font-size: 17px; }
      .hrd-user { margin-top: 10px; display:flex; gap: 16px; font-size: 15px; }

      .hrd-stats { display:grid; grid-template-columns: repeat(4, minmax(200px, 1fr)); gap: 18px; margin-bottom: 26px; }
      .hrd-stat {
        background:#fff; border-radius:14px; padding:20px 22px; border-left: 5px solid #14b8a6;
        box-shadow: 0 8px 16px rgba(0,0,0,.08);
      }
      .hrd-stat .value { font-size:42px; font-weight:700; color:#0f172a; line-height:1; margin: 8px 0 8px; }
      .hrd-stat .label { color:#475569; font-size:14px; text-transform:uppercase; letter-spacing:.4px; }

      .hrd-section-title { margin: 10px 0 8px; font-size:34px; font-weight:700; color:#0f172a; }
      .hrd-section-sub { margin: 0 0 14px; color:#475569; font-size:18px; }

      .hrd-cards { display:grid; grid-template-columns: repeat(3, minmax(260px, 1fr)); gap: 18px; }
      .hrd-card {
        background:#fff; border-radius:16px; border-top:4px solid #34d399; padding:24px;
        box-shadow: 0 8px 16px rgba(0,0,0,.08); min-height: 220px;
        display:flex; flex-direction:column; justify-content:space-between;
      }
      .hrd-card h3 { margin: 0 0 8px; font-size:22px; color:#0f172a; }
      .hrd-card p { margin: 0 0 14px; color:#475569; font-size:16px; }
      .hrd-btn {
        display:inline-block; text-decoration:none; font-weight:600; font-size:14px;
        padding:8px 14px; border-radius:999px; background:#ecfeff; color:#0f766e; border:1px solid #99f6e4;
      }

      .hrd-module-grid { display:grid; grid-template-columns: repeat(4, minmax(220px, 1fr)); gap: 14px; }
      .hrd-module-card {
        background:#fff; border:1px solid #dbe5ef; border-radius:14px; padding:16px;
        box-shadow: 0 6px 12px rgba(0,0,0,.05); transition: .2s ease;
      }
      .hrd-module-card:hover { transform: translateY(-2px); box-shadow: 0 10px 16px rgba(0,0,0,.08); }
      .hrd-module-title { font-size:16px; font-weight:700; color:#0f172a; margin: 0 0 8px; }
      .hrd-module-meta { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
      .hrd-count { font-size:13px; color:#0f766e; background:#ecfeff; border:1px solid #99f6e4; padding:2px 10px; border-radius:999px; }
      .hrd-link { font-size:13px; font-weight:600; color:#0f766e; text-decoration:none; }
      .hrd-link:hover { text-decoration:underline; }

      .hrd-group { margin-top: 28px; }
      .hrd-group h3 { margin: 0 0 10px; font-size:22px; color:#0f172a; }

      @media (max-width: 1200px) {
        .hrd-stats { grid-template-columns: repeat(2, minmax(200px, 1fr)); }
        .hrd-cards { grid-template-columns: repeat(2, minmax(240px, 1fr)); }
        .hrd-module-grid { grid-template-columns: repeat(2, minmax(220px, 1fr)); }
      }
      @media (max-width: 760px) {
        .hrd-hero h1 { font-size: 32px; }
        .hrd-stats, .hrd-cards { grid-template-columns: 1fr; }
        .hrd-module-grid { grid-template-columns: 1fr; }
      }
    </style>

    <div class="hrd-wrap">
      <div class="hrd-hero">
        <h1>Welcome back, HR Team</h1>
        <p>Manage employee services, approvals, compliance, and payroll-impact requests from one place.</p>
        <div class="hrd-user"><span id="hrd-user-email">-</span><span id="hrd-user-role">-</span></div>
      </div>

      <div class="hrd-stats">
        <div class="hrd-stat"><div class="value" id="stat-employees">0</div><div class="label">Total Employees</div></div>
        <div class="hrd-stat"><div class="value" id="stat-training">0</div><div class="label">Pending Training</div></div>
        <div class="hrd-stat"><div class="value" id="stat-allowance">0</div><div class="label">Pending Allowance</div></div>
        <div class="hrd-stat"><div class="value" id="stat-license">0</div><div class="label">Active Licenses</div></div>
      </div>

      <h2 class="hrd-section-title">HR Operations</h2>
      <p class="hrd-section-sub">Process requests, track compliance, and manage employee lifecycle activities.</p>

      <div class="hrd-cards">
        <div class="hrd-card">
          <div>
            <h3>Employee Services</h3>
            <p>Handle permission, remote work, return-from-leave, and salary certificate requests.</p>
          </div>
          <a class="hrd-btn" href="/app/medical-hrms">Open HR Workspace</a>
        </div>
        <div class="hrd-card">
          <div>
            <h3>Financial Requests</h3>
            <p>Review training, overtime, allowance, and company car requests before finance handoff.</p>
          </div>
          <a class="hrd-btn" href="/app/employee-training-request">Open Training Requests</a>
        </div>
        <div class="hrd-card">
          <div>
            <h3>Compliance & Records</h3>
            <p>Maintain medical licenses and employee data updates with auditable status history.</p>
          </div>
          <a class="hrd-btn" href="/app/employee-medical-license">Open Medical Licenses</a>
        </div>
      </div>

      <div class="hrd-group">
        <h3>Employee Request Management</h3>
        <div class="hrd-module-grid" id="hrd-requests-grid"></div>
      </div>

      <div class="hrd-group">
        <h3>Core HR Transactions</h3>
        <div class="hrd-module-grid" id="hrd-core-grid"></div>
      </div>

      <div class="hrd-group">
        <h3>Compliance & Employee Records</h3>
        <div class="hrd-module-grid" id="hrd-compliance-grid"></div>
      </div>

     
    </div>
  `);


  //  <div class="hrd-group">
  //       <h3>Jameah Master Data</h3>
  //       <div class="hrd-module-grid" id="hrd-master-grid"></div>
  //     </div>
  render_doctype_cards();
}

function render_doctype_cards() {
  const requestDoctypes = [
    ["Permission Request", "permission-request"],
    ["Remote Work Request", "remote-work-request"],
    ["Leave Plan Request", "leave-plan-request"],
    ["Return From Leave Request", "return-from-leave-request"],
    ["Salary Certificate Request", "salary-certificate-request"],
    ["Pre Approved Overtime Request", "pre-approved-overtime-request"],
    ["Employee Training Request", "employee-training-request"],
    ["Children Education Allowance Request", "children-education-allowance-request"],
    ["Company Car Request", "company-car-request"],
    ["Contract Renewal Request", "contract-renewal-request"],
    ["Employee Data Update Request", "employee-data-update-request"],
  ];

  const complianceDoctypes = [
    ["Employee Medical License", "employee-medical-license"],
    ["Employee", "employee"],
  ];

  const coreDoctypes = [
    ["Leave Application", "leave-application"],
    ["Attendance Request", "attendance-request"],
    ["Expense Claim", "expense-claim"],
    ["Travel Request", "travel-request"],
    ["Employee Separation", "employee-separation"],
    ["Full and Final Statement", "full-and-final-statement"],
  ];

  fillGrid("#hrd-requests-grid", requestDoctypes);
  fillGrid("#hrd-core-grid", coreDoctypes);
  fillGrid("#hrd-compliance-grid", complianceDoctypes);
}

function fillGrid(selector, items) {
  const html = items.map(([title, route]) => `
    <div class="hrd-module-card" data-dt="${frappe.utils.escape_html(title)}">
      <div class="hrd-module-title">${frappe.utils.escape_html(title)}</div>
      <div class="hrd-module-meta">
        <span class="hrd-count" data-count-for="${frappe.utils.escape_html(title)}">0</span>
        <a class="hrd-link" href="/app/${route}">Open</a>
      </div>
    </div>
  `).join("");
  $(selector).html(html);
}

function load_data() {
  frappe.call({
    method: "medical_hrms.medical_hrms.page.hr_dashboard.hr_dashboard.get_logged_in_user_details",
    callback: function (r) {
      const u = r?.message?.user;
      if (!u) return;
      $("#hrd-user-email").text(`✉ ${u.email || "-"}`);
      $("#hrd-user-role").text(`👤 ${u.role || "HR User"}`);
    },
  });

  frappe.call({
    method: "medical_hrms.medical_hrms.page.hr_dashboard.hr_dashboard.get_hr_dashboard_stats",
    callback: function (r) {
      const s = r?.message?.stats || {};
      $("#stat-employees").text(s.total_employees ?? 0);
      $("#stat-training").text(s.pending_training_requests ?? 0);
      $("#stat-allowance").text(s.pending_allowance_requests ?? 0);
      $("#stat-license").text(s.expiring_medical_licenses ?? 0);
    },
  });

  frappe.call({
    method: "medical_hrms.medical_hrms.page.hr_dashboard.hr_dashboard.get_hr_doctype_counts",
    callback: function (r) {
      const counts = r?.message?.counts || {};
      Object.keys(counts).forEach((dt) => {
        $(`[data-count-for="${dt}"]`).text(counts[dt] ?? 0);
      });
    },
  });
}
