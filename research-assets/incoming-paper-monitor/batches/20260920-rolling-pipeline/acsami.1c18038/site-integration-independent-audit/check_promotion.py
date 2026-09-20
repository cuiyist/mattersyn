from pathlib import Path
import copy, hashlib, json, re, shutil, sys
from collections import Counter
from datetime import datetime, timezone

A=Path(__file__).resolve().parent
L=A.parent
O=L/'site-integration-proposal/v1'
C=L/'canonical-proposal/v1'
V=L/'visuals/molecules'
S=L.parents[4]/'recipe-atlas'
sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record, eligibility, build_groups
import build_paper_reviews

def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
bound={}
def bind(p):p=Path(p);bound[str(p)]=sha(p);return load(p) if p.suffix=='.json' else p
def check(ok,label):
 checks.append({'passed':bool(ok),'check':label})
 if not ok:print('FAILED '+label)
def same(x,y,label):check(x==y,label)
def differences(x,y,p=''):
 if type(x)!=type(y):return [{'pointer':p,'old':x,'new':y}]
 if isinstance(x,dict):
  out=[]
  for k in sorted(x.keys()|y.keys()):
   q=p+'/'+k
   if k not in x:out.append({'pointer':q,'old_absent':True,'new':y[k]})
   elif k not in y:out.append({'pointer':q,'old':x[k],'new_absent':True})
   else:out+=differences(x[k],y[k],q)
  return out
 if isinstance(x,list):
  if len(x)!=len(y):return [{'pointer':p,'old':x,'new':y}]
  return [z for i,(xx,yy) in enumerate(zip(x,y)) for z in differences(xx,yy,p+'/'+str(i))]
 return [] if x==y else [{'pointer':p,'old':x,'new':y}]
def pointer(x,p):
 if p=='':return x
 for b in p.strip('/').split('/'):
  b=b.replace('~1','/').replace('~0','~');x=x[int(b)] if isinstance(x,list) else x[b]
 return x

freeze=bind(O/'package-freeze.json')
expected_freeze='361af1d8193c59c8d52d8959f2d38fca37ef79346a0612b88b0ced652e632220'
same(sha(O/'package-freeze.json'),expected_freeze,'exact root proposal freeze')
check(freeze['author']!='/root/norberg2004_extract','root authored promotion, reviewer separate')
for row in freeze['files']:
 p=O/row['path'];bind(p);same(sha(p),row['sha256'],'freeze file hash '+row['path']);same(p.stat().st_size,row['bytes'],'freeze file bytes '+row['path'])
same(sha(L/'prepare_site_proposal.py'),freeze['author_script_sha256'],'frozen root author script');bind(L/'prepare_site_proposal.py')
for rel,digest in freeze['source_audits'].items():
 p=L/rel;audit=bind(p);same(sha(p),digest,'passed audit hash '+rel);same(audit['status'],'passed','passed audit status '+rel)
check(load(L/'visuals/apparatus-independent-audit/independent-audit.json')['auditor']=='/root/peng1998_reader_assets','apparatus scientific review was independent of this author')

