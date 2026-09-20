"""One-leaf source-unit correction; immutable v1 remains in its original location."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;O=B/'source-extraction-revision-2';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
old=read(B/'source-extraction-freeze.json')
assert sha(B/'source-extraction-freeze.json')=='7349d66b2580a48988729aabc6a3f867729ec7ae2198e91674bc0f2ca6719c5e'
for x in old['files']:assert sha(x['path'])==x['sha256']
f=read(B/'source-facts.json');corrected=deepcopy(f);target=corrected['facts'][444]
assert target['id']=='evans2010-cif-diffrn-measured-fraction-theta-max-diffrn-measured-fraction-theta-max' and target['value']==0.98 and target['unit']=='deg'
target['unit']='dimensionless'
save('source-facts.json',corrected)
reverse=deepcopy(corrected);reverse['facts'][444]['unit']='deg';assert reverse==f
delta={'schema':'mattersyn-preserved-source-revision/1','revision':2,'created_at':datetime.now(timezone.utc).isoformat(),'author':'/root/norberg2004_extract','independent_finding_author':'/root/peng1998_reader_assets','previous_freeze_path':str(B/'source-extraction-freeze.json'),'previous_freeze_sha256':sha(B/'source-extraction-freeze.json'),'old_facts_sha256':sha(B/'source-facts.json'),'corrected_facts_sha256':sha(O/'source-facts.json'),'changes':[{'json_pointer':'/facts/444/unit','source_fact_id':target['id'],'before':'deg','after':'dimensionless','reason':'The CIF tag reports the measured fraction, not the angular threshold. Original token 0.980 and all numerical/source values are unchanged.'}],'unchanged':['All 457 fact identities, values, raw tokens, bounds, evidence and sample scopes','All 198 units and all 25 original selected crops','Original main, SI and CIF bytes','All prior v1 files and freeze','The optional theta_full unit normalization was not performed; its original explicit tag-semantics fallback remains.'],'status':'author_correction_pending_independent_recheck'}
save('correction-history.json',delta)
checks=1
for x in old['files']:assert sha(x['path'])==x['sha256'];checks+=1
for x in old['source_documents'].values():assert sha(x['path'])==x['sha256'];checks+=1
save('correction-validation.json',{'status':'passed_bounded_author_checks','checks':checks,'exact_changed_leaves':1,'reverse_delta_restores_original_facts':True,'source_and_v1_unchanged':True,'independent_recheck':'pending'})
files=[x for x in old['files'] if x['relative_path']!='source-facts.json']
for name in ['source-facts.json','correction-history.json','correction-validation.json']:
 p=O/name;files.append({'path':str(p),'relative_path':str(p.relative_to(B)),'sha256':sha(p),'bytes':p.stat().st_size})
files.append({'path':str(Path(__file__)),'relative_path':Path(__file__).name,'sha256':sha(__file__),'bytes':Path(__file__).stat().st_size})
save('source-extraction-freeze.json',{'schema':'mattersyn-source-author-package-freeze/1','version':2,'source_id':'evans2010','doi':'10.1021/ja103805s','author':'/root/norberg2004_extract','status':'frozen_bounded_unit_correction_pending_independent_recheck','source_documents':old['source_documents'],'previous_freeze_sha256':sha(B/'source-extraction-freeze.json'),'effective_source_facts_path':str(O/'source-facts.json'),'effective_source_inventory_path':str(B/'source-inventory.json'),'files':files,'correction_history_sha256':sha(O/'correction-history.json'),'counts_unchanged':True,'training_eligible':False,'published':False})
print('V2FREEZE',sha(O/'source-extraction-freeze.json'));print('FACTS',sha(O/'source-facts.json'));print('HISTORY',sha(O/'correction-history.json'))
