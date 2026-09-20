"""Root-only verified release receipts and the requested joint-review pause."""
from pathlib import Path
from datetime import datetime,timezone
import argparse, json, sys
from release_support import read,sha,paper_root,load_config,assert_local_candidate,validate_delivery,SID,GID
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['prepare','verify','finish']);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
 J=paper_root();O=J/'site-integration-proposal';MON=J.parents[2];M=J.parents[4];S=M/'recipe-atlas';c=load_config(J);now=datetime.now(timezone.utc).isoformat()
 summary=assert_local_candidate(J,c);plan=read(O/'release-endpoints.json');assert plan['source_projection_manifest_sha256']==c['promotion_manifest']['sha256']
 sys.dont_write_bytecode=True;sys.path.insert(0,str(MON));import monitor
 reader_path=S/('data/paper-reviews/'+SID+'.json');reader=read(reader_path)
 assert reader['presentation_gates']['browser_render'] is True and reader['presentation_gates']['exact_product_atomic_structure_binding'] is False
 control=read(MON/'review-control.json');assert control['new_paper_admission_allowed'] is False and control['resume_requires_user_instruction'] is True
 if args.stage=='prepare':
  assert reader['presentation_gates']['publication'] is False
  prep={'status':'prepared_unpublished','at':now,'dataset_version':c['dataset_version'],'source_id':SID,'reader_sha256':sha(reader_path),'endpoint_plan_sha256':sha(O/'release-endpoints.json'),'finalizer_script_sha256':sha(J/'finalize_reader_publication.py'),'release_support_sha256':sha(J/'release_support.py'),'config_sha256':sha(J/'release-config.json'),'integration_audit_sha256':c['integration_audit']['sha256'],'browser_audit_sha256':c['browser_delta_audit']['sha256'],'publication_gate':False}
  if not args.apply:print('Prepare gates passed; no mutation.');return
  assert not(O/'release-preparation.json').exists()
  save(O/'prior-latest-publication.json',read(MON/'latest-publication.json'));save(O/'release-preparation.json',prep)
  monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id=GID,note='Sasongko contribution integrated and reviewed; anonymous delivery still pending. Finish this active contribution, then pause for joint review.',data={'current_step':'Publishing reviewed Sasongko contribution'},milestones={'audit':{'status':'complete','evidence':[str(J/c['integration_audit']['path'])],'note':'Passed distinct scientific/visual and integrated transport gates.'},'integrate':{'status':'complete','evidence':[str(J/c['integration_audit']['path']),str(J/c['browser_validation']['path'])],'note':'Nineteen records and 21 stage illustrations integrated; prior science and exports unchanged.'}})
  print('Prepared, not published.');return
 proof=validate_delivery(J,read(M/'research-assets/github-public-delivery-verification.json'),plan,c)
 proof_path=O/('science-release-anonymous-verification.json' if args.stage=='verify' else 'progress-release-anonymous-verification.json')
 if proof_path.exists():assert read(proof_path)==proof,'Preserve/version a different receipt.'
 if args.stage=='verify':
  assert reader['presentation_gates']['publication'] is False
  active=monitor.active_claims(monitor.read_ledger(MON/'ledger.json'))
  assert {x['group_id'] for x in active}<={GID},'Unexpected active work: do not silently close other papers.'
  assert control['status']=='finish_active_then_pause'
 else:
  assert reader['presentation_gates']['publication'] is True and read(O/'publication-label-delta.json')['status']=='applied_after_verified_release'
  assert not monitor.active_claims(monitor.read_ledger(MON/'ledger.json'))
  assert control['status']=='paused_for_joint_review'
  pause=read(J/c['automation_pause_receipt'])
  assert pause['automation_id']==c['automation_id'] and pause['status']=='PAUSED' and pause['actual_tool_receipt'] is True,'Root must pause the existing heartbeat with its tool and retain the real receipt.'
 if not args.apply:print('Exact delivery and stage gates passed; no mutation.');return
 if not proof_path.exists():save(proof_path,proof)
 if args.stage=='verify':
  monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id=GID,status='complete',note='Complete supplied Sasongko main/SI contribution independently reviewed, published and anonymously verified. No new paper admission.',data={'current_step':'Published and verified; paused for joint review','publication':{'dataset_version':c['dataset_version'],'site_commit':proof['site_commit'],'verification_path':str(proof_path),'verification_sha256':sha(proof_path)}},milestones={'publish':{'status':'complete','evidence':[str(proof_path)],'note':'Exact deployed public bytes verified; later changed source evidence reopens review.'}})
  assert not monitor.active_claims(monitor.read_ledger(MON/'ledger.json'))
  save(O/'review-control-before-pause.json',control)
  control.update(status='paused_for_joint_review',recorded_at=now,active_group_ids=[],new_paper_admission_allowed=False,resume_requires_user_instruction=True,automation_current_action='Root must pause the existing heartbeat now and retain its actual tool receipt; no new admissions.',remaining_time_estimate='Active papers complete; corpus work paused for joint review.',estimate_scope='The remaining corpus is unfinished. No completion date is promised during the pause.')
  control['already_published_source_ids']=list(dict.fromkeys(control.get('already_published_source_ids',[])+[SID]));save(MON/'review-control.json',control)
  ed=read(MON/'public-progress-editorial.json');save(O/'editorial-before-pause.json',ed)
  ed['current_work']=[];ed['workflow']['summary']='The active papers are published and verified. Work is temporarily paused for joint review; no new papers will start until the user asks to resume.'
  ed['workflow']['capacity']='Paused for joint review. The remaining fixed collection and separate later arrivals are unfinished.'
  ed['estimate']['status']='paused_for_joint_review';ed['estimate']['current_batch']='Friedfeld and Sasongko are published. There are no active review claims; corpus review is temporarily paused.'
  ed['estimate']['summary']='No whole-corpus completion claim or finish estimate is made while work is paused.'
  ed['recent_milestones'].insert(0,{'at':proof['build']['updated_at'],'text':'Sasongko FAPbI3 contribution published and anonymously verified: 19 records, 21 illustrated operations and 17 selected source crops. Nine paired comparisons and reference-versus-measured structure limits remain explicit. Active work is complete; the remaining corpus is paused for joint review.'})
  save(MON/'public-progress-editorial.json',ed)
  release=read(O/'prior-latest-publication.json')
  release.update(status='published_verified',dataset_version=c['dataset_version'],public_live_version='GitHub Pages / dataset'+c['dataset_version'],published_at=proof['build']['updated_at'],scientific_dataset_published_at=proof['build']['updated_at'],scientific_dataset_commit=proof['site_commit'],new_source_ids=[SID],progress_only_update=False,publication_scope='Sasongko supplied main9 + SI11 contribution; 19 records, 21 operations, 17 selected crops. Prior science and six exports unchanged; no exact QD-coordinate pair or new training admission.')
  mapping={'record_count':'canonical_records','synthesis_route_count':'synthesis_route_variant_records','material_hub_count':'public_material_hubs','direct_material_hub_count':'direct_synthesis_target_systems','component_material_hub_count':'component_only_hubs','public_source_group_count':'total_canonical_source_groups','exact_structure_recipe_count':'verified_exact_structure_recipe_pairs'}
  release.update({k:summary[v] for k,v in mapping.items()});release['formal_source_reader_count']=c['expected_reader_count'];release.pop('publication_status_delta_audit',None)
 else:
  release=read(MON/'latest-publication.json');assert release['dataset_version']==c['dataset_version'] and release['scientific_dataset_commit']
  release.update(progress_only_update=True,progress_published_at=proof['build']['updated_at'],publication_scope='Verified Sasongko publication labels and paused joint-review progress; scientific dataset unchanged.')
  control['automation_current_action']='Existing heartbeat paused by root; actual tool receipt retained.';control['automation_pause_receipt']=str(J/c['automation_pause_receipt']);save(MON/'review-control.json',control)
 release.update(recorded_at=now,commit_sha=proof['site_commit'],project_commit_sha=proof['project_commit'],current_active_paper_claims=0,review_status='paused_for_joint_review',raw_papers_and_si_uploaded=False,full_document_equivalents_excluded_from_public_history=True,subsequent_project_commits_may_record_this_verification=True)
 release['deployment']={'provider':'github_pages','status':'built','source_branch':'main','source_path':'/','commit':proof['site_commit']};release['anonymous_verification']=proof['anonymous']
 release['integration_checks']={c[k]['path']:c[k]['sha256'] for k in ['integration_audit','browser_validation','build_checks']}
 for p in [MON/'latest-publication.json',M/'research-assets/github-publication-checkpoint.json']:save(p,release)
 note=f"## 2026-09-20 — Sasongko {args.stage} delivery verified; joint-review pause\n\nSaved {now}. Dataset {c['dataset_version']}; site commit {proof['site_commit']}; scientific commit {release['scientific_dataset_commit']}. All {plan['count']} anonymous endpoint checks, {plan['additional_withheld_count']} additional withheld paths and both {c['expected_citation_count']}-citation READMEs passed. Friedfeld and Sasongko active contributions are complete within supplied-source scope; zero active claims. Remaining corpus work is unfinished and paused until a new user instruction. New admissions remain disabled and later arrivals separate. Original papers, SI, full text and full-page images stay local. No paid run or download. The root automation pause must be supported by its separate actual tool receipt.\n\n"
 p=M/'MEMORY.md';p.write_text(note+p.read_text('utf8'),'utf8')
 print(json.dumps({'stage':args.stage,'status':'published_verified','review_status':'paused_for_joint_review','site_commit':proof['site_commit']}))
if __name__=='__main__':main()
