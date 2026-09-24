"""Regression: legacy crop aliases must not invalidate source-link displays."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from asset_display import transform
class DisplayAliasTest(unittest.TestCase):
    def test_legacy_hash_is_private_and_display_hash_explicit(self):
        original={'public_asset':'assets/old.png','sha256':'a'*64,'caption':'Source caption','source_sha256':'c'*64,'record_context':['sample-1']}
        row={'original_sha256':'a'*64,'display_path':'assets/source-links/new.svg','display_sha256':'b'*64,'display_note':'Source link, not measured data','source_url':'https://doi.org/10.1/example'}
        log=[];new=transform(original,{'assets/old.png':row},log)
        self.assertEqual(log[0]['source_record'],original)
        self.assertNotIn('sha256',new)
        self.assertEqual(new['public_asset_sha256'],'b'*64)
        self.assertEqual(new['source_sha256'],'c'*64)
        self.assertEqual(new['record_context'],['sample-1'])
        self.assertEqual(new['caption'],original['caption'])
    def test_wrong_source_hash_rejected(self):
        with self.assertRaises(ValueError):transform({'public_asset':'old','sha256':'bad'},{'old':{'original_sha256':'correct'}},[])
