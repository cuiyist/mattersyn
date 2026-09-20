"""Bounded private integrity check against canonical drafts and original source manifests."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,hashlib
from PIL import Image
O=Path(__file__).resolve().parent;B=O.parent
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=read(O/'shah2001.json');drafts={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')};manifest=read(B/'reader-assets/crop-manifest.json');source=read(B/'source-manifest.json');audit=read(B/'source-audit.json')
checks=[]
def ck(name,actual,expected=True):
 ok=actual==expected;checks.append({'check':name,'passed':ok,'actual':actual,'expected':expected})
def ptr(d,path):
 for t in path.split('/')[1:]:
  t=t.replace('~1','/').replace('~0','~');d=d[int(t)] if isinstance(d,list) else d[t]
 return d
items={i['id']:i for s in r['reader_sections'] for i in s['items']};assets={a['id']:a for g in ['figures','tables','schemes','equations','source_notes'] for a in r[g]}
ck('main PDF hash',sha(Path(source['source'])),source['sha256']);ck('source page count',source['page_count'],8)
ck('sections',[s['id'] for s in r['reader_sections']],['precursors','protocol','structures','properties','intuition','sources'])
ck('record IDs',sorted(x['id'] for x in r['recipe_inventory']),sorted(drafts))
ck('type counts',r['counts']['record_types'],dict(Counter(d['record_type'] for d in drafts.values())))
ck('source units',sorted({u for i in items.values() for u in i.get('source_audit_unit_ids',[])}),sorted(u['id'] for u in audit['units']))
ck('references',[x['reference_number'] for x in r['referenced_methods']],list(range(1,49)))
ck('all figures',sorted(a['id'] for a in r['figures']),sorted('figure-'+str(n) for n in range(1,12)))
meas={};ops={};params={};mats={}
for key,i in items.items():
 ck(key+' evidence',bool(i['evidence']));ck(key+' no training',i['training_eligible'],False)
 for link in i['canonical_links']:
  ck(key+' canonical record '+link['record_id'],link['record_id'] in drafts)
  if link['json_pointer']:
   value=ptr(drafts[link['record_id']],link['json_pointer']);ck(key+' pointer '+link['json_pointer'],value is not None)
   if link['json_pointer'].startswith('/operations/') and len(link['json_pointer'].split('/'))==3:ops[(link['record_id'],value['id'])]=key
 for f in i['facts']:
  rid=f['canonical_record_id'];v=ptr(drafts[rid],f['json_pointer']);q=v['value'] if 'canonical_measurement_id' in f else v
  ck(f['id']+' quantity exact',f['canonical_quantity'],q);ck(f['id']+' unit exact',f.get('unit'),q.get('unit'));ck(f['id']+' approximate exact',f['approximate'],q.get('approximate',False))
  if 'canonical_measurement_id' in f:
   ck(f['id']+' measurement ID',f['canonical_measurement_id'],v['id']);ck(f['id']+' sample ID',f['sample_id'],v['sample_id']);meas[(rid,v['id'])]=key
  if 'canonical_operation_id' in f:params[(rid,f['canonical_operation_id'],f['canonical_parameter'])]=key
  if 'canonical_material_id' in f:mats[(rid,f['canonical_material_id'],f['json_pointer'])]=key
  if q.get('minimum_exclusive'):ck(f['id']+' strict lower display',str(f['value']).startswith('> '))
  if q.get('maximum_exclusive'):ck(f['id']+' strict upper display',str(f['value']).startswith('< '))
 for j in i['sample_scope'].get('canonical_sample_links',[]):ck(key+' sample pointer',ptr(drafts[j['record_id']],j['json_pointer'])['sample_id'],j['sample_id'])
expected_meas={(rid,m['id']) for rid,d in drafts.items() for m in d.get('measurements',[])}
expected_ops={(rid,o['id']) for rid,d in drafts.items() for o in d.get('operations',[])}
expected_params={(rid,o['id'],p) for rid,d in drafts.items() for o in d.get('operations',[]) for p in o['parameters']}
ck('all measurement exact coverage',sorted(meas),sorted(expected_meas));ck('all operation coverage',sorted(ops),sorted(expected_ops));ck('all parameter coverage',sorted(params),sorted(expected_params))
for a in manifest['assets']:
 p=B/'reader-assets'/a['relative_asset'];x=assets[a['id']]
 ck(a['id']+' hash',sha(p),a['sha256']);ck(a['id']+' reader hash',x['public_asset_sha256'],a['sha256']);ck(a['id']+' source hash',a['source_sha256'],source['sha256']);ck(a['id']+' dimensions',list(Image.open(p).size),a['pixel_dimensions']);ck(a['id']+' 300 dpi',a['render_dpi'],300);ck(a['id']+' reader not final',x['reviewed'],False);ck(a['id']+' render not final',x['reader_render_verified'],False)
 for rid in x['sample_links']:ck(a['id']+' record '+rid,rid in drafts)
ck('Figure 2 no batch joins',assets['figure-2']['sample_links'],['shah-2001-ag-structure'])
ck('Figure 6 no cross-material joins',assets['figure-6']['sample_links'],['shah-2001-ag-structure'])
ck('Figure 7 no F join',assets['figure-7']['sample_links'],['shah-2001-optical-comparison'])
ck('Figure 8 Ir/Pt join',assets['figure-8']['sample_links'],['shah-2001-ir','shah-2001-pt'])
for row in r['tables'][0]['structured_rows']:
 d=drafts[row['canonical_record_id']];mm={m['id']:m for m in d['measurements']};oo={o['id']:o for o in d['operations']}
 ck('Table'+row['experiment']+' diameter',row['mean_diameter_angstrom'],mm['diameter']['value']['value'])
 ck('Table'+row['experiment']+' SD',row['standard_deviation_angstrom'],mm['diameter-standard-deviation']['value']['value'])
 ck('Table'+row['experiment']+' %SD',row['relative_standard_deviation_percent'],mm['relative-standard-deviation']['value']['value'])
 ck('Table'+row['experiment']+' concentration',row['precursor_concentration_mM'],oo['load']['parameters']['precursor_concentration']['value'])
 ck('Table'+row['experiment']+' ligand ratio',row['thiol_precursor_mol_mol'],oo['inject']['parameters']['thiol_to_precursor_molar_ratio']['value'])
 ck('Table'+row['experiment']+' temperature',row['temperature_degC'],oo['condition']['parameters']['temperature']['value'])
result={'status':'passed' if all(c['passed'] for c in checks) else 'failed','checked_at':datetime.now(timezone.utc).isoformat(),'scope':'Private canonical/reader/asset integrity. Independent scientific source audit and integrated browser/render QA remain separate.','check_count':len(checks),'failed_checks':[x for x in checks if not x['passed']],'counts':{'items':len(items),'measurements':len(meas),'operations':len(ops),'operation_parameters':len(params),'material_quantities':len(mats),'source_units':len(audit['units']),'assets':len(assets)},'hashes':{'reader':sha(O/'shah2001.json'),'source_audit':sha(B/'source-audit.json'),'crop_manifest':sha(B/'reader-assets/crop-manifest.json'),'canonical':{rid:sha(B/'canonical-drafts'/f'{rid}.json') for rid in drafts}},'checks':checks}
(O/'proposal-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','hashes']},ensure_ascii=False));assert result['status']=='passed'
