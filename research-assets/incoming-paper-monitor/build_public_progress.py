"""Publish-safe progress projection: explicit fields only, never raw private ledgers."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re
from html import escape
ROOT=Path(__file__).resolve().parent;SITE=ROOT.parent.parent/'recipe-atlas';DIST=SITE/'dist'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
queue=read(ROOT/'queue-status.json');counts=queue['counts'];release=read(ROOT/'latest-publication.json')
editorial=read(ROOT/'public-progress-editorial.json')
manifest=read(DIST/'data/dataset-manifest.json')
assert manifest['dataset_version']==release['dataset_version'] and manifest['record_count']==release['record_count'], 'Only verified live scientific counts may enter the progress page.'
out={'schema_version':'1.0.0','updated_at':datetime.now(timezone.utc).isoformat(),
 'corpus_scanned_at':queue['ledger_last_scan_at'],
 'published':{k:release[k] for k in ['dataset_version','record_count','synthesis_route_count','material_hub_count','direct_material_hub_count','component_material_hub_count','public_source_group_count','formal_source_reader_count','exact_structure_recipe_count','published_at']},
 'corpus':{k:counts[k] for k in ['present_files','source_document_copies','canonical_review_units','waiting_review_scopes','active_review_claims','confirmed_duplicate_main_aliases']},
 'count_note':'Document copies include main papers, supplements and duplicates. Provisional review scopes are not a verified count of unique papers, synthesis recipes or materials.',
 'priority':'Synthesis and crystal-structure evidence richness; existing batch retained.',
 'update_policy':'Progress is published at meaningful review milestones. This page checks for a newer published snapshot every minute. Scientific records are released after their required audits and website checks.',
 'batch':editorial['batch'],'current_work':editorial['current_work'],'recent_milestones':editorial['recent_milestones'],
 'workflow':editorial.get('workflow'),
 'estimate':editorial.get('estimate',{'status':'being_recalibrated','summary':'Whole-corpus finish time is being recalibrated from completed reviews; incoming documents are counted separately.'})}
text=json.dumps(out,ensure_ascii=False,indent=2)+'\n'
assert not re.search(r'[A-Za-z]:[[local path redacted] 'Private path or credential-like token in public projection.'
(DIST/'data/review-progress.json').write_text(text,encoding='utf8')
for name in ('index.html','library.html','dataset.html','inventory.html','progress.html'):
 p=DIST/name
 if not p.exists():continue
 s=p.read_text(encoding='utf8')
 if 'href="progress.html"' not in s:s=s.replace('</nav>','<a href="progress.html">Review progress</a></nav>',1)
 if name=='index.html':
  s=re.sub(r'<!--review-progress-start-->.*?<!--review-progress-end-->','',s,flags=re.S)
  current=editorial['current_work']
  state='Active papers are published. Work is paused for joint review; no new papers will start.' if editorial.get('estimate',{}).get('status')=='paused_for_joint_review' else current[0]['short_label']+': '+current[0]['stage']+'.' if current else 'No paper is currently under review.'
  state=escape(state)
  widget='<!--review-progress-start--><section class="progress-teaser" aria-label="Current review progress"><div><span class="eyebrow">REVIEW PROGRESS</span><p id="review-progress-brief">'+state+'</p><small id="review-progress-time">Progress is saved at review milestones.</small></div><a href="progress.html">Open the review queue →</a></section><!--review-progress-end-->'
  s=s.replace('<div class="element-controls">',widget+'<div class="element-controls">',1)
  if 'progress.css' not in s:s=s.replace('</head>','<link rel="stylesheet" href="progress.css?v=1"></head>')
  if 'progress.mjs' not in s:s=s.replace('</body>','<script type="module" src="progress.mjs?v=1"></script></body>')
 s=re.sub(r'src="progress\.mjs\?v=[^"]+"','src="progress.mjs?v=0.34.1-resume"',s)
 p.write_text(s,encoding='utf8')
print(json.dumps({'output':'data/review-progress.json','sha256':hashlib.sha256((DIST/'data/review-progress.json').read_bytes()).hexdigest(),'waiting_scopes':counts['waiting_review_scopes'],'published_records':release['record_count'],'private_paths_exported':False}))
