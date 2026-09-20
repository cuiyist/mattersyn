"""Create a public-safe ledger proposal outside the Site; no publication or promotion."""
from pathlib import Path
from collections import Counter
import hashlib
import importlib.util
import json
import re
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
SITE=Path(r'[local path redacted]')
OUT=HERE/'public-review-proposal'
OUT.mkdir(exist_ok=True)
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
EVID=read(HERE/'reader-evidence.json')
COVER=read(HERE/'coverage-ledger.json')
STAGE=read(HERE/'source-extraction.json')
SPEC=read(HERE/'reader-integration-spec.json')
MAN=read(HERE/'crop-assets/manifest.json')
paths=[p for folder in ['canonical-drafts','procedure-drafts','context-drafts']for p in sorted((HERE/folder).glob('*.json'))]
RECORDS={read(p)['record_id']:read(p)for p in paths}
protected={str(p):sha(p) for p in paths+[HERE/'reader-evidence.json',HERE/'coverage-ledger.json',HERE/'source-extraction.json',HERE/'reader-integration-spec.json',HERE/'crop-assets/manifest.json']}
assert len(RECORDS)==13 and len(EVID['items'])==171
source=STAGE['source']
assert sha(Path(source['main_file']))==source['sha256']

SECTIONS=[('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),
          ('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and limitations')]
sections=[{'id':id,'title':title,'items':[]}for id,title in SECTIONS]
bytitle={s['title']:s for s in sections}
def loc(e):
    return f"Main PDF p. {e['pdf_page']}, printed p. {e['printed_page']}, {e['locator']}"
def evidence(items):
    return [{'source_id':'littau1993','locator':loc(e),'document_role':'main','pdf_page':e['pdf_page'],'printed_page':e['printed_page']}for e in items]
def ev(page,section):return {'source_id':'littau1993','locator':f'Main PDF p. {page}, printed p. {1223+page}, {section}','document_role':'main','pdf_page':page,'printed_page':1223+page}
def pointer(obj,p):
    for key in p.strip('/').split('/') if p else []:
        key=key.replace('~1','/').replace('~0','~')
        obj=obj[int(key)]if isinstance(obj,list)else obj[key]
    return obj
def clean(text):
    text=str(text).replace('cm3','cm³').replace('SiOx','SiOₓ').replace('SiO2','SiO₂')
    for a,b in [('MatchingSI','Matching SI'),('Acidicwater5%','The 5% acidic-water addition'),('AKS41 quantified','The quantified AKS41'),
                ('1.0 crystallinity','Crystallinity of the 1.0 formulation'),('CIF.','CIF.'),('13nm','13 nm'),('14nm','14 nm'),('3nm','3 nm'),
                ('355-nm','355 nm'),('picosecond355','picosecond 355'),('with10','with 10'),('fits17','fits of 17'),('and76','and 76'),
                ('76microseconds','76 microseconds'),('5.000%','5.000%'),('5%;','5%;')]:text=text.replace(a,b)
    return re.sub(r'\s+',' ',text).strip()

PAGE_SECTIONS={
1:['Title, authors, abstract and introduction','Figure 1: continuous aerosol apparatus','Experimental A: prior aerosol context'],
2:['Table I: formulation-specific characterization and activated luminescence','Experimental A: feed, pyrolysis, dilution, oxidation and collection','Experimental B: HPLC, TEM, optical and powder preparation'],
3:['Experimental B continuation: powder XRD','Results A: three stock-flow formulations and earlier AKS41 material','Figures 2–4: absorption, AKS41 TEM and HPLC','Mie optical-concentration calibration and Si mass accounting'],
4:['Results A: concentration, AKS41 particle/fraction analysis and 6.0 structure','Figures 5–7: 6.0 HPLC, 6.0/2.0 powder XRD and 6.0 IR','Source cross-reference errors and core/shell dimensions'],
5:['Figure 8: 1.0 HPLC; smaller-particle structure limitations','Lattice comparison, IR interpretation and optical absorption','Figure 9: as-made/activated 6.0 emission','Acidic activation and pH-dependent quenching'],
6:['Figures 10–12: activated 2.0/1.0 PL and 1.0 decay','HPLC-fraction reactivation, quantum-yield estimate and bulk-Si comparison','Results C: confinement/interface hypotheses, limits and outlook','Acknowledgments'],
7:['References 1–47','Reference note 36: column stability','Reference note 41: unwashed-powder impurities','Bibliographic context for calibration, modeling and silica chemistry']}
PAGE_GAPS={1:['Figure 1 labels 865 °C; Experimental A gives 860 °C.'],2:['Pressure reference, gas standard-volume conditions and several preparation quantities are not stated.'],
3:['AKS41 quantified synthesis is not supplied; optical-concentration and collection estimates are model-dependent.'],
4:['Different size definitions and population/individual-particle scopes must remain separate.'],
5:['No directly established crystalline-core structure for 1.0; pH/addition conventions and excitation conflict remain unresolved.'],
6:['Exact physical batch/fraction joins and decay-fit amplitudes/uncertainties are absent.'],
7:['Cited external works were not independently reviewed; bibliography inclusion is not imported experimental evidence.']}

paper={k:source[k]for k in ['doi','title','journal','year','volume','pages']}
paper.update(authors='; '.join(source['authors']),url='https://doi.org/'+source['doi'])
ledger={'schema_version':'1.0','paper_id':'littau1993','doi':source['doi'],'title':source['title'],'paper':paper,
        'source_group':'littau1993','corpus_paper_id':SPEC['paper']['existing_paper_id'],'corpus_document_id':SPEC['paper']['existing_document_id'],
        'review_scope':'supplied_main_only_si_unverified',
        'supporting_information':{'status':'not_located_or_verified','note':'Matching supporting information was not located or verified. This is a review of all supplied main-article pages; it does not establish that no supporting information exists.'},
        'documents':[{'role':'main','source_file':Path(source['main_file']).name,'sha256':source['sha256'],'page_count':7,
                      'identity_verification':'Printed title, authors, journal and pagination checked; DOI agrees with the supplied filename. The existing and incoming local copies have the same fingerprint.',
                      'pages':[{'page':n,'printed_page':1223+n,'text_read':True,'visual_review':True,'sections':PAGE_SECTIONS[n],'unresolved':PAGE_GAPS[n]}for n in range(1,8)]}],
        'document_identity_verification':'Reuse the existing corpus paper/document identity. The identical incoming copy is not a second paper. No main–SI match is claimed.',
        'coverage_status':'supplied_main_reviewed; public_reader_integration_and_visual_verification_pending',
        'independent_audit':'Source and bounded record-join audits completed; reader integration remains pending',
        'audit_details':'An independent review covered all seven supplied main pages and all thirteen final crops. Subsequent bounded scientific-join audits covered the three formulation drafts, nine supporting-procedure drafts and separate AKS41 context. These scopes do not establish laboratory reproduction, verified SI, rendered source-to-view completion or training eligibility.',
        'publication_status':'proposal_only_not_published','training_eligible':False,
        'training_note':'All thirteen linked records remain imported_unreviewed with no requested training tasks. This ledger does not promote records, model labels or publication status.',
        'recipe_inventory':[],'characterization_inventory':[],'figures':[],'tables':[],'equations':[],'schemes':[],
        'reader_sections':sections,'reader_item_coverage':[],'reader_exclusions':[]}
ledger['record_formulation_labels']={
    'littau-1993-si-aerosol-6p0':['6.0'],'littau-1993-si-aerosol-2p0':['2.0'],'littau-1993-si-aerosol-1p0':['1.0'],
    'littau-1993-si-acid-activation':['6.0','2.0','1.0'],
    'littau-1993-si-colloid-concentration':[], 'littau-1993-si-powder-preparation':[],
    'littau-1993-si-hplc-fractionation':['6.0','2.0','1.0','AKS41'],
    'littau-1993-si-tem-characterization':['6.0','2.0','1.0'],
    'littau-1993-si-ir-characterization':['6.0'],
    'littau-1993-si-xrd-characterization':['6.0','2.0','1.0'],
    'littau-1993-si-optical-characterization':['6.0','2.0','1.0'],
    'littau-1993-si-time-resolved-pl':['1.0'], 'littau-1993-aks41-context':['AKS41']}
ledger['record_formulation_scope_note']='Labels support contextual figure selection, not physical-batch identity. Concentration and powder preparation have unassigned input formulations. HPLC is a shared analytical procedure discussed across all four colloids; AKS41 remains an earlier-apparatus observation and is never assigned to a current aerosol recipe. TEM/XRD/optical procedure maps do not establish 1.0 crystallinity or a shared specimen across techniques.'

# Existing records remain separate: three formulations, nine procedures, one contextual observation.
for rid,r in RECORDS.items():
    typ=r['record_type']
    recordloc=[]
    for group in ['operations','measurements']:
        for obj in r[group]:
            for e in obj['evidence']:
                if e['locator']not in recordloc:recordloc.append(e['locator'])
    if not recordloc:
        recordloc=['Main PDF pp. 3–4, printed pp. 1226–1227, Results A and Figures 3–4']
    ledger['recipe_inventory'].append({'id':rid,'label':r['title'].split(' · ',1)[-1],'record_ids':[rid],
        'record_type':typ,'status':'audited_draft_pending_reader_integration','source_locators':recordloc,
        'gaps':[clean(x)for x in r['quality']['missing_fields']],
        'scope':'Supporting procedure, not an additional synthesis or independent batch.' if typ=='procedure' else
                'AKS41 observation from an earlier apparatus; no quantified synthesis reconstructed.' if typ=='observation' else
                'One stock-gas-flow formulation of the shared aerosol process; exact physical runs are not enumerated.'})

# Public reader content has a fixed field contract and no raw staging or machine paths.
TITLE={
 'source-stocks-0':'Disilane–helium stock','source-stocks-1':'Acidified water',
 'source-supporting_procedures-0':'Acid activation','source-supporting_procedures-1':'Colloid concentration',
 'source-supporting_procedures-2':'Dry-powder preparation','source-supporting_procedures-3':'Size-exclusion HPLC',
 'source-supporting_procedures-4':'TEM preparation and acquisition','source-supporting_procedures-5':'Infrared acquisition',
 'source-supporting_procedures-6':'Powder X-ray diffraction','source-supporting_procedures-7':'Optical acquisition',
 'source-supporting_procedures-8':'Time-resolved photoluminescence',
 'source-chemicals-13':'AOT binder','source-chemicals-18':'Rhodamine 6G reference',
 'source-observations-0':'TEM dimensions of the 6.0 formulation','source-observations-1':'6.0 HPLC distribution: conflicting bounds',
 'source-observations-2':'2.0 HPLC monomer: table and prose values','source-observations-3':'Structural limit for the 1.0 formulation',
 'source-observations-4':'Lattice comparison with bulk silicon','source-observations-5':'AKS41: population and individual-particle TEM',
 'source-observations-6':'Permanent aggregation and fractionation','source-observations-7':'Infrared assignments and their limits',
 'source-observations-8':'UV absorption and size dependence','source-observations-9':'As-made and activated emission',
 'source-observations-10':'Estimated photoluminescence quantum yield','source-observations-11':'Multicomponent photoluminescence decay',
 'source-observations-12':'pH-dependent quenching and recovery','source-observations-13':'Silicon throughput and collection balance',
 'source-observations-14':'Mie-model concentration calibration','source-observations-15':'Colloidal stability',
 'source-observations-16':'Impurities in unwashed powder','source-observations-17':'Electron diffraction: prose evidence only',
 'source-observations-18':'TEM sampling bias for the 2.0 formulation','source-observations-19':'Excitation-spectrum correspondence',
 'source-observations-20':'Bulk-silicon optical control'}
PROC_TEXT=[
 'Ethylene-glycol colloids are refluxed under argon near 200 °C for approximately one hour with 5% added acidic water at pH 1, acidified using sulfuric acid. The percentage basis and final mixture pH are unspecified. The three formulation contexts and their activated products remain separate.',
 'Colloids can be concentrated five- to tenfold by mild heating at 80 °C under vacuum. The vacuum level, time and starting/final volumes are not supplied. This temperature is not reported for the separate dry-powder preparation.',
 'For IR and powder XRD, a colloid is evaporated under mild heating and vacuum to a paste, then washed repeatedly with acetone and ethylene dichloride. A deep-brown powder results, typically 10 mg or less for smaller crystallite sizes. Washing order, volumes and separation conditions are unspecified; the stated amount is not a batch-resolved synthesis yield.',
 'Size-exclusion HPLC uses sequential ZORBAX 60-S and 300-S columns on an HP 1090 with diode-array UV–vis detection. The reported mobile phase is 60:40 methanol:ethylene glycol, with 1.5 × 10⁻³ M sodium methylate and 0.1 M tetrabutylammonium bromide, at 0.75 cm³/min and 50 °C. The solvent-ratio basis is not explicit. Polymer-calibrated equivalent sizes and permanent aggregates must be distinguished from crystalline-core dimensions.',
 'TEM uses a JEOL 2000-FX at 200 keV. Samples are collected directly from the aerosol or prepared by evaporating colloid on holey-carbon films. Evaporated HPLC fractions are washed with the source-named “ethylene chloride” to remove organic salt. The exact preparation branch is not assigned to every image, and this short solvent name is not silently equated with the powder-wash solvent.',
 'Dry powder is ground and pressed into KBr pellets for infrared spectroscopy. The KBr loading, pressing conditions, instrument and spectral resolution are not supplied. Figure 7 concerns powder from the 6.0 formulation.',
 'Powder is bound with a small amount of AOT soap or encased in Mylar, then mounted on an optical-fiber tip. Measurements use a triple-crystal spectrometer, Mo Kα radiation and pyrolytic-graphite monochromator/analyzer crystals. The Rigaku source is described as a 12 kW rotating anode; actual operating power is not separately stated. Mounting alternatives remain unresolved for individual specimens.',
 'UV–vis spectra use an HP 8452A. Steady-state PL uses a SPEX Fluorolog 2 with extended red response near 900 nm; some longer-wavelength spectra use a Jobin-Yvon HR640 with Ge-photodiode detection and 355 nm excitation. Both PL systems are calibrated with a tungsten lamp. The per-curve instrument assignment is incomplete, and the separate 350/355 nm source disagreement is retained.',
 'The 1.0 colloid is excited by a picosecond 355 nm pulse and measured with a photomultiplier/digital-storage-oscilloscope system of 10 ns resolution. The reported 17 and 76 μs values are major components of a multiexponential fit, not independent or established purely radiative lifetimes.'
]
GAP_TEXT=[
 'Matching supporting information is not located or verified.',
 'Absolute versus gauge pressure and the standard temperature/pressure underlying sccm are unspecified.',
 'Continuous collection duration and collected volume are not assigned to each measured specimen.',
 'The basis of the 5% acidic-water addition and the sulfuric-acid concentration are unspecified.',
 'Frit-silanization concentration, dose, temperature, duration and finishing conditions are missing.',
 'The earlier AKS41 apparatus sample has no quantified synthesis recipe in this article.',
 'A crystalline core is not directly established for the 1.0 formulation.',
 'Physical batch, aliquot and collector-fraction identities across techniques are incompletely resolved.',
 'The source supplies no measured atomic coordinates or experimental CIF.',
 'Original curves are retained as figures; they have not been digitized into raw numeric arrays.',
 'Cited upstream work is bibliographic context and has not been independently read or imported as experimental evidence.'
]
FIELD_LABELS={'TEM_bright_field_nm':'Bright-field TEM size','TEM_dark_field_core_nm':'Dark-field TEM core size',
 'XRD_coherence_nm':'X-ray coherence length','HPLC_monomer_time_min':'HPLC monomer elution time',
 'HPLC_monomer_equivalent_size_nm':'HPLC monomer-equivalent size','HPLC_distribution_fwhm_nm':'HPLC distribution FWHM interval',
 'activated_PL_peak_nm':'Activated PL peak'}
def quantity_label(key):
    special={'KBr_amount':'KBr amount','TBAB':'Tetrabutylammonium bromide concentration','sodium_methylate':'Sodium methylate concentration',
             'pH':'pH of added acidic water','prebubbler_EG':'Ethylene glycol in the prebubbler','collector_EG':'Ethylene glycol in the frit collector',
             'oxygen_to_helium':'Oxygen:helium ratio','added_water_pH':'pH of added acidic water'}
    return special.get(key,key.replace('_',' ').capitalize())
def fact_from_q(label,q,default_evidence):
    status=q.get('status')or('reported' if q.get('value') is not None else 'not_reported')
    val=q.get('value')
    if q.get('minimum') is not None:val={'minimum':q['minimum'],'maximum':q['maximum']}
    elif isinstance(val,list) and len(val)==2:val={'minimum':val[0],'maximum':val[1]}
    qe=q.get('evidence',[])
    qe=[ev(e['pdf_page'],e['section_or_item'])for e in qe]if qe and 'section_or_item'in qe[0] else qe
    return {'label':label,'value':val,'unit':q.get('unit')or'', 'status':status,'qualifier':q.get('qualifier')or'',
            'basis':clean(q.get('basis')or q.get('meaning')or ''),'approximate':q.get('approximate',False)or q.get('qualifier')in ['approximate','near','about'],
            'evidence':qe or default_evidence}
def facts_for(item):
    out=[];data=item.get('staged_detail');default=evidence(item['evidence'])
    def descend(value,name=''):
        if isinstance(value,dict):
            if 'value'in value and 'unit'in value:
                out.append(fact_from_q(quantity_label(name.split('.')[-1]),value,default));return
            for k,v in value.items():
                if k in ['evidence','continuation_evidence','notes','summary','id','sample','samples','source','sample_scope','structural_status','paired_states']:continue
                if k in ['conditions','concentration','pH','calibration']or name:
                    if v is None:out.append({'label':quantity_label(k),'value':None,'unit':'','status':'not_reported','qualifier':'','basis':'Not reported for this procedure.','evidence':default})
                    elif isinstance(v,(int,float))and not isinstance(v,bool):out.append({'label':quantity_label(k),'value':v,'unit':'','status':'source_context','qualifier':'','basis':'Context-specific reported value; not an independent training target.','evidence':default})
                    elif isinstance(v,dict)or isinstance(v,list):descend(v,k)
                elif isinstance(v,dict):descend(v,k)
        elif isinstance(value,list):
            for v in value:
                if isinstance(v,dict):descend(v,name)
    if (item.get('source_pointer')or'').startswith('/observations/'):
        # Reuse audited quantitative objects rather than stripping qualifiers/units from narrative values.
        seen=set()
        for link in item['canonical_links']:
            if link['json_pointer'].startswith('/measurements/'):
                m=pointer(RECORDS[link['record_id']],link['json_pointer'])
                key=(link['record_id'],m['id'])
                if key not in seen:
                    out.append(fact_from_q(quantity_label(m['property']),m['value'],default));seen.add(key)
    elif isinstance(data,dict):descend(data)
    details=item.get('reader_details',{})
    for q in details.get('quantities',[]):
        val=q.get('value')
        if 'minimum'in q:val={'minimum':q['minimum'],'maximum':q['maximum']}
        out.append({'label':quantity_label(q['name']),'value':val,'unit':q.get('unit',''),'status':q.get('status','source_context'),
                    'qualifier':q.get('qualifier',''),'basis':q.get('meaning','Context only; no physical-batch or training-target join is asserted.'),'evidence':default})
    # Preserve scalar narrative contexts that use named objects rather than the quantities list.
    for k,q in details.items():
        if isinstance(q,dict)and 'value'in q:out.append(fact_from_q(quantity_label(k),q,default))
    if item['id']=='source-supporting_procedures-3':
        # Replace untyped calibration numerals with the audited logarithmic calibration parameters.
        source_labels={quantity_label(k)for k in data.get('calibration',{})}
        out=[q for q in out if q['label']not in source_labels]
        rec=RECORDS['littau-1993-si-hplc-fractionation']
        cal=next(o for o in rec['operations']if o['id']=='calibrate')
        out.extend(fact_from_q(quantity_label(k),q,default)for k,q in cal['parameters'].items()if k not in ['flow','temperature'])
    if item['id']=='source-observations-10':
        rec=RECORDS['littau-1993-si-acid-activation']
        dye=next(m for m in rec['materials']if m['id']=='r6g')
        out.append(fact_from_q('R6G reference quantum yield',dye['quantities']['reference_quantum_yield'],default))
    for q in out:
        if q['label']=='pH of added acidic water':q['unit']='pH';q['basis']='Added acidic water; not final colloid pH.'
        if q['label']=='Concentration factor':q['unit']='fold'
        if q['label']=='Disilane concentration range':q['basis']='Study-wide reported range, not an adjustable range assigned to each fixed-flow formulation.'
        if item['id']=='context-theory-comparisons':q['status']='cited_theoretical_context'
        if item['id']=='context-silica-charge':q['status']='cited_surface_chemistry_context'
    return out

metadata_dest={'title':'/title','authors':'/paper/authors','journal':'/paper/journal','year':'/paper/year','volume':'/paper/volume',
              'pages':'/paper/pages','doi':'/doi','pdf_pages':'/documents/0/page_count','si_status':'/supporting_information'}
for item in EVID['items']:
    sid=item['id'];ptr=item.get('source_pointer')or''
    mapping={'source_item_id':sid,'source_pointer':ptr or None,'original_disposition':item['disposition']}
    if item['disposition']=='excludedreason' or ptr.startswith('/new_field_requirements/'):
        reason='Administrative extraction bookkeeping is excluded from scientific reader content; no local paths or original private values are exported.' if item['disposition']=='excludedreason' else 'Implementation requirements are tracked by the project; scientific meanings are represented in the linked source content, not presented as measured paper results.'
        ledger['reader_exclusions'].append({'source_item_id':sid,'reason':reason})
        mapping.update(public_disposition='excluded',target=None,reason=reason)
        ledger['reader_item_coverage'].append(mapping);continue
    if ptr.startswith('/source/')and ptr.split('/')[-1]in metadata_dest:
        mapping.update(public_disposition='public_metadata',target=metadata_dest[ptr.split('/')[-1]],reason='Bibliographic or review metadata is represented once in the ledger header/document inventory.')
        ledger['reader_item_coverage'].append(mapping);continue
    section=bytitle[item['reader_section']]
    pi={'id':sid,'title':TITLE.get(sid,clean(item['title'])),'text':clean(item['text']),
        'claim_type':item['claim_type'],'sample_scope':item['sample_scope'],'evidence':evidence(item['evidence']),
        'source_locators':[loc(e)for e in item['evidence']],
        'canonical_links':[{'record_id':z['record_id'],'json_pointer':z['json_pointer'],
                            'relation':'Related source context; the pointer does not establish a shared physical batch.'}for z in item['canonical_links']],
        'notes':[clean(n)for n in item['notes']if not any(s in n for s in ['staged_detail','curated identity','nested calibration','Source-review limitation'])],
        'facts':facts_for(item),'training_eligible':False}
    if ptr.startswith('/supporting_procedures/'):
        pi['text']=PROC_TEXT[int(ptr.split('/')[-1])]
    if ptr.startswith('/gaps/'):
        pi['title']='Source limitation '+str(int(ptr.split('/')[-1])+1);pi['text']=GAP_TEXT[int(ptr.split('/')[-1])]
    if ptr.startswith('/synthesis_variants/'):
        n=int(ptr.split('/')[-1])
        if n<3:
            label=['6.0','2.0','1.0'][n];pp=[20,7,3.5][n]
            pi['text']=f'The {label} label denotes {label} sccm of the 0.1% disilane/helium stock, corresponding to a stated disilane partial pressure of {pp} mTorr at the pyrolysis inlet. It does not denote pure-disilane flow or an independently identified physical batch.'
            if n==2:pi['notes'].append('Direct crystalline-core structure remains unresolved for this formulation.')
        else:pi['text']='AKS41 was produced in an earlier apparatus and is described nominally as approximately 13 nm material. Its quantified synthesis is not given. Population-average TEM size, one imaged core and equivalent chromatographic sizes are separately scoped observations; AKS41 is not another reconstructed flow recipe.'
    if ptr.startswith('/table_I/rows/'):
        bits=ptr.split('/');row=int(bits[3]);field=bits[4];label=['6.0','2.0','1.0'][row]
        if field=='sample':pi['title']='Table I formulation '+label;pi['text']=f'This row refers to formulation {label}. Values come from several techniques and preparation states; they are not proof that every measurement used the same physical specimen.'
        else:
            pi['title']=f'Table I · {label} · {FIELD_LABELS[field]}'
            link=item['canonical_links'][0];m=pointer(RECORDS[link['record_id']],link['json_pointer']);q=m['value']
            pi['facts']=[fact_from_q(FIELD_LABELS[field],q,pi['evidence'])]
            val=q['value'];qual=q['qualifier']
            if q['minimum']is not None:display=f"{q['minimum']}–{q['maximum']} {q['unit']}"
            elif val is None:display='not observed / not numerically established'
            else:display=f"{'less than 'if qual=='less_than'else''}{val:g} {q['unit']}"
            pi['text']=f'{FIELD_LABELS[field]} for formulation {label}: {display}. '
            pi['text']+=('The PL value belongs to acid-activated colloid.'if field=='activated_PL_peak_nm'else m['conditions'])
    if ptr.startswith('/relevance/'):
        labels={'contains_synthesis':'Synthesis information','contains_structure':'Structural information','contains_properties':'Property information',
                'method':'Synthesis method','systems':'Material system','scope_note':'Oxide and crystallinity limits'}
        key=ptr.split('/')[-1];pi['title']=labels[key]
        pi['text']={'contains_synthesis':'The article reports a continuous aerosol synthesis with gas-phase pyrolysis, oxidative surface treatment and liquid collection.',
                    'contains_structure':'Structural evidence includes TEM, powder XRD and chromatographic size characterization, with distinct sample and technique limits.',
                    'contains_properties':'The article reports optical absorption, infrared spectra and state-dependent photoluminescence, including an estimated yield and time-resolved decay.',
                    'method':'Continuous aerosol pyrolysis is followed by dilution, oxidative passivation and collection in ethylene glycol.',
                    'systems':'The material is surface-oxidized silicon, represented here as Si/SiOₓ without assigning an exact oxide stoichiometry.',
                    'scope_note':'The source does not establish a stoichiometric crystalline SiO₂ shell or atomic interface. A crystalline core remains unresolved for the 1.0 formulation.'}[key]
    if ptr=='/table_I/evidence':pi['text']='Table I summarizes the three current-apparatus formulation families. The original table is retained with its separate TEM, XRD, HPLC and activated-emission meanings.'
    # Replace editorial curation instructions with a concise scientific linkage note.
    pi['notes']=[n for n in pi['notes']if not n.startswith('Molecular asset/registry')]
    pi['notes']=[('Study-wide ranges and operational observations do not establish an independently tested condition range for each formulation.'
                  if 'Staged nested conditions/notes remain inspectable' in n else
                  'The original figure retains its source labels and axes; it does not supply digitized raw data or establish that different techniques used one physical specimen.'
                  if 'proof of a complete reader join' in n else n)for n in pi['notes']]
    for f in pi['facts']:
        f['basis']=f.get('basis','').replace('Context-specific reported value; not an independent training target.',
                                           'Context-specific reported value; no independently identified physical specimen is assigned.')
        f['basis']=f['basis'].replace('Context only; no physical-batch or training-target join is asserted.',
                                      'Contextual statement; no particular physical specimen or synthesis run is assigned.')
    if not pi['evidence']:
        pi['evidence_basis']='Review finding or source inventory; no fabricated experimental locator.'
    index=len(section['items']);section['items'].append(pi)
    mapping.update(public_disposition='reader_item',target=f"/reader_sections/{sections.index(section)}/items/{index}",
                   public_item_id=pi['id'],canonical_links=pi['canonical_links'])
    ledger['reader_item_coverage'].append(mapping)

# Original crops use exactly the planned public path; no files are copied by this generator.
asset_records={
 'figure-1':['littau-1993-si-aerosol-'+v for v in ['6p0','2p0','1p0']],
 'figure-2':['littau-1993-si-aerosol-6p0','littau-1993-si-aerosol-2p0','littau-1993-si-optical-characterization'],
 'figure-3':['littau-1993-aks41-context'],'figure-4':['littau-1993-aks41-context'],
 'figure-5':['littau-1993-si-aerosol-6p0','littau-1993-si-hplc-fractionation'],
 'figure-6':['littau-1993-si-aerosol-6p0','littau-1993-si-aerosol-2p0','littau-1993-si-xrd-characterization'],
 'figure-7':['littau-1993-si-ir-characterization'],
 'figure-8':['littau-1993-si-aerosol-1p0','littau-1993-si-hplc-fractionation'],
 'figure-9':['littau-1993-si-acid-activation','littau-1993-si-optical-characterization'],
 'figure-10':['littau-1993-si-acid-activation'],'figure-11':['littau-1993-si-acid-activation'],
 'figure-12':['littau-1993-si-time-resolved-pl'],
 'table-1':['littau-1993-si-aerosol-'+v for v in ['6p0','2p0','1p0']]+['littau-1993-si-acid-activation']}
asset_caption={
 'figure-1':'Continuous quartz aerosol apparatus showing pyrolysis, dilution, oxidative treatment and gas delivery. The diagram labels the first furnace 865 °C; the methods text gives 860 °C.',
 'figure-2':'Absorption spectra of the 6.0 colloid (upper) and 2.0 colloid (lower). No separate AKS41 or 1.0 trace is plotted here.',
 'figure-3':'Bright-field TEM of an aggregate from the earlier AKS41 preparation. One particle shows lattice contrast inside an amorphous surface layer.',
 'figure-4':'AKS41 size-exclusion chromatogram. Polymer-calibrated equivalent diameters include monomer and aggregate contributions; the caption prints ASK41.',
 'figure-5':'Size-exclusion chromatogram of the 6.0 colloid, including a monomer shoulder and aggregate contributions.',
 'figure-6':'Powder XRD of the 6.0 formulation (upper) and 2.0 formulation (lower), with diamond-Si size-broadening fits and an arbitrary low-angle Gaussian contribution.',
 'figure-7':'Infrared spectrum of dry powder from the 6.0 formulation. The text identifies the same powder as used for XRD, while misnumbering that XRD figure.',
 'figure-8':'Size-exclusion chromatogram of the 1.0 colloid. A chromatographic size distribution does not establish a crystalline core.',
 'figure-9':'Room-temperature emission of the 6.0 colloid before activation (lower) and after acidic activation (upper). The caption gives 355 nm excitation, while the discussion gives 350 nm for Figures 9–11.',
 'figure-10':'Emission of the 2.0 colloid in the activated-state context established by the surrounding discussion.',
 'figure-11':'Emission of the 1.0 colloid in the activated-state context. Optical emission does not establish its crystalline phase.',
 'figure-12':'Time-resolved emission of the 1.0 colloid following picosecond 355 nm excitation. The measured decay and reported multiexponential fit components are distinct evidence.',
 'table-1':'Formulation-specific TEM, XRD and HPLC dimensions with activated-colloid luminescence peaks. Each column retains its technique and specimen-state meaning.'}
for m in MAN['items']:
    a=next(x for x in EVID['original_assets']if x['id']==m['id'])
    path='assets/figures/littau1993/'+m['file']
    assert sha(HERE/'crop-assets'/m['file'])==m['sha256']
    f={'id':m['id'],'label':'Table I'if m['type']=='table'else m['id'].replace('-',' ').title(),
       'document_role':'main','page':m['pdf_page'],'printed_page':m['printed_page'],
       'source_locators':[loc(e)for e in a['evidence']], 'caption_paraphrase':asset_caption[m['id']],
       'sample_links':asset_records[m['id']],'formulation_labels':a['sample_scope']['formulations'],
       'sample_scope':a['sample_scope'],'sample_linkage':'Formulation/state context; no exact physical-batch or collector-fraction identity is asserted.',
       'evidence_class':a['evidence_class'],'public_asset':path,'public_asset_sha256':m['sha256'],
       'asset_provenance':{'source_file':Path(source['main_file']).name,'source_sha256':source['sha256'],
                          'source_pdf_page':m['pdf_page'],'crop_bbox_px_top_left':m['bbox_px'],
                          'render_scale':MAN['render_scale'],'source_render_dimensions_px':m['source_render_dimensions_px'],
                          'transformation':'Original PDF raster crop; caption, axes and labels retained; no redrawing or data alteration.'},
       'reviewed':True,'text_reviewed':True,'visual_reviewed':True,'reader_render_verified':False,
       'limitations':['No numeric curve digitization is supplied.','Measured curves, model fits and reference/background components must remain distinct.']}
    if m['id']=='table-1':
        f['columns']=['sample','TEM_bright_field_nm','TEM_dark_field_core_nm','XRD_coherence_nm','HPLC_monomer_time_min','HPLC_monomer_equivalent_size_nm','HPLC_distribution_fwhm_nm','activated_PL_peak_nm']
        f['rows']=STAGE['table_I']['rows'];f['notes']=['Values compare formulation families across methods; the PL column describes activated colloids. Missing/not-observed structure entries are not zero sizes.']
        ledger['tables'].append(f)
    else:ledger['figures'].append(f)
for section in sections:
    for item in section['items']:
        if item['id'].startswith('source-figures-'):
            fid='figure-'+str(int(item['id'].split('-')[-1])+1)
            item['title']=fid.replace('-',' ').title()
            item['text']=asset_caption[fid]

# Characterization groups are linked to record objects without turning context into new experiments.
char_configs=[
 ('TEM and lattice-resolved imaging',['littau-1993-si-tem-characterization','littau-1993-aks41-context'],[2,3,4,5],
  'JEOL 2000-FX at 200 keV; direct aerosol collection or colloid evaporation on holey carbon. Exact preparation route is not assigned to every observed specimen.',
  'Population, selected-particle, core, shell and overall-size meanings are separate. AKS41 is earlier-apparatus context.'),
 ('Size-exclusion HPLC',['littau-1993-si-hplc-fractionation','littau-1993-aks41-context'],[2,3,4,5,6],
  'Sequential ZORBAX 60-S/300-S; HP 1090; 50 °C and 0.75 cm³/min; 60:40 methanol:ethylene glycol with sodium methylate and tetrabutylammonium bromide.',
  'Equivalent hard-sphere diameters use polymer calibration and may include permanent aggregates; elution time is not reaction time.'),
 ('Powder XRD',['littau-1993-si-xrd-characterization'],[2,3,4,5],
  'Powder with AOT or Mylar on an optical-fiber tip; triple-crystal Mo Kα instrument; 12 kW source specification, actual operating power unstated.',
  'Current 6.0/2.0 samples support diamond-Si-core comparison; 1.0 has no resolved crystalline pattern. No experimental CIF is supplied.'),
 ('Infrared spectroscopy',['littau-1993-si-ir-characterization'],[2,4,5],
  'Washed dry powder pressed in KBr; Figure 7 is the 6.0 formulation.',
  'Oxide/OH assignments are author interpretations; wash-dependent organic features and near-absent SiH do not determine complete surface composition.'),
 ('UV–vis absorption and steady-state PL',['littau-1993-si-optical-characterization','littau-1993-si-acid-activation'],[2,3,5,6],
  'HP 8452A UV–vis; SPEX Fluorolog 2 and selected Jobin-Yvon/Ge spectra; tungsten-lamp calibration.',
  'As-made and activated states remain separate. Quantum yield is an approximate cohort estimate; 350/355 nm excitation statements disagree.'),
 ('Time-resolved PL',['littau-1993-si-time-resolved-pl'],[6],
  'Picosecond 355 nm excitation; photomultiplier/digital-storage oscilloscope with 10 ns resolution.',
  'Activated 1.0 context; 17/76 μs are major multiexponential fit components, not proved radiative lifetimes.'),
 ('Electron diffraction: prose only',['littau-1993-si-tem-characterization','littau-1993-aks41-context'],[4,5],
  'Diffraction-ring observations are described in the text; no original SAED pattern is displayed.',
  'Do not generate an apparent measured SAED image or infer an unambiguous 1.0 phase from this prose.')]
for name,rids,pages,conditions,limits in char_configs:
    ledger['characterization_inventory'].append({'technique':name,'record_ids':rids,
      'source_locators':[f'Main PDF p. {p}, printed p. {1223+p}'for p in pages],
      'conditions':conditions,'scope_and_limits':limits,'raw_curve_digitization':False})

ledger['evidence_conflicts']=[{'id':c['id'],'source_locators':[loc(x['evidence'])for x in c['statements']],
    'issue':'; '.join(x['text']for x in c['statements']),'statements':[{'text':x['text'],'evidence':evidence([x['evidence']])}for x in c['statements']],
    'sample_scope':c['scope'],'handling':c['handling']}for c in EVID['source_conflicts']]
ledger['remaining_gaps']=GAP_TEXT+['Reader integration, figure-to-state joins and visual verification have not been completed for this proposal.']
ledger['referenced_methods']=[{'reference_number':r['reference_number'],'source_locators':[loc(e)for e in r['evidence']],
    'role':r['reader_role'],'evidence_class':r['evidence_class'],'cited_work_independently_reviewed':False}for r in EVID['reference_contexts']]
ledger['chemical_intuition']=[{'id':i['id'],'title':i['title'],'text':i['text'],'claim_type':i['claim_type'],
                            'sample_scope':i['sample_scope'],'evidence':i['evidence']}for i in bytitle['Chemical intuition']['items']]
ledger['materials_inventory']=[{'name':i['title'],'description':i['text'],'evidence':i['evidence']}for i in bytitle['Precursors']['items']if i['id'].startswith('source-chemicals')]
ledger['simulation_inventory']=[{'id':'Mie-concentration-calibration','name':'Author Mie optical-concentration model',
   'source_locators':['Main PDF p. 3, printed p. 1226, Results A','Main PDF p. 7, printed p. 1230, reference 38'],
   'assumptions':'Bulk crystalline-Si optical response in the electric-dipole approximation; quantum effects and strong aggregation-driven Rayleigh scattering excluded from the stated size-independence claim.',
   'reference_values':'1 mg/cm³ Si gives calculated optical density 1.85 at 295 nm and a 1 mm path; approximate size independence below 50 nm.',
   'limits':'Model calibration, not measured raw absorbance, a sample-specific concentration label or an exact synthesis yield.'}]
ledger['reader_contract']={'version':'1.0','section_ids':[x[0]for x in SECTIONS],
   'item_fields':['id','title','text','claim_type','sample_scope','evidence','source_locators','canonical_links','notes','facts','training_eligible'],
   'coverage_rule':'Every input reader-evidence item maps once to a public reader item, public metadata or an explicit exclusion. Render verification is a separate downstream check.'}

# Validate public serialization, exact mapping and planned dependencies without writing Site files.
serialized=json.dumps(ledger,ensure_ascii=False)
for forbidden in ['staged_detail','C:\\','C:/','/Users/','main-text.txt','research-assets','private_path','local_text_path','local_render_path']:
    assert forbidden not in serialized,forbidden
assert len(ledger['reader_item_coverage'])==171
assert len({x['source_item_id']for x in ledger['reader_item_coverage']})==171
assert {x['source_item_id']for x in ledger['reader_item_coverage']}=={x['id']for x in EVID['items']}
for x in ledger['reader_item_coverage']:
    if x['target']:pointer(ledger,x['target'])
for section in sections:
    for item in section['items']:
        for link in item['canonical_links']:pointer(RECORDS[link['record_id']],link['json_pointer'])
assert sum(len(d['pages'])for d in ledger['documents'])==7
assert len(ledger['figures'])==12 and len(ledger['tables'])==1
assert {rid for x in ledger['recipe_inventory']for rid in x['record_ids']}==set(RECORDS)
assert protected=={path:sha(Path(path))for path in protected}

# Load the existing builder read-only; it will report unresolved planned assets/records until root imports them.
sys.path.insert(0,str(SITE/'scripts'))
from review_scope import source_review_scope
scope=source_review_scope(ledger);ledger['review_scope_label']=scope['label']
spec=importlib.util.spec_from_file_location('proposal_builder_validator',SITE/'scripts/build_paper_reviews.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
builder_errors=module.validate(ledger)
unexpected=[e for e in builder_errors if not e.startswith(('Figure hash mismatch:','Unresolved recipe link:'))]
assert not unexpected,unexpected
write('littau1993.json',ledger)
coverage={'status':'public_safe_proposal_checks_passed; Site_dependency_resolution_and_rendering_pending',
          'proposal_sha256':sha(OUT/'littau1993.json'),'source_pdf_sha256':source['sha256'],
          'source_extraction_sha256':sha(HERE/'source-extraction.json'),'reader_evidence_sha256':sha(HERE/'reader-evidence.json'),
          'input_reader_items':171,'public_reader_items':sum(len(s['items'])for s in sections),
          'metadata_mappings':sum(x['public_disposition']=='public_metadata'for x in ledger['reader_item_coverage']),
          'exclusions':len(ledger['reader_exclusions']),'unmapped_items':0,
          'section_counts':{s['id']:len(s['items'])for s in sections},'record_links':13,'figures':12,'tables':1,
          'main_pages':7,'review_scope':ledger['review_scope'],'si_status':ledger['supporting_information']['status'],
          'private_path_or_staged_payload_scan':'passed','all_crop_hashes_verified':True,'protected_source_records_unchanged':True,
          'existing_builder_unexpected_errors':unexpected,'existing_builder_pending_dependencies':builder_errors,
          'checks_do_not_establish':['Actual Site copy/import','Reader rendering and interaction','Complete source-to-view verification','Record/training approval','Publication']}
write('coverage-checks.json',coverage)
write('reader-sections.json',{'paper_id':'littau1993','review_scope':ledger['review_scope'],'reader_sections':sections,
                             'reader_item_coverage':ledger['reader_item_coverage'],'reader_exclusions':ledger['reader_exclusions']})
readme=f'''# Littau 1993 public review proposal

`littau1993.json` matches the existing paper-review builder fields and adds the agreed six-section reader contract. `reader-sections.json` provides the same reader content separately.

All 171 input items are accounted for: {coverage['public_reader_items']} reader items, {coverage['metadata_mappings']} metadata mappings and {coverage['exclusions']} explicit exclusions. No `staged_detail`, private paths or full article text are exported. The 13 record links and 13 planned original-asset paths are checked against the private records/crops; all seven supplied main pages are represented. SI remains not located or verified.

Run `build_public_review_proposal.py` from the parent review directory to reproduce these proposals. It only writes this proposal directory and does not copy assets, change records, edit the Site, promote training or publish.

The existing builder accepts the ledger structure and main-only scope. It currently reports {len(builder_errors)} pending Site dependencies; these are planned record/asset imports, not fabricated links. Root must copy the verified crops to `assets/figures/littau1993/`, import the audited records and ledger, render all sections and joins, then run the normal Site checks. Reader rendering and publication remain explicitly pending.

Reader items contain `id`, `title`, `text`, `claim_type`, `sample_scope`, `evidence`, `source_locators`, `canonical_links`, `notes` and `facts`. Facts preserve context values without turning them into training targets. AKS41 remains a separate earlier-apparatus observation; 1.0 crystallinity, model calibration, bulk references and activation states retain their limitations.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
print(json.dumps({k:v for k,v in coverage.items()if k not in ['existing_builder_pending_dependencies']},indent=2))
