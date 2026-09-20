from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas/dist';A=S/'assets/crystal-references'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
reuse=read(B/'ir-reference-reuse.json');registry=read(A/'registry.json');entry=next(e for e in registry['entries'] if e['id']=='ir-fcc');model=read(A/entry['modelPath']);record=read(S/'data/records/shah-2001-ir.json');viewer=(S/'crystal-viewer.mjs').read_text(encoding='utf8');checks=[]
def check(n,ok):checks.append({'check':n,'passed':bool(ok)})
check('captured-entry-matches-current-registry',reuse['entry']==entry)
check('CIF-bytes-unchanged',sha(A/entry['cifPath'])==entry['cifSha256']==reuse['unchanged_cif_sha256'])
check('model-bytes-unchanged',sha(A/entry['modelPath'])==entry['modelSha256']==reuse['unchanged_model_sha256'])
check('registry-reference-only',entry['referenceOnly'] is True and entry['trainingEligible'] is False)
check('model-reference-only',model['training_eligible'] is False and model['measured_sample_structure'] is False)
check('source-independent-COD-reference',model['source']['entry']=='9008470' and model['source']['year']==1963)
check('source-phase-not-transferred','Shah2001 reports crystalline Ir by microscopy without a refined phase assignment' in entry['scope'])
check('Stowell-context-explicitly-separated','belong only to Stowell2005' in entry['sample_context_note'])
check('actual-model-is-Ir-reference',all(a['element']=='Ir' for a in model['atoms']) and model['spaceGroupNumber']==225 and model['cell']['a']==3.8394)
check('record-phase-remains-unreported',record['intended_target']['phase']['value'] is None and all(p['phase']['value'] is None for p in record['products']))
check('no-sample-atomic-asset-added',record['structure_assets']==[])
check('not-requested-as-exact-structure-training','exact_structure_recipe' not in record['quality']['requested_tasks'])
check('no-exact-structure-export','shah-2001-ir' not in (S/'data/exports/exact_structure_recipe.jsonl').read_text(encoding='utf8'))
check('reference-heading-and-download-label','Reference crystal structures' in viewer and 'Download reference CIF' in viewer)
check('registry-scope-is-visible-caption',"el('small',ref.scope||ref.description)" in viewer)
check('bulk-atomistic-limit-visible','Independent bulk references for comparison' in viewer and 'not atom-by-atom reconstructions' in viewer)
check('no-Shah-Ag-Pt-reference-lattice-binding',not any(any(r.startswith('shah-2001-') and r!='shah-2001-ir' for r in e.get('record_ids',[])) for e in registry['entries']))
fail=[c for c in checks if not c['passed']]
report={'schema':'mattersyn-independent-reference-reuse-audit-1','source_id':'shah2001','status':'passed_reference_only_no_assignment_leak' if not fail else 'failed','checked_utc':datetime.now(timezone.utc).isoformat(),'scope':'Read-only Site audit of the reused local Ir bulk reference; no external download or coordinate changes. No live browser claim.','reuse_manifest_sha256':sha(B/'ir-reference-reuse.json'),'crystal_registry_sha256':sha(A/'registry.json'),'cif_sha256':sha(A/entry['cifPath']),'model_sha256':sha(A/entry['modelPath']),'viewer_module_sha256':sha(S/'crystal-viewer.mjs'),'published_record_sha256':sha(S/'data/records/shah-2001-ir.json'),'exact_structure_export_sha256':sha(S/'data/exports/exact_structure_recipe.jsonl'),'findings':['The reference is an unchanged COD bulk FCC Ir structure from a separate crystallographic source. It provides a comparison viewer/download and is not evidence of the Shah specimen phase.','Registry scope explicitly distinguishes Stowell FCC evidence from Shah qualitative crystalline-core microscopy. The viewer visibly uses this registry scope, and its headings/download labels call the structure a reference.','The model retains older Stowell-specific context internally, but has independent COD provenance and explicit non-measured/non-training flags; it is not rewritten into a Shah sample structure.','Shah intended/product phase fields remain unknown, no measured structure asset was inserted, and no Shah Ir entry exists in the exact-structure training export.','No Shah Ag or Pt reference lattice was added.'],'check_count':len(checks),'failure_count':len(fail),'checks':checks,'failures':fail}
(B/'ir-reference-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'failures':fail,'audit_sha256':sha(B/'ir-reference-audit.json')}))
