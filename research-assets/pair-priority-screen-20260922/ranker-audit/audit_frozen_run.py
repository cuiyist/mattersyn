"""Independent structural/integrity audit, not a corpus scientific review."""
from pathlib import Path
from collections import Counter
import argparse,json,hashlib,datetime
W=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf8'))
def rows(p):return [json.loads(s) for s in p.open(encoding='utf8')]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args()
D=Path(a.run).resolve();S=read(D/'summary.json');checks=[]
def check(label,condition,detail=None):checks.append({'check':label,'pass':bool(condition),**({'detail':detail} if detail is not None else {})})
inputs={}
for k,b in S['input_bindings'].items():
    p=Path(b['path']);check('input binding '+k,sha(p)==b['sha256'])
    if k in ['partition','partition_ledger','inventory','validity_overlay']:inputs[k]=read(p)
for n,b in S['output_bindings'].items():check('output binding '+n,sha(D/n)==b['sha256'])
check('final code hash matches actual entrypoint',sha(D.parent/'rank_pairs.py')==S['script_sha256'])
partition=inputs['partition'];wanted=set(partition['included_canonical_group_ids']);rank=rows(D/'ranked-scopes.jsonl');files=rows(D/'file-dispositions.jsonl');cache=rows(D/'cache-binding-manifest.jsonl')
check('all9532fixedscopes exactly once',len(rank)==len({r['group_id'] for r in rank})==len(wanted)==9532 and {r['group_id'] for r in rank}==wanted)
check('no duplicate file dispositions',len(files)==len({f['file_key'] for f in files}))
ledger=inputs['partition_ledger'];paths={str(Path(e['absolute_path']).resolve()).lower() for e in inputs['inventory']['entries'] if e.get('kind')=='regular_file' and e.get('top_level') and e.get('monitor_eligible')}
def canonical(g):
    seen=set()
    while ledger['groups'].get(g,{}).get('alias_of'):
        if g in seen:raise AssertionError('cyclic input aliases')
        seen.add(g);g=ledger['groups'][g]['alias_of']
    return g
expected={};docpath=Path(S['input_bindings']['documents']['path'])
for d in map(json.loads,docpath.open(encoding='utf8')):
    g=canonical(d['group_id'])
    if g in wanted and str(Path(d['source_path']).resolve()).lower() in paths:expected[d['file_key']]={'group_id':g,'source_sha256':d['sha256'],'original_group_id':d['group_id']}
filemap={f['file_key']:f for f in files}
check('all fixed files including aliases retained',set(filemap)==set(expected),{'expected':len(expected),'actual':len(files),'missing':sorted(set(expected)-set(filemap)),'extra':sorted(set(filemap)-set(expected))})
check('expected13831file dispositions',len(expected)==13831)
for key,d in expected.items():
    f=filemap.get(key,{});check('file hash and canonical scope '+key,f.get('source_sha256')==d['source_sha256'] and f.get('group_id')==d['group_id'])
overlay=inputs['validity_overlay'];hits=[e for e in overlay['files'] if e['file_key'] in expected]
check('all48known overlay files represented',len(hits)==48)
for e in hits:
    f=filemap[e['file_key']];block=e['block_positive_pair_admission_from_this_file']
    check('overlay current hash binding '+e['file_key'],f['source_sha256']==e['source_sha256'])
    check('overlay admission block preserved '+e['file_key'],f['known_positive_admission_block']==block and (not block or not f['eligible_for_candidate_cues']))
