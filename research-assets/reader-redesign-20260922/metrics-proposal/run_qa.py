"""Run proposed code against synthetic tests and actual read-only corpus."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,importlib.util,unittest,io,copy
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;S=P.parents[2]/'recipe-atlas'
sys.path[:0]=[str(P/'files/scripts'),str(P/'files/tests'),str(S/'scripts'),str(S/'tests'),str(S/'.sites-runtime/python-packages')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
baseline=load('baseline_dataset_lib',P/'base/scripts/dataset_lib.py')
import dataset_lib,structure_recipe_metrics,catalog_view
assert Path(dataset_lib.__file__).resolve()==(P/'files/scripts/dataset_lib.py').resolve()
test_dataset=load('test_dataset',P/'files/tests/test_dataset.py');test_dataset.SITE=S
test_metrics=load('test_structure_recipe_metrics',P/'files/tests/test_structure_recipe_metrics.py')
suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(x) for x in [test_dataset,test_metrics]])
for filename in ['test_host_targets.py','test_qualitative_measurements.py']:
 mod=load(filename[:-3],S/'tests'/filename)
 if hasattr(mod,'SITE'):mod.SITE=S
 suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(mod))
log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
(P/'qa-test-output.txt').write_text(log.getvalue(),'utf8')
rows=sorted((S/'data/records').glob('*.json'));before={str(p):sha(p) for p in rows}
export_before={str(p):sha(p) for p in (S/'dist/data/exports').glob('*.jsonl')}
records=[json.loads(p.read_text('utf8')) for p in rows]
policy=json.loads((P/'files/data/structure-task-policy.json').read_text('utf8'));policy['_asset_root']=str(S/'dist')
coverage=structure_recipe_metrics.structure_recipe_coverage(records,policy)
(P/'structure-recipe-coverage.preview.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n','utf8')
checks=[]
def ck(name,ok,detail=None):checks.append({'check':name,'passed':bool(ok),**({'detail':detail} if detail else {})})
ck('Current675records retained',len(records)==675)
ck('Distinct coordinate asset / record references / link / readiness counts',coverage['counts']=={'sample_coordinate_assets':1,'records_with_sample_coordinates':2,'source_verified_explicit_links':1,'exact_task_ready_records':0},coverage['counts'])
ck('Current coordinate asset is classified molecular only',coverage['asset_representation_counts']=={'molecular_structure':1} and coverage['explicit_link_representation_counts']=={'molecular_structure':1})
counts={k:0 for k in baseline.eligibility(records[0])};newcounts=copy.deepcopy(counts)
for r in records:
 old=baseline.eligibility(r);new=dataset_lib.eligibility(r,policy)
 ck('Current task eligibility unchanged '+r['record_id'],{k:x['eligible'] for k,x in old.items()}=={k:x['eligible'] for k,x in new.items()})
 for task in old:
  counts[task]+=int(old[task]['eligible']);newcounts[task]+=int(new[task]['eligible'])
  if task!='exact_structure_recipe':ck('Other task decision unchanged '+r['record_id']+'/'+task,old[task]==new[task])
  if old[task]['eligible']:ck('Existing training view exact '+r['record_id']+'/'+task,baseline.training_view(r,task)==dataset_lib.training_view(r,task,policy))
 if r['record_id'].startswith('evans-2010-'):
  ck('Evans not auto-promoted '+r['record_id'],new['exact_structure_recipe']['eligible'] is False)
for p,h in before.items():ck('Canonical bytes unchanged '+p,sha(Path(p))==h)
for p,h in export_before.items():ck('Existing export bytes unchanged '+p,sha(Path(p))==h)
ck('No admitted real profiles',not policy['task_profiles'])
import html
fragment=catalog_view.structure_coverage_html({'structure_recipe_coverage':coverage},html.escape)
(P/'catalog-coverage.preview.html').write_text('<!doctype html><meta charset="utf-8"><title>Structure metrics proposal</title>'+fragment,'utf8')
bad=[c for c in checks if not c['passed']]
report={'status':'passed' if result.wasSuccessful() and not bad else 'failed','at':datetime.now(timezone.utc).isoformat(),'runtime':sys.executable,'dependency_path':str(S/'.sites-runtime/python-packages'),'unit_tests':result.testsRun,'unit_failures':len(result.failures),'unit_errors':len(result.errors),'regression_checks':len(checks),'failed_regression_checks':bad,'current_counts':coverage['counts'],'current_representation_counts':coverage['asset_representation_counts'],'prior_eligible_by_task':counts,'proposed_eligible_by_task':newcounts,'checks':checks,'source_record_hashes':before,'training_export_hashes':export_before,'site_written':False,'canonical_written':False,'publication_performed':False}
(P/'qa-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ['checks','source_record_hashes','training_export_hashes']},ensure_ascii=False))
if not result.wasSuccessful():print(log.getvalue()[-9000:])
raise SystemExit(0 if report['status']=='passed' else 1)
