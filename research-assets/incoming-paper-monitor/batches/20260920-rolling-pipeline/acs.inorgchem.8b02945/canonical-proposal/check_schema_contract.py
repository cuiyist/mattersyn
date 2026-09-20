"""Synthetic current-consumer probes; no Friedfeld canonical record is created."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib,sys
sys.dont_write_bytecode=True
C=Path(__file__).resolve().parent;F=C.parent;O=C/'contract-probes-v1'
assert not (O/'contract-probe-manifest.json').exists(), 'Preserve completed contract probes.'
O.mkdir(parents=True,exist_ok=True)
S=Path('[local path redacted]');sys.path.insert(0,str(S/'scripts'))
from record_helpers import record,source,fact,qty,material,operation,state,product,measurement
from dataset_lib import validate_record,eligibility,build_groups
import build_paper_reviews as reader
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
e=[{'source_id':'synthetic-schema-probe','locator':'Synthetic contract fixture only; no source claim or scientific approval.'}]
src=source('synthetic-schema-probe','synthetic-fixture','Contract fixture','No scientific author',None)
src.update(doi=None,url='',main_status='Synthetic only',si_status='Synthetic only')
r=record('synthetic-schema-probe','Synthetic schema contract','Unspecified','Schema tests','No experimental method',src,'Synthetic only','procedure')
r['schema_version']='1.3.0';r['quality'].update(review_status='imported_unreviewed',requested_tasks=[],review_scope='Synthetic consumer test, not a Friedfeld record.')
r['intended_target']['composition']=fact(None,e)
r['materials']=[material('input-reference','Synthetic input reference',None,'process_material','workup',e)]
r['material_states']=[state('separate-contexts','Separate specimens, not a mixture',['input-reference'],'sample_set'),state('probe-data','Synthetic analysis output',['separate-contexts'],'analysis_data')]
r['operations']=[operation('probe-operation','characterize','Synthetic characterization',e,['separate-contexts'],['probe-data'],stage='characterization',
    parameters={'numeric_duration':qty(None,'h',e,'not_reported',raw_text='overnight',qualifier='Synthetic qualitative duration example; no numeric duration is asserted.')},
    description='This synthetic operation exercises a valid quantity/fact transport shape only.')]
r['products']=[product('probe-context',None,e,link='general_context')]
r['measurements']=[measurement('qualitative-duration','probe-context','qualitative_duration',fact('overnight',e),'Synthetic contract',e),
    measurement('bounded-duration','probe-context','bound',qty(None,'min',e,'reported',maximum=20,maximum_exclusive=True,raw_text='<20'), 'Synthetic contract',e),
    measurement('unknown-unit','probe-context','source_value_unknown_unit',qty(1,'',e,'reported',raw_text='1',qualifier='Synthetic example: unit not supplied.'),'Synthetic contract',e)]
errors=validate_record(r);ck('actual schema accepts explicit numeric unknown plus separate reported qualitative fact',not errors)
ck('actual task admission stays empty',not any(v['eligible']for v in eligibility(r).values()))
ck('actual one-source grouping',len(set(build_groups([r]).values()))==1)
bad=deepcopy(r);bad['operations'][0]['parameters']['numeric_duration']['status']='reported'
ck('reported numeric null without a bound is rejected',bool(validate_record(bad)))
fixture=O/'isolated-fixture';(fixture/'data/records').mkdir(parents=True,exist_ok=True);(fixture/'dist').mkdir(exist_ok=True)
(fixture/'data/records/synthetic-schema-probe.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
rv={'paper_id':'synthetic-schema-probe','review_scope':'supplied_main_and_matched_si',
    'documents':[{'role':role,'sha256':'0'*64,'page_count':1,'pages':[{'page':1,'text_read':True,'visual_review':True}]}for role in ['main','si']],
    'figures':[],'recipe_inventory':[{'record_ids':['synthetic-schema-probe']}],
    'reader_sections':[{'id':'properties','items':[{'id':'synthetic-property','title':'Synthetic fixture','facts':[]}]}],
    'characterization_inventory':{'reader_item_ids':['synthetic-property']},
    'route_evidence_contexts':{'synthetic-schema-probe':['synthetic-schema-probe']}}
oldroot=reader.ROOT
try:
    reader.ROOT=fixture
    ck('actual reader consumer accepts supported scope and resolvable item/record links',reader.validate(rv)==[])
    badr=deepcopy(rv);badr['review_scope']='complete_supplied_main_and_matched_si'
    ck('actual reader rejects old unsupported scope token',any('recognized review_scope'in e for e in reader.validate(badr)))
    badr=deepcopy(rv);badr['characterization_inventory']={'reader_item_ids':['absent-item']}
    ck('actual reader rejects unresolved characterization item',any('characterization'in e for e in reader.validate(badr)))
    badr=deepcopy(rv);badr['recipe_inventory'][0]['record_ids']=['absent-record']
    ck('actual reader rejects unresolved canonical record',any('recipe link'in e for e in reader.validate(badr)))
finally:reader.ROOT=oldroot
save('synthetic-reader-fixture.json',rv)
save('consumer-probe-results.json',{'status':'passed_synthetic_contract_only','checks':checks,'count':len(checks),
    'scope':'Actual current validator/eligibility calls on clearly synthetic private fixtures, not Friedfeld source or reader approval.',
    'source_record_count':0,'source_page_reread_count':0,'actual_browser_session':False,
    'validator_scope_limit':'The reader list branch does not enforce object-only characterization entries or route-context ID types; final author checks must enforce these explicitly.',
    'current_consumer_hashes':{str(S/'scripts'/n):sha(S/'scripts'/n)for n in ['schema_definition.py','record_helpers.py','dataset_lib.py','build_paper_reviews.py','review_scope.py']}})
cp=read(C/'mapping-draft-v1/mapping-checkpoint.json');fr=read(F/'package-freeze.json')
expected='7599e47c1ef1d43d56b2f4f835e4b550a1ef652aecca2e9dd8e593abc5769c04'
ck('source author freeze is the communicated exact version',sha(F/'package-freeze.json')==expected)
bf0=fr['bound_files'];assert isinstance(bf0,dict)
bf={str(Path(p) if Path(p).is_absolute()else F/p):(h['sha256']if isinstance(h,dict)else h) for p,h in bf0.items()}
bad=[p for p,h in bf.items()if sha(p)!=h];ck('all frozen source author inputs retain their bound bytes',not bad)
ck('all mapping inputs equal completed author freeze',all(sha(p)==h and bf.get(p)==h for p,h in cp['source_input_hashes'].items()))
save('source-freeze-binding-addendum.json',{'status':'source_author_freeze_bound_independent_source_audit_pending','created_at':datetime.now(timezone.utc).isoformat(),
    'source_author_freeze_sha256':expected,'source_bound_files_checked':len(bf),
    'mapping_checkpoint_sha256':sha(C/'mapping-draft-v1/mapping-checkpoint.json'),
    'mapping_inputs_equal_source_author_freeze':True,
    'note':'The mapping README was drafted while the source freeze was being finalized. The source author freeze now exists and matches all mapping inputs; scientific audit remains pending.',
    'source_scientific_approval':False,'canonical_or_reader_scientific_approval':False,'checks':checks[-3:]})
save('contract-probe-manifest.json',{'status':'preserved_private_contract_probe','created_at':datetime.now(timezone.utc).isoformat(),
    'author':'/root/norberg2004_extract','checks':len(checks),'source_canonical_records_written':0,
    'bound_files':{str(p):sha(p)for p in O.rglob('*')if p.is_file()},'script_sha256':sha(__file__)})
print(json.dumps({'status':'passed','checks':len(checks),'manifest':str(O/'contract-probe-manifest.json'),'sha256':sha(O/'contract-probe-manifest.json')}))
