(() => {
const METHOD = "medical_hrms.medical_hrms.page.hr_academic_presence.hr_academic_presence.";
const esc = (value) => frappe.utils.escape_html(String(value ?? ""));

// One tab per HR requirement; the route segment opens a tab directly,
// e.g. /app/hr-academic-presence/students (used by the HR dashboard cards).
const TABS = {
	faculty: {
		label: __("Faculty Schedules"),
		hint: __("Every teaching session by faculty member, from the published class timetables."),
		filters: "range-instructor",
		method: "get_faculty_schedule",
		columns: [["date", __("Date")], ["day", __("Day")], ["time", __("Time")], ["instructor_name", __("Faculty Member")],
			["course", __("Course")], ["class_name", __("Class")], ["class_type", __("Type")], ["room", __("Room")], ["mode", __("Mode")]],
		stats: (s) => [[s.sessions, __("Sessions")], [s.instructors, __("Faculty Members")], [s.teaching_hours, __("Teaching Hours")], [s.on_campus_sessions, __("On-campus Sessions")]],
		empty: __("No teaching sessions in this period."),
	},
	proctors: {
		label: __("Proctor Schedules"),
		hint: __("Exam supervision assignments from Exam Committees."),
		filters: "range",
		method: "get_proctor_schedule",
		columns: [["date", __("Date")], ["time", __("Time")], ["proctor_name", __("Proctor")], ["proctor_email", __("Email")],
			["exam", __("Exam")], ["exam_type", __("Exam Type")], ["room", __("Room")], ["committee", __("Committee")]],
		stats: (s) => [[s.assignments, __("Assignments")], [s.proctors, __("Proctors")], [s.committees, __("Exam Committees")]],
		empty: __("No proctoring assignments in this period. Proctors appear here once exams and exam committees are set up."),
	},
	students: {
		label: __("Students on Campus"),
		hint: __("Students per hour in on-campus classes. Present and absent come from recorded attendance; \"not recorded\" means attendance wasn't taken yet."),
		filters: "date",
		method: "get_students_presence",
		columns: [["slot", __("Hour")], ["sessions", __("Classes")], ["expected", __("Expected")], ["present", __("Present")],
			["absent", __("Absent")], ["not_recorded", __("Not Recorded")], ["attendance_rate", __("Attendance %")]],
		rows: (r) => r.slots,
		stats: (s) => [[s.in_person_sessions, __("On-campus Classes")], [s.students_expected, __("Students Expected")], [s.students_present, __("Students Present")], [s.busiest_slot || "—", __("Busiest Hour")]],
		empty: __("No on-campus classes on this date."),
	},
	after_hours: {
		label: __("Faculty After 4 PM"),
		hint: __("Faculty on campus after the cut-off time each day (HR Settings, default 4:00 PM). Attendance-device logs are used when available; otherwise in-person teaching or proctoring, confirmed when class attendance was recorded."),
		filters: "range",
		method: "get_faculty_after_hours",
		columns: [["date", __("Date")], ["name", __("Faculty Member")], ["email", __("Email")], ["until", __("On Campus Until")],
			["activities", __("Activities")], ["status", __("Status")], ["source", __("Evidence")]],
		stats: (s) => [[s.people, __("Faculty Members")], [s.person_days, __("Person-days")], [s.busiest_day ? frappe.datetime.str_to_user(s.busiest_day) : "—", __("Busiest Day")]],
		empty: __("No faculty on campus after 4 PM in this period."),
	},
};

frappe.pages["hr-academic-presence"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("Academic Schedules & Presence"), single_column: true });
	MhPortal.mount(page, { portal: "hr", active: "presence-faculty", crumb: TABS.faculty.label });
	wrapper.presence = new AcademicPresence(page);
};

frappe.pages["hr-academic-presence"].on_page_show = function (wrapper) {
	const tab = frappe.get_route()[1];
	wrapper.presence && wrapper.presence.show(TABS[tab] ? tab : wrapper.presence.tab || "faculty");
};

