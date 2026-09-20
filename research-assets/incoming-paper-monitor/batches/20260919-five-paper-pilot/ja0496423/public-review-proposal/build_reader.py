"""Gu 2004 private reader from audited source units and immutable canonical records.

Writes only beside this helper. Does not copy source PDFs, mutate records, publish,
generate molecular geometry, or promote any presentation/binding review flags.
"""
from pathlib import Path
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib, json, re

O=Path(__file__).resolve().parent
B=O.parent
SITE=Path(r'[local path redacted]')
SID='gu2004';P='gu-2004-'
def read(p): return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,x): (O/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def uniq(xs): return list({json.dumps(x,sort_keys=True,ensure_ascii=False):x for x in xs}.values())
def resolve(obj,pointer):
    for part in pointer.strip('/').split('/') if pointer else []:
        part=part.replace('~1','/').replace('~0','~')
        obj=obj[int(part)] if isinstance(obj,list) else obj[part]
    return obj

inv=read(B/'source-inventory.json');facts_source=read(B/'source-facts.json')
source_links=read(B/'canonical-source-coverage.json')
manifest=read(B/'canonical-record-manifest.json')
crop_manifest=read(B/'reader-assets/crop-manifest.json')
records={p.stem:read(p) for p in sorted((B/'canonical-drafts').glob('*.json'))}
frozen={str(p):sha(p) for p in list((B/'canonical-drafts').glob('*.json'))+
        [B/'source-inventory.json',B/'source-facts.json',B/'canonical-source-coverage.json',B/'canonical-record-manifest.json',B/'reader-assets/crop-manifest.json']}
unit_by_id={u['id']:u for u in inv['units']}
unit_links={u['source_unit_id']:u['canonical_bindings'] for u in source_links['source_units']}
sections=[{'id':i,'title':t,'items':[]} for i,t in [('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and limitations')]]
items={};unit_to_items={u['id']:[] for u in inv['units']}
SCOPE={
 'source_cohort':'Source labels 1–4 identify preparation stages. Matching labels across techniques do not establish an identical physical batch or aliquot.',
 'method_context':'Preparation or acquisition context. Missing conditions remain missing; a procedure or measurement is not an additional synthesis experiment.',
 'model_context':'Original authors’ model, interpretation or proposed extension; not an independently measured interface, validated kinetic trajectory or new recipe.',
 'cited_context':'Bibliographic context in this paper. External works have not been inspected as part of this source bundle.',
 'source_metadata':'Source identity, coverage or administrative context; not an experimental result.',
 'curator_interpretation':'Evidence limitation or unresolved source inconsistency, preserved without silently filling or correcting historical fields.'}

TITLES={
 'identity-title':'Paper identity', 'identity-dates-affiliation':'Publication dates and affiliations',
 'si-identity':'Supporting-information identity','si-declaration':'Scope of the supplied supporting information','acknowledgments':'Acknowledgments',
 'overview-size':'Overall heterodimer size descriptions','introduction-motivation':'Motivation for magnetic–semiconductor heterodimers',
 'scheme-stages':'Proposed stages 1–4','one-pot-mechanism':'Crystallization-driven dewetting hypothesis',
 'upstream-cited-fept':'FePt preparation and its cited precedent','no-intermediate-isolation':'Continuous one-pot lineage',
 'reaction-atmosphere':'Reaction and storage atmospheres','intermediate-isolation-failure':'Isolation limits for proposed shell intermediates',
 'fept-tem-size':'FePt precursor diameter','fept-saed-claim':'FePt-1 diffraction assignment and missing pattern',
 'final-tem-dimensions':'Final FePt and CdS domain dimensions','final-cds-crystallinity':'HRTEM evidence for crystalline CdS',
 'final-saed-phases':'Actual SAED: CdS and FePt phase assignments','final-xrf-ratio':'Main-text XRF composition ratios',
 'sulfur-junction':'Proposed sulfur-containing junction','property-conservation-rationale':'Component-function preservation hypothesis',
 'magnetic-timing':'Timing and specimen limitations of magnetometry','magnetic-zfc-fc':'Blocking temperature of heterodimer 4',
 'magnetic-weak-interactions':'Interpretation of magnetic size uniformity and weak interactions','magnetic-equation':'Author estimate of magnetic anisotropy',
 'anisotropy-comparison':'Comparison of magnetic anisotropy','hysteresis':'Low-temperature hysteresis and coercivity',
 'optical-fept-band':'FePt-assigned absorption band','optical-cds-shoulder':'CdS-assigned absorption shoulder',
 'photoluminescence-result':'Photoluminescence of heterodimer 4','quantum-yield-standard':'Quantum-yield reference and acquisition limits',
 'blue-photograph':'Photograph of blue emission','outlook':'Authors’ outlook for functional heterostructures',
 'figure-1a':'Figure 1A: TEM of FePt 1','figure-1b':'Figure 1B: TEM of heterodimer 4','figure-1c':'Figure 1C: HRTEM of heterodimer 4','figure-1d':'Figure 1D: indexed electron diffraction of 4',
 'figure-2a':'Figure 2A: ZFC/FC and inverse-moment inset','figure-2b':'Figure 2B: magnetic field sweep','figure-2c':'Figure 2C: absorption and fluorescence','figure-2d':'Figure 2D: original fluorescence photograph',
 'figure-s1':'Figure S-1: XRF and software analysis inset','figure-s2':'Figure S-2: FePt-1 absorption control','figure-s3':'Figure S-3: FePt-1 magnetic control','figure-s4':'Figure S-4: isolated intermediate 2','figure-s5':'Figure S-5: isolated intermediate 3',
 'xrf-table-ratio-gap':'Unresolved main/SI XRF discrepancy',
 'gap-no-exact-atomic-structure':'Atomic structure and coordinate-file availability','gap-no-extra-techniques':'Techniques absent from the supplied source',
 'gap-sample-link-limits':'Physical sample and aliquot identity limits','gap-synthesis-apparatus-gaps':'Unreported synthesis apparatus and conditions',
 'gap-precursor-missingness':'Precursor identity and purification gaps','gap-workup-missingness':'Workup and storage gaps',
 'gap-measurement-missingness':'Measurement and calibration gaps','gap-mechanism-not-proven':'Limits of the proposed mechanism','gap-no-replicate-counts':'Replicates and raw numerical data'}
for sym in ['si','s','fe','rh','cd','pt']:TITLES['xrf-table-'+sym]='XRF inset: '+{'si':'Si','s':'S','fe':'Fe','rh':'Rh','cd':'Cd','pt':'Pt'}[sym]
for m in inv['materials']:
    title=m['name_as_reported']
    if m['source_unit_id']=='gu2004-chemical-water':title='Water: dissolution and recrystallization'
    TITLES[m['source_unit_id'].removeprefix(SID+'-')]=title
for rid,r in records.items():
    for op in r['operations']:
        if op['id'].startswith(('cdacac-','hetero-')):TITLES[op['id']]=op['label']

PROPERTIES=set('magnetic-timing magnetic-zfc-fc magnetic-weak-interactions hysteresis optical-fept-band optical-cds-shoulder photoluminescence-result quantum-yield-standard blue-photograph figure-2a figure-2b figure-2c figure-2d figure-s2 figure-s3'.split())
INTUITION=set('introduction-motivation one-pot-mechanism intermediate-isolation-failure sulfur-junction property-conservation-rationale magnetic-equation anisotropy-comparison outlook'.split())
STRUCTURES=set('overview-size fept-tem-size fept-saed-claim final-tem-dimensions final-cds-crystallinity final-saed-phases final-xrf-ratio figure-1a figure-1b figure-1c figure-1d figure-s1 figure-s4 figure-s5 xrf-table-si xrf-table-s xrf-table-fe xrf-table-rh xrf-table-cd xrf-table-pt xrf-table-ratio-gap gap-no-exact-atomic-structure'.split())
def section_for(key):
    if key.startswith(('chemical-','cdacac-')):return 'precursors'
    if key.startswith('hetero-') or key in ['reaction-atmosphere','scheme-stages','upstream-cited-fept','no-intermediate-isolation']:return 'protocol'
    if key in STRUCTURES:return 'structures'
    if key in PROPERTIES:return 'properties'
    if key in INTUITION:return 'intuition'
    return 'sources'
def evidence(u):
    role=u['source_role'];n=u['pdf_page']
    return {'source_id':SID,'document_role':role,'pdf_page':n,'printed_page':u['printed_page'],
            'locator':f'{"SI" if role=="si" else "Main"} PDF p. {n}, {u["locator"]}'}
def canonical_evidence(es):
    out=[]
    for e in es:
        match=re.search(r'(Main|SI) PDF p\. (\d+)',e['locator']);role='si' if match and match[1]=='SI' else 'main';n=int(match[2]) if match else None
        out.append({'source_id':SID,'document_role':role,'pdf_page':n,'printed_page':('S'+str(n) if role=='si' else str(5663+n)) if n else None,'locator':e['locator']})
    return out
def add(sec,key,title,text,uids,scope='source_cohort',claim_type='reported_source_fact'):
    assert key not in items
    es=uniq([evidence(unit_by_id[u]) for u in uids])
    item={'id':key,'title':title,'text':text,'claim_type':claim_type,
          'sample_scope':{'formulations':[],'physical_batch_id':None,'scope_kind':scope,'state':title,'link_limit':SCOPE[scope]},
          'evidence':es,'source_locators':[e['locator'] for e in es],'canonical_links':[],
          'notes':[],'facts':[],'source_audit_unit_ids':list(uids),'source_fact_ids':[],
          'training_eligible':False}
    items[key]=item;next(s for s in sections if s['id']==sec)['items'].append(item)
    for u in uids:unit_to_items[u].append(key)
    return item

for u in inv['units']:
    key=u['id'].removeprefix(SID+'-');kind=u['kind'];scope='source_cohort'
    if kind in ['metadata','source_scope']:scope='source_metadata'
    elif kind in ['operation','chemical_inventory','condition','acquisition','upstream_context','lineage']:scope='method_context'
    elif kind in ['author_interpretation','author_model','author_outlook','scheme','comparison','control_or_limitation']:scope='model_context'
    elif kind in ['reference','literature_context']:scope='cited_context'
    elif kind in ['source_conflict','missingness']:scope='curator_interpretation'
    title=TITLES.get(key)
    if title is None and key.startswith('reference-'):
        title=('SI reference ' if key.startswith('reference-si-') else 'Main reference ')+key.split('-')[-1]
    assert title is not None,('Unspecified academic title',key)
    # Existing source unit claims are audited curator paraphrases, not copied full text.
    text=u['claim'].replace('in this task','in this source review').replace('in this extraction','in this source review')
    item=add(section_for(key),key,title,text,[u['id']],scope,kind)
    for link in unit_links[u['id']]:item['canonical_links'].append({'record_id':link['record_id'],'json_pointer':link['pointer'],'relation':SCOPE[scope]})

for key,notes in {
 'chemical-oleylamine':['Gu reports 97% oleylamine without a geometric-isomer assay. A cis/Z reference molecule does not establish the batch isomer composition; unrelated 70% registry notes do not apply.'],
 'chemical-diol':['Technical 90% reagent: a molecular viewer may represent the named diol component only. No R/S composition is reported.'],
 'chemical-topo':['Technical 90% reagent is a mixture. A pure TOPO reference formula and molecular model do not specify the unidentified fraction.'],
 'chemical-hexane':['The source says hexane. An n-hexane model would be an explicitly illustrative isomer reference, not verified reagent-isomer composition.'],
 'chemical-water':['Only the CdCl2 dissolution water is explicitly deionized; the recrystallization-water grade is not stated.'],
 'chemical-nitrogen':['Nitrogen is explicit for storage only. Molecular visualization qualification is separate from gas-flow, pressure and chemical-atmosphere reporting.'],
 'fept-saed-claim':['The reachable original Figure 1D is the diffraction pattern of final heterodimer 4; it must not be relabeled as the missing separate precursor-1 pattern.'],
 'figure-s4':['Isolation-damage caveat: the imaged residue is not proof of an intact uniform FePt@S shell.'],
 'figure-s5':['Isolation-damage caveat: the imaged residue is not proof of an intact uniform FePt@CdS shell.'],
 'gap-no-exact-atomic-structure':['No CIF or atomic interface download is supplied by this reader. A future bulk reference would need independent provenance and an explicit reference-only label.'],
 'reference-main-7':['This is an internal reference to the matched SI. Its scope does not establish additional unsupplied images.']}.items():items[key]['notes'].extend(notes)

for material in inv['materials']:
    uid=material['source_unit_id'];key=uid.removeprefix(SID+'-')
    b=unit_links[uid][0];m=resolve(records[b['record_id']],b['pointer'])
    formula=m.get('formula')
    items[key]['notes'].append('Formula: '+formula+'.' if formula else 'A single molecular formula is not assigned to this source reagent mixture.')
    items[key]['material_identity']={'source_material_id':material['id'],'name':m['name'],'formula':formula,
        'canonical_record_id':b['record_id'],'json_pointer':b['pointer'],'exact_molecular_asset_binding_approved':False}

QFIELDS={'value','minimum','maximum','unit','status'}
def quantity_display(q):
    if q.get('value') is not None:return q['value']
    lo,hi=q.get('minimum'),q.get('maximum')
    if lo is not None and hi is not None:return f'{lo:g}–{hi:g}'
    if lo is not None:return ('> ' if q.get('minimum_exclusive') else '≥ ')+f'{lo:g}'
    if hi is not None:return ('< ' if q.get('maximum_exclusive') else '≤ ')+f'{hi:g}'
    return 'Not reported' if q.get('status')=='not_reported' else q.get('raw_text') or q.get('status','Unspecified')
def attach_fact(key,rid,pointer,identifier,label,q,es,basis,sample=None,extra=None):
    ii=items[key];ee=canonical_evidence(es)
    f={'id':rid+'::'+identifier,'label':label,'value':quantity_display(q),'unit':q.get('unit'),
       'approximate':q.get('approximate',False),'status':q.get('status'),'basis':basis,
       'qualifier':' '.join(str(x) for x in [q.get('basis'),q.get('qualifier'),q.get('note'),extra] if x),
       'evidence':ee,'canonical_record_id':rid,'json_pointer':pointer,'canonical_quantity':deepcopy(q),'training_eligible':False}
    if sample:f['sample_id']=sample
    ii['facts'].append(f);ii['canonical_links'].append({'record_id':rid,'json_pointer':pointer,'relation':SCOPE[ii['sample_scope']['scope_kind']]})
    ii['evidence']=uniq(ii['evidence']+ee);ii['source_locators']=uniq(ii['source_locators']+[e['locator'] for e in ee])
    return f

# Audited source bindings determine exact quantitative destinations. A source
# aggregate may bind multiple scalar components; none is silently recomputed.
targets=defaultdict(list)
for row in source_links['facts']:
    key=row['source_fact']['source_unit_id'].removeprefix(SID+'-')
    for b in row['canonical_bindings']:targets[(b['record_id'],b['pointer'])].append(key)
for row in source_links['source_units']:
    key=row['source_unit_id'].removeprefix(SID+'-')
    for b in row['canonical_bindings']:targets[(b['record_id'],b['pointer'])].append(key)
def target_exact(rid,pointer):
    vals=targets.get((rid,pointer),[])
    assert vals,('No audited source binding',rid,pointer)
    return vals[0]

measurement_map={};operation_map={};parameter_map={};material_map={};stock_map={}
for rid,r in records.items():
    for n,m in enumerate(r['measurements']):
        ptr=f'/measurements/{n}';key=target_exact(rid,ptr+'/value')
        f=attach_fact(key,rid,ptr,m['id'],m['property'].replace('_',' ').capitalize(),m['value'],m['evidence'],
                      'canonical_'+m['value'].get('status','reported'),m['sample_id'],m.get('conditions'))
        f['canonical_measurement_id']=m['id'];measurement_map[rid+'::'+m['id']]=key
    for n,mat in enumerate(r['materials']):
        for name,q in mat.get('quantities',{}).items():
            ptr=f'/materials/{n}/quantities/{name}';key=target_exact(rid,ptr)
            f=attach_fact(key,rid,ptr,'material-'+mat['id']+'-'+name,mat['name']+' · '+name.replace('_',' '),q,q.get('evidence',mat['evidence']),'reagent_specification')
            f['canonical_material_id']=mat['id'];material_map[rid+'::'+mat['id']+'::'+name]=key
    assert not r.get('stocks'), 'Add explicit stock mapping if a new audited stock record appears.'

ANALYTICAL_UNITS={
 ('microscopy','tem'):['fept-tem-size','final-tem-dimensions','figure-1a','figure-1b','figure-s4','figure-s5','gap-measurement-missingness'],
 ('microscopy','hrtem'):['final-cds-crystallinity','figure-1c'],
 ('microscopy','saed'):['final-saed-phases','figure-1d'],
 ('xrf','xrf'):['final-xrf-ratio','figure-s1','xrf-table-ratio-gap'],
 ('magnetometry','zfc-fc'):['magnetic-timing','magnetic-zfc-fc','figure-2a'],
 ('magnetometry','hysteresis'):['hysteresis','figure-2b'],
 ('optical','absorption'):['optical-fept-band','optical-cds-shoulder','figure-2c'],
 ('optical','fluorescence'):['photoluminescence-result','figure-2c'],
 ('optical','quantum-yield'):['quantum-yield-standard','photoluminescence-result'],
 ('optical','uv-photograph'):['blue-photograph','figure-2d'],
 ('fept-control','absorption'):['figure-s2'],
 ('fept-control','zfc-fc'):['figure-s3']}
for rid,r in records.items():
    suffix=rid.removeprefix(P)
    for n,op in enumerate(r['operations']):
        ptr=f'/operations/{n}'
        if op['id'].startswith(('cdacac-','hetero-')):key=op['id']
        else:
            key=f'method-{suffix}-{op["id"]}'
            ids=[SID+'-'+x for x in ANALYTICAL_UNITS[(suffix,op['id'])]]
            add('structures' if suffix in ['microscopy','xrf'] else 'properties',key,op['label'],op['description'],ids,'method_context','source_acquisition_procedure')
        ii=items[key];ii['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Exact canonical operation; retain source-stage and acquisition-specimen distinctions.'})
        ii['operation_context']={'record_id':rid,'operation_id':op['id'],'environment':deepcopy(op.get('environment')),'inputs':deepcopy(op.get('inputs')),'outputs':deepcopy(op.get('outputs')),'condition_options':deepcopy(op.get('condition_options',[]))}
        operation_map[rid+'::'+op['id']]=key
        for name,q in op.get('parameters',{}).items():
            f=attach_fact(key,rid,ptr+'/parameters/'+name,'operation-'+op['id']+'-'+name,op['label']+' · '+name.replace('_',' '),q,q.get('evidence',op['evidence']),'operation_parameter',extra=op.get('description'))
            f['canonical_operation_id']=op['id'];f['canonical_parameter']=name
            parameter_map[rid+'::'+op['id']+'::'+name]=key
        if op.get('environment'):
            env=op['environment']
            ii['notes'].append('Atmosphere: '+str(env.get('value') or 'not reported')+'. '+env.get('note',''))

