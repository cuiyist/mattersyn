"""Build a prioritized source queue from cached first pages; no training records."""
import json,re,hashlib,collections,html,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parent;PAPERS=ROOT.parent.parent/'downloaded_papers'
data=json.loads((ROOT/'first-page-candidate-audit.json').read_text(encoding='utf-8'))
# Expert triage based on already extracted first pages, ordered to diversify chemistry.
specs=[
(71,'lead chalcogenides','PbS','Optimization study: assess linked experimental run table first.'),
(65,'halide perovskites','CsPbBr3','Phosphonic-acid synthesis; another agent is separately auditing one TDPA branch.'),
(16,'metal oxides','ZnO','Aqueous QD synthesis; another agent is separately auditing the seed recipe.'),
(70,'metal oxides','iron oxide','Shape synthesis; distinguish initial wustite from post-oxidized phase.'),
(31,'elemental metals','Ir','Solution nanocrystal synthesis with catalytic surface-coating comparison.'),
(15,'lead chalcogenides','PbSe / lead chalcogenides','Mechanistic model reactions; size-uniformity linkage requires inspection.'),
(63,'III-V semiconductors','InP','Ligand-mediated nucleation and growth series.'),
(64,'III-V semiconductors','InP','Two-phosphine nucleation and growth study.'),
(24,'III-V semiconductors','InP/ZnS','Blue core/shell synthesis with chloride capping.'),
(66,'halide perovskites','CsPbBr3','Nanowire-width series; first page points to SI Table S1.'),
(58,'III-V semiconductors','InP','Continuous-injection growth route.'),
(57,'III-V semiconductors','InP','Two-step seed-mediated route.'),
(60,'multinary chalcogenides','Cu-Sb-S','Explicit four-phase synthesis; useful phase-label audit candidate.'),
(77,'silver chalcogenides','silver chalcogenides','Silylamide-promoted infrared QD synthesis.'),
(92,'multinary chalcogenides','Ag2ZnSnS4/ZnS','Multinary core/shell colloidal synthesis.'),
(73,'halide perovskites','antimony halide perovskite','Lead-free blue-emitting colloidal QDs.'),
(53,'mercury chalcogenides','HgTe','Infrared QD synthesis in DMF.'),
(62,'mercury chalcogenides','HgTe/CdTe; HgSe/CdX','Multiple core/shell branches; keep them separate.'),
(41,'metal phosphides','Cd3P2; (CdxZn1-x)3P2','Size-dependent synthesis with alloy branches.'),
(17,'metal phosphides','cadmium phosphide','Colloidal visible-to-NIR synthesis.'),
(2,'II-VI zinc chalcogenides','zinc chalcogenides','Quantum-rod synthesis across compositions.'),
(12,'metal oxides','ITO','Solution-phase oxide NC assemblies; separate NC growth from assembly.'),
(6,'elemental metals','Ag','Shape and etching process for monodisperse nanospheres.'),
(9,'elemental metals','Au clusters','Atomically characterized gold cluster growth; different scale from ordinary QDs.'),
(11,'metal hydroxyhalides','nickel hydroxychloride','Near-monodisperse colloidal fullerene-like structures.'),
(21,'multinary chalcogenides','Cu2ZnSnS4xSe4(1-x)','Nanocrystal ink and ligand-exchange processing; synthesis completeness unverified.'),
(51,'halide perovskites','CH3NH3PbI3','Solvent effects in air-stable colloidal synthesis.'),
(28,'halide perovskites','cesium lead halide','Thermodynamic-equilibrium size control.'),
(0,'halide perovskites','lead bromide magic-sized clusters','Self-organization and atomistic analysis; ligand-capped Cs and other cation variants need exact branch linkage.'),
(10,'III-V semiconductors','InAs','Multiple synthetic routes and resurfacing; not automatically new growth recipes.'),
(56,'lead chalcogenides','PbS/CdS','Room-temperature colloidal atomic-layer shell growth.'),
(61,'II-VI cadmium chalcogenides','CdTe nanoplatelets','3.5-monolayer synthesis and lateral-dimension series.'),
(96,'II-VI zinc chalcogenides','ZnSTe/ZnSe/ZnS','Multishell blue-emitting QD synthesis.'),
(94,'lanthanide nanocrystals',None,'Core/shell lanthanide particles; exact host and recipe branches unverified.'),
(76,'multinary chalcogenides','CuInTe2; CuInTe2-xSex gradient alloy','Abstract reports cation-rich measured compositions, distinct from nominal title formulas.'),
(59,'II-VI cadmium chalcogenides','CdSe','Automated high-throughput ML synthesis study; inspect actual experimental table.'),
(7,'II-VI cadmium chalcogenides','CdSe','Faceted zinc-blende QD nucleation/growth; benchmark against existing CdSe seed.'),
(22,'II-VI cadmium chalcogenides','CdSe','Quantum-disk size and shape series.'),
(3,'II-VI cadmium chalcogenides','CdSe','Low-temperature nanoribbon synthesis.'),
(19,'II-VI cadmium chalcogenides','CdTe/CdSe','Seeded heterostructure shape-tuning series.'),
(54,'II-VI cadmium chalcogenides','CdSe1-xSx','Alloy synthesis; preserve composition fraction and stage.'),
(48,'bismuth chalcogenides','(Bi2)m(Bi2Se3)n','Solution nanosheets; inspect colloidal scope and exact phase.'),
]
titles={
2:'A General Strategy for Synthesizing Colloidal Semiconductor Zinc Chalcogenide Quantum Rods',
3:'Low-Temperature Solution-Phase Synthesis of Quantum Well Structured CdSe Nanoribbons',
11:'Fullerene-like Colloidal Nanocrystal of Nickel Hydroxychloride',
12:'A Facile Solution-Phase Approach to Transparent and Conducting ITO Nanocrystal Assemblies',
15:'On the Mechanism of Lead Chalcogenide Nanocrystal Formation',
16:'Stable Aqueous Dispersion of ZnO Quantum Dots with Strong Blue Emission via Simple Solution Route',
17:'Synthesis and Characterization of Cadmium Phosphide Quantum Dots Emitting in the Visible Red to Near-Infrared',
19:'Shape Tuning of Type II CdTe-CdSe Colloidal Nanocrystal Heterostructures through Seeded Growth',
21:'Cu2ZnSnS4xSe4(1-x) Solar Cells from Polar Nanocrystal Inks',
22:'Size/Shape-Controlled Synthesis of Colloidal CdSe Quantum Disks: Ligand and Temperature Effects',
31:'Iridium Nanocrystal Synthesis and Surface Coating-Dependent Catalytic Activity',
51:'Colloidal Synthesis of Air-Stable CH3NH3PbI3 Quantum Dots by Gaining Chemical Insight into the Solvent Effects',
54:'Homogeneously Alloyed CdSe1-xSx Quantum Dots (0 <= x <= 1): An Efficient Synthesis for Full Optical Tunability',
56:'PbS/CdS Core/Shell Quantum Dots by Additive, Layer-by-Layer Shell Growth',
60:'Selective Nanocrystal Synthesis and Calculated Electronic Structure of All Four Phases of Copper-Antimony-Sulfide',
64:'Investigation of Indium Phosphide Quantum Dot Nucleation and Growth Utilizing Triarylsilylphosphine Precursors',
76:'Fabrication of CuInTe2 and CuInTe2-xSex Ternary Gradient Quantum Dots and Their Application to Solar Cells',
77:'Infrared Emitting and Photoconducting Colloidal Silver Chalcogenide Nanocrystal Quantum Dots from a Silylamide-Promoted Synthesis',
94:'Optimized core-shell lanthanide nanoparticles with ultrabright Ce3+-modulated second near-infrared emission for "lighting" plants',
}
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).lower()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def year_from_page(t):
    for pattern in [r'Cite\s*[Tt]his:.*?\b((?:19|20)\d{2})\s*,',r'(?:Chem\. Mater\.|J\. Am\. Chem\. Soc\.|Nano Lett\.|ACS Nano|J\. AM\. CHEM\. SOC\.|ACS Appl\. Nano Mater\.|J\. Mater\. Chem\. C)\s*,?\s*((?:19|20)\d{2})\s*,',r'VOL\..{0,80}((?:19|20)\d{2})',r'Published\s*(?:on Web)?[^\n]*\b((?:19|20)\d{2})']:
        m=re.search(pattern,t,re.I)
        if m:return int(m.group(1)),m.group(0)
    return None,None
