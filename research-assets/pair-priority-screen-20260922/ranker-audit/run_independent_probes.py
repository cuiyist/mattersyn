"""Bounded independent audit adapter; only writes beneath ranker-audit."""
from pathlib import Path
import json,hashlib,sys,importlib.util
W=Path(__file__).resolve().parent
source=W.parent/'ranker-proposal/rank_pairs.py'
raw=source.read_bytes();digest=hashlib.sha256(raw).hexdigest()
(W/('ranker-snapshot-'+digest[:12]+'.py')).write_bytes(raw)
spec=importlib.util.spec_from_file_location('ranker_independent_audit',source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
cases=json.loads((W/'independent-probe-cases.json').read_text(encoding='utf8'))['probes']
rows=[]
for p in cases:
    c=m.cue_window(p['text']);s=m.scan_text(p['text'],'f'*64)
    group={'group_id':'audit-synthetic','queue_order':0,'source_generation':1,'review_status':'queued'}
    docs=[{'file_key':'audit.pdf','sha256':'f'*64,'role_candidate':'main'}]
    states={'audit.pdf':{'eligible_for_candidate_cues':True,'effective_role_candidate':'main','known_positive_admission_block':False,'manual_text_hold':False}}
    result=m.summarize_scope(group,docs,{'f'*64:s},states)
    rows.append({'id':p['id'],'expected_invariant':p['invariant'],'text':p['text'],'cue_window':c,'links':s['link_candidates'],'priority_band':result['priority_band'],'linkage_status':result['linkage_status'],'verified_pair':result['verified_pair'],'task_ready':result['task_ready']})
report={'ranker_script_sha256':digest,'probe_count':len(rows),'actual_scope':'Synthetic bounded regression probes, not complete corpus scientific review. Independent expected invariants predate this code snapshot.','results':rows}
out=W/('probe-results-'+digest[:12]+'.json');out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'script_sha256':digest,'results_file':str(out),'results':[{'id':r['id'],'band':r['priority_band'],'sample_tokens':r['cue_window']['sample_tokens'],'origins':r['cue_window']['origin_warnings'],'links':len(r['links'])} for r in rows]},indent=2))
