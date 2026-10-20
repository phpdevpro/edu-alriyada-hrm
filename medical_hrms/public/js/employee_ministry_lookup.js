hide_ministry_code_docnames_in_links();

frappe.ui.form.on("Employee", {
	setup(frm) {
		const employee_fields = {
			gender: "Gender",
			custom_identity_type: "Identity type",
			custom_identity_issue_place: "Coding cities and governora",
			custom_ministry_place_of_birth: "Coding cities and governora",
			custom_jameah_nationality: "Nationality",
			custom_ministry_special_needs_type: "Type of special needs",
			custom_ministry_religion: "Religions",
			custom_ministry_work_city: "Coding cities and governora",
			custom_ministry_job_rank: "Job ranks",
			custom_ministry_accommodation: "Residential status coding",
		};

		Object.entries(employee_fields).forEach(([fieldname, category]) => {
			frm.set_query(fieldname, () => ministry_code_query(category));
		});

		const education_fields = {
			custom_ministry_scientific_degree: "Coding of academic degrees",
			custom_ministry_major: "Specialization Coding Guide",
			custom_ministry_minor: "Specialization Coding Guide",
			custom_ministry_assessment_type: "Cumulative GPA",
			custom_ministry_gpa_type: "Cumulative GPA",
			custom_ministry_study_type: "Study type coding",
			custom_ministry_graduate_from: "Coding of educational insti",
			custom_ministry_faculty: "College Coding Guide",
			custom_ministry_city: "Coding cities and governora",
			custom_ministry_country: "Nationality",
		};

		if (frm.fields_dict.education?.grid) {
			Object.entries(education_fields).forEach(([fieldname, category]) => {
				const grid_field = frm.fields_dict.education.grid.get_field(fieldname);
				if (grid_field) {
					grid_field.get_query = () => ministry_code_query(category);
				}
			});
		}

		const work_experience_fields = {
			employment_status: "Job status",
			institute: "Coding of educational insti",
			location: "Coding cities and governora",
			academic_department: "Coding academic departments",
			profession_rank: "Academic ranks",
			accommodation: "Residential status coding",
			city: "Coding cities and governora",
			country: "Nationality",
		};

		if (frm.fields_dict.custom_jameah_experience?.grid) {
			Object.entries(work_experience_fields).forEach(([fieldname, category]) => {
				const grid_field = frm.fields_dict.custom_jameah_experience.grid.get_field(fieldname);
				if (grid_field) {
					grid_field.get_query = () => ministry_code_query(category);
				}
			});
		}

		const training_fields = {
			city: "Coding cities and governora",
			country: "Nationality",
		};

		if (frm.fields_dict.custom_jameah_training?.grid) {
			Object.entries(training_fields).forEach(([fieldname, category]) => {
				const grid_field = frm.fields_dict.custom_jameah_training.grid.get_field(fieldname);
				if (grid_field) {
					grid_field.get_query = () => ministry_code_query(category);
				}
			});
		}
	},

	refresh(frm) {
		toggle_special_needs_type(frm);
		toggle_identity_numbers(frm);
		if (!frm.is_new() && ["HR Manager", "HR User", "System Manager"].some((r) => frappe.user.has_role(r))) {
			frm.add_custom_button(__("Ministry (Jameah) Data"), () => show_ministry_rows(frm), __("View"));
		}
	},

	custom_is_special_needs(frm) {
		toggle_special_needs_type(frm);
	},

	custom_jameah_nationality(frm) {
		toggle_identity_numbers(frm);
	},
});

function ministry_code_query(category) {
	return {
		query: "medical_hrms.ministry_lookup_query.get_ministry_codes",
		filters: {
			code_category: category,
		},
	};
}

function toggle_special_needs_type(frm) {
	const has_special_needs = Boolean(frm.doc.custom_is_special_needs);

	frm.set_df_property("custom_ministry_special_needs_type", "hidden", !has_special_needs);
	frm.set_df_property("custom_ministry_special_needs_type", "reqd", has_special_needs);

	if (!has_special_needs && frm.doc.custom_ministry_special_needs_type) {
		frm.set_value("custom_ministry_special_needs_type", "");
	}
}

function toggle_identity_numbers(frm) {
	const local_id_field = "custom_identity_number";
	const home_country_id_field = "custom_original_home_id_number";
	const nationality = frm.doc.custom_jameah_nationality;

	if (!nationality) {
		set_identity_number_state(frm, local_id_field, false, false);
		set_identity_number_state(frm, home_country_id_field, false, false);
		return;
	}

	frappe.db.get_value(
		"Jameah Ministry Code",
		nationality,
		["ministry_code", "name_english"],
		(message) => {
			const is_saudi = message?.ministry_code === "101" || message?.name_english === "Saudi Arabia";

			set_identity_number_state(frm, local_id_field, is_saudi, is_saudi);
			set_identity_number_state(frm, home_country_id_field, !is_saudi, !is_saudi);
		}
	);
}

function set_identity_number_state(frm, fieldname, show, required) {
	frm.set_df_property(fieldname, "hidden", !show);
	frm.set_df_property(fieldname, "reqd", required);

	if (!show && frm.doc[fieldname]) {
		frm.set_value(fieldname, "");
	}
}

function hide_ministry_code_docnames_in_links() {
	if (frappe.ui.form.ControlLink.prototype._ministry_code_docnames_hidden) {
		return;
	}

	const original_merge_duplicates = frappe.ui.form.ControlLink.prototype.merge_duplicates;

	frappe.ui.form.ControlLink.prototype.merge_duplicates = function (results) {
		const merged_results = original_merge_duplicates.call(this, results);

		if (this.get_options() !== "Jameah Ministry Code") {
			return merged_results;
		}

		return merged_results.map((result) => {
			if (result.value && result.label) {
				result.description = "";
			}
			return result;
		});
	};

	frappe.ui.form.ControlLink.prototype._ministry_code_docnames_hidden = true;
}

// What the Ministry views send for this employee, section by section.
function show_ministry_rows(frm) {
	frappe.call({
		method: "medical_hrms.jameah.status.employee_view_rows",
		args: { employee: frm.doc.name },
		freeze: true,
	}).then((r) => {
		const data = r.message || {};
		const esc = frappe.utils.escape_html;
		let html = "";
		if (data.excluded_reason) {
			html = `<p class="text-muted">${esc(data.excluded_reason)}</p>`;
		} else {
			for (const [view, rows] of Object.entries(data.views || {})) {
				html += `<h5 style="margin-top:14px"><code>${esc(view)}</code> (${rows.length})</h5>`;
				if (!rows.length) {
					html += `<p class="text-muted">${__("No rows.")}</p>`;
					continue;
				}
				const cols = Object.keys(rows[0]);
				html += `<div style="overflow-x:auto"><table class="table table-bordered table-sm" style="font-size:12px"><thead><tr>${cols
					.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${cols
					.map((c) => `<td>${row[c] === null ? '<span class="text-muted">—</span>' : esc(String(row[c]))}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
			}
			html = `<p class="text-muted">${__("Empty cells are sent to the Ministry as empty. Lookup columns carry the Ministry code.")}</p>` + html;
		}
		new frappe.ui.Dialog({ title: __("Ministry (Jameah) Data"), size: "extra-large", fields: [{ fieldtype: "HTML", options: html }] }).show();
	});
}
