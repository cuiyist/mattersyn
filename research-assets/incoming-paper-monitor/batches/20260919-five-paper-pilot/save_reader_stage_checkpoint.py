"""Persist current reader/SI progress without rewriting frozen scientific packages.

Root owns this checkpoint. It does not scan, promote records, close claims or publish.
"""
from pathlib import Path
from datetime import datetime, timezone
import json,hashlib,sys
B=Path(__file__).resolve().parent; MON=B.parents[1]; M=MON.parents[1]
sys.path.insert(0,str(MON));import monitor
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def verify_map(mapping,relative_base=None):
    checked=0
    for name,h in mapping.items():
        if not isinstance(h,str) or len(h)!=64:continue
        p=Path(name)
        if not p.is_absolute():
            assert relative_base is not None,name
            p=relative_base/p
        assert p.is_file() and sha(p)==h,str(p)
        checked+=1
    return checked
now=datetime.now(timezone.utc).isoformat()
ledger_path=MON/'ledger.json'; initial=read(ledger_path)
assert len(monitor.active_claims(initial))==4
pub=read(MON/'latest-publication.json')
assert pub['public_live_version']==29 and pub['deployment']['status']=='succeeded'
resume=read(B/'reader-visual-resume-20260919T2318.json')
scan=resume['scan_summary']; progress={}
configs={
 'la036034c':('nagasaki2004','reader-proposal-manifest.json',['files','bound_inputs']),
 'jp0473669':('ribeiro2004','reader-freeze-manifest.json',['files','source_inputs']),
 'ja048427j':('norberg2004','reader-package-manifest.json',['files','frozen_input_hashes'])}
for suffix,(source,manifest_name,maps) in configs.items():
    P=B/suffix;O=P/'public-review-proposal'; manifest=read(O/manifest_name)
    verified=sum(verify_map(manifest[k],O) for k in maps)
    records=[read(p) for p in sorted((P/'canonical-drafts').glob('*.json'))]
    reader=read(O/(source+'.json'));items=[i for s in reader['reader_sections'] for i in s['items']]
    audit_path=P/'reader-source-audit.json'; audit=read(audit_path) if audit_path.exists() else None
    passed=bool(audit and str(audit.get('status','')).startswith('passed'))
    if passed:
        bound=audit.get('bound_files',{})
        assert bound,'Passing reader audit must provide exact current artifact bindings.'
        verified+=verify_map(bound,P)
        auditor=audit.get('auditor',audit.get('reviewer'))
        author=audit.get('author',audit.get('reader_author'))
        assert auditor and author and auditor!=author, 'Independent auditor and reader author identities must be explicit.'
    cp={'at':now,'source_id':source,'source_generation':2,'status':'reader_source_audit_passed_visuals_pending' if passed else 'reader_author_frozen_independent_audit_pending',
        'reader_path':str(O/(source+'.json')),'reader_sha256':sha(O/(source+'.json')),
        'manifest_path':str(O/manifest_name),'manifest_sha256':sha(O/manifest_name),
        'reader_items':len(items),'canonical_records':len(records),
        'operations':sum(len(d['operations']) for d in records),
        'measurement_and_context_entries':sum(len(d['measurements']) for d in records),
        'material_slots':sum(len(d['materials']) for d in records),
        'stock_contexts':sum(len(d.get('stocks',[])) for d in records),
        'sample_contexts':sum(len(d['products']) for d in records),
        'original_asset_count':len({a['public_asset_sha256'] for i in items for a in i.get('original_assets',[])}),
        'reader_audit_status':audit['status'] if audit else 'pending',
        'reader_audit_path':str(audit_path) if audit else None,'reader_audit_sha256':sha(audit_path) if audit else None,
        'hash_bindings_verified':verified,'private_records_only':True,'public_imports':0,'training_admission':False,
        'molecular_apparatus_product_visuals':'pending','browser_validation':'not_performed','publication':'pending'}
    for name in ['visual-reuse-plan.json','visual-preparation-plan.json','visual-reuse-audit.json']:
        p=P/name
        if p.exists():
            asset_report=read(p)
            entry={'path':str(p),'sha256':sha(p),'status':asset_report.get('status','candidate plan only')}
            if name=='visual-reuse-audit.json':
                entry['counts']=asset_report.get('counts',{})
                entry['hash_bindings_verified']=verify_map(asset_report.get('bound_files_sha256',asset_report.get('bound_files',{})),P)
                assert entry['hash_bindings_verified']>0
            cp[name.replace('.json','').replace('-','_')]=entry
    render_manifest=O/'reader-original-assets-manifest.json'
    if render_manifest.exists():
        rm=read(render_manifest)
        for a in rm['assets']:assert sha(P/a['path'])==a['sha256']
        cp['reader_original_assets']={'manifest_path':str(render_manifest),'manifest_sha256':sha(render_manifest),
            'render_engine':rm['render_engine'],'asset_count':len(rm['assets']),
            'integration_note':'Use these reader-specific original-assets-pdfium files. The old source-extraction crops remain immutable and must not replace the corrected reader assets.'}
    progress[suffix]=cp;save(P/'reader-progress-checkpoint.json',cp)
    group=read(ledger_path)['groups']['10.1021_'+suffix]
    assert group['generation']==2 and group['fingerprint']['generation']==2
    d=dict(group['review']['checkpoint'])
    d.update(reader_progress=cp,reader_items=len(items),reader_scientific_audit_status='passed' if passed else 'pending',
        publication_status='pending; private source reader and canonical records only',last_substantive_checkpoint_at=now,
        next_action='Qualify/reuse exact molecular references, generate missing source-specific molecules and stage-specific apparatus/product visuals; independently review and integrate into the same Site, exercise browser controls, then publish.' if passed else 'Finish separate scientific reader audit, then prepare and independently review molecule/apparatus/product visuals before integration and publication.')
    d['current_work_items']=[
        {'label':'Source and canonical review','status':'complete','scope':f'{len(records)} private canonical records independently audited; source gaps retained.'},
        {'label':'Academic source reader','status':'complete' if passed else 'in_progress','scope':f'{len(items)} cards and {cp["original_asset_count"]} original assets; independent reader audit '+('passed.' if passed else 'pending.')},
        {'label':'Scientific viewers and publication','status':'in_progress','scope':d['next_action']}]
    ms={'extract':{'status':'partial','evidence':[str(O/manifest_name),str(P/'canonical-record-manifest.json')],
         'note':'Canonical and reader source coverage prepared; final molecular/apparatus/product bindings still pending.'},
        'audit':{'status':'partial','evidence':[str(audit_path if passed else P/'canonical-records-audit.json')],
         'note':'Source and canonical'+(' and reader' if passed else '')+' audits passed; visuals, integration and public behavior require further review.'}}
    monitor.checkpoint(ledger_path,'mattersyn-primary',group_id='10.1021_'+suffix,data=d,milestones=ms,
        note='Saved frozen academic reader and current independent scientific-review status; no promotion or publication.')

