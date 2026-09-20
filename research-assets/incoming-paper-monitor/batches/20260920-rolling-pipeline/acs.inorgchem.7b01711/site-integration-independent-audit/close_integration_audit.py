from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
A=Path(__file__).resolve().parent;N=A.parent;O=N/'site-integration-proposal'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=read(A/'integration-mechanical-checks.json');d=read(A/'integration-dispatch-checks.json')
assert m['status']==d['status']=='passed'
bound={**m['bound_files'],**d['bound_files']}
for p in [A/'integration-mechanical-checks.json',A/'integration-dispatch-checks.json',A/'integration-mechanical-before-label-correction.json',O/'reader-link-label-delta.json',O/'reader-label-rebuild-check.json',O/'empty-binding-delta.json',O/'mobile-provenance-wrap-delta.json',O/'final-check-output.json',O/'browser-validation.json',Path(__file__)]:bound[str(p.resolve())]=sha(p)
for p,h in bound.items():assert sha(Path(p))==h,p
report={
 'schema':'mattersyn.independent_site_integration_code_audit/1',
 'at':datetime.now(timezone.utc).isoformat(),
 'auditor':'/root/norberg2004_extract',
 'integration_author':'/root',
 'status':'passed','open_findings':[],
 'proposal_freeze_sha256':sha(O/'v1/package-freeze.json'),
 'product_context_freeze_sha256':sha(O/'product-context-v1/package-freeze.json'),
 'scope':'Actual local Site import, generated data, source-specific dispatch, inventory and bounded presentation-code deltas. This is not a fresh source or apparatus-science audit and is not proof of public deployment.',
 'independence':'This auditor authored the private apparatus module; its scientific qualification is the separately passed /root/peng1998_reader_assets audit. This audit checks exact module retention and ROOT-authored dispatch/import code, without self-approving apparatus science.',
 'checks':{'data_code_transport':m['checks'],'actual_dispatch_minimal_dom':d['counts']['checks'],'final_bound_hashes':len(bound)},
 'counts':m['counts'],
 'dispatch':d['counts'],
 'resolved_findings':[
  {'id':'MORRISON-INTEGRATION-01','finding':'All 18 canonical context links carry private_reader_pending_independent_review; the initial renderer alias handled the different Evans token, so stale review text remained in generated pages.','resolution':'Root preserved pre-correction code and added the exact source/token tuple alias to Source document review. All 18 generated labels and the complete reconstructed code delta pass. Canonical bytes unchanged.','evidence':'site-integration-proposal/reader-link-label-delta.json'},
 ],
 'other_bounded_root_corrections_verified':[
  {'change':'Seven explicit empty recordBindings and bindingNotes maps for zero-material observations','verification':'Complete merge reconstructed from original registry snapshot and passed proposal. Exactly the seven material-empty records gain these empty maps. All 64 populated slots, scientific notes and effective source hashes are unchanged.'},
  {'change':'Mobile source-hash wrapping','verification':'illustrated-guide.css equals its preserved snapshot plus only the declared overflow-wrap:anywhere;word-break:normal rule. Scientific provenance text is unchanged. Actual narrow-browser inspection belongs to root’s separately attributed report.'}
 ],
 'manual_scope':[
  'Read the complete root import, inventory and build/check orchestrators and their gate requirements, then inspected actual final deltas and current renderer logic.',
  'Reviewed exact append semantics for 29 chemical entries, all 64 material bindings, five solution contexts/10 components, 17 symbolic product contexts and the seven explicit empty observation maps. Historical canonical_record_sha256 in binding notes retains the audited input; sourceRecordSha256 identifies the promoted bytes.',
  'Checked source-specific measurement classification: 453 structural and 111 property IDs map directly to the passed reader sections; all remaining 258 measurements stay in the additional source-evidence table. All 822 generated measurement rows preserve displayed value, sample, technique and source.',
  'Checked 18 record copies, 1,170 exact reader fields, 30 selected original crops and 57 other approved files, with no source PDF, whole-page image or raw full text added to this public asset projection.',
  'Checked actual material hubs: the two shell routes contribute directly only to CdSe/CdS and as component contexts to the separate CdSe and CdS hubs; Cd(PTC)2 preparation/crystallization is not a new semiconductor synthesis hub. Source-scoped additional evidence records remain linked without physical-sample identity inference.',
  'Reconstructed all code changes from preserved base snapshots, including source dispatch, cache/version strings, exact reviewed-link alias and mobile CSS. Shared chemical/product renderer scientific logic is unchanged.',
  'Read final build/check reports as root-produced evidence, independently validated all 530 records with the actual schema/semantic gates, verified 512 previous raw hashes, old grouping and all exported allowlisted training rows.',
  'Executed actual integrated mountProtocol in a minimal DOM for all 24 stages and 155 adjacent rows; no duplicate generic conditions appeared. Morrison scene selection rejected all 1,716 pre-existing foreign operations without mutating canonical objects.'
 ],
 'author_evidence_attribution':{'root_browser_report':str(O/'browser-validation.json'),'root_browser_report_sha256':sha(O/'browser-validation.json'),'auditor_did_not_repeat_mounted_browser':True,'public_deployment_verified':False},
 'audit_helper_diagnostics':'Initial private checker assumptions treated historical binding-note hashes as current raw hashes, omitted the generated review_scope_label, and expected measurement IDs in HTML where rendered rows intentionally contain values/sample/source. Those diagnostic assertions were corrected against the existing contracts; only the stale visible reader status was an integration finding. The diagnostic file is retained, not counted as source errors.',
 'limitations':[
  'All measured atomic product-coordinate, exact structure–recipe and training gates remain unchanged; Morrison adds zero training tasks and zero exact structure pairs.',
  'No claim that this audit independently reread the entire Morrison paper, repeated molecular/apparatus science audits or personally operated the mounted browser.',
  'Bound to the exact local files below. Subsequent scientific/code edits require a scoped delta review; publication/release metadata and live hosting are separate.'
 ],
 'bound_files':bound}
