import unittest
from datetime import date
from unittest.mock import Mock, patch

import frappe
from medical_hrms import monthly_leave_policy as rules


class TestMonthlyLimits(unittest.TestCase):
    def setUp(self):
        self.settings = frappe._dict(custom_limit_half_days=1, custom_half_day_leave_type="Annual Leave",
            custom_half_day_monthly_limit=2, custom_limit_remote_work=1, custom_remote_work_monthly_limit=3)
        self.policy = patch.object(rules, "policy", return_value=self.settings)
        self.policy.start()
        self.addCleanup(self.policy.stop)
        self.db = patch.object(rules.frappe, "db", new=Mock()).start()
        self.addCleanup(patch.stopall)
        self.throw = patch.object(rules.frappe, "throw", side_effect=ValueError).start()

    def leave(self, **kwargs):
        return frappe._dict(doctype="Leave Application", employee="E1", name="L1", half_day=1,
            half_day_date="2026-09-10", leave_type="Annual Leave", status="Open", docstatus=0, **kwargs)

    def test_half_day_limit(self):
        with patch.object(rules, "half_day_count", return_value=1):
            rules.validate_monthly_limit(self.leave())
        with patch.object(rules, "half_day_count", return_value=2):
            with self.assertRaises(ValueError):
                rules.validate_monthly_limit(self.leave())

    def test_other_leave_type_exempt(self):
        doc = self.leave()
        doc.leave_type = "Sick Leave"
        rules.validate_monthly_limit(doc)
        self.db.sql.assert_not_called()

    def test_disabled_policy(self):
        self.settings.custom_limit_half_days = 0
        rules.validate_monthly_limit(self.leave())
        self.db.sql.assert_not_called()

    def remote(self):
        return frappe._dict(doctype="Remote Work Request", employee="E1", name="R1",
            from_date="2026-09-30", to_date="2026-10-01", status="Pending Manager", docstatus=0)

    def test_cross_month_and_limit(self):
        with patch.object(rules, "working_days", return_value={date(2026, 9, 30), date(2026, 10, 1)}):
            with patch.object(rules, "remote_days", return_value={date(2026, 9, 1), date(2026, 9, 2)}):
                rules.validate_monthly_limit(self.remote())
            with patch.object(rules, "remote_days", return_value={date(2026, 9, 1), date(2026, 9, 2), date(2026, 9, 3)}):
                with self.assertRaises(ValueError):
                    rules.validate_monthly_limit(self.remote())

    def test_duplicate_work_day_rejected(self):
        with patch.object(rules, "working_days", return_value={date(2026, 9, 30)}), patch.object(rules, "remote_days", return_value={date(2026, 9, 30)}):
            with self.assertRaises(ValueError):
                rules.validate_monthly_limit(self.remote())

    def test_rejected_remote_does_not_consume_limit(self):
        doc = self.remote()
        doc.status = "Rejected"
        rules.validate_monthly_limit(doc)
        self.db.sql.assert_not_called()