H=B/'jp0219348';chunks=[]
for pages,transcription_name,audit_name in [([1,2],'si-reflections-transcription.json','si-pages-1-2-independent-audit.json'),
                                         ([3,4],'si-pages03-04-transcription.json','si-pages-3-4-independent-audit.json')]:
    t=read(H/transcription_name);a=read(H/audit_name)
    assert str(a['status']).startswith('passed')
    count=verify_map(a['bound_files'],H)
    rows=t['rows'];cells=[c for r in rows for c in r['cells']]
    chunks.append({'pages':pages,'transcription_path':str(H/transcription_name),'transcription_sha256':sha(H/transcription_name),
        'audit_path':str(H/audit_name),'audit_sha256':sha(H/audit_name),'audit_status':a['status'],
        'rows':len(rows),'numeric_cells':sum(c['evidence']['column_key']!='marker' for c in cells),
        'markers':sum(c['evidence']['column_key']=='marker' for c in cells),'hash_bindings_verified':count})
hp={'schema':'mattersyn-si-numerical-progress-index/1','at':now,'source_id':'heo2003','source_generation':2,
    'transcribed_and_independently_audited_pages':[1,2,3,4],'chunks':chunks,
    'rows':sum(c['rows'] for c in chunks),'numeric_cells':sum(c['numeric_cells'] for c in chunks),'markers':sum(c['markers'] for c in chunks),
    'remaining_untranscribed_and_unaudited_pages':list(range(5,15)),
    'remaining_row_count':None,'complete_SI_numerical_review':False,'exact_structure_pair_created':False,
    'progress_note':'This index aggregates separately audited immutable chunks; historical pending statuses inside their author checkpoints are retained. Pages5–14 still require cell transcription and independent numerical audit.',
    'latest_correction_history':{'path':str(H/'si-pages03-04-correction-history.json'),'sha256':sha(H/'si-pages03-04-correction-history.json')}}
assert (hp['rows'],hp['numeric_cells'],hp['markers'])==(350,2100,350)
save(H/'si-numerical-progress-index.json',hp);progress['jp0219348']=hp
group=read(ledger_path)['groups']['10.1021_jp0219348'];d=dict(group['review']['checkpoint'])
d.update(si_numerical_progress=hp,last_substantive_checkpoint_at=now,
         next_action='Continue numerical transcription and independent cell review for SI pages 5–14. Preserve source conflicts and limits of the average crystal structure, then prepare the structured records, reader and illustrations.')
