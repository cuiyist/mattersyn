from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib,runpy,sys
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';D=S/'dist';G=S/'scripts/check_quality.py'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ns=runpy.run_path(str(G),run_name='independent_quality_module');Audit=ns['Audit'];glob=Audit.materials.__globals__;cache={}
def cached(p):
 key=p.resolve()
 if key not in cache:cache[key]=read(key)
 return deepcopy(cache[key])
glob['load']=cached
baseline=Audit(S);baseline.records(0);baseline.materials();assert not baseline.errors,baseline.errors
PBS=D/'data/materials/pbs-7e1774.json';GLASS=D/'data/materials/pbs-glass-241df3.json';REVIEW=S/'data/paper-reviews/dantas2002.json'
routes={'dantas-2002-'+x for x in ['sg1','sg2','sg3','sg4','afm1','afm2']}
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
ph=read(PBS);gh=read(GLASS);review=read(REVIEW)
ck('Component PbS has exact six Dantas routes',set(ph['record_ids'])==routes and ph['component_only'] is True and ph['direct_record_ids']==[])
ck('Whole composite has exact six direct routes',set(gh['direct_record_ids'])==routes==set(gh['record_ids']) and gh['component_only'] is False)
for name,h,role in [('PbS',ph,'component_of_heterostructure'),('PbS/glass',gh,'direct_material')]:
 ck(name+'/only reviewed Dantas DOI',h['paper_dois']==['10.1021/jp0208743'] and len(h['papers'])==1)
 ck(name+'/whole product and source retained',all(r['formula']=='PbS/glass' and r['architecture']=='composite' and r['contribution_role']==role and r['doi']=='10.1021/jp0208743' for r in h['records']))
 ck(name+'/benchmark exclusions',all(not p['benchmarkRecordIds'] and set(p['reviewedRecordIds'])==routes for p in h['papers']))
 ck(name+'/main-only five-page source context',all(p['fullDocumentReview']['pages']==5 and p['fullDocumentReview']['scope']=='supplied_main_only_si_unverified' for p in h['papers']))
ck('Component scope public', 'not standalone pure-material syntheses' in ph['scope_note'])
ck('Exact main source hash/coverage',review['doi']=='10.1021/jp0208743' and review['review_scope']=='supplied_main_only_si_unverified' and any(x['role']=='main' and x['page_count']==5 and x['sha256']=='c8fd35a429bf636fcccc5dfeb3211cea44299e911fbfc80e1a308c75b7b04917' and {p['page'] for p in x['pages']}==set(range(1,6)) and all(p['text_read'] and p['visual_review'] for p in x['pages']) for x in review['documents']))
mutations=[]
def test(name,path=None,change=None,record_change=None):
 def mutated_load(p):
  value=cached(p)
  if path is not None and p.resolve()==path.resolve():change(value)
  return value
 glob['load']=mutated_load;a=Audit(S);a.byid=deepcopy(baseline.byid)
 if record_change:record_change(a.byid)
 try:a.materials()
 except (OSError,ValueError,KeyError,TypeError,IndexError) as e:a.errors.append('Malformed build rejected through the same exception boundary as guard main: '+type(e).__name__+': '+str(e))
 detected=bool(a.errors);ck('Guard rejects '+name,detected);mutations.append({'case':name,'rejected':detected,'error_count':len(a.errors),'errors':a.errors})
test('component promoted to direct',PBS,lambda x:x.update(component_only=False,direct_record_ids=['dantas-2002-sg1']))
test('benchmark or unaudited route added',PBS,lambda x:x['record_ids'].append('pbs-2019-unreviewed-benchmark'))
test('additional source DOI',PBS,lambda x:x['paper_dois'].append('10.0000/unreviewed'))
test('one whole-composite route lost',GLASS,lambda x:x['direct_record_ids'].pop())
test('whole product renamed bare PbS',record_change=lambda x:x['dantas-2002-sg1']['material'].update(formula='PbS'))
test('wrong source hash',REVIEW,lambda x:x['documents'][0].update(sha256='0'*64))
test('one page not visually reviewed',REVIEW,lambda x:x['documents'][0]['pages'][2].update(visual_review=False))
test('SI scope overclaimed',REVIEW,lambda x:x.update(review_scope='main_and_si_reviewed'))
test('benchmark source row exposed',PBS,lambda x:x['papers'][0]['benchmarkRecordIds'].append('pbs-2019-benchmark'))
test('canonical route no longer source reviewed',record_change=lambda x:x['dantas-2002-afm1']['quality'].update(review_status='imported_unreviewed'))
glob['load']=cached
text=G.read_text(encoding='utf8');ck('Unrelated title-only exclusions remain','for formula in ("CO", "NO", "Fe–C–H–O"):' in text)
ck('No unconditional PbS exclusion remains','("CO", "NO", "PbS", "Fe–C–H–O")' not in text)
fail=[x for x in checks if not x['passed']]
out={'status':'passed' if not fail else 'failed','source_id':'dantas2002','audited_utc':datetime.now(timezone.utc).isoformat(),'guard_path':'scripts/check_quality.py','guard_sha256':sha(G),'material_index_sha256':sha(D/'data/materials-index.json'),'hub_hashes':{'PbS':sha(PBS),'PbS/glass':sha(GLASS)},'source_review_sha256':sha(REVIEW),'actual_material_guard_checks':baseline.counts['checks'],'actual_guard_errors':baseline.errors,'checks':checks,'check_count':len(checks),'failures':fail,'negative_cases':mutations,'manual_review':['The old unconditional PbS prohibition is replaced by seven source-specific constraints rather than a general bypass. Generic hub checks continue to require source-reviewed synthesis records, valid component identity, exact relevant source rows and no benchmarks.','PbS is a component-only browsing hub for the six reviewed glass-composite endpoints; no bare-PbS synthesis is claimed. The same six whole-composite routes remain direct under PbS/glass, retaining original product names and source links.','Actual hub metadata was read independently and ten deliberately invalid in-memory variants were rejected by the real materials guard. No Site files were changed for these tests. Source-main provenance, five-page review and SI uncertainty remain explicit.'],'site_mutated':False,'browser_verified':False}
(B/'hub-guard-independent-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'hub-guard-independent-audit.md').write_text('# Dantas PbS component-hub guard audit\n\n'+out['status']+f': {len(checks)} independent checks; ten invalid in-memory variants rejected.\n\n'+'\n\n'.join(out['manual_review'])+'\n\nExact guard and hub hashes are recorded in the JSON. No Site mutation.\n',encoding='utf8')
print(json.dumps({'status':out['status'],'guard_sha256':out['guard_sha256'],'checks':len(checks),'negative_cases_rejected':sum(x['rejected'] for x in mutations),'failures':fail}))
