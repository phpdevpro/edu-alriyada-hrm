(function () {
	const config = window.jobApplicationConfig || {};
	const form = document.getElementById("job-application-form");
	if (!form) return;

	const alertBox = document.getElementById("job-application-alert");
	const categorySelect = document.getElementById("application-category");
	const categoryBadge = document.getElementById("application-category-badge");
	const submitButton = document.getElementById("job-application-submit");
	const prevButton = document.getElementById("ja-prev");
	const nextButton = document.getElementById("ja-next");
	const steps = Array.from(document.querySelectorAll(".ja-step"));
	const panels = Array.from(document.querySelectorAll(".ja-panel"));
	const isAdminPreview = Boolean(config.allow_category_override);
	const linkFields = new Set(["custom_identity_type", "custom_jameah_nationality", "academic_qualification", "general_specialization_main", "subspecialty", "appreciation", "rate_type", "study_system", "college", "city", "country", "employee_job_status", "educational_entity", "geographical_work_location", "academic_department", "job_rank", "housing"]);
	let currentCategory = config.application_category || "Academic Staff";
	let currentStep = 0;

	if (categorySelect) {
		categorySelect.value = currentCategory;
		categorySelect.disabled = !isAdminPreview;
		categorySelect.addEventListener("change", (event) => {
			currentCategory = event.target.value || currentCategory;
			updateCategoryBadge();
		});
	}

	const defs = {
		academic_qualifications: [
			["academic_qualification", "Academic Qualification", "text", true],
			["general_specialization_main", "General Specialization", "text", true],
			["subspecialty", "Subspecialty"],
			["appreciation", "Appreciation", "text", true],
			["graduation_rate", "Graduation Rate", "number", true],
			["rate_type", "Rate Type", "text", true],
			["study_system", "Study System", "text", true],
			["graduation_place", "Graduation Place", "text", true],
			["college", "College", "text", true],
			["qualification_date", "Qualification Date", "date", true],
			["graduation_year_ad", "Graduation Year", "number", true],
			["city", "City", "text", true],
			["country", "Country", "text", true],
		],
		academic_work_experience: [
			["school_year_history", "School Year History", "date", true],
			["employee_job_status", "Job Status", "text", true],
			["job_title", "Job Title", "text", true],
			["educational_entity", "Educational Entity", "text", true],
			["geographical_work_location", "Work Location", "text", true],
			["academic_department", "Academic Department", "text", true],
			["job_number", "Job Number"],
			["job_rank", "Job Rank", "text", true],
			["date_of_appointment_to_the_rank", "Appointment Date", "date"],
			["start_date", "Start Date", "date"],
			["end_of_work_date", "End Date", "date"],
			["job_duties", "Job Duties", "textarea"],
			["housing", "Housing"],
		],
		previous_work_experience: [
			["job_title", "Job Title"],
			["institution_or_company", "Institution / Company"],
			["city", "City"],
			["country", "Country"],
			["college_administration", "College / Administration"],
			["section", "Section"],
			["start_date", "Start Date", "date"],
			["end_of_work_date", "End Date", "date"],
			["job_duties", "Job Duties", "textarea"],
		],
		professional_certificates_training: [
			["course_name", "Course Name"],
			["certificate_type", "Certificate Type"],
			["issuing_authority", "Issuing Authority"],
			["course_history", "Course History", "date"],
			["course_duration", "Course Duration"],
			["city", "City"],
			["country", "Country"],
		],
		awards: [
			["award_name", "Award Name"],
			["organization", "Organization"],
			["award_date", "Award Date", "date"],
			["details", "Details"],
		],
		research_publications: [
			["title", "Title"],
			["journal", "Journal / Conference"],
			["publication_date", "Publication Date", "date"],
			["link", "Link / DOI"],
		],
	};

	function updateCategoryBadge() {
		if (categoryBadge) categoryBadge.textContent = currentCategory;
	}

	function showStep(step) {
		currentStep = Math.max(0, Math.min(step, panels.length - 1));
		panels.forEach((p, i) => p.classList.toggle("is-active", i === currentStep));
		steps.forEach((s, i) => s.classList.toggle("is-active", i === currentStep));
		if (prevButton) prevButton.disabled = currentStep === 0;
		if (nextButton) nextButton.style.display = currentStep === panels.length - 1 ? "none" : "inline-flex";
		submitButton.style.display = currentStep === panels.length - 1 ? "inline-flex" : "none";
		window.scrollTo({ top: 0, behavior: "smooth" });
	}

	function buildInput(field, type = "text") {
		const input = document.createElement(type === "textarea" ? "textarea" : "input");
		if (type !== "textarea") input.type = type;
		input.dataset.field = field;
		if (linkFields.has(field)) {
			const listId = `ministry-code-${field}-${Math.random().toString(36).slice(2)}`;
			input.setAttribute("list", listId);
			const list = document.createElement("datalist");
			list.id = listId;
			(config.ministry_codes || []).forEach((code) => {
				const option = document.createElement("option");
				option.value = code.name;
				option.label = code.name_english || code.name;
				list.appendChild(option);
			});
			document.body.appendChild(list);
			input.dataset.displaySource = "Jameah Ministry Code / name_english";
		}
		return input;
	}

	function addRow(tableName) {
		const table = document.querySelector(`.ja-rowlist[data-table='${tableName}']`);
		if (!table) return;
		const tmpl = defs[tableName] || [];
		const row = document.createElement("div");
		row.className = "ja-row-card";
		const fields = document.createElement("div");
		fields.className = "ja-row-fields";
		tmpl.forEach(([field, label, type = "text", required = false]) => {
			const wrap = document.createElement("div");
			wrap.className = "ja-row-field";
			const lab = document.createElement("label");
			lab.textContent = label;
			if (required) {
				const star = document.createElement("span");
				star.className = "ja-required";
				star.textContent = "*";
				lab.appendChild(star);
			}
			const input = buildInput(field, type);
			if (required) input.required = true;
			wrap.appendChild(lab);
			wrap.appendChild(input);
			fields.appendChild(wrap);
		});
		const actions = document.createElement("div");
		actions.className = "ja-row-actions";
		const btn = document.createElement("button");
		btn.type = "button";
		btn.className = "ja-remove-row";
		btn.textContent = "Remove";
		actions.appendChild(btn);
		row.appendChild(fields);
		row.appendChild(actions);
		table.appendChild(row);
	}

	function renderTables() {
		Object.keys(defs).forEach((name) => {
			const table = document.querySelector(`.ja-rowlist[data-table='${name}']`);
			if (!table) return;
			if (!table.querySelector(".ja-row-card")) addRow(name);
		});
	}

	function attachMinistryDatalists() {
		form.querySelectorAll("[data-field]").forEach((input) => {
			const field = input.dataset.field;
			if (!linkFields.has(field) || input.closest(".ja-rowlist")) return;
			const listId = `ministry-code-${field}`;
			input.setAttribute("list", listId);
			const list = document.createElement("datalist");
			list.id = listId;
			(config.ministry_codes || []).forEach((code) => {
				const option = document.createElement("option");
				option.value = code.name;
				option.label = code.name_english || code.name;
				list.appendChild(option);
			});
			document.body.appendChild(list);
		});
	}

	function collectRows(name) {
		const table = document.querySelector(`.ja-rowlist[data-table='${name}']`);
		if (!table) return [];
		const rows = [];
		table.querySelectorAll(".ja-row-card").forEach((card) => {
			const row = {};
			card.querySelectorAll("[data-field]").forEach((input) => {
				const val = input.value ? input.value.trim() : "";
				if (val) row[input.dataset.field] = val;
			});
			if (Object.keys(row).length) rows.push(row);
		});
		return rows;
	}

	function normalizeMinistryLinks(payload) {
		const codes = config.ministry_codes || [];
		const byTitle = new Map(codes.map((code) => [String(code.name_english || "").trim().toLowerCase(), code.name]));
		const normalize = (value) => {
			if (!value) return value;
			return byTitle.get(String(value).trim().toLowerCase()) || value;
		};
		Object.keys(payload).forEach((key) => {
			if (linkFields.has(key) && typeof payload[key] === "string") payload[key] = normalize(payload[key]);
			if (Array.isArray(payload[key])) payload[key].forEach((row) => Object.keys(row).forEach((field) => {
				if (linkFields.has(field)) row[field] = normalize(row[field]);
			}));
		});
		return payload;
	}

	function validateRows() {
		for (const [name, fields] of Object.entries(defs)) {
			const table = document.querySelector(`.ja-rowlist[data-table='${name}']`);
			if (!table) continue;
			const requiredFields = fields.filter((f) => f[3]);
			for (const card of table.querySelectorAll(".ja-row-card")) {
				for (const [field] of requiredFields) {
					const input = card.querySelector(`[data-field='${field}']`);
					if (!input || !String(input.value || "").trim()) return false;
				}
			}
		}
		return true;
	}

	function validate(payload) {
		const required = ["personal_email", "custom_first_name_en", "custom_second_name_en", "custom_last_name_en", "custom_first_name_ar", "custom_second_name_ar", "custom_last_name_ar", "custom_identity_type", "custom_jameah_nationality"];
		const missing = required.filter((k) => !payload[k]);
		if (missing.length) {
			const labels = missing.map((field) => {
				const input = form.querySelector(`[data-field='${field}']`);
				return input?.closest(".ja-field")?.querySelector("label")?.textContent?.replace("*", "").trim() || field;
			});
			return `Please complete: ${labels.join(", ")}.`;
		}
		const arabicFields = ["custom_first_name_ar", "custom_second_name_ar", "custom_third_name_ar", "custom_last_name_ar"];
		const arabicPattern = /^[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\s'’-]+$/;
		const invalidArabic = arabicFields.filter((field) => payload[field] && !arabicPattern.test(payload[field]));
		if (invalidArabic.length) return `Arabic fields must contain Arabic letters only: ${invalidArabic.join(", ")}.`;
		return "";
	}

	async function submitForm(event) {
		event.preventDefault();
		const invalidInput = Array.from(form.querySelectorAll("[required]")).find((input) => !String(input.value || "").trim());
		if (invalidInput) {
			const panel = invalidInput.closest(".ja-panel");
			if (panel) showStep(panels.indexOf(panel));
			const label = invalidInput.closest(".ja-field")?.querySelector("label")?.textContent?.replace("*", "").trim() || invalidInput.dataset.field;
			alertBox.textContent = `Please complete: ${label}.`;
			invalidInput.focus();
			return;
		}
		submitButton.disabled = true;
		const payload = {};
		form.querySelectorAll("[data-field]").forEach((input) => {
			if (input.closest(".ja-rowlist")) return;
			const val = input.value ? input.value.trim() : "";
			if (val) payload[input.dataset.field] = val;
		});
		payload.application_category = currentCategory;
		payload.academic_qualifications = collectRows("academic_qualifications");
		payload.academic_work_experience = collectRows("academic_work_experience");
		payload.previous_work_experience = collectRows("previous_work_experience");
		payload.professional_certificates_training = collectRows("professional_certificates_training");
		payload.awards = collectRows("awards");
		payload.research_publications = collectRows("research_publications");
		normalizeMinistryLinks(payload);
		const error = validate(payload);
		if (error) { alertBox.textContent = error; submitButton.disabled = false; return; }
		if (!validateRows()) { alertBox.textContent = "Please fill all required child table fields before submitting."; submitButton.disabled = false; return; }
		const fd = new FormData();
		fd.append("data", JSON.stringify(payload));
		if (config.token) fd.append("token", config.token);
		const resume = document.getElementById("resume_file");
		if (resume && resume.files && resume.files[0]) fd.append("resume_file", resume.files[0]);
		const image = document.getElementById("profile_image");
		if (image && image.files && image.files[0]) fd.append("profile_image", image.files[0]);
		try {
			const response = await fetch("/api/method/medical_hrms.medical_hrms.recruitment.job_application.submit_application", { method: "POST", body: fd, headers: window.frappe && frappe.csrf_token ? { "X-Frappe-CSRF-Token": frappe.csrf_token } : {} });
			const responseText = await response.text();
			let result;
			try { result = JSON.parse(responseText); } catch (_) { result = {}; }
			if (!response.ok || result.exc) {
				let message = result.message || result.exc_type || `Submission failed (HTTP ${response.status}).`;
				if (result._server_messages) {
					try {
						const messages = JSON.parse(result._server_messages);
						message = messages.map((item) => JSON.parse(item.message || item).message || item.message || item).join("; ");
					} catch (_) { message = result._server_messages; }
				}
				throw new Error(message);
			}
			form.innerHTML = '<div class="ja-success"><h3>Application submitted successfully</h3><p>Your application has been received.</p></div>';
		} catch (error) {
			const message = String(error.message || error).replace(/[\[\]{}"]+/g, "").replace(/\\n/g, " ");
			alertBox.textContent = `Application was not submitted: ${message}`;
			alertBox.scrollIntoView({ behavior: "smooth", block: "center" });
			submitButton.disabled = false;
		}
	}

	document.addEventListener("click", (event) => {
		const add = event.target.closest(".ja-add-row"); if (add) addRow(add.dataset.table);
		const remove = event.target.closest(".ja-remove-row"); if (remove) { const row = remove.closest(".ja-row-card"); if (row) row.remove(); }
	});
	prevButton?.addEventListener("click", () => showStep(currentStep - 1));
	nextButton?.addEventListener("click", () => showStep(currentStep + 1));
	steps.forEach((stepEl) => stepEl.addEventListener("click", () => showStep(Number(stepEl.dataset.step || 0))));
	form.addEventListener("submit", submitForm);
	updateCategoryBadge();
	attachMinistryDatalists();
	renderTables();
	showStep(0);
})();
