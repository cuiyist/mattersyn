"""Finite authored-label projection and actual public/shard integration; tiny fixtures only."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import reader_brand_projection as brand
import build_reader_metadata as builder
from build_reader_shards import load_public_view


def label(category): return brand.CURRENT_AUTHORSHIP[category][0]


class ReaderBrandProjectionTests(unittest.TestCase):
    def fixture(self):
        return {'records':{'r':{'source_id':'s','scopeLabel':'Synthetic source scope','method_label':'Synthetic method',
            'figures':[{'id':'f','summary':label('record_figure.summary'),'notes':[label('record_figure.notes')],
                        'scope':label('record_figure.scope'),'sample_scope':label('record_figure.sample_scope'),
                        'sample_linkage':label('record_figure.sample_linkage'),'source_quote':label('record_figure.summary')}],
            'protocol_art':{'bindings':[{'operation_id':'op','caption':label('binding.caption'),'source_locator':label('binding.source_locator')}],
                            'overview':{'caption':label('overview.caption')}},'measurement':{'value':12.5,'unit':'nm'}}},
            'materials':{'m':{'record_ids':['r']}},
            'figures_by_source':{'s':[{'id':'sf','summary':label('source_figure.summary'),'notes':[label('source_figure.notes')]}]},
            'schema':'mattersyn-reader-fixture/1','history':{'text':label('binding.caption')}}

    def test_proven_categories_change_only_exact_authored_values_and_never_input(self):
        view=self.fixture();before=copy.deepcopy(view);result=brand.project_reader_branding(view)
        self.assertEqual(view,before);self.assertIsNot(result,view)
        record=result['records']['r']
        self.assertIn('NanoXtalSyn',record['protocol_art']['bindings'][0]['caption'])
        self.assertIn('NanoXtalSyn',record['protocol_art']['bindings'][0]['source_locator'])
        self.assertIn('NanoXtalSyn',record['protocol_art']['overview']['caption'])
        for name in ('summary','scope','sample_scope','sample_linkage'):self.assertIn('NanoXtalSyn',record['figures'][0][name])
        self.assertIn('NanoXtalSyn',record['figures'][0]['notes'][0])
        self.assertIn('NanoXtalSyn',result['figures_by_source']['s'][0]['summary'])
        self.assertIn('NanoXtalSyn',result['figures_by_source']['s'][0]['notes'][0])
        self.assertEqual(record['figures'][0]['source_quote'],before['records']['r']['figures'][0]['source_quote'])
        self.assertIs(record['measurement'],view['records']['r']['measurement'])
        self.assertIs(result['materials'],view['materials']);self.assertIs(result['history'],view['history'])
        self.assertEqual(result['schema'],view['schema'])

    def test_unknown_values_wrong_categories_quotes_and_history_remain_opaque(self):
        value=label('binding.caption')
        view={'records':{'r':{'figures':[{'id':'f','summary':'MatterSyn unknown new label','source_quote':value}],
             'protocol_art':{'bindings':[{'caption':value+' modified','quote':value}], 'overview':{'caption':value}}}},
             'figures_by_source':{'s':[{'summary':value,'source_quote':value}]},'evidence':value,'history':value,'schema':'mattersyn-reader/1'}
        self.assertIs(brand.project_reader_branding(view),view)

    def test_no_change_keeps_identity_for_audited_raw_byte_shortcut(self):
        view={'records':{},'materials':{},'figures_by_source':{}}
        self.assertIs(brand.project_reader_branding(view),view)
        once=brand.project_reader_branding(self.fixture())
        self.assertIs(brand.project_reader_branding(once),once)

    def test_every_fixed_map_value_changes_only_the_project_name(self):
        values=set()
        for category,strings in brand.CURRENT_AUTHORSHIP.items():
            for value in strings:
                values.add(value);self.assertEqual(brand._rename(value,category),value.replace('MatterSyn','NanoXtalSyn'))
                self.assertEqual(brand._rename(value,'not_a_proven_category'),value)
        self.assertEqual(len(values),75)

    def test_actual_main_projects_after_background_before_combined_and_shards(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent)as directory:
            root=Path(directory)
            for name in ('data/records','dist/data/materials'):(root/name).mkdir(parents=True)
            view=self.fixture();raw=(json.dumps(view,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode()
            source=root/'data/reader-presentation-reviewed.json';source.write_bytes(raw)
            record=root/'data/records/r.json';record_raw=b'{"record_id":"r","lineage":{"source_group":"s"}}\r\n';record.write_bytes(record_raw)
            (root/'dist/data/materials/m.json').write_text('{"record_ids":["r"]}',encoding='utf8')
            def background(value,*args):
                return {**value,'background_untouched':{'label':label('binding.caption')}},{}
            with patch.object(builder,'ROOT',root),patch.object(builder,'attach_background',side_effect=background),patch.object(builder,'load_library',return_value={}),patch.object(builder,'library_digest',return_value='0'*64):
                builder.main()
            public=load_public_view(root/'dist/data')
            shard=json.loads((root/'dist/data/reader/records/r.json').read_bytes())
            self.assertEqual(shard,public['records']['r'])
            self.assertIn('NanoXtalSyn',shard['protocol_art']['bindings'][0]['caption'])
            self.assertIn('NanoXtalSyn',public['figures_by_source']['s'][0]['summary'])
            self.assertEqual(public['background_untouched']['label'],label('binding.caption'))
            self.assertEqual(source.read_bytes(),raw);self.assertEqual(record.read_bytes(),record_raw)
            self.assertNotIn(b'\r\n',(root/'dist/data/reader-presentation.json').read_bytes())


if __name__=='__main__':unittest.main()
