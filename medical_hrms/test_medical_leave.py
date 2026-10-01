import unittest
from medical_hrms.medical_leave import check_stage_sequence


class TestMedicalStages(unittest.TestCase):
    def test_full_then_partial_then_unpaid(self):
        check_stage_sequence([
            dict(from_date="2026-01-01", to_date="2026-01-30", days=30, stage=0),
            dict(from_date="2026-02-01", to_date="2026-04-01", days=60, stage=1),
            dict(from_date="2026-04-02", to_date="2026-05-01", days=30, stage=2),
        ], [30, 60, 30])

    def test_partial_cannot_be_first(self):
        with self.assertRaises(ValueError):
            check_stage_sequence([dict(from_date="2026-01-01", to_date="2026-01-02", days=2, stage=1)], [30, 60, 30])

    def test_request_crossing_stage_must_be_split(self):
        with self.assertRaises(ValueError):
            check_stage_sequence([dict(from_date="2026-01-01", to_date="2026-01-31", days=31, stage=0)], [30, 60, 30])

    def test_intermittent_half_days(self):
        check_stage_sequence([
            dict(from_date="2026-01-01", to_date="2026-01-01", days=.5, stage=0),
            dict(from_date="2026-01-10", to_date="2026-01-10", days=.5, stage=0),
        ], [30, 60, 30])

    def test_overlapping_dates(self):
        with self.assertRaises(ValueError):
            check_stage_sequence([
                dict(from_date="2026-01-01", to_date="2026-01-02", days=2, stage=0),
                dict(from_date="2026-01-02", to_date="2026-01-03", days=2, stage=0),
            ], [30, 60, 30])

    def test_total_cap(self):
        with self.assertRaises(ValueError):
            check_stage_sequence([
                dict(from_date="2026-01-01", to_date="2026-01-30", days=30, stage=0),
                dict(from_date="2026-02-01", to_date="2026-04-01", days=60, stage=1),
                dict(from_date="2026-04-02", to_date="2026-05-02", days=31, stage=2),
            ], [30, 60, 30])
