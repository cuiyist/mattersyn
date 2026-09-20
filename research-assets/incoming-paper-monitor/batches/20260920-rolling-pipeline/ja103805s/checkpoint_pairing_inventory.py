"""Freeze the actual first complete reading; not a completed extraction/audit."""
from pathlib import Path
import hashlib,json,datetime
B=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,obj):
    (B/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
prep=json.loads((B/'source-preparation.json').read_text(encoding='utf-8'))
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
docs={}
for i,d in enumerate(prep['documents']):
    role=['main','si','cif'][i]
    assert sha(d['source_path'])==d['sha256']
    docs[role]={'path':d['source_path'],'original_filename':d['original_filename'],'sha256':d['sha256'],'bytes':d['bytes'],'page_count':d.get('pdf_page_count'),'verified_at':now}
pairing={
 'schema':'mattersyn-private-pairing-review/1','source_id':'evans2010','doi':'10.1021/ja103805s','author':'/root/norberg2004_extract','created_at':now,
 'status':'author_content_pairing_complete_pending_independent_audit','source_documents':docs,
 'title':'Mysteries of TOPSe Revealed: Insights into Quantum Dot Nucleation',
 'authors':['Christopher M. Evans','Meagan E. Evans','Todd D. Krauss'],
 'bibliography':'J. Am. Chem. Soc. 2010, 132, 10973–10975',
 'pairing_evidence':[
  {'link':'main_to_si','locators':['main PDF1 title/byline/DOI footer','SI S1 title/byline','main PDF3 Supporting Information Available'],'finding':'Identical full title and three authors. Main declares QD synthesis experiments, observed products, NMR and species-9 X-ray crystal structure, all present in the 21-page SI.'},
  {'link':'si_to_cif','locators':['SI S15 Figure S12 and crystallographic paragraph','SI S16 Scheme S1/species-9 preparation','SI S17 Figure S13 and metric paragraph','CIF data_krace01, chemical formula/cell/diffraction/geometry tags'],'finding':'Molecular formula C24 H20 P2 Pb Se4 and atom labels Pb1/Se1–4/P1–2/C1–24 match species 9. Yellow rod 0.22×0.10×0.08 mm, 100.0(1) K, P-1, Bruker SMART APEX II CCD, 29063 measured reflections, and Pb–Se distances 2.9969(4), 3.0350(4), 3.4029(4) Å agree with SI descriptions. CIF does not carry the paper title/DOI; pairing is content-supported, not filename-only.'}
 ],
 'cif_scope':{'species':'9, Pb(Se2PPh2)2 molecular crystal','formula':'C24 H20 P2 Pb Se4','block':'data_krace01','space_group':'P -1','cell_a_A':'9.0041(4)','cell_b_A':'11.0498(5)','cell_c_A':'12.8215(6)','cell_alpha_deg':'80.593(1)','cell_beta_deg':'89.867(1)','cell_gamma_deg':'82.296(1)','cell_volume_A3':'1246.89(10)','Z':2,'quantum_dot_structure_pair':False,'restrictions':['Do not assign this CIF to PbSe/CdSe QDs or magic-size clusters.','Do not identify postulated intermediates 1, 6, 10, 11 or 14 as isolated atomic structures.','Atom/geometry loop semantic extraction and parser validation remain pending.','The leading publication-reference field precedes data_krace01; preserve original bytes and report parser handling rather than silently rewriting.']},
 'source_mutation':False,'downloads':False,'independent_pairing_audit':'pending','canonical_or_training_approval':False}
write('pairing-review.json',pairing)

# These are manually authored page inventories from the completed text and visual reading.
main=[
 ('10973','Title/abstract/background; Figure 1 A/B/C absorption; Table 1 eight identified compounds and all footnotes. Pure tertiary-phosphine controls, secondary impurities and room-temperature reactivity. Background literature is not a measured sample.'),
 ('10974','Scheme 1 proposed DPPSe/metal-oleate mechanism and Scheme 2 proposed DPP/Pb-oleate route. Unisolated intermediates, ratio dependence, 24 h byproduct chemistry, DPP-added TOPSe observations. Cd/Pb ratio narrative ambiguity retained.'),
 ('10975','Figure 2 TOPSe+15 mol% DPP before/30 min after Pb oleate at40°C; mechanistic limitations, >90% optical conversion claims, ligand/aggregation note, future S/Te expectations, acknowledgments, SI declaration, all11 numbered references/13 bibliography subentries.')]
si=[
 'Cover/title/authors; complete reagent supplier/purity list, NMR preparation/acquisition, Cd/Pb oleate preparation/workup and TOPSe stock synthesis.',
 'DPPSe, TIPPSe, TEPSe, TPPSe preparation/purification and NMR identity; pure-tertiary negative control followed by DIPP rescue, and stated TEPSe/TPPSe analogues.',
 'Figure S1 four NMR panels: 90% Aldrich and97% Strem TOP and DOP/DOPO coupling details. Plot labels and unassigned peaks retained in original image; not all are species assignments.',
 'Figure S2 tributylphosphine impurity31P spectra/DBP identity; individual unassigned plot peaks remain unassigned.',
 'Figure S3 A–G TOPSe impurities, tentatively assigned P(V) selenide species, P–Se/P–H splittings, capillary H3PO4 standard.',
 'TOPSe distillation10mL/50mTorr,2mL fractions185/190/195°C,~4mL residueC; separately made1M stockB; Figure S4 A–C31P spectra. B preparation prose/caption difference retained.',
 'Inline A/B/C composition table from31P integration; controlled PbSe MSC synthesis and Figure S5 A–C absorption time courses. Main Figure1 is40min comparison; individual S5 curve times unreported.',
 'DPP/Pb oleate sealed-tube140°C experiment and DPP/Cd oleate no-reaction control after several days. Printed Pb oleate mass/mmol inconsistency retained.',
 'Figure S6 A–F31P DPP/Pb time series0/10/20/40/60/240min with printed DPP/tetraphenyldiphosphine integrals; standard100 is not a chemical yield.',
 'Figure S7 A–F1H same time series with DPP and oleic-acid integrals; exact sample correspondence to Figure S6.',
 'Figure S8 A/B/C31P DPPSe:Cd oleate2:1/1:1/1:2 near10min room temperature; 875Hz inset for compound8; unassigned peaks retained.',
 'Figure S9 DPPSe:Pb oleate1:1 near10min room temperature31P spectrum; identifiable and unassigned resonances retain original context.',
 'Figure S10 A/B at10min and C/D at24h for DPPSe:Cd oleate1:2; acid and intermediate3 change into4/5; crystals13 after slow evaporation. Unnumbered proposed2eq4→13+DPP scheme at bottom.',
 'Figure S11 13C same24h sample as S10 C/D;169ppm-region oleic anhydride identification, no new synthesis batch.',
 'Single-crystal9 acquisition/refinement description and Figure S12 atom-labelled molecular structure; excessDPPSe>5:1; SIR97 superscript4 not resolved by the supplied SI reference list.',
 'Scheme S1 proposed paths through1/6/14 to9; stable9 crystallization500uL0.1M DPPSe+100uL0.1M Pb oleate, slow room-temperature evaporation several days. Nominal5:1 charge vs stated>5:1 boundary retained.',
 'Figure S13 intermolecular9 packing and Pb–Se distances/angles. Similarity to rocksalt propagation is author mechanistic interpretation, not PbSe-QD crystallographic data.',
 'Figure S14 two proposed alternative secondary-phosphine/metal-oleate/Se-exchange routes; no new isolated coordinates or quantified kinetic experiment.',
 'Separate explicit PbSe80°C sealed-N2 cuvette recipe and CdSe200°C rapid-injection recipe. Oleic-acid amounts, stock quantities and atmospheres retained; no invented quench/workup.',
 'Figure S15 absorption/fluorescence CdSe10min and PbSe20min without postprocessing or size-selection. Figure S16 PbSe spherical and cubic TEM examples with5nm and20nm scale bars; bars are not particle diameters; individual recipe-panel joins incomplete.',
 'Representative PbSe conversion-yield calculation, empirical optical diameter/extinction equations and all numerical steps;93% optically derived. Printed final denominator exponent conflict and differing charge/volume vs S19 sample retained. Two SI references.'
]
pages=[]
for role,descs in [('main',main),('si',si)]:
 d=prep['documents'][0 if role=='main' else 1]
 for idx,desc in enumerate(descs,1):
  printed,coverage=desc if role=='main' else (f'S{idx}',desc)
  text=d['text_pages'][idx-1]; render=d['rendered_pages'][idx-1]
  assert sha(text['path'])==text['sha256'] and sha(render['path'])==render['sha256']
  pages.append({'source_role':role,'pdf_page':idx,'printed_page':printed,'source_sha256':d['sha256'],'text_asset':text,'original_page_render':render,'text_read':True,'visually_inspected':True,'reader':'/root/norberg2004_extract','reading_completed_before_checkpoint_at':now,'coverage_notes':coverage,'typed_extraction_complete':False,'unread_regions':[],'plot_raw_data_digitization':'not_performed','high_resolution_selected_crops':'pending'})
write('page-coverage.json',{'schema':'mattersyn-page-coverage/1','source_id':'evans2010','status':'all_supplied_pdf_pages_read_and_visually_inspected_extraction_pending','created_at':now,'pages':pages,'counts':{'main_pages_read':3,'main_pages_visually_inspected':3,'si_pages_read':21,'si_pages_visually_inspected':21,'unread_pdf_pages':0},'cif_text_read_entirely':True,'cif_structured_loop_inventory_complete':False,'independent_audit':'pending'})

objects=[]
def obj(identifier,role,page,kind,scope,note=''):
 objects.append({'id':identifier,'source_role':role,'pdf_page':page,'printed_page':str(10972+page) if role=='main' else f'S{page}','kind':kind,'sample_scope':scope,'source_sha256':docs[role]['sha256'],'source_page_asset':next(p['original_page_render']['path'] for p in pages if p['source_role']==role and p['pdf_page']==page),'selected_crop':'pending','notes':note,'independent_review_status':'pending'})
obj('figure-1','main',1,'figure','PbSe MSC composition-controlled A/B/C at40min40°C')
obj('table-1','main',1,'table','8 observed compounds, solution NMR identity','Separate 1H/31P/13C shifts and authentic-sample/crystal evidence; no automatic coordinate availability for12/13.')
obj('scheme-1','main',2,'scheme','author-proposed DPPSe/Pb oleate mechanism','Intermediate labels are not isolated species unless explicitly stated.')
obj('scheme-2','main',2,'scheme','author-proposed DPP/Pb oleate reduction mechanism')
obj('figure-2','main',3,'figure','15mol% DPP/TOPSe before and30min after Pb oleate40°C')
for n,page,scope in [(1,3,'TOP commercial purity/impurity panels'),(2,4,'tributylphosphine impurity'),(3,5,'TOPSe impurity identities and couplings'),(4,6,'distilledA/residueC and separateB stock'),(5,7,'PbSe MSC A/B/C absorption kinetics'),(6,9,'DPP/Pb oleate31P time course'),(7,10,'same DPP/Pb oleate1H time course'),(8,11,'DPPSe/Cd oleate three stoichiometries'),(9,12,'DPPSe/Pb oleate1:1'),(10,13,'Cd reaction10min versus24h'),(11,14,'same Cd reaction24h13C'),(12,15,'isolated molecular species9'),(13,17,'species9 intermolecular packing'),(14,18,'two hypothesized monomer-generation routes'),(15,20,'separate CdSe/PbSe optical examples'),(16,20,'two PbSe TEM morphology examples')]:
 obj(f'figure-S{n}','si',page,'figure',scope)
obj('scheme-S1','si',16,'scheme','hypothesized paths to isolated molecular species9')
obj('scheme-S13-unnumbered','si',13,'unnumbered_scheme','proposed diphenylphosphine oxide disproportionation to13+DPP')
assert len(objects)==23
conflicts=[
 {'id':'C1','locator':'SI S2 pure-tertiary control','printed_values':'23.0mg TIPPSe (48umol)','issue':'Mass and amount do not agree with SeP(C3H7)3 formula; preserve both. Exact concentration/stoichiometry cannot be silently repaired.'},
 {'id':'C2','locator':'SI S8 Pb control','printed_values':'0.22g Pb(oleate)2 (0.57mmol)','issue':'Mass and amount do not agree with stated Pb(C18H33O2)2 formula; preserve both and avoid silently doubling or halving.'},
 {'id':'C3','locator':'main PDF2 ratio paragraph','printed_values':'DPPSe/Cd(oleate)2 variation10:1 to1:2, then PbSe/species9 discussion','issue':'Mixed Cd/Pb narrative identity; SI-resolved specific experiments must not inherit an unsupported generic metal identity.'},
 {'id':'C4','locator':'SI S6 prose vs Figure S4 caption','printed_values':'B made by dissolving TOPSe in TOP versus dissolving selenium in TOP','issue':'B is a separate1M stock, not a distillation fraction; source wording differs concerning the dissolved starting species.'},
 {'id':'C5','locator':'SI S15–16 species9 formation','printed_values':'>5:1 excess description versus500uL0.1M DPPSe+100uL0.1M Pb oleate (nominal5:1)','issue':'Preserve threshold wording and exact preparation separately.'},
 {'id':'C6','locator':'SI S21 final conversion expression','printed_values':'denominator2.25×10^6 mol versus starting2.25×10^-6 mol','issue':'Final printed positive exponent conflicts with initial limiting charge and93%; raw expression must remain visible; any interpretation/repair labelled.'},
 {'id':'C7','locator':'SI S15 SIR97 superscript4 vs SI S21 references','printed_values':'SIR97^4 but only references1–2 supplied','issue':'Unresolved citation pointer. CIF retains a SIR97 bibliography entry, without proving identity of the missing SI numbering.'}
]
inventory={'schema':'mattersyn-source-inventory-checkpoint/1','source_id':'evans2010','doi':'10.1021/ja103805s','created_at':now,'authoring_status':'complete_first_reading_inventory_checkpoint_not_complete_typed_extraction','source_documents':docs,'page_inventory':[{k:p[k] for k in ['source_role','pdf_page','printed_page','coverage_notes']} for p in pages],'figure_table_scheme_inventory':objects,'counts':{'pdf_pages':24,'main_figures':2,'main_numbered_tables':1,'main_schemes':2,'si_numbered_figures':16,'si_numbered_schemes':1,'si_unnumbered_schemes':1,'total_figure_table_scheme_objects':23,'main_numbered_references':11,'main_bibliographic_subentries':13,'si_numbered_references':2},'additional_source_units_to_type':['S7 A/B/C composition table','S21 complete worked numerical yield calculation and empirical equations','CIF scalar fields and all atom/anisotropy/geometry loops','all captions, table footnotes, method paragraphs, acknowledgments and cited/observed/model distinctions'],'candidate_experiment_boundaries':['Cd oleate preparation','Pb oleate preparation, explicit inheritance from Cd procedure','TOPSe preparation','DPPSe preparation','TIPPSe preparation','TEPSe preparation','TPPSe preparation','TIPPSe/Pb negative control and DIPP rescue with analogous TEPSe/TPPSe outcomes','TOPSe distillation and independentB stock','PbSe MSC A/B/C impurity-comparison family','DPP/Pb thermal control and associated NMR time course','DPP/Cd negative thermal control','DPPSe/Cd ratio-family NMR observation','DPPSe/Pb1:1 NMR observation','Cd10min/24h observation and slow organic transformation','isolated species9 crystal preparation','PbSe80°C QD synthesis','CdSe200°C QD synthesis','representative optical PbSe conversion calculation with incomplete recipe join','author mechanistic/cited-background contexts, not additional syntheses'],'sample_join_limits':['S15 optical specimens not automatically identical to the two S16 TEM specimens.','S21 representative conversion sample has2.25umol selenium and3.025mL versus S19 recipe10umol selenium and approximately4mL; no exact shared batch asserted.','Only species9 supplied coordinates; MSC/QD exact atomic structures absent.','Unassigned plotted NMR peaks retain original assets without invented chemical identity.','Broad >90% conversion claim is extinction-coefficient-based, not isolated mass yield.'],'source_conflicts':conflicts,'absent_or_unestablished':['Quantum-dot CIF or measured atomic coordinates','QD powder XRD/SAED/Raman','NMR raw FID files','Full quantitative reaction-rate analysis','Precisely timed/quench/workup details for both QD recipes','TEM specimen preparation and numeric size distribution','Full stoichiometric replacement charges for analogous TEPSe/TPPSe negative controls'],'next_actions':['Create complete source-facts.json with typed quantities and precise evidence pointers.','Expand source-inventory.json into all scientific units/complete payloads; preserve checkpoint snapshot.','Extract all CIF scalar/loop payloads with raw uncertainties and source-line provenance; record parser result.','Create readable selected original figure/table/scheme crops with hashes/bounds and visually verify them.','Build sample lineage, missingness/conflicts, original-label NMR annotations and source references.','Freeze complete author package and request independent scientific audit.','Only after audit consider canonical records, visuals, reader and publication.'],'all_training_admission':False,'independent_scientific_audit':'pending','publication_status':'not_published'}
write('source-inventory.json',inventory)
notes='''# Evans 2010 — first complete reading checkpoint

The original 3-page article, 21-page SI and CIF have unchanged intake hashes. All 24 PDF pages were read as text and visually inspected; the entire CIF was read. This is an early durable pairing and inventory checkpoint, not a completed typed extraction, independent audit, canonical dataset or published reader.

The CIF is the molecular termination species 9, Pb(Se2PPh2)2 (C24H20P2PbSe4), matched by SI identity, atom labels, crystal/acquisition details and bond metrics. It must never be assigned as PbSe/CdSe quantum-dot coordinates. It contains a publication-reference field before its data block; structured parsing and complete loop inventory are pending.

There are 23 figure/table/scheme objects, including the unnumbered reaction scheme on S13, plus an inline composition table and the S21 worked conversion calculation. Original full-page renderings remain private; selected readable crops are pending. Dense spectra are retained as original images; no raw-curve digitization or complete numeric peak annotation is yet claimed.

The inventory distinguishes seven precursor preparations, control/ratio families, a molecular-crystal preparation and two explicit QD recipes. Candidate boundaries are not final recipe counts. Main/SI quantities conflict for the TIPPSe and Pb-oleate controls; the species-9 threshold and B-stock wording also differ. The conversion calculation prints a contradictory final exponent. All are retained as unresolved source issues.

Next: type all source facts, finish scientific and CIF payload inventories, create and inspect selected crops, then freeze for a different agent's independent audit. No source, Site, shared queue, root memory or GitHub file has been modified.
'''
(B/'extraction-notes.md').write_text(notes,encoding='utf-8')
snapshot=B/'checkpoints'/'pairing-inventory-v1';snapshot.mkdir(parents=True,exist_ok=True)
names=['pairing-review.json','page-coverage.json','source-inventory.json','extraction-notes.md','source-preparation.json','checkpoint_pairing_inventory.py']
bound=[]
for name in names:
 source=B/name;dest=snapshot/name
 if dest.exists(): assert dest.read_bytes()==source.read_bytes(),f'Frozen checkpoint differs: {name}'
 else: dest.write_bytes(source.read_bytes())
 bound.append({'path':str(dest),'sha256':sha(dest),'bytes':dest.stat().st_size})
write('checkpoint-freeze.json',{'schema':'mattersyn-private-author-checkpoint-freeze/1','source_id':'evans2010','created_at':now,'scope':'First complete reading and content-pairing inventory; scientific extraction/audit/canonical/publication pending','author':'/root/norberg2004_extract','files':bound,'source_documents':docs,'all_pdf_pages_text_and_visual_read':24,'training_admission':False})
print(json.dumps({'freeze_sha256':sha(B/'checkpoint-freeze.json'),'pairing_sha256':sha(B/'pairing-review.json'),'inventory_sha256':sha(B/'source-inventory.json'),'page_coverage_sha256':sha(B/'page-coverage.json'),'status':'early_checkpoint_saved_not_extraction_complete'},indent=2))
