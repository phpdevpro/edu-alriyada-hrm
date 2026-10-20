// What the Ministry (Jameah) views would send right now. Data comes from
// medical_hrms.jameah.status.get_status.
frappe.pages["jameah-data-check"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("Jameah Data Check"), single_column: true });
	const esc = frappe.utils.escape_html;
	const $body = $(`<div class="jdc"></div>`).appendTo(page.body);
	$body.before(`<style>
		.jdc { padding: 8px 0 32px; }
		.jdc h3 { font-size: 16px; margin: 24px 0 8px; }
		.jdc .jdc-sub { color: var(--text-muted); margin: 0 0 10px; }
		.jdc table { width: 100%; border-collapse: collapse; font-size: 13px; background: var(--card-bg); }
		.jdc th, .jdc td { text-align: left; padding: 7px 9px; border-bottom: 1px solid var(--border-color); vertical-align: top; }
		.jdc th { background: var(--subtle-fg); white-space: nowrap; }
		.jdc .jdc-ok { color: var(--green-600); font-weight: 600; }
		.jdc .jdc-warn { color: var(--orange-600); font-weight: 600; }
		.jdc .jdc-bad { color: var(--red-600); font-weight: 600; }
		.jdc-cards { display: flex; flex-wrap: wrap; gap: 10px; }
		.jdc-card { flex: 1 1 180px; border: 1px solid var(--border-color); border-radius: 10px; padding: 12px 14px; background: var(--card-bg); }
		.jdc-card strong { display: block; font-size: 24px; }
		.jdc-wrap { overflow-x: auto; }
	</style>`);

	page.set_primary_action(__("Refresh"), () => load(), "refresh");
	page.add_inner_button(__("Jameah Settings"), () => frappe.set_route("Form", "Jameah Settings"));
	page.add_inner_button(__("Code Map"), () => frappe.set_route("List", "Jameah Code Map", { status: "Needs Review" }));
	page.add_inner_button(__("Refresh Academic Figures"), () =>
		frappe.call({ method: "medical_hrms.jameah.summary.refresh_now" }).then(() =>
			frappe.show_alert({ message: __("Queued. GPA and credit hours update in about a minute."), indicator: "green" })));

	function table(head, rows) {
		return `<div class="jdc-wrap"><table><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead>
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
		$body.html(`<p class="text-muted">${__("Checking the Ministry views…")}</p>`);
		frappe.call({ method: "medical_hrms.jameah.status.get_status", freeze: false }).then((r) => render(r.message || {}));
	}
	load();
};
