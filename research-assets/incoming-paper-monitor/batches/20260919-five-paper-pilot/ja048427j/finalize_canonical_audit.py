"""Freeze the separate canonical audit after manual scientific review; never mutates authors' files."""
import json,hashlib
from pathlib import Path
B=Path(__file__).resolve().parent
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads((B/'canonical-audit-working-checks.json').read_text(encoding='utf-8'))
assert r['status']=='passed' and r['findings']==[]
r['scope']='Independent scientific source-to-canonical audit of 19 private draft records. This verifies faithful transformation of the passed full supplied-source extraction. It is not a repeat full-paper extraction, an experimental reproduction, or reader/visual/training/publication approval.'
r['source_inventory_and_facts']='All 201 source facts were individually read; every 366 typed binding was resolved against its exact source value/member, units, approximation, uncertainty, qualifier, source-native and canonical status, evidence locator and actual canonical sample ID. All 174 inventory objects were compared as lossless payloads, including 68 numbered reference groups, four complete tables, seven equation/definition entries, 18 figure/table/scheme entries and 14 missingness/conflict objects.'
r['actual_original_source_rechecks']={
 'main_text_pages':[2,3,4,8,9,10,11],
 'main_visually_inspected_pages':[3,4,11],
 'si_text_pages':[2,3,4],
 'si_visually_inspected_pages':[2,3,4],
 'locators':['Main II.A materials; II.B hydrolysis, washing, amine treatment and films; II.C acquisition','Main pp. 3–4 Figures 1–4 composition, growth aliquots, microscopy and oxidation controls','Main IV.D–E growth/phase and oxidation interpretation','Main IV.F charge-transfer model and alternatives','Main IV.G luminescence','Main IV.H domain magnetism, Film A residual response and literature/theory caveats','SI Table S1–S3 ligand-field parameters, estimates, calculated versus cited transition energies','SI Figure S1 and equations S1–S2 dopant distributions and printed notation','SI Figures S2–S3 and Table S4 film-specific outcomes and conflicting D/F representations'],
 'prior_complete_source_audit':'The independent source audit by /root/backlog_eta already covers all 12 main and four SI pages, 24 crops and 16 full pages. That earlier scope is cited, not claimed as newly performed by this reviewer.',
 'asset_scope_this_audit':'All four original PDF copies and all 40 previously audited evidence assets rehashed. Only the six page images enumerated above were newly visually inspected in this canonical audit; no claim of a new full crop/presentation audit.'}
