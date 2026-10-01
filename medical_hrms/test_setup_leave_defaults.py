import unittest
from unittest.mock import Mock, patch

from medical_hrms import setup_leave_defaults as seed


class TestLeaveDefaults(unittest.TestCase):
    def test_scope_notes_preserve_hr_edits(self):
        row = seed.frappe._dict(name="Annual", **{seed.KEY: "annual", seed.NOTES: "Our HR policy notes"})
        with patch.object(seed.frappe, "get_all", return_value=[row]):
            seed.clarify_defaults()
        self.db.set_value.assert_not_called()

    def test_scope_notes_explain_separate_entitlements(self):
        row = seed.frappe._dict(name="Annual", **{seed.KEY: "annual", seed.NOTES: None})
        with patch.object(seed.frappe, "get_all", side_effect=[[row], []]):
            seed.clarify_defaults()
        self.db.set_value.assert_called_once_with("Leave Type", "Annual", seed.NOTES, seed.GUIDANCE["annual"])

    def setUp(self):
        db_patch = patch.object(seed.frappe, "db", new=Mock())
        self.db = db_patch.start()
        self.addCleanup(db_patch.stop)
        doc_patch = patch.object(seed.frappe, "get_doc")
        self.get_doc = doc_patch.start()
        self.addCleanup(doc_patch.stop)

    def test_renamed_type_is_preserved(self):
        self.db.get_value.return_value = "HR Renamed Annual"
        self.assertEqual(seed._leave_type("annual", "Annual Leave", is_carry_forward=1), "HR Renamed Annual")
        self.get_doc.assert_not_called()
        self.db.set_value.assert_not_called()

    def test_existing_type_settings_not_overwritten(self):
        self.db.get_value.return_value = None
        self.db.exists.side_effect = [False, True]
        self.assertEqual(seed._leave_type("annual", "Annual Leave", aliases=("Annual",)), "Annual")
        self.db.set_value.assert_called_once_with("Leave Type", "Annual", seed.KEY, "annual", update_modified=False)
        self.get_doc.assert_not_called()

    def test_existing_policy_not_overwritten(self):
        self.db.exists.return_value = True
        seed._policy("annual_21", "Original title", "Annual", 21)
        self.get_doc.assert_not_called()

    def test_new_policy_stays_draft(self):
        self.db.exists.return_value = False
        self.db.get_value.side_effect = [None, 0]
        seed._policy("annual_21", "Starter", "Annual", 21)
        values = self.get_doc.call_args.args[0]
        self.assertEqual(values["leave_policy_details"][0]["annual_allocation"], 21)
        self.get_doc.return_value.insert.assert_called_once_with(ignore_permissions=True)
        self.get_doc.return_value.submit.assert_not_called()
