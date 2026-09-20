from pathlib import Path
import json,hashlib,copy,datetime
from inspect_revision_delta import diff
A=Path(__file__).parent;R=A.parent;S=A/'author-v1-read-snapshot';checks=[]
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(name,x):checks.append({'check':name,'passed':bool(x)})
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
old=load(S/'source-facts.json');new=load(R/'source-facts.json');freeze=load(R/'package-freeze.json');prior=load(S/'package-freeze.json')
check('expected source v2 freeze',sha(R/'package-freeze.json')=='fb2aa081c3c33972454111a4631ffcf944b66f2b78bfec2894564745bccf072b')
for p,h in freeze['bound_files'].items():check('current input hash '+p,Path(p).exists() and sha(p)==h)
for p,h in freeze['source_hashes'].items():check('original hash '+p,sha(p)==h)
arch=load(R/'source-extraction-revision-1/preserved-file-map.json')
check('archived prior freeze bytes',sha(R/'source-extraction-revision-1/package-freeze.json')==sha(S/'package-freeze.json'))
for p,h in prior['bound_files'].items():
 check('archival binding '+p,p in arch and arch[p]['sha256']==h)
 if p in arch:check('archived bytes '+p,sha(arch[p]['archive_path'])==h)
replacements={'Figure 4 and preceding discussion':'Al-only precursor paragraph before the Figure 3 discussion','Figure 3 discussion':'Discussion below Figure 4: reciprocal-space ZnO dimensions','Laboratory Synthesis and Figure 8':'Laboratory Synthesis and Figure 9 inset'}
def normalize_locators(x):
 if isinstance(x,list):return [normalize_locators(v) for v in x]
 if isinstance(x,dict):return {k:(replacements.get(v,v) if k=='locator' else normalize_locators(v)) for k,v in x.items()}
 return x
expected=copy.deepcopy(old);expected['created_at']=new['created_at']
affected_ids={'sommer2020-d4-solution','sommer2020-d2-size','sommer2020-mw-middle-outcome'}
expected['facts']=[normalize_locators(f) if f['id'] in affected_ids else f for f in expected['facts']]
expected['protocols']=[normalize_locators(p) if p['id']=='pdf-procedure' else p for p in expected['protocols']]
ef={x['id']:x for x in expected['facts']};nf={x['id']:x for x in new['facts']}
ef['sommer2020-insitu-nobase']['claim']=ef['sommer2020-insitu-nobase']['claim'].replace('low crystallinity/yield','low yield')
ef['sommer2020-workup']['claim']=ef['sommer2020-workup']['claim'].replace('This workup is not automatically','Apply this workup separately to the microwave, SCF and autoclave powders; these are alternative specimens, never a pooled charge. This workup is not automatically')
stock=next(x for x in expected['stocks'] if x['id']=='insitu-base-solutions')
stock['quantities']=stock['quantities'][:1]
stock['notes']+=' Only the 1.00 mL NaOH-solution aliquot applies to this stock entry; the nitrate aliquot and final Zn/Al concentrations belong to the mixed reaction, retained in sommer2020-insitu-mix and the insitu-mix operation.'
stock['mixed_reaction_context']={'source_fact_id':'sommer2020-insitu-mix','protocol_id':'insitu-nitrate','operation_id':'insitu-mix'}
for p in expected['protocols']:p['specimen_application']='Each listed specimen is processed separately; grouped reactor-family inputs are alternatives, never a pooled physical charge.'
added=nf['sommer2020-cited-zno-heating'];q=added['quantities'][0]
check('one new fact',set(nf)-set(ef)=={'sommer2020-cited-zno-heating'} and len(added['quantities'])==1)
check('new cited-context class and scope',added['claim_class']=='cited_context' and added['sample_scope']=='literature-zno-formation')
check('new range exact source',q['raw_text']=='150-350' and q['value'] is None and q['range']=={'min':150.0,'max':350.0} and q['unit']=='degC' and not q['approximate'])
check('new range source locator',all(e['pdf_page']==3 and e['source_sha256']==next(iter(freeze['source_hashes'].values())) and 'reference 42' in e['locator'] for e in added['evidence']+q['evidence']))
check('new fact excludes current D2 condition and unread cited paper','not a demonstrated heating condition' in added['claim'] and 'cited full paper was not independently read' in added['claim'])
expected['facts'].append(added)
check('only the approved source-fact changes',expected==new)
for f in old['facts']:
 of=normalize_locators(f) if f['id'] in affected_ids else f;actual=nf[f['id']]
 check('all original quantities preserved '+f['id'],of['quantities']==actual['quantities'])
for p in new['protocols']:
 for op in p['operations']:check('cited temperature not a current operation '+op['id'],'sommer2020-cited-zno-heating' not in op.get('source_fact_ids',[])+op.get('context_fact_ids',[]))
check('mixed reaction all four values preserved',nf['sommer2020-insitu-mix']['quantities']==ef['sommer2020-insitu-mix']['quantities'] and len(nf['sommer2020-insitu-mix']['quantities'])==4)
oldi=load(S/'source-inventory.json');newi=load(R/'source-inventory.json')
oldi['inventory_units']=[normalize_locators(u) if u['source_object_id'] in affected_ids|{'pdf-solutions'} else u for u in oldi['inventory_units']]
ou={x['id']:x for x in oldi['inventory_units']};nu={x['id']:x for x in newi['inventory_units']}
check('332 unique units',len(newi['inventory_units'])==len(nu)==332)
check('one added unit',set(nu)-set(ou)=={'fact:sommer2020-cited-zno-heating'})
for k,v in ou.items():check('all old inventory units preserved '+k,nu.get(k)==v)
expectedi=copy.deepcopy(oldi);expectedi['created_at']=newi['created_at'];expectedi['counts'].update({'facts':65,'fact_quantities':137,'inventory_units':332});expectedi['inventory_units']=newi['inventory_units']
check('inventory metadata change only',expectedi==newi)
def ptr(x,p):
 for k in p.lstrip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~');x=x[int(k)] if isinstance(x,list) else x[k]
 return x
