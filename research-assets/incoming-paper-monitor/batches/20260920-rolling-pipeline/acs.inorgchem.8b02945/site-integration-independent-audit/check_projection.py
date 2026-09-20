import json,hashlib,re,sys,os,copy,datetime
from pathlib import Path
M=Path('[local path redacted]');sys.path.insert(0,str(M/'research-assets'));from sync_github_public import io_path
F=Path(__file__).parent.parent;O=Path(__file__).parent;V=F/'site-integration-proposal/v1';C=F/'canonical-proposal/draft-v3'
def sha(p):return hashlib.sha256(io_path(Path(p)).read_bytes()).hexdigest()
def read(p):return json.loads(io_path(Path(p)).read_text(encoding='utf-8-sig'))
checks=[];bound={};deltas={}
def bind(p):p=Path(p);bound[str(p)]=sha(p);return bound[str(p)]
def ck(label,ok,detail=None):checks.append({'check':label,'pass':bool(ok),**({'detail':detail} if detail is not None else {})})
def diff(a,b,path=''):
 if type(a)!=type(b):return [{'path':path,'old':a,'new':b}]
 if isinstance(a,dict):
  out=[]
  for k in sorted(a.keys()|b.keys()):
   if k not in a:out.append({'path':path+'/'+k,'added':b[k]})
   elif k not in b:out.append({'path':path+'/'+k,'removed':a[k]})
   else:out+=diff(a[k],b[k],path+'/'+k)
  return out
 if isinstance(a,list):
  out=[]
  for i in range(max(len(a),len(b))):
   if i>=len(a):out.append({'path':path+'/'+str(i),'added':b[i]})
   elif i>=len(b):out.append({'path':path+'/'+str(i),'removed':a[i]})
   else:out+=diff(a[i],b[i],path+'/'+str(i))
  return out
 return [] if a==b else [{'path':path,'old':a,'new':b}]
def walk(v,path=''):
 yield path,v
 if isinstance(v,dict):
  for k,x in v.items():yield from walk(x,path+'/'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):yield from walk(x,path+'/'+str(i))
z=read(V/'package-freeze.json');man=read(V/'promotion-manifest.json')
ck('expected projection freeze',bind(V/'package-freeze.json')=='1714710fcab2068a7b9dc13e0392ccb8dd708cc661961c324ef969c6fee34612')
ck('bound author script',bind(F/'prepare_site_proposal.py')==z['author_script_sha256'])
for row in z['files']:
 p=V/row['path'];ck('proposal file '+row['path'],bind(p)==row['sha256'] and io_path(p).stat().st_size==row['bytes'])
actual={str((Path(d)/n).relative_to(io_path(V))).replace('\\','/') for d,_,names in os.walk(io_path(V)) for n in names}
ck('exhaustive frozen inventory',actual=={r['path'] for r in z['files']}|{'package-freeze.json'})
for rel,h in z['source_audits'].items():
 p=F/rel;a=read(p);ck('passed bound upstream audit '+rel,bind(p)==h and a['status']=='passed' and not a.get('open_findings'))
 # Inputs in these private upstream audits are immutable. Validate every supplied binding, including historical inputs.
 for q,w in a.get('bound_files',{}).items():
  expected=w.get('sha256') if isinstance(w,dict) else w
  ck('upstream bound input '+rel+' '+q,bind(q)==expected)
