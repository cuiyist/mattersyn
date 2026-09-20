from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
E=Path(__file__).resolve().parent;MON=E.parents[2];M=E.parents[4];I=E.parent/'intake-20260920T071632Z/intake-manifest.json'
sys.path.insert(0,str(MON));import monitor
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
group='legacy::10.1021_acsami.1c18038';paper=next(p for p in read(I)['papers'] if p['paper_id']==group)
assert paper['bundle_sha256']=='a66f9080c2876ab1cf3186edc8821f577dd9a5455a1e91839e0aa7c3711c0fd5'
title='Realizing Near-Unity Quantum Efficiency of Zero-Dimensional Antimony Halides through Metal Halide Structural Modulation';now=datetime.now(timezone.utc).isoformat()
monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id=group,note='Admitted via current fixed-cutoff membership and independently audited evidence-priority workflow. Root checked matching titles/byline on main/SI firstpages only; full source review assigned after existing molecular handoff.',data={'current_step':'Main/SI identity verification and complete source reading next','title_from_main_first_page':title,'author_label':'Lian et al. (2021)','page_counts':{'main':8,'si':26},'intake_manifest':{'path':str(I),'sha256':sha(I)},'review_directory':str(E.parent/'acsami.1c18038'),'no_full_reading_claim':True})
ed=read(MON/'public-progress-editorial.json');ed['current_work'].append({'short_label':'Lian et al. (2021)','title':title,'stage':'Admitted from screened fixed collection; source reading next','summary':'The existing local8-page main paper and26-page SI have matching first-page titles and authors. Full pairing, reading and extraction are the next steps. This is an intake candidate, not a reviewed synthesis or published contribution.','stages':[{'label':'Stable source bundle and cutoff selection','status':'complete','detail':'Main/SI originals retained with SHA256identities; selected by synthesis/structure evidence rank.'},{'label':'Complete source reading and extraction','status':'pending','detail':'Assigned after the current chemical-illustration handoff.'},{'label':'Independent audits and website release','status':'pending','detail':'No scientific approval or training admission yet.'}],'gaps':['Full main/SI content, synthesis variants, atomic structure availability and property/sample assignments remain unverified.']})
cut=read(MON/'deadline-20260920/active-cutoff.json')['counts'];pending=cut['included_pending_scopes'];assert pending==9511
ed['estimate']['summary']=f'The two-month target covers the fixed existing collection. Following completed reviews and duplicate reconciliation, {pending:,} provisional cutoff scopes remain pending, plus three nested identity cases. Roughly159closures/day over60days or190/day over50production days would be required. Achievable capacity and the recipe-bearing fraction remain unverified.'
ed['estimate']['current_batch']='Original five-paper pilot5/5published; Evans rolling contribution published. Morrison has passed source and structured-data audits; Lian2021was admitted for the next source review. Later arrivals remain separate.'
ed['recent_milestones'].insert(0,{'at':now,'text':'The completed Evans slot was refilled from the screened fixed collection with Lian2021antimony halides. Morrison illustrations continue in parallel. Latest folder scan found13,984documentcopies; later-arrival papers remain outside the fixed deadline collection.'})
save(MON/'public-progress-editorial.json',ed)
p=MON/'latest-publication.json';release=read(p);release['current_active_paper_claims']=2
for p in [MON/'latest-publication.json',M/'research-assets/github-publication-checkpoint.json']:save(p,release)
save(E.parent/'next-intake-checkpoint-20260920T0716.json',{'at':now,'group_id':group,'intake_manifest_sha256':sha(I),'first_pages_only_checked_by_root':True,'full_review_pending':True,'cutoff_counts':cut})
print(json.dumps({'next':title,'main_pages':8,'si_pages':26,'fixed_pending_scopes':pending,'active':2}))
