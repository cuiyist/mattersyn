from pathlib import Path
import json, hashlib
from datetime import datetime, timezone

B = Path(r'[local path redacted]')

def e(role, page, locator, finding):
    return dict(document_role=role, pdf_page=page, locator=locator, finding=finding)

def fig(role, label, pages, scope):
    return dict(document_role=role, label=label, pdf_pages=pages, scope=scope)

data = {
 'jp0219348': {
  'title':'Spatially Ordered Quantum Dot Array of Indium Nanoclusters in Fully Indium-Exchanged Zeolite X',
  'authors':['Nam Ho Heo','Jong Sam Park','Young Joo Kim','Woo Taik Lim','Sung Wook Jung','Karl Seff'],
  'journal':'The Journal of Physical Chemistry B', 'year':2003, 'volume':'107', 'printed_pages':'1120–1128',
  'pairing_status':'matched_by_manuscript_identifier_and_specific_content_with_header_conflict',
  'pairing_evidence':[
   e('main',1,'Title, authors, journal header and DOI footer','The published article prints the title and six authors above, J. Phys. Chem. B 2003,107,1120–1128 and DOI 10.1021/jp0219348.'),
   e('main',9,'Supporting Information Available','Declares observed and calculated structure factors squared with esds for In66-X.'),
   e('si',1,'Printed header and Supporting Table 1 title','Printed header identifies Heo jp0219348. Table title identifies observed and calculated structure factors squared with esds for In66-X, exactly the material and data type announced in the main article.'),
   e('si',list(range(1,15)),'Headers, column headings and continuous table','All fourteen pages are the same supporting structure-factor table, with h,k,l,Fcal^2,Fobs^2,sigma(Fobs^2) headings. Header page numbering runs 1–14; lower original pagination runs41–54. No experimental recipe section is present.')],
  'pairing_caveats':['SI does not repeat the full title or complete author list. Its printed header says ©2002 and J. Phys. Chem. A, whereas the published main article is J. Phys. Chem. B2003. The exact manuscript identifier, Heo name, In66-X identity and declared structure-factor content support pairing despite this header discrepancy.','The SI PDF is an image scan with no useful PDFium text layer; page images, rather than an empty text extraction, were inspected.'],
  'material_overview':['Cationic indium nanocluster array within fully indium-exchanged zeolite X; final single-crystal material is described approximately as In66Si100Al92O384 (In66-X).','Upstream supplied Na92-X host, Tl92-X ion-exchanged precursor and In87-X precursor are distinct from the final In66-X product. The proposed (In5)7+ charge and local integer oxidation states are structural/chemical interpretations, not independently measured exact molecular charges.'],
  'synthesis_overview':'The article reports dynamic aqueous Tl+ exchange of supplied zeolite X crystals, vacuum dehydration, solvent-free indium/thallium redox exchange, water washing, redehydration and H2S treatment to populate the sodalite cavities with indium clusters. The initial Na-X synthesis is attributed to a prior source, but this paper contains an explicit present-study conversion recipe.',
  'recipe_evidence':[
   e('main',2,'Experimental Section, first paragraph','Approximately0.15mm Na-X crystals in fine Pyrex capillaries are dynamically exchanged with0.1M aqueous thallous acetate at pH6.4.'),
   e('main',2,'Experimental Section, second and third paragraphs','Prose specifies vacuum dehydration623K,1e-6Torr,48h; contact with elemental In at623K96h; water wash; redehydration623K,1e-6Torr,48h; exposure to0.5atm zeolitically dried H2S for12h at673K; evacuation at temperature and room-temperature sealing.'),
   e('main',4,'Table1, upper experimental rows','Table specifies Tl+ exchange4days/10.0mL/298K; dehydration3days/673K; In reaction5days/623K; water wash1day/10.0mL; redehydration3days/673K; H2S0.5atm/12h/673K and evacuation10min/673K. Several entries conflict with prose and must remain separate source claims.')],
  'recipe_scope':'Present-study zeolite conversion with an upstream host supplied from prior work. Recipe is eligible even though some upstream methods are cited and several preparation conditions conflict. No definitive number of canonical recipes is assigned at screening.',
  'si_gaps':['The supplied SI provides diffraction structure factors, not a missing alternate synthetic procedure.','No CIF is part of these two PDFs. Atomic coordinates, thermal parameters and occupancies occur in main Table2; generating a downloadable structure would require separate careful validation.','Scanned reflection rows have not been transcribed or audited numerically.'],
  'scientific_flags':[
   e('main',[2,4],'Experimental prose versus Table1','Both initial dehydration and redehydration differ:623K48h in prose versus673K3days in table. In exchange differs:623K96h in prose versus623K5days in table. Do not merge these into one unqualified recipe.'),
   e('main',[2,4,8],'Surface residue and charge balance discussion','The gray surface powder is tentatively assigned to several possible species; it is not a verified bulk sulfide product. Oxygen loss versus proton compensation and cluster charge are alternative interpretations.'),
   e('main',3,'Figure1 caption','The reactant In87-X EPXMA spectrumB is copied from reference34; preserve its external provenance rather than assigning it to this newly synthesized product.'),
   e('main',[1,9],'Quantum-dot array/application discussion','The work has crystallographic and chemical-state evidence. Electronic storage applications are proposed; no measured electronic-storage performance is supplied.')],
  'inventory':[
   fig('main','Figure1',[3],'EPXMA product In66-X and externally sourced reactant In87-X spectra.'),
   fig('main','Figure2',[3],'XPS In3d spectra: indium metal reference, product In66-X and reactant In87-X.'),
   fig('main','Figure3',[4],'Product In66-X XPS depth-profile series.'),
   fig('main','Figure4',[5],'Stylized zeolite X framework/site drawing; a structural illustration, not microscopy.'),
   fig('main','Figure5',[7],'Stereoview of an In66-X supercage.'),
   fig('main','Figure6',[7],'Stereoview of an In66-X sodalite unit with proposed In5 cluster.'),
   fig('main','Figure7',[8],'Stereoview of adjacent sodalite units and clusters.'),
   fig('main','Table1',[4],'Experimental and crystallographic parameters, with important prose/table condition conflicts.'),
   fig('main','Table2',[5],'Atomic positional, thermal and occupancy parameters with scale factors and footnotes.'),
   fig('main','Table3',[5],'Selected interatomic distances and angles.'),
   fig('main','Table4',[6],'Guest atom/ion offsets from six-ring planes.'),
   fig('main','Table5',[6],'Author-derived ionic radii; includes previous In-A/In-X materials with citation footnotes.'),
   fig('si','Supporting Table1',list(range(1,15)),'One continuous scanned table of observed/calculated squared structure factors and esds for In66-X; not14 independent tables.'),
   fig('main','Unnumbered equations',[2,3,4,5,6,8],'Redox/disproportionation, refinement weights/scattering factors/error indices/thermal factor, and alternative charge-balance reactions. Equation-by-equation scientific extraction remains pending.')],
  'text_pages_read':{'main':list(range(1,10)),'si':[]},
  'visual_pages_inspected':{'main':list(range(1,10)),'si':list(range(1,15))},
  'coverage_note':'All nine main text pages read and all main page images inspected for screening. All fourteen SI page images inspected for identity, headings, table continuity and presence/absence of recipe prose; individual reflection rows were not fully read/transcribed or numerically audited. Empty extracted SI text was not counted as reading.',
  'next_actions':['Independently verify pairing and relevance, retaining SI header conflict.','If promoted to full review, extract the explicit preparation alongside separate contradictory Table1 conditions; do not resolve by guessing.','Curate seven figures, five main tables, source equations and the full scanned structure-factor attachment with sample/citation boundaries.','Keep supplied upstream host method cited and unknown details explicit; do not download further papers during this batch intake.']
 },
 'ja0496423': {
  'title':'Facile One-Pot Synthesis of Bifunctional Heterodimers of Nanoparticles: A Conjugate of Quantum Dot and Magnetic Nanoparticles',
  'authors':['Hongwei Gu','Rongkun Zheng','XiXiang Zhang','Bing Xu'],
  'journal':'Journal of the American Chemical Society','year':2004,'volume':'126','printed_pages':'5664–5665',
  'pairing_status':'matched_by_title_authors_and_specific_content',
  'pairing_evidence':[
   e('main',1,'Title/authors and DOI footer','Published main title and authors above; DOI10.1021/ja0496423.'),
   e('si',1,'Title, authors and Supporting Information heading','The SI repeats the same title with Quantum-Dot hyphenation and lists HongweiGu,RongkunZheng,X.X.Zhang,BingXu, matching the main authors.'),
   e('main',2,'Supporting Information Available and reference7','Main announces magnetic measurement of1 and TEM images of intermediates; reference7 directs method/spectrum claims to SI.'),
   e('si',[1,2,3],'Synthesis of4; FiguresS-1 throughS-5','The detailed preparation and numbered1–4 species match main Scheme1. FigureS-3 gives FePt1 ZFC/FC; FiguresS-4/S-5 give intermediates2/3 TEM, matching the explicit main SI declaration.')],
  'pairing_caveats':['SI abbreviates XiXiangZhang as X.X.Zhang and does not print a DOI. Full title/authors and exact numbered intermediates/data types provide content-based pairing independent of the filename.'],
  'material_overview':['FePt–CdS heterodimer nanoparticles combining a magnetic FePt part with a fluorescent CdS part.','FePt1, proposed FePt@S2 and FePt@CdS3 intermediates, final heterodimer4, and synthesized Cd(acac)2 precursor must remain distinct stages/materials. Intermediates were not successfully isolated as intact uniform shells.'],
  'synthesis_overview':'One-pot sequential FePt nanoparticle formation, sulfur addition at100°C, cadmium precursor/TOPO/diol addition at100°C, and280°C annealing produces FePt–CdS heterodimers. SI supplies detailed charges, holds, purification and N2 storage, plus the upstream preparation of Cd(acac)2.',
  'recipe_evidence':[
   e('main',1,'Scheme1 and synthesis paragraphs','Scheme1 and text identify1→2→3→4 with S addition100°C, Cd(acac)2 addition100°C and final280°C treatment.'),
   e('si',1,'Synthesis of Cd(acac)2','CdCl2 2.28g/10mmol in5mL water;2,4-pentanedione4.1mL/40mmol,15min stirring;triethylamine3mL;filter and ethanol/water recrystallize;2.8g product dried80°C under vacuum. Printed CdCl2 identity/quantity/purity require later consistency review.'),
   e('si',1,'Synthesis of4, first half','Pt(acac)2 95mg and diol195mg in10mL dioctyl ether;100°C about5min;oleylamine0.08mL,oleic acid0.08mL,Fe(CO)5 0.06mL;dioctyl ether boiling point30min;cool100°C;S5mg5min;TOPO120mg,diol105mg,Cd(acac)2 50mg at100°C10min,then280°C30min.'),
   e('si',1,'Synthesis of4, workup and General','Ambient cooling;ethanol precipitation/centrifugation;hexane redispersion and removal of insolubles;repeat ethanol precipitation;final15mL hexane dispersion stored under nitrogen. General section specifies inert atmosphere unless otherwise stated.')],
  'recipe_scope':'Definite present-study synthesis, with detailed downstream product and upstream Cd(acac)2 preparation. FePt preparation is cited in main but operationally supplied in SI. Screening does not assign a final recipe count.',
  'si_gaps':['The matched SI contains the advertised magnetic/intermediate data plus detailed procedures. It does not supply an independent intact-shell isolation recipe; the main explicitly reports isolation difficulty.','Centrifugal force/time, heating ramps, exact boiling-point temperature and some drying/purification durations are not fully specified. No guessed values were added.'],
  'scientific_flags':[
   e('si',1,'General and Cd(acac)2 preparation','Printed CdCl2 purity80.5%, CdCl2 2.28g/10mmol, and absent hydrate specification should be checked as source ambiguity; do not silently change to a hydrate.'),
   e('main',1,'Intermediate isolation paragraph','Core–shell intermediates are inferred/metastable; attempted isolation impaired shells. TEM residues do not establish a separately validated complete core–shell recipe.'),
   e('main',2,'Magnetic anisotropy estimate','Ku is calculated using a particle-size and measurement-time model, distinct from measured magnetization curves.'),
   e('si',[2,3],'FiguresS-1 toS-5','XRF belongs final4, UV–vis and ZFC/FC belong FePt1, and TEM images belong2/3; do not collapse their specimen identities.')],
  'inventory':[
   fig('main','Scheme1',[1],'Proposed sequential1–4 heterodimer synthesis mechanism.'),
   fig('main','Figure1A–D',[2],'FePt1 TEM;final4 TEM/HRTEM;final4 electron-diffraction pattern with CdS/FePt assignments.'),
   fig('main','Figure2A–D',[2],'Final4 temperature-dependent magnetization and inverse-moment inset;5K hysteresis;UV–vis/fluorescence;solution UV photograph.'),
   fig('si','FigureS-1',[2],'Final4 X-ray fluorescence spectrum with embedded elemental-analysis information.'),
   fig('si','FigureS-2',[2],'As-synthesized FePt1 UV–vis spectrum in hexane.'),
   fig('si','FigureS-3',[2],'As-synthesized FePt1 ZFC/FC magnetization.'),
   fig('si','FigureS-4',[3],'Intermediate2 TEM, source-labeled FePt and S residues.'),
   fig('si','FigureS-5',[3],'Intermediate3 TEM, source-labeled FePt and CdS residues.'),
   fig('main','Unnumbered magnetic relation',[2],'Measurement time/relaxation/anisotropy/volume/blocking-temperature relation used for author estimate.')],
  'text_pages_read':{'main':[1,2],'si':[1,2,3]},
  'visual_pages_inspected':{'main':[1,2],'si':[1,2,3]},
  'coverage_note':'All two main and three SI text pages read; all five corresponding page images inspected for screening. This is a source/relevance screen, not a measurement transcription or completed scientific audit.',
  'next_actions':['Independently verify title/author/species pairing and recipe relevance.','Full review should extract precursor preparation, sequential product preparation, specimen-specific original figures and acquisition details.','Retain source uncertainties in CdCl2 identity/quantity and intermediate shell isolation; distinguish observed heterodimers from proposed formation mechanism.']
 },
 'la036034c': {
  'title':'Novel Molecular Recognition via Fluorescent Resonance Energy Transfer Using a Biotin-PEG/Polyamine Stabilized CdS Quantum Dot',
  'authors':['Yukio Nagasaki','Takehiko Ishii','Yuka Sunaga','Yousuke Watanabe','Hidenori Otsuka','Kazunori Kataoka'],
  'journal':'Langmuir','year':2004,'volume':'20','printed_pages':'6396–6400',
  'pairing_status':'matched_by_embedded_manuscript_identifier_and_declared_specific_content',
  'pairing_evidence':[
   e('main',1,'Title, authors, journal header and DOI footer','The main prints the complete title/authors above, Langmuir2004,20,6396–6400 and DOI10.1021/la036034c.'),
   e('main',5,'Supporting Information Available','Explicitly announces TEM image of PEG/PAMA CdS QD and XRD of PEG/PAMA CdS QD.'),
   e('si',1,'Supporting information heading and TEM/XRD methods','Describes TEM and XRD acquisition specifically for PEG/PAMA and PEG/PAMA–CdS specimens.'),
   e('si',[2,3],'Figure1 and Figure2 captions','The supplied SI contains exactly TEM image of PEG/PAMA–CdS QD and X-ray diffractograms of PEG/PAMA–CdS, matching the main declaration and main p3 discussion.'),
   e('si',None,'Embedded PDF Title metadata','Microsoft Word - la036034csi20040323_025126.doc contains the exact manuscript identifier and SI designation; this is corroboration, not filename-only pairing.')],
  'pairing_caveats':['SI does not display the main article title or authors. Pairing relies on its embedded manuscript identifier plus exact announced PEG/PAMA–CdS TEM/XRD content and experimental context.'],
  'material_overview':['CdS quantum dots stabilized by CHO-PEG/PAMA block copolymer and by biotin-PEG/PAMA for recognition/FRET assays.','Unstabilized CdS, PEG-stabilized and PAMA-homopolymer preparations are comparison conditions. Polymer preparation, biotin installation and protein assay are distinct from the CdS precipitation route.'],
  'synthesis_overview':'Main Experimental Section includes a summarized but operational polymer synthesis and aldehyde/biotin functionalization, followed by aqueous CdCl2/Na2S coprecipitation in polymer solution, ambient stirring and dialysis. SI provides microscopy and diffraction acquisition/results rather than additional synthesis.',
  'recipe_evidence':[
   e('main',2,'Experimental Section1: Preparation of CHO-PEG/PAMA Block Copolymers','PDP initiator1mmol inTHF45mL;EO113.5mmol2days;AMA60mmol followed by60min ambient polymerization;2-propanol precipitation;protonation/Soxhlet cleanup. The source cites prior polymer methods but supplies this present-paper summary.'),
   e('main',2,'Experimental Section1: end-group modification','Acetic acid/water10:1v/v,35°C5h converts acetal to aldehyde;NaOH neutralization and dialysis. Biocytin hydrazide is introduced before dialysis and reacted2h, followed byNaBH4 reduction; amounts for these latter reagents are not reported.'),
   e('main',2,'Experimental Section2: Coprecipitation','In a glass vial,8mL aqueous block-copolymer solution with amine concentration3.08e-4mol/L receives CdCl2 andNa2S in that order;each is reported as2.5e-3mol/L;stir1h at ambient temperature,then dialyze against water. Biotin-installed CdS is prepared similarly using biotin-PEG/PAMA.'),
   e('main',3,'Figures1–2 captions','Comparison stabilizers and polymer-amine concentrations1.16,3.08,4.62×10^-4mol/L are reported; preserve concentration basis and avoid inventing stock addition volumes.')],
  'recipe_scope':'Definite CdS synthesis with functional polymer preparation and a biotin-functionalized variant. Some upstream or variant details are summarized/cited, which does not make the paper ineligible. No final recipe count assigned during screening.',
  'si_gaps':['Supplied SI matches both declared characterization figures and contains TEM/XRD methods.','Exact CdCl2/Na2S addition volumes or a separate stock-versus-final concentration definition are not explicit in the representative recipe.','Biocytin hydrazide/NaBH4 amounts, dialysis membrane/time and several polymer-workup details are unreported or refer to prior methods.','TEM/XRD SI captions name PEG/PAMA–CdS, without a direct biotin-specific specimen ID; do not automatically assign these measurements to every biotin sample.'],
  'scientific_flags':[
   e('main',[2,3],'Polymer concentration and optical comparison','Polymer concentration is expressed as amine-group concentration, not molarity of whole chains. Keep homopolymer and block-copolymer controls separate.'),
   e('main',3,'Figure2 and adjacent discussion','The text describes increasing polymer concentration increasing emission and uses the term hypochromic shift; plotted intensity ordering and shift terminology need careful full-review comparison rather than silent correction.'),
   e('main',[3,4],'Particle size and FRET interpretation','4.8nm is estimated from absorption/band-gap theory and compared with TEM; a measured size distribution has not been extracted. FRET/recognition assay conditions must remain distinct from synthesis.'),
   e('main',4,'Figure5 and inhibition text','Figure5 caption describes TexasRed–streptavidin concentration, while text describes nonlabelled-protein inhibition. Preserve original axes/labels and verify the precise control series during detailed review.')],
  'inventory':[
   fig('main','Figure1a–f',[3],'Solution photographs for no-polymer/PEG/PAMA/block-copolymer cases and PAMA versus block-copolymer emission under salt conditions.'),
   fig('main','Figure2a–d',[3],'Polymer-concentration fluorescence comparison and CdS UV–vis absorption.'),
   fig('main','Figure3',[3],'Zeta potential versuspH; caption refers to Figure2 sample.'),
   fig('main','Figure4',[4],'Biotinylated CdS/TexasRed–streptavidin fluorescence series.'),
   fig('main','Figure5',[4],'FRET inhibition/control comparison with nonlabelled streptavidin/BSA; caption/text series interpretation needs audit.'),
   fig('main','Figure6',[4],'TexasRed–streptavidin concentration dependence of FRET and inset.'),
   fig('si','Figure1',[2],'PEG/PAMA–CdS TEM in two views with50nm and20nm scale bars.'),
   fig('si','Figure2',[3],'PEG/PAMA–CdS XRD pattern with reference sticks; keep original trace and labels. No atomistic structure file supplied.')],
  'text_pages_read':{'main':[1,2,3,4,5],'si':[1,2,3]},
  'visual_pages_inspected':{'main':[1,2,3,4,5],'si':[1,2,3]},
  'coverage_note':'All five main and three SI text pages read; all eight page images inspected for source screening. Neither plotted data nor complete sample/recipe records have been scientifically extracted or audited.',
  'next_actions':['Independently verify content/metadata-based SI pairing.','Full review should extract the polymer precursor, aldehyde/biotin variants, CdS precipitation, controls and FRET procedures with explicit concentration bases and unknown quantities.','Preserve main and SI figure identities; separate unmodified PEG/PAMA structural measurements from biotin-specific assay samples unless the source establishes a join.']
 }
}