cache={'source-facts.json':new,'source-tables.json':load(R/'source-tables.json')}
for u in newi['inventory_units']:
 if u['path'] not in cache:cache[u['path']]=load(R/u['path'])
 try:v=ptr(cache[u['path']],u['json_pointer']);ok=v.get('id',v.get('row_label'))==u['source_object_id']
 except Exception:ok=False
 check('current pointer '+u['id'],ok)
check('unchanged source-tables.json',sha(S/'source-tables.json')==sha(R/'source-tables.json'))
for name in ['original-assets-manifest.json','page-coverage.json']:
 expectedmeta=load(S/name);actualmeta=load(R/name);expectedmeta['created_at']=actualmeta['created_at']
 if name=='page-coverage.json':expectedmeta['pages'][2]['fact_ids'].append('sommer2020-cited-zno-heating')
 check('metadata-only approved changes '+name,expectedmeta==actualmeta)
for p,h in prior['bound_files'].items():
 if any(t in p for t in ['reader-assets','source-render','private\\text']):check('unchanged source/crop '+p,sha(p)==h)
check('source conflicts/equations/samples unchanged',all(old[k]==new[k] for k in ['conflicts','missingness','equations','sample_contexts','materials','figures','references']))
check('65 facts/137 quantities',len(new['facts'])==65 and sum(len(f['quantities']) for f in new['facts'])==137)
results={'reviewer':'/root/norberg2004_extract','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_freeze_sha256':sha(R/'package-freeze.json'),'checks':checks,'failed':[x for x in checks if not x['passed']],'passed':sum(x['passed'] for x in checks),'scientific_facts_delta':diff(old,new),'inventory_by_id_delta':diff(ou,nu),'scope':'Bounded independent final correction verification, with prior complete manual source/crop/table audit retained.'}
write(A/'revision-2-independent-checks.json',results)
print(json.dumps({'checks':len(checks),'failed':results['failed']},ensure_ascii=False))
if results['failed']:raise SystemExit(1)
v1=load(A/'independent-audit-v1.json');report=copy.deepcopy(v1)
report.update({'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed','audited_source_revision':2,'source_freeze_sha256':sha(R/'package-freeze.json'),'prior_audit_sha256':sha(A/'independent-audit-v1.json'),'independent_revision_checks':len(checks),'open_findings':[]})
report['manual_scope'].update({'facts':65,'fact_quantities':137,'inventory_units':332})
report['method']+=' Revision 2 was rechecked against preserved v1, with source-scoped review of the newly typed cited-context range and all five corrections. Unchanged pages/crops were hash-confirmed, not falsely counted as freshly reread.'
for finding in report['findings']:finding['status']='resolved_in_source_revision_2'
bound={str(R/'package-freeze.json'):sha(R/'package-freeze.json'),**freeze['bound_files'],**freeze['source_hashes']}
for p in [A/'independent-audit-v1.json',A/'independent-audit-v1.md',A/'mechanical-checks-v1.json',A/'independent-reading-checkpoint.json',A/'independent-reading-notes.md',A/'independent-table1.json',A/'revision-2-independent-checks.json',Path(__file__)]:bound[str(p)]=sha(p)
report['bound_files']=bound
write(A/'independent-audit-v2.json',report);write(A/'independent-audit.json',report)
md='# Independent Sommer source audit — revision 2\n\n**Passed for the supplied main article.** Reviewer `/root/norberg2004_extract`; separate author `/root/backlog_eta`.\n\nAll 11 supplied main pages and 20 selected crops were actually read/viewed. The review covers 65 source facts, 137 typed quantities, all 37 Table 1 rows (185 data cells plus 37 labels), 31 operations, 28 materials, 7 stocks, 44 sample contexts, 14 figures including the graphical abstract, 7 expressions, 65 printed references and 332 inventory units. The cited references were not themselves read as full papers.\n\nFive bounded findings were resolved in preserved revision 2: low-yield wording, mixed-reaction versus NaOH-stock quantities, three precise locators, one separately cited 150–350 °C context, and independent rather than pooled workup specimens. Existing numerical values, all table cells, formulas and all 20 crop bytes remain unchanged.\n\nThe initial 3,217 independent supporting checks passed; '+str(len(checks))+' further bounded checks verified the final revision and preserved v1. Source conflicts C1–C13 remain explicit.\n\n**SI is declared but locally unlocated/unverified.** This audit does not establish complete main-plus-SI coverage, exact structure–recipe pairing, training eligibility, canonical/visual integration, mounted browser or publication approval.\n\nFinal source freeze SHA256: `'+report['source_freeze_sha256']+'`. Exact bound inputs and correction history are in the JSON.\n'
for name in ['independent-audit-v2.md','independent-audit.md']:(A/name).write_text(md,encoding='utf-8')
print(json.dumps({'status':'passed','audit':str(A/'independent-audit-v2.json'),'audit_sha256':sha(A/'independent-audit-v2.json'),'bound_files':len(bound)}))
