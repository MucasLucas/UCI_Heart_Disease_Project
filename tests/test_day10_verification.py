"""Integrity failures must stop review before model deserialization or metric reuse."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from day10_verify import evidence_checks, model_checks


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def copy_evidence(self):
        for day in ['day06','day08']:
            shutil.copytree(ROOT/'reports'/day, self.root/'reports'/day)

    def test_changed_probability_bytes_rejected(self):
        self.copy_evidence()
        path = self.root/'reports/day08/predictions.csv'
        path.write_bytes(path.read_bytes().replace(b'0.5219028864262593',b'0.1219028864262593'))
        with self.assertRaisesRegex(ValueError, 'CSV content changed: predictions.csv'):
            evidence_checks(self.root)

    def test_unrecognized_disputed_image_rejected(self):
        self.copy_evidence()
        path = self.root/'reports/day08/site_comparison.png'
        path.write_bytes(path.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError, 'disputed image changed'):
            evidence_checks(self.root)

    def test_wrong_model_never_unpickled(self):
        (self.root/'models').mkdir()
        (self.root/'models/day06_candidate.joblib').write_bytes(b'not the accepted binary')
        with patch('joblib.load') as loader:
            with self.assertRaisesRegex(ValueError, 'binary hash mismatch'):
                model_checks(self.root)
            loader.assert_not_called()

    def test_missing_model_stays_pending(self):
        with self.assertRaisesRegex(ValueError, 'binary missing'):
            model_checks(self.root)


if __name__ == '__main__':
    unittest.main()
