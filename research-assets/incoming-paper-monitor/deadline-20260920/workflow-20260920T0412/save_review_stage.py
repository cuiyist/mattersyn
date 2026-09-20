from pathlib import Path
from datetime import datetime,timezone
import json,sys
HERE=Path(__file__).resolve().parent;MON=HERE.parent.parent;ROOT=MON.parent.parent
sys.path.insert(0,str(MON));import monitor
now=datetime.now(timezone.utc).isoformat()
H=MON/'batches/20260919-five-paper-pilot/jp0219348'
audit=H/'visuals/molecules-independent-audit/independent-audit.json'
assert audit.is_file()
heo={'next_action':'Resolve canonical v1 independent findings in preserved v2; finalize apparatus/product/reader integration using the independently passed effective molecular registry plus binding revision2. No Heo publication yet.',
 'last_substantive_checkpoint_at':now,
 'current_work_items':[
  {'label':'Canonical source-to-record and reader audit','status':'in_progress','scope':'Distinct audit of frozen v1; duplicate reader sample links and SI-audit path correction remain under revision.'},
  {'label':'Molecular identities and exact stock/material bindings','status':'complete_within_scope','scope':'Distinct audit passed original molecular assets plus effective registry and binding revision2. This is not Site/browser/product approval.'},
  {'label':'Apparatus, product and reader integration','status':'in_progress','scope':'14-stage draft and audited average occupancy CIF; final scene/model integration and browser checks pending.'}],
 'molecular_binding_audit':{'path':str(audit),'status':'passed_effective_registry_and_binding_revision2_only'},
 'canonical_records_promoted':False,'published':False}
monitor.checkpoint(MON/'ledger.json','mattersyn-primary','in_progress',data=heo,group_id='10.1021_jp0219348',note='Screen-first rolling pipeline resumed; scoped molecular audit passed, canonical correction and Site integration remain.')
evans={'title':'Mysteries of TOPSe Revealed: Insights into Quantum Dot Nucleation','doi':'10.1021/ja103805s',
 'evidence_directory':str(MON/'batches/20260920-rolling-pipeline/ja103805s'),
 'main_pages':3,'si_pages':21,'pairing_status':'content_verification_in_progress',
 'next_action':'Complete source pairing and inventory, then independently authored extraction; a different reviewer audits the frozen package.',
 'current_work_items':[{'label':'Main/SI/CIF identity and page inventory','status':'in_progress','scope':'Original local main,21-pageSI,CIF; preserve precursor/molecular versus QD product distinctions.'}],
 'extractor':'/root/norberg2004_extract','independent_auditor':'to_be_assigned_distinct_from_extractor',
 'source_scope_note':'No scientific completion, coordinate-product pair, canonical record or publication approval from automated ranking or file availability.'}
monitor.checkpoint(MON/'ledger.json','mattersyn-primary','in_progress',data=evans,group_id='10.1021_ja103805s',note='Admitted into a free active slot after complete cutoff screening. Source extraction proceeds while Heo is independently audited.')
p=MON/'public-progress-editorial.json';d=json.loads(p.read_bytes())
d['current_work'][0]['stages'][4]['detail']='Molecular identities and exact stock/material bindings audited; apparatus, product and browser checks remain'
d['recent_milestones'].insert(0,{'at':now,'text':'Heo molecular identities and exact material/stock bindings passed their scoped independent audit after a source-page locator correction. Canonical corrections and website integration remain pending.'})
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
proof={'checked_at':now,'workflow_audit':'independent-workflow-audit.json','workflow_audit_status':'passed',
 'molecule_audit':str(audit),'molecule_audit_status':'passed_combined_effective_package',
 'browser_local_progress':{'url':'http://127.0.0.1:5190/progress.html','actual_dom_and_screenshot_checked':True,'error_logs':0,'published_records_unchanged':470,'workflow_and_two_active_papers_visible':True},
 'scientific_contributions_published_in_this_stage':0}
(HERE/'stage-checkpoint.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8')
print(json.dumps({'checkpointed':['Heo','Evans'],'new_scientific_publications':0}))
