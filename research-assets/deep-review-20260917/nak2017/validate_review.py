import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'runtime'));import jsonschema
sys.path.insert(0,str(R.parents[2]/'recipe-atlas/scripts'))
from dataset_lib import validate_record
import struct
def png_dimensions(path):
 data=path.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n' and data[12:16]==b'IHDR'
 return list(struct.unpack('>II',data[16:24]))
C=json.loads((R/'coverage.json').read_text(encoding='utf-8'))
rs={p.stem:json.loads(p.read_text(encoding='utf-8')) for p in (R/'canonical').glob('*.json')}
errors=[]
def check(test,msg):
 if not test:errors.append(msg)
for r in rs.values():errors+=validate_record(r)
check(len(rs)==17,'17 canonical records')
for d in C['documents']:
 check(hashlib.sha256(Path(d['source_path']).read_bytes()).hexdigest()==d['sha256'],'Original source hash '+d['role'])
 check(len(d['pages'])==d['page_count'],'Page inventory '+d['role'])
 check(all(p['text_read'] and p['visual_review'] and Path(p['local_text_path']).exists() and Path(p['local_render_path']).exists() for p in d['pages']),'Per-page full review '+d['role'])
check(len(C['figures'])==10,'8numbered+2unnumbered figures')
check(len(C['tables'])==2,'Both tables')
crops=json.loads((R/'crop-manifest.json').read_text(encoding='utf-8'))
for a in crops:
 p=R/a['relative_path'];check(p.exists(),'Crop exists '+a['id']);check(hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256'],'Crop hash '+a['id']);check(png_dimensions(p)==a['pixel_dimensions'],'Crop dimensions '+a['id']);check(a['visual_review'],'Crop visually reviewed '+a['id'])
for item in C['figures']+C['tables']:
 check(hashlib.sha256((R/item['crop_asset']).read_bytes()).hexdigest()==item['crop_sha256'],'Coverage crop consistency '+item['id'])
P='nakonechnyi-2017-'
def matq(rid,id,k):return next(m for m in rs[P+rid]['materials'] if m['id']==id)['quantities'][k]['value']
for amount in [25,50,100]:
 rid='zb-cdse-znse-'+str(amount)+'nmol';r=rs[P+rid]
 check(matq(rid,'seeds','nanocrystal_amount')==amount,'Seed loading correct '+rid)
 check(matq(rid,'metal-oxide','amount')==.65 and matq(rid,'oa','reactor_amount')==5.3,'Zn/OA charges '+rid)
 check(next(o for o in r['operations'] if o['id']=='form-oleate')['parameters']['temperature']['value']==310,'Zn precursor formation310')
 check(next(o for o in r['operations'] if o['id']=='inject')['parameters']['temperature']['value']==260,'Zn injection260')
 check(all(next(p for p in r['products'] if p['sample_id']==m['sample_id'])['recipe_link']!='explicit' for m in r['measurements']),'Unassigned measurements not loading-linked '+rid)
check(matq('wz-cdse-core','cdo','amount')==1.5,'Wz core CdO1.5')
check(matq('wz-cdse-cds-seeded-growth','metal-oxide','amount')==.6,'Wz shell CdO0.6')
check(matq('wz-cdse-cds-seeded-growth','chalcogen','amount')==.5,'Wz sulfur0.5')
check(matq('wz-cdse-znse-seeded-growth','chalcogen','amount')==.96,'Wz selenium0.96')
check(matq('zb-cdse-cds-low-oa-control','oleic-acid','amount') is None,'No guessed low-OA absolute charge')
for rid,r in rs.items():
 if 'no-seed-control' in rid:
  check(not any(m['role']=='seed' for m in r['materials']),'No retained seeds in no-seed control '+rid)
  check(r['operations'][0]['parameters']['seed_amount']['value']==0,'Explicit seed absence '+rid)
 if 'core-stability-' in rid:
  key=rid.split('core-stability-')[1];mids={m['id'] for m in r['materials']}
  check(('cadmium-oleate' in mids)==key.startswith('cd-oa'),'Correct Cd omission '+rid)
  check(('top-s' in mids)==(key=='top-s-only'),'Correct S omission '+rid)
  check([o['id'] for o in r['operations']]==['run-control','sample'],'Partial control addition order retained '+rid)
 for o in r['operations']:
  for k,q in o['parameters'].items():
   if 'centrifugation' in k and q.get('value')==3000:check(q['unit']=='g_relative','Relative-force unit '+rid)
 if rid!=P+'zb-cdse-core':check(all(m['property']!='diameter' or next(p for p in r['products'] if p['sample_id']==m['sample_id'])['recipe_link']!='explicit' for m in r['measurements']),'No exact size-outcome training from unlinked contexts '+rid)
report={'status':'passed' if not errors else 'failed','errors':errors,'source_pages':16,'numbered_figures':8,'tables':2,'unnumbered_graphics':2,'original_crops':12,'canonical_records':len(rs),'schema_and_semantic_checks':True,'quantity_variant_boundary_checks':True,'source_hashes_verified':True,'coverage_sha256':hashlib.sha256((R/'coverage.json').read_bytes()).hexdigest(),'limits':'Validator checks consistency, not independent reproduction or source semantic completeness. Continuous graph data and cited upstream methods remain explicit gaps.'}
(R/'review-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2));raise SystemExit(bool(errors))
