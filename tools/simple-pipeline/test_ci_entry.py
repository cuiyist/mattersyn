import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('simple_ci_entry', Path(__file__).with_name('check_simple_pipeline.py'))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class CIEntryTest(unittest.TestCase):
    def test_positive_success_is_accepted(self):
        self.assertEqual(runner.result(0, 'Ran 32 tests in 1.0s\n\nOK')['status'], 'passed')

    def test_failure_or_empty_test_discovery_cannot_claim_success(self):
        for code, stderr in ((1, 'Ran 32 tests in 1.0s\nFAILED'), (0, 'Ran 0 tests in 0.0s\nOK'), (0, 'no test summary')):
            self.assertEqual(runner.result(code, stderr)['status'], 'failed')

    def test_skipped_suite_cannot_claim_complete_smoke(self):
        self.assertEqual(runner.result(0, 'Ran 32 tests in 1.0s\nOK (skipped=1)')['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
