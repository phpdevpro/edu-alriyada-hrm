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
	},

	custom_is_special_needs(frm) {
		toggle_special_needs_type(frm, true);
	},

	custom_jameah_nationality(frm) {
		toggle_identity_numbers(frm, true);
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

// Values only change when the user changes the controlling field (clear = true);
// opening a record must not mark it "Not Saved". The server clears values that
// do not apply on save (ministry_lookup_validation.clear_values_that_do_not_apply).
function toggle_special_needs_type(frm, clear) {
	const has_special_needs = Boolean(frm.doc.custom_is_special_needs);

	frm.set_df_property("custom_ministry_special_needs_type", "hidden", !has_special_needs);
	frm.set_df_property("custom_ministry_special_needs_type", "reqd", has_special_needs);

	if (clear && !has_special_needs && frm.doc.custom_ministry_special_needs_type) {
		frm.set_value("custom_ministry_special_needs_type", "");
	}
}

// Ministry rule (see identity_problems): the Kingdom identity number - National ID
// for Saudis, Iqama for residents - is mandatory for everyone; the home-country ID
// is optional and only applies to non-Saudis.
function toggle_identity_numbers(frm, clear) {
	const home_country_id_field = "custom_original_home_id_number";
	const nationality = frm.doc.custom_jameah_nationality;

	frm.set_df_property("custom_identity_number", "hidden", false);
	frm.set_df_property("custom_identity_number", "reqd", true);

	if (!nationality) {
		set_identity_number_state(frm, home_country_id_field, false, clear);
		return;
	}

	frappe.db.get_value(
		"Jameah Ministry Code",
		nationality,
		["ministry_code", "name_english"],
		(message) => {
			const is_saudi = message?.ministry_code === "101" || message?.name_english === "Saudi Arabia";

			set_identity_number_state(frm, home_country_id_field, !is_saudi, clear);
		}
	);
}

function set_identity_number_state(frm, fieldname, show, clear) {
	frm.set_df_property(fieldname, "hidden", !show);
	frm.set_df_property(fieldname, "reqd", false);

	if (clear && !show && frm.doc[fieldname]) {
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
