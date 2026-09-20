"""Persist verified native publication, scoped review closure and project memory."""
from pathlib import Path
from datetime import datetime, timezone
import json

B = Path(__file__).resolve().parent
MON = B.parents[1]
M = B.parents[3]
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

native = read(B/'native-publication.json')
saved, deployment = native['saved_version'], native['deployment']
archive = read(B/'archive-validation.json')
ledger = read(MON/'ledger.json')
group = ledger['groups']['10.1021_la980800b']
fp = group['fingerprint']
assert deployment['status'] == 'succeeded'
assert deployment['version_id'] == saved['id'] and saved['version_number'] == 18
assert saved['project_id'] == deployment['project_id'] == archive['project_id']
assert saved['source']['commit_sha'] == '6ffb826acf75d309e4a5e4879a46f8cd654fe50c'
assert archive['status'] == 'passed' and archive['dataset_version'] == '0.11.0'
assert fp['generation'] == group['generation'] == 2
assert fp['bundle_sha256'] == 'a9904d5768e81aba7d5b51264a2b4d741a190e6b4118c99fa2f153aad9cf7c7c'
assert set(fp['files'].values()) == {'e581449713ddca5e0cb68d05593df476d0e5150b88bc7c6dcbdb269ac70881fb'}
write(B/'final-source-fingerprint.json', {'group_id':'10.1021_la980800b', **fp})
p = {
    'status':'published', 'source_commit':saved['source']['commit_sha'],
    'site_project_id':saved['project_id'], 'public_live_version':18,
    'dataset_version':'0.11.0', 'source_pushed':True,
    'archive':'recipe-atlas/.sites-runtime/site-v18.tar.gz',
    'archive_sha256':archive['sha256'], 'archive_storage':saved['archive_storage'],
    'version_id':saved['id'], 'deployment_id':deployment['id'],
    'deployment_status':deployment['status'], 'public_url':deployment['url'],
    'published_at':deployment['updated_at'],
    'review_scope':'supplied_main_only_si_unverified',
    'source_id':'stiger1999', 'doi':'10.1021/la980800b',
    'records':8, 'synthesis_routes':1, 'controls':2, 'supporting_procedures':4,
    'contextual_observations':1, 'measurement_entries':145, 'operations':36,
    'reader_evidence_items':144, 'source_audit_units':202, 'references_and_notes':44,
    'original_assets':15, 'original_figures':9, 'original_tables':1,
    'original_schemes':1, 'original_equations':3, 'dedicated_saed_panel':1,
    'canonical_records_total':241, 'material_hubs_total':22, 'source_groups_total':17,
    'source_documents_unchanged':True, 'source_generation':fp['generation'],
    'source_fingerprint_at':fp['created_at'], 'bundle_sha256':fp['bundle_sha256'],
    'independent_audit':['source-audit.json','canonical-records-audit.json',
        'reader-source-audit.json','molecular-source-audit.json','apparatus-source-audit.json',
        'crop-source-audit.json','reader-assets/canonical-to-reader-audit.json',
        'reader-assets/final-presentation-check.json'],
    'browser_checks':'browser-qa.json', 'build_checks':'build-validation.json',
    'native_publication_evidence':'native-publication.json',
    'material_url':deployment['url']+'/material.html?id=ag-si-25bd7c'
}
for name in p['independent_audit'] + [p['browser_checks'],p['build_checks']]:
    assert (B/name).is_file(), name
write(B/'publication-checkpoint.json', p)
stages = read(B/'milestones.json')
assert all(stages[k]['status']=='complete' for k in ['read','extract','audit','integrate'])
for k in ['read','extract','audit','integrate']:
    stages[k]['note'] = 'Completed for all 9 supplied main pages; matching SI not located or verified.'
stages['publish'] = {
    'status':'complete', 'evidence':[str(B/'publication-checkpoint.json')],
    'note':'Published on the existing public MatterSyn Site as version 18. Nine supplied main pages fully reviewed; matching SI not located or verified.'
}
write(B/'milestones.json', stages)
c = read(B/'checkpoint.json')
c.update(checkpoint_at=datetime.now(timezone.utc).isoformat(), website_published=True,
    public_live_version=18, dataset_version='0.11.0',
    publication_checkpoint=str(B/'publication-checkpoint.json'),
    source_commit=p['source_commit'], public_url=p['public_url'],
    source_fingerprint_at=fp['created_at'],
    current_work_items=[{'label':k.capitalize(),'status':'complete','scope':v['note']} for k,v in stages.items()],
    next_action='Stiger supplied-main review closed. Continue the oldest eligible existing local paper using the existing monitor. Reopen this source if matching new or changed SI arrives. Add reviewed materials to the same MatterSyn Site and periodic-table navigation.')
