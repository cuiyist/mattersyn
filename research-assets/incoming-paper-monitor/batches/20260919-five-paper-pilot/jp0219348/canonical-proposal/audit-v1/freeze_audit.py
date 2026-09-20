"""Freeze the bounded independent v1 findings; never modifies author inputs."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, collections

A=Path(__file__).resolve().parent; V=A.parent/'v1'; H=V.parents[1]
def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
t=read(A/'transport-checks.json'); package=read(V/'proposal-package-manifest.json')
reader=read(V/'public-review-proposal/heo2003.json')
items={i['id']:i for s in reader['reader_sections'] for i in s['items']}
assert t['counts']=={'checks':8665,'failed':43}
failuretypes=collections.Counter(f['check'] for f in t['findings'])
assert failuretypes=={'No duplicate sample link':42,'Reader SI audit path resolves relative to its JSON file':1}
assert t['schema_runtime_issue'] is None
for rel,h in package['files'].items(): assert sha(V/rel)==h,rel
for rel,h in package['external_input_hashes'].items(): assert sha(H/rel)==h,rel
duplicate_ids=[f['scope'] for f in t['findings'] if f['check']=='No duplicate sample link']
figures=['asset-heo2003-figure-'+str(n) for n in range(1,8)]
assert all(not items[i]['sample_scope']['canonical_sample_links'] and any(l.get('sample_id') for l in items[i]['canonical_links']) for i in figures)
findings=[
 {'id':'HEO-V1-01','severity':'required_bounded_correction','category':'reader_sample_links',
  'summary':'Deduplicate explicit sample links and populate established figure sample scopes.',
  'observed':'42 reader items repeat the same (record_id, sample_id) pair. All seven figure items have empty explicit sample-scope lists although their canonical_links already identify the supported products and contextual comparisons.',
  'affected_item_ids':duplicate_ids,'additional_figure_item_ids':figures,
  'required_change':'Deduplicate by record_id/sample_id while retaining metadata. Populate figure sample_scope.canonical_sample_links only from the existing supported canonical product links. Preserve Figure 1 parent/current, Figure 2 metal/current/parent, Figure 3 current, and Figures 4–7 distinct topology/average-model scopes; invent no new joins.',
  'scientific_value_change_required':False},
 {'id':'HEO-V1-02','severity':'required_bounded_correction','category':'dependency_path',
  'summary':'The reader SI-audit relative path points outside the v1 source-payload directory.',
  'json_pointer':'/si_aggregate_evidence/audit_path',
  'observed':reader['si_aggregate_evidence']['audit_path'],
  'resolved_missing_path':str((V/'public-review-proposal'/reader['si_aggregate_evidence']['audit_path']).resolve()),
  'required_change':'Use a relative path that resolves from the reader JSON directory to v2/source-payloads/si-complete-candidate/independent-audit.json, and retain the independently passed audit hash.',
  'scientific_value_change_required':False},
 {'id':'HEO-V1-03','severity':'required_bounded_correction','category':'historical_status_presentation',
  'summary':'An inherited extraction-era SI gap is displayed as a current pending transcription.',
  'affected_item_ids':['inventory-remaining_gaps-0'],
  'observed':'The historical source-inventory gap says typed reflection export remains pending, while this package contains the passed 1,209-row aggregate.',
  'required_change':'Keep the frozen source payload unchanged. Label this display as a historical inventory checkpoint and explain the current 1,209-row aggregate, 7,252 resolved numeric cells and two unresolved signs. Preserve the two nulls and remaining source ambiguity. Apply the same historical/current distinction to other inherited workflow-status statements where appropriate.',
  'scientific_value_change_required':False},
 {'id':'HEO-V1-04','severity':'required_bounded_correction','category':'source_locator',
  'summary':'The explicit argon identity needs its actual page-5 evidence locator.',
  'record_id':'heo-2003-xps-acquisition',
  'json_pointers':['/materials/1/evidence','/operations/1/environment/evidence'],
  'observed':'Main PDF p.2/printed1121 reports ion-gun voltage and sputter rate but does not name argon. Main PDF p.5/printed1124 explicitly says sputtering with argon. The source-inventory gas object already cites p.5.',
  'required_change':'Use/add Main PDF p.5 (printed p.1124), XPS Analyses for the gas-identity claim. Keep p.2 for 3 kV, 0.6 Å/s and other acquisition settings. Do not change the gas, numerical settings, analytical role or sample identity.',
  'scientific_value_change_required':False},
 {'id':'HEO-V1-05','severity':'required_bounded_correction','category':'reader_prose',
  'summary':'Some generated reader prose retains compressed extraction notation.',
  'example_item_ids':['fact-unit-cell','fact-xrd-monitor','fact-epxma-tl','fact-exchange-ph','fact-outlook'],
  'additional_json_pointer':'/evidence_conflicts',
  'examples':['Reported24.942(4)angstrom','every3h','at10.26/12.21keV','Ph ...6.4 .','initial/redehydration623K48h1e-6Torr'],
  'required_change':'Polish display sentences, spacing, units and pH capitalization without altering raw/source/canonical values. Reuse already polished conflict descriptions. For the speculative outlook preserve the source wording tagged electronically or magnetically, with no demonstration of individual addressing or a device.',
  'scientific_value_change_required':False},
]
manual=[
 {'scope':'Canonical science and specimen boundaries','actual_work':'Read all ten record scopes, materials, stock, 14 operation descriptions/conditions and product/context organization; assessed the canonical quantities with source-fact/table mappings. Checked one physical route versus analytical/reference/model contexts and the three contradictory recipe conditions.'},
 {'scope':'Reader prose','actual_work':'Read the complete non-bibliographic prose of all 301 non-reference items across all six reader sections. The 71 bibliography strings were checked for exact transport from the passed source inventory, not newly researched or reread as 71 source papers.'},
 {'scope':'Targeted native source views','actual_work':'Actually viewed the experimental-procedure crop, main Table 1 crop, main PDF pages 2 and 5 from exact original page images, and all seven original Figure 1–7 crops. Page 5 includes Tables 2–3 and the explicit argon evidence. This is targeted proposal verification, not a repeat full-main-source extraction or new all-cell main-table audit.'},
 {'scope':'Quantitative main tables','actual_work':'Independently enumerated and checked exact transport of all 209 row quantities (198 populated numeric values and 11 blanks), raw precision/footnote tokens, entire row payloads and scoped canonical measurements. Fifteen auxiliary quantities are retained in the exact source payload: 14 duplicated conflict-condition quantities and one oxygen-radius derivation reference.'},
 {'scope':'SI reflections','actual_work':'Reused the distinct passed aggregate independent audit; checked its exact hash, exact aggregate JSON/TSV copies, all 1,209 row/cell mappings, 7,254 numeric positions, 7,252 resolved cells, two sign nulls, 137 negative Fobs2 values and one zero. No new SI-cell visual rereading is claimed.'},
 {'scope':'Original assets','actual_work':'Verified byte hashes and reader/projected reachability for all 39 originals; actual visual review in this audit is the targeted subset listed above, not all 39 images.'},
]
positive=[
 'All ten records pass current Site schema and semantic validation; 14 material slots, one stock, 14 operations, 473 measurements and 188 product/context identifiers are present. The 188 identifiers are not 188 physical experiments.',
 'All 114 source facts, 433 inventory units, 209 table-row quantities, eight chemical equations and 71 bibliography entries retain exact mapped source payloads. All 473 measurements reach the 535 typed reader facts; all 372 reader items and their canonical pointers resolve.',
 'The single nine-operation synthesis route retains three prose/Table 1 condition conflicts. Unresolved primary temperatures/times are not silently selected; reported alternative evidence is not represented as independently approved recipe variants.',
 'The 0.1 M pH 6.4 feed, unspecified interpretation of the 10 mL exchange volume, separate deionized-water wash, redox temperature gradient, H2S treatment and final evacuation/sealing remain source scoped. Cited metal vapor pressures are not promoted to reactor pressures.',
 'Nominal In66Si100Al92 and the average Si96Al96 structural model remain distinguished. Site counts, occupancy fractions, multiplicity, framework conventions and average/disordered models are not converted into a measured ordered atomic structure.',
 'Current In66-X, prior In87-X and other literature compositions, indium-metal references, framework sketches and average cluster models remain separate sample/context identities. All batch_id values remain null; no new cross-technique specimen join is claimed.',
 'The 83-versus-92 charge discrepancy, oxygen-loss/proton hypotheses, possible cluster charge and eight author mechanism equations remain interpretations rather than executed recipes or added measured atoms.',
 'Both unresolved SI signed values remain null: si-p11-R-r035-Fobs2 and si-p12-L-r012-Fcal2. SI reflections are not recast as atomic coordinates.',
 'No requested training task, exact recipe–structure pair, measured source CIF, DFT/ordered model or browser/integration approval is assigned. The separately audited average-geometry candidate is not imported by these records.',
 'Fresh hashes of both original local PDFs match the retained main/SI identities, and all 85 frozen proposal file hashes plus external frozen input hashes remain unchanged.'
]
bound=dict(t['bound_files'])
for p in [A/'transport-checks.json',A/'check_transport.py',A/'inspect_package.py',A/'checker-draft-1.json',Path(__file__)]:bound[str(p.resolve())]=sha(p)
for p in A.glob('reader-*.txt'):bound[str(p.resolve())]=sha(p)
bound[str((A/'record-operations.txt').resolve())]=sha(A/'record-operations.txt')
report={
 'schema':'mattersyn.heo_canonical_reader_independent_audit/1',
 'audited_at':datetime.now(timezone.utc).isoformat(),
 'author':'/root/peng1998_reader_assets','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta',
 'status':'requires_bounded_correction','scope':'Frozen canonical/reader proposal v1 only; source science, transport and display mappings. Not a molecular/model self-audit, publication approval or repeated SI-cell audit.',
 'proposal_manifest':str(V/'proposal-package-manifest.json'),'proposal_manifest_sha256':sha(V/'proposal-package-manifest.json'),
 'counts':package['counts'],
 'mechanical_checks':{'total':8665,'passed':8622,'failed_instances':43,'failure_instances':'42 duplicate sample-link instances plus one invalid SI-audit path; consolidated with manual findings below.','current_schema_records_passed':10},
 'manual_review_scope':manual,'positive_findings':positive,'required_findings':findings,
 'correction_protocol':'Preserve all frozen v1 bytes. Author prepares a separate v2, limits changes to the described reader display/link and evidence-locator corrections, and supplies a scientific field/quantity/condition/specimen/raw-source invariance proof. Re-audit the bounded delta before passage.',
 'remaining_gates':['These five findings remain open in frozen v1.','Any v2 must be separately hash-bound and rechecked.','Molecule, protocol visual, average-geometry candidate and final binding/browser/promotion approvals remain separate.','Two unresolved SI signs and original scientific conflicts remain source limitations.'],
 'checker_development_note':'The preserved checker-draft-1.json contains superseded checker assumptions, not additional author defects. Corrected assumptions cover sample-link schema, ESD parsing with raw tokens, source-status qualifiers, unit distinctions, metadata projections, footnote raw_cell handling and row-versus-auxiliary table quantity counts. Only the current transport-checks.json supplies final mechanical results.',
 'mutations':'Only audit-v1 output files written; author proposal, sources, Site, shared ledger and publication state unchanged.',
 'bound_files':bound
}
(A/'independent-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=[
 '# Heo canonical/reader v1 independent audit','',
 '**Result: requires five bounded corrections.** No scientific quantity, synthesis condition, specimen identity or SI-cell correction is requested. Preserve v1 and recheck a separate v2.','',
 'Author: `/root/peng1998_reader_assets`. Independent auditor: `/root/backlog_eta`.','',
 f"Frozen proposal manifest SHA256: `{report['proposal_manifest_sha256']}`.",'',
 'The audit covered 10 records, 14 operations, 14 material slots, one stock, 473 measurements, 188 product/context identifiers, 372 reader items and 535 typed reader facts. The independent checker ran 8,665 checks: 8,622 passed; 43 failing instances consolidate to 42 duplicate sample-link cases and one broken SI-audit path. All 10 schema/semantic validations passed.','',
 '## Required corrections',''
]
for f in findings:lines.extend([f"- **{f['id']}: {f['summary']}** {f['required_change']}",''])
lines+=['## Scientific and transport conclusions','']
for x in positive:lines+=['- '+x,'']
lines+=['## Actual review scope','']
for x in manual:lines+=['- **'+x['scope']+':** '+x['actual_work'],'']
lines+=['## Limits and next gate','',report['correction_protocol'],'',
 'The two unresolved SI signs remain null; the three recipe conflicts and interpretation/model limits remain. No molecule, atomic model, exact-pair, training, browser, integration or publication approval follows from this report. Only private audit files were written.','',
 'The JSON report binds the original sources, frozen package, passed source/aggregate evidence, current validator, independent checker and audit digests by absolute path and SHA256. The preserved initial checker draft contains corrected checker assumptions and is not an extra set of author findings.','']
(A/'independent-audit.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({'status':report['status'],'findings':len(findings),'json':str(A/'independent-audit.json'),'json_sha256':sha(A/'independent-audit.json'),'md_sha256':sha(A/'independent-audit.md'),'proposal_manifest_sha256':report['proposal_manifest_sha256'],'bound_files':len(bound)},ensure_ascii=False))
