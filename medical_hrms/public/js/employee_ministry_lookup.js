<<<<<<< HEAD

=======
>>>>>>> 31a5d95401dd98673b8dda7840d4f2a7600b47d9
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

<<<<<<< HEAD
		const academic_qualification_fields = {
			degree: "Coding of academic degrees",
			specialization: "Specialization Coding Guide",
			minor: "Specialization Coding Guide",
			assessment_type: "Cumulative GPA",
			gpa_type: "Cumulative GPA",
			study_type: "Study type coding",
			institute: "Coding of educational insti",
			faculty: "College Coding Guide",
=======
		const work_experience_fields = {
>>>>>>> 31a5d95401dd98673b8dda7840d4f2a7600b47d9
			city: "Coding cities and governora",
			country: "Nationality",
		};

<<<<<<< HEAD
		if (frm.fields_dict.custom_jameah_qualifications?.grid) {
			Object.entries(academic_qualification_fields).forEach(([fieldname, category]) => {
				const grid_field = frm.fields_dict.custom_jameah_qualifications.grid.get_field(fieldname);
				if (grid_field) {
					grid_field.get_query = () => ministry_code_query(category);
				}
			});
		}

		const work_experience_fields = {
			is_latest_work_experience_record: "",
			current_academic_year_date: "",
			employment_status_code: "Job status",
			profession: "",
			institute_code: "Coding of educational insti",
			location_code: "Coding cities and governora",
			section_code: "Coding academic departments",
			employee_number: "",
			profession_rank_code: "Job ranks",
			hiring_date: "",
			start_working_date: "",
			end_working_date: "",
			functional_tasks: "",
			accommodation_code: "Residential status coding",
		};

		if (frm.fields_dict.custom_jameah_experience?.grid) {
			Object.entries(work_experience_fields).forEach(([fieldname, category]) => {
				if (!category) {
					return;
				}
=======
		if (frm.fields_dict.custom_jameah_experience?.grid) {
			Object.entries(work_experience_fields).forEach(([fieldname, category]) => {
>>>>>>> 31a5d95401dd98673b8dda7840d4f2a7600b47d9
				const grid_field = frm.fields_dict.custom_jameah_experience.grid.get_field(fieldname);
				if (grid_field) {
					grid_field.get_query = () => ministry_code_query(category);
				}
			});
		}

<<<<<<< HEAD
		const previous_work_experience_fields = {
=======
		const training_fields = {
>>>>>>> 31a5d95401dd98673b8dda7840d4f2a7600b47d9
			city: "Coding cities and governora",
			country: "Nationality",
		};

<<<<<<< HEAD
		if (frm.fields_dict.custom_jameah_previous_experience?.grid) {
			Object.entries(previous_work_experience_fields).forEach(([fieldname, category]) => {
				const grid_field = frm.fields_dict.custom_jameah_previous_experience.grid.get_field(fieldname);
				if (grid_field) {
					grid_field.get_query = () => ministry_code_query(category);
				}
			});
		}

		const training_fields = {
			course_city: "Coding cities and governora",
			course_country: "Nationality",
		};

=======
>>>>>>> 31a5d95401dd98673b8dda7840d4f2a7600b47d9
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
