"""Record the verified GitHub publication and close only its three audited source scopes."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess,sys
ROOT=Path('[local path redacted]');MON=ROOT/'research-assets/incoming-paper-monitor'
B=MON/'batches/20260919-five-paper-pilot';O=B/'integration-proposal'
NOW=datetime.now(timezone.utc).isoformat();COMMIT='6e9c97b961fa0d5db2463cc017f483e406908389'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf8')
def binding(p):
    assert p.is_file(),p
    return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
verification=read(ROOT/'research-assets/github-publication-verification.json')
assert verification['status']=='passed' and verification['public_commit']==COMMIT
release={'schema':'mattersyn.publication-checkpoint.github.v1','status':'published_verified',
    'host':'github_pages','public_url':'https://cuiyist.github.io/mattersyn-site/',
    'public_live_version':'GitHub Pages / dataset0.23.0','published_at':'2026-09-20T02:23:26Z',
    'recorded_at':NOW,'public_repository':'https://github.com/cuiyist/mattersyn-site',
    'private_repository':'https://github.com/cuiyist/mattersyn','commit_sha':COMMIT,
    'private_initial_backup_commit':'d22f6715091387965ff9e3f1e9a983f19217b6b2',
    'dataset_version':'0.23.0','record_count':470,'synthesis_route_count':97,'material_hub_count':42,
    'direct_material_hub_count':32,'component_material_hub_count':10,'public_source_group_count':31,
    'formal_source_reader_count':26,'exact_structure_recipe_count':0,
    'new_source_ids':['nagasaki2004','ribeiro2004','norberg2004'],
    'deployment':{'provider':'github_pages','status':'built','source_branch':'main','source_path':'/','commit':COMMIT},
    'anonymous_verification':verification,'public_transport_audit':binding(ROOT/'research-assets/github-public-staging-audit.json'),
    'reader_integration_audit':binding(O/'reader-integration-independent-audit.json'),
    'asset_integration_audit':binding(O/'asset-integration-independent-audit.json'),
    'asset_url_addendum':binding(O/'asset-integration-url-addendum.json'),
    'historical_sites_deployment':{'version':29,'dataset_version':'0.22.0','url':'https://mattersyn-recipe-atlas.cuiy781513.chatgpt.site/'},
    'raw_papers_and_si_uploaded':False,'remaining_batch_papers':1}
historical=MON/'latest-publication-sites-v29.json'
if not historical.exists():shutil.copyfile(MON/'latest-publication.json',historical)
write(MON/'latest-publication.json',release)
write(ROOT/'research-assets/github-publication-checkpoint.json',release)

for folder,source,count in [('la036034c','nagasaki2004',16),('jp0473669','ribeiro2004',11),('ja048427j','norberg2004',19)]:
    p=B/folder
    scope='All supplied main pages; SI unverified and not inferred absent.' if source=='ribeiro2004' else 'All supplied main and content-matched SI pages.'
    visual=['component-source-audit.json','apparatus-source-audit.json','product-source-audit.json'] if source=='nagasaki2004' else ['visual-source-audit.json']
    evidence=[p/x for x in ['source-scientific-audit.json','canonical-records-audit.json','reader-source-audit.json','promotion-source-audit.json',*visual]]
    for file in evidence:assert file.is_file(),file
    paper_release={**release,'source_id':source,'source_scope':scope,'new_records_for_source':count,
        'source_audits':[binding(x) for x in evidence]}
    write(p/'publication-checkpoint.json',paper_release)
    milestones={
        'read':{'status':'complete','evidence':[str(p/'page-coverage.json')],'note':scope},
        'extract':{'status':'complete','evidence':[str(p/'source-inventory.json'),str(p/'canonical-record-manifest.json'),str(p/'reader-source-audit.json')],'note':f'{count} source-scoped records and full reader coverage; record count is not an independent experiment count.'},
        'audit':{'status':'complete','evidence':[str(x) for x in evidence]+[str(O/'reader-integration-independent-audit.json'),str(O/'asset-integration-independent-audit.json'),str(O/'asset-integration-url-addendum.json')],'note':'Independent source/canonical/reader/visual and integration audit scopes passed; unresolved source facts remain explicit.'},
        'integrate':{'status':'complete','evidence':[str(B/'build-check-output.json'),str(ROOT/'research-assets/github-public-staging-audit.json')],'note':'Integrated with source-specific figures, molecular/solution/product views and operation diagrams. Browser behavior checked; published scientific files match source.'},
        'publish':{'status':'complete','evidence':[str(p/'publication-checkpoint.json')],'note':'GitHub Pages build completed; anonymous delivery verified against checked files.'}}
    data={'publication_status':'published_verified_GitHub_Pages','publication_checkpoint':str(p/'publication-checkpoint.json'),
        'last_substantive_checkpoint_at':NOW,'next_action':'Current supplied source scope complete. Reopen for new/changed main/SI or new audit findings.',
        'canonical_records_created':count,'browser_validation_status':'passed','current_work_items':[
            {'label':label,'status':'complete','scope':info['note']} for label,info in milestones.items()]}
    write(p/'github-completion-data.json',data);write(p/'github-completion-milestones.json',milestones)
    ledger=read(MON/'ledger.json');group='10.1021_'+folder
    if ledger['groups'][group]['review']['status']!='complete':
        result=subprocess.run([sys.executable,'-X','utf8',str(MON/'monitor.py'),'checkpoint','--reviewer','mattersyn-primary','--group',group,
            '--status','complete','--data',str(p/'github-completion-data.json'),'--milestones',str(p/'github-completion-milestones.json'),
            '--note','Audited source contribution published on GitHub Pages; anonymous delivery verified.'],capture_output=True,text=True,encoding='utf8')
        if result.returncode:raise SystemExit(result.stderr or result.stdout)
        print(f'Closed verified supplied source scope: {source}',flush=True)

w=read(B/'workflow-state.json');w['updated_at']=NOW
w['status']='Gu_previously_published;Nagasaki_Ribeiro_Norberg_published_GitHub_Pages;Heo_SI1_12_audited_13_14_pending'
w['next_action']='Resume Heo SI13-14 and its independent audit; preserve explicit uncertain signs on pages11-12. Continue evidence-priority selection after the retained batch. Publish future releases to GitHub Pages and sync the private project backup.'
for p in w['papers']:
    if p['group_id'] in {'10.1021_la036034c','10.1021_jp0473669','10.1021_ja048427j'}:
        p['publication']='published_verified_GitHub_Pages_dataset0.23.0';p['publication_commit']=COMMIT
        p['full_extraction']='complete_within_supplied_source_scope_missingness_retained'
write(B/'workflow-state.json',w)
memory=ROOT/'MEMORY.md';heading='## 2026-09-20 — GitHub migration complete; private project and public Pages website'
entry=f'''{heading}

Saved {NOW}. Website: https://cuiyist.github.io/mattersyn-site/ . PUBLIC website-only repository: https://github.com/cuiyist/mattersyn-site . PRIVATE project repository: https://github.com/cuiyist/mattersyn . Visibility verified through authenticated GitHub metadata; the private repository returns404 anonymously. Both initial pushes succeeded. Public commit {COMMIT}; GitHub Pages build completed2026-09-20T02:23:26Z with HTTPS. Twelve anonymous page/data/asset requests exactly matched the checked deployment bytes; periodic-table navigation and source-specific controls/figures were browser-checked. No ChatGPT login is required. The old chatgpt.site address remains a historical version29 deployment; future publication targets GitHub Pages.

The private backup preserves30 prior website commits as ancestry and about59,000 project files, including code, memory, skills, structured extraction outputs and scientific audit history. The first private backup commit is d22f6715091387965ff9e3f1e9a983f19217b6b2; later commits add final publication/queue/memory checkpoints. Raw downloaded papers and SI, installed dependencies, credentials and redundant archives remain local. Explicit manifests and checks are under research-assets/github-*.json. Working copies: [local path redacted] and [local path redacted] The authoring project stays [local path redacted]; never edit its source PDFs to prepare a backup. Private Git history formerly has website files at root; the backup reorganizes the current application under recipe-atlas/.

Published dataset0.23.0 has470 canonical records,97 route/variant records,42 material collections(32direct+10component),31sourcegroups and26formalreaders/245pages. Nagasaki CdS, Ribeiro SnO2 and Norberg Mn:ZnO add46records. Their individual source scopes passed the required audits and are now closed after verified publication; missing SI in Ribeiro remains explicitly unverified. These counts are not independent experiments or a completed-corpus claim. Heo remains the one unfinished batch member:SI1-12 audited with two unresolved signs;13-14 pending. Exact structure-recipe pairs remain0; no coordinates were invented.

The existing single five-minute heartbeat has been updated to the chosen GitHub destination, retaining evidence-priority batches, local-only sources, independent audits and quiet notifications. Consult research-assets/github-publication-checkpoint.json and incoming-paper-monitor/latest-publication.json for authoritative current release state. Supersedes earlier GitHub authorization/upload/publishing-pending entries below.

'''
old=memory.read_text(encoding='utf8')
if heading not in old:memory.write_text(entry+old,encoding='utf8')
config=Path('[local path redacted]')
shutil.copyfile(config,ROOT/'research-assets/mattersyn-review-automation.toml')
print('Saved GitHub publication, private/public scope and current memory.')