# Bind original source facts to every resolved reader destination without altering
# raw arrays, unreported values, approximations or model-derived status.
source_fact_mapping={}
for row in source_links['facts']:
    key=row['source_fact']['source_unit_id'].removeprefix(SID+'-')
    items[key]['source_fact_ids'].append(row['source_fact_id'])
    links=[]
    for b in row['canonical_bindings']:
        ptr=b['pointer'];rid=b['record_id']
        matches=[(ii['id'],f) for ii in items.values() for f in ii['facts'] if f['canonical_record_id']==rid and (f['json_pointer']==ptr or f['json_pointer']+'/value'==ptr)]
        assert len(matches)==1,(row['source_fact_id'],b,len(matches))
        target,f=matches[0]
        f.setdefault('source_fact_ids',[]).append(row['source_fact_id'])
        if row['source_fact_id'] not in items[target]['source_fact_ids']:items[target]['source_fact_ids'].append(row['source_fact_id'])
        links.append({**b,'reader_item_id':target,'reader_fact_id':f['id']})
    source_fact_mapping[row['source_fact_id']]={'source_unit_id':row['source_fact']['source_unit_id'],'reader_item_ids':list(dict.fromkeys([key]+[b['reader_item_id'] for b in links])),'canonical_bindings':links}

# All source-stage labels stay paired to their record ID; 'stage-4' never serves
# as an implicit global batch ID for microscopy, magnetometry and optical samples.
for ii in items.values():
    joins=[]
    for f in ii['facts']:
        if not f.get('sample_id'):continue
        rid=f['canonical_record_id'];sample=f['sample_id']
        n=next(n for n,p in enumerate(records[rid]['products']) if p['sample_id']==sample)
        joins.append({'record_id':rid,'sample_id':sample,'json_pointer':f'/products/{n}',
                      'source_label':records[rid]['products'][n]['source_sample_label'],'relation':SCOPE[ii['sample_scope']['scope_kind']]})
    joins=uniq(joins)
    ii['sample_scope']['formulations']=[j['record_id']+' / '+j['sample_id'] for j in joins]
    ii['sample_scope']['canonical_sample_links']=joins
    ii['canonical_links']=uniq(ii['canonical_links'])

