"""Save Heo's completed review gates, then close only after verified deployment."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,sys,hashlib
H=Path(__file__).resolve().parent;MON=H.parents[2];M=H.parents[4];O=H/'site-integration-proposal'
sys.path.insert(0,str(MON));import monitor
parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['ready','published']);a=parser.parse_args()
now=datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def refs(*names):
 paths=[H/n for n in names]
 assert all(p.is_file() for p in paths)
 return [str(p) for p in paths]
ledger=read(MON/'ledger.json');g=ledger['groups']['10.1021_jp0219348']
snap=O/'pre-final-review-checkpoint.json'
if not snap.exists():save(snap,g['review'])
milestones={
 'read':{'status':'complete','evidence':refs('source-scientific-audit.json','si-complete-candidate/independent-audit.json'),'note':'All 9 main and14 matched SI pages; two source SI signs unresolved explicitly.'},
 'extract':{'status':'complete','evidence':refs('canonical-proposal/v2/proposal-package-manifest.json','canonical-proposal/audit-v2/independent-audit.json')},
 'audit':{'status':'complete','evidence':refs('canonical-proposal/audit-v2/independent-audit.json','visuals/molecules-independent-audit/binding-revision-3-delta-audit.json','visuals/apparatus/audit-v1/apparatus-source-audit.json','visuals/products-independent-audit/product-si-source-audit.json','site-integration-independent-audit/promotion-projection-delta-audit.json','integration-code-independent-audit/delta-audit.json')},
 'integrate':{'status':'complete','evidence':refs('site-integration-proposal/site-import-manifest.json','site-integration-proposal/build-check-output.json','site-integration-proposal/browser-validation.json')},
 'publish':{'status':'pending','evidence':[]}}
data={'si_status':'All14 scanned SI pages and1209 reflection rows transcribed and independently audited;7252 resolved numeric positions,2 signed nulls with both candidates.',
 'source_extraction_status':'complete_with_explicit_source_uncertainties','source_scientific_audit_status':'passed_main_and_complete_si_scopes','canonical_scientific_audit_status':'passed_v2_and_promotion_delta',
 'private_typed_draft_records':10,'canonical_records_created':10,'private_canonical_drafts_audited':10,'visual_reuse_qualification_status':'passed_source_specific_models_and_browser',
 'source_review_checkpoint':str(O/'review-ready-checkpoint.json'),'last_substantive_checkpoint_at':now,
 'current_work_items':[{'label':'Reading, extraction, independent audits and illustrated reader','status':'complete_within_scope','scope':'1route,3acquisition procedures,6contexts;473measurements;1209SIrows; no new training labels.'}],
 'next_action':'Publish checked contribution and verify anonymous bytes before closing this claim.',
 'publication_status':'integrated_and_checked_deployment_pending'}
if a.stage=='published':
 v=read(M/'research-assets/github-public-delivery-verification.json')
 assert v['status']=='passed' and any(x['path']=='data/paper-reviews/heo2003.json' and x['matches_checked_local_bytes'] for x in v['anonymous']['checks'])
 frozen=O/'science-release-anonymous-verification.json';save(frozen,v)
 data.update(publication_status='published_verified',publication_url='https://cuiyist.github.io/mattersyn-site/paper-review.html?id=heo2003',next_action='Complete for current generation; reopen if main/SI evidence changes.',published_commit=v['site_commit'])
 milestones['publish']={'status':'complete','evidence':[str(frozen)],'note':'GitHub Pages build and exact anonymous content verified.'}
 result=monitor.checkpoint(MON/'ledger.json','mattersyn-primary',status='complete',data=data,note='Heo complete main/SI contribution audited, integrated and anonymously verified on GitHub Pages.',milestones=milestones,group_id='10.1021_jp0219348')
else:
 result=monitor.checkpoint(MON/'ledger.json','mattersyn-primary',data=data,note='Heo full source/canonical/visual audit and actual browser verification passed; publication pending.',milestones=milestones,group_id='10.1021_jp0219348')
save(O/('review-published-checkpoint.json' if a.stage=='published' else 'review-ready-checkpoint.json'),{'at':now,'result':result,'milestones':milestones})
print(json.dumps({k:result[k] for k in ['group_id','status','claim_retained','active_review_claims']},indent=2))