records={};counts={'routes':0,'procedures':0,'observations':0}
stale=man['removed_stale_quality_text'];ck('one historical workflow sentence',len(stale)==1 and 'Canonical/reader review remains pending' in stale[0])
for row in man['records']:
 rid=row['record_id'];old=read(row['original_path']);new=read(V/'records'/(rid+'.json'));records[rid]=new
 ck('v3 input hash '+rid,bind(row['original_path'])==row['original_sha256'])
 ck('staged record hash '+rid,sha(V/'records'/(rid+'.json'))==row['promoted_sha256'])
 ck('v2 record unchanged receipt '+rid,bind(F/'canonical-proposal/draft-v2/records'/(rid+'.json'))==sha(row['original_path']))
 ds=diff(old,new);deltas['record:'+rid]=ds
 allowed=re.compile(r'^/(collection|reader_role)$|^/quality/(review_status|review_scope|missing_fields)(/.*)?$|^/sources/\d+/(main_status|si_status|reuse_status)$')
 for d in ds:ck('record allowed metadata '+rid+d['path'],bool(allowed.fullmatch(d['path'])))
 restore=copy.deepcopy(new)
 for k in ['collection','reader_role']:
  if k in old:restore[k]=old[k]
  else:restore.pop(k,None)
 for k in ['review_status','review_scope','missing_fields']:restore['quality'][k]=old['quality'][k]
 for osrc,nsrc in zip(old['sources'],restore['sources']):
  for k in ['main_status','si_status','reuse_status']:
   if k in osrc:nsrc[k]=osrc[k]
   else:nsrc.pop(k,None)
 ck('all record science exact after metadata restoration '+rid,restore==old)
 ck('only resolved workflow gap removed '+rid,new['quality']['missing_fields']==[x for x in old['quality']['missing_fields'] if x not in stale])
 ck('no training tasks or structure labels '+rid,new['quality']['requested_tasks']==old['quality']['requested_tasks']==[] and new['structure_assets']==old['structure_assets']==[])
 ck('source-reviewed literature '+rid,new['collection']=='reviewed_literature' and new['quality']['review_status']=='source_reviewed')
 typ='routes' if old['record_type'] in ['literature_protocol','protocol_variant'] else 'procedures' if old['record_type']=='procedure' else 'observations';counts[typ]+=1
 role={'routes':'synthesis_route','procedures':'supporting_procedure','observations':'contextual_observation'}[typ];ck('correct display-only classification '+rid,new['reader_role']==role)
 ck('isolated consumer record '+rid,sha(V/'consumer-fixture/data/records'/(rid+'.json'))==sha(V/'records'/(rid+'.json')))
ck('record counts',len(records)==30 and counts=={'routes':4,'procedures':15,'observations':11})
ck('operation and measurement counts',sum(len(r['operations']) for r in records.values())==58 and sum(len(r['measurements']) for r in records.values())==750)
oldreader=read(C/'reader/friedfeld2019.json');reader=read(V/'reader/friedfeld2019.json');bind(C/'reader/friedfeld2019.json')
rd=diff(oldreader,reader);deltas['reader']=rd
top={'coverage_status','independent_audit','source_review_promoted','publication_status','review_state','training_note','audit_details','presentation_gates'}
for d in rd:
 bits=d['path'].strip('/').split('/');ok=bits[0] in top or (bits[0]=='recipe_inventory' and len(bits)>2 and bits[2] in ['status','gaps']) or (bits[0] in ['figures','tables','schemes','equations','source_notes'] and bits[-1]=='reviewed')
 ck('reader only promotion metadata '+d['path'],ok)
rest=copy.deepcopy(reader)
for k in top:
 if k in oldreader:rest[k]=oldreader[k]
 else:rest.pop(k,None)
for a,b in zip(oldreader['recipe_inventory'],rest['recipe_inventory']):
 b['status']=a['status'];b['gaps']=a.get('gaps',[])
for k in ['figures','tables','schemes','equations','source_notes']:
 for a,b in zip(oldreader[k],rest[k]):
  if 'reviewed' in a:b['reviewed']=a['reviewed']
  else:b.pop('reviewed',None)
ck('full reader science and pointers unchanged',rest==oldreader)
ck('417 reader items unchanged',sum(len(s['items']) for s in reader['reader_sections'])==417 and reader['reader_sections']==oldreader['reader_sections'])
ck('browser/import/publication not preapproved',all(reader['presentation_gates'][k] is False for k in ['site_integration','browser_render','publication','exact_product_atomic_structure_binding']))
pub=man['public_assets'];ck('162 unique public assets',len(pub)==162 and len({a['public_path'] for a in pub})==162)
actualdist={str((Path(d)/n).relative_to(io_path(V/'dist'))).replace('\\','/') for d,_,names in os.walk(io_path(V/'dist')) for n in names}
ck('public dist exactly allowlisted',actualdist=={a['public_path'] for a in pub})
uphashes={}
for rel in z['source_audits']:
 a=read(F/rel)
 for q,w in a.get('bound_files',{}).items():uphashes[str(Path(q))]=w.get('sha256') if isinstance(w,dict) else w
