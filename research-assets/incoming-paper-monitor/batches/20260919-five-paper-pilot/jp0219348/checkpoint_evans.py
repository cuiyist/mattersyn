"""Root-owned queue checkpoint from Evans frozen source audit and reader proposal."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys
H=Path(__file__).resolve().parent;MON=H.parents[2];E=MON/'batches/20260920-rolling-pipeline/ja103805s'
sys.path.insert(0,str(MON));import monitor
audit=E/'source-scientific-audit.json';freeze=E/'proposal-freeze-v2.json';source=E/'source-extraction-revision-2/source-extraction-freeze.json'
assert all(p.is_file() for p in [audit,freeze,source])
assert json.loads(audit.read_text(encoding='utf8'))['status'].startswith('passed')
data={'review_package':str(E),'source_scientific_audit_status':'passed_revision_2','source_scientific_audit':str(audit),'source_extraction_freeze':str(source),'canonical_reader_proposal_freeze':str(freeze),
 'main_pages_text_reviewed':[1,2,3],'main_pages_visually_reviewed':[1,2,3],'si_pages_text_reviewed':list(range(1,22)),'si_pages_visually_reviewed':list(range(1,22)),
 'source_typed_facts':457,'source_units':198,'selected_original_assets':25,'si_status':'All21 SI pages plus molecular CIF read and independently audited. CIF belongs to molecular compound9, not a QD lattice.',
 'canonical_scientific_audit_status':'in_progress_frozen_v2','publication_status':'private_proposal_not_integrated',
 'last_substantive_checkpoint_at':datetime.now(timezone.utc).isoformat(),
 'next_action':'Independent canonical/reader audit runs alongside private molecular assets. Keep revisions separate; integrate only passed outputs.',
 'current_work_items':[{'label':'Main/SI/CIF source extraction and independent audit','status':'complete_within_scope','scope':'24pages,457facts,2896CIFcells; one dimensionless-unit correction preserved.'},{'label':'Canonical/reader independent audit and molecular assets','status':'in_progress','scope':'32draftrecords,3QD/MSC route families; no automatic training or publication promotion.'}]}
milestones={'read':{'status':'complete','evidence':[str(audit)]},'extract':{'status':'partial','evidence':[str(source),str(freeze)],'note':'Full source extraction passed; canonical proposal has a separate active audit.'},'audit':{'status':'partial','evidence':[str(audit)],'note':'Source audit passed; canonical, visual, integration and publication gates remain.'}}
r=monitor.checkpoint(MON/'ledger.json','mattersyn-primary',data=data,note='Evans full source audit passed revision2; frozen canonical/reader independent audit and molecular assets underway.',milestones=milestones,group_id='10.1021_ja103805s')
print(json.dumps({k:r[k] for k in ['group_id','status','claim_retained','active_review_claims']},indent=2))
