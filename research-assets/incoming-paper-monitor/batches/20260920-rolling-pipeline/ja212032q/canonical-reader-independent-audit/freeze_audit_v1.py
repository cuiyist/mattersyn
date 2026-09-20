from pathlib import Path
import json,hashlib,datetime
A=Path(__file__).resolve().parent;G=A.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
checks=read(A/'mechanical-checks-v1.json');assert not checks['failures']
manual=[
 'All 325 academic reader items read in full, including titles, prose, notes and source-conflict statements; field values checked separately by exact mappings.',
 'All 21 record boundaries: two literature routes, three variants, ten procedures and six observation/context records; not 21 independent recipes or batches.',
 'All 33 process graphs, 88 material slots, three stocks and 89 record-local sample/context slots inspected; no exact cross-technique specimen identity inferred.',
 'Common initial core steps are referenced by small/large branches. The 7 nm negative control does not borrow the 5.5 nm preparation.',
 'Core charge 1 g TOPO, 8 mL ODE, 0.38 mmol Cd-oleate; 100 mL source vessel. Sequential 30 min RT and 30 min 80 C evacuation, followed by argon 300 C and injection/growth 270 C remain separate.',
 'Whole injection mixture: 4 mmol TOP-Se, 3 mL oleylamine, 1 mL ODE; final volume, upstream stock chemistry and flow/rate remain missing.',
 'Small cold-toluene quench has no invented temperature/volume; large branch retains approximate initial 10 min, additional 0.8 mmol Cd/8 mmol TOP-Se at 270 C, then 10 min at 300 C.',
 'Repeated ethanol collection retains cores and uses hexane redispersion; 2–3 cycles are a range, not two separate invented experiments.',
 'Preferred shell growth: source 250 mL vessel, approximately 2e-7 mol cores, 5 mL oleylamine/5 mL OD; prepassivation is one Cd-monolayer equivalent, not a completed CdS shell.',
 'Separate 0.2 M S/OD and Cd-oleate/OD stocks; 240 C, 1 h post-S/2.5 h post-Cd; unresolved first 5–8-layer ratio switch preserved.',
 'All five Table 1 schedules separately represented; 21±0.2 and 41±6 percent narrative outcomes remain distinct from rounded/bounded table values.',
 'One versus ten percent withdrawals concern reaction volume and unchanged subsequent precursor charges; output aliquot IDs are operation-specific, not extra measured batches.',
 'OD late dilution 9e-6 to 7e-6 M at ten layers is separate from initial 1.5e-6 M extreme dilution and its negative outcome.',
 'Primary, secondary and no-added-amine alternatives retain distinct outcomes and residual core-bound amine; proposed state sample_set correction prevents combined-batch implication.',
 'All-sulfur-at-start is a distinct 13-monolayer-equivalent/four-hour Cd-increment schedule, not preferred alternating SILAR.',
 'FTIR six purification cycles are preparation; 4 cm^-1/32 scans are acquisition. Pure-ligand references are separate specimens; proposed sample_set correction fixes typed state ambiguity.',
 'XRD deposition has no scan parameters; acquisition retains 1.5406 A, 10–90 deg, 0.005 deg and 0.100 deg/min. Phase fractions remain semiquantitative, with no supplied coordinates.',
 'TEM instrument identity retained without invented grid/voltage/statistical sample count. All 36 selected original crop hashes equal passed source assets.',
 'Single-dot 405 nm CW, approximately 15 mW/75 um, 20,000 frames, 100 ms integration and approximately 90 ms readout remain distinct from SI 91 ms. Liquid nitrogen is CCD coolant only.',
 'Lifetime pulsed 405 nm, approximately 70 ps, 400 kHz–2.5 MHz and low excitation regime remain analytical settings, not synthesis parameters.',
 'All eighteen Table S1 rows/180 values preserve sample scopes and printed mean coefficients. Recalculation from rounded means does not replace reported lifetime.',
 'SI 5.5 nm/16.9 ML examples are not force-joined to 15.57 ML final table row; the two dot-index-6 traces remain different populations.',
 'Pure-OA 1705 cm^-1 reference is distinct from particle acid-like approximately 1710 cm^-1; descending source range retains raw 3300-2500 while numeric bounds normalize order.',
 'All six source conflicts/eight missingness groups remain; source author interpretations, cited historical outcomes, hypothetical 11.2 nm core and empirical 750 nm^3/65 ns trends remain qualified.',
 'No training, exact atomic pairing, molecular/apparatus viewer, browser, Site integration or publication approval inferred. Source-neutral molecule qualification remains separate.'
]
findings=[{'id':'GHOSH-CAN-01','status':'open','category':'typed_grouped_specimen_scope','description':'Five states describe alternatives or separate analytical specimens but currently use reaction_batch/mixture. Existing schema sample_set is the scientifically appropriate grouped-state classification.','required_changes':[
 {'record_id':'ghosh-2012-anneal-series','state_id':'anneal-series-particles','field':'kind','expected':'sample_set'},
 {'record_id':'ghosh-2012-solvent-ligand-series','state_id':'solvent-series-particles','field':'kind','expected':'sample_set'},
 {'record_id':'ghosh-2012-solvent-ligand-series','state_id':'ligand-series-particles','field':'kind','expected':'sample_set'},
 {'record_id':'ghosh-2012-stoichiometry-series','state_id':'withdrawal-series-particles','field':'kind','expected':'sample_set'},
 {'record_id':'ghosh-2012-ftir-procedure','state_id':'ftir-film','field':'kind','expected':'sample_set','name':'Separate particle and pure-ligand FTIR specimens','reader_delta':'Update only corresponding operation input/output display labels.'}
 ],'scientific_values_changed':False}]
