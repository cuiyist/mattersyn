"""Generate both bibliographies and progress HTML/JSON from one fixed snapshot."""
from pathlib import Path
import json,html,re,hashlib
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def dump(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def progress_label(data):
    if data.get('estimate',{}).get('status')=='paused_for_joint_review':return 'Active papers are published. Work is paused for joint review; no new papers will start.'
    rows=data.get('current_work',[])
    return (rows[0]['short_label']+': '+rows[0]['stage']).rstrip('.')+'.'if rows else'No paper is currently under review.'
def render_banner(text,progress):
    label=html.escape(progress_label(progress));timestamp=html.escape(progress['updated_at'])
    widget='<!--review-progress-start--><section class="progress-teaser" aria-label="Current review progress"><div><span class="eyebrow">REVIEW PROGRESS</span><p id="review-progress-brief">'+label+'</p><small id="review-progress-time">Published snapshot '+timestamp+' · automatic update checks require JavaScript.</small></div><a href="progress.html">Open the review queue →</a></section><!--review-progress-end-->'
    pattern=r'<!--review-progress-start-->.*?<!--review-progress-end-->'
    if re.search(pattern,text,re.S):return re.sub(pattern,lambda _:widget,text,flags=re.S)
    if '<div class="element-controls">'not in text:raise ValueError('Home progress insertion anchor missing')
    return text.replace('<div class="element-controls">',widget+'<div class="element-controls">',1)
def citation(s,review):
    paper=review.get('paper',{});authors=paper.get('authors')or s.get('authors')or'Authors unrecorded'
    if isinstance(authors,list):authors='; '.join(authors)
    line=f"{authors} ({s.get('year')or paper.get('year')or'year unrecorded'}). {s['title'].rstrip('.')}."
    if paper.get('journal'):line+=' *'+paper['journal']+'*'+(', '+str(paper['volume'])if paper.get('volume')else'')+(', '+str(paper['pages'])if paper.get('pages')else'')+'.'
    if s.get('doi'):line+=' ['+s['doi']+'](https://doi.org/'+s['doi']+').'
    elif s.get('url'):line+=' [Source]('+s['url']+').'
    if review:line+=' [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id='+s['id']+').'
    else:line+=' Review scope remains stated in the linked website records.'
    return line.replace('\n',' ')
def readme_with_references(existing,introduction,body):
    start='<!-- mattersyn-generated-references:start -->';end='<!-- mattersyn-generated-references:end -->'
    block=start+'\n'+body+'\n'+end
    if start in existing or end in existing:
        if existing.count(start)!=1 or existing.count(end)!=1:raise ValueError('README reference markers must occur exactly once')
        return re.sub(re.escape(start)+r'.*?'+re.escape(end),lambda _:block,existing,flags=re.S)
    return (existing.rstrip()or introduction.rstrip())+'\n\n'+block+'\n'

def generate(root,snapshot):
    dist=root/'dist';records=[load(p)for p in sorted((root/'data/records').glob('*.json'))];manifest=load(dist/'data/dataset-manifest.json')
    if {r['record_id']for r in records}!={r['record_id']for r in manifest['records']}:raise ValueError('Release record/manifest membership differs')
    if len(records)!=snapshot['record_count']:raise ValueError('Release record count differs from approved snapshot')
    reviews={r['paper_id']:r for r in (load(p)for p in (root/'data/paper-reviews').glob('*.json'))};primary={};other={}
    for r in records:
        for s in r['sources']:
            key=(s.get('doi')or s.get('url')or s['id']).lower();(primary if s['id']==r['lineage']['source_group']else other).setdefault(key,s)
    for key in primary:other.pop(key,None)
    refs=['## Papers used in the published website','',f"Dataset **{manifest['dataset_version']}** · **{len(primary)} primary source groups** · release `{snapshot['release_id']}`. Records are not independent experiments.",'']
    for s in sorted(primary.values(),key=lambda s:(s.get('year')or 0,s['title'])):refs+=['- '+citation(s,reviews.get(s['id'],{})),'']
    if other:
        refs+=['## Additional contextual sources','','These are contextual/upstream references, not extra reviewed synthesis contributions.','']
        for s in sorted(other.values(),key=lambda s:(s.get('year')or 0,s['title'])):refs+=['- '+citation(s,reviews.get(s['id'],{})),'']
    registry=load(dist/'assets/crystal-references/registry.json')if (dist/'assets/crystal-references/registry.json').exists()else{'entries':[]};seen=set()
    refs+=['## Crystal reference models','','Reference structures are distinguished from sample-resolved synthesis targets. Provenance and qualifications remain in the website registry.','']
    for entry in registry['entries']:
        if not entry.get('record_ids')or entry.get('sourceUrl')in seen:continue
        seen.add(entry['sourceUrl']);refs+=['- ['+entry['name']+']('+entry['sourceUrl']+'). '+entry.get('sourceType','Qualified reference').replace('_',' ')+'.','']
    refs+=['A citation does not grant reuse rights to third-party figures or source text. The separate release boundary gate controls public delivery.',''];body='\n'.join(refs)
    for folder in [root.parent,dist]:
        (folder/'REFERENCES.md').write_text('# MatterSyn references\n\n'+body,encoding='utf-8',newline='\n')
        readme=folder/'README.md';intro=('# MatterSyn website'if folder==dist else'# MatterSyn')+'\n\n[Open the atlas](https://cuiyist.github.io/mattersyn-site/) · [Review progress](https://cuiyist.github.io/mattersyn-site/progress.html)\n\nMatterSyn organizes source-attributed synthesis, characterization and property records. Publication and task-specific training eligibility are separate approvals.\n'
        readme.write_text(readme_with_references(readme.read_text(encoding='utf-8')if readme.exists()else'',intro,body),encoding='utf-8',newline='\n')
    progress=load(root/'data/release-progress.json');progress['updated_at']=snapshot['updated_at'];dump(dist/'data/review-progress.json',progress)
    home=dist/'index.html';home.write_text(render_banner(home.read_text(encoding='utf-8'),progress),encoding='utf-8',newline='\n')
    binding={'schema':'mattersyn-generated-release-metadata/1','release_id':snapshot['release_id'],'updated_at':snapshot['updated_at'],'source_commit':snapshot['source_commit'],'canonical_records':len(records),'primary_sources':len(primary),'manifest_sha256':hashlib.sha256((dist/'data/dataset-manifest.json').read_bytes()).hexdigest(),'progress_sha256':hashlib.sha256((dist/'data/review-progress.json').read_bytes()).hexdigest(),'bibliography_sha256':hashlib.sha256(body.encode()).hexdigest()}
    dump(dist/'data/release-snapshot.json',binding);return binding
