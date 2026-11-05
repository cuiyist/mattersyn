"""Per-record and per-material Reader files hold the exact combined-view objects."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_reader_shards import shards  # noqa: E402


def view():
    return {'records': {'r1': {'source_id': 's', 'figures': [{'id': 'f1'}], 'scopeLabel': 'A', 'method_label': 'Hot injection'},
                        'r2': {'source_id': 's', 'figures': [], 'scopeLabel': 'B'}},
            'materials': {'cdse-1': {'record_ids': ['r1', 'r2']}, 'cds-2': {'record_ids': ['r2']}},
            'figures_by_source': {'s': {'f1': {}}}}


class ReaderShardTest(unittest.TestCase):
    def test_each_record_file_is_its_exact_view(self):
        out, v = shards(view()), view()
        for rid, entry in v['records'].items():
            self.assertEqual(json.loads(out['records/' + rid + '.json']), entry)

    def test_material_file_holds_its_view_and_method_labels(self):
        material = json.loads(shards(view())['materials/cdse-1.json'])
        self.assertEqual(material['material'], {'record_ids': ['r1', 'r2']})
        self.assertEqual(material['method_labels'], {'r1': 'Hot injection'})

    def test_index_maps_every_record_to_its_materials(self):
        index = json.loads(shards(view())['index.json'])
        self.assertEqual(index['record_materials'], {'r1': ['cdse-1'], 'r2': ['cds-2', 'cdse-1']})

    def test_unknown_record_or_unsafe_id_is_rejected(self):
        broken = view()
        broken['materials']['cdse-1']['record_ids'].append('missing')
        with self.assertRaises(ValueError):
            shards(broken)
        unsafe = view()
        unsafe['records']['../x'] = {}
        with self.assertRaises(ValueError):
            shards(unsafe)


if __name__ == '__main__':
    unittest.main()
