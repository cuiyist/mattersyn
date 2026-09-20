from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
D=Path(__file__).resolve().parent;G=D.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
scope='''core-charge|Main2|100 mL round-bottom flask, condenser/thermocouple; 1 g TOPO, 8 mL ODE, 0.38 mmol cadmium oleate. No precursor-preparation or dissolved-speciation inference.
core-evacuate|Main2|Sequential 30 min room-temperature vacuum, 30 min at 80 °C under vacuum, then 300 °C under argon. No pressure, flow or bath type invented.
core-inject|Main2|Rapid TOP–Se 4 mmol with oleylamine 3 mL and ODE 1 mL, followed by 270 °C growth. Whole formulation charges, not per-layer shell doses or a measured final volume.
core-grow-cool|Main2|Several minutes, then room temperature; standard 3 or 4 nm context without invented exact time-to-size calibration.
core-isolate|Main2|Ethanol precipitation/centrifugation and hexane redispersion, 2–3 cycles. Retain particles; no rpm, duration or solvent-volume invention.
small-quench|Main2|Cold toluene several seconds after common injection gives 2.2 nm branch; no numeric quench temperature, delay or ice bath.
small-isolate|Main2|Inherited 2–3-cycle ethanol/hexane workup; common upstream charge is referenced rather than charged again.
large-feed|Main2|About 10 min initial growth; extra 0.8 mmol Cd oleate and 8 mmol TOP–Se dropwise at 270 °C, then 10 min at 300 °C. No feed rate or final batch totals inferred.
large-isolate|Main2|5.5 nm branch uses common isolation; no additional common precursor charge or made-up separation settings.
shell-charge|Main2–3|250 mL round-bottom flask, approximately 2e−7 mol washed cores with 5 mL oleylamine and 5 mL octadecane; no unique seed batch or gas condition invented.
shell-passivate|Main2–3|One Cd monolayer equivalent prepassivates Se-rich cores; separate from full S/Cd cycles, no measured surface geometry or exact dose volume.
shell-cycles|Main2–3|Two 0.2 M stocks in OD, 240 °C, post-S 1 h and post-Cd 2.5 h; Cd:OA 1:4 first 5–8 cycles then 1:10. Half additions versus full cycles explicit; exact ligand-switch cycle unknown.
shell-withdraw|Main3|Remove 1% of reaction-solution volume after full cycles; subsequent planned precursor charges unchanged. Not a molar precursor excess or 1% particle count.
shell-purify|Main3|2–3 precipitation/redispersion cycles with ethanol/hexane; distinct from six-cycle FTIR preparation and QY acquisition.
compare-anneals|Main3 Table1 and Main4|Five separate S/Cd schedules (10min/10min,10min/3h,3h/10min,1h/3h,3h/1h); no combined sequential schedule. QYs and rounded narrative totals are contexts, not controls.
compare-ode-od|Main4–5 Table2|ODE versus OD alternatives; late dilution starts at 10 ML, dot concentration 9e−6 to7e−6 M. No universal additional stock dose or solvent mixture.
extreme-dilution|Main5|Initial dot concentration 1.5e−6 M; separate negative-outcome context, not endpoint of preceding late dilution. No invented full formulation.
compare-ligands|Main5–6|Primary oleylamine, secondary dioctylamine, and no-added-amine are alternatives. Residual core-bound amine possible; 15 mmol belongs primary-amine context, OA after14ML is context.
compare-withdrawals|Main6 and Table3|1% versus10% reaction-volume removals are alternatives after full cycles; preserve planned precursor dosing. TEM moderate-shell versus >15ML QY remains separate.
withdraw-oa|Main6 and Table3|1% removal plus2.5-fold OA increase from unresolved 5th–8th-layer transition; exact switch and doses absent. Morphology/QY remain observations.
constant-s-grow|Main6–7 and SI4|All sulfur for13 layers initially, then Cd-only additions at4h intervals; no repeated sulfur dosing, measured13-layer universal endpoint or invented full formulation.
ftir-purify-cast|Main2|Particle six-cycle wash, then separate particle or pure-ligand hexane deposits onto diamond ATR and solvent evaporation. No six-cycle ligand washing or co-mixture of all references.
ftir-acquire|Main2|Nicolet6700,4 cm−1 resolution,32 scans; pure-ligand references remain separate. No synthetic spectrum or inherited wash condition.
tem-acquire|Main2|JEOL2010 TEM; voltage, grid and deposition unreported. No invented micrograph, SAED or atom positions.
xrd-deposit|Main2|Deposit onto background-less silicon, not copper TEM grid. No acquisition settings applied during deposition.
xrd-acquire-fit|Main2 and SI4|RigakuUltimaIII CuKα1.5406Å,10–90°2θ,.005°width,.100°/min; Jade9 WPF/Rietveld phase estimates semiquantitative. No invented pattern, lattice or CIF.
ensemble-acquire|Main2–3|CARY UV–Vis–NIR,Horiba NanoLog; separate Rhodamine6G reference.99% is material grade, not product QY; concentrations not invented.
single-deposit|Main2|Dilute hexane until resolved single dots; deposit on acetone-cleaned glass. No fixed dilution factor or film thickness.
single-acquire|Main2 and SI8–9|CW405nm,approximately15mW/75µm;LN2 coolsCCD,not specimen.20,000 frames,100ms integration,~90ms main/91msSI readout; no fabricated optical path.
single-analyze|Main2 and SI8–9|I_pix>BG+2sqrt(BG),unsubtracted rawpixel; denominator dots ever emitted.>99% prose versus≥99%figure preserved; no synthetic trajectory.
lifetime-deposit|Main2|Hexane rough film on glass; distinct from single-dot dilution. Amount, thickness and concentration remain missing.
lifetime-acquire-fit|Main2–3 and SI7|~70ps405nm,400kHz–2.5MHz,~100µm,qualitativepower range;<N>~1e−5;100×NA1.3oilobjective,SPAD/TCSPC,triexponential.ΣAτ²/ΣAτ described neutrally, no synthetic decay or model/sample certainty.
core-control-wash|SI9|Separate7nm control with missing upstream prep: unwashed~15%/680nm,washed nondetect; diluted unwashed slide also nondetect. No exactzero QY or inherited5.5nm recipe.'''
rows=[]
for line in scope.splitlines():
 oid,loc,notes=line.split('|',2);rows.append({'operation_id':oid,'source_scope':loc,'required_distinctions':notes,'final_frozen_scene_review':'pending'})
assert len(rows)==33
pages=['main-02','main-03','main-04','main-05','main-06','main-07','si-09']
files=[G/'source-render'/f'{p}.png'for p in pages]+[G/'source-facts.json',G/'source-tables.json',G/'source-independent-audit/independent-audit-v2.json',G/'canonical-proposal/v2/package-manifest.json']
out={'schema':'mattersyn-independent-apparatus-source-checklist/1','auditor':'/root/backlog_eta','apparatus_author':'/root/norberg2004_extract','prepared_at':datetime.now(timezone.utc).isoformat(),'status':'prepared_before_final_apparatus_freeze_not_an_approval','manual_source_scope':'Targeted stage reread of main PDF2–7 and SI9 text/native images; previously passed extraction and full-source peer audit reused for complete source context. Final apparatus views are pending.','operations':rows,'bound_inputs':{str(p):sha(p)for p in files},'independent_apparatus_approved':False}
(D/'source-stage-checklist.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(len(rows))
