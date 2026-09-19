"""Validate canonical records, generate record pages and gated training exports."""
import argparse,json,html,sys,shutil
from pathlib import Path
from collections import Counter
from dataset_lib import ROOT,SCHEMA,validate_record,eligibility,build_groups,training_view,digest,chemical_signature,fmt
from review_scope import source_review_scope

DISPLAY=json.loads((ROOT/'data/measurement-display.json').read_text(encoding='utf-8'))
PROTOCOL_TYPES={'literature_protocol','protocol_variant','experiment'}
def is_structural(m):return m['property'] in DISPLAY['structural_properties'] or any(part in m['property'] for part in DISPLAY['structural_property_fragments'])

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def esc(x):return html.escape(str(x),quote=True)
def human(x):return x.replace('_',' ').replace('.',' · ')
def evidence(items):return '; '.join(esc(x['source_id']+' · '+x['locator']) for x in items)
def quantities(qs):
    return ''.join('<div class="quantity"><dt>'+esc(human(k))+'</dt><dd>'+esc(fmt(q))+'<small>'+esc(q['status'].replace('_',' '))+(' · '+esc(q['basis']) if q['basis'] else '')+'</small></dd></div>' for k,q in qs.items()) or '<p class="muted">No separate quantity entered here; consult stocks, operations and source notes below.</p>'
def fact_text(f):return (str(f['value']) if f['value'] is not None else f['status'].replace('_',' ').capitalize())+(' · '+f['note'] if f.get('note') else '')
def head(title,prefix=''):
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+' · MatterSyn</title><link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 40 40%27%3E%3Crect width=%2740%27 height=%2740%27 rx=%279%27 fill=%27%23295888%27/%3E%3Ctext x=%2720%27 y=%2728%27 text-anchor=%27middle%27 fill=%27white%27 font-family=%27sans-serif%27 font-size=%2726%27%3EM%3C/text%3E%3C/svg%3E"><link rel="stylesheet" href="'+prefix+'styles.css"><link rel="stylesheet" href="'+prefix+'academic.css"><link rel="stylesheet" href="'+prefix+'dataset.css"><link rel="stylesheet" href="'+prefix+'apparatus.css"><link rel="stylesheet" href="'+prefix+'illustrated-guide.css?v=0.9.0-r1"></head>'
def header(prefix=''):
    return '<header class="site-header dataset-header"><a class="brand" href="'+prefix+'index.html"><span class="brand-mark">M</span>MatterSyn</a><nav aria-label="Dataset navigation"><a href="'+prefix+'index.html">Periodic table</a><a href="'+prefix+'library.html">Source library</a><a href="'+prefix+'dataset.html">Synthesis dataset</a></nav></header>'
def section(id,number,title,subtitle,body):return '<section id="'+id+'" class="record-section"><div class="section-heading"><div><span class="section-number">'+number+'</span><h2>'+title+'<small>'+subtitle+'</small></h2></div></div>'+body+'</section>'

