(function () {
	console.log("job_application.js loaded");
	const config = window.jobApplicationConfig || {};
	const form = document.getElementById("job-application-form");
	if (!form) {
		console.error("Job application form not found");
		return;
	}
	console.log("Job application form found");

	const alertBox = document.getElementById("job-application-alert");
	const categorySelect = document.getElementById("application-category");
	const categoryBadge = document.getElementById("application-category-badge");
	const submitButton = document.getElementById("job-application-submit");
	const isAdminPreview = Boolean(config.allow_category_override);

	let currentCategory = config.application_category || "Academic Staff";
	if (categorySelect) {
		categorySelect.value = currentCategory;
		categorySelect.disabled = !isAdminPreview;
		categorySelect.addEventListener("change", (event) => {
			currentCategory = event.target.value || currentCategory;
			applyCategoryRules();
		});
	}

	if (categoryBadge) {
		categoryBadge.textContent = currentCategory;
	}

	const tableDefinitions = {
		education: {
			label: "Education Qualifications",
			columns: [
				{ name: "school_univ", label: "School/University", type: "text" },
				{ name: "qualification", label: "Qualification", type: "text" },
				{
					name: "level",
					label: "Level",
					type: "select",
					options: ["Graduate", "Post Graduate", "Under Graduate"],
				},
				{ name: "year_of_passing", label: "Year", type: "number" },
				{ name: "class_per", label: "Class / %", type: "text" },
				{ name: "maj_opt_subj", label: "Major / Optional", type: "text" },
			],
		},
		work_experience: {
			label: "Work Experience",
			columns: [
				{ name: "company_name", label: "Company", type: "text" },
				{ name: "designation", label: "Designation", type: "text" },
				{ name: "total_experience", label: "Total Experience", type: "text" },
				{ name: "salary", label: "Salary", type: "number" },
				{ name: "address", label: "Address", type: "text" },
				{ name: "contact", label: "Contact", type: "text" },
			],
		},
		skills: {
			label: "Skills",
			columns: [
				{ name: "skill_name", label: "Skill", type: "text" },
				{
					name: "proficiency",
					label: "Proficiency",
					type: "select",
					options: ["Beginner", "Intermediate", "Advanced", "Expert"],
				},
				{ name: "years_of_experience", label: "Years", type: "number" },
			],
		},
		training_courses: {
			label: "Training Courses",
			columns: [
				{ name: "course_name", label: "Course Name", type: "text" },
				{ name: "provider", label: "Provider", type: "text" },
				{ name: "completion_date", label: "Completion Date", type: "date" },
				{ name: "duration", label: "Duration", type: "text" },
			],
		},
		academic_certifications: {
			label: "Academic Certifications",
			columns: [
				{ name: "certification_name", label: "Certification", type: "text" },
				{ name: "issuing_body", label: "Issuing Body", type: "text" },
				{ name: "issue_date", label: "Issue Date", type: "date" },
				{ name: "expiry_date", label: "Expiry Date", type: "date" },
				{ name: "certificate_id", label: "Certificate ID", type: "text" },
			],
		},
		teaching_experience: {
			label: "Teaching Experience",
			columns: [
				{ name: "institution", label: "Institution", type: "text" },
				{ name: "designation", label: "Designation", type: "text" },
				{ name: "subject_area", label: "Subject Area", type: "text" },
				{ name: "start_date", label: "Start Date", type: "date" },
				{ name: "end_date", label: "End Date", type: "date" },
				{ name: "years", label: "Years", type: "number" },
			],
		},
		research_publications: {
			label: "Research Publications",
			columns: [
				{ name: "title", label: "Title", type: "text" },
				{ name: "journal", label: "Journal", type: "text" },
				{ name: "publication_date", label: "Publication Date", type: "date" },
				{ name: "link", label: "Link / DOI", type: "text" },
			],
		},
		professional_memberships: {
			label: "Professional Memberships",
			columns: [
				{ name: "organization", label: "Organization", type: "text" },
				{ name: "membership_id", label: "Membership ID", type: "text" },
				{ name: "start_date", label: "Start Date", type: "date" },
				{ name: "end_date", label: "End Date", type: "date" },
				{ name: "status", label: "Status", type: "text" },
			],
		},
		awards: {
			label: "Awards",
			columns: [
				{ name: "award_name", label: "Award Name", type: "text" },
				{ name: "organization", label: "Organization", type: "text" },
				{ name: "award_date", label: "Award Date", type: "date" },
				{ name: "details", label: "Details", type: "text" },
			],
		},
		academic_qualifications: {
			label: "Employee Academic Qualifications",
			columns: [
				{ name: "latest_record", label: "Latest Record", type: "checkbox" },
				{ name: "academic_qualification", label: "Academic Qualification", type: "text" },
				{ name: "general_specialization_main", label: "General Specialization (Main)", type: "text" },
				{ name: "subspecialty", label: "Subspecialty", type: "text" },
				{ name: "appreciation", label: "Appreciation", type: "text" },
				{ name: "graduation_rate", label: "Graduation Rate", type: "text" },
				{ name: "rate_type", label: "Rate Type", type: "text" },
				{ name: "study_system", label: "Study System", type: "text" },
				{ name: "graduation_place", label: "Graduation Place", type: "text" },
				{ name: "college", label: "College", type: "text" },
				{ name: "qualification_date", label: "Date of Obtaining the Qualification", type: "date" },
				{ name: "graduation_year_ad", label: "Graduation Year AD", type: "number" },
				{ name: "city", label: "City", type: "text" },
				{ name: "country", label: "Country", type: "text" },
			],
		},
		academic_experience: {
			label: "Employee Academic Experience",
			columns: [
				{ name: "school_year_history", label: "School Year History", type: "text" },
				{ name: "employee_job_status", label: "Employee Job Status", type: "text" },
				{ name: "job_title", label: "Job Title", type: "text" },
				{ name: "educational_entity", label: "Educational Entity", type: "text" },
				{ name: "geographical_work_location", label: "Geographical Work Location", type: "text" },
				{ name: "academic_department", label: "Academic Department", type: "text" },
				{ name: "job_number", label: "Job Number", type: "text" },
				{ name: "job_rank", label: "Job Rank", type: "text" },
				{ name: "date_of_appointment_to_the_rank", label: "Date of Appointment to the Rank", type: "date" },
				{ name: "start_date", label: "Start Date", type: "date" },
				{ name: "end_of_work_date", label: "End of Work Date", type: "date" },
				{ name: "job_duties", label: "Job Duties", type: "textarea" },
				{ name: "housing", label: "Housing", type: "text" },
			],
		},
		previous_experience: {
			label: "Employee Previous Experience",
			columns: [
				{ name: "job_title", label: "Job Title", type: "text" },
				{ name: "institution_or_company", label: "Name of Educational Institution / Company", type: "text" },
				{ name: "city", label: "City", type: "text" },
				{ name: "country", label: "Country", type: "text" },
				{ name: "college_administration", label: "College / Administration", type: "text" },
				{ name: "section", label: "Section", type: "text" },
				{ name: "start_date", label: "Start Date", type: "date" },
				{ name: "end_of_work_date", label: "End of Work Date", type: "date" },
				{ name: "job_duties", label: "Job Duties", type: "textarea" },
			],
		},
		professional_certificates_training: {
			label: "Employee Professional Certificates & Training Courses",
			columns: [
				{ name: "course_name", label: "Course Name", type: "text" },
				{ name: "certificate_type", label: "Type", type: "text" },
				{ name: "issuing_authority", label: "Issuing Authority", type: "text" },
				{ name: "course_history", label: "Course History", type: "text" },
				{ name: "course_duration", label: "Course Duration", type: "text" },
				{ name: "city", label: "City", type: "text" },
				{ name: "country", label: "Country", type: "text" },
			],
		},
	};

	function renderTables() {
		Object.keys(tableDefinitions).forEach((tableName) => {
			const table = document.querySelector(`table[data-table='${tableName}']`);
			if (!table) {
				return;
			}

			const thead = table.querySelector("thead tr");
			const tbody = table.querySelector("tbody");
			const defn = tableDefinitions[tableName];

			if (thead && thead.children.length === 0) {
				defn.columns.forEach((column) => {
					const th = document.createElement("th");
					th.textContent = column.label;
					thead.appendChild(th);
				});
				const th = document.createElement("th");
				th.textContent = "";
				thead.appendChild(th);
			}

			// Only auto-add row for Academic Qualifications (the only required new table)
			if (tableName === "academic_qualifications" && tbody && tbody.children.length === 0) {
				addRow(tableName);
			}
		});
	}

	function addRow(tableName) {
		console.log("addRow function called for:", tableName);
		const table = document.querySelector(`table[data-table='${tableName}']`);
		console.log("Table query result:", table);
		if (!table) {
			console.error("Table element not found for:", tableName);
			return;
		}
		console.log("Table element found, tagName:", table.tagName);

		const defn = tableDefinitions[tableName];
		let tbody = table.querySelector("tbody");
		
		// If tbody doesn't exist, create it
		if (!tbody) {
			console.log("Tbody not found, creating one...");
			tbody = document.createElement("tbody");
			table.appendChild(tbody);
		}
		console.log("Tbody ready");

		const row = document.createElement("tr");
		console.log("Creating row for:", tableName);

		defn.columns.forEach((column) => {
			const cell = document.createElement("td");
			const input = buildInput(column);
			cell.appendChild(input);
			row.appendChild(cell);
		});

		const actionCell = document.createElement("td");
		const removeButton = document.createElement("button");
		removeButton.type = "button";
		removeButton.className = "ja-remove-row";
		removeButton.textContent = "Remove";
		actionCell.appendChild(removeButton);
		row.appendChild(actionCell);

		tbody.appendChild(row);
		console.log("Row added successfully to:", tableName);
	}

	function buildInput(column) {
		let input;
		if (column.type === "select") {
			input = document.createElement("select");
			const blankOption = document.createElement("option");
			blankOption.value = "";
			blankOption.textContent = "--";
			input.appendChild(blankOption);
			(column.options || []).forEach((option) => {
				const opt = document.createElement("option");
				opt.value = option;
				opt.textContent = option;
				input.appendChild(opt);
			});
		} else {
			if (column.type === "textarea") {
				input = document.createElement("textarea");
			} else {
				input = document.createElement("input");
				input.type = column.type === "number" ? "number" : column.type === "date" ? "date" : column.type === "checkbox" ? "checkbox" : "text";
			}
		}
		input.dataset.field = column.name;
		return input;
	}

	function collectTableRows(tableName) {
		const table = document.querySelector(`table[data-table='${tableName}']`);
		if (!table) {
			return [];
		}

		const rows = [];
		table.querySelectorAll("tbody tr").forEach((row) => {
			const rowData = {};
			row.querySelectorAll("[data-field]").forEach((input) => {
				const value = input.type === "checkbox" ? input.checked : input.value ? input.value.trim() : "";
				if (value !== "" && value !== false && value !== null && value !== undefined) {
					rowData[input.dataset.field] = value;
				}
			});
			if (Object.keys(rowData).length) {
				rows.push(rowData);
			}
		});

		return rows;
	}

	function applyCategoryRules() {
		if (categoryBadge) {
			categoryBadge.textContent = currentCategory;
		}

		renderTables();
	}

	function showError(message) {
		if (!alertBox) {
			return;
		}
		alertBox.textContent = message;
		alertBox.style.display = "block";
		alertBox.scrollIntoView({ behavior: "smooth", block: "center" });
	}

	function clearError() {
		if (!alertBox) {
			return;
		}
		alertBox.textContent = "";
		alertBox.style.display = "none";
	}

	function validateForm(payload, tables) {
		const requiredFields = ["full_name", "email", "phone", "designation", "department"];
		const missing = requiredFields.filter((field) => !payload[field]);
		if (missing.length) {
			return "Please fill all required fields before submitting.";
		}

		// Only Academic Qualifications is required
		if ((tables.academic_qualifications || []).length === 0) {
			return "Please add at least one academic qualification.";
		}

		return "";
	}

	async function submitForm(event) {
		event.preventDefault();
		clearError();
		submitButton.disabled = true;

		const payload = {};
		// Only collect fields that are NOT inside table rows
		form.querySelectorAll("[data-field]").forEach((input) => {
			// Skip inputs that are inside table cells
			if (input.closest("table")) {
				return;
			}
			const value = input.value ? input.value.trim() : "";
			if (value) {
				payload[input.dataset.field] = value;
			}
		});

		payload.application_category = currentCategory;

		const tables = {
			education: collectTableRows("education"),
			work_experience: collectTableRows("work_experience"),
			skills: collectTableRows("skills"),
			training_courses: collectTableRows("training_courses"),
			academic_certifications: collectTableRows("academic_certifications"),
			teaching_experience: collectTableRows("teaching_experience"),
			research_publications: collectTableRows("research_publications"),
			professional_memberships: collectTableRows("professional_memberships"),
			awards: collectTableRows("awards"),
			academic_qualifications: collectTableRows("academic_qualifications"),
			academic_experience: collectTableRows("academic_experience"),
			previous_experience: collectTableRows("previous_experience"),
			professional_certificates_training: collectTableRows("professional_certificates_training"),
		};

		Object.assign(payload, tables);

		const error = validateForm(payload, tables);
		if (error) {
			submitButton.disabled = false;
			showError(error);
			return;
		}

		const formData = new FormData();
		formData.append("data", JSON.stringify(payload));

		if (config.token) {
			formData.append("token", config.token);
		}

		const resumeInput = document.getElementById("resume_file");
		if (resumeInput && resumeInput.files && resumeInput.files[0]) {
			formData.append("resume_file", resumeInput.files[0]);
		}

		try {
			const headers = {};
			if (window.frappe && frappe.csrf_token) {
				headers["X-Frappe-CSRF-Token"] = frappe.csrf_token;
			}

			const response = await fetch(
				"/api/method/medical_hrms.medical_hrms.recruitment.job_application.submit_application",
				{
					method: "POST",
					headers,
					body: formData,
				}
			);

			const result = await response.json();
			if (!response.ok || result.exc) {
				const message = (result._server_messages && JSON.parse(result._server_messages)[0]) ||
					result.message ||
					"Submission failed. Please try again.";
				throw new Error(message);
			}

			form.innerHTML = `
				<div class="ja-success">
					<h3>Application submitted successfully</h3>
					<p>Your application has been received. Our HR team will review it shortly.</p>
				</div>
			`;
		} catch (error) {
			showError(error.message || "Submission failed. Please try again.");
		} finally {
			submitButton.disabled = false;
		}
	}

	document.addEventListener("click", (event) => {
		const button = event.target.closest(".ja-add-row");
		if (!button) {
			return;
		}

		console.log("Add Row button clicked");
		const tableName = button.dataset.table;
		console.log("Table name from data attribute:", tableName);

		const defn = tableDefinitions[tableName];
		if (!defn) {
			console.error("Table definition not found for:", tableName);
			return;
		}

		console.log("Calling addRow for:", tableName);
		addRow(tableName);
	});

	document.addEventListener("click", (event) => {
		const button = event.target.closest(".ja-remove-row");
		if (!button) {
			return;
		}
		const row = button.closest("tr");
		if (row) {
			row.remove();
		}
	});

	form.addEventListener("submit", submitForm);
	applyCategoryRules();
})();
