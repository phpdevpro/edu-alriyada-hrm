// My HR on the staff dashboards (Round 3, HR-11). Instructors, heads of department, deans and the other staff land on
// their own dashboard (education app), not on the Employee Portal. For a login linked to an Employee record, this
// adds one card to that dashboard: leave balances and what's next, the latest requests with their status, and the
// same request dialogs as the Employee Portal (self_service.js). Nothing in the education app changes: the card is
// placed after the dashboard's first row of figures, and placed again whenever the dashboard redraws that part.
(() => {
	// Dashboard page -> the element the card goes after (the Advisor dashboard has no figures: after its heading).
	const SPOTS = {
		"instructor-dashboard": "#instructor-dashboard-page > #stats-grid",
		"department-dashboard": "#dhd-stats",
		"dean-dashboard": "#exs-view > .exs-row",
		"admin-dashboard": "#exs-view > .exs-row",
		"academic-dashboard": "#exs-view > .exs-row",
		"it-dashboard": "#exs-view > .exs-row",
		"academic-operations": "#exs-view > .exs-row",
		"student-affair": "#sad-main-view > .sad-stats-grid",
		"admission-dashboard": "#adc-kpis",
		"finance-dashboard": "#fd-summary",
		"clinical-manager": "#cd-kpis",
		"advisor-dashboard": ".advisor-dashboard > .ash-pagehead",
	};
	const FRESH_FOR = 60 * 1000; // coming back to the dashboard after this long loads the figures again
	const SS = () => window.MhSelfService;
	let data = null;
	let loadedAt = 0;
	let loading = null;
	let observer = null;
	let timer = null;

	// no route yet at the first page-load call (frappe.get_route() is null until the router has run)
	const page = () => ((frappe.get_route && frappe.get_route()) || [])[0] || "";
	const visible = (el) => !!(el && el.getClientRects().length);
	const spotOf = (selector) => [...document.querySelectorAll(selector)].find(visible);
	const hasCard = (spot) => !!(spot && spot.nextElementSibling && spot.nextElementSibling.classList.contains("mhs-card"));
	// The Employee role comes with the link to an Employee record (ERPNext adds it to the login).
	const eligible = () => frappe.session && !["Guest", "Administrator"].includes(frappe.session.user) && frappe.user.has_role("Employee");

	function load() {
		if (data && Date.now() - loadedAt < FRESH_FOR) return Promise.resolve(data);
		if (!loading) {
			loading = frappe.xcall("medical_hrms.medical_hrms.page.employee_dashboard.employee_dashboard.get_dashboard_data")
				.then((r) => {
					data = r || {};
					loadedAt = Date.now();
					if (data.employee) SS().setEmployee(data.employee);
					return data;
				})
				.catch(() => ({}))
				.finally(() => { loading = null; });
		}
		return loading;
	}

	function place() {
		const name = page();
		const selector = SPOTS[name];
		if (!selector || !eligible() || hasCard(spotOf(selector))) return;
		if (!spotOf(selector)) return; // the dashboard has not drawn its figures yet; the observer calls again
		load().then((d) => {
			const spot = spotOf(selector); // looked up again: the dashboard may have redrawn while loading
			if (!d || !d.employee || page() !== name || !spot || hasCard(spot)) return;
			spot.insertAdjacentElement("afterend", render(d));
		});
	}

	function refresh() {
		data = null;
		document.querySelectorAll(".mhs-card").forEach((card) => card.remove());
		place();
	}

	// Watch the page while a staff dashboard shows: it draws its figures after loading, and redraws them (term change ...).
	function watch(on) {
		if (on && !observer) {
			observer = new MutationObserver(() => {
				clearTimeout(timer);
				timer = setTimeout(place, 150);
			});
			observer.observe(document.body, { childList: true, subtree: true });
		} else if (!on && observer) {
			observer.disconnect();
			observer = null;
		}
	}

	function onPageChange() {
		const onDashboard = !!SPOTS[page()] && eligible();
		watch(onDashboard);
		if (!onDashboard) return;
		if (data && Date.now() - loadedAt >= FRESH_FOR) refresh();
		else place();
	}

	function render(d) {
		const esc = SS().esc;
		const balances = Object.entries((d.leave_summary && d.leave_summary.balances) || {})
			.sort(([a], [b]) => Number(/annual/i.test(b)) - Number(/annual/i.test(a)))
			.slice(0, 3);
		const steps = (d.leave_flow || []).map((s) => ({ s, k: SS().leaveStep(s) })).filter((x) => x.k).slice(0, 3);
		const recent = (d.recent_requests || []).slice(0, 4);
		const waiting = (d.stats && d.stats.pending) || 0;

		const balanceHtml = balances.length
			? `<div class="mhs-balances">${balances.map(([type, b]) => `<div class="mhs-balance">
				<b>${esc(b.remaining_leaves)}</b><span>${esc(__(type))}</span><small>${esc(__("of {0} days", [b.total_leaves]))}</small></div>`).join("")}</div>`
			: `<p class="mhs-muted">${esc(__("No leave assigned to you yet. HR assigns annual leave at the start of the leave year."))}</p>`;
		const stepHtml = steps.map(({ k }, i) => `<div class="mhs-step">
				<span class="mhs-dot ${esc(k.tone)}" aria-hidden="true"><i class="fa-solid ${esc(k.icon)}"></i></span>
				<span class="mhs-step-text">${k.text}</span>
				${k.button ? `<button type="button" class="mhs-btn sm primary mhs-step-btn" data-i="${i}">${esc(k.button)}</button>` : ""}
			</div>`).join("");
		const recentHtml = recent.length
			? recent.map((row) => `<div class="mhs-row">
				<div class="mhs-row-main"><b>${esc(__(row.doctype))}</b><small>${esc(row.name)} · ${frappe.datetime.comment_when(row.modified)}</small></div>
				<span class="mhs-pill ${SS().statusTone(row.status)}">${esc(__(row.status))}</span>
				${SS().isService(row.doctype) ? `<button type="button" class="mhs-link mhs-view" data-doctype="${esc(row.doctype)}" data-name="${esc(row.name)}">${esc(__("View"))}</button>` : ""}
			</div>`).join("")
			: `<p class="mhs-muted">${esc(__("No requests yet. Use New Request to send one."))}</p>`;

		const card = document.createElement("section");
		card.className = "mhs-card";
		card.setAttribute("aria-label", __("My HR"));
		card.innerHTML = `
			<div class="mhs-head">
				<span class="mhs-icon" aria-hidden="true"><i class="fa-solid fa-id-badge"></i></span>
				<div class="mhs-titles">
					<h3>${esc(__("My HR"))}</h3>
					<p>${esc(__("Your leave and HR requests"))} · <span class="mhs-id">${esc(d.employee.name)}</span></p>
				</div>
				<div class="mhs-actions">
					<button type="button" class="mhs-btn primary mhs-apply"><i class="fa-solid fa-calendar-plus" aria-hidden="true"></i>${esc(__("Apply for Leave"))}</button>
					<div class="dropdown mhs-menu">
						<button type="button" class="mhs-btn mhs-new" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
							<i class="fa-solid fa-plus" aria-hidden="true"></i>${esc(__("New Request"))}<i class="fa-solid fa-chevron-down mhs-caret" aria-hidden="true"></i></button>
						<div class="dropdown-menu dropdown-menu-right mhs-services">
							${SS().services().map(([title, doctype, , icon]) => `<button type="button" class="dropdown-item mhs-service" data-doctype="${esc(doctype)}"><i class="fa-solid ${esc(icon)}" aria-hidden="true"></i>${esc(title)}</button>`).join("")}
						</div>
					</div>
					<a class="mhs-btn ghost mhs-portal" href="/app/employee-dashboard">${esc(__("Employee Portal"))}<i class="fa-solid fa-arrow-right mhs-flip" aria-hidden="true"></i></a>
				</div>
			</div>
			<div class="mhs-body">
				<div class="mhs-panel mhs-leave">
					<h4>${esc(__("My Leave"))}</h4>
					${balanceHtml}
					${stepHtml ? `<div class="mhs-steps">${stepHtml}</div>` : ""}
				</div>
				<div class="mhs-panel mhs-requests">
					<h4>${esc(__("My Requests"))}${waiting ? ` <span class="mhs-pill amber mhs-waiting">${esc(waiting === 1 ? __("1 waiting") : __("{0} waiting", [waiting]))}</span>` : ""}</h4>
					<div class="mhs-rows">${recentHtml}</div>
				</div>
			</div>`;
		$(card)
			.on("click", ".mhs-apply", () => SS().newRequest("Leave Application"))
			.on("click", ".mhs-service", function () { SS().newRequest($(this).attr("data-doctype")); })
			.on("click", ".mhs-view", function () { SS().showDetails($(this).attr("data-doctype"), $(this).attr("data-name")); })
			.on("click", ".mhs-step-btn", function () { SS().runLeaveStep(steps[Number($(this).attr("data-i"))].s); });
		return card;
	}

	$(document).on("page-change", onPageChange);
	$(() => {
		if (window.MhSelfService) SS().onChange("staff-hr-card", () => { if (SPOTS[page()]) refresh(); else data = null; });
		onPageChange();
	});
})();
