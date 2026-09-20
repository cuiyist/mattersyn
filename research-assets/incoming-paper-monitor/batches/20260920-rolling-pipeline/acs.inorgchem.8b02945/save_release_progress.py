"""Root checkpoint for the current rolling parallel review, without completion claims."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,subprocess
F=Path(__file__).resolve().parent;J=F.parent/'acs.jpcc.5c05144';MON=F.parents[2];M=F.parents[4]
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
sys.path.insert(0,str(MON));import monitor
audit=J/'canonical-independent-audit/independent-audit-v1.json';assert read(audit)['status']=='passed'
freeze=J/'canonical-proposal/v1/package-freeze.json'
monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='legacy::10.1021_acs.jpcc.5c05144',note='Distinct source and canonical/reader audits passed. Scientific illustrations are now in preparation outside Site.',data={'current_step':'Scientific illustrations and exact material bindings in preparation','canonical_freeze_sha256':sha(freeze),'canonical_audit_sha256':sha(audit),'source_status':'Complete supplied main9+SI11 read and independently audited; canonical and reader also passed.','publication_status':'not published'},milestones={'audit':{'status':'partial','evidence':[str(audit),str(J/'source-independent-audit/independent-audit-v2.json')],'note':'Source and canonical/reader reviews passed. Separate illustrations, browser and publication gates remain open.'}})
ed=read(MON/'public-progress-editorial.json')
for item in ed['current_work']:
 if item['short_label']=='Friedfeld et al. (2019)':
  item['stage']='Browser checks passed; preparing the public release'
  item['stages'][3]={'label':'Website integration, browser checks and publication','status':'in_progress','detail':'All58stage controls, molecular and sample-context interactions, and desktop/mobile layouts checked. Exact anonymous delivery remains pending.'}
 if item['short_label']=='Sasongko et al. (2025)':
  item['stage']='Source and structured-data audits passed; illustrations in preparation'
  item['summary']='All20supplied main/SI pages reviewed.19records,21operations,nine explicitly paired condition options,273reader items and17source crops passed independent source and canonical audits. Source crystal references remain separate from measured QD coordinates.'
  item['stages'][2]={'label':'Structured records and scientific illustrations','status':'in_progress','detail':'19records and complete reader passed; chemical/stock illustrations and their separate audit remain pending.'}
save(MON/'public-progress-editorial.json',ed)
subprocess.run([sys.executable,str(MON/'build_queue_report.py')],check=True)
# The public-progress generator intentionally rejects candidate counts until
# anonymous science delivery is verified. Preserve its last live snapshot.
manifest=read(M/'recipe-atlas/dist/data/dataset-manifest.json');release=read(MON/'latest-publication.json')
if manifest['dataset_version']==release['dataset_version']:
 subprocess.run([sys.executable,str(MON/'build_public_progress.py')],check=True)
note=f'''## 2026-09-20 — Parallel review checkpoint before Friedfeld delivery

Saved {datetime.now(timezone.utc).isoformat()}. Friedfeld candidate0.32.0 has passed source, canonical, molecular, binding, apparatus, product, integration and actual browser checks. All58scenes across19procedure records selected; shared InP hub retains Tessier plusfour new conversion methods. Desktop1280 and mobile390 checked; a scoped context-label spacing correction eliminated mobile overflow. Publication is still pending its exact deployment proof. Prior626record bytes andsixtrainingexports unchanged.

Sasongko canonical/reader v1 SHA{sha(freeze)} and distinct canonical audit SHA{sha(audit)} passed.19records,21operations,ninepaired comparisons,502measurements,273reader items/1197typedfields,127table quantity positions,33named contexts and17crops preserved. Peng's original extraction-author role is disclosed in the canonical audit; Backlog independently audited the source. Molecular and stock visual proposal is underway in J/visuals/molecules outside Site; visuals/browser/publication remain pending. Resume these exact packages, not another full re-extraction. The paid pilot remains deferred. Public memory/skills/audits/reference lists update at review milestones; original PDFs/SI/fulltext/fullpages stay local.

'''
p=M/'MEMORY.md';p.write_text(note+p.read_text('utf8'),'utf8')
print('Saved current parallel review and unpublished release progress.')
