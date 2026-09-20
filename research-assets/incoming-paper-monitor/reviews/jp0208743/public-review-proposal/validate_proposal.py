"""Read-only bounded private reader/canonical/asset integrity checks."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,hashlib
from PIL import Image
O=Path(__file__).resolve().parent;B=O.parent
read=lambda p:json.loads(p.read_text(encoding='utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=read(O/'dantas2002.json');drafts={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')};manifest=read(B/'reader-assets/crop-manifest.json');source=read(B/'source-manifest.json');audit=read(B/'source-audit.json');checks=[]
def ck(name,actual,expected=True):checks.append({'check':name,'passed':actual==expected,'actual':actual,'expected':expected})
def ptr(d,path):
 for t in path.split('/')[1:]:
  t=t.replace('~1','/').replace('~0','~');d=d[int(t)] if isinstance(d,list) else d[t]
 return d
items={i['id']:i for s in r['reader_sections'] for i in s['items']};assets={a['id']:a for g in ['figures','tables','schemes','equations','source_notes'] for a in r[g]}
ck('source hash',sha(Path(source['source_path'])),source['sha256']);ck('main page count',source['main_page_count'],5)
ck('section IDs',[s['id'] for s in r['reader_sections']],['precursors','protocol','structures','properties','intuition','sources'])
ck('record IDs',sorted(x['id'] for x in r['recipe_inventory']),sorted(drafts));ck('record types',r['counts']['record_types'],dict(Counter(d['record_type'] for d in drafts.values())))
ck('all source units',sorted({u for i in items.values() for u in i.get('source_audit_unit_ids',[])}),sorted(u['id'] for u in audit['units']))
ck('all reference entries',[x['reference_number'] for x in r['referenced_methods']],list(range(1,22)));ck('all figures',sorted(a['id'] for a in r['figures']),sorted('figure-'+str(n) for n in range(1,8)))
meas={};ops={};quantities=set();factids=[]
for key,i in items.items():
 ck(key+' evidence',bool(i['evidence']));ck(key+' no training',i['training_eligible'],False)
 for link in i['canonical_links']:
  ck(key+' record '+link['record_id'],link['record_id'] in drafts)
  if link['json_pointer']:
   value=ptr(drafts[link['record_id']],link['json_pointer']);ck(key+' pointer '+link['json_pointer'],value is not None)
   if link['json_pointer'].startswith('/operations/') and len(link['json_pointer'].split('/'))==3:ops[(link['record_id'],value['id'])]=key
 for f in i['facts']:
  factids.append(f['id']);rid=f['canonical_record_id'];v=ptr(drafts[rid],f['json_pointer']);q=v['value'] if 'canonical_measurement_id' in f else v
  ck(f['id']+' quantity',f['canonical_quantity'],q);ck(f['id']+' unit',f.get('unit'),q.get('unit'));ck(f['id']+' approximate',f['approximate'],q.get('approximate',False))
  quantities.add((rid,f['json_pointer']))
  if 'canonical_measurement_id' in f:
   ck(f['id']+' ID',f['canonical_measurement_id'],v['id']);ck(f['id']+' sample',f['sample_id'],v['sample_id']);meas[(rid,v['id'])]=key
  if q.get('minimum_exclusive'):ck(f['id']+' lower bound',str(f['value']).startswith('> ') if q.get('maximum') is None else str(f['value']).startswith('('))
  if q.get('maximum_exclusive'):ck(f['id']+' upper bound',str(f['value']).startswith('< ') if q.get('minimum') is None else str(f['value']).endswith(')'))
 for j in i['sample_scope'].get('canonical_sample_links',[]):ck(key+' sample pointer',ptr(drafts[j['record_id']],j['json_pointer'])['sample_id'],j['sample_id'])
ck('fact ID unique',len(factids),len(set(factids)))
ck('all measurement coverage',sorted(meas),sorted((rid,m['id']) for rid,d in drafts.items() for m in d['measurements']))
ck('all operation coverage',sorted(ops),sorted((rid,o['id']) for rid,d in drafts.items() for o in d['operations']))
expected=set()
for rid,d in drafts.items():
 for n,m in enumerate(d['measurements']):expected.add((rid,f'/measurements/{n}'))
 for n,o in enumerate(d['operations']):expected.update((rid,f'/operations/{n}/parameters/{p}') for p in o['parameters'])
 for n,m in enumerate(d['materials']):expected.update((rid,f'/materials/{n}/quantities/{p}') for p in m.get('quantities',{}))
 for n,s in enumerate(d['stocks']):
  expected.update((rid,f'/stocks/{n}/concentrations/{p}') for p in s.get('concentrations',{}))
  for c,m in enumerate(s['components']):expected.update((rid,f'/stocks/{n}/components/{c}/quantities/{p}') for p in m.get('quantities',{}))
ck('all typed quantity coverage',sorted(quantities),sorted(expected))
for a in manifest['assets']:
 p=B/'reader-assets'/a['relative_asset'];x=assets[a['id']]
 ck(a['id']+' hash',sha(p),a['sha256']);ck(a['id']+' reader hash',x['public_asset_sha256'],a['sha256']);ck(a['id']+' source hash',a['source_sha256'],source['sha256']);ck(a['id']+' dimensions',list(Image.open(p).size),a['pixel_dimensions']);ck(a['id']+' dpi',a['render_dpi'],300);ck(a['id']+' pending review',x['reviewed'],False);ck(a['id']+' pending render',x['reader_render_verified'],False)
 for rid in x['sample_links']:ck(a['id']+' record '+rid,rid in drafts)
ck('Figure 3 remains pure theory',assets['figure-3']['sample_links'],['dantas-2002-parabolic-model','dantas-2002-four-band-model'])
ck('Figure 4 remains AFM cohorts',assets['figure-4']['sample_links'],['dantas-2002-afm1','dantas-2002-afm2','dantas-2002-afm-analysis'])
ck('Figure 6 remains SG1',assets['figure-6']['sample_links'],['dantas-2002-sg1','dantas-2002-power-response','dantas-2002-mechanisms'])
result={'status':'passed' if all(c['passed'] for c in checks) else 'failed','checked_at':datetime.now(timezone.utc).isoformat(),'scope':'Private canonical, reader, source-unit and asset integrity; independent science/crop audit and integrated browser checks remain separate.','check_count':len(checks),'failed_checks':[c for c in checks if not c['passed']],'counts':{'items':len(items),'source_units':len(audit['units']),'records':len(drafts),'operations':len(ops),'measurements':len(meas),'typed_facts':len(quantities),'assets':len(assets)},'hashes':{'reader':sha(O/'dantas2002.json'),'source_audit':sha(B/'source-audit.json'),'crop_manifest':sha(B/'reader-assets/crop-manifest.json'),'canonical':{rid:sha(B/'canonical-drafts'/f'{rid}.json') for rid in drafts}},'checks':checks}
(O/'proposal-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k not in ['checks','hashes']}));assert result['status']=='passed'
