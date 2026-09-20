"""Save exact verified progress delivery and a resumable scientific-work handoff."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
F=Path(__file__).resolve().parent;M=F.parents[4];J=F.parent/'acs.jpcc.5c05144'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=F/'progress-publication/anonymous-progress-verification.json';v=read(proof)
assert v['status']=='passed' and v['pages_build']['commit']=='e986792d8b55727241d515ac25890f2ee679c1ab'
assert len(v['endpoints'])==5 and all(x['anonymous_exact_match'] for x in v['endpoints'])
assert not v['new_science_records_published']
pa=F/'site-integration-independent-audit/promotion-delta-audit.json'
promotion_pass=pa.exists() and read(pa)['status']=='passed'
now=datetime.now(timezone.utc).isoformat()
handoff={
 'at':now,'live_site':'https://cuiyist.github.io/mattersyn-site/','queue_url':'https://cuiyist.github.io/mattersyn-site/progress.html',
 'site_commit':v['pages_build']['commit'],'verified_project_commit':next(x['commit'] for x in v['repositories'] if x['repository']=='mattersyn'),
 'anonymous_progress_proof':str(proof),'anonymous_progress_proof_sha256':sha(proof),'unchanged_scientific_dataset':'0.31.0','published_canonical_records':626,
 'friedfeld':{'source':'main8 + matched SI25; independently passed','canonical_reader':'v3 independently passed; 30 records,750 measurements,51 source crops unchanged','molecular_chemistry_and_bindings':'passed','apparatus':'passed;58 scene instances,115 quantities','symbolic_product_contexts':'passed;88 mapped contexts,14 symbols; zero atomistic products','publication_projection_freeze':'1714710fcab2068a7b9dc13e0392ccb8dd708cc661961c324ef969c6fee34612','publication_projection_audit_passed':promotion_pass,'publication_projection_audit_sha256':sha(pa) if promotion_pass else None,'shared_site_imported':False,'browser_tested':False,'published':False},
 'sasongko':{'source':'main9 + matched SI11; independently passed after locator-only correction','source_audit_sha256':'c709225b9555ba89d3d952a6153561b011351c00fb2c62733c920447479edb58','canonical_reader_author':'/root/norberg2004_extract','canonical_proposal_in_progress':True,'published':False},
 'next_actions':[
  'Use the passed Friedfeld publication-projection audit (or obtain its final saved receipt); preserve every upstream freeze. Do not re-read unchanged source PDFs to change publication metadata.',
  'Run prepared import_reviewed_friedfeld.py only after its explicit pass and freeze gates. It verifies all metadata-edit anchors, uses extended Windows paths, snapshots626 existing record hashes andsix training exports, and leaves source science unchanged.',
  'Run build_and_check_site.py and independent integration-transport review. Candidate should add30records andfour route/variant records; derive actual hub/source counts from builders rather than assume them.',
  'Exercise actual integrated desktop/mobile readers, all operation dispatches, chemical/stock controls, source figure enlargement and product/sample contexts. No mounted-browser check is currently claimed.',
  'Publish completed contributions together through existing filtered GitHub copies; regenerate source citations from actually published canonical records. Verify exact Pages commit and anonymous asset bytes before any scientific-publication claim or paper closure.',
  'Resume Sasongko author checkpoint and then a distinct canonical/reader audit. Do not admit or download another source simply to fill a worker slot.',
  'Keep the existing five-minute heartbeat, fixed cutoff, evidence priority, separate arrival queue and no paid API run. Original papers/SI/full text/full-page renders remain local.'
 ]}
(F/'parallel-work-handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
text=f'''## 2026-09-20 — Parallel-review queue published and anonymously verified

Saved {now}. Live queue: https://cuiyist.github.io/mattersyn-site/progress.html . Progress-only Site commit **e986792d8b55727241d515ac25890f2ee679c1ab** is built and anonymously verified against the exact local bytes for the queue, progress page, scientific manifest and both reference files. Public project **c71dae065e92ae8b6a8c5e4a525dff84a1b0609d** was also verified; a subsequent project commit records this delivery proof and final audit receipts. Both repositories remain public; original papers/SI and document equivalents remain local. The previous progress proof is preserved as `progress-publication/anonymous-progress-verification-03a8d782.json`; prior full scientific verification is unchanged.

Scientific release remains **0.31.0, 626 records and 118 synthesis routes/variants**. This update publishes progress and research work, not an unfinished scientific contribution. Friedfeld's source, corrected canonical/reader, molecular, exact binding, apparatus and product-context audits all pass. Its 30-record, 162-asset publication projection is frozen; saved independent promotion pass at this checkpoint: **{promotion_pass}**. Shared Site import, actual browser checks and scientific release remain pending. Sasongko's complete main/SI source audit passes and canonical authoring is underway in parallel.

Resume `acs.inorgchem.8b02945/parallel-work-handoff.json` for exact next actions and hashes. The prepared root import/build helpers have not run. Use the immutable reviewed inputs and bounded metadata checks; keep earlier source conflicts, sample ambiguities and all training exclusions. The user-approved screen-first, separate per-paper independent audits, reusable reviewed illustrations and grouped-publication workflow is active. Memory, skills and audit history are in the public backup; no paid pilot or new paper download was started.

'''
p=M/'MEMORY.md';p.write_text(text+p.read_text(encoding='utf-8'),encoding='utf-8')
print(json.dumps({'memory_saved':True,'public_progress_verified':True,'promotion_audit_passed':promotion_pass,'science_dataset_unchanged':'0.31.0'}))