bound={x['path']:x['sha256'] for x in checks['bound_files']}
for p in [A/'check_proposal.py',A/'mechanical-checks-v1.json',A/'inspect_proposal.py',Path(__file__)]:bound[str(p)]=sha(p)
r={'schema':'mattersyn-independent-canonical-reader-audit/1','version':'v1','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'open_findings','author':'/root/backlog_eta','independent_reviewer':'/root/norberg2004_extract','proposal_freeze_sha256':sha(G/'canonical-proposal/v1/package-manifest.json'),'source_audit_sha256':sha(G/'source-independent-audit/independent-audit-v2.json'),'counts':checks['counts'],'checks':{'passed':checks['check_count'],'failed':0,'public_string_path_guards':checks['checks_by_category']['no_private_public_path'],'scientific_transport_and_other_checks':checks['check_count']-checks['checks_by_category']['no_private_public_path']},'manual_scopes':manual,'findings':findings,'source_review_basis':'This reviewer previously read/viewed all 19 original source pages and all 36 crops for the separately frozen source audit. This audit reads the new canonical/reader representations and verifies their transport against that passed source; it is not a claim of a second fresh visual reading of every source pixel.','excluded_gates':['molecule/apparatus science','mounted browser rendering','Site integration','publication','training admission','exact recipe–atomic structure pairing'],'bound_files':[{'path':p,'sha256':h} for p,h in sorted(bound.items())]}
(A/'independent-audit-v1.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(A/'independent-audit-v1.md').write_text('# Ghosh 2012 canonical/reader audit — v1\n\nStatus: open bounded classification finding GHOSH-CAN-01.\n\nAll 21 records, 33 operations, 325 reader items, 1,176 typed fields, 585 measurement contexts, 71 facts, 243 inventory units and 272 source table cells were checked. '+str(checks['check_count'])+' executed checks passed, including '+str(checks['checks_by_category']['no_private_public_path'])+' public-path string guards.\n\nFive grouped states should use the existing `sample_set` classification, with the FTIR specimen name and two reader labels clarified. No numerical, table, evidence, sample-identity or source correction was found. V1 author files remain unchanged.\n\n'+ '\n'.join('- '+x for x in manual)+'\n',encoding='utf-8')
print('audit_v1_sha256',sha(A/'independent-audit-v1.json'))