for suffix, d in data.items():
    folder = B/suffix
    manifest = json.loads((folder/'intake-manifest.json').read_text(encoding='utf-8'))
    docs=[]
    for original in manifest['documents']:
        doc=dict(original)
        doc['role']=doc.pop('role_candidate')
        doc['identity_status']='content_screened_main' if doc['role']=='main' else d['pairing_status']
        assert hashlib.sha256(Path(doc['path']).read_bytes()).hexdigest()==doc['sha256']
        doc['original_bytes_reverified_before_screening_write']=True
        doc['text_pages_actually_read']=d['text_pages_read'][doc['role']]
        doc['visual_pages_actually_inspected']=d['visual_pages_inspected'][doc['role']]
        docs.append(doc)
    result={
      'schema_version':'1.0', 'screening_stage':'source_content_intake_only',
      'created_at':datetime.now(timezone.utc).isoformat(), 'screened_by':'peng1998_reader_assets',
      'doi':manifest['doi'], 'title':d['title'], 'authors':d['authors'],
      'bibliographic_identity':{k:d[k] for k in ['journal','year','volume','printed_pages']},
      'documents':docs,
      'main_si_pairing':{k.replace('pairing_',''):d[k] for k in ['pairing_status','pairing_evidence','pairing_caveats']},
      'recipe_present':'yes','decision':'include_for_full_review',
      'decision_reason':'Source contains an explicit present-study material synthesis/preparation procedure; partial or cited upstream details do not justify exclusion.',
      'synthesis_relevance':{k:d[k] for k in ['material_overview','synthesis_overview','recipe_evidence','recipe_scope']},
      'supporting_information_gaps':d['si_gaps'], 'source_ambiguities_and_scope_flags':d['scientific_flags'],
      'figures_tables_equations_inventory':{'scope':'Screening-level inventory of labelled visual objects across supplied pages; not a full data transcription, digitization, equation audit, or source-unit inventory.','items':d['inventory']},
      'coverage':{'text_pages_actually_read':d['text_pages_read'],'visual_pages_actually_inspected':d['visual_pages_inspected'],'scope_note':d['coverage_note']},
      'next_actions':d['next_actions'],
      'completion_flags':{'source_content_screening_complete':True,'independent_screening_audit_complete':False,'complete_scientific_extraction':False,'complete_scientific_audit':False,'website_integrated':False,'published':False},
      'originals_modified':False,'downloads_performed':False,'live_ledger_modified':False,'site_modified':False
    }
    (folder/'screening.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=[f'# {d["title"]}', '',f'DOI: {manifest["doi"]}. Authors: '+ '; '.join(d['authors'])+'.', '',
      '**Decision: include for full review. Recipe present: yes.** This is source-content intake screening only; complete scientific extraction, independent audit and publication remain pending.', '',
      d['synthesis_overview'], '', '## Main/SI identity and source bytes', '']
    for doc in docs:
      lines += [f'- {doc["role"]}: {doc["page_count"]} PDF pages; {doc["size_bytes"]} bytes. SHA256 `{doc["sha256"]}`. Source: [{doc["filename"]}]({doc["path"].replace(chr(92),"/")}).']
    lines+=['',f'Pairing: {d["pairing_status"]}.']
    for item in d['pairing_evidence']:
      lines += ['',f'- {item["document_role"]} PDF page(s) {item["pdf_page"]}, {item["locator"]}: {item["finding"]}']
    lines += ['', 'Pairing limitations: '+ ' '.join(d['pairing_caveats']), '', '## Synthesis evidence', '']
    for item in d['recipe_evidence']:
      lines += [f'- {item["document_role"]} PDF page(s) {item["pdf_page"]}, {item["locator"]}: {item["finding"]}']
    lines+=['',d['recipe_scope'],'','## Coverage and retained information','',d['coverage_note'],'']
    for item in d['inventory']:
      lines += [f'- {item["document_role"]} {item["label"]}, PDF page(s) {item["pdf_pages"]}: {item["scope"]}']
    lines+=['','## Unresolved points and next actions','']
    for item in d['scientific_flags']:
      lines += [f'- {item["document_role"]} PDF page(s) {item["pdf_page"]}, {item["locator"]}: {item["finding"]}']
    lines += [f'- {x}' for x in d['si_gaps']+d['next_actions']]
    lines += ['', 'Original PDFs remained unchanged. No downloads, Site edits, live-ledger changes or publication were performed.', '']
    (folder/'screening-notes.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'suffix':suffix,'recipe_present':'yes','decision':result['decision'],'documents':[{'role':x['role'],'pages':x['page_count']} for x in docs],'screening_sha256':hashlib.sha256((folder/'screening.json').read_bytes()).hexdigest()}))
