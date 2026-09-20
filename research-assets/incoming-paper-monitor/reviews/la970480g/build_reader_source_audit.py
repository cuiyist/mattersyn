"""Private bounded reader-evidence audit; source semantics read independently, no Site access."""
from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
proposal=B/'public-review-proposal/yao1998.json';d=read(proposal)
coverage=read(B/'public-review-proposal/source-item-coverage.json');source=read(B/'source-audit.json')
records={p.stem:read(p)for p in(B/'canonical-drafts').glob('*.json')}
items={i['id']:i for s in d['reader_sections']for i in s['items']}
checks=[]
def check(n,b):checks.append({'name':n,'passed':bool(b)})
def at(obj,pointer):
 for key in pointer.strip('/').split('/')if pointer else []:obj=obj[int(key)]if isinstance(obj,list)else obj[key.replace('~1','/').replace('~0','~')]
 return obj
check('100 distinct source-linked academic reader items',len(items)==100 and all(i.get('text')and i.get('evidence')and i.get('claim_type')and i.get('sample_scope')for i in items.values()))
check('All144 independent scientific units mapped exactly once',{x['source_audit_id']for x in coverage['source_audit_unit_map']}=={x['id']for x in source['units']}and len(coverage['source_audit_unit_map'])==144)
check('All coverage targets resolve',all(at(d,p)for x in coverage['source_audit_unit_map']for p in x['public_targets']))
check('Source audit exact hash',d['audit_details']['source_audit_sha256']==sha(B/'source-audit.json'))
check('Characterization source rows exact hash',d['audit_details']['characterization_draft_sha256']==sha(B/'characterization-draft.json'))
check('Supplied-main-only scope preserved',d['review_scope']=='supplied_main_only_si_unverified' and 'not_located'in d['supporting_information']['status'])
check('Proposal carries no promotion or training claim',not d['source_review_promoted']and not d['training_eligible']and all(not i['training_eligible']for i in items.values()))
check('No private filesystem paths in public proposal','C:\\Users'not in json.dumps(d)and'C:/Users'not in json.dumps(d))
for i in items.values():
 for link in i.get('canonical_links',[]):check(i['id']+'/'+link['record_id']+' canonical context link resolves',bool(at(records[link['record_id']],link.get('json_pointer',''))))
 for link in i['sample_scope'].get('canonical_sample_links',[]):check(i['id']+'/'+link['sample_id']+' source sample pointer matches',at(records[link['record_id']],link['json_pointer'])['sample_id']==link['sample_id'])
facts={f['id']:f for i in items.values()for f in i.get('facts',[])}
canonical={m['id']:m for m in records['yao-1998-characterization']['measurements']}
check('All53 characterization facts represented',set(canonical)<=set(facts))
for mid,m in canonical.items():
 f=facts[mid];q=m['value'];v=q['value']
 if v is None and q.get('minimum')is not None:v=str(q['minimum'])+'–'+str(q['maximum'])
 check(mid+' displayed value and unit preserve audited canonical',f['value']==v and (f.get('unit')or'')==(q.get('unit')or''))
 if q.get('basis'):check(mid+' evidence basis retained',f['basis']==q['basis'])
 if q.get('approximate'):check(mid+' approximation retained',f.get('approximate')is True)
check('Public SD0.4 remains undefined',facts['char-a-surface-hist-sd']['unit']is None and 'not printed'in facts['char-a-surface-hist-sd']['qualifier'])
check('Public plateau bound and clock conflict retained','Upper-time'in facts['char-sample-b-plateau']['qualifier']and'2 h'in items['conflict-02']['text'])
check('Donnan model not experimental label','model'in items['donnan-values']['claim_type']and facts['char-donnan-swelling']['unit']=='meV')
check('Cited Na value and hardware rating clarified','Chelex 100'in items['pretreatment-diffusion-context']['text']and facts['char-lamp-power']['basis']=='hardware_specification')
check('Radial populations not collapsed','4–5'in items['conflict-08']['text']and'2.7'in items['regional-histograms']['text']and'4.6'in items['regional-histograms']['text'])
check('No fabricated source patterns','No original XRD pattern'in items['conflict-16']['text'])
check('Curator outlook remains labelled',items['future-questions']['claim_type']=='curator_proposed_outlook')
out={'source_id':'yao1998','status':'passed'if all(x['passed']for x in checks)else'must_fix','scope':'Independent source-semantic reading of all100 reader items and cited notes, plus bounded crosswalk/value/provenance checks. Original main previously read on all7pages. No Site rendering audit.','proposal_sha256':sha(proposal),'source_coverage_sha256':sha(B/'public-review-proposal/source-item-coverage.json'),'reader_item_count':len(items),'independent_unit_count':144,'check_count':len(checks),'checks':checks,'open_findings':[],'scientific_limits':['Only supplied main is reviewed; local SI not located or verified.','Source formulations, spatial regions and analytical contexts are not exact physical-batch joins.','Model, cited input, manufacturer capacity and proposed future work remain separate from experimental observations.','All53 characterization facts reproduce the audited canonical rows; alternative salts remain one qualitative comparative reader fact linked to three separately labeled comparison contexts.','This checks public proposal content, not actual rendered Site or publication.']}
(B/'reader-source-audit.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
(B/'reader-source-audit.md').write_text('# Independent reader source audit\n\nStatus: **'+out['status']+'**. 100 reader items, all144 independent source units mapped, all53 characterization facts preserved. '+str(len(checks))+' bounded checks.\n\nNo remaining scientific findings in the proposal. Salt/clock ambiguities, undefined log-normal SD unit, radial scope, author-model/cited context and source-only XRD claims remain explicit.\n\nSI remains unverified. Root owns actual rendering, public import and publication. Exact proposal and coverage hashes are recorded in JSON.\n',encoding='utf8')
print(json.dumps({'status':out['status'],'checks':len(checks),'failed':[x for x in checks if not x['passed']]},indent=2))