# All twelve original crops remain reachable from their evidence items and the
# source appendix. Figure-specific specimen links exclude unrelated controls.
ASSET_SAMPLES={
 'scheme-1':[('mechanism','source-model')],
 'figure-1':[('microscopy',x) for x in ['tem-1','tem-4','hrtem-4','saed-4']],
 'figure-2':[('magnetometry','zfc-fc-4'),('magnetometry','hysteresis-4')]+[('optical',x) for x in ['absorption-4','fluorescence-4','yield-4','photograph-4']],
 'magnetic-model':[('magnetic-model','model-context'),('optical','absorption-4'),('optical','fluorescence-4')],
 'si-general':[], 'si-cdacac-preparation':[('cdacac-preparation','cdacac-isolate'),('cdacac-preparation','cdacac-dried')],
 'si-heterodimer-preparation':[('heterodimer',x) for x in ['stage-1','stage-2','stage-3','stage-4']],
 'figure-s1':[('xrf','si-software')],'figure-s2':[('fept-control','absorption-1')],'figure-s3':[('fept-control','zfc-fc-1')],
 'figure-s4':[('microscopy','tem-2')],'figure-s5':[('microscopy','tem-3')]}
ASSET_EXTRA={
 'figure-1':['A: FePt 1 TEM, 5 nm scale. B: final 4 TEM, 10 nm scale. C: final 4 HRTEM, 5 nm scale. D: actual final-product EDP/SAED with indexed CdS and FePt rings.','No separate SAED image of FePt 1 is located in the supplied SI.'],
 'figure-2':['A: 4 at 100 Oe; m in 10⁻⁵ emu versus temperature, with inverse-moment inset. B: 4 at 5 K; the printed field axis is Hc (kOe).','C: separate absorbance/fluorescence axes; 365 nm excitation. D: original UV-lamp photograph; the lamp wavelength is unreported.'],
 'figure-s1':['The six inset rows and their line/energy/mol% labels are retained. Rh mol% and all Type cells are blank, not zero.','Si/Rh origins and correction procedures are unreported. Raw software mol% are not adopted as product dopant fractions or silently normalized to the main ratio.'],
 'figure-s2':['FePt 1 in hexane, not final heterodimer 4. No numerical precursor peak is transcribed from a visual estimate.'],
 'figure-s3':['FePt 1 comparison; SI gives no applied field or exact fitted blocking temperature. The final-product 100 Oe condition does not transfer.'],
 'figure-s4':['Isolated intermediate 2: S and FePt arrows, 2 nm scale. Shell impairment during isolation is an author explanation.'],
 'figure-s5':['Isolated intermediate 3: CdS and FePt arrows, 20 nm scale. No intact-shell thickness or yield is established.'],
 'magnetic-model':['Original equation and surrounding magnetic/optical paragraphs. Anisotropy is author-derived; no new fit or digitization.'],
 'scheme-1':['Conceptual shells and domain shapes are author hypotheses; not atomic geometry or independent intermediate synthesis runs.']}