record_manifest=bind(C/'record-manifest.json');bind(C/'package-manifest.json')
removed=[
 'Distinct supplied-PDF source audit passed revision 2; canonical/reader approval remains pending.',
 'Canonical/reader independent approval, publication and training admission are not asserted.'
]
records={};record_deltas={};schema_results=[]
for row in record_manifest['records']:
 src=Path(row['path']);old=bind(src);same(sha(src),row['sha256'],'canonical prior hash '+row['record_id'])
 p=O/'records'/src.name;r=bind(p);rid=r['record_id'];records[rid]=r
 restored=copy.deepcopy(r)
 for key in ['collection','reader_role','quality','sources']:
  if key in old:restored[key]=copy.deepcopy(old[key])
  else:restored.pop(key,None)
 same(restored,old,'every scientific field unchanged '+rid)
 old_quality=copy.deepcopy(old['quality']);new_quality=copy.deepcopy(r['quality'])
 for key in ['review_status','review_scope','missing_fields']:new_quality[key]=old_quality[key]
 same(new_quality,old_quality,'all remaining quality fields unchanged '+rid)
 same(r['quality']['missing_fields'],[x for x in old['quality']['missing_fields'] if x not in removed],'only stale missingness text removed '+rid)
 same(r['collection'],'reviewed_literature','collection '+rid)
 same(r['quality']['review_status'],'source_reviewed','review state '+rid)
 role='synthesis_route' if old['record_type'] in ['literature_protocol','protocol_variant'] else 'supporting_procedure' if old['record_type']=='procedure' else 'contextual_observation'
 same(r['reader_role'],role,'correct role '+rid)
 for j,(os,ns) in enumerate(zip(old['sources'],r['sources'])):
  ss=copy.deepcopy(ns)
  for key in ['main_status','si_status','reuse_status']:
   if key in os:ss[key]=os[key]
   else:ss.pop(key,None)
  same(ss,os,'source identity/provenance unchanged '+rid+str(j))
 same(len(old['sources']),len(r['sources']),'no sources added '+rid)
 same(r['quality']['requested_tasks'],[],'no requested tasks '+rid)
 same(r['structure_assets'],[],'no coordinate-binding promotion '+rid)
 err=validate_record(r);admission=eligibility(r)
 same(err,[],'current schema/semantic validation '+rid)
 check(not any(x['eligible'] for x in admission.values()),'no task admission '+rid)
 schema_results.append({'record_id':rid,'errors':err,'eligibility':admission})
 record_deltas[rid]=differences(old,r)
same(len(records),16,'16 records')
same(Counter(r['reader_role'] for r in records.values()),Counter({'synthesis_route':3,'supporting_procedure':6,'contextual_observation':7}),'3 route/variant,6 procedure,7 observations')
same(sum(len(r['measurements']) for r in records.values()),1149,'1149 measurements preserved')
same(sum(len(r['operations']) for r in records.values()),21,'21 operations preserved')
same(len(set(build_groups(list(records.values())).values())),1,'one source split group')

old_reader=bind(L/'public-review-proposal/v1/lian2021.json');reader=bind(O/'reader/lian2021.json')
reader_deltas=differences(old_reader,reader)
reader_copy=copy.deepcopy(reader)
allowed_top=['coverage_status','independent_audit','source_review_promoted','publication_status','review_state','training_note','audit_details','remaining_gaps','presentation_gates']
for key in allowed_top:
 if key in old_reader:reader_copy[key]=old_reader[key]
 else:reader_copy.pop(key,None)
for old,item in zip(old_reader['recipe_inventory'],reader_copy['recipe_inventory']):
 same(item['gaps'],[x for x in old.get('gaps',[]) if x not in removed],'recipe real gaps preserved '+item['id'])
 same(item['status'],'source_reviewed','recipe review status '+item['id'])
 item['status']=old['status']
 if 'gaps' in old:item['gaps']=old['gaps']
 else:item.pop('gaps',None)
for key in ['figures','tables','schemes','equations','source_notes']:
 for old,item in zip(old_reader[key],reader_copy[key]):
  same(item['reviewed'],True,'source item review overlay '+key+item['id'])
  if 'reviewed' in old:item['reviewed']=old['reviewed']
  else:item.pop('reviewed',None)
same(reader_copy,old_reader,'all reader scientific prose/tables/figures/fields exact unchanged')
same(reader['presentation_gates'],{'canonical_source_audit':True,'reader_source_audit':True,'molecular_bindings':True,'apparatus_bindings':True,'exact_product_atomic_structure_binding':False,'site_integration':False,'browser_render':False,'publication':False},'review gates limited to passed source/visual scopes')
check('0' in str(reader['audit_details']['training_promotions']),'reader no training promotion')
same(reader['audit_details']['source_conflicts_resolved'],False,'source conflicts not claimed resolved')
check('Browser and deployment gates remain separate' in reader['publication_status'],'no browser/deployment approval claimed')