queue=[]
for rank,(i,family,composition,reason) in enumerate(specs,1):
    r=data['candidates'][i];t=Path(r['firstPageTextFile']).read_text(encoding='utf-8')
    title=titles[i] if i in titles else html.unescape(r.get('pdfMetadataTitle',''))
    year,evidence=year_from_page(t)
    mains=[PAPERS/n for n in r['mainFiles']];sis=[PAPERS/n for n in r['siFiles']]
    hashes={p.name:sha(p) for p in mains+sis}
    identical=[p.name for p in sis if hashes[p.name]==hashes[mains[0].name]]
    identity=norm(r['doi']) in norm(t)
    queue.append({'priority':rank,'doi':r['doi'],'doiUrl':'https://doi.org/'+r['doi'],'title':title,'titleSource':'PDF metadata and first-page heading' if title else 'unknown: extraction artifact; visually verify title','year':year,'yearEvidence':evidence,'candidateMaterialFamily':family,'candidateComposition':composition,'familyConfidence':'medium: first-page triage only','priorityReason':reason,'curationStatus':'uncurated-source-candidate','trainingEligible':False,'mainFiles':[str(p) for p in mains],'supportingInformationFiles':[str(p) for p in sis],'mainDoiAppearsOnFirstPage':identity,'mainIdentityConfidence':'high DOI match on first page' if identity else 'medium title/filename match; DOI not located on first page','mainSiMatchConfidence':'low: identical main/SI hashes' if identical else 'medium: matching download log and DOI filename; SI content not verified by this audit','identicalMainSiFiles':identical,'sha256':hashes,'firstPageTextFile':r['firstPageTextFile'],'downloadEvidence':r['logEvidence'],'recipeFieldCoverage':{'quantities':'not audited','temperature':'not audited','time':'not audited','sizeOutcome':'not audited','phase':'not audited','exactGeometry':'not audited'},'licenseStatus':'Publisher paper/SI license not audited. Local access does not imply redistribution permission.'})