def render_record(r,meta):
    rid=r['record_id'];src=r['sources'][0];e=meta['eligibility'];p='../'
    s=head(r['title'],p)+'<body data-record-id="'+rid+'">'+header(p)+'<main class="dataset-main record-main"><p class="academic-breadcrumb"><a href="../dataset.html">Synthesis records</a> / '+esc(r['material']['formula'])+' / '+esc(r['method'])+'</p><div class="dataset-heading"><div class="method-label">'+esc(r['method'].upper())+' · '+esc(r['material']['formula'])+'</div><h1>'+esc(r['title'])+'</h1><p>'+esc(src['title'])+'</p><p class="record-citation">'+esc(src['authors'])+' · '+str(src['year'])+' · <a href="'+esc(src['url'])+'" target="_blank" rel="noopener">'+esc(src['doi'])+' ↗</a></p></div>'
    s+='<div class="record-identity"><div><span>Record</span><strong>'+rid+'</strong></div><div><span>Evidence type</span><strong>'+esc(human(r['record_type']))+'</strong></div><div><span>Review</span><strong>'+esc(human(r['quality']['review_status']))+'</strong></div><a class="data-download" href="../data/records/'+rid+'.json" download>Download record JSON ↓</a></div><p class="source-scope">'+esc(r['quality']['review_scope'])+'</p>'
    s+='<nav class="record-sections" aria-label="Record sections"><a href="#precursors">Precursors</a><a href="#protocol">Synthesis protocol</a><a href="#structures">Final structures</a><a href="#properties">Properties</a><a href="#intuition">Chemical intuition</a><a href="#evidence">Evidence & training</a></nav>'
    material_cards=[]
    for m in r['materials']:
        material_cards.append('<article class="reagent-record"><div class="record-meta"><span>'+esc(human(m['role']))+'</span><span>'+esc(human(m['stage']))+'</span></div><h3>'+esc(m['name'])+'</h3><p class="chemical-formula">'+esc(m['formula'] or 'Mixture / formula unresolved')+'</p><dl>'+quantities(m['quantities'])+'</dl><button class="molecule-link" data-material-id="'+esc(m['id'])+'" data-molecule-name="'+esc(m['name'])+'" data-molecule-formula="'+esc(m['formula'] or '')+'" type="button">Molecular identity & structure ↗</button>'+(''.join('<p class="record-note">'+esc(n)+'</p>' for n in m['notes']))+'<small class="evidence-label">'+evidence(m['evidence'])+'</small></article>')
    body='<div class="reagent-grid">'+''.join(material_cards)+'</div>'
    if r['stocks']:
        body+='<h3 class="inventory-heading">Stocks and solutions</h3><div class="stock-records">'
        names={m['id']:m['name'] for m in r['materials']}
        for stock in r['stocks']:
            body+='<article class="stock-record"><h4>'+esc(stock['name'])+'</h4><p>'+esc(stock['scope'])+'</p>'
            for c in stock['components']:body+='<h5>'+esc(names[c['material_id']])+'</h5><dl>'+quantities(c['quantities'])+'</dl>'
            body+='<dl>'+quantities(stock['concentrations'])+'</dl><small class="evidence-label">'+evidence(stock['evidence'])+'</small></article>'
        body+='</div>'
    s+=section('precursors','01','Precursors','Chemical identities, quantities and separately defined stocks',body)
    body=''
    if r['condition_options']:
        body+='<div class="record-notice"><strong>Reported condition sets</strong><p>Each set retains its source-defined scope: an alternative, observation window, trajectory point or scale-up claim. Read its label before interpreting it; these entries do not establish independent batches.</p></div><div class="condition-options">'+''.join('<article><h3>'+esc(x['label'])+'</h3><dl>'+quantities(x['parameters'])+'</dl></article>' for x in r['condition_options'])+'</div>'
    body+='<div class="operation-list">'
    for i,o in enumerate(r['operations']):
        body+='<article class="operation-card"><div class="operation-index">'+str(i+1).zfill(2)+'</div><div class="operation-body"><span class="mini-label">'+esc(human(o['stage']))+(' · OPTIONAL BRANCH' if o['optional'] else '')+'</span><h3>'+esc(o['label'])+'</h3><p>'+esc(o['description'])+'</p><dl class="operation-parameters">'+quantities(o['parameters'])+'</dl><div class="operation-context"><span><strong>Environment:</strong> '+esc(fact_text(o['environment']))+'</span><span><strong>Endpoint:</strong> '+esc(fact_text(o['endpoint']))+'</span>'+('<span><strong>Retain:</strong> '+esc(o['retained_fraction'])+'</span>' if o['retained_fraction'] else '')+'</div><details class="material-flow"><summary>Material flow & source</summary><p>Inputs: '+esc(', '.join(o['inputs']) or 'Inputs not specified in this source')+(' (optional: '+esc(', '.join(o.get('optional_inputs',[])))+')' if o.get('optional_inputs') else '')+'</p><p>Outputs: '+esc(', '.join(o['outputs']))+'</p><p>Depends on: '+esc(', '.join(o['depends_on']) or 'Independent preparation / input state')+'</p><small>'+evidence(o['evidence'])+'</small></details></div></article>'
    body+='</div>'
    if r['collection']=='reviewed_literature':body='<div id="record-protocol-visual"></div>'+body
    s+=section('protocol','02','Synthesis protocol','Ordered operations, material dependencies and stage-specific conditions',body)
    body='<p class="source-scope">Product IDs identify source observations. Physical batch identity is unknown unless the authors explicitly provide it.</p><div class="product-records">'
    for prod in r['products']:
        body+='<article class="product-record"><span class="record-badge">Recipe link: '+esc(prod['recipe_link'].replace('_',' '))+'</span><h3>'+esc(prod['source_sample_label'] or prod['sample_id'])+'</h3><dl class="fact-list">'+''.join('<div><dt>'+k.capitalize()+'</dt><dd>'+esc(fact_text(prod[k]))+'</dd></div>' for k in ['composition','phase','morphology','surface'])+'</dl>'+''.join('<p>'+esc(n)+'</p>' for n in prod['notes'])+'</article>'
    body+='</div>'
    structural=[m for m in r['measurements'] if is_structural(m)]
    body+=measurement_table(structural)
    if r['structure_assets']:
        body+='<h3 class="inventory-heading">Structure references</h3><div class="structure-downloads">'+''.join('<a href="'+esc(x['url'])+'"><strong>'+esc(human(x['role']))+' ↗</strong><span>'+esc(x['description'])+'</span></a>' for x in r['structure_assets'])+'</div>'
    else:body+='<p class="record-note">No sample-resolved atomic coordinates are supplied for this record. A reported phase or size does not establish an exact product CIF.</p>'
    body+='<div id="record-crystal-references"></div>'
    s+=section('structures','03','Final structures','Source-linked product identity, phase and size measurements',body)
    other_measurements=[m for m in r['measurements'] if not is_structural(m)]
    s+=section('properties','04','Properties','Measurements retain their sample, technique and source',measurement_table(other_measurements))
    if r['collection']=='reviewed_literature':s+='<section id="original-characterization" class="record-section"><h2>Original characterization and property figures</h2><div id="record-original-evidence"></div></section>'
    links=[dict(l,url=('../'+l['url'] if l['url'].startswith('paper-review.html') else l['url'])) for l in r['context_links']]
    review=ROOT/'data/paper-reviews'/(r['lineage']['source_group']+'.json')
    if review.exists() and not any('paper-review.html' in l['url'] for l in links):links.append({'url':'../paper-review.html?id='+r['lineage']['source_group'],'label':source_review_scope(json.loads(review.read_text(encoding='utf-8')))['label']+' and original figures','relation':'source coverage'})
    body='<div id="record-intuition-content"></div><p>Mechanistic interpretations and related literature remain separate from the experimental training labels.</p>'+(''.join('<a class="context-reference" href="'+esc(l['url'])+'"><strong>'+esc(l['label'])+' ↗</strong><span>'+esc(l['relation'])+'</span></a>' for l in links) if links else '<p class="record-note">No separately reviewed chemical-intuition essay is attached to this record yet.</p>')
    s+=section('intuition','05','Chemical intuition','Referenced context and interpretation',body)
    body='<div class="eligibility-grid">'+''.join('<article><strong>'+esc(human(task))+'</strong><span class="record-badge '+('eligible' if v['eligible'] else '')+'">'+('Included' if v['eligible'] else 'Excluded')+'</span><p>'+esc(v['reason'])+'</p></article>' for task,v in e.items())+'</div><h3>Unresolved information</h3><ul class="gap-list">'+''.join('<li>'+esc(x)+'</li>' for x in r['quality']['missing_fields'])+'</ul>'
    if r['quality']['conflicts']:body+='<h3>Source distinctions and conflicts</h3><ul class="gap-list">'+''.join('<li>'+esc(x)+'</li>' for x in r['quality']['conflicts'])+'</ul>'
    body+='<details class="record-audit"><summary>Provenance and record integrity</summary><p>Revision '+str(r['revision'])+' · Schema '+r['schema_version']+'</p><p>Evaluation group: '+meta['group_id']+' · '+meta['split']+'</p><p>Record SHA-256: <code>'+meta['record_sha256']+'</code></p><p>All records in the same source, recipe, parent/batch or duplicate group stay together in data splits.</p>'+''.join('<p><a href="'+esc(x['url'])+'">'+esc(x['title'])+'</a><br>Main: '+esc(x['main_status'])+'<br>SI: '+esc(x['si_status'])+'</p>' for x in r['sources'])+'</details>'
    s+=section('evidence','06','Evidence and training','Task eligibility follows source review and sample linkage',body)
    s+='</main><dialog id="record-molecule-dialog" class="record-dialog"><div class="dialog-header"><h2 id="record-molecule-title">Molecular identity</h2><button id="record-molecule-close" type="button">Close ×</button></div><div id="record-molecule-view" class="record-molecule-view"></div><p id="record-molecule-note"></p><a id="record-molecule-source" target="_blank" rel="noopener">Reference ↗</a></dialog><script src="../vendor/3Dmol-min.js"></script><script type="module" src="../illustrated-record.mjs?v=0.9.0-r1"></script></body></html>'
    return s