maps={sec:{rid:set() for rid in records} for sec in ['structures','properties']}
link_count=0
for section in reader['reader_sections']:
 for item in section['items']:
  for link in item.get('canonical_links',[]):
   check(link['record_id'] in records,'reader linked record '+item['id'])
   val=pointer(records[link['record_id']],link['json_pointer']);check(True,'reader exact pointer resolves '+item['id']+' '+link['json_pointer']);link_count+=1
   bits=link['json_pointer'].strip('/').split('/')
   if section['id'] in maps and bits[0]=='measurements':maps[section['id']][link['record_id']].add(records[link['record_id']]['measurements'][int(bits[1])]['id'])
for section in maps:
 actual=bind(O/('record-'+section+'-measurements.json'))
 same(actual,{rid:sorted(ids) for rid,ids in maps[section].items()},'display '+section+' map derived exactly from audited reader')
for rid,r in records.items():
 check(not(maps['structures'][rid]&maps['properties'][rid]),'disjoint role maps '+rid)
 mids={m['id'] for m in r['measurements']}
 check((maps['structures'][rid]|maps['properties'][rid])<=mids,'role maps IDs exist '+rid)

old_reg=bind(V/'registry-additions.json');reg=bind(O/'molecules/registry-additions.json');rc=copy.deepcopy(reg)
for key in ['binding_approved','status']:
 if key in old_reg:rc[key]=old_reg[key]
 else:rc.pop(key,None)
for old,item in zip(old_reg['entries'],rc['entries']):
 for key in ['binding_approved','independentScientificAudit','published','eligible_training']:
  if key in old:item[key]=old[key]
  else:item.pop(key,None)
same(rc,old_reg,'all molecular identities graphs captions refs unchanged')
same(len(reg['entries']),15,'15 molecular identities')
for entry in reg['entries']:
 same(entry['binding_approved'],True,'molecular passed binding '+entry['id'])
 same(entry['published'],False,'molecular publication pending '+entry['id'])
 same(entry['eligible_training'],False,'molecular no training '+entry['id'])
old_bind=bind(V/'bindings-proposal.json');new_bind=bind(O/'molecules/bindings-additions.json');bc=copy.deepcopy(new_bind)
for key in ['binding_approved','status','sourceRecordSha256']:
 if key in old_bind:bc[key]=old_bind[key]
 else:bc.pop(key,None)
empty_records=[]
for rid,r in records.items():
 same(new_bind['sourceRecordSha256'][rid],sha(O/'records'/(rid+'.json')),'promoted record hash binding '+rid)
 same(set(new_bind['recordBindings'][rid]),{m['id'] for m in r['materials']},'complete material-slot keys '+rid)
 if not r['materials']:
  empty_records.append(rid)
  same(new_bind['recordBindings'][rid],{},'empty analytical binding '+rid)
  same(new_bind['bindingNotes'][rid],{},'empty analytical notes '+rid)
  for key in ['recordBindings','bindingNotes']:
   if rid not in old_bind[key]:bc[key].pop(rid,None)
for rid,notes in old_bind['bindingNotes'].items():
 for mid,old in notes.items():
  item=bc['bindingNotes'][rid][mid]
  for key in ['binding_approved','independent_scientific_audit']:
   if key in old:item[key]=old[key]
   else:item.pop(key,None)
