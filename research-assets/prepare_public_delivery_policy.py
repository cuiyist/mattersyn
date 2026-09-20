"""Prepare the existing heartbeat update; actual automation change uses app tool."""
from pathlib import Path
import os,json,tomllib
root=Path(__file__).resolve().parent.parent
cfg=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))/'automations/mattersyn-sequential-paper-review/automation.toml'
data=tomllib.loads(cfg.read_text(encoding='utf8'))
prompt=data['prompt']
prompt=prompt.replace('Keep the full project backup in PRIVATE cuiyist/mattersyn, preserving code, memory, skills, structured extraction and audit history. Papers and SI remain local; only website assets enter the public repository.',
 'The latest September 20 user instruction makes cuiyist/mattersyn PUBLIC as well: publish code, memory, skills, structured extraction and audit history there, while cuiyist/mattersyn-site remains the public website. Original papers, SI, full-document text caches/page renderings, credentials and dependencies remain local; use the current audited publication filter for all history and future sync. Retain selected source figures and typed factual data with provenance. Keep unfinished scientific work explicitly labeled. Generate citations in both GitHub READMEs and REFERENCES.md from the actually published canonical sources, preserving each source review scope.')
prompt=prompt.replace('sync the private backup after meaningful reviewed releases.',
 'sync the public project after meaningful work milestones, including saved memory, skills, references and labeled work in progress. Use the current staging checkout documented in MEMORY.md; historical scripts that require private visibility are superseded.')
prompt=prompt.replace('regenerate build_queue_report.py after meaningful progress, and save memory/reusable skills.',
 'regenerate build_queue_report.py after meaningful progress, update the public-progress-editorial.json from verified current checkpoints, run build_public_progress.py, and publish the saved progress snapshot to https://cuiyist.github.io/mattersyn-site/progress.html. The homepage links to this dashboard, which checks for updates every minute. Publish progress and reference updates at meaningful milestones while keeping unreviewed scientific contributions out of the live dataset. Run research-assets/build_reference_readmes.py before website/project sync, and save memory/reusable skills. Do not claim instantaneous updates or active execution from a stale snapshot; include actual progress and scan timestamps.')
data['prompt']=prompt
out=root/'research-assets/public-delivery-automation-proposal.json';out.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data))