groups={k:[] for k in ['figures','tables','schemes','equations','source_notes']};assets={};private_assets=[]
for a in crop_manifest['assets']:
    key=a['id'].removeprefix(SID+'-')
    group='figures' if key.startswith('figure-') else 'schemes' if key=='scheme-1' else 'equations' if key=='magnetic-model' else 'source_notes'
    refs=[{'record_id':P+r,'sample_id':s,'relation':'Source-defined specimen or model context; physical batch joins across techniques remain unassigned.'} for r,s in ASSET_SAMPLES[key]]
    scope=a['caption_scope'];path='assets/figures/gu2004/'+Path(a['path']).name
    aa={'id':a['id'],'label':a['locator'],'document_role':a['source_role'],'page':a['pdf_page'],'printed_page':a['printed_page'],
        'caption_paraphrase':scope,'sample_scope':scope,'sample_links':list(dict.fromkeys(j['record_id'] for j in refs)),
        'canonical_sample_links':refs,'sample_linkage':'Source-stage associations only. The four preparation labels and each analytical record preserve their individual context; no common physical batch is inferred.',
        'evidence_class':'author_model' if group in ['schemes','equations'] else 'direct_source_excerpt' if group=='source_notes' else 'original_experimental_figure',
        'public_asset':path,'public_asset_sha256':a['sha256'],
        'asset_provenance':{'source_file':Path(a['source_path']).name,'source_sha256':a['source_sha256'],'source_pdf_page':a['pdf_page'],
                            'crop_normalized':a['normalized_bbox'],'crop_pixel_bbox':a['pixel_bbox'],'render_dpi':a['render_dpi'],
                            'pixel_dimensions':a['asset_dimensions'],'renderer':a['renderer'],'transformation':'Original source crop; no redraw, retouching or numerical trace digitization.'},
        'notes':ASSET_EXTRA.get(key,[]),'panels':[], 'source_locators':[f'{a["source_role"]} PDF p. {a["pdf_page"]}, {a["locator"]}'],
        'source_unit_ids':a['source_unit_ids'],'text_reviewed':True,'visual_reviewed':True,
        'reviewed':False,'reader_render_verified':False,'training_eligible':False}
    if key=='si-general':aa['sample_links']=[P+'cdacac-preparation',P+'heterodimer',P+'optical']
    groups[group].append(aa);assets[a['id']]=aa
    private_assets.append({'id':a['id'],'private_path':a['path'],'public_asset':path,'sha256':a['sha256'],'reviewed':False,'reader_render_verified':False})
    for uid in a['source_unit_ids']:
        for item_id in unit_to_items[uid]:
            item=items[item_id];item.setdefault('original_assets',[]).append({'id':a['id'],'label':'Original '+a['locator'],'public_asset':path,'public_asset_sha256':a['sha256']})