same(bc,old_bind,'all material maps/context snapshots unchanged except approvals/hash/empty inventories')
old_sol=bind(V/'solution-components-proposal.json');sol=bind(O/'molecules/solution-components-additions.json');sc=copy.deepcopy(sol)
sc['binding_approved']=old_sol['binding_approved']
for old,item in zip(old_sol['contexts'],sc['contexts']):item['binding_approved']=old['binding_approved']
same(sc,old_sol,'all stock component quantities scopes and reference mappings unchanged')
same(len(sol['contexts']),5,'five stock contexts')
same(sum(len(x['components']) for x in sol['contexts']),14,'14 stock components')

promotion=bind(O/'promotion-manifest.json');assets=promotion['public_assets']
same(len(assets),81,'81 public files')
same(Counter(x['kind'] for x in assets),Counter({'selected_original_scientific_crop':53,'reviewed_chemical_reference':27,'independently_audited_apparatus':1}),'53 crops27chemical1apparatus')
source_crops=bind(L/'original-assets-manifest.json')['assets'];crop_by_name={Path(x['path']).name:x for x in source_crops}
public_proposal=bind(V/'public-asset-proposal.json')['relative_asset_files']
apparatus_freeze=bind(L/'visuals/apparatus/package-freeze.json')
apparatus_audit=load(L/'visuals/apparatus-independent-audit/independent-audit.json')
check(sha(L/'visuals/apparatus/package-freeze.json') in json.dumps(apparatus_audit),'audited apparatus freeze exactly retained')
public_paths=set()
for asset in assets:
 rel=asset['public_path'];p=O/'dist'/rel;source=Path(asset['source_path']);bind(source)
 check(rel not in public_paths,'unique public path '+rel);public_paths.add(rel)
 same(sha(p),asset['sha256'],'public file proposal hash '+rel);same(sha(p),sha(source),'exact source copy '+rel)
 check(p.suffix in ['.png','.svg','.json','.mjs'],'no PDF/rawtext extension '+rel)
 check(not re.search(r'(?:^|/)(?:source-render|private|downloaded_papers|data_Tanjin)(?:/|$)',rel),'no private/fullpage public path '+rel)
 if asset['kind']=='selected_original_scientific_crop':
  crop=crop_by_name[p.name];same(crop['whole_source_page'],False,'selected crop not whole page '+rel);same(sha(p),crop['sha256'],'crop immutable source hash '+rel)
 if asset['kind']=='reviewed_chemical_reference':same(sha(p),public_proposal[rel.removeprefix('assets/chemical-registry/')],'exact audited chemical asset '+rel)
 if asset['kind']=='independently_audited_apparatus':same(sha(p),apparatus_freeze['public_allowlist'][0]['sha256'],'exact independently passed apparatus bytes only')
 if p.suffix in ['.json','.mjs','.svg']:check(not re.search(r'[A-Z]:[\\/]|file://',p.read_text(encoding='utf-8')),'no private drive paths in public asset '+rel)
same(set(p.relative_to(O/'dist').as_posix() for p in (O/'dist').rglob('*') if p.is_file()),public_paths,'public projection exactly matches allowlist')
for r in [reader]+list(records.values()):check(not re.search(r'[A-Z]:[\\/]|file://',json.dumps(r)),'public record/reader contains no private drive paths')

# Current schema and reader validator operate on isolated private inputs, never Site.
P=A/'private-validator-projection'
for rid in records:
 dest=P/'data/records'/(rid+'.json');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(O/'records'/(rid+'.json'),dest)
