frappe.pages["job-application"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		single_column: true,
	});

	$(wrapper).find(".page-head .title-area").remove();
	$(wrapper).find(".page-head-content").remove();

	const allowed =
		frappe.user.has_role("HR User") ||
		frappe.user.has_role("HR Manager") ||
		frappe.user.has_role("System Manager");

	if (!allowed) {
		$(page.body).html(
			'<div style="padding:24px;font-size:16px;">You are not authorized to view this page.</div>'
		);
		return;
	}

	render_layout(page);
};

function render_layout(page) {
	$(page.body).html(`
		<style>
			.ja-admin-wrap { max-width: 1200px; margin: 0 auto; padding: 18px 10px 36px; }
			.ja-admin-hero {
				background: linear-gradient(135deg, #2563eb 0%, #10b981 100%);
				border-radius: 18px;
				padding: 26px 32px;
				color: #fff;
				box-shadow: 0 14px 24px rgba(15, 23, 42, 0.18);
				margin-bottom: 24px;
			}
			.ja-admin-hero h1 { margin: 0 0 8px; font-size: 34px; font-weight: 700; color: #fff; }
			.ja-admin-hero p { margin: 0; font-size: 16px; opacity: 0.95; }
			.ja-admin-grid { display: grid; grid-template-columns: repeat(2, minmax(260px, 1fr)); gap: 16px; }
			.ja-admin-card {
				background: #fff;
				border-radius: 16px;
				padding: 20px;
				box-shadow: 0 8px 16px rgba(15, 23, 42, 0.1);
				border: 1px solid #e2e8f0;
			}
			.ja-admin-card h3 { margin: 0 0 8px; font-size: 20px; color: #0f172a; }
			.ja-admin-card p { margin: 0 0 14px; color: #475569; }
			.ja-admin-btn {
				display: inline-block;
				padding: 8px 14px;
				border-radius: 999px;
				background: #eff6ff;
				color: #1d4ed8;
				text-decoration: none;
				font-weight: 600;
				border: 1px solid #bfdbfe;
			}
			.ja-admin-btn.secondary { background: #ecfdf3; color: #047857; border-color: #a7f3d0; }
			.ja-admin-btn.ghost { background: #fff; color: #0f172a; border-color: #cbd5f5; }
			@media (max-width: 900px) {
				.ja-admin-grid { grid-template-columns: 1fr; }
			}
		</style>

		<div class="ja-admin-wrap">
			<div class="ja-admin-hero">
				<h1>Job Application Management</h1>
				<p>Create public links, review applicants, and preview the guest-facing application form.</p>
			</div>

			<div class="ja-admin-grid">
				<div class="ja-admin-card">
					<h3>Application Links</h3>
					<p>Manage public links for external applicants.</p>
					<div style="display:flex;gap:8px;flex-wrap:wrap;">
						<a class="ja-admin-btn" href="/app/job-application-link/new">New Link Record</a>
						<a class="ja-admin-btn ghost" href="/app/job-application-link">Open Link Manager</a>
					</div>
				</div>
				<div class="ja-admin-card">
					<h3>Review Applications</h3>
					<p>Approve, reject, and convert Job Applicant records into Employee profiles.</p>
					<a class="ja-admin-btn secondary" href="/app/medical-hrms-job-applicant">Open Job Applicants</a>
				</div>
				<div class="ja-admin-card">
					<h3>Preview Public Form</h3>
					<p>Open the application form preview (admin-only) without a token.</p>
					<a class="ja-admin-btn ghost" href="/job-application" target="_blank">Open Preview</a>
				</div>
			</div>
		</div>
	`);
}
