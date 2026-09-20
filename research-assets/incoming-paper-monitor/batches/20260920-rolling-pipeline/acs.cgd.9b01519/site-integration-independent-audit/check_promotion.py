"""Independent frozen promotion comparison. Writes private audit outputs only."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import copy, hashlib, json, re, shutil, sys, argparse
A=Path(__file__).resolve().parent; G=A.parent; P=G/'site-integration-proposal/v1'
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
same(sha(bind(G/'prepare_site_proposal.py')),f['author_script_sha256'],'author script frozen')
for rel,digest in f['source_audits'].items():
 audit=bind(G/rel);same(sha(G/rel),digest,'audit hash '+rel);same(audit['status'],'passed','prior audit passed '+rel)
 for path,h in audit.get('bound_files',{}).items():
  fp=Path(path) if Path(path).is_absolute() else G/path
  bind(fp);same(sha(fp),h,'audit dependency unchanged '+str(path))
baseline=bind(A/'pre-integration-baseline.json')
for rel,digest in baseline['approved_inputs'].items():bind(G/rel);same(sha(G/rel),digest,'approved input unchanged '+rel)
rm=bind(G/'canonical-proposal/v2/record-manifest.json');pm=bind(P/'promotion-manifest.json')
removed=['The complete supplied 11-page main extraction passed distinct source audit. Declared SI remains locally unlocated/unverified. Canonical/reader independent review remains pending; this is an unapproved private author draft. Historical pending flags in immutable source payloads refer to their author-freeze time.']
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
same(len(records),19,'19 records');same(Counter(r['reader_role'] for r in records.values()),Counter({'synthesis_route':3,'supporting_procedure':9,'contextual_observation':7}),'roles 3/9/7')
same(sum(len(r['operations']) for r in records.values()),31,'31 operations');same(sum(len(r['measurements']) for r in records.values()),532,'532 measurements')
old=bind(G/'public-review-proposal/v2/sommer2020.json');reader=bind(P/'reader/sommer2020.json');rr=copy.deepcopy(reader)
reader_deltas=diff(old,reader)
restore(rr,old,['coverage_status','independent_audit','source_review_promoted','publication_status','review_state','training_note','audit_details','remaining_gaps','presentation_gates'])
same(len(rr['recipe_inventory']),len(old['recipe_inventory']),'recipe count unchanged')
for o,n in zip(old['recipe_inventory'],rr['recipe_inventory']):
 same(n['status'],'source_reviewed','recipe status '+n['id']);same(n.get('gaps'),[x for x in o.get('gaps',[]) if x not in removed],'recipe gaps '+n['id']);restore(n,o,['status','gaps'])
for key in ['figures','tables','schemes','equations','source_notes']:
 same(len(rr[key]),len(old[key]),'reader object count '+key)
 for o,n in zip(old[key],rr[key]):same(n['reviewed'],True,'reviewed source object '+n['id']);restore(n,o,['reviewed'])
same(rr,old,'ALL reader prose quantities field maps specimen joins source payloads unchanged')
old_gaps={'The distinct supplied-main source audit passed; canonical and reader independent approval remain pending.','Molecular, apparatus, product-context, browser and publication gates remain separate.'}
new_gap='Source, canonical/reader, molecular and apparatus audits passed. Symbolic product-context binding, integrated browser and publication gates remain separate.'
same(reader['remaining_gaps'],[x for x in old['remaining_gaps'] if x not in old_gaps]+[new_gap],'only historical reader gate replaced')
same(reader['presentation_gates'],{'canonical_source_audit':True,'reader_source_audit':True,'molecular_bindings':True,'apparatus_bindings':True,'exact_product_atomic_structure_binding':False,'site_integration':False,'browser_render':False,'publication':False},'scope-limited review gates')
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
effective=bind(V/'canonical-v2-rebind/effective-file-map.json')
def effective_read(name):
 row=effective[name];d=bind(row['path']);same(sha(row['path']),row['sha256'],'effective overlay input '+name);return d
orig=effective_read('registry-additions.json');reg=bind(P/'molecules/registry-additions.json');r=copy.deepcopy(reg);restore(r,orig,['binding_approved','status'])
same(len(reg['entries']),28,'28 molecular entries')
for o,n in zip(orig['entries'],r['entries']):
 same(n['binding_approved'],True,'qualified entry '+n['id']);same(n['published'],False,'publication not approved '+n['id']);same(n['eligible_training'],False,'training false '+n['id']);restore(n,o,['binding_approved','independentScientificAudit','published','eligible_training'])
same(r,orig,'ALL identities captions provenance and model hashes unchanged')
orig=effective_read('bindings-proposal.json');bm=bind(P/'molecules/bindings-additions.json');b=copy.deepcopy(bm);restore(b,orig,['binding_approved','status','sourceRecordSha256'])
same(set(bm['sourceRecordSha256']),set(records),'source hash binding keys only Sommer')
for rid,r in records.items():
 same(bm['sourceRecordSha256'][rid],sha(P/'records'/(rid+'.json')),'promoted hash '+rid);same(set(bm['recordBindings'][rid]),{m['id'] for m in r['materials']},'complete exact slots '+rid)
 if not r['materials']:
  same(bm['recordBindings'][rid],{},'empty materials mapping '+rid);same(bm['bindingNotes'][rid],{},'empty material notes '+rid)
  for key in ('recordBindings','bindingNotes'):
   if rid not in orig[key]:b[key].pop(rid,None)
for rid,notes in orig['bindingNotes'].items():
 for mid,o in notes.items():
  same(bm['bindingNotes'][rid][mid]['binding_approved'],True,'slot approval '+rid+mid);restore(b['bindingNotes'][rid][mid],o,['binding_approved','independent_scientific_audit'])
same(b,orig,'ALL 62 assignments quantities snapshots and scoped overrides unchanged')
orig=effective_read('solution-components-proposal.json');sol=bind(P/'molecules/solution-components-additions.json');ss=copy.deepcopy(sol);restore(ss,orig,['binding_approved'])
for o,n in zip(orig['contexts'],ss['contexts']):same(n['binding_approved'],True,'stock approval '+n['id']);restore(n,o,['binding_approved'])
same(ss,orig,'ALL stock source quantities component identities unchanged');same(len(sol['contexts']),7,'seven stocks');same(sum(len(x['components']) for x in sol['contexts']),23,'23 components')
assets=pm['public_assets'];same(len(assets),57,'57 public files');same(Counter(x['kind'] for x in assets),Counter({'selected_original_scientific_crop':20,'reviewed_chemical_reference':36,'independently_audited_apparatus':1}),'20 crops36 chemicals1module')
crops={Path(x['path']).name:x for x in bind(G/'original-assets-manifest.json')['assets']};public=bind(V/'canonical-v2-rebind/effective-public-assets.json');apparatus=bind(G/'visuals/apparatus/package-freeze.json');paths=set()
for row in assets:
 rel=row['public_path'];p=P/'dist'/rel;check(rel not in paths,'unique public path '+rel);paths.add(rel);bind(row['source_path']);same(sha(p),row['sha256'],'public hash '+rel);same(sha(p),sha(row['source_path']),'exact copied source '+rel)
 check(p.suffix in ('.png','.svg','.json','.mjs'),'allowed selected asset type '+rel)
 if row['kind']=='selected_original_scientific_crop':same(crops[p.name]['contains_complete_source_page'],False,'not whole page '+rel);same(sha(p),crops[p.name]['sha256'],'audited crop '+rel)
 elif row['kind']=='reviewed_chemical_reference':same(sha(p),public[rel.removeprefix('assets/chemical-registry/')]['sha256'],'effective chemical overlay bytes '+rel)
 else:same(sha(p),apparatus['public_assets'][0]['sha256'],'audited apparatus bytes')
 if p.suffix in ('.svg','.json','.mjs'):check(not re.search(r'[A-Z]:[\\/]|file://',p.read_text(encoding='utf8')),'no local path in public asset '+rel)
same({p.relative_to(P/'dist').as_posix() for p in (P/'dist').rglob('*') if p.is_file()},paths,'exact public allowlist no hidden additions')
for rid,r in records.items():check(not re.search(r'[A-Z]:[\\/]|file://',json.dumps(r)),'no local path record '+rid)
check(not re.search(r'[A-Z]:[\\/]|file://',json.dumps(reader)),'no local path reader')
Q=A/'private-validator-projection'
for rid in records:
 dest=Q/'data/records'/(rid+'.json');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(P/'records'/(rid+'.json'),dest)
for row in assets:
 if row['kind']!='selected_original_scientific_crop':continue
 dest=Q/'dist'/row['public_path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(P/'dist'/row['public_path'],dest)
build_paper_reviews.ROOT=Q;errors=build_paper_reviews.validate(reader);same(errors,[],'actual reader validator isolated projection')
for rel in ('dataset_lib.py','schema_definition.py','review_scope.py','build_paper_reviews.py'):bind(S/'scripts'/rel)
bind(Path(__file__));findings=[x for x in checks if not x['passed']]
result={'schema':'mattersyn-independent-promotion-delta-audit/1','author':'/root','auditor':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'source_id':'sommer2020','status':'passed' if not findings else 'open_findings','proposal_freeze_sha256':sha(P/'package-freeze.json'),'check_count':len(checks),'open_findings':findings,'counts':{'records':19,'routes_variants':3,'procedures':9,'observations':7,'operations':31,'measurements':532,'reader_links':links,'entries':28,'material_slots':62,'stocks':7,'stock_components':23,'public_files':57},'record_deltas':deltas,'reader_deltas':reader_deltas,'schema_results':schema,'reader_validator_errors':errors,'display_map_counts':{k:sum(map(len,v.values())) for k,v in maps.items()},'manual_scope':['Read complete root promotion script and every permitted status/gap transformation; genuine gaps remain and browser/publication are false.','Scientific arrays and reader content compared deeply, not merely quantities; only permitted metadata removed for equality.','Effective molecular v2 rebind overlay used; all identities, 62 slot assignments, stock quantities and source captions unchanged.','Exact 57-file allowlist contains only independently passed selected crops, chemical assets and apparatus module; no full papers, full text or page images.','Display maps derive from this source reader only; separate product-context and actual integration gates remain pending.'],'bound_files':dict(sorted(bound.items())),'full_source_reaudit':False,'site_changed':False,'integration_approved':False,'browser_approved':False,'publication_approved':False,'training_approved':False}
save(A/'promotion-delta-audit.json',result);save(A/'promotion-delta-checks.json',{'checks':checks})
(A/'promotion-delta-audit.md').write_text(f"# Sommer promotion delta audit\n\nStatus: **{result['status']}**; {len(checks)} independent checks, {len(findings)} open findings.\n\nThe exact frozen root proposal `{result['proposal_freeze_sha256']}` preserves all scientific content in 19 records, 31 operations and 532 measurement/context entries. Three route, nine procedure and seven observation roles are retained. Requested tasks and structure assets remain empty.\n\nAll reader scientific prose, source conflicts, tables, figures, typed fields and specimen associations remain unchanged. Only supported review metadata and stale approval-gate text differ. Effective molecular v2 rebind references, all 62 material slots and seven stock contexts/23 components are transported without scientific changes. The 57 public files are exactly 20 selected crops, 36 chemical assets and one separately audited apparatus module. Current canonical and reader validators run on private inputs.\n\nThis is a promotion/projection audit, not another full source audit. Product mapping, integrated code/browser, deployment and training approval remain separate.\n",encoding='utf8')
print(json.dumps({'status':result['status'],'checks':len(checks),'open_findings':findings,'audit_sha256':sha(A/'promotion-delta-audit.json')}))
