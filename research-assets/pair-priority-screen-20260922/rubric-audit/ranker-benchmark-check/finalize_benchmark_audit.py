"""Bounded independent final-run transport plus source-benchmark checks.

Reads a completed run; writes only this audit directory. Does not run the
corpus screen, modify the frozen rubric, or assign scientific approval.
"""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;Q=O.parent;R=Q.parent/'ranker-proposal'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb')as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def vs(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def pointer(o,p):
    for s in p.strip('/').split('/'):
        s=s.replace('~1','/').replace('~0','~');o=o[int(s)]if isinstance(o,list)else o[s]
    return o
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args()
run=Path(args.run).resolve();assert run.is_relative_to(R.resolve())
checks=[];bound={}
def check(name,ok):
    checks.append({'id':name,'passed':bool(ok)})
    if not ok:raise AssertionError(name)
def bind(p,expected=None):
    p=Path(p);h=sha(p);bound[str(p.resolve())]=h
    if expected:check('hash:'+str(p),h==expected)
    return h
summary=read(run/'summary.json');bind(run/'summary.json')
author=read(R/'author-freeze.json');bind(R/'author-freeze.json','6bbed99f39209a0958d243f6aa8cfcf712fe0ebefc7981f47922b84e53ab84d0')
check('author_run_identity',author['run']==run.name and author['script_sha256']==summary['script_sha256'])
check('author_summary_binding',next(x['sha256']for x in author['files']if x['path']==run.name+'/summary.json')==sha(run/'summary.json'))
bind(R/'README.md',next(x['sha256']for x in author['files']if x['path']=='README.md'))
check('run_completed',read(run/'progress.json')['status']=='completed_dry_run_not_activated')
bind(R/'rank_pairs.py',summary['script_sha256'])
check('corrected_code_bound',summary['script_sha256']=='4815804844292ab1378a0be9dd5b264014fd63c4a34dc4c9ca2e12473f2c85a2')
manifest=read(Q/'package-manifest.json');bind(Q/'package-manifest.json','4dfb2fa4ad60c68ffd8c3c463a512644dd0881c9a3381b8d4678c7ec174abefd')
for section in ['bound_files','bound_input_files']:
    for p,h in manifest[section].items():bind(p,h)
bench=read(Q/'verified-benchmark-rows.json');assess=read(O/'case-assessments.json')
check('twelve_distinct_benchmarks',len(bench['rows'])==len({x['id']for x in bench['rows']})==12)
check('same_assessment_ids',{x['id']for x in bench['rows']}=={x['id']for x in assess['cases']})
for b in bench['rows']:
    for e in b['evidence']:check(b['id']+e['json_pointer'],vs(pointer(read(e['path']),e['json_pointer']))==e['value_sha256'])
probe=read(O/'corrected-cache-probe-v2.json');agg=read(O/'corrected-aggregate-probe-v2.json')
check('probe_code_matches_final',probe['ranker_sha256']==agg['ranker_sha256']==summary['script_sha256'])
byhash={x['source_sha256']:x for x in probe['rows']};byname={x['file']:x for x in probe['rows']}
groupids={x['group_id']for x in agg['results']}
selected=[]
with (run/'ranked-scopes.jsonl').open(encoding='utf-8')as f:
    for line in f:
        x=json.loads(line)
        if x['group_id']in groupids:selected.append(x)
check('seven_actual_run_nominations',len(selected)==len(groupids)==7)
for x in selected:
    old=next(r for r in agg['results']if r['group_id']==x['group_id'])
    check('aggregate_transport:'+x['group_id'],{k:v for k,v in x.items()if k!='candidate_inspection_rank'}==old)
    check('no_approval:'+x['group_id'],not x['verified_pair']and not x['task_ready']and not x['automatic_exclusion'])
    check('no_asserted_recipe_join:'+x['group_id'],x['linkage_status']=='unknown_no_qualifying_local_link_cue')
finalscans={}
with (run/'private/source-cues.jsonl').open(encoding='utf-8')as f:
    for line in f:
        x=json.loads(line)
        if x['source_sha256']in byhash:finalscans[x['source_sha256']]=x
