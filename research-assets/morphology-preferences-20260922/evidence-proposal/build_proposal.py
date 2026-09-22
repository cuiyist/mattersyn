"""Small, additive morphology display proposal; never changes canonical/site files."""
from pathlib import Path
import hashlib
import json

SITE = Path(r'[local path redacted]')
OUT = Path(__file__).resolve().parent
PRESENTATION = json.loads((SITE / 'dist/data/reader-presentation.json').read_text(encoding='utf-8'))
ENTRIES = {}
VISUAL_ASSETS = {}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def add(rid, sid, shape, label, rationale, pointers, fig_route, fig_id, panel, limitations, basis):
    record_path = SITE / 'dist/data/records' / (rid + '.json')
    record = json.loads(record_path.read_text(encoding='utf-8'))
    product_index, product = next((i,p) for i,p in enumerate(record['products']) if p['sample_id'] == sid)
    figure = next(f for f in PRESENTATION['records'][fig_route]['figures'] if f['id'] == fig_id and f['category'] == 'structure')
    asset = SITE / 'dist' / figure['public_asset']
    assert asset.is_file()
    assert sha(asset) == figure['public_asset_sha256']
    evidence = []
    for pointer in [f'/products/{product_index}/source_sample_label'] + pointers:
        node = record
        for part in pointer.strip('/').split('/'):
            node = node[int(part)] if isinstance(node,list) else node[part]
        locators = node.get('evidence',[]) if isinstance(node,dict) else product.get('morphology',{}).get('evidence',[])
        if not locators:
            locators = product['composition']['evidence']
        for locator in locators:
            evidence.append({'record_id':rid, 'pointer':pointer, 'source_id':locator['source_id'], 'locator':locator['locator'], 'figure_id':fig_id, 'panel':panel})
    evidence.append({'record_id':rid, 'pointer':figure['source']['json_pointer'],
                     'data_path':figure['source']['data_path'], 'source_id':figure['source_id'],
                     'locator':figure['original_title']+'; '+panel,
                     'figure_id':fig_id, 'panel':panel,
                     'public_asset':figure['public_asset'], 'asset_sha256':sha(asset)})
    ENTRIES[rid+':'+sid] = {
        'record_id':rid, 'sample_id':sid, 'shape':shape, 'label':label,
        'status':'curator_interpretation', 'basis':basis,
        'rationale':rationale, 'evidence':evidence,
        'limitations':limitations,
        'source_sha256':sha(record_path),
        'source_hash_scope':'dist/data/records/'+rid+'.json',
        'recipe_link':product['recipe_link'],
        'measured_atomic_coordinates':False,
        'same_batch_asserted':False,
        'geometry_parameters':'Illustrative proportions only; no image-derived dimension or coordinate estimate.'
    }
    VISUAL_ASSETS[figure['public_asset']] = {'sha256':sha(asset), 'inspection':'Existing local crop inspected visually; no source-paper re-review or fresh download.'}

common = 'The schematic is a simplified envelope, not a measured 3D surface, crystallographic facet assignment or atomic reconstruction.'
evans_limits = [common, 'The spherical and cubic panels are separate source contexts; their exact recipe, growth time and physical batch are unassigned.', 'The 5 nm and 50 nm labels are scale bars, not particle diameters. Particle packing does not assign internal atomic phase.']
add('evans-2010-pbse-tem','pbse-tem-spheres','sphere','Spherical PbSe example',
    'The existing source caption and left-morphology observation identify the left Figure S16 example as small spherical PbSe dots.',
    ['/measurements/3/value'], 'evans-2010-pbse-qd','evans2010-figure-S16','left panel',evans_limits,'reported_description_to_schematic')
add('evans-2010-pbse-tem','pbse-tem-cubes','cube','Cubic PbSe example',
    'The existing source caption and right-morphology observation identify the right Figure S16 example as larger cubic PbSe dots.',
    ['/measurements/4/value'], 'evans-2010-pbse-qd','evans2010-figure-S16','right panel',evans_limits,'reported_description_to_schematic')

for rid,sid,panel,fig,pointer in [
    ('fu-2007-zno-s1','fu2007-s1','panel a','fig2','/measurements/0/value'),
    ('fu-2007-zno-s2','fu2007-s2','panel b','fig2','/measurements/0/value'),
    ('fu-2007-zno-s4','fu2007-s4','S4 image','figS3','/measurements/0/value')]:
    add(rid,sid,'sphere','Rounded-dot schematic',
        'The assigned HRTEM crop shows compact, broadly rounded dot projections; a sphere is used as a simple visual interpretation.',
        [pointer],rid,fig,panel,
        [common, 'Two-dimensional TEM projections do not establish a unique 3D shape; exact geometric shape is not independently parameterized.', 'This interpretation belongs only to the named S1, S2 or S4 context, with no transfer to dry powder, early aliquots or post-treatment states.'],
        'curator_visual_interpretation_of_existing_tem')