write(B/'checkpoint.json', c)

entry = f'''## 2026-09-19 — Ag nanocrystals on silicon published in the existing atlas

Published version 18, dataset 0.11.0, commit {p['source_commit']} at {p['published_at']}. Same existing public MatterSyn Site. The user's reminder remains in force: each newly reviewed material joins this atlas, its periodic-table discovery and existing material contributions. Selecting Ag and Si exposes the new Ag/Si hub at {p['material_url']}; Ag and Si component hubs retain their respective contribution links. Native proof: research-assets/incoming-paper-monitor/reviews/la980800b/publication-checkpoint.json.

Stiger, Gorer, Craft and Penner, Investigations of Electrochemical Silver Nanocrystal Growth on Hydrogen-Terminated Silicon(100), Langmuir 1999, 15(3), 790–798, DOI 10.1021/la980800b: all nine supplied main pages read and visually reviewed. Both local main copies are byte-identical, SHA256 e581449713ddca5e0cb68d05593df476d0e5150b88bc7c6dcbdb269ac70881fb. Source generation 2 remained unchanged at final post-publication fingerprint {fp['created_at']}. Matching SI not located or verified; completion applies only to the supplied main. Legacy year corrected to journal year 1999 (online December 1998).

Eight canonical records comprise one electrodeposition route, four characterization procedures, two controls and one contextual observation, with 36 operations and 145 measurement entries. The source reader retains 144 items covering 202 audit units and 44 references/notes. Fifteen original assets include nine figures, one table, one scheme, three numbered equations and a dedicated actual SAED panel (Figure 6b); Figure 6c is the source's indexing schematic. All 36 apparatus states, chemical bindings, source crops, canonical records and reader coverage passed independent audits. Browser QA covered periodic-table discovery, molecular controls, stage-specific scenes, all original images, evidence search and mobile layout. Native deployment succeeded.

Preserved scientific boundaries include wafer versus exposed electrode area; preparation versus cyclic-voltammetry/transient conditions; Ag reference scale versus SCE hardware; deposited silver versus backside silver paint; immersion controls versus electrically connected measurements; AFM height versus tip-convolved lateral size; substrate particles versus TEM/SAED material transferred to a carbon-coated gold grid. Kept the source's mC/µC charge conflicts, nucleation-rate time-unit conflict, figure-caption sample-count discrepancies, caption/body concentration and substrate differences, mean-size discrepancies and equation-definition gaps explicit. No invented Ag CIF, atomic interface, spectrum, pulse train, unreported reaction conditions or retrospective calibration was added. New particle/model/context records retain their actual composition and physical sample scope.

Dataset totals: 241 records = 51 routes + 14 controls + 60 procedures + 16 observations + 100 benchmark rows. Twenty-two hubs = 16 direct synthesis systems + 6 component hubs; 17 canonical source groups = 16 literature groups + one benchmark. Seven formal main-only reviews cover 56 pages; five matched-main/SI reviews separately cover 74 pages. Training exports contain 51 precursor-selection, 67 partial-protocol, six size-conditioned, zero exact-structure, zero success and 95 optical-outcome entries; these are task entries, not independent experiments. This paper adds one precursor-selection and one partial-protocol entry, with no new size, exact-structure, success or optical labels.

The 10:58:23Z scan contained 13,146 document copies (5,773 incoming + 7,373 legacy), 8,889 groups and 8,882 provisional canonical review units. These are indexing/worklist counts; verified unique-paper, material and recipe totals for the entire corpus remain unknown. Close all five evidence-backed milestones for this supplied main, then continue oldest eligible local arrival through the existing five-minute heartbeat. No downloads or separate websites; future chatbot, DFT and theory-comparison work remains deferred. Electrochemical-reference, physical-sample and original-SAED distinctions are saved in the workflow reference.

'''
memory = M/'MEMORY.md'
old = memory.read_text(encoding='utf-8')
if not old.startswith(entry.splitlines()[0]):
    memory.write_text(entry+old, encoding='utf-8')
print('Saved version 18 native proof, scoped closure and project memory.')
