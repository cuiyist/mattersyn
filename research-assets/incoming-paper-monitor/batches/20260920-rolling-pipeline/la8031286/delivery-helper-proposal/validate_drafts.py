"""Read-only author checks of private delivery drafts; no release code executed."""
from pathlib import Path
import ast,json,hashlib,sys,datetime
D=Path(__file__).resolve().parent;N=D.parent;M=N.parents[4];S=M/'recipe-atlas';sys.dont_write_bytecode=True;sys.path.insert(0,str(M/'research-assets'))
import public_projection_policy as policy
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
for p in D.glob('*.py'):ast.parse(p.read_text('utf8'));ck('Valid Python syntax '+p.name,True)
plan=read(D/'release-endpoints.json');base=read(N.parent/'acsanm.2c04342/site-integration-proposal/release-endpoints.json');pm=read(N/'site-integration-proposal/v1/promotion-manifest.json');records=read(N/'canonical-proposal/v2/record-manifest.json')['records']
ck('Exactly 324 unique endpoints',len(plan['paths'])==len(set(plan['paths']))==plan['count']==324)
ck('All previous219 endpoints preserved in order',plan['paths'][:219]==base['paths'])
expected=['data/paper-reviews/pati2009.json']+[x['public_path']for x in pm['public_assets']]+[prefix+r['record_id']+suffix for r in records for prefix,suffix in [('records/','.html'),('data/records/','.json')]]
ck('Exact 105 new endpoints',plan['paths'][219:]==expected and len(expected)==105)
for rel in plan['paths']:ck('Current Site endpoint exists '+rel,(S/'dist'/rel).is_file())
ck('39 citation source groups',read(S/'dist/data/dataset-manifest.json')['group_count']==39==plan['expected_citation_count'])
ck('16 additional withheld endpoints',len(plan['additional_withheld_paths'])==len(set(plan['additional_withheld_paths']))==16)
for p in plan['additional_withheld_paths']:ck('No selected endpoint is a withheld source page '+p,p not in plan['paths']);ck('Withheld page absent locally '+p,not(S/'dist'/p).exists())
tree=ast.parse((D/'verify_public_delivery-proposed.py').read_text('utf8'));nodes=[]
def targetname(n):return isinstance(n,ast.Name)and n.id in ['paths','withheld']
for n in tree.body:
 if isinstance(n,ast.Assign)and any(targetname(t)for t in n.targets):nodes.append(n)
 elif isinstance(n,ast.AugAssign)and targetname(n.target):nodes.append(n)
 elif isinstance(n,ast.If)and any(isinstance(x,ast.AugAssign)and targetname(x.target)for x in n.body):nodes.append(n)
ns={'D':S/'dist'};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<pure endpoint selection>','exec'),ns)
ck('Actual proposed verifier path selector matches plan',ns['paths']==plan['paths']);ck('Actual proposed withheld selector matches plan',ns['withheld']==plan['additional_withheld_paths'])
original=(D/'input-snapshots/verify_public_delivery.py').read_text('utf8');proposed=(D/'verify_public_delivery-proposed.py').read_text('utf8')
insertion="if (D/'data/paper-reviews/pati2009.json').exists():\n paths += "+repr(expected)+"\n"
withhold="if (D/'data/paper-reviews/pati2009.json').exists():withheld += ['assets/figures/pati2009/pages/main-01.png','assets/figures/pati2009/pages/si-01.png']\n"
ck('Verifier delta exactly two source-scoped extensions',proposed.replace(insertion,'').replace(withhold,'')==original)
fin=(D/'finalize_reader_publication.py').read_text('utf8');release=(D/'release_pati.py').read_text('utf8');sync=(D/'sync_release_delta.py').read_text('utf8')
for token in ['==324','==39','==16',"'matuhina2023','pati2009'","'0.31.0'","'pati2009'"]:ck('Finalizer exact current guard '+token,token in fin)
for token in ['==38','==219','==14',"'0.30.0'",'data/paper-reviews/matuhina2023.json']:ck('No stale finalizer guard '+token,token not in fin)
for token in ['canonical_records\']==626','synthesis_route_variant_records\']==118','total_canonical_source_groups\']==39','len(checks)==324','==16','==39']:ck('Release current gate '+token,token in release)
for token in ["acs.inorgchem.8b02945","intake-20260920T133256Z","admission-20260920T133256Z",'policy.exclude_path(rel)','policy.project_bytes(rel','io_path(source).is_symlink()','os.walk(io_path(folder))']:ck('Projection retains verified policy and current scope '+token,token in sync)
for rel in ['research-assets/incoming-paper-monitor/batches/20260920-rolling-pipeline/acs.inorgchem.8b02945/source-render/main-01.png','research-assets/incoming-paper-monitor/batches/20260920-rolling-pipeline/acs.inorgchem.8b02945/source-render/text/main-01.txt','research-assets/incoming-paper-monitor/batches/20260920-rolling-pipeline/acs.inorgchem.8b02945/complete-source-payloads.json','downloaded_papers/paper.pdf','downloaded_papers/paper_si_1.pdf']:
 ck('Source artifact excluded '+rel,bool(policy.exclude_path(rel)))
for rel in ['MEMORY.md','skills/mattersyn-paper-to-site/SKILL.md','research-assets/incoming-paper-monitor/batches/20260920-rolling-pipeline/la8031286/source-facts.json','recipe-atlas/dist/assets/figures/pati2009/figure-1.png']:
 ck('Intended structured/project content retained '+rel,policy.exclude_path(rel)is None)
ck('Shared verifier original bytes unchanged',sha(M/'research-assets/verify_public_delivery.py')==sha(D/'input-snapshots/verify_public_delivery.py'))
status='passed'if all(x['passed']for x in checks)else'open_findings'
out={'schema':'mattersyn-delivery-helper-author-validation/1','author':'/root/norberg2004_extract','status':status,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'failures':[x for x in checks if not x['passed']],'method':'AST syntax and exact-delta checks; executed only local endpoint-selection statements with current Site as a read-only fixture and imported read-only projection policy. No draft release helper, verifier network code, Site/project/ledger mutation, credential function or API executed.','independent_approval':False,'site_changed':False,'network_calls':False}
(D/'author-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'status':status,'checks':len(checks),'failures':out['failures']}))
