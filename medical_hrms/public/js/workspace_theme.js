/* Decorate native workspace links so Frappe retains permission filtering. */
(() => {
	const descriptions = {
		"hr-dashboard": ["chart", "Overview of HR services, requests, and approvals."],
		"permission-request": ["file", "Request permission for time away from work."],
		"remote-work-request": ["users", "Submit and track remote work requests."],
		"leave-plan-request": ["calendar", "Plan upcoming leave and review requests."],
		"return-from-leave-request": ["calendar", "Record an employee’s return from leave."],
		"salary-certificate-request": ["file", "Request employment and salary certificates."],
		"leave-application": ["calendar", "Manage employee leave applications."],
		"attendance-request": ["calendar", "Review attendance adjustments and requests."],
		"pre-approved-overtime-request": ["calendar", "Submit and review planned overtime."],
		"expense-claim": ["file", "Manage employee expense reimbursements."],
		"travel-request": ["file", "Plan and approve employee business travel."],
		"children-medical-allowance-request": ["heart", "Manage children’s medical allowance requests."],
		"company-car-request": ["file", "Request a company vehicle for work."],
		"contract-renewal-request": ["file", "Track employee contract renewals."],
		"employee-training-request": ["education", "Coordinate employee training requests."],
		"employee-separation": ["users", "Manage employee separation processes."],
		"full-and-final-statement": ["file", "Review final employee settlements."],
		"employee-data-update-request": ["edit", "Review changes to employee information."],
		"employee-medical-license": ["heart", "Track professional medical licenses."],
		"employee": ["users", "View and manage employee profiles."],
	};

	function decorate() {
		const workspace = frappe.workspace;
		const root = workspace?.body?.[0];
		if (!root) return;
		const active = ["Medical HRMS", "HR"].includes(workspace.current_page?.name) && workspace.is_read_only;
		root.classList.toggle("medical-hrms-themed", Boolean(active));
		if (!active) return;
		const header = workspace.current_page?.name === "Medical HRMS" && root.querySelector(".ce-header");
		if (header && !header.querySelector(".medical-hrms-icon")) {
			const icon = document.createElement("span");
			icon.className = "medical-hrms-icon";
			icon.setAttribute("aria-hidden", "true");
			icon.innerHTML = frappe.utils.icon("heart", "lg");
			header.prepend(icon);
		}
		root.querySelectorAll("[card_name]").forEach((section) => {
			section.closest(".ce-block")?.classList.add("medical-hrms-section");
		});
		root.querySelectorAll(".links-widget-box a.link-item:not([data-medical-themed])").forEach((link) => {
			if (link.classList.contains("disabled-link")) return;
			const route = new URL(link.href, location.origin).pathname.split("/").filter(Boolean).pop();
			const detail = descriptions[route] || ["file", ""];
			link.dataset.medicalThemed = "1";
			const icon = document.createElement("span");
			icon.className = "medical-hrms-icon";
			icon.setAttribute("aria-hidden", "true");
			icon.innerHTML = frappe.utils.icon(detail[0], "md");
			link.prepend(icon);
			if (detail[1]) {
				const description = document.createElement("span");
				description.className = "medical-hrms-description";
				description.textContent = __(detail[1]);
				link.querySelector(".link-content")?.append(description);
			}
		});
		root.querySelectorAll(".shortcut-widget-box:not([data-medical-themed])").forEach((shortcut) => {
			shortcut.dataset.medicalThemed = "1";
			const icon = document.createElement("span");
			icon.className = "medical-hrms-icon";
			icon.setAttribute("aria-hidden", "true");
			icon.innerHTML = frappe.utils.icon("chart", "md");
			shortcut.prepend(icon);
		});
	}

	$(document).ready(() => {
		let pending = false;
		const schedule = () => {
			if (pending) return;
			pending = true;
			requestAnimationFrame(() => { pending = false; decorate(); });
		};
		// Workspace content is rendered asynchronously and replaced on navigation/edit.
		const observer = new MutationObserver(schedule);
		observer.observe(document.querySelector(".page-container")?.parentElement || document.body,
			{ childList: true, subtree: true });
		frappe.router.on("change", schedule);
		schedule();
	});
})();
