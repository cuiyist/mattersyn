from pathlib import Path
from datetime import datetime, timezone
import json, hashlib

B = Path(__file__).resolve().parent
MON = B.parent.parent
M = MON.parent.parent
def read(p):
    return json.loads(p.read_text(encoding='utf-8'))
def write(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
native = read(B / 'native-publication.json')
saved, deployed = native['saved_version'], native['deployment']
assert deployed['status'] == 'succeeded' and deployed['url']
assert saved['id'] == deployed['version_id']
assert saved['source']['commit_sha'] == '6659eff7d22a2f13f8b2d51e91eafe61aaf33448'
ledger = read(MON / 'ledger.json')
assert ledger['current_paper']['group_id'] == '10.1021_jp011815c'
group = ledger['groups']['10.1021_jp011815c']
fp = group['fingerprint']
assert fp['generation'] == group['generation'] == 2
assert fp['bundle_sha256'] == '667d71bcdc3dc983b462d209e8e6375a07883e48f4e699fcd6a1960b64618767'
assert set(fp['files'].values()) == {'2e6310ab5f5c6102ffa46e91dc3ccc2a180e6a6d17fd6a82ef448867edd79967'}
write(B / 'final-source-fingerprint.json', {'group_id': '10.1021_jp011815c', **fp})
archive = M / 'recipe-atlas/.sites-runtime/site-v20.tar.gz'
pub = dict(status='published', source_commit=saved['source']['commit_sha'], site_project_id=saved['project_id'],
    public_live_version=saved['version_number'], dataset_version='0.13.0', source_pushed=True,
    archive=str(archive.relative_to(M)), archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
    archive_storage=saved['archive_storage'], version_id=saved['id'], deployment_id=deployed['id'],
    deployment_status=deployed['status'], public_url=deployed['url'], published_at=deployed['updated_at'],
    review_scope='supplied_main_only_si_unverified', source_id='shah2001', doi='10.1021/jp011815c',
    records=19, synthesis_routes=11, controls=0, supporting_procedures=4, contextual_observations=4,
    measurement_entries=111, operations=74, reader_evidence_items=138, source_audit_units=214,
    typed_facts=253, original_assets=21, original_figures=11, original_tables=1, original_equations=3,
    canonical_records_total=272, material_hubs_total=24, source_groups_total=19,
    source_documents_unchanged=True, source_generation=2, source_fingerprint_at=fp['created_at'],
    bundle_sha256=fp['bundle_sha256'], native_publication_evidence='native-publication.json',
    browser_checks='browser-qa.json', build_checks='final-validation.json',
    independent_audit=['source-audit.json','canonical-records-audit.json','reader-source-audit.json',
        'molecular-source-audit.json','visual-source-audit.json','ir-reference-audit.json',
        'crop-source-audit.json','reader-assets/canonical-to-reader-audit.json',
        'reader-assets/integrated-presentation-audit.json'],
    material_urls={k: deployed['url'] + '/material.html?id=' + v for k,v in
        {'Pt':'pt-b602b7','Ag':'ag-468415','Ir':'ir-460eda'}.items()})
write(B / 'publication-checkpoint.json', pub)
milestones = read(B / 'milestones.json')
milestones['publish'] = {'status':'complete','evidence':[str(B/'publication-checkpoint.json'), str(B/'native-publication.json'),str(B/'final-source-fingerprint.json')],
    'note':'Native deployment succeeded on the same existing public MatterSyn Site. Current source generation unchanged after publication; supplied main scope only, matching SI unverified.'}
assert all(v['status'] == 'complete' and v['evidence'] for v in milestones.values())
write(B / 'milestones.json', milestones)
c = read(B / 'checkpoint.json')
c.update(website_published=True, checkpoint_at=datetime.now(timezone.utc).isoformat(),
    public_live_version=saved['version_number'], dataset_version='0.13.0', publication_evidence=str(B/'publication-checkpoint.json'),
    current_work_items=[{'label':k.capitalize(),'status':v['status'],'scope':v['note']} for k,v in milestones.items()],
    next_action='Current supplied main review complete. Continue the oldest eligible local backlog through the existing heartbeat; retain any later SI as a re-review obligation.')
write(B / 'checkpoint.json', c)
print(json.dumps({'publication':'succeeded','version':saved['version_number'],'milestones':'all complete','source_generation':2,'source_unchanged':True}))