check('fifteen_source_caches_present',len(finalscans)==len(byhash)==15)
cue_lookup={c['cue_id']:c for s in finalscans.values()for c in s['cues']}
for x in selected:
    for e in x['candidate_evidence']:
        c=cue_lookup[e['cue_id']]
        if c['atomic_evidence_candidate']:
            check('atomic_origin_hold:'+c['cue_id'],not c['origin_warnings']or (c['origin_warnings']==['fixed_or_constrained_positions']and c.get('explicit_refined_positions_statement')and x['priority_band']=='B_atomic_link_unknown_candidate'))
    if '8b04556'in x['group_id']:
        check('Chen_mixed_not_measured_admission',x['mixed_refined_fixed_atomic_table_windows']==2 and x['measured_refined_coordinate_candidate_windows']==0 and x['priority_band']=='B_atomic_link_unknown_candidate')
    if 'ja103805s'in x['group_id']:
        check('Evans_actual_CIF_file_retained',any(z['source_sha256']==byname['10.1021_ja103805s_si_2.cif']['source_sha256']for z in x['coordinate_file_availability']))
spec=importlib.util.spec_from_file_location('ranker_audited',R/'rank_pairs.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
documents=[json.loads(x)for x in m.INPUTS['documents'][0].open(encoding='utf-8')]
for h,old in byhash.items():
    d=next(x for x in documents if x['sha256']==h);b,t=m.cache_binding(d)
    check('cache_binding:'+h,b==old['binding'])
    check('final_cues_exact_replay:'+h,finalscans[h]=={'source_sha256':h,'text_sha256':b['text_sha256'],**m.scan_text(t,h)})
    bind(b['text_path'],b['text_sha256'])
case_results=[]
for a in assess['cases']:
    b=next(x for x in bench['rows']if x['id']==a['id']);p=byname[a['source_name']];scan=finalscans[p['source_sha256']]
    tables=[c for c in scan['cues']if c['numeric_atom_table_candidate']]
    chosen=[]
    for page in a.get('required_table_pages',[]):
        matches=[c for c in tables if c['locator']['page']==page and (not a.get('required_header_page')or c.get('table_header_locator',{}).get('page')==a['required_header_page'])]
        check(a['id']+':tablepage:'+str(page),bool(matches));chosen+=matches
    if a.get('required_detection'):
        matches=[c for c in tables if c.get('table_detection')==a['required_detection']]
        check(a['id']+':detection',bool(matches));chosen+=matches
    if a['id'].startswith('chen-'):
        check(a['id']+':mixed_warning',all('fixed_or_constrained_positions'in c['origin_warnings']and c.get('component_assignment')=='unresolved_do_not_transfer_refined_or_fixed_origin_between_components'for c in chosen))
    if a.get('require_no_atomic_tables_for_paper'):
        suffix=b['doi'].split('/')[-1]
        check(a['id']+':no_atom_table',all(not c['atomic_evidence_candidate']for p2 in probe['rows']if suffix in p2['file']for c in finalscans[p2['source_sha256']]['cues']))
    group=next(x for x in selected if b['doi'].split('/')[-1]in x['group_id'])
    case_results.append({**a,'expected_case_classification':b['expected'],'actual_paper_nomination':group['priority_band'],'actual_group_id':group['group_id'],'actual_inspection_rank':group['candidate_inspection_rank'],'candidate_evidence':[{'cue_id':c['cue_id'],'locator':c['locator'],'table_header_locator':c.get('table_header_locator'),'origin_warnings':c['origin_warnings']}for c in chosen],'scientific_case_classification_resolved_by_ranker':False,'verified_pair':False,'task_ready':False})
heo=byname['10.1021_jp0219348_si_1.pdf'];check('reflection_SI_not_atomic',not any(c['atomic_evidence_candidate']for c in finalscans[heo['source_sha256']]['cues']))
for n in ['ranked-scopes.jsonl','private/source-cues.jsonl','cache-binding-manifest.jsonl','progress.json']:
    bind(run/n,summary['output_bindings'][n]['sha256'])
for n in ['initial-benchmark-findings.json','initial-benchmark-findings.md','provisional-cache-probe.json','probe_current.py','corrected-cache-probe-v2.json','probe_revision2.py','corrected-aggregate-probe-v2.json','probe_aggregate_v2.py','case-assessments.json','finalize_benchmark_audit.py']:bind(O/n)
save('final-selected-nominations.json',{'scope':'Seven known-source paper-level nominations only; not the full corpus report','run':str(run),'rows':selected});bind(O/'final-selected-nominations.json')
report={'status':'passed_for_bounded_candidate_nomination_with_role_resolution_limits','auditor':'/root/backlog_eta','ranker_author':'/root/morphology_evidence','checked_at':datetime.now(timezone.utc).isoformat(),'scope':'Independent known-source sensitivity/role-boundary audit. All-corpus coverage, invalid-source admission, and generic code tests are a separate /root/all_page_coverage audit. No new full-paper audit, shared-state edit, publication or task admission.','run_directory':str(run),'ranker_sha256':summary['script_sha256'],'summary_sha256':sha(run/'summary.json'),'rubric_manifest_sha256':sha(Q/'package-manifest.json'),'open_required_findings':[],'closed_findings':[{'id':'RB'+str(i),'status':'resolved_in_corrected_table_detection'}for i in range(1,6)],'counts':{'benchmark_cases_evaluated':12,'papers':7,'unique_cached_sources':15,'coordinate_bearing_benchmark_papers_detected':5,'distinct_table_or_CIF_scopes_detected':7,'checks_passed':len(checks),'automatically_verified_pairs':0,'task_admissions':0},'actual_manual_scope':['Read all twelve frozen benchmark classifications, exact evidence locators and retained constraints.','Inspected actual corrected source text cue/table spans for Chen SI8/9, Heo main5, Morrison SI3, Evans atom-site CIF loop, and Lian SI18–22; compared against prior source-audited benchmark evidence.','Checked seven final nominations and component/origin warnings. Did not repeat unchanged full-page source reading or claim automatic twelve-case semantic classification.'],'case_results':case_results,'remaining_limits':assess['remaining_limits'],'cache_scope':'The screen uses previously SHA-bound text caches. Current cache hashes were verified here for fifteen benchmark sources; source corpus bytes were not newly rehashed by this task.','checks':checks,'bound_files':bound}
report['passed']=True
report['ranker_script_sha256']=summary['script_sha256']
report['author_freeze_sha256']=sha(R/'author-freeze.json')
report['findings']=[]
report['open_findings']=[]
save('independent-benchmark-audit.json',report)
lines=['# Independent ranker benchmark audit','','Passed for candidate nomination with explicit role-resolution limits. Five source-table sensitivity findings are corrected. All twelve benchmark cases were evaluated across seven papers and fifteen cached sources.','','The final run detects Chen S1/S2.5 tables, Heo Table2, Morrison precursor TableS1, Evans atom-site CIF and both Lian bulk tables. Chen stays a mixed fixed/refined B candidate; Heo SI reflections, Sasongko cited cells and Nagasaki XRD do not become atomic coordinates.','','| Paper | Final nomination | Remaining source-specific review |','|---|---|---|']
for x in selected:lines.append('| '+x['group_id']+' | '+x['priority_band'].split('_')[0]+' | Target component and recipe link remain unverified |')
lines+=['','The ranker has paper-level output, not sample/phase-level classification. Evans/Morrison still need molecular or precursor separation; Lian bulk evidence must not transfer to NCs; Chen minority fixed sites must not inherit host refinement. The frozen benchmark rows remain authoritative for these distinctions. No pair or task is approved.','','This deliberately selected regression set is not an estimate of corpus accuracy or pair yield. Duplicate cue windows are not distinct structures. All-corpus integrity and source validity are audited separately.','',f'Checks: {len(checks)}. Final run: `{run.name}`. Script SHA256: `{summary["script_sha256"]}`.',f'JSON SHA256: `{sha(O/"independent-benchmark-audit.json")}`.']
(O/'independent-benchmark-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(checks),'report':str(O/'independent-benchmark-audit.json'),'sha256':sha(O/'independent-benchmark-audit.json')},indent=2))
