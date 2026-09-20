import datetime,hashlib,json,sys
from pathlib import Path
M=Path('[local path redacted]');O=Path(__file__).parent;F=O.parent;S=M/'recipe-atlas';P=F/'site-integration-proposal'
sys.path.insert(0,str(M/'research-assets'));from sync_github_public import io_path
def sha(p):return hashlib.sha256(io_path(Path(p)).read_bytes()).hexdigest()
def read(p):return json.loads(io_path(Path(p)).read_text(encoding='utf-8-sig'))
def save(p,x):io_path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
c=read(O/'integration-checks.json');d=read(O/'integration-dispatch-checks.json')
assert c['status']=='passed' and d['passed']
bound=c['bound_files']
for p in [O/'integration-checks.json',O/'integration-dispatch-checks.json',O/'integration-checks-initial-diagnostics.json',O/'check_integration.py',O/'check_integration_dispatch.mjs',Path(__file__)]:bound[str(p)]=sha(p)
for name,rel in [('integration-baseline-reader.json','data/paper-reviews/friedfeld2019.json'),('integration-baseline-public-reader.json','dist/data/paper-reviews/friedfeld2019.json')]:
 p=O/name
 if not p.exists():io_path(p).write_bytes(io_path(S/rel).read_bytes())
 assert sha(p)==bound[str(S/rel)]
 bound[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bound.items()),'Inputs changed before final freeze'
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
r={'audit_id':'friedfeld2019-actual-site-integration-transport-v1','status':'passed','author':'/root','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','created_at':now,
 'proposal_freeze_sha256':c['proposal_freeze_sha256'],'promotion_audit_sha256':sha(O/'promotion-delta-audit.json'),
 'scope':'Read-only actual Site integration transport and source-specific dispatch audit. Separate from the prior proposal audit and all browser/publication gates.',
 'findings':[],'open_findings':[],
 'counts':{'existing_records_preserved':626,'new_records':30,'total_records':656,'routes':122,'material_hubs':49,'old_training_exports_byte_unchanged':6,'new_training_tasks':0,'new_exact_structure_pairs':0,'public_assets':162,'selected_original_crops':51,'new_registry_entries':53,'chemical_entries':39,'symbolic_product_entries':14,'material_slots':77,'solutions':8,'stock_components':16,'product_contexts':88,'reader_items':417,'reader_field_links':2131,'apparatus_instances':58},
 'checks':{'transport_schema_hash_assertions':c['summary'],'actual_module_dispatch_assertions':d['executed'],'actual_module_dispatch_passed':d['passed'],'prior_other_source_operation_instances_rejected':d['unrelated_operation_instances'],'final_files_rehashed':len(bound)},
 'results':[
  'All 30 actual canonical and public record files are byte-identical to the passed frozen promotion proposal; every original 626 canonical file matches the pre-import hash inventory.',
  'All six task-export files match their pre-import bytes. Actual current eligibility remains false for every Friedfeld task; no training or measured coordinate pair is introduced.',
  'Actual reader differs only by local integration status, removal of the explicitly resolved workflow-gap sentence and two passed audit digests. All scientific cards, source locators, sample assignments, values and conflict fields are unchanged. Public reader differs only by the supported scope label.',
  'All 162 actual public asset files match the allowlist and proposal bytes. The Friedfeld-scoped asset inventory has no extras, whole pages, PDFs or complete-source payloads. Public model/module/SVG text contains no private local paths.',
  'Registry merge equals retained baseline plus the 39 chemical and 14 symbolic entries with published/binding flags. Every prior registry entry, binding, solution and product context remains structurally unchanged. All exact 77 material bindings, eight solutions/sixteen components, 88 product mappings and measurement-display additions match the frozen proposal.',
  'Retained Python/MJS code and static page baselines replay exactly through documented import edits and cache revisions. Dataset and inventory HTML are regenerated count pages; this audit verifies their source data rather than claiming browser rendering.',
  'The imported apparatus module recognizes all 58 exact source operation pairs, rejects each with wrong source/record/operation identifiers, and rejects all 1,899 operation instances from the 626 earlier records. Existing dispatch order is retained after the added Friedfeld guard.',
  'Generated dataset/inventory report v0.32.0, 656 records, 122 routes and 49 hubs. Four Friedfeld routes reach the InP hub; all 30 records reach the source library/reader and declared contextual records resolve. Contextual procedures are not blanket-assigned as independent InP syntheses.'
 ],
 'reader_delta':c['reader_delta'],
 'manual_review_scope':['Read import script and documented code delta; assessed additive/scoped changes and preflight guards.','Reviewed exact reader integration metadata and resolved workflow-gap deletion.','Read source-specific module guard and compared code replay; executed actual dispatch factory without a browser.'],
 'checker_history':'Initial diagnostics are preserved. Thirty initial manifest checks incorrectly used serialized-file SHA instead of the documented canonical JSON-content digest; one initial hub check incorrectly required all source procedures/observations as direct material evidence. Corrected assertions follow the actual builder contracts and preserve conservative source scope. No author change was needed.',
 'pending_separate_gates':['Root browser interaction/rendering review','Announced forthcoming 33 page-note wording and browser-flag metadata addendum','Publication and anonymous-delivery verification'],
 'baseline_limit':'Prior-state preservation is checked against the import-time base-record/base-export inventories and retained base-site-inputs. This report does not treat an older unrelated Git checkout as that immediate pre-import baseline.',
 'bound_files':dict(sorted(bound.items()))}
save(O/'integration-audit.json',r)
io_path(O/'integration-audit.md').write_text(f'''# Friedfeld actual integration transport audit

**Passed; no required corrections.** Author `/root`; independent auditor `/root/backlog_eta`.

The actual Site matches proposal `{c['proposal_freeze_sha256']}`. All 30 imported canonical/public records and 162 approved assets match exact bytes. The 626 prior records and all six training exports are unchanged. Reader science, 77 material slots, eight solutions/sixteen components, 88 symbolic product contexts and display mappings are preserved.

All {c['summary']['executed']:,} transport/schema/hash assertions and {d['executed']:,} actual dispatch checks passed. The Friedfeld module recognizes its 58 operations and rejects all 1,899 operations from prior sources. Current totals are 656 records, 122 routes and 49 hubs, with no new training eligibility or exact structure–recipe pair.

Reader changes are integration/audit metadata and removal of one resolved workflow sentence. Recorded code edits replay exactly for retained Python/MJS files. No shared Site file was changed by the auditor, and no browser claim is made.

The proposed page-note prose cleanup and browser-status change require a separate narrow addendum after root applies them. Publication and live-delivery gates remain separate. Exact checks, history and {len(bound):,} file bindings are retained in the JSON report.
''',encoding='utf-8')
print(json.dumps({'status':r['status'],'audit_path':str(O/'integration-audit.json'),'audit_sha256':sha(O/'integration-audit.json'),'bound_files':len(bound),'checks':c['summary']['executed']+d['executed']},indent=2))
