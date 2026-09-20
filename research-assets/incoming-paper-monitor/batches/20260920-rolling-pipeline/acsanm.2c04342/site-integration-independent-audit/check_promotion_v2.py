"""Independent frozen promotion comparison. Writes private audit outputs only."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import copy, hashlib, json, re, shutil, sys, argparse
A=Path(__file__).resolve().parent; G=A.parent; P=G/'site-integration-proposal/v2'
S=Path('[local path redacted]'); V=G/'visuals/molecules'
sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record, eligibility
import build_paper_reviews
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[];bound={}
def check(ok,label):
 checks.append({'passed':bool(ok),'check':label})
 if not ok:print('FAILED '+label)
def same(a,b,label):check(a==b,label)
def bind(p):
 p=Path(p);bound[str(p)]=sha(p)
 return load(p) if p.suffix=='.json' else p
def restore(dst,src,keys):
 for key in keys:
  if key in src:dst[key]=copy.deepcopy(src[key])
  else:dst.pop(key,None)
def diff(a,b,p=''):
 if type(a)!=type(b):return [{'pointer':p,'old':a,'new':b}]
 if isinstance(a,dict):
  out=[]
  for k in sorted(a.keys()|b.keys()):
   q=p+'/'+k.replace('~','~0').replace('/','~1')
   if k not in a:out.append({'pointer':q,'old_absent':True,'new':b[k]})
   elif k not in b:out.append({'pointer':q,'old':a[k],'new_absent':True})
   else:out+=diff(a[k],b[k],q)
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return [{'pointer':p,'old':a,'new':b}]
  return [z for i,(x,y) in enumerate(zip(a,b)) for z in diff(x,y,p+'/'+str(i))]
 return [] if a==b else [{'pointer':p,'old':a,'new':b}]
def pointer(x,p):
 if p=='':return x
 for k in p.strip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~');x=x[int(k)] if isinstance(x,list) else x[k]
 return x
ap=argparse.ArgumentParser();ap.add_argument('--expected-freeze',required=True);args=ap.parse_args()
f=bind(P/'package-freeze.json')
same(sha(P/'package-freeze.json'),args.expected_freeze,'exact promotion freeze')
same(f['author'],'/root','separate root author')
for row in f['files']:
 p=P/row['path'];bind(p);same(sha(p),row['sha256'],'frozen hash '+row['path']);same(p.stat().st_size,row['bytes'],'frozen bytes '+row['path'])
same(sha(bind(G/'revise_promotion_v2.py')),f['author_script_sha256'],'author script frozen')
prior=bind(G/'site-integration-proposal/v1/package-freeze.json')
same(sha(G/'site-integration-proposal/v1/package-freeze.json'),'23aac54bd96ab821d9f12c5398823340ec07ef3b94995fcf2d6e535aa25556ee','prior freeze preserved')
for row in prior['files']:
 priorpath=G/'site-integration-proposal/v1'/row['path'];bind(priorpath);same(sha(priorpath),row['sha256'],'v1 original unchanged '+row['path'])
 newpath=P/row['path']
 if row['path']!='reader/matuhina2023.json':same(sha(newpath),sha(priorpath),'v2 same file '+row['path'])
a=readprior=load(G/'site-integration-proposal/v1/reader/matuhina2023.json');b=load(P/'reader/matuhina2023.json')
same(diff(a,b),[{'pointer':'/review_scope','old':'complete_supplied_main_and_matched_si','new':'supplied_main_and_matched_si'}],'EXACT one reader metadata correction')
bind(G/'site-integration-proposal/promotion-v2-delta.json')
for rel,digest in f['source_audits'].items():
 audit=bind(G/rel);same(sha(G/rel),digest,'audit hash '+rel);same(audit['status'],'passed','prior audit passed '+rel)
 for path,h in (audit.get('bound_files',{}).items() if isinstance(audit.get('bound_files',{}),dict) else [(z['path'],z['sha256']) for z in audit['bound_files']]):
  fp=Path(path) if Path(path).is_absolute() else G/path
  bind(fp);same(sha(fp),h,'audit dependency unchanged '+str(path))
baseline=bind(A/'independent-baseline.json')
same(baseline['record_count'],586,'independent old-record count')
rm=bind(G/'canonical-proposal/v1/record-manifest.json');pm=bind(P/'promotion-manifest.json')
removed=['The supplied 13-page main and 13-page SI extraction passed distinct source audit. Canonical and reader independent review remain pending. Historical pending flags in immutable source payloads describe the author-freeze stage.']
same(pm['removed_stale_quality_text'],removed,'only known historical gate removed')
records={};deltas={};schema=[]
for row in rm['records']:
 old=bind(row['path']);same(sha(row['path']),row['sha256'],'source record freeze '+row['record_id'])
 rid=row['record_id'];r=bind(P/'records'/(rid+'.json'));records[rid]=r
 restored=copy.deepcopy(r);restore(restored,old,['collection','reader_role','quality','sources'])
 same(restored,old,'ALL scientific record arrays unchanged '+rid)
 q=copy.deepcopy(r['quality']);restore(q,old['quality'],['review_status','review_scope','missing_fields']);same(q,old['quality'],'other quality fields unchanged '+rid)
 same(r['quality']['missing_fields'],[x for x in old['quality']['missing_fields'] if x not in removed],'all real gaps retained '+rid)
 same(r['collection'],'reviewed_literature','collection '+rid);same(r['quality']['review_status'],'source_reviewed','review state '+rid)
 expected='synthesis_route' if old['record_type'] in ('literature_protocol','protocol_variant') else 'supporting_procedure' if old['record_type']=='procedure' else 'contextual_observation'
 same(r['reader_role'],expected,'role '+rid)
 same(len(r['sources']),len(old['sources']),'source count '+rid)
 for i,(os,ns) in enumerate(zip(old['sources'],r['sources'])):
  ss=copy.deepcopy(ns);restore(ss,os,['main_status','si_status','reuse_status']);same(ss,os,'source provenance unchanged '+rid+str(i))
 same(r['quality']['requested_tasks'],[],'tasks remain empty '+rid);same(r['structure_assets'],[],'no coordinates '+rid)
 errors=validate_record(r);admit=eligibility(r);same(errors,[],'schema '+rid);check(not any(x['eligible'] for x in admit.values()),'no task eligibility '+rid)
 schema.append({'record_id':rid,'errors':errors,'eligibility':admit});deltas[rid]=diff(old,r)
same(len(records),21,'21 records');same(Counter(r['reader_role'] for r in records.values()),Counter({'synthesis_route':1,'supporting_procedure':13,'contextual_observation':7}),'roles 1/13/7')
same(sum(len(r['operations']) for r in records.values()),39,'39 operations');same(sum(len(r['measurements']) for r in records.values()),678,'678 measurements')
old=bind(G/'public-review-proposal/v1/matuhina2023.json');reader=bind(P/'reader/matuhina2023.json');rr=copy.deepcopy(reader)
reader_deltas=diff(old,reader)
same(reader['review_scope'],'supplied_main_and_matched_si','corrected recognized review scope')
restore(rr,old,['review_scope','coverage_status','independent_audit','source_review_promoted','publication_status','review_state','training_note','audit_details','remaining_gaps','presentation_gates'])
same(len(rr['recipe_inventory']),len(old['recipe_inventory']),'recipe count unchanged')
for o,n in zip(old['recipe_inventory'],rr['recipe_inventory']):
 same(n['status'],'source_reviewed','recipe status '+n['id']);same(n.get('gaps'),[x for x in o.get('gaps',[]) if x not in removed],'recipe gaps '+n['id']);restore(n,o,['status','gaps'])
for key in ['figures','tables','schemes','equations','source_notes']:
 same(len(rr[key]),len(old[key]),'reader object count '+key)
 for o,n in zip(old[key],rr[key]):same(n['reviewed'],True,'reviewed source object '+n['id']);restore(n,o,['reviewed'])
same(rr,old,'ALL reader prose quantities field maps specimen joins source payloads unchanged')
old_gaps={'The distinct supplied main/SI source audit passed; canonical and reader independent approval remain pending.','Molecular, apparatus, product-context, model, browser and publication gates remain separate.'}
new_gap='Source, canonical/reader and visual audits passed. Integrated browser and publication gates remain separate; no qualified atomic model is admitted.'
same(reader['remaining_gaps'],[x for x in old['remaining_gaps'] if x not in old_gaps]+[new_gap],'only historical reader gate replaced')
same(reader['presentation_gates'],{'canonical_source_audit':True,'reader_source_audit':True,'molecular_bindings':True,'apparatus_bindings':True,'symbolic_product_contexts':True,'exact_product_atomic_structure_binding':False,'site_integration':False,'browser_render':False,'publication':False},'scope-limited review gates')
same(reader['audit_details']['audit_sha256'],f['source_audits'],'reader exact receipts');same(reader['audit_details']['training_promotions'],0,'no training promotion');same(reader['audit_details']['source_conflicts_resolved'],False,'conflicts retained')
maps={k:{rid:set() for rid in records} for k in ('structures','properties')};links=0
for section in reader['reader_sections']:
 for item in section['items']:
  for link in item.get('canonical_links',[]):
   r=records[link['record_id']];pointer(r,link['json_pointer']);check(True,'valid canonical pointer '+item['id']+' '+link['json_pointer']);links+=1
   bits=link['json_pointer'].strip('/').split('/')
   if section['id'] in maps and bits[0]=='measurements':maps[section['id']][r['record_id']].add(r['measurements'][int(bits[1])]['id'])
for section in maps:same(bind(P/('record-'+section+'-measurements.json')),{rid:sorted(ids) for rid,ids in maps[section].items()},'display map exact '+section)
for rid in records:check(not(maps['structures'][rid]&maps['properties'][rid]),'disjoint sections '+rid)
def effective_read(name):return bind(V/name)
orig=effective_read('registry-additions.json');reg=bind(P/'molecules/registry-additions.json');r=copy.deepcopy(reg);restore(r,orig,['binding_approved','status'])
same(len(reg['entries']),28,'28 molecular entries')
for o,n in zip(orig['entries'],r['entries']):
 same(n['binding_approved'],True,'qualified entry '+n['id']);same(n['published'],False,'publication not approved '+n['id']);same(n['eligible_training'],False,'training false '+n['id']);restore(n,o,['binding_approved','independentScientificAudit','published','eligible_training'])
same(r,orig,'ALL identities captions provenance and model hashes unchanged')
orig=effective_read('bindings-proposal.json');bm=bind(P/'molecules/bindings-additions.json');b=copy.deepcopy(bm);restore(b,orig,['binding_approved','status','sourceRecordSha256'])
same(set(bm['sourceRecordSha256']),set(records),'source hash binding keys only Matuhina')
for rid,r in records.items():
 same(bm['sourceRecordSha256'][rid],sha(P/'records'/(rid+'.json')),'promoted hash '+rid);same(set(bm['recordBindings'][rid]),{m['id'] for m in r['materials']},'complete exact slots '+rid)
 if not r['materials']:
  same(bm['recordBindings'][rid],{},'empty materials mapping '+rid);same(bm['bindingNotes'][rid],{},'empty material notes '+rid)
  for key in ('recordBindings','bindingNotes'):
   if rid not in orig[key]:b[key].pop(rid,None)
for rid,notes in orig['bindingNotes'].items():
 for mid,o in notes.items():
  same(bm['bindingNotes'][rid][mid]['binding_approved'],True,'slot approval '+rid+mid);restore(b['bindingNotes'][rid][mid],o,['binding_approved','independent_scientific_audit'])
same(b,orig,'ALL 55 assignments quantities snapshots and scoped overrides unchanged')
orig=effective_read('solution-components-proposal.json');sol=bind(P/'molecules/solution-components-additions.json');ss=copy.deepcopy(sol);restore(ss,orig,['binding_approved'])
for o,n in zip(orig['contexts'],ss['contexts']):same(n['binding_approved'],True,'stock approval '+n['id']);restore(n,o,['binding_approved'])
same(ss,orig,'ALL stock source quantities component identities unchanged');same(len(sol['contexts']),5,'five stocks');same(sum(len(x['components']) for x in sol['contexts']),15,'15 components')
assets=pm['public_assets'];same(len(assets),82,'82 public files');same(Counter(x['kind'] for x in assets),Counter({'selected_original_scientific_crop':30,'reviewed_chemical_reference':44,'independently_audited_apparatus':1,'reviewed_symbolic_product_context':7}),'30 crops44 chemicals1module7symbols')
crops={Path(x['path']).name:x for x in bind(G/'original-assets-manifest.json')['assets']};public={a['path']:a for a in bind(V/'public-asset-proposal.json')['assets']};apparatus=bind(G/'visuals/apparatus/package-freeze.json');paths=set()
for row in assets:
 rel=row['public_path'];p=P/'dist'/rel;check(rel not in paths,'unique public path '+rel);paths.add(rel);bind(row['source_path']);same(sha(p),row['sha256'],'public hash '+rel);same(sha(p),sha(row['source_path']),'exact copied source '+rel)
 check(p.suffix in ('.png','.svg','.json','.mjs'),'allowed selected asset type '+rel)
 if row['kind']=='selected_original_scientific_crop':same(crops[p.name]['contains_complete_source_page'],False,'not whole page '+rel);same(sha(p),crops[p.name]['sha256'],'audited crop '+rel)
 elif row['kind']=='reviewed_chemical_reference':same(sha(p),public[rel.removeprefix('assets/chemical-registry/')]['sha256'],'effective chemical overlay bytes '+rel)
 elif row['kind']=='independently_audited_apparatus':same(sha(p),apparatus['public_assets'][0]['sha256'],'audited apparatus bytes')
 elif row['kind']=='reviewed_symbolic_product_context':same(sha(p),sha(G/'visuals/product-context'/rel.removeprefix('assets/chemical-registry/')),'audited product symbol bytes')
 if p.suffix in ('.svg','.json','.mjs'):check(not re.search(r'[A-Z]:[\\/]|file://',p.read_text(encoding='utf8')),'no local path in public asset '+rel)
same({p.relative_to(P/'dist').as_posix() for p in (P/'dist').rglob('*') if p.is_file()},paths,'exact public allowlist no hidden additions')
for rid,r in records.items():check(not re.search(r'[A-Z]:[\\/]|file://',json.dumps(r)),'no local path record '+rid)
check(not re.search(r'[A-Z]:[\\/]|file://',json.dumps(reader)),'no local path reader')
Q0=G/'visuals/product-context'
orig=bind(Q0/'product-contexts-additions.json');products=bind(P/'products/product-contexts-additions.json')
keys={'sample_id','label','registry_id','caption','phase','morphology','composition_evidence','reported_parent_context','same_physical_batch_asserted','projection_kind','phase_component_formula','training_eligible','atomic_model'}
same(pm['product_public_field_allowlist'],sorted(keys),'explicit product allowlist')
expected=copy.deepcopy(orig)
for rid,rows in expected['recordContexts'].items():
 expected['recordContexts'][rid]=[{**{k:v for k,v in r.items() if k in keys},'binding_approved':True} for r in rows]
same(products,expected,'ALL rendered product scientific fields retained; only private wrappers removed')
same(sum(map(len,products['recordContexts'].values())),47,'47 product contexts')
same(len({(rid,r['sample_id']) for rid,rows in products['recordContexts'].items() for r in rows}),45,'45 record/sample pairs')
orig=bind(Q0/'registry-additions.json');preg=bind(P/'products/registry-additions.json');rest=copy.deepcopy(preg)
for o,n in zip(orig['entries'],rest['entries']):
 same(n['binding_approved'],True,'product gate true '+n['id']);same(n['published'],False,'product publication false '+n['id']);restore(n,o,['binding_approved','published','independentScientificAudit'])
same(rest,orig,'ALL seven symbolic product identities/captions/assets unchanged');same(len(preg['entries']),7,'seven product symbols')
check(not re.search(r'[A-Z]:[\\/]|file://',json.dumps(products)),'no private product paths')
Q=A/'private-validator-projection'
for rid in records:
 dest=Q/'data/records'/(rid+'.json');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(P/'records'/(rid+'.json'),dest)
for row in assets:
 if row['kind']!='selected_original_scientific_crop':continue
 dest=Q/'dist'/row['public_path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(P/'dist'/row['public_path'],dest)
build_paper_reviews.ROOT=Q;errors=build_paper_reviews.validate(reader);same(errors,[],'actual reader validator isolated projection')
for rel in ('dataset_lib.py','schema_definition.py','review_scope.py','build_paper_reviews.py'):bind(S/'scripts'/rel)
bind(Path(__file__));findings=[x for x in checks if not x['passed']]
result={'schema':'mattersyn-independent-promotion-delta-audit/1','author':'/root','auditor':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'source_id':'matuhina2023','status':'passed' if not findings else 'open_findings','proposal_freeze_sha256':sha(P/'package-freeze.json'),'check_count':len(checks),'open_findings':findings,'counts':{'records':21,'routes_variants':1,'procedures':13,'observations':7,'operations':39,'measurements':678,'reader_links':links,'entries':28,'material_slots':55,'stocks':5,'stock_components':15,'public_files':82,'product_contexts':47,'product_symbols':7},'record_deltas':deltas,'reader_deltas':reader_deltas,'schema_results':schema,'reader_validator_errors':errors,'display_map_counts':{k:sum(map(len,v.values())) for k,v in maps.items()},'manual_scope':['Read complete root promotion script and every permitted status/gap transformation; genuine gaps remain and browser/publication are false.','Scientific arrays and reader content compared deeply, not merely quantities; only permitted metadata removed for equality.','Frozen molecular reference proposal used; all identities, 55 slot assignments, stock quantities and source captions unchanged.','Exact 82-file allowlist contains only independently passed selected crops, chemical assets and apparatus module; no full papers, full text or page images.','Display maps derive from this source reader only; product public projection preserves every consumer field; actual integration gates remain pending.'],'bound_files':dict(sorted(bound.items())),'closed_findings':[{'id':'MATUHINA-PROM-01','status':'resolved','scope':'Exactly one review_scope token normalized; prior freeze and all other files preserved; actual reader validator now accepts the proposal.'}],'prior_audit_sha256':sha(A/'promotion-delta-audit-v1.json'),'full_source_reaudit':False,'site_changed':False,'integration_approved':False,'browser_approved':False,'publication_approved':False,'training_approved':False}
save(A/'promotion-delta-audit.json',result);save(A/'promotion-delta-checks.json',{'checks':checks})
(A/'promotion-delta-audit.md').write_text(f"# Matuhina promotion delta audit\n\nStatus: **{result['status']}**; {len(checks)} independent checks; {len(findings)} open findings.\n\nThe exact root-authored proposal `{result['proposal_freeze_sha256']}` preserves all scientific content in21 records,39 operations and678 measurements. It retains one route,13 procedures and7 observations, with no admitted training task or atomic model. All reader prose, quantities, source conflicts, selected graphics and specimen associations remain unchanged.\n\nAll28 chemical references,55 material slots and5 stocks/15 components retain their audited identity and quantity data. The public product projection preserves all rendered fields across47 contexts while removing private staging paths and duplicate audit snapshots.82 exact public assets comprise30 selected crops,44 chemical files,7 symbolic product SVGs and1 separately audited apparatus module. No full papers, fulltext or whole-page renders are included.\n\nThis is a private promotion audit. Actual integrated code, browser rendering and public delivery remain separate gates.\n",encoding='utf8')

print(json.dumps({'status':result['status'],'checks':len(checks),'open_findings':findings,'audit_sha256':sha(A/'promotion-delta-audit.json')}))
