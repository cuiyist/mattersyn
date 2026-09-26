"""A figure-level illustration must stay attached to its actual displayed source."""
import hashlib
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]

class FigureMorphologyTests(unittest.TestCase):
    def test_every_interpretation_is_hash_bound_and_separate_from_recipe_evidence(self):
        data=json.loads((ROOT/'static/data/reader-figure-morphology.json').read_text(encoding='utf-8'))
        presentation=json.loads((ROOT/'data/reader-presentation-reviewed.json').read_text(encoding='utf-8'))['records']
        seen=set()
        for entry in data['entries']:
            with self.subTest(entry=entry['id']):
                self.assertNotIn(entry['id'],seen);seen.add(entry['id'])
                self.assertEqual('source_figure_context_only',entry['binding'])
                self.assertIs(False,entry['eligible_training'])
                self.assertIs(False,entry['measured_coordinates'])
                self.assertTrue(entry['limitations'] and entry['rationale'] and entry['record_ids'])
                path=(ROOT/'static'/entry['asset']).resolve()
                self.assertTrue(path.is_relative_to((ROOT/'static').resolve()))
                self.assertEqual(entry['asset_sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
                for rid in entry['record_ids']:
                    self.assertIn(rid,presentation)
                    record=json.loads((ROOT/'data/records'/(rid+'.json')).read_text(encoding='utf-8'))
                    self.assertEqual(entry['source_group'],record['lineage']['source_group'])
                    self.assertTrue(any(entry['asset']==(f.get('public_asset') or f.get('asset')) and f.get('display_kind')!='source_link' for f in presentation[rid]['figures']))
                if entry.get('svg_path'):
                    svg=(ROOT/'static'/entry['svg_path']).resolve()
                    self.assertTrue(svg.is_relative_to((ROOT/'static').resolve()))
                    self.assertEqual(entry['svg_sha256'],hashlib.sha256(svg.read_bytes()).hexdigest())
                    tree=ET.fromstring(svg.read_bytes())
                    self.assertTrue(tree.tag.endswith('svg'))
                    self.assertFalse(any(e.tag.split('}')[-1] in {'script','foreignObject','image'} for e in tree.iter()))

if __name__=='__main__':unittest.main()
