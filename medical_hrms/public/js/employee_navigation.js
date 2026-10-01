// Navigation UX only. Ownership and write protection are enforced server-side.
(() => {
	const employeeForms = new Set([
		"Employee", "Permission Request", "Remote Work Request", "Leave Plan Request", "Leave Application",
		"Return from Leave Request", "Salary Certificate Request", "Pre Approved Overtime Request",
		"Employee Training Request", "Children Medical Allowance Request", "Company Car Request",
		"Contract Renewal Request", "Employee Data Update Request",
	]);
	function redirectStandardForm() {
		if (!frappe.user.has_role("Employee") || frappe.session.user === "Administrator" ||
			["HR User", "HR Manager", "System Manager"].some(role => frappe.user.has_role(role))) return;
		const route = frappe.get_route();
		if (["Form", "List"].includes(route[0]) && employeeForms.has(route[1])) {
			frappe.set_route("employee-dashboard");
		}
	}
	$(document).ready(() => {
		frappe.router.on("change", redirectStandardForm);
		redirectStandardForm();
	});
})();
