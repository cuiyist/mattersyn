import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from compare_candidate_manifests import compare, unique_object


def row(path, content):
    return {'path': path, 'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content)}


def candidate():
    return {
        'schema': 'mattersyn-unapproved-build-candidate/1', 'status': 'UNAPPROVED',
        'release_eligible': False, 'boundary_gate_passed': False, 'published': False,
        'source_commit': '1' * 40, 'snapshot_sha256': '2' * 64, 'release_id': 'fixture',
        'display_override_sha256': None, 'metadata': {'source_commit': '1' * 40},
        'files': [row('data/example.json', b'{"value":1}\n'),
                  row('assets/original.png', b'\x89PNG\r\n\x1a\n\x00fixture')],
    }


class CandidateComparison(unittest.TestCase):
    def test_complete_equal_inventories_ignore_listing_order_only(self):
        left = candidate(); right = copy.deepcopy(left); right['files'].reverse()
        result = compare(left, right)
        self.assertTrue(result['passed'])
        self.assertEqual(result['excluded_artifact_paths'], [])
        self.assertFalse(result['release_eligible'])

    def test_text_newline_or_original_image_byte_changes_fail(self):
        for replacement in [row('data/example.json', b'{"value":1}\r\n'),
                            row('assets/original.png', b'altered image')]:
            with self.subTest(path=replacement['path']):
                left = candidate(); right = copy.deepcopy(left)
                right['files'] = [replacement if x['path'] == replacement['path'] else x for x in right['files']]
                result = compare(left, right)
                self.assertFalse(result['passed'])
                self.assertEqual(result['changed_files'], [replacement['path']])

    def test_added_and_missing_artifact_paths_fail(self):
        left = candidate(); right = copy.deepcopy(left)
        right['files'].pop(); right['files'].append(row('data/unexpected.json', b'{}'))
        result = compare(left, right)
        self.assertFalse(result['passed'])
        self.assertEqual(result['left_only'], ['assets/original.png'])
        self.assertEqual(result['right_only'], ['data/unexpected.json'])

    def test_snapshot_and_source_binding_differences_fail(self):
        for field, changed in [('snapshot_sha256', '3' * 64), ('source_commit', '4' * 40),
                               ('metadata', {'source_commit': '5' * 40})]:
            with self.subTest(field=field):
                left = candidate(); right = copy.deepcopy(left); right[field] = changed
                result = compare(left, right)
                self.assertFalse(result['passed'])
                self.assertIn(field, result['binding_differences'])

    def test_duplicate_paths_are_rejected(self):
        left = candidate(); left['files'].append(copy.deepcopy(left['files'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate artifact'):
            compare(left, candidate())

    def test_invalid_paths_hashes_sizes_and_approval_are_rejected(self):
        for field, value in [('path', '../escape'), ('path', '/absolute'),
                             ('path', 'data\\ambiguous.json'), ('sha256', 'bad'),
                             ('bytes', -1), ('bytes', True)]:
            with self.subTest(field=field, value=value):
                left = candidate(); left['files'][0][field] = value
                with self.assertRaises(ValueError): compare(left, candidate())
        left = candidate(); left['release_eligible'] = True
        with self.assertRaises(ValueError): compare(left, candidate())

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
            json.loads('{"files":[],"files":[]}', object_pairs_hook=unique_object)


if __name__ == '__main__':
    unittest.main()