quarantine=[]
for i,reason in [(82,'Named main PDF starts with SUPPLEMENTARY INFORMATION; main source identity not established.'),(85,'Named main PDF starts with Supporting Information; main source identity not established.')]:
    r=data['candidates'][i];quarantine.append({'doi':r['doi'],'mainFiles':[str(PAPERS/n) for n in r['mainFiles']],'reason':reason})
out={'schemaVersion':'mattersyn-source-queue/1','auditDate':'2026-09-16','scope':'Source prioritization only. No extracted experimental training rows and no claimed protocol completeness. Separate agent record audits are authoritative for curated seeds.','summary':{**data['summary'],'prioritizedCandidates':len(queue),'familyCounts':dict(collections.Counter(r['candidateMaterialFamily'] for r in queue)),'quarantinedMainIdentity':len(quarantine),'queueTrainingEligibleRecords':0,'unselectedFirstPages':100-len(queue)-len(quarantine)},'selectionMethod':'Deterministic 100-paper stratified journal sample, then human semantic triage of titles and first pages to 42 diverse sources. This is not an unbiased systematic corpus review.','queue':queue,'quarantine':quarantine,'remainingInspectionManifest':'first-page-candidate-audit.json'}
(ROOT/'diverse-pilot-source-queue.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
lines=['# Diverse colloidal nanocrystal source queue','',f'Inspected exactly 100 cached main-PDF first pages; prioritized {len(queue)} candidates across {len(out["summary"]["familyCounts"])} broad material families. Every queue entry remains uncurated and excluded from training. Recipe fields are explicitly unaudited.','',f'The local index contains {data["summary"]["uniqueDoiRecords"]} DOI records, with {data["summary"]["withExistingMainAndSI"]} having existing main and SI files. Download logs contain filenames/status, not bibliographic titles or recipe metadata. Filename matching alone does not establish SI identity.','','| Rank | Family | Year | DOI | Title |','|---|---|---:|---|---|']
for r in queue:lines.append(f'| {r["priority"]} | {r["candidateMaterialFamily"]} | {r["year"] or "unknown"} | [{r["doi"]}]({r["doiUrl"]}) | {r["title"] or "Title needs visual verification"} |')
lines+=['','Two incorrectly labeled main PDFs are quarantined: 10.1038/nphoton.2015.142 and 10.1038/srep03330. Their first pages identify supporting information.','', 'Top immediate expansion candidates are PbS optimization (Voznyy 2019), CsPbBr3 phosphonic-acid synthesis (Zhang 2019), ZnO aqueous QDs (Fu 2007), iron-oxide shape formation (Feld 2019 journal issue / 2018 online), and iridium nanocrystals (Stowell 2005). InP, CsPbBr3, and ZnO seed audits are performed separately; they must not confer curated status on other recipes from those papers.','', 'Before importing experimental records: identify the exact main/SI relationship, preserve raw source quantities and stock composition, link each result to a specific variant, represent missing phase/time/size values as unknown, and split model evaluation by source DOI rather than by adjacent rows from the same paper. Do not treat ideal bulk crystals or generated particle cartoons as measured atomic-coordinate labels.','']
(ROOT/'diverse-pilot-source-queue.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({'entries':len(queue),'families':out['summary']['familyCounts'],'unknownYears':[r['doi'] for r in queue if not r['year']],'doiNotFound':[r['doi'] for r in queue if not r['mainDoiAppearsOnFirstPage']],'identicalMainSI':[r['doi'] for r in queue if r['identicalMainSiFiles']]},indent=2))
