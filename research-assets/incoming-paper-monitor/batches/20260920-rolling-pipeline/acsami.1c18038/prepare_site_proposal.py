"""Root metadata promotion of independently audited Lian records and visuals."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, re, shutil

L=Path(__file__).resolve().parent; O=L/'site-integration-proposal/v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert not O.exists(),'Preserve a frozen proposal; create a revision instead.'
audits={}
for rel in ['source-independent-audit/independent-audit-v2.json','canonical-reader-independent-audit/independent-audit-v1.json','visuals/molecules-independent-audit/independent-audit.json','visuals/apparatus-independent-audit/independent-audit.json']:
 p=L/rel;a=read(p);assert a['status']=='passed';audits[rel]=sha(p)
scope='Complete supplied eight-page main article and matched 26-page SI read and independently audited. Separate canonical/reader, molecular and apparatus audits passed. Two routes, one protocol variant, six supporting procedures and seven observation contexts remain distinct. Printed conflicts, missing crystal ZIP/video and unresolved physical specimen joins are preserved. No new training task or exact structure–recipe pair is admitted.'
removed_missing=['Distinct supplied-PDF source audit passed revision 2; canonical/reader approval remains pending.','Canonical/reader independent approval, publication and training admission are not asserted.']
records={};deltas=[]
for row in read(L/'canonical-proposal/v1/record-manifest.json')['records']:
 src=Path(row['path']);assert sha(src)==row['sha256'];r=read(src);old=copy.deepcopy(r);rid=r['record_id']
 r['collection']='reviewed_literature'
 r['reader_role']='synthesis_route' if r['record_type'] in ('literature_protocol','protocol_variant') else 'supporting_procedure' if r['record_type']=='procedure' else 'contextual_observation'
 r['quality'].update(review_status='source_reviewed',review_scope=scope)
 r['quality']['missing_fields']=[x for x in r['quality']['missing_fields'] if x not in removed_missing]
 for s in r['sources']:
  s.update(main_status='All eight supplied main pages read, visually inspected and independently audited; source and canonical checks passed.',si_status='Matched 26-page SI fully read, visually inspected and independently audited. Cited crystal ZIP and MP4 were not supplied locally; their absence is retained.',reuse_status='Source-linked facts and selected scientific crops; original article, SI files, complete text and page scans remain local.')
 assert not r['quality']['requested_tasks'] and not r['structure_assets']
 for k in set(r)-{'collection','reader_role','quality','sources'}:assert r[k]==old[k],(rid,k)
 for k in set(r['quality'])-{'review_status','review_scope','missing_fields'}:assert r['quality'][k]==old['quality'][k]
 dest=O/'records'/src.name;save(dest,r);records[rid]=r
 deltas.append({'record_id':rid,'original_path':str(src),'original_sha256':sha(src),'promoted_sha256':sha(dest),'reader_role':r['reader_role'],'scientific_values_unchanged':True})
assert len(records)==16 and sum(len(r['operations']) for r in records.values())==21
reader=read(L/'public-review-proposal/v1/lian2021.json')
reader.update(coverage_status='supplied_main_and_matched_si_review_complete',independent_audit=scope,source_review_promoted=True,publication_status='Source-reviewed contribution staged for website integration. Browser and deployment gates remain separate.',review_state='source_reviewed',training_note='No new training task is admitted. The printed bulk-crystal coordinate tables do not establish nanocrystal atomic coordinates, complete ordered hydrogen/occupancy models, exact sample–recipe joins or DFT-ready inputs.')
reader['audit_details']={'scope':scope,'audit_sha256':audits,'source_conflicts_resolved':False,'training_promotions':0}
reader['remaining_gaps']=[x for x in reader['remaining_gaps'] if x!='Independent source passage does not approve this canonical/reader proposal. Molecular, product/crystal, apparatus, browser and publication stages remain separate.']
reader['remaining_gaps'].append('Source, canonical/reader, molecular and apparatus audits passed. Bulk-coordinate display qualification, integrated browser and publication gates remain separate.')
for item in reader['recipe_inventory']:
 item['status']='source_reviewed';item['gaps']=[x for x in item.get('gaps',[]) if x not in removed_missing]
for key in ['figures','tables','schemes','equations','source_notes']:
 for item in reader[key]:item['reviewed']=True
reader['presentation_gates']={'canonical_source_audit':True,'reader_source_audit':True,'molecular_bindings':True,'apparatus_bindings':True,'exact_product_atomic_structure_binding':False,'site_integration':False,'browser_render':False,'publication':False}
assert not re.search(r'[A-Z]:[\\/]|file://',json.dumps(reader))
save(O/'reader/lian2021.json',reader)
public=[]
def asset(src,rel,kind):
 dest=O/'dist'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
 public.append({'public_path':rel,'source_path':str(src),'sha256':sha(src),'kind':kind})
assets=read(L/'original-assets-manifest.json')['assets'];assert len(assets)==53
for a in assets:
 src=Path(a['path']);assert sha(src)==a['sha256'] and a['whole_source_page'] is False
 asset(src,'assets/figures/lian2021/'+src.name,'selected_original_scientific_crop')
urls=set()
def walk(x):
 if isinstance(x,dict):
  if x.get('public_asset'):urls.add(x['public_asset'])
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(reader);assert urls=={a['public_path'] for a in public}
V=L/'visuals/molecules';registry=read(V/'registry-additions.json');bindings=read(V/'bindings-proposal.json')
for e in registry['entries']:e.update(binding_approved=True,independentScientificAudit='passed_source_scoped_molecular_and_binding_audit',published=False,eligible_training=False)
registry.update(binding_approved=True,status='independently_passed_source_references_staged_for_integration')
for rid,notes in bindings['bindingNotes'].items():
 assert rid in records
 for note in notes.values():note.update(binding_approved=True,independent_scientific_audit='Passed separate molecular/source-binding audit; metadata promotion preserves all scientific fields.')
# Empty analytical inventories must have explicit empty binding maps too.
for rid,r in records.items():
 if not r['materials']:
  bindings['recordBindings'].setdefault(rid,{})
  bindings['bindingNotes'].setdefault(rid,{})
bindings.update(binding_approved=True,status='independently_passed_source_bindings_staged_for_integration')
bindings['sourceRecordSha256']={rid:sha(O/'records'/(rid+'.json')) for rid in records}
save(O/'molecules/registry-additions.json',registry);save(O/'molecules/bindings-additions.json',bindings)
solutions=read(V/'solution-components-proposal.json');solutions['binding_approved']=True
for c in solutions['contexts']:c['binding_approved']=True
save(O/'molecules/solution-components-additions.json',solutions)
for rel,digest in read(V/'public-asset-proposal.json')['relative_asset_files'].items():
 src=V/rel;assert sha(src)==digest;asset(src,'assets/chemical-registry/'+rel,'reviewed_chemical_reference')
asset(L/'visuals/apparatus/lian2021-protocol.mjs','lian2021-protocol.mjs','independently_audited_apparatus')
maps={section:{rid:set() for rid in records} for section in ['structures','properties']}
for section in reader['reader_sections']:
 if section['id'] not in maps:continue
 for item in section['items']:
  for link in item.get('canonical_links',[]):
   bits=link['json_pointer'].strip('/').split('/')
   if bits[0]=='measurements':maps[section['id']][link['record_id']].add(records[link['record_id']]['measurements'][int(bits[1])]['id'])
for rid in records:assert not(maps['structures'][rid]&maps['properties'][rid]),rid
for section,data in maps.items():save(O/('record-'+section+'-measurements.json'),{rid:sorted(ids) for rid,ids in data.items()})
counts={'records':16,'routes_and_variants':3,'supporting_procedures':6,'observations':7,'operations':21,'measurements':sum(len(r['measurements']) for r in records.values()),'selected_source_crops':53,'molecular_entries':15,'material_slots':45,'stock_components':14,'new_training_tasks':0,'exact_product_structure_pairs':0}
save(O/'promotion-manifest.json',{'schema':'mattersyn.lian_promotion_proposal/1','at':datetime.now(timezone.utc).isoformat(),'author':'/root','status':'frozen_metadata_overlay_pending_independent_delta_audit','source_audits':audits,'records':deltas,'counts':counts,'public_assets':public,'scope':scope,'removed_stale_quality_text':removed_missing,'display_map_counts':{k:sum(map(len,v.values())) for k,v in maps.items()},'pending_gates':['independent promotion delta audit','qualified bulk-coordinate display audit','shared Site integration checks','actual integrated browser review','anonymous deployment verification']})
files=[{'path':p.relative_to(O).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(O.rglob('*')) if p.is_file()]
save(O/'package-freeze.json',{'schema':'mattersyn.site_integration_proposal_freeze/1','author':'/root','at':datetime.now(timezone.utc).isoformat(),'status':'frozen_for_independent_promotion_audit','files':files,'source_audits':audits,'author_script_sha256':sha(Path(__file__))})
print(json.dumps({'freeze_sha256':sha(O/'package-freeze.json'),'counts':counts,'public_files':len(public),'site_changed':False}))
