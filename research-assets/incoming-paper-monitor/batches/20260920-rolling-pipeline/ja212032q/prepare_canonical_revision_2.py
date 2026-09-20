"""Preserved, narrowly scoped Ghosh sample-set classification correction."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil, sys, copy
sys.dont_write_bytecode = True
G = Path(__file__).resolve().parent
C1=G/'canonical-proposal/v1'; C2=G/'canonical-proposal/v2'
R1=G/'public-review-proposal/v1'; R2=G/'public-review-proposal/v2'
def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v): Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def diffs(a,b,p=''):
 if type(a)!=type(b): return [{'pointer':p,'before':a,'after':b}]
 if isinstance(a,dict):
  assert a.keys()==b.keys(),p
  return [d for k in a for d in diffs(a[k],b[k],p+'/'+k)]
 if isinstance(a,list):
  assert len(a)==len(b),p
  return [d for i in range(len(a)) for d in diffs(a[i],b[i],p+'/'+str(i))]
 return [] if a==b else [{'pointer':p,'before':a,'after':b}]
assert not C2.exists() and not R2.exists(),'Create a new preserved revision rather than overwrite.'
old=read(C1/'package-manifest.json')
protected={str(p):sha(p) for base in [C1,R1] for p in base.rglob('*') if p.is_file()}
for p,h in old['bound_files'].items():
 if Path(p).is_relative_to(G): assert sha(p)==h,p
shutil.copytree(C1,C2); shutil.copytree(R1,R2)
(C2/'package-manifest.json').unlink()
changes={
 'anneal-series':['anneal-series-particles'],
 'solvent-ligand-series':['solvent-series-particles','ligand-series-particles'],
 'stoichiometry-series':['withdrawal-series-particles'],
 'ftir-procedure':['ftir-film'],
}
record_deltas=[]
name='Separate particle and pure-ligand FTIR specimens'
for stem,states in changes.items():
 p=C2/('ghosh-2012-'+stem+'.json'); before=read(p); after=copy.deepcopy(before)
 for state in after['material_states']:
  if state['id'] in states:
   assert state['kind'] in ['mixture','reaction_batch']
   state['kind']='sample_set'
   if state['id']=='ftir-film': state['name']=name
 ds=diffs(before,after)
 assert len(ds)==len(states)+(stem=='ftir-procedure')
 record_deltas.append({'record_id':before['record_id'],'changes':ds})
 save(p,after)
before=read(R1/'ghosh2012.json'); after=copy.deepcopy(before)
found=[]
for s in after['reader_sections']:
 for item in s['items']:
  if item['id'] in ['operation-ftir-purify-cast','operation-ftir-acquire']:
   labels=item['operation_context']['material_flow_labels']
   assert labels['ftir-film']=='ftir film'; labels['ftir-film']=name
   item['notes']=[n.replace('ftir film',name) for n in item['notes']]
   found.append(item['id'])
assert len(found)==2
reader_deltas=diffs(before,after);assert len(reader_deltas)==4
assert all('/notes/' in d['pointer'] or '/material_flow_labels/ftir-film' in d['pointer'] for d in reader_deltas)
save(R2/'ghosh2012.json',after)
checks=[]
def ck(ok,label):
 assert ok,label
 checks.append({'check':label,'passed':True})
sys.path.insert(0,str(G.parents[4]/'recipe-atlas/scripts'))
from dataset_lib import validate_record,eligibility
records={p.stem:read(p) for p in C2.glob('ghosh-2012-*.json')}
for rid,r in records.items():
 prior=read(C1/(rid+'.json'))
 for field in r:
  if field!='material_states':ck(r[field]==prior[field],rid+' unchanged '+field)
 ck(not validate_record(r),rid+' current schema/semantic validation')
 ck(not any(v['eligible'] for v in eligibility(r).values()),rid+' zero training eligibility')
 for st1,st2 in zip(prior['material_states'],r['material_states']):
  ck({k:v for k,v in st1.items() if k not in ['name','kind']}=={k:v for k,v in st2.items() if k not in ['name','kind']},rid+' unchanged state topology '+st1['id'])
ck(sum(len(d['changes'])for d in record_deltas)==6,'Exactly five state kinds and one FTIR name changed')
ck(len(reader_deltas)==4,'Exactly four FTIR reader label leaves changed')
for p,h in protected.items():ck(sha(p)==h,'Original v1 preserved '+str(Path(p).relative_to(G)))
delta={'schema':'mattersyn-bounded-canonical-reader-delta/1','author':'/root/backlog_eta','reviewer_request':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'parent_manifest_sha256':sha(C1/'package-manifest.json'),'allowed_scope':'Five grouped alternative or analytical specimen states become sample_set; FTIR name and its four reader labels only. No values, source evidence, operation graph, specimen IDs, parent IDs or training gates changed.','canonical_changes':record_deltas,'reader_changes':reader_deltas,'unchanged_record_bytes':[rid for rid in records if sha(C1/(rid+'.json'))==sha(C2/(rid+'.json'))],'protected_v1_files':protected,'source_payload_unchanged':True,'independent_approval':False}
save(C2/'revision-2-delta.json',delta)
validation={'author':'/root/backlog_eta','status':'bounded_revision_author_checks_passed','created_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'inherited_v1_canonical_checks':old['author_checks']['canonical'],'inherited_v1_reader_checks':old['author_checks']['reader'],'counts':old['canonical_counts'],'current_module_sha256':sha(G.parents[4]/'recipe-atlas/scripts/dataset_lib.py'),'independent_approval':False}
save(C2/'revision-2-validation.json',validation)
cm=read(C2/'record-manifest.json');cm.update(version=2,created_at=datetime.now(timezone.utc).isoformat(),validation_sha256=sha(C2/'revision-2-validation.json'),author_script_sha256=sha(__file__),parent_manifest_sha256=sha(C1/'record-manifest.json'))
for row in cm['records']:
 p=C2/(row['record_id']+'.json');row.update(path=str(p),sha256=sha(p))
save(C2/'record-manifest.json',cm)
rm=read(R2/'reader-manifest.json');rm.update(version=2,created_at=datetime.now(timezone.utc).isoformat(),author_script_sha256=sha(__file__),parent_manifest_sha256=sha(R1/'reader-manifest.json'))
rm['input_hashes']={str(C2/Path(p).name) if Path(p).is_relative_to(C1) else p:h for p,h in rm['input_hashes'].items()}
rm['input_hashes'][str(C2/'record-manifest.json')]=sha(C2/'record-manifest.json')
rm['outputs']={n:sha(R2/n) for n in rm['outputs']}
save(R2/'reader-manifest.json',rm)
(C2/'REVISION-2.md').write_text('Private revision 2 preserves v1. Five grouped comparison/analytical states now use sample_set; the FTIR state and four reader display labels explicitly identify separate particle and pure-ligand specimens. All quantities, evidence, source payloads, operation graphs, parent/sample IDs and task gates are unchanged. Copied v1 author-validation and notes are historical inherited checks; revision-2-validation.json is the current bounded author check. Independent reviewer confirmation remains pending.\n',encoding='utf-8')
bound={str(p):sha(p)for base in [C2,R2]for p in base.rglob('*')if p.is_file()}
for p,h in old['bound_files'].items():
 if not Path(p).is_relative_to(C1) and not Path(p).is_relative_to(R1):bound[p]=h
bound[str(C1/'package-manifest.json')]=sha(C1/'package-manifest.json');bound[str(Path(__file__))]=sha(__file__)
final=copy.deepcopy(old);final.update(version=2,frozen_at=datetime.now(timezone.utc).isoformat(),canonical_record_manifest_sha256=sha(C2/'record-manifest.json'),reader_manifest_sha256=sha(R2/'reader-manifest.json'),reader_sha256=sha(R2/'ghosh2012.json'),bound_files=bound,bound_file_count=len(bound),parent_manifest_sha256=sha(C1/'package-manifest.json'),bounded_revision_check_count=len(checks),scope_notes_path=str(C2/'REVISION-2.md'),input_snapshots_path=str(C2/'input-snapshots.json'),revision_delta_sha256=sha(C2/'revision-2-delta.json'))
save(C2/'package-manifest.json',final)
print(json.dumps({'manifest':str(C2/'package-manifest.json'),'sha256':sha(C2/'package-manifest.json'),'reader_sha256':sha(R2/'ghosh2012.json'),'record_manifest_sha256':sha(C2/'record-manifest.json'),'checks':len(checks),'unchanged_record_bytes':len(delta['unchanged_record_bytes'])}))
