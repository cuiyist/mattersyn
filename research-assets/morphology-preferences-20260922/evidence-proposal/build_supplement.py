from pathlib import Path
import hashlib
import json

SITE = Path(r'[local path redacted]')
OUT = Path(__file__).resolve().parent
rid = 'sasongko-2025-hot-injection'
observation_rid = 'sasongko-2025-growth-results'
record_path = SITE / 'dist/data/records' / (rid+'.json')
r = json.loads(record_path.read_text(encoding='utf-8'))
observation = json.loads((SITE/'dist/data/records'/(observation_rid+'.json')).read_text(encoding='utf-8'))
p = json.loads((SITE/'dist/data/reader-presentation.json').read_text(encoding='utf-8'))
fig = next(f for f in p['records']['sasongko-2025-hot-injection']['figures'] if f['id']=='asset-sasongko2025-figure-3' and f['category']=='structure')
asset = SITE/'dist'/fig['public_asset']
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(asset)==fig['public_asset_sha256']
entries = {}

for i,(sid,panel,temp,shape,label,rationale,mi) in enumerate([
    ('growth-25','d',25,'irregular','Varied particle outlines — schematic','The 25 °C TEM panel shows compact particles with varied, less-regular projected outlines; an irregular envelope avoids imposing one uniform geometric shape.',12),
    ('growth-50','e',50,'cube','Box-like particle schematic','The 50 °C TEM panel shows many compact, approximately squared or rectangular projections; a cube is a simple interpretation of those box-like outlines.',17),
    ('growth-100','f',100,'cube','Box-like particle schematic','The 100 °C TEM panel shows compact particles with approximately squared or rectangular projections; a cube is a simple interpretation of those box-like outlines.',22)
]):
    product_index=i+6
    product=r['products'][product_index]
    assert product['sample_id']==sid
    assert observation['measurements'][mi]['sample_id']==sid
    assert any(link['sample_id']==sid and link['record_id']==observation_rid for link in fig['sample_scope']['canonical_sample_links'])
    evidence=[]
    for evidence_rid,pointer,node in [(rid,f'/products/{product_index}/source_sample_label',product['morphology']), (observation_rid,f'/measurements/{mi}/value',observation['measurements'][mi]['value'])]:
        for ev in node['evidence']:
            evidence.append({'record_id':evidence_rid,'pointer':pointer,'source_id':ev['source_id'],'locator':ev['locator'],'figure_id':fig['id'],'panel':panel})
    evidence.append({'record_id':rid,'data_path':fig['source']['data_path'],'pointer':fig['source']['json_pointer'],'source_id':'sasongko2025','locator':f'Main PDF p. 4, printed p. 15345, Figure 3{panel}; panel label Growth Temp = {temp} °C','figure_id':fig['id'],'panel':panel,'public_asset':fig['public_asset'],'asset_sha256':sha(asset)})
    entries[rid+':'+sid]={
        'record_id':rid,'sample_id':sid,'shape':shape,'label':label,
        'status':'curator_interpretation','basis':'curator_visual_interpretation_of_existing_tem',
        'rationale':rationale,'evidence':evidence,
        'limitations':[
            'The shape is inferred for illustration from 2D TEM projections; a unique 3D surface, exact aspect ratio and facet indices are not measured.',
            'The source does not explicitly parameterize particle morphology. The idealized envelope is not a canonical reported shape value.',
            'This entry belongs only to the temperature-labeled Figure 3 context; no exact physical aliquot or replicate match to another technique, ligand ratio, washing series or general synthesis product is asserted.',
            'Shape does not assign composition, phase purity or atomic crystal structure. The 25 °C context retains its reported mixed phase evidence; individual TEM particles are not assigned to those phases.',
            'The 20 nm bar remains an image scale. Existing reported dimensions and their undefined ± statistic are preserved without estimating new dimensions.'
        ],
        'source_sha256':sha(record_path),'source_hash_scope':'dist/data/records/'+rid+'.json',
        'recipe_link':product['recipe_link'],'measured_atomic_coordinates':False,'same_batch_asserted':False,
        'geometry_parameters':'Illustrative proportions only; no image-derived dimension or coordinate estimate.'
    }

payload={
    'schema_version':'1.0','status':'supplement_proposal_not_integrated',
    'scope':'Three exact temperature-labeled Sasongko Figure 3 TEM contexts only.',
    'policy':'Additive particle-display interpretation; no canonical measurement, sample join, coordinate or training change.',
    'entries':entries
}
(OUT/'morphology-inferences-supplement.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
validation={
    'entry_count':3,'exact_canonical_record_and_sample_ids_valid':True,
    'canonical_measurement_sample_ids_match':True,'reader_figure_sample_scope_links_match':True,
    'existing_asset_hash_matches_reader_metadata':True,
    'visual_inspection':{'public_asset':fig['public_asset'],'sha256':sha(asset),'scope':'Full existing Figure 3 crop including original caption and panel labels; TEM panels d/e/f inspected visually.'},
    'new_downloads':False,'whole_paper_review_claimed':False,'site_or_canonical_files_edited':False,
    'murray_figure6_deferred':{'reason':'Existing Figure 6 caption supports slightly prolate particles, but the current canonical and Reader product contexts contain only method products; no separate reachable Figure 6 sample ID was found. Do not bind this figure shape to method1, method2 or small-species products.','public_asset':'assets/murray1993-figures/figure-06-tem.png','visual_inspection':'Not needed after the exact sample-binding prerequisite failed.'},
    'review_type':'Bounded curator supplement; no independent scientific audit or browser validation claimed.'
}
(OUT/'supplement-validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'entries':len(entries),'shape_map':{k:v['shape'] for k,v in entries.items()}}))