manual=[
 ('Recipe count','One common hydrolysis literature route; 11 supporting procedures and seven observation/context records are not independent synthesis runs.'),
 ('Source identity','Matched main and SI DOI/title/context preserved with exact original hashes; four copies are two byte-identical document pairs.'),
 ('Materials','Hydrated metal precursors, TMAH source typo, technical 90% TOPO, 98% dodecylamine and <0.0005% Zn-precursor magnetic impurity limit retained.'),
 ('Hydrolysis concentration','0.10 M combined Mn/Zn acetates and 0.55 M ethanolic TMAH are stocks; 1.7 equivalents is the common hydrolysis addition.'),
 ('Titration distinction','2% initial feed, 0.15-equivalent increments, 0.45 onset, 1.65 endpoint and 70-fold aliquot dilution remain in the titration context.'),
 ('Growth alternatives','Qualitative minutes and several days at room temperature versus near 60 °C are preserved without inheriting the two-hour specimen experiment.'),
 ('Isolation','Ethyl acetate precipitation, ethanol resuspension, iterative heptane/ethanol washing and initial DDA capping remain ordered; unreported amounts and settings remain unknown.'),
 ('Cleaning separation','180 °C approximately 30 min under nitrogen is surface cleaning; below 80 °C is a strict cooling threshold.'),
 ('Ligand property','DDA melting point near 30 °C is a reagent property, not a reaction hold.'),
 ('Surface-bound control','Pure ZnO with approximately 2% Mn relative to Zn and 0.002-equivalent ethanolic LiOH is a separate surface-binding control without the stripping treatment.'),
 ('Incomplete TOPO','Cited TOPO method lacks its own restated time, temperature and amount. It does not inherit DDA conditions.'),
 ('Growth aliquot lineage','The 0.02% feed progression preserves b at 10 min, c after 2 h at 60 °C and d after 30 min at 180 °C. Later growth does not consume an already analyzed aliquot.'),
 ('Feed versus product','0.50% feed and ICP-derived 0.20 ± 0.01% final Mn are distinct. Nominal Zn0.998Mn0.002O is not refined site occupancy.'),
 ('Size estimands','TEM 6.1 ± 0.7 nm, powder Scherrer 6.1 nm, Film A Scherrer 20 nm and unreliable optical estimate 6–7 nm are separate technique/specimen facts.'),
 ('Structural evidence','Wurtzite diffraction, measured fringe spacings and figures remain source-scoped; no lattice constants, atomistic coordinates, SAED pattern or CIF fabricated.'),
 ('Film preparation','A/B/C coat counts and 525 °C for 2 min per layer under air apply only to the documented A–C preparation.'),
 ('Film D–F provenance','D–F outcomes retain unresolved preparation/batch linkage; no copied A–C recipe or film parent assignment.'),
 ('Mass representations','Main A/B/C masses in mg and SI values in micrograms remain separate reported representations.'),
 ('D/F conflict','Figure S3b D>E>F and Table S4 D<E<F remain separately preserved; actual D/F outcome fields include the conflict qualifier and no label swap.'),
 ('Magnetic units','Mass-normalized emu/g and per-Mn µB/Mn moments remain distinct.'),
 ('Collective domain spin','S>800 is an author-derived lower bound for the A–C collective domain context, not a measured atomic spin or unique Film A value.'),
 ('Film A residual magnetism','64% residual paramagnetic contribution and derived 36% remainder stay in Film A context; aligned fractions are model-based lower bounds.'),
 ('Temperature bound','Curie-temperature evidence above the 350 K instrument ceiling remains a bound, not an exact transition temperature.'),
 ('Optical specimens','TOPO-treated 1.1% Mn, structural 0.20% Mn and the 0.13%/1.3% luminescence cohorts remain separate.'),
 ('Optical acquisition','Room-temperature absorption, 300 K luminescence and 5 K field-dependent MCD retain distinct sample/method conditions.'),
 ('EPR fit','g, signed A and D, D uncertainty and strain retain fit provenance. Bulk reference parameters are not current-particle observations.'),
 ('Charge-transfer interpretation','Tentative Mn-to-conduction-band assignment remains a hypothesis with the competing intensity-based alternative and cited model inputs.'),
 ('SI ligand-field tables','All S1–S3 cells, row-species/ref associations and distinct calculated/cited-experimental columns remain preserved; member units correctly normalized.'),
 ('Dopant statistics','6.5 nm is an assumed uniform size; means 7.9 and 79 are author model outputs. The printed variable/Poisson notation conflict remains open.'),
 ('Oxidation controls','Zn acetate, Na acetate, nitrate substitution and anaerobic condition are alternative controls, not co-added reagents.'),
 ('Mechanism versus measurement','Acidification, supersaturation, basic zinc acetate clusters, dopant stripping and carrier/nitrogen explanations are source interpretations; measured pH, carrier density/polarity and N incorporation are absent.'),
 ('Literature conditions','900 °C/low oxygen MnO conditions, solubility at 1 kbar and theoretical carrier density are reference/model context, not synthesis or film conditions.'),
 ('Unknown contexts','Unquantified specimen and instrument contexts use general-context samples without invented amounts, conditions or independent-batch claims.'),
 ('Dataset boundaries','All requested_tasks remain empty, review status imported_unreviewed, eligibility false and shared source split enforced. 590 entries include lossless contexts, not 590 measured properties.'),
 ('Hash immutability','All 19 author draft hashes match the requested manifest at both audit start and end; no author/Site/ledger files modified.')]