stowell_limits = [common, 'Rounded and locally faceted projections are simplified to a sphere; no facet indices or measured aspect ratio are assigned.', 'Only the named TEM panel is represented. No transfer to the general method product, SAXS fractions, XRD specimen or recycling aliquots.']
for rid,sid,panel,fig,pointer in [
    ('stowell-2005-ir-oa-oleylamine-290c','oa-fig1a','panel A','figure-1','/measurements/1/value'),
    ('stowell-2005-ir-oa-oleylamine-290c','oa-fig1d','panel D single particle','figure-1','/measurements/2/value'),
    ('stowell-2005-ir-toab-270c','toab-fig3','panel A','figure-3','/measurements/0/value'),
    ('stowell-2005-ir-topb-270c','topb-fig3','panel B','figure-3','/measurements/0/value')]:
    add(rid,sid,'sphere','Rounded Ir particle schematic',
        'The assigned TEM panel shows compact, broadly rounded particles with some faceting; a sphere is a simplified display interpretation.',
        [pointer],rid,fig,panel,stowell_limits,'curator_visual_interpretation_of_existing_tem')

add('saha-2019-coo-cofe2o4-seeded-growth','saha2019-core-shell-30min','core-shell','Rounded core/shell schematic',
    'The selected 30 min context combines almost-spherical morphology, the authors\' core/shell assignment, and corresponding core/shell TEM/HRTEM.',
    ['/products/1/morphology','/products/1/notes','/measurements/2/value'],
    'saha-2019-coo-cofe2o4-seeded-growth','figure-2','panels b and d',
    [common, 'The drawing uses an idealized concentric interface; thickness uniformity, exact interface shape and atomic positions are not measured.', 'The 15 min aliquot has no separately assigned TEM diameter or shell-thickness value and does not receive this rounded 30 min depiction.'],
    'reported_architecture_and_morphology_to_schematic')

payload = {
    'schema_version':'1.0', 'status':'proposal_not_integrated',
    'scope':'Ten source-context-specific, additive particle-display interpretations drawn only from existing reviewed records and six local figure crops.',
    'policy':'These entries authorize schematic display only, never canonical measurement changes, new sample joins, measured coordinates or training eligibility.',
    'input_reader_presentation_sha256':sha(SITE / 'dist/data/reader-presentation.json'),
    'entries':ENTRIES
}
(OUT/'morphology-inferences.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
validation = {
    'entry_count':len(ENTRIES),
    'unique_keys':len(ENTRIES)==len(set(ENTRIES)),
    'exact_canonical_record_and_sample_ids_valid':True,
    'canonical_evidence_pointers_resolved':True,
    'existing_asset_hashes_match_reader_metadata':True,
    'visual_assets':VISUAL_ASSETS,
    'site_or_canonical_files_edited':False,
    'new_downloads':False,
    'whole_paper_review_claimed':False,
    'coordinates_inferred':False,
    'review_type':'Bounded curator proposal; independent scientific approval not claimed.',
    'deferred':[
        {'context':'tessier2015-inp-incl3-reference1:inp-reference-characterization-20min','reason':'Figure 1c was visually inspected but the low-contrast selected crop does not add a sufficiently clear shape claim; preserve the separate 20/30 minute boundary.'},
        {'context':'tessier2015-inp-incl3-reference1:inp-reference1-product','reason':'No shape imported from the separate 20 minute characterization or core/shell panels.'},
        {'context':'saha-2019-coo-cofe2o4-seeded-growth:saha2019-core-shell-15min','reason':'Do not transfer the 30 minute rounded TEM envelope or thickness to this separately scoped aliquot.'},
        {'context':'evans-2010-pbse-tem:two-pbse-tem-morphology-examples','reason':'Contains two morphology examples; do not select only sphere or cube.'},
        {'context':'evans-2010-pbse-qd','reason':'Figure S16 exact recipe/time linkage is unreported; no morphology propagated to the timed QD optical recipe product.'}
    ]
}
deferred_asset = SITE / 'dist/assets/selected-evidence/tessier2015/figure-1.png'
validation['additional_inspected_asset_without_added_inference'] = {
    'public_asset':'assets/selected-evidence/tessier2015/figure-1.png',
    'sha256':sha(deferred_asset),
    'outcome':'Deferred: insufficiently clear projected shape in panel c; no propagation across 20/30 minute or core/shell contexts.'
}
(OUT/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'entry_count':len(ENTRIES),'visual_asset_count':len(VISUAL_ASSETS),'outputs':['morphology-inferences.json','validation.json']}))
