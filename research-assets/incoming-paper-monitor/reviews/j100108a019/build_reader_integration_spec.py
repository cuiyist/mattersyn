"""Private reader-integration specification; does not modify the Site."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
SITE = Path('[local path redacted]')
def read(p):
    return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name, data):
    (BASE/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

ex = read(BASE/'source-extraction.json')
manifest = read(BASE/'crop-assets/manifest.json')
source = Path('[local path redacted]')
source_hash = sha(source)
assert source_hash == manifest['source_sha256']
variants = []
for label, flow, partial in [('6p0',6,20),('2p0',2,7),('1p0',1,3.5)]:
    rid = 'littau-1993-si-aerosol-'+label
    p = BASE/'canonical-drafts'/(rid+'.json')
    variants.append({'record_id':rid,'source_label':label.replace('p','.'),'draft_path':str(p),'sha256':sha(p),
        'stock_flow_sccm':flow,'stock_identity':'0.1% Si2H6 in He; percentage basis unreported',
        'reported_Si2H6_partial_pressure_mTorr':partial,'scope':'Published formulation, not an identified physical batch.',
        'product_link':'general_context; exact collector fraction and specimen identity unresolved',
        'phase_scope':'Diamond-lattice Si core reported for 6.0 and 2.0; no directly observed crystalline core for 1.0.',
        'requested_tasks':[]})

def stage(id, action, inputs, outputs, scene, conditions, limits, page=2, item='Experimental A'):
    return {'id':id,'canonical_action':action,'inputs':inputs,'outputs':outputs,'scene':scene,
            'conditions':conditions,'scope_and_limits':limits,
            'source_locator':f'Main PDF p. {page}, printed p. {1223+page}, {item}'}

stages = [
 stage('frit-treatment',None,['SiH2Cl2','toluene','coarse glass frit'],['silanized frit'],
       'Separate apparatus-treatment card and treated collector frit; not a reagent feed into the furnace.',
       ['Printed formula SiH2Cl2 in toluene; visually verified in source.'],
       ['Concentration, amount, temperature, time, washing and drying are unreported.']),
 stage('feed','gas_feed',['0.1% Si2H6/He stock','purified helium'],['mixed-feed'],
       'Gas cylinders, Oxisorb purifier on helium, MKS flow controllers and quartz inlet.',
       ['Stock flow: 6.0, 2.0 or 1.0 sccm; not pure-disilane flow.','Total pyrolysis feed 300 sccm.',
        'Reactor pressure 1.4 atm; absolute/gauge convention unreported.','Quartz tube internal diameter 7 mm.'],
       ['Standard conditions underlying sccm are unstated.','Study-wide 3–30 ppm is not a variant-specific adjustable range.',
        'No run duration or inlet temperature is given.','Do not apply the reactor pressure to downstream collection vessels.']),
 stage('pyrolysis','aerosol_pyrolysis',['mixed-feed'],['raw-aerosol','wall-deposit'],
       'Quartz tube through first external furnace, 1 cm heated zone; show wall deposition as a distinct side stream.',
       ['860 °C in Experimental A; 865 °C in Figure 1. Display both with a conflict note.',
        'Approximately 18 cm/s and 60 ms residence in this heated zone.'],
       ['Residence time is not synthesis run duration.','Internal thermocouples were removed before disilane admission.',
        'Study-wide 2–8 nm zone-exit description is not a measurement for every formulation.',
        'No apparent change over 850–1050 °C and amorphous material below 700 °C/faster flow are contextual observations, not fully specified extra recipes.']),
 stage('dilution','gas_dilution_quench',['raw-aerosol','O2','He'],['quenched-aerosol'],
       '0.6 mm aperture followed immediately by a side-stream gas mixer; no cooling liquid or flask.',
       ['Reported dilution 1:23 with O2:He = 1:6.','Figure 1 supplies O2 1000 sccm and He 6000 sccm.',
        'Rapid cooling to 200–300 °C.'],
       ['Keep printed ratio 1:23; do not silently replace it with a recomputed total-flow ratio.',
        'Cooling time and exact local pressure are unreported.']),
 stage('oxidation','aerosol_oxidation',['quenched-aerosol'],['oxidized-aerosol'],
       'Second 1–2 mm aperture and separate external tube furnace.',
       ['700 °C; approximately 430 cm/s and 20 ms residence.','Protocol-level surface oxide estimate 1–2 nm.'],
       ['Oxide estimate is not a universal measured shell thickness.','No stoichiometrically exact SiO2 assignment or atomic-coordinate model is supplied.']),
 stage('cool-before-collection',None,['oxidized-aerosol'],['cooled-aerosol'],
       'Unheated transfer line toward two serial bubblers; schematic geometry only.',[],
       ['Cooling is reported, but rate, method, temperature and duration are not.']),
 stage('prebubbler','sequential_bubbler_collection',['cooled-aerosol','9 cm3 ethylene glycol'],['prebubbler-colloid','continuing-aerosol'],
       'First collection vessel with submerged inlet, followed in series by the frit collector.',
       ['9 cm3 ethylene glycol in this vessel.'],
       ['Do not pool with the second collector.','Temperature, pressure and collection duration are unreported.',
        'Reported 2–3 cm3/day solvent loss is an operational observation, not a dose or universal run duration.']),
 stage('frit-collector','sequential_bubbler_collection',['continuing-aerosol','9 cm3 ethylene glycol','silanized coarse glass frit'],['collector-colloid','exhaust'],
       'Second vessel with coarse treated frit and its own 9 cm3 collection liquid.',
       ['9 cm3 ethylene glycol; roughly two-thirds of collected crystallites appear here.'],
       ['Do not carry 700 °C, 20 ms or 1.4 atm into this panel.','This collection fraction is distinct from the author-derived approximately one-third Si-feed mass capture.',
        'Figure-specific assignment to this vessel remains unresolved.'])]

support_scenes = {
 'acid-activation':('Argon reflux vessel and condenser','Separate acid-activated product state; near 200 °C, about 1 h, 5% added acidic water at pH 1 (H2SO4). The percentage denominator, acid dose and argon flow are unreported.'),
 'concentrate':('Vacuum concentration apparatus','80 °C and 5–10-fold concentration; vacuum pressure and duration unknown.'),
 'dry-powder':('Vacuum evaporation followed by separate repeated washing','Mild heat has no numerical temperature; do not borrow 80 °C. Acetone and ethylene dichloride washing yields analytical powder, not a universal synthesis workup or overall yield.'),
 'HPLC':('Two sequential chromatographic columns and detector','ZORBAX 60-S then 300-S; 50 °C, 0.75 cm3/min; methanol:ethylene glycol 60:40 with unreported ratio basis, 1.5e-3 M sodium methylate and 0.1 M tetrabutylammonium bromide. Polymer-calibrated equivalent size includes aggregates.'),
 'TEM':('Holey carbon support and electron microscope','JEOL 2000-FX, 200 keV electron energy. Direct aerosol collection OR colloid evaporation; specimen-specific preparation branch unresolved.'),
 'IR':('Powder grinding and KBr pellet, then spectrometer','Analytical preparation; matrix amount, pellet pressure and most acquisition details unknown.'),
 'powder-XRD':('Powder in AOT soap OR Mylar enclosure on optical fiber tip','Alternative mounting preparations; Mo K-alpha, triple-crystal spectrometer, Rigaku 12 kW rotating anode and graphite optics. Keep measured pattern and fitted model separate.'),
 'optical-acquisition':('Cuvette and optical instruments','Absorption and emission instruments differ. Preserve main-text 350 nm versus Figure 9 caption 355 nm excitation discrepancy.'),
 'time-resolved-PL':('Pulse excitation, sample, photomultiplier and storage oscilloscope','1.0 colloid; picosecond 355 nm pulse and 10 ns resolution. Fitted 17/76 microsecond components are not a universal radiative lifetime.')}
support = []
procedure_ids={'acid-activation':'littau-1993-si-acid-activation','concentrate':'littau-1993-si-colloid-concentration',
 'dry-powder':'littau-1993-si-powder-preparation','HPLC':'littau-1993-si-hplc-fractionation',
 'TEM':'littau-1993-si-tem-characterization','IR':'littau-1993-si-ir-characterization',
 'powder-XRD':'littau-1993-si-xrd-characterization','optical-acquisition':'littau-1993-si-optical-characterization',
 'time-resolved-PL':'littau-1993-si-time-resolved-pl'}
for proc in ex['supporting_procedures']:
    sid=proc['id']; scene, rule=support_scenes[sid]
    pp=BASE/'procedure-drafts'/(procedure_ids[sid]+'.json')
    support.append({'staging_id':sid,'record_id':procedure_ids[sid], 'draft_path':str(pp),'sha256':sha(pp),
        'record_type':'procedure','status':'Written private draft; passed the root bounded independent procedure/source-join audit. Reader integration and full item coverage remain pending.',
        'scene':scene,'reader_rule':rule,'source_extraction':proc,'requested_tasks':[]})

chem_notes = {
 'disilane':('Si2H6','molecule','No verified registry match; validate identity and asset source before adding.'),
 'helium':('He','atom','Carrier gas; no bonding model.'),
 'oxygen':('O2','molecule','Oxidant stream; separate from silicon source.'),
 'ethylene-glycol':('C2H6O2','molecule','Collection solvent and HPLC component are distinct use stages.'),
 'dichlorosilane':('SiH2Cl2','molecule','Printed reagent verified; frit treatment only.'),
 'sodium-methoxide':('CH3NaO','ionic-components','Source synonym sodium methylate; do not invent solution ion pairing.'),
 'tetrabutylammonium-bromide':('C16H36BrN','ionic-components','Do not reuse tetraoctylammonium bromide or tetraoctylphosphonium bromide models.'),
 'polystyrene-sulfonate-sodium':(None,'polymer-reference','Calibration polymer molecular weights and chain lengths unresolved; no single discrete molecular model.'),
 'ethylene-dichloride':('C2H4Cl2','molecule','Conventional identity 1,2-dichloroethane; retain source wording ethylene chloride in the TEM washing passage.'),
 'acetone':('C3H6O','molecule','Analytical washing solvent.'),
 'potassium-bromide':('KBr','ionic-components','IR pellet matrix.'),
 'aot':(None,'identity-unresolved','Paper uses unexpanded AOT; do not silently assign a particular formula/model.'),
 'mylar':(None,'polymer-support','Support film; no reported precise formulation or chain length.'),
 'sulfuric-acid':('H2SO4','molecule-reference','Reference model does not specify acidic-water composition, dose or aqueous speciation.'),
 'rhodamine-6g':(None,'identity-partially-specified','Exact salt/counterion and concentration are unresolved; quantum-yield reference in ethanol, not a synthesis input.'),
 'toluene':('C7H8','existing-reference','CID 1140; frit-treatment solvent.'),
 'methanol':('CH4O','existing-reference','CID 887; HPLC solvent.'),
 'argon':('Ar','existing-reference','CID 23968; activation atmosphere.'),
 'water':('H2O','existing-reference','CID 962; acid activation.'),
 'ethanol':('C2H6O','existing-reference','CID 702; optical standard solvent.')}
chemicals=[]
for cid,(formula,kind,note) in chem_notes.items():
    chemicals.append({'id':cid,'formula':formula,'model_kind':kind,'note':note,
        'asset_status':'Existing validated registry reference may be reused.' if kind=='existing-reference' else 'No asset obtained or identity lookup performed in this task.',
        'depiction_scope':'Reference chemical identity only; not measured solution structure.'})

sections=['Precursors','Synthesis protocol','Final structures','Properties','Chemical intuition']
asset_sections={'figure-1':[sections[1]],'table-1':[sections[2],sections[3]],'figure-2':[sections[3]],
 'figure-3':[sections[2]],'figure-4':[sections[2]],'figure-5':[sections[2]],'figure-6':[sections[2]],
 'figure-7':[sections[3],sections[2]],'figure-8':[sections[2]],'figure-9':[sections[3]],
 'figure-10':[sections[3]],'figure-11':[sections[3]],'figure-12':[sections[3]]}
asset_scopes={
 'figure-1':'Shared apparatus for 6.0, 2.0 and 1.0. Not the earlier AKS41 apparatus; preserve 860/865 °C conflict.',
 'table-1':'Separate formulation rows and analytical techniques; PL column belongs to activated colloids. Not a single specimen with every measurement.',
 'figure-2':'Upper 6.0 and lower 2.0 absorption. No 1.0 or AKS41 trace is shown.',
 'figure-3':'AKS41 aggregate only. One depicted lattice-resolved core; contextual card, never the selected 6.0/2.0/1.0 micrograph.',
 'figure-4':'AKS41 HPLC. Original caption spells ASK41; surrounding text identifies AKS41. Separate aggregates and monomers.',
 'figure-5':'6.0 HPLC; aggregate distribution and monomer shoulder are distinct.',
 'figure-6':'Prepared powders: upper 6.0 and lower 2.0. Measured traces, diamond-Si fits and arbitrary Gaussian background are distinct evidence classes.',
 'figure-7':'Powder from 6.0. Source prose incorrectly cross-references XRD as Figure 5; actual XRD is Figure 6.',
 'figure-8':'1.0 HPLC with monomer and aggregates; does not establish a crystalline core.',
 'figure-9':'6.0 before activation (lower) versus after activation (upper). Caption 355 nm excitation conflicts with 350 nm prose.',
 'figure-10':'Activated 2.0 according to surrounding discussion; caption alone only says 2.0.',
 'figure-11':'Activated 1.0 according to surrounding discussion; no direct phase assignment follows from emission.',
 'figure-12':'1.0 in activation context; measured decay and fitted 17/76 microsecond components must be distinguished.'}
assets=[]
for item in manifest['items']:
    p=BASE/'crop-assets'/item['file']; actual=sha(p); assert actual==item['sha256']
    assets.append({**item,'sample_scope':asset_scopes[item['id']], 'private_asset_path':str(p),
        'proposed_public_asset':'assets/paper-reviews/littau1993/'+item['file'],
        'desired_sections':asset_sections[item['id']], 'source_sha256':source_hash,
        'hash_verified_in_this_task':True,'raw_data_digitized':False,'eligible_training':False})

spec = {
 'spec_version':'1.0.0','status':'Private integration specification; no Site change, publication or training promotion performed.',
 'paper':{'doi':'10.1021/j100108a019','title':'A Luminescent Silicon Nanocrystal Colloid via a High-Temperature Aerosol Reaction',
 'authors':'K. A. Littau; P. J. Szajowski; A. J. Muller; A. R. Kortan; L. E. Brus','year':1993,
 'journal':'Journal of Physical Chemistry','volume':97,'pages':'1224–1230','source_group':'littau1993',
 'existing_paper_id':'paper-c93e8dc8393a5d19cda8','existing_document_id':'doc-01944414b621171a9ec0',
 'source_path':str(source),'source_sha256':source_hash,'page_count':7,
 'duplicate_path':'[local path redacted]',
 'identity_rule':'Reuse existing corpus IDs; upgrade bibliographic year/title and verified contribution. Do not count the identical incoming file as another paper.',
 'si_status':'Not located or verified; this is a complete supplied-main review, not a main-plus-SI review.',
 'public_export_rule':'Publish source identifiers, DOI, file hash and page locators; exclude machine-local paths and full extracted article text.'},
 'review_scope':{'source_extraction_sha256':sha(BASE/'source-extraction.json'),
 'reused_prior_reviews':'Existing all-seven-page extraction and independent source/crop audits. This task does not claim to repeat that full-paper review.',
 'current_task':'Read staging extraction, draft audits and manifest; reconcile corpus and reader implementation; verify all 13 crop hashes; inspect apparatus/reagent source and bounded AKS41 pages/crops.',
 'canonical_milestone':'Three synthesis drafts and nine supporting-procedure drafts passed bounded scientific/source-join audits. The root procedure audit covers nine records and 21 measurement/reference/cohort entries. All thirteen private records including AKS41 contain 48 entries and validate; full item coverage and reader integration remain pending.',
 'procedure_audit':{'path':str(BASE/'procedure-drafts-independent-audit.json'),'sha256':sha(BASE/'procedure-drafts-independent-audit.json'),'status':read(BASE/'procedure-drafts-independent-audit.json')['status']}},
 'reader_identity':{'material':'Si/SiOx','method_family':'Continuous-flow aerosol synthesis with subsequent liquid collection',
 'five_sections':sections,'header':'Full academic title, authors/year, DOI and explicit main-only review scope.',
 'crystal_viewer':'No experimentally identified CIF exists in the supplied source. A future independently sourced diamond-Si reference must be labeled external reference, never the experimental nanocrystal or 1.0 phase proof.'},
 'candidate_record_plan':{'synthesis_variants':variants,'supporting_procedures':support,
 'context_record':{'record_id':'littau-1993-aks41-context','path':str(BASE/'context-drafts/littau-1993-aks41-context.json'),
 'sha256':sha(BASE/'context-drafts/littau-1993-aks41-context.json'),
 'audit_status':read(BASE/'context-draft-audit.json')['status'],
 'record_type':'observation','scope':'Earlier-apparatus sample with incomplete preparation; figures 3 and 4 remain contextual. No synthesis operations or requested tasks.'},
 'count_rule':'Three formulation drafts, nine supporting-procedure drafts and one contextual observation draft are thirteen private content records, not thirteen experiments or published records.'},
 'chemical_registry_plan':chemicals,'scene_stages':stages,
 'stock_panels':[
 {'id':'Si2H6-in-He','scope':'Commercial 0.1% feed stock; fraction basis unknown. Flow selection uses the mixture.'},
 {'id':'O2-He-diluent','scope':'Separate O2:He 1:6 stream; Figure 1 rates 1000 and 6000 sccm.'},
 {'id':'frit-treatment','scope':'SiH2Cl2 in toluene; composition and treatment conditions unknown.'},
 {'id':'acidic-water','scope':'pH 1 sulfuric-acid water added at 5%, denominator unspecified; not a quantified sulfuric-acid stock.'},
 {'id':'HPLC-mobile-phase','scope':'60:40 methanol/ethylene glycol; 1.5e-3 M sodium methylate and 0.1 M tetrabutylammonium bromide; solvent-ratio basis unknown.'}],
 'original_assets':assets,
 'section_rules':{
 sections[0]:'Group gas feeds, apparatus treatment, collection solvent, post-treatment and analytical chemicals by actual use. Do not list all twenty as mandatory furnace inputs.',
 sections[1]:'Choose 6.0/2.0/1.0 formulation, show the same flow selection in cards and continuous-flow scene. Branch optional activation, concentration, drying and characterization rather than flattening them into one recipe.',
 sections[2]:'Show technique-specific size values, current-formulation XRD/HPLC, and a separately labeled AKS41 contextual panel. No displayed SAED pattern is supplied. No Raman data are reported.',
 sections[3]:'Distinguish as-made versus acid-activated optical states. Activated PL peaks 970/770/660 nm correspond to 6.0/2.0/1.0; quantum yields are reported slightly above 5%, not precisely 5% for as-made product. Keep instrument conditions and fitted decay constants separate.',
 sections[4]:'Render source chemical-intuition entries as author interpretations/hypotheses. Confinement, oxide/passivation and noncrystalline possibilities do not create new measured phases or recipe outcomes.'},
 'implementation_issues':[
 {'priority':'must_fix','file':'dist/protocol-visuals.mjs','issue':'Current generic action matching renders gas feeds/pyrolysis/oxidation/collection as preparation vials, and gas dilution as a cooling vial. Add explicit continuous-flow scenes with two tube furnaces and serial bubblers.'},
 {'priority':'must_fix','file':'dist/protocol-visuals.mjs','issue':'The first matching temperature/time field is insufficient. Display both 860/865 °C sources, distinguish 60/20 ms residence from run time, and retain raw dilution notation 1:23.'},
 {'priority':'must_fix','file':'dist/material-guide.mjs','issue':'Ledger presence must not trigger an unconditional complete main/SI review claim. This paper has seven reviewed main pages and unverified SI availability.'},
 {'priority':'must_fix','file':'dist/material-guide.mjs','issue':'Filter and contextualize figures by formulation, specimen preparation and activation state. Route Table I from tables as well as figures; avoid assigning every paper figure to every method.'},
 {'priority':'must_fix','file':'data/corpus/library-source.json','issue':'Reuse existing paper/document identity. Upgrade its candidate-only contribution status only after audited records are integrated.'},
 {'priority':'remaining','file':'canonical drafts and registries','issue':'Nine procedure drafts including activated-state optical entries are now written and root-audited; see procedure-drafts-independent-audit.json (9 records, 21 entries). AKS41 bounded audit is closed after verified corrections. Full item-coverage checks, reader state/figure joins and molecular assets remain necessary before canonical/public completion.'}],
 'acceptance_checks':[
 'All 13 original assets retain axes, scale bars, labels, source pages and hashes; no curve digitization claimed.',
 'AKS41 Figure 3/4 evidence cannot be selected as measured evidence for 6.0, 2.0 or 1.0.',
 'No experimental CIF or synthetic SAED image is introduced.',
 'The 1.0 formulation has no observed core/XRD coherence length; do not convert not-observed to zero or measured 2 nm.',
 'Table I total particle size, core size, coherence length, HPLC equivalent diameter and activated PL remain distinct properties.',
 'Figure 6 model fits and Figure 12 fitted decay parameters remain labeled as derived/model values.',
 'Unknown run duration, stock percentage basis, collection pressure and acid dose remain unknown.',
 'Serial collection yields two physical fractions; current formulation products retain unresolved collector/specimen joins.',
 'Requested training tasks remain empty until record-specific eligibility is independently reviewed.',
 'Bibliographic identity, original-asset rights, canonical audit completion and website publication are separate statuses.']}
assert len(assets)==13 and len(chemicals)==20 and len(support)==9
dump('reader-integration-spec.json', spec)

lines=['# Littau 1993 reader integration specification','',
 spec['paper']['title']+' — DOI '+spec['paper']['doi']+'.','',
 'Private specification only. Reuse paper-c93e8dc8393a5d19cda8 and doc-01944414b621171a9ec0; the incoming and existing PDFs have the same hash. Seven main pages are reviewed; matching SI is not located or verified.','',
 '## Reader and record structure','',
 'Use the five academic sections: Precursors; Synthesis protocol; Final structures; Properties; Chemical intuition. Keep sources and review limitations in an appendix. The three formulations use 6.0, 2.0 or 1.0 sccm of a 0.1% disilane/helium stock, not pure disilane. They are not identified physical batches. Nine supporting procedures and an AKS41 observation remain separate content types. The nine procedure drafts and 21 entries have passed the root bounded independent audit; all thirteen private records and 48 entries validate. Full item coverage and reader joins remain pending.','',
 '## Continuous-flow apparatus','',
 '| Stage | Scene and conditions | Scope |','|---|---|---|']
for s in stages:
    lines.append('| '+s['id']+' | '+s['scene']+' '+ ' '.join(s['conditions'])+' | '+' '.join(s['scope_and_limits'])+' |')
lines += ['', '## Molecular identities','',
 'Reuse validated references for toluene, methanol, argon, water and ethanol. Fifteen other identity/model entries need reviewed registry treatment. AOT is unexpanded; polymer and Rhodamine 6G salt specifications remain incomplete. Tetrabutylammonium bromide is not tetraoctylammonium bromide. Frit treatment uses printed SiH2Cl2 in toluene. The JSON lists all twenty chemicals by role and model limits.','',
 '## Original figure and table routing','',
 '| Asset | Page | Reader section | Exact scope |','|---|---|---|---|']
for a in assets:
    lines.append('| '+a['id']+' | '+str(a['pdf_page'])+' / '+str(a['printed_page'])+' | '+', '.join(a['desired_sections'])+' | '+a['sample_scope']+' |')
lines += ['', '## Required implementation work','']
lines += ['- '+x['issue'] for x in spec['implementation_issues']]
lines += ['', '## Review limits','',spec['review_scope']['reused_prior_reviews'],
          'All thirteen crop hashes and the source hash were checked in this task. No new molecular/crystal assets, Site modifications, downloads, training promotion or publication were performed. The companion AKS41 draft audit records its own bounded source and join review.','']
(BASE/'reader-integration-spec.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({'spec':str(BASE/'reader-integration-spec.json'),'markdown':str(BASE/'reader-integration-spec.md'),
 'assets':len(assets),'synthesis_variants':len(variants),'supporting_procedures':len(support),'chemical_identities':len(chemicals)}))