r['manual_scientific_checks']=[{'topic':k,'result':'passed','evidence_review':v} for k,v in manual]
r['manual_scientific_check_count']=len(manual)
r['open_findings']=[];r['author_corrections_requested']=[]
r['retained_source_limitations']=['No completely quantified synthesis SOP: absolute scale, many volumes, addition/wash/isolation details, yields and batch joins are unreported.','D/F figure/table labeling or values conflict remains unresolved.','Printed dopant-statistics notation and TMAH formula inconsistency remain explicit.','No atomic coordinates, measured lattice constants, experimental CIF or carrier measurement supplied.','External references remain citations; no claim of their full-paper reading.']
r['downstream_gates']={'canonical_source_transformation':'passed','reader_and_original_figure_integration':'not_audited_here','molecular_and_apparatus_visuals':'not_audited_here','actual_runtime_presentation':'not_audited_here','training_admission':'not_granted','publication':'not_granted'}
r['manifest_sha256']='185ae1359ba2aab1e2091e877cc2b72f929cfb14128fc7ae56ddffe067a0d609'
for n in ['main-02.txt','main-03.txt','main-04.txt','main-08.txt','main-09.txt','main-10.txt','main-11.txt','si-02.txt','si-03.txt','si-04.txt','main-03.png','main-04.png','main-11.png','si-2.png','si-3.png','si-4.png','canonical-audit-working-checks.json','finalize_canonical_audit.py']:
 p=B/n;r['bound_files'][str(p)]=h(p)
out=B/'canonical-records-audit.json';out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=f'''# Norberg 2004 — independent canonical scientific audit

**Passed**, with no author corrections requested and no open canonical findings.

Reviewer: `/root/peng1998_reader_assets`; canonical author: `/root/norberg2004_extract`. DOI: 10.1021/ja048427j.

The frozen package contains 19 records, 47 operations and 201 source facts represented through 366 typed bindings. The audit resolved every binding against original source values, sample contexts, uncertainties, units and locators, and compared all 174 complete inventory payloads. All 26 original protocol operations are mapped exactly once. All {r['check_count']:,} programmatic consistency checks and {len(manual)} separately documented scientific boundary checks passed.

The 590 measurement/context entries include bibliography, source equations, model table cells and lossless inventory payloads. They are not 590 measured properties or independent synthesis examples. The package has one common synthesis route, 11 supporting procedures and seven observation/context records.

This audit read every source fact and checked all canonical mappings and operation/sample relationships. It reread main pages 2–4 and 8–11 and SI pages 2–4; visually rechecked main pages 3, 4 and 11 and SI pages 2–4. The earlier independent complete-source audit covers all 12 main and four SI pages. Here, all four PDF copies and 40 previously audited assets were rehashed; a new full-source or full-crop visual audit is not claimed.

Critical distinctions remain intact: synthesis versus 180 °C cleaning; initial feed versus ICP composition; optical/structural/film cohorts; growth aliquots; collective S > 800 domain-spin estimate; calculated versus cited ligand-field values; and model assumptions versus measured observables. Film D/F values and labels remain explicitly inconsistent between Figure S3b and Table S4, without swapping them or constructing an unreported D–F recipe. Unknown reaction scale, specimen links, carrier measurements and crystal coordinates remain unknown.

All training tasks are empty, current eligibility is false and canonical review statuses remain imported_unreviewed. Reader integration, molecules, apparatus, runtime presentation and publication are separate gates. No Site, ledger, original source or author draft files were changed.

Frozen manifest SHA256: `{r['manifest_sha256']}`.

Audit JSON SHA256: `{h(out)}`. The JSON binds each source and canonical file, the complete checks and the exact original-page recheck scope.
'''
(B/'canonical-records-audit.md').write_text(md,encoding='utf-8')
print(json.dumps({'status':'passed','checks':r['check_count'],'manual_checks':len(manual),'bound_files':len(r['bound_files']),'audit_sha256':h(out),'manifest_sha256':r['manifest_sha256']}))
