"""Create bounded proposed files only. Never edits recipe-atlas."""
from pathlib import Path
import json,hashlib,difflib
P=Path(__file__).resolve().parent;S=P.parents[2]/'recipe-atlas'
def snapshot(rel):
 p=P/'base'/rel;p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():p.write_bytes((S/rel).read_bytes())
 return p.read_text('utf8')
def put(rel,text):
 p=P/'files'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,'utf8')
def replace(text,before,after):
 assert text.count(before)==1,before
 return text.replace(before,after)
t=snapshot('scripts/dataset_lib.py')
t=replace(t,'from schema_definition import SCHEMA','from schema_definition import SCHEMA\nfrom structure_recipe_metrics import assess_structure_recipe, exact_recipe_selection')
t=replace(t,'def eligibility(r):','def eligibility(r, structure_policy=None):')
t=replace(t,"    measured=[s for s in r['structure_assets'] if s['eligible_as_measured_label'] and s['sample_id'] in explicit]\n",'')
t=replace(t,"    unresolved_protocol=any(v.get('status')=='not_reported' for _,v in walk({'materials':r['materials'],'stocks':r['stocks'],'operations':r['operations']}))\n",'')
t=replace(t,"      'exact_structure_recipe':(base and bool(measured) and not r['quality']['missing_fields'] and not unresolved_protocol,'Requires measured sample coordinates, explicit recipe linkage and no unresolved required fields.'),\n",'')
before="    return {k:{'eligible':bool(v[0]) and k in r['quality']['requested_tasks'],'reason':v[1] if base or k=='optical_outcome' else 'Source review required, or structured-data verification supports only a separately gated benchmark task.'} for k,v in candidates.items()}"
after=before.replace('return {','result={')+"\n    result['exact_structure_recipe']=assess_structure_recipe(r,structure_policy)\n    return result"
t=replace(t,before,after)
t=replace(t,"def training_view(r,task):\n    if not eligibility(r).get(task,{}).get('eligible'):raise ValueError('Record is not eligible for '+task)","def training_view(r,task,structure_policy=None):\n    if not eligibility(r,structure_policy).get(task,{}).get('eligible'):raise ValueError('Record is not eligible for '+task)")
t=replace(t,"    if task=='exact_structure_recipe':\n        explicit={p['sample_id'] for p in r['products'] if p['recipe_link']=='explicit'}\n        inputs['measured_structures']=[s for s in r['structure_assets'] if s['eligible_as_measured_label'] and s['sample_id'] in explicit]", "    if task=='exact_structure_recipe':\n        profile=structure_policy['task_profiles'][r['record_id']]\n        sample=next(p for p in r['products'] if p['sample_id']==profile['sample_id'])\n        inputs={'composition':sample['composition']['value'],'method':r['method']}\n        inputs['structure_representation']=profile['coordinate_validation']['representation']\n        inputs['measured_structures']=[s for s in r['structure_assets'] if s['id'] in profile['structure_asset_ids']]\n        output=exact_recipe_selection(r,structure_policy)\n        output['task_profile_id']=profile['id']\n        output['contextual_missing_fields']=r['quality']['missing_fields']")
put('scripts/dataset_lib.py',t)
t=snapshot('scripts/catalog_view.py')
helper='''
def structure_coverage_html(report,esc):
    coverage=report.get('structure_recipe_coverage')
    if not coverage:
        return '<section class="record-section"><h2>Structure and recipe coverage</h2><p>Coordinate availability and recipe-link metrics have not been generated for this build. Unavailable counts are not zero.</p></section>'
    counts=coverage['counts']
    metrics=[('sample_coordinate_assets','Distinct sample-coordinate assets'),('source_verified_explicit_links','Source-verified explicit sample–recipe links'),('exact_task_ready_records','Task-ready exact-structure records')]
    result='<section class="record-section"><h2>Structure and recipe coverage</h2><div class="dataset-summary">'
    for key,label in metrics:
        value=counts.get(key)
        result+='<div><strong>'+('—' if value is None else str(value))+'</strong><span>'+esc(label)+'</span></div>'
    result+='</div><p>These are different units: coordinate assets, documentary recipe links and task-ready records. They are not counts of independent batches. A source-verified link does not establish recipe completeness or approve a training label.</p>'
    kinds=coverage.get('asset_representation_counts',{})
    linked_kinds=coverage.get('explicit_link_representation_counts',{})
    names={'molecular_structure':'molecular structures','experimental_periodic_structure':'experimental periodic structures','finite_sample_structure':'finite sample structures','unclassified':'representation not yet classified'}
    if kinds:
        result+='<p>Available sample-coordinate assets: '+esc('; '.join(str(n)+' '+names.get(k,k) for k,n in sorted(kinds.items())))+'.'
        if linked_kinds:result+=' Explicit recipe links: '+esc('; '.join(str(n)+' '+names.get(k,k) for k,n in sorted(linked_kinds.items())))+'.'
        result+=' Molecular species are not automatically the paper’s nominal nanocrystal material.</p>'
    result+='<p>Canonical sample-coordinate links are checked for local asset availability. External bulk references and illustrative viewers improve the reader view but are excluded here. Exact training admission additionally requires approved measured labels, an explicit requested task, and an independently audited profile of required recipe fields. Optional or characterization missingness is not automatically a required synthesis gap.</p>'
    result+='<a class="data-download" href="data/structure-recipe-coverage.json">Inspect record-level availability, linkage and exclusion reasons ↓</a></section>'
    return result

'''
t=replace(t,'def render(report,manifest,head,header,esc,human):',helper+'def render(report,manifest,head,header,esc,human):')
t=replace(t,",(tasks['exact_structure_recipe'],'Verified sample-coordinate–recipe pairs')",'')
t=replace(t,'<p><strong>Structure-pair scope:</strong> this count requires measured atomic coordinates linked to the experimental sample and an eligible recipe. It excludes illustrative or independent bulk reference structures. Crystal-phase, morphology and size observations remain available in the source records even when this exact-pair count is zero.</p>','<p>Crystal-phase, morphology and size observations remain available even when no record is ready for exact-structure training. Coordinate availability, recipe linkage and task readiness are reported separately below.</p>')
t=replace(t,"    s+='''</div><div class=\"dataset-filters\">", "    s+='</div>'+structure_coverage_html(report,esc)\n    s+='''<div class=\"dataset-filters\">")
put('scripts/catalog_view.py',t)
t=snapshot('tests/test_dataset.py')
t=replace(t,"    def test_exact_structure_export_actually_contains_measured_structure_input(self):", "    def test_measured_asset_without_audited_profile_remains_excluded(self):")
t=replace(t,"        self.assertTrue(eligibility(r)['exact_structure_recipe']['eligible'])\n        exported=training_view(r,'exact_structure_recipe')\n        self.assertIn(url,json.dumps(exported['input']), 'A structure-conditioned training example cannot silently contain only composition and method')", "        self.assertFalse(eligibility(r)['exact_structure_recipe']['eligible'])\n        self.assertIn('audited_task_profile_missing',eligibility(r)['exact_structure_recipe']['reason_codes'])\n        with self.assertRaises(ValueError):\n            training_view(r,'exact_structure_recipe')")
put('tests/test_dataset.py',t)
model=S/'dist/assets/chemical-registry/models/evans2010-species9-reference-3d.json'
policy={'schema_version':'1.0','scope':'Metadata classification only; no real training profiles are admitted. Coordinate availability is not scientific/task approval.','asset_qualifications':{'evans2010::evans2010-species9-source-model':{'url':'/assets/chemical-registry/models/evans2010-species9-reference-3d.json','asset_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'representation':'molecular_structure','label':'Molecular species 9 · C24H20P2PbSe4','basis':'Existing source-scoped model caption and canonical structure-asset descriptions identify the molecular species; transformed refinement coordinates include 20 reported calculated riding hydrogens. This classification adds no QD, full-cell, DFT or training approval.','source_url':None}},'task_profiles':{}}
# The DOI is read from the actual bound canonical source rather than inferred.
r=json.loads((S/'data/records/evans-2010-species9-crystallization.json').read_text('utf8'));policy['asset_qualifications']['evans2010::evans2010-species9-source-model']['source_url']=r['sources'][0]['url']
put('data/structure-task-policy.json',json.dumps(policy,ensure_ascii=False,indent=2)+'\n')
snapshot('scripts/build_dataset.py');snapshot('scripts/schema_definition.py')
patch=''
for rel in ['scripts/dataset_lib.py','scripts/catalog_view.py','tests/test_dataset.py']:
 patch+=''.join(difflib.unified_diff((P/'base'/rel).read_text('utf8').splitlines(True),(P/'files'/rel).read_text('utf8').splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
(P/'replacements.patch').write_text(patch,'utf8')
print('Prepared private replacement files; Site untouched.')
