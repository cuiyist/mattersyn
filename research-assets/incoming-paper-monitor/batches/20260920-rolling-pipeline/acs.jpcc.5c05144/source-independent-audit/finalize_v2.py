import json,hashlib,datetime,copy
from pathlib import Path
O=Path(__file__).parent;P=O.parent;V=P/'source-extraction-revision-2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(V/'package-freeze.json')=='d34778349e9942a73a1d275536af354e93d52739692e689fe2f12d394db7fddc'
prior=read(O/'independent-audit-v1.json');z=read(V/'package-freeze.json');c=read(O/'bounded-revision-2-checks.json');assert not c['summary']['failed']
assert sum(len(x) for x in c['exact_deltas'].values())==9
bound=dict(prior['bound_files'])
for p,h in z['bound_files'].items():
 expected=h['sha256'] if isinstance(h,dict) else h;assert sha(p)==expected;bound[str(Path(p).resolve())]=expected
for p in [V/'package-freeze.json',O/'independent-audit-v1.json',O/'independent-audit-v1.md',O/'check_revision_2.py',O/'bounded-revision-2-checks.json',Path(__file__)]:bound[str(p.resolve())]=sha(p)
for p,h in bound.items():assert sha(p)==h
report=copy.deepcopy(prior)
report.update(revision=2,status='passed',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_freeze=str(V/'package-freeze.json'),source_freeze_sha256=sha(V/'package-freeze.json'),effective_files=z['effective_files'],prior_audit={'path':str(O/'independent-audit-v1.json'),'sha256':sha(O/'independent-audit-v1.json'),'status':'preserved immutable historical finding report'},bound_files=bound,bound_file_count=len(bound))
report['findings'][0]['status']='resolved_in_revision_2'
report['findings'][0]['resolution']='Exact SI p5/S5 FigureS2 caption evidence added to the range claim, displayed-range quantity and operation mirrors; inventory source evidence/payload and p5 coverage propagated. Original p4/p6 evidence remains. All scientific leaves after removing evidence are identical; all76 original bound files and both source originals remain byte-identical.'
report['open_findings']=[]
report['targeted_revision_scope']={'actual_scope':'Reviewed all9 exact JSON additions and the effective file map against the previously viewed native FigureS2 caption. Reverified all unchanged source/table/crop/scientific hashes; did not repeat full unchanged-paper reading.','exact_deltas':c['exact_deltas'],'independent_checks':c['summary'],'unchanged_main_pages':9,'unchanged_si_pages':11,'unchanged_selected_crops':17,'unchanged_original_author_files':76,'scientific_invariance':'Every source-facts leaf outside evidence arrays is unchanged. The121 body table cells, six embedded formula/size quantities,100 fact quantities and all sample assignments retain original values.'}
report['mechanical_summary']={'original_executed':2272,'original_supporting_passed':2270,'original_locator_failures_now_resolved':2,'bounded_revision_executed':315,'bounded_revision_passed':315,'total_executed':2587,'passed_checks':2585,'unresolved_failures':0,'note':'Two historical v1 locator failures remain in immutable history and are explicitly resolved, rather than retrospectively relabeled passed.'}
report['manual_scopes'].append('Bounded revision2 review: all9 added evidence/coverage objects independently compared, proper exact caption/page identity confirmed, and original source/science/assets rehashed. No new source/science scope was introduced.')
data=json.dumps(report,ensure_ascii=False,indent=2)+'\n';dest=O/'independent-audit-v2.json';assert not dest.exists();dest.write_text(data,encoding='utf-8');(O/'independent-audit.json').write_text(data,encoding='utf-8')
md='''# Sasongko2025 independent source audit — revision2

**Passed. No open extraction finding.** Author: `/root/peng1998_reader_assets`; independent reviewer: `/root/backlog_eta`.

The correction adds exactly nine evidence/coverage objects, including the actual SI page5 FigureS2 caption for the displayed80–190K Raman range. Original p4 instrument and p6 prose evidence remain. Every scientific source leaf outside evidence is unchanged; all76 base files, both original PDFs, all121 table body cells and17 selected crops remain byte-identical. The315 bounded revision checks pass, following2,270 supporting checks in the full v1 review.

The inherited independent scope is nine main plus eleven SI pages actually read/viewed;48 facts/100 quantities,13 materials, four stocks,21 operations,33 contexts, six table groups and89 references compared. All17 selected crops were actually viewed and reproduced pixel-for-pixel. This turn rechecked the exact locator delta and unchanged hashes; it did not repeat unchanged full-paper reading.

Source discrepancies and missingness remain explicit. No measured QD atomic coordinates, exact sample joins, canonical/reader/visual approval or training admission is implied. Full-page images and complete source text remain local. V1 reading, audit and diagnostics are preserved. The JSON binds the exact effective overlay and original inputs.
'''
for name in ['independent-audit-v2.md','independent-audit.md']:(O/name).write_text(md,encoding='utf-8')
print(json.dumps({'audit':str(dest),'sha256':sha(dest),'bound_files':len(bound),'effective_freeze':sha(V/'package-freeze.json'),'effective_facts':z['effective_files']['source-facts.json']['sha256']},indent=2))
