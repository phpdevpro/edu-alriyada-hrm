// Instructor / Academic Advisor (education app): picking an Employee fills gender and department with the
// matching values from this form's own lists, instead of copying the Employee's values (B-26, staff_links.py).
(() => {
	const FIELDS = { Instructor: ["gender", "department"], "Academic Advisor": ["gender"] };

	// The education form script copies Employee.department with add_fetch; that value is not a Department Edu.
	function dropCopies(frm) {
		for (const key of ["*", frm.doctype]) {
			const fetches = frm.fetch_dict && frm.fetch_dict[key] && frm.fetch_dict[key].employee;
			if (fetches) FIELDS[frm.doctype].forEach((field) => delete fetches[field]);
		}
	}

	const handlers = {
		setup: dropCopies,
		onload: dropCopies,
		employee(frm) {
			dropCopies(frm);
			if (!frm.doc.employee) return;
			frappe.call({
				method: "medical_hrms.staff_links.values_from_employee",
				args: { doctype: frm.doctype, employee: frm.doc.employee },
				callback: (r) => {
					const { values = {}, filled_on_save = [] } = r.message || {};
					Object.entries(values).forEach(([field, value]) => frm.set_value(field, value));
					// a list this user cannot read: left empty here, the server fills it from the Employee on save
					filled_on_save.forEach((field) => frm.set_value(field, ""));
				},
			});
		},
	};
	Object.keys(FIELDS).forEach((doctype) => frappe.ui.form.on(doctype, handlers));
})();
