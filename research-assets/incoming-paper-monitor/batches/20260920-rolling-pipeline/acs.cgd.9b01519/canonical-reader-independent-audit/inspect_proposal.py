from pathlib import Path
import json,sys
A=Path(__file__).resolve().parent;G=A.parent;C=G/'canonical-proposal/v1';P=G/'public-review-proposal/v1'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def short(x):
 if isinstance(x,list):return [short(v) for v in x]
 if isinstance(x,dict):
  if 'raw_text' in x and 'status' in x and 'evidence' in x:return {k:v for k,v in x.items() if k in ['value','minimum','maximum','minimum_exclusive','maximum_exclusive','raw_text','unit','status','approximate'] and v is not None}
  return {k:short(v) for k,v in x.items() if k not in ['created_at','extracted_at','evidence','source_sha256','source_excerpt','source_files'] and v is not None and v!=[]}
 return x
mode=sys.argv[1]
if mode=='keys':
 for name in ['source-to-field-coverage','lossless-source-map','operation-quantity-scope']:
  x=load(C/(name+'.json'));print(name,list(x));
  for k,v in x.items():
   if isinstance(v,list):print(k,len(v),json.dumps(v[:1],ensure_ascii=False)[:5500])
 reader=load(P/'sommer2020.json');print('reader',list(reader));print('sections',[(s['id'],len(s['items'])) for s in reader['reader_sections']]);print('exampleitem',json.dumps(reader['reader_sections'][0]['items'][0],ensure_ascii=False)[:6500])
elif mode=='reader':
 items=[i for s in load(P/'sommer2020.json')['reader_sections'] for i in s['items']]
 for ix,i in enumerate(items[int(sys.argv[2]):int(sys.argv[3])],int(sys.argv[2])):print(ix,i['id'],i.get('title'),i.get('text'),i.get('sample_scope'),[(f.get('label'),f.get('value')) for f in i.get('facts',[]) if not f.get('canonical_quantity')])
elif mode=='record':
 r=load(C/('sommer-2020-'+sys.argv[2]+'.json'))
 keys=sys.argv[3:] or list(r)
 for k in keys:print(k,json.dumps(short(r.get(k)),ensure_ascii=False))
elif mode=='prose':
 items=[i for s in load(P/'sommer2020.json')['reader_sections'] for i in s['items']]
 for ix,i in enumerate(items[int(sys.argv[2]):int(sys.argv[3])],int(sys.argv[2])):print(ix,i['id'],'|',i.get('title'),'|',i.get('text'),'| NOTES',i.get('notes'))
elif mode=='shapes':
 for root,name in [(G,'original-assets-manifest'),(P,'reader-manifest'),(P,'source-item-coverage'),(P,'reader-bindings-proposal'),(G,'source-inventory'),(G,'source-tables')]:
  x=load(root/(name+'.json'));print(name,[(k,len(v) if isinstance(v,(dict,list)) else str(v)[:100]) for k,v in x.items()]);print('first',str(x)[:1900])
elif mode=='diagnostic':
 r=load(P/'sommer2020.json');fmap={f['id']:f for s in r['reader_sections'] for i in s['items'] for f in i['facts']}
 for f in load(A/'mechanical-checks-v1.json')['failures']:
  if f['category']=='reader_display':
   x=fmap[f['detail']];print(f['detail'],repr(x['value']),short(x['canonical_quantity']))
 for n in ['source-context','ligand-spectra','anneal-series']:
  x=load(C/('sommer-2020-'+n+'.json'));print(n,[(m['id'],m['sample_id'],str(m['value']['value'])[:400]) for m in x['measurements'][:8]])
  for m in x['measurements']:
   if str(m['value']['value']).startswith('{'):print('payload',m['id'],list(json.loads(m['value']['value'])));break
 print('historical',[(f['id'],f['sample_scope']) for f in load(G/'source-facts.json')['facts'] if 'historical' in f['id']])
 print('OA',[(m['id'],m['sample_id']) for m in load(C/'sommer-2020-ligand-spectra.json')['measurements'] if 'inset' in m['id']])
 for t in load(G/'source-tables.json')['tables']:print(t['id'],list(t),t.get('sample_scope'))
elif mode=='graphs':
 for p in sorted(C.glob('sommer-2020-*.json')):
  r=load(p);print(p.stem,'LINEAGE',short(r['lineage']))
  for o in r['operations']:print('OP',o['id'],'deps',o['depends_on'],'branch',o['branch'],'in',o['inputs'],'out',o['outputs'],'retained',o['retained_fraction'])
  print('STATES',json.dumps(short(r['material_states']),ensure_ascii=False))
elif mode=='identities':
 for p in sorted(C.glob('sommer-2020-*.json')):
  r=load(p);print(p.stem,'TARGET',short(r['intended_target']))
  print('MATERIALS',[(m['id'],m['name'],m['formula'],m['role'],m['stage'],short(m['quantities'])) for m in r['materials']])
  print('STOCKS',json.dumps(short(r['stocks']),ensure_ascii=False))
  print('PRODUCTS',[(p['sample_id'],p['material_state_id'],p['parent_sample_id'],p['recipe_link'],p['composition']['value']) for p in r['products']])