check('known32file blocks applied',sum(f['known_positive_admission_block'] for f in files)==32)
blocked_groups={f['group_id'] for f in files if f['known_positive_admission_block']}
rankmap={r['group_id']:r for r in rank}
check('known32group source holds preserved',len(blocked_groups)==32 and all(rankmap[g].get('source_hold') and rankmap[g].get('dispatch_status')=='source_identity_or_role_repair_required' for g in blocked_groups))
check('no fabricated source-validity approval',all(r.get('source_validity')=='known_exceptions_applied_others_unassessed' for r in rank))
check('no verified pair/task/exclusion flags',all(r.get('verified_pair') is False and r.get('task_ready') is False and r.get('automatic_exclusion') is False for r in rank))
check('all main SI pairing remains unverified',all(r.get('main_si_pairing')=='unverified_candidate_group_only' for r in rank))
check('historic statuses preserved by name and value',all(r['review_status_in_partition']==next(g['review_status'] for g in partition['included_groups'] if g['group_id']==r['group_id']) for r in rank))
nested=read(D/'nested-held.json');check('all3unadmitted nested files preserved',nested['files']==partition['nested_cutoff_candidates_held_for_scope_review'] and len(nested['files'])==3 and nested.get('automatic_exclusion') is False)
check('all3nested sources separately screen without admission',len(nested.get('second_stage_screen',[]))==3)
expected_cache_sources={f['source_sha256'] for f in files}|{n['source_sha256'] for n in nested.get('second_stage_screen',[])}
check('cache binding every source represented once',len(cache)==len({c['source_sha256'] for c in cache}) and {c['source_sha256'] for c in cache}==expected_cache_sources)
check('historical/source-byte authentication limits explicit',all(c.get('current_source_bytes_rehashed') is False and c.get('historical_text_hash_available') is False for c in cache))
cachemap={c['source_sha256']:c for c in cache};check('eligible files require eligible cache',all(not f['eligible_for_candidate_cues'] or cachemap[f['source_sha256']]['status']=='historically_bound_cache_candidate' for f in files))
# Selected actual cache bytes, including all inspected source-exception hashes.
sampled=set(e['source_sha256'] for e in hits)|{c['source_sha256'] for c in cache[::max(1,len(cache)//15)]}
replayed=[]
for digest in sorted(sampled):
    c=cachemap[digest]
    if c.get('text_sha256') and c.get('text_path'):
        actual=sha(Path(c['text_path']));check('bounded current text hash replay '+digest,actual==c['text_sha256']);replayed.append(digest)
selectedids={e['cue_id'] for r in rank for e in r.get('candidate_evidence',[])}|{e['cue_id'] for r in rank for e in r.get('procedure_evidence',[])}
selected={};source_count=0
for src in map(json.loads,(D/'private/source-cues.jsonl').open(encoding='utf8')):
    source_count+=1;digest=src['source_sha256'];check('source cue text hash binding '+digest,src.get('text_sha256')==cachemap[digest].get('text_sha256'))
    for c in src['cues']:
        if c['cue_id'] in selectedids:selected[c['cue_id']]=c
check('all selected cue IDs resolve',selectedids<=set(selected))
top=[r for r in rank if r['priority_band'].startswith('A_')]
for r in top:
    for e in r['candidate_evidence']:
        c=selected[e['cue_id']];check('A candidate has numeric measured noncontext cue '+e['cue_id'],c['numeric_atom_table_candidate'] and c['experimental_refinement_cue'] and not c['origin_warnings'])
known=[rankmap[g] for g in ['legacy::10.1021_acsami.8b04556','10.1016_j.joule.2018.08.011','10.1016_j.snb.2019.127343']]
report={'schema':'mattersyn-independent-ranker-run-audit/1','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run_directory':str(D),'summary_sha256':sha(D/'summary.json'),'ranker_script_sha256':S['script_sha256'],'scope':'Output integrity, denominator and exception gates plus bounded current-cache replay. Not all-paper scientific review or ranker precision measurement.','counts':{'checks':len(checks),'failed':sum(not c['pass'] for c in checks),'scope_count':len(rank),'file_count':len(files),'unique_cached_sources':len(cache),'bounded_text_hash_replays':len(replayed),'selected_cues_resolved':len(selected),'A_candidate_scopes':len(top)},'checks':checks,'bounded_current_text_replay_hashes':replayed,'known_source_rows':known,'source_quality_limit':'None of these integrity checks authenticates old extracted text against original PDFs or independently verifies scientific recipe/structure links. Most original pages were not manually viewed in this audit.'}
out=W/('run-integrity-'+S['script_sha256'][:12]+'.json');out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'report':str(out),'counts':report['counts'],'failed_checks':[c for c in checks if not c['pass']]},indent=2))