# The XRF table is an embedded region of the supplied Figure S-1 crop, not a
# separately fabricated asset. Exact machine facts already link all six rows.
table=deepcopy(assets['gu2004-figure-s1']);table.update({'id':'gu2004-xrf-inset-table','label':'Figure S-1 analysis inset','caption_paraphrase':'Six original software rows; energy heading omits units, interpreted only from the surrounding keV spectrum. Main and SI quantification remain unresolved.','row_count':6,'source_asset_type':'embedded_table_in_figure'})
table['source_unit_ids']=[SID+'-xrf-table-'+x for x in ['si','s','fe','rh','cd','pt']]+[SID+'-xrf-table-ratio-gap']
groups['tables'].append(table)

# Upstream precursor preparation is discoverable from the reagent entry as well
# as its six ordered steps, without treating it as a second FePt–CdS route.
items['chemical-cadmium-acac']['canonical_links'].append({'record_id':P+'cdacac-preparation','json_pointer':'','relation':'Complete source-supplied upstream precursor preparation; separate from the sole heterodimer route.'})
items['chemical-cadmium-acac']['original_assets']=[{'id':'gu2004-si-cdacac-preparation','label':'Original Cd(acac)2 preparation','public_asset':assets['gu2004-si-cdacac-preparation']['public_asset'],'public_asset_sha256':assets['gu2004-si-cdacac-preparation']['public_asset_sha256']}]
items['upstream-cited-fept']['notes'].append('Sun et al. (2000) is an uninspected external precedent in this review; Gu’s supplied SI provides the actual amounts and procedure shown here.')
for ii in items.values():ii['original_assets']=uniq(ii.get('original_assets',[]))