# Two independent reports bind their full asset manifests by freeze hash instead of
# repeating every asset path. Follow that exact verified chain before coverage checks.
for rel,freeze_rel in [('apparatus-independent-audit/independent-audit.json','visuals/apparatus/package-freeze.json'),('product-independent-audit/independent-audit.json','visuals/product-context/package-freeze.json')]:
 a=read(F/rel);fp=F/freeze_rel;fm=read(fp)
 expected=a.get('proposal_freeze_sha256') or a['inputs']['product_freeze']['sha256']
 ck('transitive audited asset freeze '+freeze_rel,bind(fp)==expected)
 for q,w in fm['bound_files'].items():
  path=Path(q) if Path(q).is_absolute() else fp.parent/q;expected=w.get('sha256') if isinstance(w,dict) else w
  ck('transitive asset freeze member '+str(path),bind(path)==expected);uphashes[str(path)]=expected
for a in pub:
 dest=V/'dist'/a['public_path'];src=Path(a['source_path']);ck('asset exact approved bytes '+a['public_path'],sha(dest)==bind(src)==a['sha256'])
 ck('source asset covered by upstream audit '+a['public_path'],str(src) in uphashes and uphashes[str(src)]==a['sha256'])
 ck('no raw source/full-page path '+a['public_path'],not re.search(r'(?i)source-render|audit-pages|\.pdf$|complete-source|(?:^|/)(?:main|si)-\d+\.png$',a['public_path']))
urls={v for path,v in walk(reader) if isinstance(v,str) and path.endswith('/public_asset')}
orig=read(F/'original-assets-manifest.json')['assets'];bind(F/'original-assets-manifest.json')
croppub={a['public_path'] for a in pub if a['kind']=='selected_original_scientific_crop'}
ck('51 reviewed crop paths and unchanged reader attachment set',len(croppub)==len(orig)==51 and urls==croppub and all(not a['contains_complete_source_page'] for a in orig))
for base in ['dist','reader','records','molecules','products']:
 for directory,dirs,names in os.walk(io_path(V/base)):
  for name in names:
   p=Path(directory)/name
   if p.suffix.lower() in ['.json','.mjs','.svg']:
    raw=p.read_text(encoding='utf-8');ck('public text has no private payload/path '+str(p.relative_to(io_path(V))),not re.search(r'[A-Z]:[\\/]|file://|/Users/|source-render|complete-source-payload',raw))
effective=read(F/'visuals/molecules-correction-v2/effective-file-map.json');bind(F/'visuals/molecules-correction-v2/effective-file-map.json')
ep=lambda rel:Path(effective['overrides'][rel]['path']) if rel in effective['overrides'] else F/'visuals/molecules'/rel
oldreg=read(ep('registry-additions.json'));reg=read(V/'molecules/registry-additions.json');bind(ep('registry-additions.json'))
rg=diff(oldreg,reg);deltas['molecular_registry']=rg
for d in rg:ck('registry only approval metadata '+d['path'],bool(re.fullmatch(r'/(binding_approved|status)|/entries/\d+/(binding_approved|independentScientificAudit|published|eligible_training)',d['path'])))
ck('39 exact entry IDs',len(reg['entries'])==39 and [e['id'] for e in reg['entries']]==[e['id'] for e in oldreg['entries']])
assetmap={a['public_path']:a for a in pub}
for a,b in zip(oldreg['entries'],reg['entries']):
 for k in ['svgPath','model2dPath','model3dPath']:
  if b.get(k):ck('registry model path/hash '+b['id']+'/'+k,b[k]==a[k] and 'assets/chemical-registry/'+b[k] in assetmap and assetmap['assets/chemical-registry/'+b[k]]['sha256']==b['assetHashes'][k])
bb=F/'visuals/molecular-bindings';b0=read(bb/'bindings-proposal.json');b1=read(V/'molecules/bindings-additions.json');bind(bb/'bindings-proposal.json')
bd=diff(b0,b1);deltas['molecular_bindings']=bd
for d in bd:
 path=d['path'];bits=path.strip('/').split('/');ok=path in ['/binding_approved','/status','/sourceRecordSha256'] or bits[0]=='sourceRecordSha256' or (bits[0]=='bindingNotes' and len(bits)==4 and bits[-1] in ['binding_approved','independent_scientific_audit']) or (bits[0] in ['recordBindings','bindingNotes'] and len(bits)==2 and d.get('added')=={} and not records[bits[1]]['materials'])
 ck('bindings only approval/hash/empty-record metadata '+path,ok)
ck('77 exact material-slot assignments',sum(len(x) for x in b1['recordBindings'].values())==77 and all(b1['recordBindings'][rid]==rows for rid,rows in b0['recordBindings'].items()))
for rid,rec in records.items():
 ck('binding complete slot IDs '+rid,set(b1['recordBindings'].get(rid,{}))=={m['id'] for m in rec['materials']})
 ck('promoted record hash bound '+rid,b1['sourceRecordSha256'].get(rid)==sha(V/'records'/(rid+'.json')))
