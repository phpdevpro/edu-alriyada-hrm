// MhPortal - the HR Portal and Employee Portal shell: a left rail and a top bar drawn around the
// Medical HRMS pages, in the same design as the Education portals (Instructor Portal ...).
//
// Our own implementation and class names (mhp-*, styles in public/css/hr_portal.css) rather than
// Education's DashboardTopbar / *Shell scripts: those carry Education's routes and roles, and
// Education's global page scripts act on anything inside their .sad-shell markup.
//
// Usage, in a page's on_page_load:
//   const portal = MhPortal.mount(page, { portal: "hr", active: "dashboard" });
//   $(page.body).html(...)          // the page keeps drawing into page.body, now inside the shell
//   MhPortal.head(page, {...})      // optional page heading (icon, eyebrow, title, meta, actions)
//   MhPortal.on("new-request", fn)  // employee rail entries that act on the dashboard
(function () {
	const esc = (v) => frappe.utils.escape_html(String(v == null ? "" : v));
	const COLLAPSE_KEY = "mhp:rail-collapsed";
	const HR_ROLES = ["HR User", "HR Manager", "System Manager"];
	const handlers = {};

	const dt = (doctype, icon, label) => ({ id: frappe.router.slug(doctype), icon, label: label || __(doctype), route: `/app/${frappe.router.slug(doctype)}`, doctype });

	const PORTALS = {
		hr: {
			title: () => __("HR Portal"),
			home: "/app/hr-dashboard",
			groups: () => [
				{ label: __("Overview"), items: [{ id: "dashboard", icon: "fa-gauge-high", label: __("Dashboard"), route: "/app/hr-dashboard" }] },
				{
					label: __("People"),
					items: [
						dt("Employee", "fa-users", __("Employees")),
						{
							id: "requests", icon: "fa-inbox", label: __("Employee Requests"),
							children: [
								dt("Permission Request", "fa-clock"), dt("Remote Work Request", "fa-laptop-house"), dt("Salary Certificate Request", "fa-file-invoice"),
								dt("Pre Approved Overtime Request", "fa-business-time"), dt("Employee Training Request", "fa-chalkboard"),
								dt("Children Medical Allowance Request", "fa-hand-holding-medical"), dt("Company Car Request", "fa-car"),
								dt("Contract Renewal Request", "fa-file-signature"), dt("Employee Data Update Request", "fa-user-pen"),
							],
						},
						{
							id: "leave", icon: "fa-umbrella-beach", label: __("Leave"),
							// Daily work first (plan -> apply -> return), then the yearly setup in the order it is done.
							children: [
								dt("Leave Application", "fa-calendar-check"), dt("Leave Plan Request", "fa-calendar-week"), dt("Leave Return Request", "fa-rotate-left"),
								dt("Leave Period", "fa-calendar"), dt("Holiday List", "fa-calendar-day"), dt("Leave Policy", "fa-book"),
								{ id: "leave-control-panel", icon: "fa-sliders", label: __("Leave Control Panel"), route: "/app/leave-control-panel", doctype: "Leave Control Panel" },
								dt("Leave Policy Assignment", "fa-user-tag"), dt("Leave Allocation", "fa-scale-balanced"), dt("Leave Type", "fa-tags"),
							],
						},
						{
							id: "transactions", icon: "fa-briefcase", label: __("HR Transactions"),
							children: [
								dt("Attendance Request", "fa-user-check"), dt("Expense Claim", "fa-receipt"), dt("Travel Request", "fa-plane"),
								dt("Employee Separation", "fa-door-open"), dt("Full and Final Statement", "fa-file-contract"),
							],
						},
					],
				},
				{
					label: __("Hiring & Records"),
					items: [
						{ id: "recruitment", icon: "fa-user-plus", label: __("Recruitment"), children: [dt("Job Application Link", "fa-link"), dt("Employee Job Applicant", "fa-id-badge", __("Job Applicants"))] },
						dt("Employee Medical License", "fa-id-card-clip", __("Medical Licenses")),
					],
				},
				{
					label: __("Academic & Ministry"),
					items: [
						{
							id: "presence", icon: "fa-chalkboard-user", label: __("Academic Presence"),
							children: [
								{ id: "presence-faculty", icon: "fa-person-chalkboard", label: __("Faculty Schedules"), route: "/app/hr-academic-presence/faculty" },
								{ id: "presence-proctors", icon: "fa-user-shield", label: __("Proctor Schedules"), route: "/app/hr-academic-presence/proctors" },
								{ id: "presence-students", icon: "fa-user-graduate", label: __("Students on Campus"), route: "/app/hr-academic-presence/students" },
								{ id: "presence-after_hours", icon: "fa-moon", label: __("Faculty After 4 PM"), route: "/app/hr-academic-presence/after_hours" },
							],
						},
						{
							id: "jameah", icon: "fa-building-columns", label: __("Ministry (Jameah)"),
							children: [
								{ id: "jameah-data-check", icon: "fa-clipboard-check", label: __("Jameah Data Check"), route: "/app/jameah-data-check" },
								{ id: "jameah-missing", icon: "fa-user-xmark", label: __("Employees Missing Ministry Data"), route: "/app/query-report/Employees Missing Ministry Data" },
								dt("Jameah Code Map", "fa-right-left", __("Code Map")),
								{ id: "jameah-settings", icon: "fa-gear", label: __("Jameah Settings"), route: "/app/jameah-settings", doctype: "Jameah Settings" },
							],
						},
					],
				},
				{
					label: __("Settings"),
					items: [
						{ id: "hr-settings", icon: "fa-sliders", label: __("HR Settings"), route: "/app/hr-settings", doctype: "HR Settings" },
						{ id: "workspace", icon: "fa-table-cells-large", label: __("HR Workspace"), route: "/app/medical-hrms" },
					],
				},
			],
		},
		employee: {
			title: () => __("Employee Portal"),
			home: "/app/employee-dashboard",
			groups: () => [
				{ label: __("Overview"), items: [{ id: "dashboard", icon: "fa-gauge-high", label: __("Dashboard"), route: "/app/employee-dashboard" }] },
				{
					label: __("My Work"),
					items: [
						{
							id: "new", icon: "fa-circle-plus", label: __("New Request"),
							children: [
								["Leave Plan Request", "fa-calendar-week", __("Leave Plan")], ["Leave Application", "fa-calendar-check", __("Leave Application")],
								["Leave Return Request", "fa-rotate-left", __("Leave Return")],
								["Permission Request", "fa-clock", __("Permission Request")], ["Remote Work Request", "fa-laptop-house", __("Remote Work")],
								["Salary Certificate Request", "fa-file-invoice", __("Salary Certificate")], ["Pre Approved Overtime Request", "fa-business-time", __("Overtime")],
								["Employee Training Request", "fa-chalkboard", __("Training")], ["Children Medical Allowance Request", "fa-hand-holding-medical", __("Medical Allowance")],
								["Company Car Request", "fa-car", __("Company Car")], ["Employee Data Update Request", "fa-user-pen", __("Update My Data")],
							].map(([doctype, icon, label]) => ({ id: `new-${frappe.router.slug(doctype)}`, icon, label, action: "new-request", arg: doctype })),
						},
						{ id: "my-leave", icon: "fa-umbrella-beach", label: __("My Leave"), action: "scroll", arg: "emd-leave-summary" },
						{ id: "my-requests", icon: "fa-list-check", label: __("Recent Requests"), action: "scroll", arg: "emd-recent-card" },
					],
				},
				{
					label: __("Records"),
					items: [
						dt("Attendance Request", "fa-user-check", __("Attendance Requests")),
						dt("Expense Claim", "fa-receipt", __("Expense Claims")),
						{ id: "profile", icon: "fa-id-card", label: __("My Profile"), action: "profile" },
					],
				},
			],
		},
	};

	// ── Who sees what ───────────────────────────────────────────────────────────────
	const hasRole = (roles) => frappe.session.user === "Administrator" || roles.some((r) => frappe.user.has_role(r));
	const isHr = () => hasRole(HR_ROLES);
	const isEmployee = () => frappe.session.user === "Administrator" || frappe.user.has_role("Employee");

	function visible(item) {
		if (item.doctype) return frappe.model.can_read(item.doctype);
		return true;
	}

	function groupsFor(portal) {
		return PORTALS[portal].groups()
			.map((g) => ({
				label: g.label,
				items: g.items
					.map((it) => (it.children ? Object.assign({}, it, { children: it.children.filter(visible) }) : it))
					.filter((it) => (it.children ? it.children.length : visible(it))),
			}))
			.filter((g) => g.items.length);
	}

	// ── Rail ────────────────────────────────────────────────────────────────────────
	function navButton(it, active, extra) {
		const current = it.id === active;
		const attrs = `class="mhp-navbtn" data-id="${esc(it.id)}"${it.action ? ` data-action="${esc(it.action)}" data-arg="${esc(it.arg || "")}"` : ""}${current ? ' aria-current="page"' : ""}${extra || ""}`;
		const inner = `<span class="mhp-navmain"><i class="fa-solid ${esc(it.icon)}" aria-hidden="true"></i><span>${esc(it.label)}</span></span>`;
		return it.route && !it.children
			? `<a href="${esc(encodeURI(it.route))}" ${attrs}>${inner}</a>`
			: `<button type="button" ${attrs}>${inner}${it.children ? '<i class="fa-solid fa-chevron-down mhp-chev" aria-hidden="true"></i>' : ""}</button>`;
	}

	function navHtml(portal, active) {
		return groupsFor(portal).map((g) => `
			<div class="mhp-navlabel">${esc(g.label)}</div>
			${g.items.map((it) => {
				if (!it.children) return navButton(it, active, ` title="${esc(it.label)}"`);
				const hasCurrent = it.children.some((c) => c.id === active);
				return `<div class="mhp-group${hasCurrent ? " is-open has-current" : ""}" data-group="${esc(it.id)}">
					${navButton(it, active, ` aria-expanded="${hasCurrent}" title="${esc(it.label)}"`)}
					<div class="mhp-sub"${hasCurrent ? "" : " hidden"}>${it.children.map((c) => navButton(c, active)).join("")}</div>
				</div>`;
			}).join("")}`).join("");
	}

	function initials(name) {
		return (name || "").split(/\s+/).filter(Boolean).slice(0, 2).map((s) => s.charAt(0).toUpperCase()).join("") || "--";
	}

	function shellHtml(portal, active, crumb) {
		const P = PORTALS[portal];
		const me = frappe.session.user;
		const name = frappe.session.user_fullname || me;
		const image = (frappe.user_info(me) || {}).image;
		const lang = (frappe.boot.lang || "en").toLowerCase();
		const otherPortal = portal === "hr" ? (isEmployee() && frappe.user.has_role("Employee") ? "employee" : null) : (isHr() ? "hr" : null);
		return `
		<div class="mhp-shell" data-portal="${esc(portal)}">
			<div class="mhp-app">
				<aside class="mhp-rail" aria-label="${esc(P.title())}">
					<a class="mhp-brand" href="${esc(P.home)}"><img src="/assets/medical_hrms/images/rchs-logo.png" alt="${esc(__("RCHS"))}" onerror="this.style.visibility='hidden'"><b>${esc(P.title())}</b></a>
					<nav class="mhp-nav">${navHtml(portal, active)}</nav>
					<div class="mhp-railfoot">
						<button type="button" class="mhp-navbtn mhp-collapse"><span class="mhp-navmain"><i class="fa-solid fa-angles-left" aria-hidden="true"></i><span>${esc(__("Collapse menu"))}</span></span></button>
					</div>
				</aside>
				<div class="mhp-scrim"></div>
				<main class="mhp-main">
					<div class="mhp-bar">
						<button type="button" class="mhp-iconbtn mhp-menu-btn" aria-label="${esc(__("Menu"))}"><i class="fa-solid fa-bars"></i></button>
						<nav class="mhp-crumbs" aria-label="${esc(__("Breadcrumb"))}">
							<i class="fa-solid fa-gauge-high" aria-hidden="true"></i>
							<a href="${esc(P.home)}">${esc(P.title())}</a><span class="sep">/</span><b class="mhp-crumb">${esc(crumb)}</b>
						</nav>
						<div class="mhp-actions">
							<div class="mhp-lang" role="group" aria-label="${esc(__("Language"))}">
								<button type="button" data-lang="en" class="${lang === "ar" ? "" : "active"}">EN</button><button type="button" data-lang="ar" class="${lang === "ar" ? "active" : ""}">AR</button>
							</div>
							<button type="button" class="mhp-iconbtn mhp-theme" aria-label="${esc(__("Toggle dark mode"))}" title="${esc(__("Toggle dark mode"))}"><i class="fa-regular fa-moon"></i><i class="fa-regular fa-sun"></i></button>
							<div class="mhp-pop">
								<button type="button" class="mhp-iconbtn mhp-bell" aria-label="${esc(__("Notifications"))}" aria-expanded="false"><i class="fa-regular fa-bell"></i><span class="mhp-dot" hidden></span></button>
								<div class="mhp-panel" data-panel="notifications" hidden>
									<div class="mhp-panel-head"><span>${esc(__("Notifications"))}</span><button type="button" class="mhp-readall">${esc(__("Mark all as read"))}</button></div>
									<div class="mhp-notifs"><div class="mhp-panel-empty">${esc(__("Loading..."))}</div></div>
								</div>
							</div>
							<div class="mhp-pop">
								<button type="button" class="mhp-avatar" aria-label="${esc(__("Account"))}" aria-expanded="false">${image ? `<img src="${esc(image)}" alt="" onerror="this.remove()">` : ""}${image ? "" : esc(initials(name))}</button>
								<div class="mhp-panel mhp-account" data-panel="account" hidden>
									<div class="mhp-account-head"><b>${esc(name)}</b><span>${esc(me)}</span></div>
									${portal === "employee" ? `<button type="button" class="mhp-menuitem" data-act="profile"><i class="fa-solid fa-id-card"></i>${esc(__("My Profile"))}</button>` : ""}
									<a class="mhp-menuitem" href="/app/user/${encodeURIComponent(me)}"><i class="fa-solid fa-gear"></i>${esc(__("My Settings"))}</a>
									${otherPortal ? `<a class="mhp-menuitem" href="${esc(PORTALS[otherPortal].home)}"><i class="fa-solid fa-repeat"></i>${esc(__("Switch to {0}", [PORTALS[otherPortal].title()]))}</a>` : ""}
									<button type="button" class="mhp-menuitem danger" data-act="logout"><i class="fa-solid fa-right-from-bracket"></i>${esc(__("Log Out"))}</button>
								</div>
							</div>
						</div>
					</div>
					<div class="mhp-view"></div>
				</main>
			</div>
		</div>`;
	}

	// ── Assets: the fonts and icon set the Education portals use ────────────────────
	function ensureAssets() {
		if (!document.querySelector('link[href*="family=Sora"]')) {
			$("head").append('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Figtree:wght@400;500;600;700&display=swap">');
		}
		if (!document.querySelector('link[href*="font-awesome/6"]')) {
			$("head").append('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">');
		}
	}

	// Frappe's navbar is hidden only while the page on screen carries the shell: an HR page a user may not
	// open shows Frappe's "Not permitted" page instead, which must keep the navbar to get away from it.
	function syncBodyClass() {
		const current = frappe.container && frappe.container.page;
		document.body.classList.toggle("mhp-on", !!(current && current.classList && current.classList.contains("mhp-page")));
	}

	// ── Top bar behaviour ───────────────────────────────────────────────────────────
	function closePanels($shell) {
		$shell.find(".mhp-panel").prop("hidden", true);
		$shell.find(".mhp-bell, .mhp-avatar").attr("aria-expanded", "false");
	}

	function togglePanel($shell, $btn, name) {
		const $panel = $shell.find(`.mhp-panel[data-panel="${name}"]`);
		const open = $panel.prop("hidden");
		closePanels($shell);
		$panel.prop("hidden", !open);
		$btn.attr("aria-expanded", String(open));
		return open;
	}

	function notifRoute(n) {
		if (n.link) return n.link;
		return n.document_type && n.document_name ? `/app/${frappe.router.slug(n.document_type)}/${encodeURIComponent(n.document_name)}` : "#";
	}

	function loadNotifications($shell) {
		frappe.call({
			method: "frappe.desk.doctype.notification_log.notification_log.get_notification_logs",
			args: { limit: 20 },
			callback(r) {
				const logs = (r.message && r.message.notification_logs) || [];
				$shell.find(".mhp-dot").prop("hidden", !logs.some((n) => !n.read));
				const $list = $shell.find(".mhp-notifs");
				if (!logs.length) {
					$list.html(`<div class="mhp-panel-empty">${esc(__("No notifications yet"))}</div>`);
					return;
				}
				$list.html(logs.map((n) => `<a class="mhp-notif${n.read ? "" : " unread"}" href="${esc(notifRoute(n))}" data-name="${esc(n.name)}">
					${esc($("<div>").html(n.subject || "").text())}<small>${esc(frappe.datetime.comment_when(n.creation))}</small></a>`).join(""));
			},
		});
	}

	function bindShell($shell, portal) {
		$shell.on("click", ".mhp-navbtn[data-action]", function (e) {
			e.preventDefault();
			$shell.removeClass("rail-open");
			trigger($(this).attr("data-action"), $(this).attr("data-arg"), portal);
		});
		$shell.on("click", ".mhp-group > .mhp-navbtn", function () {
			const $g = $(this).parent();
			if ($shell.hasClass("is-collapsed")) setCollapsed($shell, false);
			const open = !$g.hasClass("is-open");
			$shell.find(".mhp-group").not($g).removeClass("is-open").children(".mhp-sub").prop("hidden", true).end().children(".mhp-navbtn").attr("aria-expanded", "false");
			$g.toggleClass("is-open", open).children(".mhp-sub").prop("hidden", !open);
			$(this).attr("aria-expanded", String(open));
		});
		$shell.on("click", "a.mhp-navbtn, .mhp-brand", () => $shell.removeClass("rail-open"));
		$shell.find(".mhp-collapse").on("click", () => setCollapsed($shell, !$shell.hasClass("is-collapsed")));
		$shell.find(".mhp-menu-btn").on("click", () => $shell.toggleClass("rail-open"));
		$shell.find(".mhp-scrim").on("click", () => $shell.removeClass("rail-open"));

		$shell.find(".mhp-lang button").on("click", function () {
			const lang = $(this).data("lang");
			if (lang === (frappe.boot.lang || "en").toLowerCase()) return;
			frappe.call({
				method: "frappe.client.set_value",
				args: { doctype: "User", name: frappe.session.user, fieldname: "language", value: lang },
				freeze: true,
				callback: () => window.location.reload(),
			});
		});
		$shell.find(".mhp-theme").on("click", () => {
			const mode = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
			frappe.ui.set_theme(mode);
			document.documentElement.setAttribute("data-theme-mode", mode);
			frappe.call({ method: "frappe.core.doctype.user.user.switch_theme", args: { theme: mode === "dark" ? "Dark" : "Light" } });
		});
		$shell.find(".mhp-bell").on("click", function (e) {
			e.stopPropagation();
			if (togglePanel($shell, $(this), "notifications")) loadNotifications($shell);
		});
		$shell.find(".mhp-avatar").on("click", function (e) {
			e.stopPropagation();
			togglePanel($shell, $(this), "account");
		});
		$shell.on("click", ".mhp-panel", (e) => e.stopPropagation());
		$shell.on("click", ".mhp-notif", function () {
			const name = $(this).attr("data-name");
			frappe.call({ method: "frappe.desk.doctype.notification_log.notification_log.mark_as_read", args: { docname: name } });
		});
		$shell.find(".mhp-readall").on("click", () => {
			frappe.call({ method: "frappe.desk.doctype.notification_log.notification_log.mark_all_as_read", callback: () => loadNotifications($shell) });
		});
		$shell.on("click", '[data-act="logout"]', () => frappe.app.logout());
		$shell.on("click", '[data-act="profile"]', () => { closePanels($shell); trigger("profile", null, portal); });
		$(document).on("click.mhp", () => closePanels($shell));
		$(document).on("keydown.mhp", (e) => { if (e.key === "Escape") { closePanels($shell); $shell.removeClass("rail-open"); } });
		loadNotifications($shell);
	}

	function setCollapsed($shell, collapsed) {
		$shell.toggleClass("is-collapsed", collapsed);
		$shell.find(".mhp-collapse span span").text(collapsed ? __("Expand menu") : __("Collapse menu"));
		try { collapsed ? localStorage.setItem(COLLAPSE_KEY, "1") : localStorage.removeItem(COLLAPSE_KEY); } catch (e) { /* storage blocked */ }
	}

	// ── Actions the employee rail performs on the dashboard ────────────────────────
	function on(action, fn) {
		handlers[action] = fn;
	}

	function trigger(action, arg, portal) {
		if (action === "scroll") {
			const el = document.getElementById(arg);
			if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
			return;
		}
		if (handlers[action]) return handlers[action](arg);
		// The dashboard that handles it is not open yet: open it and run the action once it has loaded.
		try { sessionStorage.setItem("mhp:pending", JSON.stringify({ action, arg })); } catch (e) { /* storage blocked */ }
		frappe.set_route(PORTALS[portal || "employee"].home.replace("/app/", ""));
	}

	function runPending() {
		let pending = null;
		try { pending = JSON.parse(sessionStorage.getItem("mhp:pending") || "null"); sessionStorage.removeItem("mhp:pending"); } catch (e) { return; }
		if (pending && handlers[pending.action]) handlers[pending.action](pending.arg);
	}

	// ── Public API ──────────────────────────────────────────────────────────────────
	function mount(page, opts) {
		const $wrapper = $(page.wrapper);
		if ($wrapper.data("mhp-shell")) return $wrapper.data("mhp-shell");
		ensureAssets();
		const portal = PORTALS[opts.portal] ? opts.portal : "hr";
		const $shell = $(shellHtml(portal, opts.active || "dashboard", opts.crumb || __("Dashboard")));
		$wrapper.addClass("mhp-page").append($shell);
		$shell.find(".mhp-view").append(page.body);
		try { if (localStorage.getItem(COLLAPSE_KEY) === "1") setCollapsed($shell, true); } catch (e) { /* storage blocked */ }
		bindShell($shell, portal);
		$wrapper.data("mhp-shell", $shell);
		syncBodyClass();
		return $shell;
	}

	function setActive(page, id, crumb) {
		const $shell = $(page.wrapper).data("mhp-shell");
		if (!$shell) return;
		$shell.find(".mhp-navbtn[aria-current]").removeAttr("aria-current");
		const $btn = $shell.find(`.mhp-navbtn[data-id="${id}"]`).attr("aria-current", "page");
		$shell.find(".mhp-group").removeClass("has-current");
		const $g = $btn.closest(".mhp-group");
		if ($g.length) {
			$g.addClass("has-current is-open").children(".mhp-sub").prop("hidden", false);
			$g.children(".mhp-navbtn").attr("aria-expanded", "true");
		}
		if (crumb) $shell.find(".mhp-crumb").text(crumb);
	}

	// Page heading: { icon | image | initials, eyebrow, title, titleId, meta: [{icon, text, id}], actions: [{label, icon, primary, id, onClick}] }
	function head(spec) {
		const art = spec.image ? `<img src="${esc(spec.image)}" alt="" onerror="this.remove()">` : (spec.initials ? esc(spec.initials) : `<i class="fa-solid ${esc(spec.icon || "fa-user")}" aria-hidden="true"></i>`);
		const meta = (spec.meta || []).map((m) => `<span${m.id ? ` id="${esc(m.id)}"` : ""}><i class="fa-solid ${esc(m.icon)}" aria-hidden="true"></i><span class="mhp-meta-text">${esc(m.text)}</span></span>`).join("");
		const actions = (spec.actions || []).map((a) => `<button type="button" class="mhp-btn${a.primary ? " primary" : ""}"${a.id ? ` id="${esc(a.id)}"` : ""}>${a.icon ? `<i class="fa-solid ${esc(a.icon)}" aria-hidden="true"></i>` : ""}${esc(a.label)}</button>`).join("");
		const $head = $(`<header class="mhp-head">
			<div class="mhp-head-icon"${spec.iconId ? ` id="${esc(spec.iconId)}"` : ""}>${art}</div>
			<div class="mhp-head-text">
				<div class="mhp-eyebrow">${esc(spec.eyebrow || "")}</div>
				<h1${spec.titleId ? ` id="${esc(spec.titleId)}"` : ""}>${esc(spec.title || "")}</h1>
				${meta ? `<div class="mhp-meta">${meta}</div>` : ""}
			</div>
			${actions ? `<div class="mhp-head-actions">${actions}</div>` : ""}
		</header>`);
		(spec.actions || []).forEach((a, i) => { if (a.onClick) $head.find(".mhp-head-actions .mhp-btn").eq(i).on("click", a.onClick); });
		return $head;
	}

	// Collapsible notice under the heading: { icon, title, text, body (html), tone: "warn" }
	function banner(spec) {
		const $b = $(`<section class="mhp-banner${spec.tone ? " " + esc(spec.tone) : ""}">
			<button type="button" class="mhp-banner-top" aria-expanded="false">
				<span class="mhp-banner-icon"><i class="fa-solid ${esc(spec.icon || "fa-circle-info")}" aria-hidden="true"></i></span>
				<span class="mhp-banner-text"><b>${esc(spec.title)}</b>${spec.text ? `<span>${esc(spec.text)}</span>` : ""}</span>
				${spec.body ? '<i class="fa-solid fa-chevron-down mhp-chev" aria-hidden="true"></i>' : ""}
			</button>
			${spec.body ? `<div class="mhp-banner-body" hidden>${spec.body}</div>` : ""}
		</section>`);
		$b.find(".mhp-banner-top").on("click", function () {
			if (!spec.body) return;
			const open = !$b.hasClass("is-open");
			$b.toggleClass("is-open", open).find(".mhp-banner-body").prop("hidden", !open);
			$(this).attr("aria-expanded", String(open));
		});
		return $b;
	}

	function sectionHead(icon, title, sub) {
		return `<h2 class="mhp-section-title"><i class="fa-solid ${esc(icon)}" aria-hidden="true"></i>${esc(title)}</h2>${sub ? `<p class="mhp-section-sub">${esc(sub)}</p>` : ""}`;
	}

	// One stat card: value element id, label, note, chip icon and tone (teal / amber / violet / rose / sky).
	function stat(s) {
		return `<div class="mhp-stat"><span class="mhp-chip${s.tone ? " " + esc(s.tone) : ""}"><i class="fa-solid ${esc(s.icon)}" aria-hidden="true"></i></span>
			<strong class="mhp-stat-value" id="${esc(s.id)}">${esc(s.value == null ? "0" : s.value)}</strong>
			<span class="mhp-stat-label">${esc(s.label)}</span>${s.note ? `<span class="mhp-stat-note"${s.noteId ? ` id="${esc(s.noteId)}"` : ""}>${esc(s.note)}</span>` : ""}</div>`;
	}

	$(document).on("page-change", syncBodyClass);

	window.MhPortal = { mount, setActive, head, banner, sectionHead, stat, on, runPending, isHr, isEmployee };
})();
