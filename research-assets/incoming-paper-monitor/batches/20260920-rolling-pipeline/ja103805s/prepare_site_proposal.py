"""Root-authored, metadata-only Evans promotion; no shared Site mutation."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,re,shutil
E=Path(__file__).resolve().parent;O=E/'site-integration-proposal/v1';O.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert not (O/'package-freeze.json').exists(),'Preserve frozen proposal; create a revision instead.'
audits={}
for rel in ['source-scientific-audit.json','proposal-independent-audit/independent-audit-v3.json','visuals/molecules-independent-audit/independent-audit-v2.json','visuals/apparatus-independent-audit/independent-audit-v1.json']:
 p=E/rel;assert read(p)['status'] in {'passed','passed_independent_source_scientific_audit_revision_2'},rel;audits[rel]=sha(p)
scope='Complete supplied 3-page main article, matched 21-page SI and molecular-species-9 CIF read and independently audited. Separate canonical/reader, molecular and apparatus audits passed. Three QD/MSC synthesis families, supporting procedures and analytical contexts retain separate identities; record IDs are not replicate counts. Source discrepancies and unspecified sample joins remain explicit. No QD atomic coordinates or training eligibility is inferred.'
pending='Canonical independent scientific audit is pending; the source audit passed separately.'
routes={'evans-2010-pbse-msc-family','evans-2010-pbse-qd','evans-2010-cdse-qd'}
manifest=read(E/'canonical-proposal/v3/record-manifest.json');deltas=[];records={}
for row in manifest['records']:
 src=Path(row['path']);assert sha(src)==row['sha256'];r=read(src);old=copy.deepcopy(r);rid=r['record_id']
 r['collection']='reviewed_literature';r['reader_role']='synthesis_route' if rid in routes else 'supporting_procedure' if r['record_type']=='procedure' else 'contextual_observation'
 r['quality'].update(review_status='source_reviewed',review_scope=scope)
 r['quality']['missing_fields']=[x for x in r['quality']['missing_fields'] if x!=pending]
 for s in r['sources']:
  s.update(main_status='Complete supplied three-page main article read, visually inspected and independently audited with canonical/source checks.',si_status='Matched21-page SI and species9 molecular CIF fully read and independently audited; source conflicts retained.',reuse_status='Source-linked factual extraction and selected scientific crops; original article, SI files, complete text and page scans remain local.')
 assert not r['quality']['requested_tasks']
 for key in set(r)-{'collection','reader_role','quality','sources'}:assert r[key]==old[key],(rid,key)
 for key in set(r['quality'])-{'review_status','review_scope','missing_fields'}:assert r['quality'][key]==old['quality'][key]
 dst=O/'records'/src.name;save(dst,r);records[rid]=r
 deltas.append({'record_id':rid,'original_path':str(src),'original_sha256':sha(src),'promoted_sha256':sha(dst),'reader_role':r['reader_role'],'scientific_values_unchanged':True})
assert len(records)==32 and sum(len(r['operations']) for r in records.values())==46
reader=read(E/'public-review-proposal/v3/evans2010.json')
reader.update(coverage_status='supplied_main_and_matched_si_review_complete',independent_audit=scope,source_review_promoted=True,publication_status='Source-reviewed contribution staged for website integration. Browser, integration and deployment gates are separate.',review_state='source_reviewed',training_note='No new training task is admitted. The supplied atomic coordinates are molecular species9; they do not describe CdSe or PbSe quantum dots. Context links are not physical specimen joins.')
reader['audit_details']={'scope':scope,'audit_sha256':audits,'source_conflicts_resolved':False,'training_promotions':0}
reader['remaining_gaps']=[x for x in reader['remaining_gaps'] if x!=pending]
for item in reader['recipe_inventory']:
 item['status']='source_reviewed';item['gaps']=[x for x in item.get('gaps',[]) if x!=pending]
for k in ['figures','tables','schemes','equations','source_notes']:
 for item in reader[k]:item['reviewed']=True
reader['presentation_gates']={'canonical_source_audit':True,'reader_source_audit':True,'molecular_bindings':True,'apparatus_bindings':True,'exact_qd_atomic_structure_binding':False,'site_integration':False,'browser_render':False,'publication':False}
assert not re.search(r'[A-Z]:[\\/]|file://',json.dumps(reader))
save(O/'reader/evans2010.json',reader)
assets=read(E/'selected-original-assets.json')['assets'];assetmap={a['id']:a for a in assets};public=[]
assert len(assets)==25
for a in assets:
 src=Path(a['path']);assert sha(src)==a['sha256'];rel='assets/figures/evans2010/'+src.name
 dst=O/'dist'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 public.append({'public_path':rel,'source_path':str(src),'sha256':sha(src),'kind':'selected_original_scientific_crop'})
urls=set()
def walk(x):
 if isinstance(x,dict):
  if x.get('public_asset'):urls.add(x['public_asset'])
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(reader);assert urls=={r['public_path'] for r in public}
V=E/'visuals/molecules';registry=read(V/'registry-additions.json');bindings=read(V/'revision-2/bindings-proposal.json')
for entry in registry['entries']:
 entry.update(binding_approved=True,independentScientificAudit='passed_source_scoped_molecular_and_binding_audit',published=False,eligible_training=False)
for rid,notes in bindings['bindingNotes'].items():
 assert rid in records
 for note in notes.values():note.update(binding_approved=True,independent_scientific_audit='Passed separate source-scoped molecular and binding audit; canonical scientific fields unchanged by publication promotion.')
bindings.update(binding_approved=True,status='independently_passed_source_bindings_staged_for_integration')
bindings['sourceRecordSha256']={rid:sha(O/'records'/(rid+'.json')) for rid in records}
registry['status']='independently_passed_source_references_staged_for_integration'
save(O/'molecules/registry-additions.json',registry);save(O/'molecules/bindings-additions.json',bindings)
for a in read(V/'public-asset-proposal.json')['assets']:
 src=Path(a['private_path']);assert sha(src)==a['sha256'];rel='assets/chemical-registry/'+a['registry_relative_path'];dst=O/'dist'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 public.append({'public_path':rel,'source_path':str(src),'sha256':sha(src),'kind':'reviewed_chemical_reference'})
src=E/'visuals/apparatus/v1/evans2010-protocol.mjs';shutil.copy2(src,O/'dist/evans2010-protocol.mjs');public.append({'public_path':'evans2010-protocol.mjs','source_path':str(src),'sha256':sha(src),'kind':'independently_audited_apparatus'})
save(O/'promotion-manifest.json',{'schema':'mattersyn.evans_promotion_proposal/1','at':datetime.now(timezone.utc).isoformat(),'author':'/root','status':'frozen_metadata_overlay_pending_independent_integration_delta_audit','source_audits':audits,'records':deltas,'counts':{'records':32,'routes':3,'supporting_procedures':13,'observations':16,'operations':46,'selected_source_crops':25,'molecular_entries':50,'material_slots':123,'stock_components':41,'new_training_tasks':0,'exact_qd_structure_pairs':0},'public_assets':public,'scope':scope,'pending_gates':['independent metadata/presentation integration delta audit','shared Site import and checks','actual integrated browser review','anonymous deployment verification']})
files=[{'path':p.relative_to(O).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(O.rglob('*')) if p.is_file()]
save(O/'package-freeze.json',{'schema':'mattersyn.site_integration_proposal_freeze/1','author':'/root','at':datetime.now(timezone.utc).isoformat(),'status':'frozen_for_independent_promotion_audit','files':files,'source_audits':audits,'author_script_sha256':sha(Path(__file__))})
print(json.dumps({'freeze':str(O/'package-freeze.json'),'sha256':sha(O/'package-freeze.json'),'records':len(records),'public_files':len(public),'site_changed':False}))
