"""Additional bounded regressions identified during independent code review."""
from pathlib import Path
import json,hashlib,importlib.util
W=Path(__file__).resolve().parent;p=W.parent/'ranker-proposal/rank_pairs.py';digest=hashlib.sha256(p.read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('ranker_extra_audit',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
rows=[]
def evaluate(id,text,condition,expected):
    cue=m.cue_window(text);scan=m.scan_text(text,'e'*64)
    group={'group_id':'audit','queue_order':0,'source_generation':1,'review_status':'queued'}
    docs=[{'file_key':'audit.pdf','sha256':'e'*64,'role_candidate':'main'}]
    states={'audit.pdf':{'eligible_for_candidate_cues':True,'effective_role_candidate':'main','known_positive_admission_block':False,'manual_text_hold':False}}
    result=m.summarize_scope(group,docs,{'e'*64:scan},states)
    rows.append({'id':id,'text':text,'expected':expected,'pass':condition(cue,scan,result),'cue':cue,'links':scan['link_candidates'],'priority_band':result['priority_band']})
evaluate('integer-atom-rows-positive','Sample A was synthesized by mixing 1 mmol lead bromide in 1 mL DMSO for 12 h.\nThe atomic coordinates of sample A were refined by Rietveld analysis.\nAtom x y z occupancy\nPb 0 0 0.5 1\nBr 0.2935 0.4761 0.2061 1',lambda c,s,r:c['numeric_atom_table_candidate'] and r['priority_band'].startswith('A_'),'Integer/fractional mixed atom rows count as candidate positions; explicit A linkage gives candidate A, never verified.')
evaluate('reflection-not-atomic-rows','Sample A was synthesized by mixing 1 mmol lead bromide in 1 mL DMSO for 12 h.\nThe diffraction data of sample A were refined by Rietveld analysis.\nReflection intensities:\nh k l Fobs Fcalc\n1 0 0 0.2935 0.4761\n1 1 1 0.2061 0.1734',lambda c,s,r:not c['numeric_atom_table_candidate'] and not r['priority_band'].startswith('A_'),'Reflection h/k/l/Fobs rows do not become atomic coordinates.')
evaluate('hyphenated-variants-distinct','Sample S4-1 was synthesized by mixing 1 mmol lead bromide in 1 mL DMSO for 12 h.\nThe atomic coordinates of sample S4-2 were refined by Rietveld analysis.\nAtom x y z occupancy\nPb 0 0 0.5 1\nBr 0.2935 0.4761 0.2061 1',lambda c,s,r:set(c['sample_tokens'])=={'S4-1','S4-2'} and not s['link_candidates'] and not r['priority_band'].startswith('A_'),'Different hyphenated variants cannot collapse to the same parent sample token or produce a local same-sample join.')
evaluate('multiline-fixed-coordinate-qualifier','Sample A was synthesized by mixing 1 mmol lead bromide in 1 mL DMSO for 12 h.\nThe atomic coordinates of sample A were refined by Rietveld analysis. The minority\natomic positions were\nfixed rather than measured.\nAtom x y z occupancy\nPb 0 0 0.5 1\nBr 0.2935 0.4761 0.2061 1',lambda c,s,r:'fixed_or_constrained_positions' in c['origin_warnings'] and not r['priority_band'].startswith('A_'),'A wrapped fixed-position qualifier must remain in the coordinate-origin warning; mixed phases require manual separation.')
out=W/('supplemental-probes-'+digest[:12]+'.json');report={'script_sha256':digest,'prepared_during_code_review':True,'scope':'Four synthetic bounded checks, not scientific corpus validation.','counts':{'checks':len(rows),'failed':sum(not r['pass'] for r in rows)},'results':rows};out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({'path':str(out),'counts':report['counts'],'results':[{'id':r['id'],'pass':r['pass'],'band':r['priority_band']} for r in rows]},indent=2))
