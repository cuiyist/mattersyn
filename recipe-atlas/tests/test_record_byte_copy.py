import unittest,tempfile,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_dataset import copy_verified_record
class CanonicalByteCopy(unittest.TestCase):
    def test_both_newline_styles_and_unicode_remain_exact(self):
        with tempfile.TemporaryDirectory()as td:
            source=Path(td)/'source.json';out=Path(td)/'public/record.json';record={'note':'Synthetic å fixture','value':0}
            for ending in ['\n','\r\n']:
                raw=(json.dumps(record,ensure_ascii=False,indent=2)+'\n').replace('\n',ending).encode();source.write_bytes(raw);copy_verified_record(source,out,record);self.assertEqual(raw,out.read_bytes())
            with self.assertRaises(ValueError):copy_verified_record(source,out,{'value':1})
