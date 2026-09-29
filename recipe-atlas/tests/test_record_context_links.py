"""Regression: root reader links must resolve from nested static record pages."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_dataset import record_href

class RecordContextLinks(unittest.TestCase):
    def test_root_reader_targets_preserve_query_and_anchor(self):
        for url in ('material.html?id=oxide&method=route','paper-review.html?id=source#evidence'):
            with self.subTest(url=url):
                self.assertEqual(record_href(url),'../'+url)

    def test_legacy_record_reader_resolves_to_real_record_entrypoint(self):
        self.assertEqual(record_href('reader.html?record=parent-oxide#protocol'),'parent-oxide.html#protocol')
        self.assertEqual(record_href('reader.html?record=parent-oxide'),'parent-oxide.html')

    def test_invalid_or_ambiguous_record_targets_are_not_silently_rewritten(self):
        for url in ('reader.html?record=../outside','reader.html?record=','reader.html?record=a&record=b','reader.html?record=a&unknown=b'):
            with self.subTest(url=url):
                self.assertEqual(record_href(url),url)

    def test_external_and_already_relative_links_remain_exact(self):
        for url in ('https://doi.org/10.1007/example','https://example.org/reader.html?record=x','//example.org/reader.html','../reader.html?record=x','./reader.html?record=x','#protocol','other.html?reader.html'):
            with self.subTest(url=url):
                self.assertEqual(record_href(url),url)

    def test_existing_atlas_asset_and_record_paths_still_resolve(self):
        for url in ('assets/structure.cif','data/record.json','records/parent.html','/reader.html?record=parent'):
            with self.subTest(url=url):
                self.assertEqual(record_href(url),'../'+url.lstrip('/'))

if __name__=='__main__':unittest.main()
