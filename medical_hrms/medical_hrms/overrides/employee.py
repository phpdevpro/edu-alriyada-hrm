from hrms.overrides.employee_master import EmployeeMaster

from medical_hrms.ministry_lookup_validation import core_gender


class MedicalEmployee(EmployeeMaster):
	def update_user(self):
		# ERPNext copies gender onto the linked User, whose Gender field links
		# to the core Gender list; Employee.gender holds a Ministry code such
		# as Gender::1. Hand over the matching core Gender for the copy only.
		ministry_gender = self.gender
		self.gender = core_gender(ministry_gender)
		try:
			super().update_user()
		finally:
			self.gender = ministry_gender
