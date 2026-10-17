import copy,importlib.util,json,sys,unittest,uuid
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'scripts'))
import public_reader_registry as m
import reader_presentation_registry as source

def value():
 return {'schema_version':'1.0','records':{f'r{i}':{'status':'source_extracted','training_eligible':False,'figures':[{'id':f'f{i}','public_caption':'short factual paraphrase '+str(i),'origin':'manual','status':'accepted','full_crop_sha256':'a'*64}],'padding':'x'*160}for i in range(8)},'materials':{'m':{'record_ids':['r0'],'component_only':True}},'figures_by_source':{},'counter':9}
def merge(parts):
 base=json.loads(parts[m.BASE]);marker=base.pop(source.MARKER,None)
 return base if marker is None else source._merge(base,json.loads(parts[m.PART]))
class PublicParts(unittest.TestCase):
 def test_current_unsplit_preserves_exact_legacy_bytes(self):
  v=value();raw=(json.dumps(v,indent=2)+'\n').encode();self.assertEqual(m.public_parts(v,raw),{m.BASE:raw});self.assertEqual(merge(m.public_parts(v,raw)),v)
 def test_forced_small_split_is_deterministic_exact_and_disjoint(self):
  v=value();before=copy.deepcopy(v);limit=int(len(m.encoded(v))*.8)
  with patch.object(m,'MAX_PART_BYTES',limit):first=m.public_parts(v);second=m.public_parts(v)
  self.assertEqual(first,second);self.assertEqual(set(first),{m.BASE,m.PART});self.assertTrue(all(len(b)<limit for b in first.values()));self.assertEqual(merge(first),v);self.assertEqual(v,before)
  a=json.loads(first[m.BASE]);b=json.loads(first[m.PART]);self.assertEqual(a[source.MARKER]['part'],m.PART)
  for table in source.TABLES:self.assertFalse(set(a[table])&set(b[table]))
 def test_exact_public_limit_splits_instead_of_emitting_equal_limit(self):
  v=value();limit=len(m.encoded(v))
  with patch.object(m,'MAX_PART_BYTES',limit):parts=m.public_parts(v)
  self.assertEqual(set(parts),{m.BASE,m.PART});self.assertTrue(all(len(b)<limit for b in parts.values()))
 def test_one_indivisible_oversized_entry_fails(self):
  v={'records':{'r':{'caption':'x'*2000}},'materials':{},'figures_by_source':{}}
  with patch.object(m,'MAX_PART_BYTES',400),self.assertRaisesRegex(ValueError,'below80MiB'):m.public_parts(v)
 def test_bad_tables_reserved_marker_and_wrong_legacy_bytes_fail(self):
  for key in source.TABLES:
   v=value();v[key]=[]
   with self.assertRaises(ValueError):m.public_parts(v)
  v=value();v[source.MARKER]={}
  with self.assertRaises(ValueError):m.public_parts(v)
  with self.assertRaises(ValueError):m.public_parts(value(),b'{}')
 def test_source_split_code_and_unsplit_contract_unchanged(self):
  self.assertEqual(m.MAX_PART_BYTES,80*1024*1024);self.assertEqual(merge(m.public_parts(value())),value())
 def test_normal_builder_uses_small_fixture_and_preserves_display_semantics(self):
  spec=importlib.util.spec_from_file_location('private_candidate_reader_builder',HERE.parent/'scripts/build_reader_metadata.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
  root=HERE.parents[2]/'fixtures'/('reader-'+uuid.uuid4().hex);(root/'data/records').mkdir(parents=True);(root/'dist/data/materials').mkdir(parents=True)
  v=value()
  for rid in v['records']:
   v['records'][rid].update(source_id='s',scopeLabel='Source extracted scope')
   (root/'data/records'/(rid+'.json')).write_text(json.dumps({'lineage':{'source_group':'s'}}),encoding='utf-8')
  # Exercise unchanged asset-display transformation BEFORE physical splitting.
  import asset_display,hashlib
  fig=v['records']['r0']['figures'][0];fig.update(public_asset='assets/withheld.png',public_asset_sha256='a'*64)
  card=b'<svg/>';cardpath=root/'dist/assets/source-links/card.svg';cardpath.parent.mkdir(parents=True);cardpath.write_bytes(card)
  row={'original_path':'assets/withheld.png','original_sha256':'a'*64,'display_path':'assets/source-links/card.svg','display_sha256':hashlib.sha256(card).hexdigest(),'source_url':'https://doi.org/example','display_note':'Source link only'}
  (root/'private-build').mkdir();(root/'private-build/asset-display-overrides.json').write_text(json.dumps({'schema':'mattersyn-asset-display-overrides/1','scope':'private_build_input_do_not_deploy','assets':[row]}),encoding='utf-8')
  expected=asset_display.transform(v,{row['original_path']:row},[])
  (root/'data/reader-presentation-reviewed.json').write_text(json.dumps(v),encoding='utf-8');(root/'dist/data/materials/m.json').write_text(json.dumps({'record_ids':['r0']}),encoding='utf-8')
  builder.ROOT=root
  with patch.object(m,'MAX_PART_BYTES',int(len(m.encoded(expected))*.8)):builder.main()
  parts={n:(root/'dist/data'/n).read_bytes()for n in [m.BASE,m.PART]};actual=merge(parts);self.assertEqual(actual,expected)
  self.assertEqual(actual['records']['r0']['status'],'source_extracted');self.assertFalse(actual['records']['r0']['training_eligible']);self.assertEqual(actual['records']['r0']['figures'][0]['origin'],'manual');self.assertEqual(actual['counter'],v['counter']);self.assertEqual(actual['records']['r0']['figures'][0]['display_kind'],'source_link')
if __name__=='__main__':unittest.main()
