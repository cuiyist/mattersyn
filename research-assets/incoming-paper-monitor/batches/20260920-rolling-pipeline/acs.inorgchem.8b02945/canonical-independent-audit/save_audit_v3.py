"""Freeze the independent v3 delta conclusion after actual manual display review."""
from pathlib import Path
from copy import deepcopy
import json, hashlib, datetime
O=Path(__file__).resolve().parent; F=O.parent; C=F/'canonical-proposal/draft-v3'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
prior=read(O/'independent-audit-v2.json'); check=read(O/'v3-delta-checks.json')
assert check['status']=='passed' and not check['failures'] and not check['reader_validator_errors']
actual=read(O/'reader-v3-all-delta.json')
declared=read(C/'reader-revision3-delta.json')['reader_delta']
assert actual==[{'path':x['pointer'],'before':x['before'],'after':x['after']} for x in declared]
bound=deepcopy(prior['bound_files']);bound.update(check['bound_files'])
for n in ['independent-audit-v2.json','check_v3_delta.py','save_audit_v3.py','v3-delta-checks.json','reader-v3-all-delta.json','reader-v3-changed-prose.json','reader-v3-changed-prose.txt']:
 bound[str(O/n)]=sha(O/n)
for p,h in bound.items():
 assert sha(p)==h,(p,'changed dependency')
out=deepcopy(prior)
out.update({'status':'passed','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'revision':3,
 'proposal_freeze_sha256':sha(C/'package-freeze.json'),'reader_sha256':sha(C/'reader/friedfeld2019.json'),
 'prior_audit_sha256':sha(O/'independent-audit-v2.json'),'open_findings':[],
 'resolved_findings':[{'id':'FR-CAN-01','resolution':'Read all 351 changed item prose fields and the top-level labels, 12 conflict descriptions and mirrored figure captions. Readable prose preserves all numerical, missingness and sample qualifications; raw source payloads and typed scientific objects are unchanged.'},{'id':'FR-CAN-02','resolution':'Exactly 62 existing named record/sample/product-pointer links were added to their source context cards; no new sample or physical-batch assertion was introduced.'}],
 'delta_scope':{'canonical_records_byte_identical':30,'reader_items':417,'typed_reader_fields_unchanged':2131,'measurements_unchanged':750,'original_crops_unchanged':51,'named_sample_links_added':62,'changed_item_prose_fields_manually_read':351,'independently_recomputed_reader_delta_entries':len(actual),'declared_delta_exactly_matches_independent_delta':True,'raw_scientific_item_fields_unchanged_except_exact_supported_links':True,'top_level_scientific_fields_unchanged':True,'current_reader_validator_errors':[]},
 'supporting_check_counts':{**prior['supporting_check_counts'],'v3_hash_and_delta_checks':check['check_count']},
 'manual_v3_scopes':['Read every changed operation, figure, sample-context, conflict, methods, source-unit and table display field. All 351 changed item prose fields were inspected; all top-level changed labels and narratives were inspected, with 44 figure captions checked equal to their reviewed item prose.','Checked low-temperature labels, source 30/72 h conflict, undefined TEM ± uncertainty, cited-only preparation, varied-concentration stock exclusions, phase/fraction and optical/NMR boundaries remain explicit.','Verified two original-asset labels and equation labels only remove the extra space in S38/S39. Paths, crop hashes and source renderers are unchanged.','Directly executed the current Site reader validator against the frozen private v3 fixture; no author builder was executed as audit evidence.','Carried the passed canonical transport/schema/scientific checks from v2 through exact byte equality of all 30 records and complete non-display reader equality. No redundant new full-source read or model/browser qualification is claimed.'],
 'bound_files':bound})
path=O/'independent-audit-v3.json'
assert not path.exists(),'Do not overwrite a frozen final audit'
path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(O/'independent-audit-v3.md').write_text('# Friedfeld canonical/reader v3 independent audit\n\nStatus: passed; no open findings.\n\n'+out['role_disclosure']+'\n\nThe v3 correction changes only reviewed display text and 62 supported named sample links. All 30 canonical record bytes, 750 measurements, 2,131 typed reader fields and 51 original crops remain unchanged. The independent delta exactly matches all '+str(len(actual))+' declared edits. The current reader validator and '+str(check['check_count'])+' bounded hash/delta checks passed.\n\n'+'\n'.join('- '+x for x in out['manual_v3_scopes'])+'\n\nThe original v2 findings remain preserved. This audit does not admit training tasks, atomic structures, Site integration, browser rendering or publication. No source, author or Site files were edited.\n',encoding='utf8')
print(json.dumps({'audit':str(path),'sha256':sha(path),'bound_files':len(bound),'checks':check['check_count'],'delta_entries':len(actual)}))
