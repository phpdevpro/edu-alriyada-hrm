### Medical HRMS

Medical College HRMS

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app medical_hrms
```

### Server Setup (Step-by-Step)

1. Prerequisites in bench: `frappe`, `erpnext`, `hrms`, `education`
2. Install app:

```bash
cd /path/to/frappe-bench
bench --site <your-site> install-app medical_hrms
bench --site <your-site> migrate
```

3. Run setup scripts in order:

```bash
bench --site <your-site> execute medical_hrms.create_jameah_doctypes.execute
bench --site <your-site> execute medical_hrms.create_institute_doctypes.execute
bench --site <your-site> execute medical_hrms.create_facility_doctype.execute
bench --site <your-site> execute medical_hrms.create_child_tables.execute
bench --site <your-site> execute medical_hrms.setup_jameah_fields.execute
bench --site <your-site> execute medical_hrms.apply_hr_workspace_layout.execute
bench --site <your-site> execute medical_hrms.configure_hrm_request_governance.execute
bench --site <your-site> execute medical_hrms.configure_jameah_master_permissions.execute
bench --site <your-site> execute medical_hrms.quick_grant_hr_permissions.execute
```

4. Clear cache and restart:

```bash
bench --site <your-site> clear-cache
bench --site <your-site> clear-website-cache
bench restart
```

### Troubleshooting: App Not In apps.txt

If installation fails with `App medical_hrms not in apps.txt`, fix `sites/apps.txt` so each app is on its own line:

```text
frappe
erpnext
payments
education
hrms
medical_hrms
```

Then run:

```bash
bench --site <your-site> install-app medical_hrms
bench --site <your-site> migrate
```

### Import Ministry Excel Into Jameah Ministry Code

Script added: `medical_hrms.import_ministry_excel_to_jameah_codes.execute`

Mapping used:
- Sheet tab name -> `code_category`
- Column A (`The symbol`) -> `ministry_code`
- Column B (`Name`) -> `name_arabic`
- Column C (`Name in English`) -> `name_english`

Run:

```bash
bench --site <your-site> execute medical_hrms.import_ministry_excel_to_jameah_codes.execute --kwargs "{'file_path':'/absolute/path/Ministry Code - (Translated).xlsx'}"
bench --site <your-site> clear-cache
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/medical_hrms
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
