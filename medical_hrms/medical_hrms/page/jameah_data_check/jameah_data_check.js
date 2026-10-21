// What the Ministry (Jameah) views would send right now. Data comes from
// medical_hrms.jameah.status.get_status.
frappe.pages["jameah-data-check"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("Jameah Data Check"), single_column: true });
	MhPortal.mount(page, { portal: "hr", active: "jameah-data-check", crumb: __("Jameah Data Check") });
	const esc = frappe.utils.escape_html;
	$(page.body).append(MhPortal.head({
		icon: "fa-building-columns", eyebrow: __("Ministry (Jameah) Data"), title: __("Jameah Data Check"),
		meta: [{ icon: "fa-circle-info", text: __("What the Ministry views would send right now") }],
		actions: [
			{ label: __("Code Map"), icon: "fa-right-left", onClick: () => frappe.set_route("List", "Jameah Code Map", { status: "Needs Review" }) },
			{ label: __("Jameah Settings"), icon: "fa-gear", onClick: () => frappe.set_route("Form", "Jameah Settings") },
			{ label: __("Refresh Academic Figures"), icon: "fa-graduation-cap", onClick: () =>
				frappe.call({ method: "medical_hrms.jameah.summary.refresh_now" }).then(() =>
					frappe.show_alert({ message: __("Queued. GPA and credit hours update in a few minutes."), indicator: "green" })) },
			{ label: __("Refresh"), icon: "fa-rotate", primary: true, id: "jdc-refresh", onClick: () => load() },
		],
	}));
	const $body = $(`<div class="jdc"></div>`).appendTo(page.body);
	$body.before(`<style>
		.jdc { padding: 0 0 32px; }
		.jdc h3 { font: 600 19px/1.3 var(--f-display); color: var(--text-primary); margin: 30px 0 6px; }
		.jdc .jdc-sub { color: var(--text-secondary); margin: 0 0 12px; font-size: 14px; }
		.jdc table code { font-size: 12.5px; color: var(--primary-dark); background: var(--lighter); padding: 2px 6px; border-radius: 6px; }
		[data-theme="dark"] .jdc table code { color: var(--primary); }
		.jdc .jdc-ok { color: var(--success); font-weight: 600; }
		.jdc .jdc-warn { color: var(--warning); font-weight: 600; }
		.jdc .jdc-bad { color: var(--error); font-weight: 600; }
		.jdc-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 18px; }
		.jdc-card { background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: 22px 24px; box-shadow: var(--shadow-sm); color: var(--text-secondary); font-size: 13.5px; font-weight: 600; letter-spacing: .03em; text-transform: uppercase; }
		.jdc-card strong { display: block; font: 700 36px/1.1 var(--f-display); margin-bottom: 12px; letter-spacing: -.02em; text-transform: none; }
		.jdc ul { margin: 0; padding-inline-start: 20px; color: var(--text-primary); }
	</style>`);

	function table(head, rows) {
		return `<div class="jdc-wrap mhp-tablewrap"><table class="mhp-table"><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead>
			<tbody>${rows.join("")}</tbody></table></div>`;
	}

	function render(d) {
		const gaps = d.views.reduce((n, v) => n + v.mandatory_missing.length, 0);
		const invalid = d.views.reduce((n, v) => n + v.invalid_codes, 0);
		let html = `<div class="jdc-cards">
			<div class="jdc-card"><strong class="${invalid ? "jdc-bad" : "jdc-ok"}">${invalid}</strong>${__("Invalid Ministry codes sent")}</div>
			<div class="jdc-card"><strong class="${d.needs_review.length ? "jdc-warn" : "jdc-ok"}">${d.needs_review.length}</strong>${__("Values waiting for a Ministry code")}</div>
			<div class="jdc-card"><strong class="${d.settings_missing.length ? "jdc-warn" : "jdc-ok"}">${d.settings_missing.length}</strong>${__("Settings not filled")}</div>
			<div class="jdc-card"><strong class="${gaps ? "jdc-warn" : "jdc-ok"}">${gaps}</strong>${__("Mandatory columns with gaps")}</div>
		</div>
		<p class="jdc-sub" style="margin-top:10px">${__("Academic figures (GPA, credit hours) last refreshed")}: ${esc(d.summary_refreshed_on ? frappe.datetime.str_to_user(d.summary_refreshed_on) : __("never"))}.
			${__("Teaching staff left out of the Employee views (sent as Faculty)")}: ${d.teaching_staff_excluded}.</p>`;

		if (d.settings_missing.length) {
			html += `<h3>${__("Settings to fill")}</h3><p class="jdc-sub">${__("Until these are set, the matching columns are sent empty.")}</p>
				<ul>${d.settings_missing.map((s) => `<li>${esc(s)}</li>`).join("")}</ul>`;
		}
		if (d.needs_review.length) {
			html += `<h3>${__("Values waiting for a Ministry code")}</h3>
				<p class="jdc-sub">${__("Open a row, pick the Ministry code and set Status to Verified. Until then the value is sent empty.")}</p>` +
				table([__("Source"), __("Value"), __("Ministry list"), __("Records"), __("Suggestions")], d.needs_review.map((r) =>
					`<tr><td>${esc(r.source_doctype)}</td><td><a href="/app/jameah-code-map/${encodeURIComponent(r.name)}">${esc(r.source_value)}</a></td>
					<td>${esc(r.code_category)}</td><td>${r.usage_count}</td><td style="white-space:pre-line">${esc(r.suggestion || "")}</td></tr>`));
		}
		html += `<h3>${__("Views")}</h3>` + table([__("View"), __("Section"), __("Rows"), __("Invalid codes"), __("Mandatory gaps")], d.views.map((v) =>
			`<tr><td><code>${esc(v.view)}</code></td><td>${esc(v.section)}</td><td>${v.rows}</td>
			<td class="${v.invalid_codes ? "jdc-bad" : "jdc-ok"}">${v.invalid_codes}</td>
			<td>${v.mandatory_missing.length ? v.mandatory_missing.map((m) =>
				`<div><b>${esc(m.column)}</b>: ${m.missing} ${esc(m.scope === "graduates" ? __("graduates") : __("rows"))}${m.note ? ` <span class="text-muted">— ${esc(m.note)}</span>` : ""}</div>`).join("") :
				`<span class="jdc-ok">${__("None")}</span>`}</td></tr>`));
		if (d.data_problems.length) {
			html += `<h3>${__("Source data to correct")}</h3><p class="jdc-sub">${__("The views send these as they are (or empty); fix them in the source records.")}</p>` +
				table([__("Problem"), __("Records")], d.data_problems.map((p) => `<tr><td>${esc(p.problem)}</td><td>${p.count}</td></tr>`));
		}
		$body.html(html);
	}

	function load() {
		$body.html(`<div class="mhp-empty"><i class="fa-solid fa-magnifying-glass-chart"></i>${__("Checking the Ministry views…")}</div>`);
		frappe.call({ method: "medical_hrms.jameah.status.get_status", freeze: false }).then((r) => render(r.message || {}));
	}
	load();
};
