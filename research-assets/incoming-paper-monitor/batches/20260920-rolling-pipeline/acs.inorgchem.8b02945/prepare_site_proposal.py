"""Root-only publication projection. Refuses execution before separate upstream gates pass."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,re,shutil,sys,os
F=Path(__file__).resolve().parent
O=F/'site-integration-proposal/v1'
S=F.parents[4]/'recipe-atlas'
C=F/'canonical-proposal/draft-v3'
sys.path.insert(0,str(F.parents[4]/'research-assets'))
from sync_github_public import io_path
read=lambda p:json.loads(io_path(p).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(io_path(p).read_bytes()).hexdigest()
def save(p,x):
 p=io_path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (O/'package-freeze.json').exists(),'Preserve frozen proposals; create an explicit revision instead.'
assert not O.exists() or (O/'FAILED_ATTEMPT.json').exists(),'Only resume an explicitly recorded, never-frozen staging attempt.'
audits={}
for rel in ['source-independent-audit/independent-audit-v2.json','canonical-independent-audit/independent-audit-v3.json','molecular-independent-audit/independent-audit-v2.json','molecular-bindings-independent-audit/independent-audit.json','apparatus-independent-audit/independent-audit.json','product-independent-audit/independent-audit.json']:
 p=F/rel;a=read(p);assert a['status']=='passed' and not a.get('open_findings'),rel;audits[rel]=sha(p)
scope='All eight supplied main pages and 25 matched SI pages read and independently audited. Canonical records, corrected reader, molecular references and bindings, stage-specific apparatus and symbolic product contexts passed separate audits. Four conversion route/variant records, fifteen supporting procedures and eleven observation records retain their separate contexts. Source inconsistencies and unreported conditions remain explicit. No current-product atomic coordinates, exact structure–recipe pair or new training task is admitted.'
stale='The frozen effective source extraction passed distinct independent source audit. Canonical/reader review remains pending; this private draft has no scientific promotion.'
records={};deltas=[]
for row in read(C/'record-manifest.json')['records']:
 src=Path(row['path']);assert sha(src)==row['sha256'];r=read(src);old=copy.deepcopy(r);rid=r['record_id']
 r['collection']='reviewed_literature'
 r['reader_role']='synthesis_route' if r['record_type'] in ('literature_protocol','protocol_variant') else 'supporting_procedure' if r['record_type']=='procedure' else 'contextual_observation'
 r['quality'].update(review_status='source_reviewed',review_scope=scope)
 r['quality']['missing_fields']=[x for x in r['quality']['missing_fields'] if x!=stale]
 for source in r['sources']:
  source.update(main_status='All eight supplied main pages read, visually inspected and independently audited; source and canonical checks passed.',si_status='All 25 matched SI pages read, visually inspected and independently audited; title, authors and contents confirm the main–SI association.',reuse_status='Source-linked facts and selected scientific crops; original article, SI, complete text and full-page scans remain local.')
 assert not r['quality']['requested_tasks'] and not r['structure_assets']
 for k in set(r)-{'collection','reader_role','quality','sources'}:assert r[k]==old[k],(rid,k)
 for k in set(r['quality'])-{'review_status','review_scope','missing_fields'}:assert r['quality'][k]==old['quality'][k]
 dest=O/'records'/src.name;save(dest,r);records[rid]=r
 deltas.append({'record_id':rid,'original_path':str(src),'original_sha256':sha(src),'promoted_sha256':sha(dest),'reader_role':r['reader_role'],'scientific_values_unchanged':True})
assert len(records)==30 and sum(len(r['operations']) for r in records.values())==58
reader=read(C/'reader/friedfeld2019.json')
reader.update(coverage_status='supplied_main_and_si_review_complete',independent_audit=scope,source_review_promoted=True,publication_status='Source-reviewed contribution staged for integration; browser and live deployment remain separate.',review_state='source_reviewed',training_note='No new task or exact structure–recipe training pair is admitted. Literature cluster formulas, local lattice fringes and calculated Scherrer domains do not supply current specimen atomic coordinates or verified cross-technique batch identity.')
reader['audit_details']={'scope':scope,'audit_sha256':audits,'source_conflicts_resolved':False,'training_promotions':0}
for item in reader['recipe_inventory']:
 item['status']='source_reviewed';item['gaps']=[x for x in item.get('gaps',[]) if x!=stale]
for key in ['figures','tables','schemes','equations','source_notes']:
 for item in reader[key]:item['reviewed']=True
reader['presentation_gates']={'canonical_source_audit':True,'reader_source_audit':True,'molecular_bindings':True,'apparatus_bindings':True,'symbolic_product_contexts':True,'exact_product_atomic_structure_binding':False,'site_integration':False,'browser_render':False,'publication':False}
assert not re.search(r'[A-Z]:[\\/]|file://',json.dumps(reader));save(O/'reader/friedfeld2019.json',reader)
public=[]
def asset(src,rel,kind):
 dest=io_path(O/'dist'/rel);dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():assert sha(dest)==sha(src)
 else:dest.write_bytes(io_path(src).read_bytes())
 if not any(x['public_path']==rel for x in public):public.append({'public_path':rel,'source_path':str(src),'sha256':sha(src),'kind':kind})
assets=read(F/'original-assets-manifest.json')['assets'];assert len(assets)==51
for a in assets:
 src=Path(a['path']);assert sha(src)==a['sha256'] and a['contains_complete_source_page'] is False
 asset(src,'assets/figures/friedfeld2019/'+src.name,'selected_original_scientific_crop')
urls=set()
def walk(x):
 if isinstance(x,dict):
  if x.get('public_asset'):urls.add(x['public_asset'])
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(reader);assert urls=={a['public_path'] for a in public},(urls-{a['public_path'] for a in public})
V=F/'visuals/molecules';effective=read(F/'visuals/molecules-correction-v2/effective-file-map.json')
def ep(rel):
 override=effective['overrides'].get(rel)
 p=Path(override['path']) if override else V/rel
 if override:assert sha(p)==override['sha256']
 else:assert sha(p)=={k.replace('\\','/'):v for k,v in read(V/'package-freeze.json')['bound_files'].items()}[rel]
 return p
registry=read(ep('registry-additions.json'))
for e in registry['entries']:
 e.update(binding_approved=True,independentScientificAudit='passed_source_scoped_molecular_and_binding_audits',published=False,eligible_training=False)
 for key in ['svgPath','model2dPath','model3dPath']:
  if not e.get(key):continue
  src=ep(e[key]);assert sha(src)==e['assetHashes'][key]
  asset(src,'assets/chemical-registry/'+e[key],'reviewed_chemical_reference')
registry.update(binding_approved=True,status='independently_passed_source_references_staged_for_integration')
B=F/'visuals/molecular-bindings';bindings=read(B/'bindings-proposal.json')
for rid,notes in bindings['bindingNotes'].items():
 assert rid in records
 for note in notes.values():note.update(binding_approved=True,independent_scientific_audit='Separate molecular identity and exact material/stock binding audits passed; scientific fields unchanged.')
for rid,r in records.items():
 if not r['materials']:bindings['recordBindings'].setdefault(rid,{});bindings['bindingNotes'].setdefault(rid,{})
bindings.update(binding_approved=True,status='independently_passed_source_bindings_staged_for_integration')
bindings['sourceRecordSha256']={rid:sha(O/'records'/(rid+'.json')) for rid in records}
save(O/'molecules/registry-additions.json',registry);save(O/'molecules/bindings-additions.json',bindings)
solutions=read(B/'solution-components-proposal.json');solutions['binding_approved']=True
for c in solutions['contexts']:c['binding_approved']=True
save(O/'molecules/solution-components-additions.json',solutions)
stock_assets=[]
for a in read(B/'stock-figure-bindings.json')['stocks']:
 src=Path(a['path']);assert sha(src)==a['sha256'];rel='assets/chemical-registry/stock-svg/'+src.name
 asset(src,rel,'reviewed_stock_reference_diagram')
 stock_assets.append({'record_id':a['record_id'],'stock_id':a['stock_id'],'public_path':rel,'sha256':a['sha256'],'scope':a['scope']})
save(O/'molecules/stock-assets.json',{'note':'Separate downloadable stock illustration candidates; actual website integration is checked independently.','stocks':stock_assets})
asset(F/'visuals/apparatus/friedfeld2019-protocol.mjs','friedfeld2019-protocol.mjs','independently_audited_apparatus')
Q=F/'visuals/product-context';products=read(Q/'public-product-contexts-proposal.json');preg=read(Q/'registry-additions.json')
for rows in products['recordContexts'].values():
 for row in rows:row['binding_approved']=True
byentry={a['entry_id']:a for a in read(Q/'public-asset-proposal.json')['assets']}
for e in preg['entries']:
 a=byentry[e['id']];src=Path(a['path']);assert sha(src)==a['sha256']==e['assetHashes']['svgPath'];asset(src,a['public_path'],'reviewed_symbolic_product_context')
 e['svgPath']=a['public_path'].removeprefix('assets/chemical-registry/');e.update(binding_approved=True,published=False,independentScientificAudit='passed_source_scoped_product_context_audit')
save(O/'products/product-contexts-additions.json',products);save(O/'products/registry-additions.json',preg)
assert not re.search(r'[A-Z]:[\\/]|file://',json.dumps(products))
maps={section:{rid:set() for rid in records} for section in ['structures','properties']}
for section in reader['reader_sections']:
 if section['id'] not in maps:continue
 for item in section['items']:
  for link in item.get('canonical_links',[]):
   bits=link['json_pointer'].strip('/').split('/')
   if bits[0]=='measurements':maps[section['id']][link['record_id']].add(records[link['record_id']]['measurements'][int(bits[1])]['id'])
for rid in records:assert not (maps['structures'][rid]&maps['properties'][rid]),rid
for section,data in maps.items():save(O/('record-'+section+'-measurements.json'),{rid:sorted(ids) for rid,ids in data.items()})
sys.path.insert(0,str(S/'scripts'));import build_paper_reviews as consumer
fixture=O/'consumer-fixture';(fixture/'data/records').mkdir(parents=True,exist_ok=True)
for p in (O/'records').glob('*.json'):(fixture/'data/records'/p.name).write_bytes(p.read_bytes())
for p in (O/'dist/assets/figures').rglob('*'):
 if p.is_file():
  dest=fixture/'dist/assets/figures'/p.relative_to(O/'dist/assets/figures');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
consumer.ROOT=fixture;errors=consumer.validate(reader);assert not errors,errors
save(O/'actual-reader-validator-check.json',{'status':'passed','consumer_path':str(S/'scripts/build_paper_reviews.py'),'consumer_sha256':sha(S/'scripts/build_paper_reviews.py'),'errors':errors,'fixture_isolated_from_site':True,'no_browser_approval':True})
counts={'records':30,'routes_and_variants':4,'supporting_procedures':15,'observations':11,'operations':58,'measurements':750,'selected_source_crops':51,'molecular_entries':39,'material_slots':77,'stock_components':16,'product_contexts':88,'product_context_symbols':14,'new_training_tasks':0,'exact_product_structure_pairs':0}
save(O/'promotion-manifest.json',{'schema':'mattersyn.friedfeld_promotion_proposal/1','at':datetime.now(timezone.utc).isoformat(),'author':'/root','status':'frozen_metadata_overlay_pending_independent_delta_audit','source_audits':audits,'records':deltas,'counts':counts,'public_assets':public,'scope':scope,'removed_stale_quality_text':[stale],'effective_molecular_map_sha256':sha(F/'visuals/molecules-correction-v2/effective-file-map.json'),'display_map_counts':{k:sum(map(len,v.values())) for k,v in maps.items()},'pending_gates':['independent publication-projection delta audit','shared Site integration','actual integrated desktop/mobile browser review','anonymous deployment verification']})
files=[]
for directory,dirs,names in os.walk(io_path(O)):
 for name in names:
  p=Path(directory)/name;files.append({'path':p.relative_to(io_path(O)).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
files.sort(key=lambda x:x['path'])
save(O/'package-freeze.json',{'schema':'mattersyn.site_integration_proposal_freeze/1','author':'/root','at':datetime.now(timezone.utc).isoformat(),'status':'frozen_for_independent_promotion_audit','files':files,'source_audits':audits,'author_script_sha256':sha(Path(__file__))})
print(json.dumps({'freeze_sha256':sha(O/'package-freeze.json'),'counts':counts,'public_files':len(public),'site_changed':False}))