docs=[]
for role,d in inv['source_documents'].items():
    docs.append({'role':role,'filename':d['filename'],'sha256':d['sha256'],'page_count':d['page_count'],
                 'pages':[{'page':n,'printed_page':str(5663+n) if role=='main' else 'S'+str(n),'text_read':True,'visual_review':True,
                           'sections':['Complete supplied page read and visually inspected in the source extraction; source scientific audit passed separately.']} for n in range(1,d['page_count']+1)]})
corp=next(p for p in read(SITE/'data/corpus/library-source.json')['papers'] if p.get('doi','').lower()==inv['doi'].lower())
counts={'reader_items':len(items),'source_audit_units':len(unit_to_items),'source_facts':len(source_fact_mapping),'records':len(records),
        'record_types':dict(Counter(r['record_type'] for r in records.values())),'linked_operations':len(operation_map),
        'typed_characterization_rows':len(measurement_map),'operation_parameter_facts':len(parameter_map),'reagent_quantity_facts':len(material_map),'stock_quantity_facts':len(stock_map),
        'typed_facts':sum(len(i['facts']) for i in items.values()),'main_figures':2,'si_figures':5,'figures':7,'tables':1,'table_rows':6,
        'schemes':1,'numbered_equations':0,'inline_equation_groups':1,'source_notes':3,'original_assets':len(assets),
        'references_and_notes':len(inv['references']),'external_works_uninspected':25,'supplied_main_pages':2,'matched_si_pages':3}