d['current_work_items']=[{'label':'Main paper and tables','status':'complete','scope':'All 9 main pages and 5 main tables have passed independent source review.'},
    {'label':'SI numerical review','status':'in_progress','scope':'Pages 1–4: 350 rows, 2,100 numeric cells and 350 markers independently audited. Pages 5–14 still need transcription and numerical review.'},
    {'label':'Canonical, illustrated reader and publication','status':'in_progress','scope':'Pending; no CIF, exact structure pair or training admission.'}]
monitor.checkpoint(ledger_path,'mattersyn-primary',group_id='10.1021_jp0219348',data=d,
    note='Added independently audited SI pages3–4, with one corrected digit and immutable prior revision; pages5–14 still pending.')

wf=read(B/'workflow-state.json');idx=read(B/'source-review-index.json')
for target in [wf,idx]:
    target['updated_at']=now
    for paper in target['papers']:
        suffix=paper['group_id'].split('_',1)[1]
        if suffix in configs:
            paper['reader_progress']=progress[suffix]
            passed=str(progress[suffix]['reader_audit_status']).startswith('passed')
            paper['full_extraction']='canonical_and_academic_reader_prepared_visuals_pending'
            paper['full_scientific_audit']='source_canonical_reader_passed_visuals_pending' if passed else 'source_canonical_passed_reader_audit_pending'
        elif suffix=='jp0219348':paper['si_numerical_progress']=hp
wf['status']='Gu_published_v29; three_private_readers_prepared_with_current_audits; Heo_SI1_4_audited_5_14_pending'
wf['latest_queue_snapshot']={'at':scan['last_scan_at'],'source_copies':scan['present_files'],
    'incoming_copies':scan['source_document_copies']['incoming'],'legacy_copies':scan['source_document_copies']['legacy'],
    'waiting':scan['waiting_review_scopes'],'active':4,'pending_unscreened_scopes':scan['priority_pending_unscreened_scopes'],
    'scope':'Dated metadata scan, not a new full-paper review or verified unique-paper count.'}
save(B/'workflow-state.json',wf);save(B/'source-review-index.json',idx)
skill=M/'skills/mattersyn-paper-to-site/references/full-paper-review.md'
installed=Path(r'[local path redacted]')
assert sha(skill)==sha(installed)
checkpoint={'at':now,'batch_id':wf['batch_id'],'source_priority':'synthesis_and_structure_evidence_richness',
    'private_reader_progress':{k:progress[k] for k in configs},'Heo_SI_progress':hp,
    'latest_scan':wf['latest_queue_snapshot'],'published_version_unchanged':29,
    'site_changed_this_stage':False,'new_public_contributions_this_stage':0,'active_claims':len(monitor.active_claims(read(ledger_path))),
    'skill_reference_sha256':sha(skill),'skill_validation':'Project and installed quick_validate checks passed using existing Miniforge YAML runtime.'}
save(B/'reader-stage-progress.json',checkpoint)

heading='## 2026-09-19 — Three academic readers; Heo SI pages 1–4 numerically audited'
parts=[heading,'',
    'Evidence-rich synthesis/structure priority remains active, with the same five-paper batch preserved and four claims still active. Actual concurrent AI capacity remains four agents including root. Gu stays published at Site version29/dataset0.22.0; this reader stage did not modify or deploy the Site. No original papers were renamed or downloaded. Molecular/apparatus/product visuals, browser checks and publication remain pending for the three new readers.',
    '']
for suffix in configs:
    p=progress[suffix]
    parts.append(f'{p["source_id"]}: {p["reader_items"]} academic reader cards, {p["canonical_records"]} private canonical records, {p["operations"]} operations, {p["measurement_and_context_entries"]} measurement/context entries, {p["material_slots"]} material slots, {p["stock_contexts"]} stock contexts, {p["sample_contexts"]} sample/context IDs and {p["original_asset_count"]} original assets. Reader independent status: {p["reader_audit_status"]}. Reader SHA256 {p["reader_sha256"]}; manifest SHA256 {p["manifest_sha256"]}; audit SHA256 {p["reader_audit_sha256"]}. Exact private paths and current verified bindings: research-assets/incoming-paper-monitor/batches/20260919-five-paper-pilot/{suffix}/reader-progress-checkpoint.json. No public import or training admission.')
    parts.append('')
