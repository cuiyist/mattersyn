"""Additive, read-only scientific presentation projection. Writes only beside this file.

No canonical, reader, model, or source input is changed. Classification is editorial
navigation, never a new experiment/sample or scientific-evidence qualification.
"""
from pathlib import Path
from collections import Counter
import hashlib, json, re

SITE = Path(__file__).resolve().parents[1]
HERE = SITE.parent/'research-assets/reader-metadata-build'
HERE.mkdir(parents=True,exist_ok=True)
INPUTS = {}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    INPUTS[p.relative_to(SITE).as_posix()] = sha(p)
    return json.loads(p.read_bytes())
def write(name, data):
    (HERE/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
def source(path, pointer, **extra):
    return {'data_path':path, 'json_pointer':pointer, 'input_sha256':INPUTS[path], **extra}
def neat(text):
    return re.sub(r'\s+', ' ', str(text or '')).strip()
def sentence(text):
    """Keep a complete first sentence; never cut at a character budget."""
    text = neat(text)
    # Avoid decimal points, initials, reference page abbreviations and formula labels.
    spans = re.split(r'(?<=[.!?])\s+(?=[A-Z][a-z])', text)
    return spans[0] if spans else text
def scope_text(value):
    if isinstance(value,str): return neat(value)
    if isinstance(value,dict): return neat(value.get('label') or value.get('description') or '')
    return ''

# One code per source figure in the reviewed reader's existing order. Both-category
# figures are deliberately repeated in per-route galleries, preserving the same id.
# S=structure/morphology/surface; P=physical/optical/magnetic/functional property;
# O=preparation/precursor identity/interpretive mechanism. SP is a mixed source figure.
CLASSIFICATION = {
 'banerjee2003':'S S S S S S P O S',
 'besson2002':'SP S S P',
 'braun2001':'O P P P',
 'dabbousi1997':'P P P P P S S S S S S S S O P P',
 'danek1996':'P S S P P P P P P P P',
 'dantas2002':'P P O S P P P',
 'evans2010':'P P O O O O P O O O O O O S S O P S',
 'feld2019':'O O O S S S S S S O O O O O O O O O O O S S O S S S S P P P',
 'friedfeld2019':'P O SP P P P O P P O P P P P S S S P S P P P P P P P P P P P P P P P P P P P P P P P S S',
 'fu2007':'S S S P P P O O S P S',
 'gerion2001':'O P P P S S P',
 'ghosh2012':'SP S S SP SP S O S S S O S P P P',
 'gu2004':'S P S P P S S',
 'heath1996':'O S S S S S',
 'heo2003':'S S S S S S S',
 'lian2021':'O S P P SP P S S S P P P P P P P P P P P S S P P P P P',
 'littau1993':'O P S S S S S S P P P P',
 'matuhina2023':'O O S S P P P P SP P O S S S P P P P S S',
 'morrison2017':'S S P S S P P S S O O O S P S S P S S',
 'nagasaki2004':'P P P P P P S S',
 'nakonechnyi2017':'O SP SP P SP O O O P S',
 'norberg2004':'P P S O P P P P P P O P P',
 'pati2009':'S S S S S S P S',
 'peng1998':'P SP S O P',
 'ribeiro2004':'P S O S S P S',
 'saha2019':'SP S S P P S S P P',
 'sashchiuk2004':'S S S P P',
 'sasongko2025':'SP SP SP P P O P P',
 'schwartz2003':'P S P P S P P P P SP P P P S P P P',
 'shah2001':'O S S S S S P S S S S',
 'sommer2020':'O S S S S O S S S S S S S P',
 'stiger1999':'S P P P S S S S S',
 'stowell2005':'S P S SP P',
 'veinot1997':'S O S S P S',
 'yao1998':'P P S S S S S P SP',
 'yi2002':'S S S P P P P P O P',
 'tessier2015':'SP S S', 'zhang2019':'SP SP SP P P S',
}

# Titles are navigation labels, based on the reviewed caption, not new findings.
# Most figures already have readable scientific titles and require no override.
TITLES = {
 'feld2019':['Precursor-to-particle concept','Iron-oleate complexes during heating','Proposed reduction and gas analysis','Star and cube morphology with diffraction','Accessible star and cube morphologies','Octapod microscopy and tomography','Pod lattice, facets and intensity profile','Spatial iron-valence analysis','Star-to-cube growth interpretation','Iron(II) precursor precipitation','Iron(III) precursor precipitation','Iron(II) oleate drying','Iron(III) oleate drying','Synthesis apparatus','Iron(II) oleate mass spectrum','Assigned oleate-ion fragmentation','Oleic-acid purity and isotope envelopes','Linoleic-acid mixture fit','Gas analysis at 60 °C','Oleic-acid air control','Octapod lattice imaging','Tilted octapod microscopy','Dilution and time condition matrix','Early star morphology','Later cube morphology','Fe:OA ratio and cubic morphology','Octapod-to-cube time series','Star magnetization','Cube magnetization','Smaller-particle magnetization'],
 'fu2007':['S1/S2 powder diffraction','S1/S2 particle morphology','Surface groups by infrared spectroscopy','Emission and photostability','Absorption and extrapolated onsets','Surface-treatment emission comparison','Proposed surface reaction','Proposed interface-state model','Early-growth lattice image','Relative quantum-yield comparison','S4 particle morphology'],
 'gu2004':['FePt and heterodimer microscopy','Heterodimer magnetic and optical properties','Heterodimer elemental spectrum','FePt optical absorption','FePt magnetization','Sulfur-treated intermediate microscopy','CdS-treated intermediate microscopy'],
 'heath1996':['Patterning and selective growth','Patterned well array','Germanium island lattice contrast','Island spacing and relative size','Island number and growth-time proxy','Confined feature and height profile'],
 'littau1993':['Aerosol synthesis apparatus','Colloid absorption','Earlier AKS41 particle microscopy','Earlier AKS41 chromatographic size','6.0 colloid chromatographic size','6.0/2.0 powder diffraction','6.0 powder infrared spectrum','1.0 colloid chromatographic size','6.0 colloid activation and emission','2.0 colloid emission','1.0 colloid emission','1.0 time-resolved emission'],
 'nakonechnyi2017':['Seeded-growth concept','Zinc-blende CdSe/CdS comparisons','Zinc-blende CdSe/ZnSe comparisons','Seeded and unseeded optical yield','Wurtzite core/shell comparisons','Simulated growth trajectories','Kinetic model scheme','Assumed solubility in the growth model','Precursor-omission optical controls','Four material systems by SAED'],
 'saha2019':['Core/shell concept and measurements','Core and shell-grown diffraction','Core and shell-grown microscopy','Field-dependent magnetic hysteresis','Exchange bias and coercivity','Core and shell-grown size distributions','Additional core/shell lattice images','Hysteresis and thermomagnetic curves','Magnetic heating response'],
 'stowell2005':['Oleic-acid/oleylamine Ir characterization','Ligand-dependent hydrogenation','Ligand-dependent Ir morphology','Recycling: catalysis and morphology','TOPB-coated Ir recycling'],
 'tessier2015':['InP and core/shell optics and microscopy','InP size histogram','InP and core/shell diffraction'],
 'zhang2019':['Ligand-dependent dimensions and photophysics','Ligand-dependent morphology and optics','Formulation-resolved optical and diffraction data','Formulation-resolved PL decays','Multiexponential lifetime-fit parameters','Phosphonate surface-binding interpretation'],
}

# Explicit scientific excerpts chosen from the existing reviewed intuition sections.
# No literature background is silently relabeled as an outcome of the current recipe.
INTUITION_IDS = {
 'banerjee2003':['tdpa-competition','site-selectivity'],
 'besson2002':['complexation','surface-retention'],
 'braun2001':['well-count-design','nucleation-ph'],
 'dabbousi1997':['temperature-tradeoff'],
 'danek1996':['slow-delivery'],
 'dantas2002':['anneal-rationale','two-photon-model'],
 'evans2010':['unit-abstract-mechanistic-scope','unit-object-scheme-1'],
 'friedfeld2019':['overview-intuition'],
 'gerion2001':['why-shell'],
 'ghosh2012':['source-fact-ghosh2012-ml-model','source-fact-ghosh2012-steric-model'],
 'gu2004':['one-pot-mechanism','intermediate-isolation-failure'],
 'heath1996':['growth-mode'],
 'heo2003':['fact-scattering-model','fact-oxidation-assignment'],
 'lian2021':['source-fact-lian2021-photophysical-model','source-fact-lian2021-nc-surface-interpretation'],
 'littau1993':['source-chemical_intuition-0','source-chemical_intuition-2'],
 'matuhina2023':['overview-intuition'],
 'morrison2017':['source-morrison2017-mechanism','source-morrison2017-surface-model'],
 'nagasaki2004':['author-coordination','author-segregation'],
 'norberg2004':['intuition-induction','intuition-amine-clean'],
 'pati2009':['overview-intuition'],
 'peng1998':['why-focusing','why-refeeding'],
 'ribeiro2004':['overview-growth-model'],
 'sashchiuk2004':['assembly-controls','ligand-heating'],
 'sasongko2025':['overview-intuition','source-facts-sasongko2025-ligand-mechanism'],
 'schwartz2003':['colloid-rationale','dopant-problem'],
 'shah2001':['why-arrested','why-fluorinated'],
 'sommer2020':['overview-intuition'],
 'stiger1999':['surface-energy-islanding'],
 'veinot1997':['mild-acyl-transfer'],
 'yao1998':['radial-nucleation','salt-screening'],
 'yi2002':['anneal-rationale','sensitizer-emitter'],
}

def get_links(value):
    """Collect only explicitly supplied record ids, never infer from composition."""
    result=set()
    if isinstance(value,list):
        for x in value: result.update(get_links(x))
    elif isinstance(value,dict):
        if isinstance(value.get('record_id'),str): result.add(value['record_id'])
        for k in ['canonical_sample_links','sample_links','canonical_links']:
            result.update(get_links(value.get(k,[])))
    elif isinstance(value,str):
        if value in ALL_RECORDS: result.add(value)
    return result

def figure_base(sid,r,path,i,f):
    code=CLASSIFICATION[sid].split()[i]
    cats=[{'S':'structure','P':'property','O':'other'}[c] for c in code]
    original_title=neat(f.get('label') or f['id'])
    title=TITLES.get(sid,[None]*len(r['figures']))[i] or original_title
    caption=neat(f.get('caption_paraphrase') or f.get('summary') or original_title)
    original_scope=scope_text(f.get('sample_scope')) or neat(f.get('sample_assignments'))
    direct=get_links(f.get('sample_links',[]))|get_links(f.get('sample_scope',{}))
    if not original_scope: original_scope='The original figure and caption define the specimen context.'
    asset=f.get('public_asset')
    locator=f.get('source_locator') or {'document_role':f.get('document_role'),'page':f.get('page'),'printed_page':f.get('printed_page'),'figure':original_title}
    return {'id':f['id'],'source_id':sid,'public_asset':asset,
      'categories':cats,'title':title,'summary':caption,'scope':original_scope,
      'source_locator':locator,'record_links':sorted(direct),'sample_links':f.get('sample_links',[]),
      'sample_scope':f.get('sample_scope'),
      'source':source(path,f'/figures/{i}'),'original_title':original_title,
      'public_asset_sha256':sha(SITE/'dist'/asset) if asset else None,
      'evidence_class':f.get('evidence_class',f.get('evidence_kind')),
      'reader_url':f'paper-review.html?id={sid}' if sid in REVIEWS else None,
      'selected_evidence_only':sid not in REVIEWS,
      'notes':f.get('notes',[]),'sample_linkage':f.get('sample_linkage'),
      'classification_basis':'Editorial gallery classification of the existing reviewed figure label/caption; no additional scientific claim.'}

def intuition(sid,r,path):
    result=[]
    chosen=set(INTUITION_IDS.get(sid,[]))
    for si,s in enumerate(r.get('reader_sections',[])):
        for ii,x in enumerate(s.get('items',[])):
            if x.get('id') not in chosen: continue
            result.append({'id':x['id'],'title':neat(x['title']),'summary':neat(x['text']),
               'scope':'Source discussion; interpretation and cited context are distinguished in the text.',
               'claim_type':x.get('claim_type','source_discussion'),
               'source_id':sid,'source':source(path,f'/reader_sections/{si}/items/{ii}'),
               'source_locator':x.get('evidence',[]),'canonical_links':x.get('canonical_links',[]),
               'sample_scope':x.get('sample_scope'),'reader_url':f'paper-review.html?id={sid}'})
    assert chosen=={x['id'] for x in result}, (sid,'missing selected intuition',chosen-{x['id'] for x in result})
    if isinstance(r.get('chemical_intuition'),list):
        for i,x in enumerate(r['chemical_intuition'][:2]):
            summary=x.get('claim') or ' '.join([x.get('author_interpretation',''),x.get('curator_caveat','')])
            result.append({'id':x.get('id',f'intuition-{i+1}'),'title':x.get('title','Authors’ chemical rationale'),
              'summary':neat(summary),'scope':x.get('type','Authors’ interpretation; caveats retained.'),
              'claim_type':'author_interpretation','source_id':sid,'source':source(path,f'/chemical_intuition/{i}'),
              'source_locator':x.get('source_locators',x.get('locator'))})
    if sid=='feld2019':
        for i in [1,2]:
            x=r['mechanistic_findings'][i]
            result.append({'id':f'mechanism-{i+1}','title':['','Proposed precursor network','Star-to-cube growth'][i],
              'summary':x['finding']+' '+x['status'],'scope':x['status'],'claim_type':'author_interpretation',
              'source_id':sid,'source':source(path,f'/mechanistic_findings/{i}'),'source_locator':x['source']})
    if sid=='stowell2005':
        x=r['characterization_inventory'][4]
        for i,text in enumerate(x['interpretations']):
            result.append({'id':f'ligand-interpretation-{i+1}',
              'title':['Ligand exposure and catalytic activation','Particle growth during recycling'][i],
              'summary':text,'scope':'Authors’ interpretation; no direct ligand-coverage or binding-energy measurement.',
              'claim_type':'author_interpretation','source_id':sid,
              'source':source(path,f'/characterization_inventory/4/interpretations/{i}'),
              'source_locator':x['source_locators']})
    # Explicitly reviewed mechanism figure captions provide the source text where a
    # legacy reader has no separately structured intuition section.
    for i in {'fu2007':[6,7],'nakonechnyi2017':[5,7]}.get(sid,[]):
        f=r['figures'][i]
        result.append({'id':f"interpretation-{f['id']}",'title':TITLES[sid][i],
          'summary':neat(f['caption_paraphrase']),'scope':'Source model or interpretation; not a measured atomic reconstruction.',
          'claim_type':'model_or_interpretation','source_id':sid,'source':source(path,f'/figures/{i}'),
          'source_locator':{'document_role':f.get('document_role'),'page':f.get('page'),'figure':f['label']}})
    return result

def products(r,path):
    facts=[];contexts=[]
    products=r.get('products',[])
    # A source-context placeholder has no non-null scientific product field and is
    # therefore omitted from the concise result list, never from canonical data.
    for i,p in enumerate(products):
        fields=[(k,p.get(k,{})) for k in ['composition','phase','morphology','surface']]
        if p['sample_id'].startswith(('fact-context-','source-payload-')):continue
        scope=neat(p.get('source_sample_label') or p['sample_id'].replace('-',' '))
        context={'sample_id':p['sample_id'],'label':scope,'recipe_link':p.get('recipe_link'),
                 'source':source(path,f'/products/{i}'),'notes':p.get('notes',[])}
        contexts.append(context)
        for k,v in fields:
            if not isinstance(v,dict) or v.get('value') is None:continue
            facts.append({'label':{'composition':'Reported composition','phase':'Phase','morphology':'Morphology','surface':'Surface'}[k],
              'value':v['value'],'scope':scope,'sample_id':p['sample_id'],
              'recipe_link':p.get('recipe_link'),'status':v.get('status'),
              'source':source(path,f'/products/{i}/{k}'),'source_locator':v.get('evidence',[]),
              'qualifier':v.get('note'),'record_id':r['record_id'],'kind':k})
    # Unknown composition remains unknown. The nominal target is a separate field.
    return facts,contexts

HUBS={p.stem:read(p) for p in sorted((SITE/'dist/data/materials').glob('*.json'))}
ALL_RECORDS={p.stem:read(p) for p in sorted((SITE/'data/records').glob('*.json'))}
ROUTES=sorted({i for h in HUBS.values() for i in h['record_ids']})
REVIEWS={p.stem:read(p) for p in sorted((SITE/'data/paper-reviews').glob('*.json'))}
LEGACY={p.stem:read(p) for p in sorted((SITE/'dist/data/recipe-figures').glob('*.json'))}
all_reviews={**REVIEWS,**LEGACY}
figures={};intuitions={}
for sid,r in all_reviews.items():
    path=f'data/paper-reviews/{sid}.json' if sid in REVIEWS else f'dist/data/recipe-figures/{sid}.json'
    assert sid in CLASSIFICATION, sid
    assert len(CLASSIFICATION[sid].split())==len(r.get('figures',[])),(sid,'classification count')
    if sid in TITLES:assert len(TITLES[sid])==len(r['figures']), (sid,'title count')
    figures[sid]=[figure_base(sid,r,path,i,f) for i,f in enumerate(r['figures'])]
    intuitions[sid]=intuition(sid,r,path)

# Earlier curated benchmark readers predate the paper-review contract. Their
# retained figure evidence is transported without claiming exact recipe mapping.
mpath='dist/data/paper-evidence/murray1993.json'
murray=read(SITE/mpath)
read(SITE/'dist/assets/murray1993-characterization.json')
figures['murray1993']=[]
murray_titles=['Size selection and absorption','CdS/CdSe/CdTe absorption','CdSe absorption size series',
 'Optical gap: experiment and theory','CdSe absorption and photoluminescence','Dispersed CdSe lattice image',
 'CdSe planar disorder','Particle orientation and stacking faults','CdSe particle packing','CdS/CdSe/CdTe diffraction',
 'CdSe diffraction size series','Phase-model diffraction comparison','Shape-model diffraction comparison',
 'Small-particle diffraction models','Experimental and model diffraction']
for i,f in enumerate(murray['figures']):
    a=f['original_figure_asset'];asset=a['file'];assert sha(SITE/'dist'/asset)==a['sha256']
    cat='property' if f['figure']<=5 else 'structure'
    figures['murray1993'].append({'id':f['id'],'source_id':'murray1993','public_asset':asset,
      'categories':[cat],'title':murray_titles[f['figure']-1],'summary':f['caption_paraphrase'],
      'scope':'Figure-specific specimen; exact synthesis settings and cross-figure identity are not established.',
      'source_locator':f['source'],'record_links':f['sample'].get('linked_recipe_record_ids',[]),
      'sample_scope':f['sample'],'sample_links':[], 'source':source(mpath,f'/figures/{i}'),
      'original_title':f"Figure {f['figure']}",'public_asset_sha256':a['sha256'],
      'evidence_class':f['evidence_kind'],'reader_url':'murray-1993-characterization.html',
      'selected_evidence_only':False,'notes':murray['evidence_rules'],
      'classification_basis':'Existing reviewed characterization category and figure caption.'})
ppath='dist/assets/peng2000-recipe.json';peng=read(SITE/ppath)
figures['peng2000']=[]
for i,f in enumerate(peng['figure_outcomes']):
    summary=f['type']+'.'
    if f.get('observations'):summary+=' '+' '.join(f['observations'])
    if f.get('body_connections'):summary+=' '+f['body_connections']
    figures['peng2000'].append({'id':f"peng2000-figure-{f['figure']}",'source_id':'peng2000','public_asset':None,
      'categories':['property' if f['figure']==4 else 'structure'],
      'title':['Quantum-rod TEM','Rod diffraction and simulation','Rod orientation microscopy','Dot/rod optical comparison'][i],
      'summary':summary,'scope':peng['scope']['key_constraint'],
      'source_locator':{'document_role':'main','page':f['pdf_page'],'printed_page':f['printed_page'],'figure':f['figure']},
      'record_links':[],'sample_links':[],'sample_scope':None,
      'source':source(ppath,f'/figure_outcomes/{i}'),'original_title':f"Figure {f['figure']}",
      'public_asset_sha256':None,'evidence_class':f['type'],'reader_url':'alivisatos-2000.html',
      'selected_evidence_only':False,'notes':[f.get('caution',f.get('measurement_caution',''))],
      'asset_status':'No corresponding original figure image is present in the existing public assets.',
      'classification_basis':'Existing reviewed figure-outcome type; this is a text-only evidence card, not a synthetic image.'})
intuitions['peng2000']=[{'id':f'growth-narrative-{i+1}','title':['Initial axial growth','Monomer depletion','Monomer replenishment'][i],
    'summary':x['description'],'scope':peng['growth_narrative']['display_note'],
    'source_id':'peng2000','claim_type':'author_growth_interpretation',
    'source':source(ppath,f'/growth_narrative/stages/{i}'),'source_locator':x['source']}
    for i,x in enumerate(peng['growth_narrative']['stages'])]
mrpath='dist/assets/murray1993-recipe.json';mr=read(SITE/mrpath)
intuitions['murray1993']=[{'id':'injection-growth-size-selection','title':'Injection, growth and size selection',
    'summary':mr['recommended_display']['main_story'],
    'scope':'Reviewed Method 1 rationale; specific Method 2 and CdS/CdTe variants retain their own procedures.',
    'source_id':'murray1993','claim_type':'reviewed_procedure_rationale',
    'source':source(mrpath,'/recommended_display/main_story'),
    'source_locator':'Murray et al. (1993), Experimental Section and growth/size-selection discussion.'}]

records={}
for rid in ROUTES:
    r=ALL_RECORDS[rid];sid=r['lineage']['source_group'];path=f'data/records/{rid}.json'
    product_facts,contexts=products(r,path)
    source_figures=figures.get(sid,[]);review=all_reviews.get(sid,{})
    linked_contexts=set(review.get('route_evidence_contexts',{}).get(rid,[]))|{rid}
    display=[]
    for f in source_figures:
        exact=rid in f['record_links']
        context_link=bool(linked_contexts.intersection(f['record_links']))
        relationship='explicit_record_link' if exact else 'linked_evidence_context' if context_link else 'same_source_study_context'
        # Even explicit record links do not certify a physical specimen/batch join.
        scope_label='Linked source evidence' if exact or context_link else 'Study-level comparison'
        scope=f['scope']
        if not exact and not context_link:scope='Study-level evidence; exact recipe/specimen assignment is not established. '+scope
        for category in f['categories']:
            display.append({**f,'category':category,'record_link':rid if exact else None,
              'relationship':relationship,'scope_label':scope_label,'scope':scope,
              'same_batch_asserted':False,'gallery_key':f"{sid}:{f['id']}:{category}"})
    # Short list remains exact. The full list retains every named product field;
    # no repeated variants are merged and no extrema or averages are computed.
    primary=[f for f in product_facts if f['kind'] in ['composition','phase','morphology']]
    primary.sort(key=lambda f:(f['recipe_link']!='explicit', f['kind']=='composition'))
    shortlist=[];seen=set()
    for f in primary:
        # Identical text may be shown once only with that exact first sample scope.
        key=(f['kind'],str(f['value']))
        if key in seen:continue
        seen.add(key);shortlist.append(f)
        if len(shortlist)==4:break
    target=r.get('intended_target',{}).get('composition',{})
    records[rid]={'source_id':sid,'title':r['title'],'material_formula':r.get('material',{}).get('formula'),
      'productFacts':product_facts,'featuredProductFacts':shortlist,'allProductFacts':product_facts,'productContexts':contexts,
      'primary_product':{'samples':contexts,'default_sample_id':next((p['sample_id'] for p in contexts if any(f['sample_id']==p['sample_id'] for f in product_facts)),contexts[0]['sample_id'] if contexts else None)},
      'nominalTarget':{'label':'Nominal synthesis target','value':target.get('value'),
       'scope':'Target composition; not substituted for an unknown product composition.',
       'source':source(path,'/intended_target/composition')},
      'figures':display,'intuition':intuitions.get(sid,[]),
      'scopeLabel':'Distinct route; source-defined variants and specimens remain separate.',
      'source':source(path,''),'data_links':{'record':f'data/records/{rid}.json','record_page':f'records/{rid}.html?view=data',
        'full_review':f'paper-review.html?id={sid}' if sid in REVIEWS else ('murray-1993-characterization.html' if sid=='murray1993' else 'alivisatos-2000-evidence.html' if sid=='peng2000' else None),
        'full_review_data':f'data/paper-reviews/{sid}.json' if sid in REVIEWS else None},
      'availability':{'figures':'available' if display else 'no_reviewed_figure_mapping_available',
        'intuition':'available' if intuitions.get(sid) else 'no_reviewed_explanation_selected',
        'product_facts':'available' if shortlist else 'no_named_nonnull_product_facts'}}

# Explicit illustration contexts expose existing figure specimens, not new batch joins.
morphology_path=SITE/'dist/data/reader-morphology-interpretations.json'
if morphology_path.exists():
    morphology=read(morphology_path)
    for key,item in morphology['entries'].items():
        if sha(SITE/item['source_hash_scope'])!=item['source_sha256']:
            raise ValueError('Morphology interpretation requires source recheck: '+key)
    for rid,extensions in morphology.get('additional_contexts',{}).items():
        for extension in extensions:
            source_id=extension['record_id'];source_record=ALL_RECORDS[source_id]
            if source_record['lineage']['source_group']!=records[rid]['source_id']:
                raise ValueError('Cross-source morphology context: '+rid)
            facts,contexts=products(source_record,f'data/records/{source_id}.json')
            selected=set(extension['sample_ids'])
            if not selected.issubset({c['sample_id'] for c in contexts}):
                raise ValueError('Missing morphology specimen: '+source_id)
            for context in contexts:
                if context['sample_id'] not in selected:continue
                context['record_id']=source_id
                context['label']+=' · '+extension['scope_label']
                records[rid]['productContexts'].append(context)
            records[rid]['allProductFacts'].extend(f for f in facts if f['sample_id'] in selected)

materials={hid:{'id':hid,'formula':h['formula'],'record_ids':h['record_ids'],
    'component_only':h.get('component_only',False),
    'scopeLabel':('Component in a reported architecture; route results and figures describe their original specimen, not this component in isolation.' if h.get('component_only') else 'Source-specific methods and samples are kept separate.'),
    'source':source(f'dist/data/materials/{hid}.json',''),
    'figure_count':len({(f['source_id'],f['id']) for rid in h['record_ids'] for f in records[rid]['figures']}),
    'property_figure_count':len({(f['source_id'],f['id']) for rid in h['record_ids'] for f in records[rid]['figures'] if f['category']=='property'})}
    for hid,h in HUBS.items()}

output={'schema_version':'1.0','status':'integrated_reader_metadata','input_policy':'Existing reviewed site data only; no new scientific claims, sample joins, training eligibility or publication approval.',
 'classification_policy':'A figure with structural and property panels appears in both galleries using the same original asset and scope. The complete reviewed caption and sample qualifications remain available.',
 'records':records,'materials':materials,'figures_by_source':figures,
 'counts':{'materials':len(materials),'routes':len(records),'source_groups':len({r['source_id'] for r in records.values()}),
   'unique_figures':sum(len(v) for v in figures.values()),'full_readers':len(REVIEWS),'selected_evidence_readers':len(LEGACY),
   'legacy_readers':2,'figures_with_public_asset':sum(bool(f['public_asset']) for fs in figures.values() for f in fs)}}
write('reader-presentation.json',output)
(SITE/'dist/data/reader-presentation.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
write('input-manifest.json',{'files':[{'path':p,'sha256':h} for p,h in sorted(INPUTS.items())]})
print(json.dumps(output['counts']))
print('reader-presentation sha256',sha(HERE/'reader-presentation.json'))
