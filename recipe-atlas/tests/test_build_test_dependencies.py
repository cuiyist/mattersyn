"""Exercise the real snapshot-bound test dependency copier on synthetic files."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import build_release


class BuildTestDependencies(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='mattersyn-test-dependencies-')
        self.root=Path(self.tmp.name)
        self.source=self.root/'source'
        self.work=self.root/'candidate/project/recipe-atlas'
        self.work.mkdir(parents=True)
        self.rows=[]
        for i,relative in enumerate(build_release.TEST_MODULE_INPUTS):
            path=self.source/relative
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(('# synthetic authored dependency '+str(i)+'\n').encode())
            self.rows.append({'path':relative,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})

    def tearDown(self):
        self.tmp.cleanup()

    def copy(self,rows=None):
        build_release.copy_test_dependencies(self.source,self.work,{'input_files':self.rows if rows is None else rows})

    def test_two_exact_dependencies_keep_repository_layout_and_stay_out_of_dist(self):
        self.copy()
        for relative in build_release.TEST_MODULE_INPUTS:
            self.assertEqual((self.work.parent/relative).read_bytes(),(self.source/relative).read_bytes())
        self.assertEqual(len(list((self.work.parent/'tools').rglob('*.py'))),2)
        self.assertFalse((self.work/'dist/tools').exists())

    def test_missing_required_row_rejects_before_any_dependency_copy(self):
        with self.assertRaisesRegex(ValueError,'Missing or duplicate'):
            self.copy(self.rows[:1])
        self.assertFalse((self.work.parent/'tools').exists())

    def test_duplicate_required_row_is_not_a_replacement_approval(self):
        with self.assertRaisesRegex(ValueError,'Missing or duplicate'):
            self.copy(self.rows+[dict(self.rows[0])])
        self.assertFalse((self.work.parent/'tools').exists())

    def test_changed_authored_bytes_reject_before_any_dependency_copy(self):
        (self.source/build_release.TEST_MODULE_INPUTS[1]).write_bytes(b'# changed dependency\n')
        with self.assertRaisesRegex(ValueError,'input hash mismatch'):
            self.copy()
        self.assertFalse((self.work.parent/'tools').exists())

    def test_missing_authored_file_rejects(self):
        (self.source/build_release.TEST_MODULE_INPUTS[1]).unlink()
        with self.assertRaisesRegex(ValueError,'input hash mismatch'):
            self.copy()
        self.assertFalse((self.work.parent/'tools').exists())

    def test_other_snapshot_tools_are_not_copied(self):
        extra=self.source/'tools/extra.py'
        extra.parent.mkdir(parents=True,exist_ok=True);extra.write_bytes(b'# not a test dependency\n')
        self.copy(self.rows+[{'path':'tools/extra.py','sha256':hashlib.sha256(extra.read_bytes()).hexdigest()}])
        self.assertFalse((self.work.parent/'tools/extra.py').exists())

    def test_dependency_copy_never_rewrites_canonical_input_bytes(self):
        record=self.work/'data/records/audited-synthetic.json'
        record.parent.mkdir(parents=True);raw=b'{"review_status":"source_reviewed","exact":1.000}\r\n';record.write_bytes(raw)
        self.copy()
        self.assertEqual(record.read_bytes(),raw)


if __name__=='__main__':
    unittest.main()