parts.extend([
    'Heo now has two separately frozen numerical chunks covering SI pages1–4 (printed41–44):350rows,2100numericcells and350uninterpreted markers, independently audited. The newly added pages3–4 contain180rows,1080numericcells,180markers and8negative Fobs² values. The distinct reviewer caught one source transcription digit: p4leftrow33,hkl(1,15,17),Fobs²255019.38→255019.39. Root reopened the native crop, corrected only that token, preserved the prior four outputs and recorded the cell delta. Corrected chunk audit SHA256376c4641af742164f12032b67917ebf01742b34c5449ebf2143387381affa8b9. The other1259tokens remained unchanged. Prior1–2audit and main/source artifacts remain byte-identical. Current aggregate scope: jp0219348/si-numerical-progress-index.json. Every numerical cell on pages5–14 remains pending; complete SI review, CIF, exact structure pair and publication are NOT approved.',
    '',
    'Ribeiro reader preserves the acid-set versus unreported post-TBAOH pH, radius versus diameter, source Figure3/4 typo, 500:1 ratio with unspecified basis, model assumptions and main-only SI gap. Root actually read all6main-textpages, all93readeritems and viewed all15originalcrops; separate reader audit passed1976consistencychecks after bounded author prose/sample-link corrections. It maps193typedfields as101visibletypedfacts plus92retained source-context prose fields; these are not193measured outcomes. Nagasaki preserves C1–C4, pre-dialysisbiotin branch and unresolved SI specimen joins. Norberg preserves A–Fcontexts, D/F conflict, collectiveS>800 and incomplete film preparation. Source models and raw metadata are not new experiments.',
    '',
    f'Latest dated intake scan {scan["last_scan_at"]}: {scan["present_files"]} documentcopies ({scan["source_document_copies"]["incoming"]} incoming +{scan["source_document_copies"]["legacy"]} legacy), {scan["waiting_review_scopes"]} waitingprovisionalscopes,4active;154new/unranked scopes await incremental screening before the next batch. All4active gen2source bundles matched saved manifests at resume. No corpus-wide text re-extraction was run. Verified unique-paper/material/recipe totals remain unknown.',
    '',
    'Visual plans: Nagasaki retains its prior61slot reuse plan; Ribeiro visual-preparation-plan.json covers13slots/9identities/13scenes, SHA256b9751dabb6dd97068bce5bea101eee30243ddb2c05b08808d7aad183872c0a74. Ribeiro cached-reference audit passed401checks and52currentfilehashes (audit SHA2566e09841cba187ce4d3a39e9c116a955129f77aed109d6a8068b32785a6b41bfb): ethanol/water qualify for3slots,3unchangedcandidates are rejected,7slots remain pending. Required hydroxide cannot inherit the bromide counterion; acid/support source metadata cannot transfer. Hydrolysis water cannot inherit Milli-Q or deionized-dialysis labels. No final binding or scene approval is granted.',
    '',
    'Norberg reader-specific original assets: the independent reviewer found Poppler degree-symbol corruption. All40 reader images were faithfully re-rendered from the same verified PDFs with PDFium (pypdfium2 5.13.0/PDFium153.0.7999.0), retaining crop bounds and dimensions. Final reader-original-assets-manifest.json SHA25600f40350fa13b3a3e07972a8d6563ba3db2651e535b598098e0f2aebc74278e3. Integrate public-review-proposal/original-assets-pdfium files, not the old extraction crops. Prior extraction/canonical files and two earlier reader freezes remain preserved. Consult the current independent reader audit status above for the final replacement-asset check.',
    '',
    f'Memory and reusable skill synchronized. Project/installed full-paper-review.md SHA256{sha(skill)}; both validators passed. Added immutable numeric chunks and correction provenance, treatment/measurement uncertainty, deduplicated source-context pointers, readable academic captions and explicit field-display transformations. Use save_reader_stage_checkpoint.py for this phase; old save_presentation_checkpoint.py hardcodes Heo1–2/readerpending/olderintake and would rewind progress. Next: finish any remaining reader audits, prepare and independently review all missing viewers, integrate ready contributions into the SAME Site and publish after browser verification, while advancing Heo pages5–14. The existing single heartbeat continues; no duplicate automation or complete-corpus claim.',
    ''])
memory=M/'MEMORY.md';old=memory.read_text(encoding='utf-8')
if old.startswith(heading):
    split=old.find('\n## ',len(heading))
    old=old[split+1:] if split>=0 else ''
memory.write_text('\n\n'.join(parts).rstrip()+'\n\n'+old,encoding='utf-8')
print(json.dumps({'at':now,'readers':{k:v['reader_audit_status'] for k,v in progress.items() if k in configs},
    'Heo_rows_audited':hp['rows'],'active_claims':checkpoint['active_claims'],'site_changed':False,
    'skill_sha256':sha(skill)},ensure_ascii=False))
