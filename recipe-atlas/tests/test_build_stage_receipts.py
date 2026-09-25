"""Stage timing must preserve subprocess failures, not turn them into successes."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_release import BuildCommandError, execute


class StageReceipts(unittest.TestCase):
    def test_success_preserves_output_and_records_wall_time(self):
        with tempfile.TemporaryDirectory() as directory:
            run=execute([sys.executable,'-c','print("stage passed")'],directory)
        self.assertEqual(run['returncode'],0)
        self.assertEqual(run['stdout'].strip(),'stage passed')
        self.assertGreaterEqual(run['elapsed_seconds'],0)

    def test_failed_stage_retains_exit_status_and_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(BuildCommandError) as caught:
                execute([sys.executable,'-c','import sys; print("invalid binding",file=sys.stderr); sys.exit(7)'],directory)
        run=caught.exception.run
        self.assertEqual(run['returncode'],7)
        self.assertIn('invalid binding',run['stderr'])
        self.assertGreaterEqual(run['elapsed_seconds'],0)


if __name__=='__main__':
    unittest.main()
