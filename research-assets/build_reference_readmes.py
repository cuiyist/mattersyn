"""Generate repository citations from published canonical sources, not folder title matches."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re
ROOT=Path(__file__).resolve().parent.parent;SITE=ROOT/'recipe-atlas';DIST=SITE/'dist'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
records=[read(p) for p in sorted((SITE/'data/records').glob('*.json'))]
manifest=read(DIST/'data/dataset-manifest.json')
assert {r['record_id'] for r in records}=={r['record_id'] for r in manifest['records']}
reviews={r['paper_id']:r for r in [read(p) for p in (SITE/'data/paper-reviews').glob('*.json')]}
primary={};other={}
for r in records:
 for s in r['sources']:
  doi=(s.get('doi') or '').strip().lower();key=doi or s.get('url') or s['id']
  dest=primary if s['id']==r['lineage']['source_group'] else other
  entry=dest.setdefault(key,{'source':s,'records':[],'source_groups':set()})
  entry['records'].append(r['record_id']);entry['source_groups'].add(r['lineage']['source_group'])
for k in primary:other.pop(k,None)
def plain(v):return str(v or '').replace('\n',' ').replace('|','\\|')
def citation(entry):
 s=entry['source'];review=reviews.get(s['id'],{});paper=review.get('paper',{})
 authors=paper.get('authors') or s.get('authors') or 'Authors not recorded in the current source metadata'
 if isinstance(authors,list):authors='; '.join(authors)
 parts=[plain(authors),f"({s.get('year') or paper.get('year') or 'year unrecorded'}).",plain(s.get('title')).rstrip('.')+'.']
 if paper.get('journal'):parts.append('*'+plain(paper['journal'])+'*'+(', '+plain(paper['volume']) if paper.get('volume') else '')+(', '+plain(paper['pages']) if paper.get('pages') else '')+'.')
 doi=s.get('doi');url='https://doi.org/'+doi if doi else s.get('url')
 if url:parts.append('['+plain(doi or 'Source link')+']('+url+').')
 if review:
  scope={'supplied_main_and_matched_si':'Supplied main paper and matched SI reviewed','supplied_main_si_unverified':'Main paper reviewed; SI unverified','supplied_main_only_si_unverified':'Main paper reviewed; SI unverified'}.get(review.get('review_scope'),plain(review.get('review_scope','Source-specific reviewed scope')).replace('_',' '))
  parts.append('['+scope+'](https://cuiyist.github.io/mattersyn-site/paper-review.html?id='+s['id']+').')
 else:parts.append('Review scope is stated in the linked website records; this citation does not imply full main/SI review.')
 return ' '.join(parts)
lines=['## Papers used in the published website','',
 f"Generated from dataset **{manifest['dataset_version']}**, containing **{len(primary)} primary source groups**. The reference list follows published records, not all indexed documents. A paper can contribute several records; records are not independent experiments.",'']
for entry in sorted(primary.values(),key=lambda e:(e['source'].get('year') or 0,e['source'].get('title',''))):lines.append('- '+citation(entry));lines.append('')
if other:
 lines+=['## Additional sources cited by the published records','',
 'These sources supply contextual, upstream or comparative information. Inspection and reuse scope remain attached to the corresponding record; inclusion here does not claim that every cited preparation was recovered.','']
 for entry in sorted(other.values(),key=lambda e:(e['source'].get('year') or 0,e['source'].get('title',''))):lines+=['- '+citation(entry),'']
lines+=['Molecular and crystal reference databases and original-figure provenance are also credited beside the corresponding website assets. A bibliography entry does not grant additional rights to third-party figures or data.','']
refs='\n'.join(lines)
for p in [ROOT/'REFERENCES.md',DIST/'REFERENCES.md']:p.write_text('# MatterSyn references\n\n'+refs,encoding='utf8')
intro='''# MatterSyn

[Open the materials atlas](https://cuiyist.github.io/mattersyn-site/) · [Review progress and queue](https://cuiyist.github.io/mattersyn-site/progress.html) · [Synthesis dataset](https://cuiyist.github.io/mattersyn-site/dataset.html)

MatterSyn organizes source-linked materials synthesis recipes, characterization and properties for readers and future machine-learning datasets. Published pages distinguish reported measurements, author interpretations, external reference structures and illustrative models.

This public project repository contains code, structured data, memory, reusable skills and audit history. Work in progress is explicitly labeled; publication in this repository is not scientific approval. Original papers and SI, full-document caches, credentials and installed dependencies remain local. Historical source-file hashes and paths remain provenance references even where their original documents are excluded.

- `recipe-atlas/`: website, canonical dataset and validation code.
- `research-assets/`: structured extraction, independent audits and progress checkpoints.
- `skills/`: reusable curation and publishing workflow.
- `MEMORY.md`: project decisions, progress and unresolved work.

The website is published from the separate [mattersyn-site repository](https://github.com/cuiyist/mattersyn-site). Saved progress, references, memory and skills are synchronized at meaningful work milestones; reviewed scientific additions are published after their required checks. Earlier website commits are retained as history. Original-document equivalents are excluded from public history, with the unfiltered local project preserved.

'''
(ROOT/'README.md').write_text(intro+refs,encoding='utf8')
site_intro='''# MatterSyn website

[Open MatterSyn](https://cuiyist.github.io/mattersyn-site/) · [Review progress](https://cuiyist.github.io/mattersyn-site/progress.html) · [Public project, memory, skills and audit history](https://github.com/cuiyist/mattersyn)

This repository contains the published static materials atlas and machine-readable data. The separate public project repository contains development work and review history. Original papers and SI remain local. Progress snapshots update as review milestones are completed; scientific additions retain their individual audit and source-scope requirements.

'''
(DIST/'README.md').write_text(site_intro+refs,encoding='utf8')
report={'created_at':datetime.now(timezone.utc).isoformat(),'dataset_version':manifest['dataset_version'],
 'primary_sources':len(primary),'additional_record_sources':len(other),'canonical_records':len(records),
 'source_manifest_sha256':hashlib.sha256((DIST/'data/dataset-manifest.json').read_bytes()).hexdigest(),
 'in_progress_sources_added':False,'source_readme':'README.md','site_readme':'recipe-atlas/dist/README.md'}
(ROOT/'research-assets/reference-readme-generation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

# Independent structure sources do not increase the reviewed synthesis-paper count.
registry=read(DIST/'assets/crystal-references/registry.json')
modelrefs=['\n## Crystal reference models\n','Reference models support the Reader and are excluded from measured synthesis labels. Full unit-cell provenance, limitations and licenses are in the [reference registry](https://cuiyist.github.io/mattersyn-site/assets/crystal-references/registry.json).\n']
seen=set()
for item in registry['entries']:
 if not item.get('record_ids') or item['sourceUrl'] in seen:continue
 seen.add(item['sourceUrl']);modelrefs.append('- ['+item['name']+']('+item['sourceUrl']+'). '+item.get('sourceType','Qualified existing reference').replace('_',' ')+'.\n')
for name in ['README.md','REFERENCES.md']:
 for folder in [ROOT,DIST]:
  target=folder/name
  target.write_text(target.read_text(encoding='utf8').split('\n## Crystal reference models\n')[0]+'\n'.join(modelrefs),encoding='utf8')
