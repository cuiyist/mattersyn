"""Root publication projection; requires all source and visualization audits."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,re,sys,os
J=Path(__file__).resolve().parent;C=J/'canonical-proposal/v1';O=J/'site-integration-proposal/v1';S=J.parents[4]/'recipe-atlas'
sys.path.insert(0,str(J.parents[4]/'research-assets'))
from sync_github_public import io_path
read=lambda p:json.loads(io_path(p).read_text('utf8'))
sha=lambda p:hashlib.sha256(io_path(p).read_bytes()).hexdigest()
def save(p,x):
 p=io_path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
assert not (O/'package-freeze.json').exists()
assert not O.exists() or (O/'FAILED_ATTEMPT.json').exists()
audits={}
for rel in ['source-independent-audit/independent-audit-v2.json','canonical-independent-audit/independent-audit-v1.json','visuals/molecules-independent-audit/independent-audit.json','apparatus-independent-audit/independent-audit.json','product-independent-audit/independent-audit.json']:
 p=J/rel;a=read(p);assert a['status']=='passed' and not a.get('open_findings'),rel;audits[rel]=sha(p)
scope='All nine supplied main pages and 11 matched SI pages read and independently audited. The canonical records and reader, molecular/stock references, 21 operation illustrations and symbolic source sample contexts passed separate scoped audits. One synthesis route, seven supporting preparation/acquisition procedures and eleven observation records remain distinct. Nine paired comparison contexts do not establish independent replicate counts or shared physical aliquots. Source inconsistencies and missing conditions remain explicit. No current QD atomic coordinates or exact structure–recipe training pair is admitted.'
records={};deltas=[]
for row in read(C/'record-manifest.json')['records']:
 src=Path(row['path']);assert sha(src)==row['sha256'];r=read(src);old=copy.deepcopy(r);rid=r['record_id']
 r['collection']='reviewed_literature';r['reader_role']='synthesis_route' if r['record_type'] in ('literature_protocol','protocol_variant') else 'supporting_procedure' if r['record_type']=='procedure' else 'contextual_observation'
 r['quality'].update(review_status='source_reviewed',review_scope=scope)
 for source in r['sources']:
  source.update(main_status='All nine supplied main pages read, visually inspected and independently audited; canonical and reader checks passed.',si_status='All 11 matched SI pages read, visually inspected and independently audited; title, authors and contents verify the pairing.',reuse_status='Source-linked facts and selected scientific crops; original article, SI, complete text and full-page scans remain local.')
 assert not r['quality']['requested_tasks'] and not r['structure_assets']
 for k in set(old)-{'collection','reader_role','quality','sources'}:assert r[k]==old[k],(rid,k)
 for k in set(old['quality'])-{'review_status','review_scope'}:assert r['quality'][k]==old['quality'][k]
 dest=O/'records'/src.name;save(dest,r);records[rid]=r
 deltas.append({'record_id':rid,'original_path':str(src),'original_sha256':sha(src),'promoted_sha256':sha(dest),'reader_role':r['reader_role'],'scientific_values_unchanged':True})
assert len(records)==19 and sum(len(r['operations']) for r in records.values())==21
reader=read(C/'reader/sasongko2025.json')
reader.update(coverage_status='supplied_main_and_si_review_complete',independent_audit=scope,source_review_promoted=True,publication_status='Source-reviewed contribution staged for integration; browser and deployment remain separate.',review_state='source_reviewed',training_note='No new training task or exact structure–recipe pair is admitted. Quoted literature cells, conceptual phase diagrams and local lattice-fringe annotations are not refined atomic coordinates of the current QDs. Source-scoped comparison labels do not establish cross-technique physical aliquot identity.')
reader['audit_details']={'scope':scope,'audit_sha256':audits,'source_conflicts_resolved':False,'training_promotions':0}
for item in reader['recipe_inventory']:item['status']='source_reviewed'
for key in ['figures','tables','schemes','equations','source_notes']:
 for item in reader[key]:item['reviewed']=True
reader['presentation_gates']={'canonical_source_audit':True,'reader_source_audit':True,'molecules':True,'apparatus':True,'products':True,'exact_product_atomic_structure_binding':False,'site_integration':False,'browser_render':False,'publication':False}
assert not re.search(r'[A-Z]:[\\/]|file://',json.dumps(reader));save(O/'reader/sasongko2025.json',reader)
public=[]
def asset(src,rel,kind):
 dest=io_path(O/'dist'/rel);dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():assert sha(dest)==sha(src)
 else:dest.write_bytes(io_path(src).read_bytes())
 if not any(x['public_path']==rel for x in public):public.append({'public_path':rel,'source_path':str(src),'sha256':sha(src),'kind':kind})
for a in read(J/'original-assets-manifest.json')['assets']:
 src=Path(a['path']);assert sha(src)==a['sha256'] and a['contains_complete_source_page'] is False
 asset(src,'assets/figures/sasongko2025/'+src.name,'selected_original_scientific_crop')
assert len(public)==17
V=J/'visuals/molecules'
for a in read(V/'effective-public-assets.json')['assets']:
 src=Path(a['path']);assert sha(src)==a['sha256'];asset(src,a['public_path'],a.get('kind','reviewed_chemical_reference'))
registry=read(V/'registry-additions.json')
for e in registry['entries']:e.update(binding_approved=True,independentScientificAudit='passed_source_scoped_molecular_and_stock_audit',published=False,eligible_training=False)
registry.update(binding_approved=True,status='independently_passed_source_references_staged_for_integration')
bindings=read(V/'bindings-proposal.json')
for rid,notes in bindings['bindingNotes'].items():
 assert rid in records
 for note in notes.values():note.update(binding_approved=True,independent_scientific_audit='Separate molecular and exact stock/material binding audit passed; scientific fields unchanged.')
for rid,r in records.items():
 if not r['materials']:bindings['recordBindings'].setdefault(rid,{});bindings['bindingNotes'].setdefault(rid,{})
bindings.update(binding_approved=True,status='independently_passed_source_bindings_staged_for_integration')
bindings['sourceRecordSha256']={rid:sha(O/'records'/(rid+'.json')) for rid in records}
save(O/'molecules/registry-additions.json',registry);save(O/'molecules/bindings-additions.json',bindings)
solutions=read(V/'solution-components-proposal.json');solutions['binding_approved']=True
for c in solutions['contexts']:c['binding_approved']=True
save(O/'molecules/solution-components-additions.json',solutions)
save(O/'molecules/stock-illustration-proposal.json',read(V/'stock-illustration-proposal.json'))
asset(J/'visuals/apparatus/sasongko2025-protocol.mjs','sasongko2025-protocol.mjs','independently_audited_apparatus')
# Product author exports the same existing recordContexts/sourceNotices interface.
Q=J/'visuals/products';products=read(Q/'public-product-contexts-proposal.json');preg=read(Q/'registry-additions.json')
for rows in products['recordContexts'].values():
 for row in rows:row['binding_approved']=True
product_assets=read(Q/'public-assets-proposal.json')['assets']
for a in product_assets:
 src=Path(a['path']);assert sha(src)==a['sha256'];asset(src,a['public_path'],'reviewed_symbolic_product_context')
for e in preg['entries']:
 a=next(a for a in product_assets if a['entry_id']==e['id']);assert a['sha256']==e['assetHashes']['svgPath']
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
for a in public:
 if a['kind']!='selected_original_scientific_crop':continue
 p=io_path(fixture/'dist'/a['public_path']);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(io_path(O/'dist'/a['public_path']).read_bytes())
consumer.ROOT=fixture;errors=consumer.validate(reader);assert not errors,errors
save(O/'actual-reader-validator-check.json',{'status':'passed','consumer_path':str(S/'scripts/build_paper_reviews.py'),'consumer_sha256':sha(S/'scripts/build_paper_reviews.py'),'errors':errors,'no_browser_approval':True})
counts={'records':19,'routes_and_variants':1,'supporting_procedures':7,'observations':11,'operations':21,'measurements':sum(len(r['measurements']) for r in records.values()),'selected_source_crops':17,'molecular_entries':13,'material_slots':26,'stock_instances':5,'stock_components':12,'named_source_contexts':33,'product_contexts':sum(map(len,products['recordContexts'].values())),'product_context_symbols':len(preg['entries']),'new_training_tasks':0,'exact_product_structure_pairs':0}
save(O/'promotion-manifest.json',{'schema':'mattersyn.sasongko_promotion_proposal/1','at':datetime.now(timezone.utc).isoformat(),'author':'/root','status':'frozen_metadata_overlay_pending_independent_delta_audit','source_audits':audits,'records':deltas,'counts':counts,'public_assets':public,'scope':scope,'display_map_counts':{k:sum(map(len,v.values())) for k,v in maps.items()},'pending_gates':['independent publication-projection delta audit','shared Site integration','actual desktop/mobile browser review','anonymous deployment verification']})
files=[]
for directory,dirs,names in os.walk(io_path(O)):
 for name in names:
  p=Path(directory)/name;files.append({'path':p.relative_to(io_path(O)).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
save(O/'package-freeze.json',{'schema':'mattersyn.site_integration_proposal_freeze/1','author':'/root','at':datetime.now(timezone.utc).isoformat(),'status':'frozen_for_independent_promotion_audit','files':sorted(files,key=lambda x:x['path']),'source_audits':audits,'author_script_sha256':sha(Path(__file__))})
print(json.dumps({'freeze_sha256':sha(O/'package-freeze.json'),'counts':counts,'public_files':len(public),'site_changed':False}))