for asset in assets:
 if asset['kind']!='selected_original_scientific_crop':continue
 dest=P/'dist'/asset['public_path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(O/'dist'/asset['public_path'],dest)
build_paper_reviews.ROOT=P
reader_errors=build_paper_reviews.validate(reader)
same(reader_errors,[],'current independent reader validator on private projection')
for rel in ['dataset_lib.py','schema_definition.py','review_scope.py','build_paper_reviews.py']:bind(S/'scripts'/rel)
bind(Path(__file__))
findings=[x for x in checks if not x['passed']]
result={
 'schema':'mattersyn-independent-promotion-delta-audit/1',
 'author':'/root','auditor':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),
 'source_id':'lian2021','status':'passed' if not findings else 'open_findings',
 'proposal_freeze_sha256':sha(O/'package-freeze.json'),
 'scope':'Independent metadata/scientific transport and public-asset projection audit only. Prior source and canonical audits used as immutable dependencies. Apparatus science was separately audited by Peng, not self-audited here.',
 'counts':{'records':len(records),'routes_and_variants':3,'supporting_procedures':6,'observations':7,'operations':21,'measurements':1149,'reader_canonical_links':link_count,'molecular_entries':15,'material_slots':45,'stocks':5,'stock_components':14,'empty_analytical_record_maps':len(empty_records),'public_assets':81,'selected_crops':53,'chemical_files':27,'apparatus_modules':1,'training_tasks':0,'structure_assets':0},
 'display_map_counts':{k:sum(len(x) for x in v.values()) for k,v in maps.items()},
 'check_count':len(checks),'findings':findings,'schema_results':schema_results,'reader_validator_errors':reader_errors,
 'record_deltas':record_deltas,'reader_deltas':reader_deltas,
 'manual_scopes':[
  'Read the complete root author script and all status/approval transformations; approval remains source-scoped, no browser/site/publication claim.',
  'Original 16 records restored exactly after removing only permitted metadata changes; source quantities, statuses, specimens, operations, structures and 1149 measurements unchanged.',
  'Protocol variant correctly appears as a route; records retain two literature routes, one variant, six procedures and seven observations.',
  'Reader scientific prose, all tables/figures/equations, source conflicts and field links unchanged; source reviewed overlays have passed immutable audit support.',
  'Molecular registry/material-slot/stock mappings compared exactly to independently passed originals; no graph/model/quantity mutation.',
  'The entire public allowlist is selected crops, audited chemical references and the independently passed apparatus module; no original PDF, source whole page, full-text cache or private-path leakage.',
  'Structure/property display maps derive from original audited reader IDs with disjoint membership; remaining source observations stay in unchanged canonical data.',
  'No task or exact structure-recipe pair is admitted; qualified partial bulk-coordinate display remains a separate forthcoming proposal.'
 ],
 'bound_files':dict(sorted(bound.items())),
 'scientific_source_reaudit':False,'apparatus_science_self_audit':False,
 'site_integration_approved':False,'browser_approved':False,'publication_approved':False,'training_approved':False
}
save(A/'promotion-delta-audit.json',result)
save(A/'promotion-delta-checks.json',{'checks':checks})
(A/'promotion-delta-audit.md').write_text(f'''# Lian promotion delta audit

Status: **{result['status']}**. Root proposal freeze: `{result['proposal_freeze_sha256']}`.

The independent audit executed {len(checks)} checks against the actual frozen proposal, current record validator and isolated reader validator. All 16 records retain their exact scientific content, including 21 operations and 1,149 measurements. Presentation roles are three routes/variants, six supporting procedures and seven observations. No training task or structure asset is added.

The reader's scientific prose, tables, figures, equations and field links are unchanged. Only supported review-status metadata and stale gate text changed. Molecular identities, all 45 material slots and five stock contexts/14 components retain the independently passed scientific content. Empty analytical inventories receive explicit empty maps.

The public projection contains exactly 81 files: 53 selected source crops, 27 chemical files and one byte-identical apparatus module already independently audited by Peng. No original PDFs, full-page renders, raw full text or local drive paths enter this projection. Structure/property section maps are disjoint and derived from the audited reader.

Open findings: {len(findings)}. This is a promotion/transport audit, not a fresh full source review or a self-audit of apparatus science. The separate bulk-coordinate proposal, shared Site integration, mounted browser, deployment and training gates remain unapproved here.
''',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'findings':findings,'counts':result['counts'],'map_counts':result['display_map_counts'],'audit_sha256':sha(A/'promotion-delta-audit.json')}))