(A/'integration-code-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
text=f'''# Morrison Site integration independent audit

Passed against the actual local integration. Auditor: `/root/norberg2004_extract`; root authored the import/code changes. No open findings.

- **512 previous records unchanged; 18 new records:** 2 shell routes, 8 procedures, 8 observations.
- **{m['checks']:,} transport/code checks + {d['counts']['checks']:,} actual dispatch checks**, and {len(bound):,} final hash bindings.
- 64 material slots, 5 solutions / 10 components, 17 symbolic product contexts; 29 chemical entries and 87 approved public assets, including 30 selected source crops.
- All 24 stages / 155 adjacent rows dispatch correctly. The source module rejects all 1,716 existing foreign operations. The apparatus scientific audit remains Peng’s distinct passed gate; this auditor checks byte retention/integration only.
- 453 structural, 111 property and 258 other source measurements retained; 1,170 reader field transports pass.
- Existing training counts and exports unchanged. No new task or exact structure–recipe pair.

The single independent finding was stale `private_reader_pending_independent_review` text. Root’s preserved, source-specific display correction is verified on all 18 pages. Seven empty observation binding maps and the narrow mobile provenance-wrap rule are also verified as exact bounded corrections.

The current canonical/input hash distinction is intentional: binding-note hashes identify immutable audited inputs; `sourceRecordSha256` separately binds promoted records. Scientific payloads and chemical/coordinate assets are unchanged.

Root’s actual browser report is cited separately; this audit did not repeat mounted-browser operation and does not certify public deployment. The exact-file JSON contains full provenance, scope and limitations.

Audit SHA256: `{sha(A/'integration-code-audit.json')}`
'''
(A/'integration-code-audit.md').write_text(text,encoding='utf-8')
print(json.dumps({'status':'passed','audit_sha256':sha(A/'integration-code-audit.json'),'bound_files':len(bound),'checks':report['checks']},indent=2))