s0=read(bb/'solution-components-proposal.json');s1=read(V/'molecules/solution-components-additions.json');bind(bb/'solution-components-proposal.json')
sd=diff(s0,s1);deltas['solution_components']=sd
for d in sd:ck('solution components only approval flags '+d['path'],bool(re.fullmatch(r'/binding_approved|/contexts/\d+/binding_approved',d['path'])) and d.get('new',d.get('added')) is True)
ck('8 stocks and16 components',len(s1['contexts'])==8 and sum(len(s['components']) for s in s1['contexts'])==16)
varied=[s for s in s1['contexts'] if s['record_id']=='friedfeld-2019-conversion-concentration']
ck('varied stock does not inherit representative charge',len(varied)==1 and '20.0 mg' not in json.dumps(varied[0]) and '1.21e-3 mmol' not in json.dumps(varied[0]))
stocks=read(V/'molecules/stock-assets.json')['stocks'];stockold=read(bb/'stock-figure-bindings.json')['stocks'];bind(bb/'stock-figure-bindings.json')
ck('stock figure assignments unchanged',[(x['record_id'],x['stock_id'],x['sha256'],x['scope']) for x in stocks]==[(x['record_id'],x['stock_id'],x['sha256'],x['scope']) for x in stockold])
Q=F/'visuals/product-context';p0=read(Q/'public-product-contexts-proposal.json');p1=read(V/'products/product-contexts-additions.json');bind(Q/'public-product-contexts-proposal.json')
pd=diff(p0,p1);deltas['product_contexts']=pd
for d in pd:ck('products only binding approval '+d['path'],bool(re.fullmatch(r'/recordContexts/[^/]+/\d+/binding_approved',d['path'])) and d.get('new',d.get('added')) is True)
ck('88 exact product contexts',sum(len(x) for x in p1['recordContexts'].values())==88)
pr0=read(Q/'registry-additions.json');pr1=read(V/'products/registry-additions.json');pa=read(Q/'public-asset-proposal.json');bind(Q/'registry-additions.json');bind(Q/'public-asset-proposal.json')
prd=diff(pr0,pr1);deltas['product_registry']=prd
for d in prd:ck('product registry approval/public-path only '+d['path'],bool(re.fullmatch(r'/entries/\d+/(svgPath|binding_approved|published|independentScientificAudit)',d['path'])))
ck('14 exact product entry IDs',len(pr1['entries'])==14 and [x['id'] for x in pr0['entries']]==[x['id'] for x in pr1['entries']])
for e in pr1['entries']:
 a=next(a for a in pa['assets'] if a['entry_id']==e['id']);ck('product image approved path '+e['id'],'assets/chemical-registry/'+e['svgPath']==a['public_path'] and assetmap[a['public_path']]['sha256']==a['sha256'])
for section in ['structures','properties']:
 expected={rid:set() for rid in records}
 for s in reader['reader_sections']:
  if s['id']!=section:continue
  for it in s['items']:
   for l in it.get('canonical_links',[]):
    bits=l['json_pointer'].strip('/').split('/')
    if bits[0]=='measurements':expected[l['record_id']].add(records[l['record_id']]['measurements'][int(bits[1])]['id'])
 actual=read(V/f'record-{section}-measurements.json');ck('display map exact source reader section '+section,actual=={k:sorted(v) for k,v in expected.items()})
bind(M/'research-assets/sync_github_public.py');bind(M/'recipe-atlas/scripts/build_paper_reviews.py');bind(M/'recipe-atlas/scripts/review_scope.py')
sys.path.insert(0,str(M/'recipe-atlas/scripts'));import build_paper_reviews as consumer
consumer.ROOT=V/'consumer-fixture';errors=consumer.validate(reader);ck('actual current reader validator',not errors,errors)
result={'author':'/root','auditor':'/root/backlog_eta','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'proposal_freeze_sha256':sha(V/'package-freeze.json'),'checks':checks,'summary':{'executed':len(checks),'passed':sum(c['pass'] for c in checks),'failed':[c for c in checks if not c['pass']]},'counts':man['counts'],'public_asset_count':len(pub),'record_categories':counts,'exact_deltas':deltas,'bound_files':bound}
io_path(O).mkdir(parents=True,exist_ok=True);io_path(O/'projection-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result['summary'],ensure_ascii=False,indent=2))