class AcademicPresence {
	constructor(page) {
		this.page = page;
		$(page.body).html(`
			<style>
				.mhap-tabs { display:flex; flex-wrap:wrap; gap:8px; margin:0 0 14px; }
				.mhap-tab { all:unset; cursor:pointer; border:1px solid var(--line); background:var(--surface); color:var(--text-secondary); border-radius:999px; padding:9px 18px; font-weight:600; font-size:14px; }
				.mhap-tab:hover { border-color:var(--primary); color:var(--primary); }
				.mhap-tab:focus-visible { outline:2px solid var(--primary); outline-offset:2px; }
				.mhap-tab.active { background:var(--primary); color:#fff; border-color:var(--primary); }
				[data-theme="dark"] .mhap-tab.active { color:#04201c; }
				.mhap-hint { color:var(--text-secondary); margin:0 0 16px; font-size:15px; max-width:90ch; }
				.mhap-filters { display:flex; flex-wrap:wrap; gap:14px; align-items:flex-end; margin-bottom:20px; padding:16px 18px 6px; }
				.mhap-filters .frappe-control { margin-bottom:10px; min-width:200px; }
				.mhap-stats { margin-bottom:22px; }
				.mhap-table th { position:sticky; top:0; }
				.mhap-empty { padding:30px; text-align:center; color:var(--text-tertiary); background:var(--surface); }
				.mhap-extra { display:flex; flex-direction:column; gap:10px; margin-top:16px; }
				.mhap-note { color:var(--amber-fg); background:var(--amber-bg); border-radius:12px; padding:11px 14px; font-size:13.5px; }
				.mhap-bar { display:inline-block; height:8px; border-radius:4px; background:var(--accent); vertical-align:middle; margin-inline-end:6px; }
			</style>
			<div class="mhap-head"></div>
			<div class="mhap-tabs" role="tablist"></div>
			<p class="mhap-hint"></p>
			<div class="mhap-filters mhp-card"></div>
			<div class="mhap-stats mhp-stats"></div>
			<div class="mhap-table-wrap mhp-tablewrap"></div>
			<div class="mhap-extra"></div>
		`);
		this.$ = (selector) => $(page.body).find(selector);
		this.$(".mhap-tabs").html(Object.entries(TABS).map(([key, tab]) =>
			`<button class="mhap-tab" data-tab="${key}">${esc(tab.label)}</button>`).join(""));
		this.$(".mhap-tabs").on("click", ".mhap-tab", (e) => frappe.set_route("hr-academic-presence", $(e.currentTarget).data("tab")));
		this.$(".mhap-head").replaceWith(MhPortal.head({
			icon: "fa-chalkboard-user", eyebrow: __("HR Portal"), title: __("Academic Schedules & Presence"),
			meta: [{ icon: "fa-circle-info", text: __("From the published class timetables, exam committees and recorded attendance") }],
			actions: [
				{ label: __("Refresh"), icon: "fa-rotate", id: "mhap-refresh", onClick: () => this.load() },
				{ label: __("Export (Excel CSV)"), icon: "fa-download", id: "mhap-export", primary: true, onClick: () => this.export() },
			],
		}));
	}

	show(tab) {
		this.tab = tab;
		MhPortal.setActive(this.page, `presence-${tab}`, TABS[tab].label);
		this.$(".mhap-tab").removeClass("active").attr("aria-selected", "false").filter(`[data-tab="${tab}"]`).addClass("active").attr("aria-selected", "true");
		this.$(".mhap-hint").text(TABS[tab].hint);
		this.render_filters();
		this.load();
	}

	render_filters() {
		const $filters = this.$(".mhap-filters").empty();
		const kind = TABS[this.tab].filters;
		const today = frappe.datetime.get_today();
		const make = (df) => {
			const control = frappe.ui.form.make_control({ parent: $("<div>").appendTo($filters), df: { ...df, change: () => this.load() }, render_input: true });
			control.set_value(df.default || "");
			return control;
		};
		this.controls = {};
		if (kind === "date") {
			this.controls.on_date = make({ fieldtype: "Date", fieldname: "on_date", label: __("Date"), default: today });
		} else {
			this.controls.from_date = make({ fieldtype: "Date", fieldname: "from_date", label: __("From Date"), default: frappe.datetime.week_start() });
			this.controls.to_date = make({ fieldtype: "Date", fieldname: "to_date", label: __("To Date"), default: frappe.datetime.week_end() });
		}
		if (kind === "range-instructor") {
			this.controls.instructor = make({ fieldtype: "Link", fieldname: "instructor", label: __("Faculty Member"), options: "Instructor" });
		}
	}

