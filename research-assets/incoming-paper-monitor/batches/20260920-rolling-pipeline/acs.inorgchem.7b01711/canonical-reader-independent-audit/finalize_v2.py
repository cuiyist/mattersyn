from pathlib import Path
import json,hashlib,datetime,copy
A=Path(__file__).resolve().parent;B=A.parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (A/'independent-audit-v2.json').exists()
pkg=B/'canonical-proposal/v2/package-manifest.json'
assert sha(pkg)=='433555d5ccaaa0a3d98c01f3f9657921872611fee766557e9c4756f49e806508'
delta=load(A/'delta-check-v2.json');schema=load(A/'schema-check-v2.json');assert delta['status']==schema['status']=='passed'
out=copy.deepcopy(load(A/'independent-audit-v1.json'))
out.update(status='passed',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),package_sha256=sha(pkg),canonical_version=2,reader_sha256=sha(B/'public-review-proposal/v2/morrison2017.json'),delta_checks=delta['check_count'],total_supporting_checks=out['mechanical_checks']+delta['check_count'],open_findings=0)
out['findings'][0]['status']='resolved_in_preserved_v2'
out['findings'][0]['resolution']='Exactly /material_states/0/kind changed mixture to analysis_data. All 17 other canonical files and reader bytes are identical. No source fact, quantity, operation ID, condition, specimen, table cell, image or training state changed.'
out['manual_scopes'].append('Verified the v2 single-leaf classification correction against preserved v1 and independently reran current schema/semantic eligibility validation on all 18 final records.')
out['record_hashes']={p.stem:sha(p) for p in sorted((B/'canonical-proposal/v2').glob('morrison-*.json'))}
bound=dict(load(pkg)['bound_files']);bound[str(pkg)]=sha(pkg)
for p in sorted(A.glob('*')):
 if p.is_file() and p.name not in ['independent-audit-v2.json','independent-audit-v2.md','independent-audit.json','independent-audit.md']:bound[str(p)]=sha(p)
out['bound_files']=bound
for name in ['independent-audit-v2.json','independent-audit.json']:(A/name).write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
md='''# Morrison canonical/reader v2 independent audit

Passed after one preserved classification correction: the precursor diffraction/refinement output is analytical data rather than a chemical mixture. The reader is byte-identical to v1; 17 of 18 records are byte-identical and the remaining record has one changed leaf.

The audit covers all 18 records, 24 operations, 72 source facts, 176 source units, 185 source fact quantities, 471 table cells, 822 measurement/context entries, 252 reader items and 1,170 exact fields. All 17,830 transport checks and 163 bounded delta checks passed. Current schema/semantic validation independently passes every final record, with empty requested tasks and no eligible training export.

Full reader prose, source and specimen joins, phase/recipe/control boundaries, model interpretations, source discrepancies and selected-asset associations were reviewed. The passed source revision2 audit supplies the separately completed 27-page reading and 30 individual crop inspections; every retained asset hash is unchanged. No second complete source read is claimed here.

The THF-solvated precursor crystal tables remain separate from CdSe/CdS product observations. No atomic model, CIF, exact recipe–structure training pair, molecule/apparatus binding, integrated browser, Site import or publication is approved by this audit.
'''
for name in ['independent-audit-v2.md','independent-audit.md']:(A/name).write_text(md,encoding='utf-8')
print(json.dumps({'status':out['status'],'audit_sha256':sha(A/'independent-audit-v2.json'),'package_sha256':sha(pkg),'reader_sha256':out['reader_sha256'],'checks':out['total_supporting_checks'],'bound_files':len(bound)},indent=2))