gaps=[unit_by_id[SID+'-'+k]['claim'] for k in TITLES if k.startswith('gap-')]
out={'schema_version':'1.0','paper_id':SID,'doi':inv['doi'],'title':inv['title'],
     'paper':{'authors':['Hongwei Gu','Rongkun Zheng','XiXiang Zhang','Bing Xu'],'journal':'Journal of the American Chemical Society','year':2004,'volume':126,'pages':'5664–5665','online_publication_date':'2004-04-20'},
     'source_group':SID,'corpus_paper_id':corp['id'],'corpus_document_id':corp['titleMetadata']['evidenceDocumentId'],'corpus_document_ids':corp['documentIds'],
     'review_scope':'supplied_main_and_matched_si','supporting_information':{'status':'matched_and_reviewed','matched_local_si_count':1,'scientific_pages':3,'administrative_cover_pages':0,'scope':'Title, authors and experimental/figure content match the main article; all three supplied SI pages read and visually inspected. No additional supplement is established.'},
     'documents':docs,'document_identity_verification':{'method':'Actual source title, authors, DOI and content verified; source hashes bound to separately passed source audit. Original main and matched SI retained with their own identities.'},
     'coverage_status':'private_reader_proposal_pending_independent_audit','independent_audit':'Source extraction and canonical scientific audits passed separately. Reader prose, specimen links and presentation remain pending a separate independent review.',
     'publication_status':'Private proposal only; not integrated or published.','source_review_promoted':False,'training_eligible':False,
     'training_note':'One heterodimer synthesis route, a separate upstream precursor preparation and source-scoped analytical/model contexts. Missing quantities, unresolved XRF discrepancy and absent atomic coordinates remain explicit; no training admission is granted.',
     'recipe_inventory':[{'id':rid,'label':r['title'],'record_ids':[rid],'record_type':r['record_type'],'status':'canonical_source_audit_passed_presentation_pending','scope':'One source-defined preparation, acquisition, comparison or interpretation context. Records and figures are not independent synthesis replicates.','gaps':gaps if rid==P+'heterodimer' else ['Presentation and source-to-reader binding review pending.'],'canonical_draft_present':True} for rid,r in records.items()],
     'characterization_inventory':{'reader_item_ids':[i['id'] for s in sections if s['id'] in ['structures','properties'] for i in s['items']]},
     'chemical_intuition':{'reader_item_ids':[i['id'] for s in sections if s['id']=='intuition' for i in s['items']],'scope':'Original hypotheses and model estimates remain distinct from measured outcomes; cited external works are uninspected in this bundle.'},
     'reader_contract':{'version':'1.0','section_ids':[s['id'] for s in sections],'item_fields':['id','title','text','claim_type','sample_scope','evidence','source_locators','canonical_links','notes','facts','training_eligible']},
     'reader_sections':sections,**groups,
     'referenced_methods':[{'id':ref['id'],'citation':ref['citation_as_printed'],'context':ref['context'],'inspection_status':ref['access_status'],'reader_item_id':ref['source_unit_id'].removeprefix(SID+'-'),'doi':ref['doi']} for ref in inv['references']],
     'remaining_gaps':gaps+['Molecular, apparatus and crystal-context presentation/bindings are separate pending stages; this reader does not approve or claim those assets.'],
     'evidence_conflicts':[{'id':k,'text':items[k]['text'],'source_locators':items[k]['source_locators']} for k in ['xrf-table-ratio-gap','fept-saed-claim','figure-2b','gap-precursor-missingness','intermediate-isolation-failure']],
     'record_formulation_labels':{rid:[p['sample_id'] for p in r['products']] for rid,r in records.items()},
     'record_formulation_scope_note':'Pair every sample ID with its record. Source 1, 2, 3 and 4 identify stages, not universal physical batch IDs. Controls and author models retain their own context.',
     'material_evidence_records':{'FePt/CdS':list(records),'CdS':[P+x for x in ['heterodimer','microscopy','optical','xrf','mechanism','literature-context']],
                                  'FePt':[P+x for x in ['heterodimer','microscopy','fept-control','magnetometry','magnetic-model','xrf','mechanism','literature-context']]},
     'material_evidence_scope_notes':{'FePt/CdS':'Whole heterodimer contribution with upstream precursor preparation, labeled stages, comparisons and models; one final synthesis route.',
         'CdS':'CdS-domain context in FePt–CdS heterodimers, not an independently synthesized CdS material. FePt-assigned absorption and total XRF remain explicitly compound-study context.',
         'FePt':'FePt precursor and heterodimer-component context. Isolated FePt controls remain separate from final 4; magnetic model values are author estimates.'},
     'material_original_asset_ids':{'FePt/CdS':list(assets),'CdS':[SID+'-'+x for x in ['scheme-1','figure-1','figure-2','figure-s1','figure-s5','si-heterodimer-preparation']],
                                    'FePt':[SID+'-'+x for x in ['scheme-1','figure-1','figure-2','figure-s1','figure-s2','figure-s3','figure-s4','figure-s5','magnetic-model','si-heterodimer-preparation']]},
     'material_asset_scope_note':'Original multi-panel figures retain their complete captions and panel-specific labels. Their presence in a component context does not relabel whole-product or control measurements as standalone component properties.',
     'route_evidence_contexts':{P+'heterodimer':[P+x for x in ['cdacac-preparation','microscopy','xrf','magnetometry','optical','fept-control','magnetic-model','mechanism','literature-context']]},
     'counts':counts}