	args() {
		const values = {};
		Object.entries(this.controls || {}).forEach(([key, control]) => { values[key] = control.get_value() || undefined; });
		return values;
	}

	load() {
		const tab = TABS[this.tab];
		const requested = this.tab;
		this.$(".mhap-table-wrap").html(`<div class="mhap-empty">${__("Loading…")}</div>`);
		frappe.call({ method: METHOD + tab.method, args: this.args(), callback: (r) => {
			if (requested !== this.tab) return; // the user switched tabs meanwhile
			this.data = r.message || {};
			this.render();
		}});
	}

	rows() {
		const tab = TABS[this.tab];
		return (tab.rows ? tab.rows(this.data) : this.data.rows) || [];
	}

	render() {
		const tab = TABS[this.tab];
		const chips = [["fa-calendar-days", ""], ["fa-users", "sky"], ["fa-clock", "amber"], ["fa-building", "violet"]];
		this.$(".mhap-stats").html(tab.stats(this.data.summary || {}).map(([value, label], i) =>
			`<div class="mhp-stat"><span class="mhp-chip ${chips[i % 4][1]}"><i class="fa-solid ${chips[i % 4][0]}" aria-hidden="true"></i></span>
				<strong class="mhp-stat-value">${esc(value ?? 0)}</strong><span class="mhp-stat-label">${esc(label)}</span></div>`).join(""));
		const rows = this.rows();
		if (!rows.length) {
			this.$(".mhap-table-wrap").html(`<div class="mhap-empty">${esc(tab.empty)}</div>`);
		} else {
			const max_present = Math.max(1, ...rows.map((row) => row.present || 0));
			const cell = (key, row) => {
				let value = row[key];
				if (key === "date") value = frappe.datetime.str_to_user(value);
				if (key === "attendance_rate") value = value === null || value === undefined ? "—" : `${value}%`;
				if (key === "present" && this.tab === "students") {
					return `<span class="mhap-bar" style="width:${Math.round(80 * (row.present || 0) / max_present)}px"></span>${esc(value)}`;
				}
				return esc(value);
			};
			this.$(".mhap-table-wrap").html(`<table class="mhp-table mhap-table">
				<thead><tr>${tab.columns.map(([, label]) => `<th>${esc(label)}</th>`).join("")}</tr></thead>
				<tbody>${rows.map((row) => `<tr>${tab.columns.map(([key]) => `<td>${cell(key, row)}</td>`).join("")}</tr>`).join("")}</tbody>
			</table>`);
		}
		const notes = [];
		const outside = this.data.outside_hours || [];
		if (outside.length) {
			notes.push(esc(__("{0} class session(s) fall outside 07:00–22:00 and are not shown in the hourly table (check the timetable): ", [outside.length])) + outside.map((s) => esc(`${s.class_name} ${s.time}`)).join(", "));
		}
		const days_off = this.data.days_off || [];
		if (days_off.length) {
			notes.push(esc(__("No regular classes on: ")) + days_off.map((d) => esc(`${frappe.datetime.str_to_user(d.date)} (${d.reason})`)).join(", "));
		}
		if (this.data.holiday_list_missing) {
			notes.push(esc(__("No Academic Holiday List is set, so official holidays are not excluded. Set it in HR Settings > Academic Schedules & Presence.")));
		}
		if (this.tab === "after_hours") {
			notes.push(esc(__("Cut-off time: {0}. Change it in HR Settings > Academic Schedules & Presence.", [this.data.cutoff])));
			if (!this.data.devices_connected) {
				notes.push(esc(__("No attendance-device logs in this period, so times come from the timetable and class attendance. Once devices are connected, actual check-out times are used automatically.")));
			}
		}
		this.$(".mhap-extra").html(notes.map((note) => `<div class="mhap-note">${note}</div>`).join(""));
	}

	export() {
		const tab = TABS[this.tab];
		const rows = this.rows();
		if (!rows.length) {
			frappe.msgprint(__("Nothing to export for this period."));
			return;
		}
		const data = [tab.columns.map(([, label]) => label), ...rows.map((row) => tab.columns.map(([key]) => row[key] ?? ""))];
		const stamp = frappe.datetime.now_datetime().replace(/[: ]/g, "-").slice(0, 16);
		frappe.tools.downloadify(data, null, `${stamp}_${tab.label.replace(/\W+/g, "-")}`);
	}
}
})();
