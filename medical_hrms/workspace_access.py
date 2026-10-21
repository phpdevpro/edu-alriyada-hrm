def hide_inaccessible_workspace_breadcrumbs(bootinfo):
	"""Breadcrumbs must only point at workspaces the user can open.

	Frappe picks a page's breadcrumb workspace from module_wise_workspaces,
	which lists every public workspace of the module without a permission
	check. For the Medical HRMS module the first one is the HR-only "Medical
	HRMS" workspace, so employees saw a "Medical HRMS" breadcrumb on their
	dashboard and leave list that opened "Not permitted". Keep only the
	workspaces the sidebar already allows (allowed_workspaces is filtered).
	"""
	allowed = bootinfo.get("allowed_workspaces")
	module_wise = bootinfo.get("module_wise_workspaces")
	if allowed is None or not module_wise:
		return
	names = {w.get("name") for w in allowed}
	for module, workspaces in list(module_wise.items()):
		module_wise[module] = [w for w in workspaces if w in names]
