"""Checklist: what still has to be done or checked outside the code before and after go-live.

Rule: when an item changes, update its Status / Done on / Last updated here (with the date) and add a
line to changelog.py, then run build_all.py.
"""

D21, D22 = "21 Oct 2026", "22 Oct 2026"
STATUSES = ["Open", "Done", "Blocked", "Not needed"]
SRV, DEV, OWNER, HR, ACAD, MIN, TEST = "Server admin", "Developer (Abdul Hakeem)", "Project owner", "HR", "Academic Affairs", "Ministry contact (Ms. Najah)", "Testing team"

# (ID, group, item, how / where, owner, needed by, ref, status, done on, added on, last updated)
CHECKLIST = [
	# ------------------------------------------------------------ deployment
	("CL-01", "1. Deploy to the live server", "Pull the new branch", "In apps/medical_hrms on the server: git fetch, then check out the branch named in the latest Change Log line.", SRV, "Before UAT", "HR-58", "Open", "", D21, D21),
	("CL-02", "1. Deploy to the live server", "Migrate", "bench --site <site> migrate. Read the output: no errors; send any line 'Kept (they hold data ...)' to the developer (TC-ERR-05). The migrate also renames the three sick-leave types to Sick Leave 1 / 2 / 3 (balances kept, TC-LV-17).", SRV, "Before UAT", "HR-51, HR-68", "Open", "", D21, D22),
	("CL-03", "1. Deploy to the live server", "Build, clear cache, restart", "bench build --app medical_hrms; bench --site <site> clear-cache; bench restart. Needed for the new HR / Employee Portal, the new report and the Arabic translations.", SRV, "Before UAT", "HR-66", "Open", "", D21, D21),
	("CL-04", "1. Deploy to the live server", "Scheduler and long-queue worker running", "bench --site <site> doctor. The hourly Jameah refresh now runs on the long queue (about 7 minutes), so a long-queue worker must run.", SRV, "After deploy", "JM-18", "Open", "", D21, D21),
	("CL-05", "1. Deploy to the live server", "Verify the Ministry views", "bench --site <site> execute medical_hrms.jameah.verify.run -> all 23 views OK (5 Employee, 8 Faculty, 10 Student).", DEV, "After deploy", "JM-06, JM-14", "Open", "", D21, D21),
	# ------------------------------------------------------------ live server checks
	("CL-06", "2. Check on the live server", "Error Log", "Open /app/error-log on the live site; group by title; note the times. This is where the client's 'random' error will show.", OWNER, "Before UAT", "HR-46", "Open", "", D21, D21),
	("CL-07", "2. Check on the live server", "System e-mail account", "Email Account 'Notifications' -> re-enter the password -> Save -> send a test e-mail. Fixes 'Failed to decrypt key ...password'.", SRV, "Before UAT", "HR-47", "Open", "", D21, D21),
	("CL-08", "2. Check on the live server", "Logo file", "Open /files/rchs-logo.png on the live site; upload it again if missing.", SRV, "Before UAT", "HR-54", "Open", "", D21, D21),
	("CL-09", "2. Check on the live server", "Real HR login", "Log in with a real HR account (or Impersonate) and confirm the HR Portal opens.", OWNER, "After deploy", "HR-45", "Open", "", D21, D21),
	("CL-10", "2. Check on the live server", "Real instructor / HOD / advisor logins", "Impersonate one of each and confirm their own dashboards still open.", OWNER, "After deploy", "HR-45", "Open", "", D21, D21),
	("CL-11", "2. Check on the live server", "Real non-Saudi employees", "As HR open 2-3 real non-Saudi (Iqama) employees: no 'Not Saved' on opening; edit a field and Save.", OWNER, "After deploy", "HR-63", "Open", "", D21, D21),
	# ------------------------------------------------------------ decisions
	("CL-12", "3. Decisions", "Ministry view and column names", "Ask which names the Jameah agent reads (HTML or schema V0.1), including the HTML spellings EnglishFourhtName and Summury.", MIN, "Before Jameah go-live", "DEC-01", "Open", "", D21, D21),
	("CL-13", "3. Decisions", "Read-only database account for the Ministry", "Create it with medical_hrms.jameah.views.grant_statements and give the Ministry the connection details.", SRV, "Before Jameah go-live", "JM-08", "Open", "", D21, D21),
	("CL-14", "3. Decisions", "Jameah Settings and Student code decisions", "Answers for DEC-02 - DEC-07, entered in Jameah Settings and the Code Map.", ACAD, "Before Jameah go-live", "DEC-02 - DEC-07", "Open", "", D21, D21),
	("CL-15", "3. Decisions", "Credit-hour definitions", "Confirm Registered = this term's hours; Passed = earned + bridged plan hours.", ACAD, "Before Jameah go-live", "DEC-11", "Open", "", D21, D21),
	("CL-16", "3. Decisions", "Which faculty are sent", "Active Instructors only (as built), or also former (Left) ones.", ACAD, "Before Jameah go-live", "DEC-12", "Open", "", D21, D21),
	("CL-17", "3. Decisions", "Faculty status and contract codes", "Pick the Ministry code for Faculty Status 'Active' and Contract Type 'Full Time' in Jameah Code Map.", ACAD, "Before Jameah go-live", "DEC-13", "Open", "", D21, D21),
	("CL-18", "3. Decisions", "Demo employee EMP-00001", "Complete it or delete it before go-live (it misses Ministry-mandatory fields).", HR, "Before go-live", "HR-53", "Open", "", D21, D21),
	# ------------------------------------------------------------ HR data
	("CL-19", "4. HR data", "Instructor data sheet", "Fill the Instructor sheet so the existing Instructors are linked to Employees; the Faculty views fill in as they are.", HR, "Before Jameah go-live", "HR-55", "Open", "", D21, D21),
	("CL-20", "4. HR data", "Non-academic staff data sheet", "Employees Missing Ministry Data report -> Download Data Sheet -> fill the red cells -> Check -> Import.", HR, "Before Jameah go-live", "HR-50", "Open", "", D21, D21),
	("CL-21", "4. HR data", "Academic Holiday List", "Set it in HR Settings > Academic Schedules & Presence.", HR, "Before UAT", "HR-57", "Open", "", D21, D21),
	("CL-28", "4. HR data", "Leave period for Al Riyada College", "HR Portal > Leave > Yearly setup 1: Leave Period for this year, company Al Riyada College, tick Is Active.", HR, "Before UAT", "HR-69", "Open", "", D22, D22),
	("CL-29", "4. HR data", "Holiday list for Al Riyada College", "Step 2: Holiday List with the official holidays and weekends; set it as the default holiday list on the Company.", HR, "Before UAT", "HR-69, DEC-10", "Open", "", D22, D22),
	("CL-30", "4. HR data", "Leave approvers", "Step 5: set the leave approver on each Department (Leave Approvers table) or on each Employee. 3 of 4 employees have none today.", HR, "Before UAT", "HR-69", "Open", "", D22, D22),
	("CL-31", "4. HR data", "Annual leave balances", "Steps 3-4: submit the annual leave policy (21 or 30 days) and assign it with Leave Control Panel; the Leave setup check turns green.", HR, "Before UAT", "HR-69", "Open", "", D22, D22),
	("CL-32", "4. HR data", "Sick Leave policy", "Review and submit 'Medical HRMS - Sick Leave (3 Pay Stages, Separate Sick Year)'; Finance checks the 75% pay on a salary slip.", "HR + Finance", "Before UAT", "HR-20, DEC-14", "Open", "", D22, D22),
	("CL-22", "4. HR data", "Attendance devices", "Connect the devices so Faculty After 4 PM uses real check-out times.", "HR + IT", "Later", "HR-56", "Open", "", D21, D21),
	# ------------------------------------------------------------ reviews and testing
	("CL-23", "5. Reviews and testing", "Run the test cases", "Testing team works through Medical_HRMS_Jameah_Test_Cases.xlsx and records results and bugs there.", TEST, "UAT", "HR-46", "Open", "", D21, D21),
	("CL-24", "5. Reviews and testing", "Arabic labels", "An Arabic speaker reads the HR / Employee Portal pages in Arabic and lists wording to change, including the 114 new leave texts (22 Oct).", OWNER, "UAT", "HR-66, HR-68", "Open", "", D21, D22),
	("CL-25", "5. Reviews and testing", "Portal design approval", "Client confirms the new HR Portal / Employee Portal look.", OWNER, "UAT", "HR-66", "Open", "", D21, D21),
	("CL-33", "5. Reviews and testing", "Leave flow UAT", "An employee and their manager go through TC-LV-09 - TC-LV-17: plan, apply now, approve, return (also after sick leave).", TEST, "UAT", "HR-68", "Open", "", D22, D22),
	("CL-26", "5. Reviews and testing", "Arabic interface", "Switch to AR and repeat a few test cases (HR Portal, Employee Portal, application form).", TEST, "UAT", "—", "Open", "", D21, D21),
	("CL-27", "5. Reviews and testing", "Developer copy of Education up to date", "On the development machine the Education checkout is behind its master branch; update it before testing there (git pull --ff-only).", OWNER, "Now", "—", "Open", "", D21, D21),
]