write('gu2004.json',out)
write('source-item-coverage.json',{'source_id':SID,'source_inventory_sha256':sha(B/'source-inventory.json'),'source_facts_sha256':sha(B/'source-facts.json'),'mapped_unit_count':len(unit_to_items),'unit_to_reader_items':unit_to_items,'unmapped_units':[],'fact_to_reader':source_fact_mapping})
write('canonical-measurement-coverage.json',{'measurement_count':len(measurement_map),'measurement_to_reader_item':measurement_map,'operation_count':len(operation_map),'operation_to_reader_item':operation_map,'operation_parameter_count':len(parameter_map),'operation_parameter_to_reader_item':parameter_map,'material_quantity_count':len(material_map),'material_quantity_to_reader_item':material_map,'stock_quantity_count':0,'stock_quantity_to_reader_item':{},'draft_sha256':{rid:sha(B/'canonical-drafts'/f'{rid}.json') for rid in records}})
write('reader-bindings-proposal.json',{'schema':'mattersyn-private-reader-bindings/1','source_id':SID,'status':'proposed_not_approved','reader_sha256':sha(O/'gu2004.json'),'source_fact_count':len(source_fact_mapping),'source_unit_count':len(unit_to_items),'canonical_records':{rid:sha(B/'canonical-drafts'/f'{rid}.json') for rid in records},'original_assets':private_assets,'operation_to_reader_item':operation_map,'molecular_or_apparatus_bindings_approved':False,'publication_approved':False})
write('reader-items-summary.json',[{'id':i['id'],'title':i['title'],'section':s['id'],'source_unit_ids':i['source_audit_unit_ids'],'facts':len(i['facts'])} for s in sections for i in s['items']])
assert all(sha(p)==h for p,h in frozen.items()),'Immutable source/canonical boundary changed.'
print(json.dumps(counts,ensure_ascii=False))