def measurement_table(ms):
    if not ms:return '<p class="record-note">No measurements in this category are assigned to the specific record. Contextual figures are not automatically used as product labels.</p>'
    s='<div class="table-scroll"><table class="reagent-table measurement-table"><thead><tr><th>Property</th><th>Value</th><th>Technique / conditions</th><th>Sample & source</th></tr></thead><tbody>'
    for m in ms:s+='<tr><td>'+esc(human(m['property']))+'</td><td>'+esc(fmt(m['value']))+'<small>'+esc(human(m['value']['status']))+'</small></td><td>'+esc(m['technique'])+'<small>'+esc(m['conditions'])+'</small></td><td>'+esc(m['sample_id'])+'<small>'+evidence(m['evidence'])+'</small></td></tr>'
    return s+'</tbody></table></div>'

def catalog_html(report,manifest):
    from catalog_view import render
    return render(report,manifest,head,header,esc,human)


def main():
    records=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT/'data/records').glob('*.json'))]
    errors=[e for r in records for e in validate_record(r)];ids=[r['record_id'] for r in records]
    if len(set(ids))!=len(ids):errors.append('Duplicate record IDs')
    for r in records:
        for k in ['parent_record_id','duplicate_of']:
            v=r['lineage'][k]
            if v and v not in ids:errors.append(r['record_id']+' unresolved '+k)
    if errors:print('\n'.join(errors),file=sys.stderr);return 1
    groups=build_groups(records);unique_groups=sorted(set(groups.values()));assign={g:('development' if len(unique_groups)<10 else 'test' if int(digest(g)[:8],16)%10==0 else 'validation' if int(digest(g)[:8],16)%10==1 else 'train') for g in unique_groups}
    public=ROOT/'dist/data';pages=ROOT/'dist/records';pages.mkdir(parents=True,exist_ok=True)
    tasks=['precursor_selection','partial_protocol','size_conditioned_recipe','exact_structure_recipe','success_prediction','optical_outcome'];exports={k:[] for k in tasks};items=[]
    for r in records:
        rid=r['record_id'];ee=eligibility(r);meta={'record_id':rid,'title':r['title'],'formula':r['material']['formula'],'family':r['material']['family'],'method':r['method'],'record_type':r['record_type'],'source_year':r['sources'][0]['year'],'source_doi':r['sources'][0]['doi'],'revision':r['revision'],'record_sha256':digest(r),'recipe_signature':chemical_signature(r),'group_id':groups[rid],'split':assign[groups[rid]],'eligibility':ee,'record_url':'data/records/'+rid+'.json','page_url':'records/'+rid+'.html','missing_field_count':len(r['quality']['missing_fields'])};items.append(meta)
        meta['collection']=r.get('collection','reviewed_literature')
        meta['components']=r['material'].get('components',[r['material']['formula']])
        dump(public/'records'/(rid+'.json'),r)
        (pages/(rid+'.html')).write_text(render_record(r,meta),encoding='utf-8')
        for task in tasks:
            if ee[task]['eligible']:
                x=training_view(r,task);x['group_id']=meta['group_id'];x['split']=meta['split'];x['record_sha256']=meta['record_sha256'];exports[task].append(x)
    # Fail closed: stale public records must not survive removing a canonical record.
    expected={r['record_id'] for r in records}
    stale=[str(p) for folder in [public/'records',pages] for p in folder.glob('*') if p.is_file() and p.stem not in expected]
    if stale:raise ValueError('Review and remove obsolete generated record files explicitly: '+', '.join(stale))
    families=sorted({r['material']['family'] for r in records if r['record_type']!='procedure'})
    manifest={'schema_version':'1.0.0','dataset_version':'0.9.0','record_count':len(records),'group_count':len(unique_groups),'families':families,'split_policy':'Connected source/recipe/parent/batch/duplicate components. Development-only below ten groups. Split thresholds are deterministic group hash 80/10/10, not a claim of balanced class coverage.','records':items}
    report={'status':'passed','dataset_version':'0.9.0','records':len(records),'recipe_records':sum(r['record_type']!='procedure' for r in records),'shared_procedures':sum(r['record_type']=='procedure' for r in records),'independent_experiment_count':None,'source_groups':len(unique_groups),'families':len(families),'eligible_by_task':{k:len(v) for k,v in exports.items()},'checks':['JSON Schema Draft 2020-12','Unique IDs and source references','Typed finite quantities and missing-value status','Operation dependencies and material-state graph','Product/measurement linkage','Illustrative-structure exclusion','Connected-component evaluation grouping','Allowlisted training inputs'],'warnings':['No source-reviewed exact experimental CIF-to-complete-recipe pair is established.','Small seed collection; no general model-performance estimate.','No experimental failure-rate or reproducibility dataset yet.']}
    report['curated_recipes']=sum(r['record_type'] in PROTOCOL_TYPES and r.get('collection')=='reviewed_literature' for r in records)
    report['contextual_observation_records']=sum(r['record_type']=='observation' for r in records)
    report['recipe_records']=sum(r['record_type'] in PROTOCOL_TYPES for r in records)
    report['published_benchmark_rows']=sum(r.get('collection')=='published_benchmark' for r in records)
    report['warnings']=['No verified exact experimental CIF-to-complete-recipe pairs.','Literature seed is too small for cross-study performance estimates.','PbS benchmark rows are published numeric experiments, not individually reviewed complete protocols. The baseline is evaluated separately within that study.','Five selected PbS failure rows are retained as evidence with null continuous targets.']
    queue=ROOT/'data/pilot-source-queue.json'
    if queue.exists():
        q=json.loads(queue.read_text(encoding='utf-8'));dump(public/'pilot-source-queue.json',q);report['queue_count']=len(q['candidates']);report['queue_families']=len({x['family'] for x in q['candidates']})
    dump(public/'measurement-display.json',DISPLAY)
    dump(public/'record.schema.json',SCHEMA);dump(public/'dataset-manifest.json',manifest);dump(public/'validation-report.json',report)
    (public/'records.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
    for task,rows in exports.items():
        path=public/'exports'/(task+'.jsonl');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows),encoding='utf-8')
    (ROOT/'dist/dataset.html').write_text(catalog_html(report,manifest),encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0
if __name__=='__main__':raise SystemExit(main())
