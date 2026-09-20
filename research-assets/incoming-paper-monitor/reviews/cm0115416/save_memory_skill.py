from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;M=B.parents[3];S=M/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf8'))
p=read(B/'publication-checkpoint.json');assert p['deployment_status']=='succeeded';inv=read(S/'data/inventory-summary.json');s=inv['summary']
entry=f'''## 2026-09-19 — Yb/Er-codoped lanthanum molybdate added to the existing MatterSyn atlas

Published existing public MatterSyn Site version {p['public_live_version']}, dataset {p['dataset_version']}, commit {p['source_commit']} at {p['published_at']}. Material hub: {p['material_url']}. Five hydrothermal/annealing comparisons and one separate solid-state bulk method join the same periodic-table atlas with equal method cards. Native proof: research-assets/incoming-paper-monitor/reviews/cm0115416/publication-checkpoint.json. User reminder honored: new materials belong in the existing MatterSyn site.

Yi, Sun, Yang, Chen, Zhou and Cheng, Synthesis and Characterization of High-Efficiency Nanocrystal Up-Conversion Phosphors: Ytterbium and Erbium Codoped Lanthanum Molybdate, Chem. Mater. 2002, 14, 2910–2914, DOI 10.1021/cm0115416. All five supplied main pages text-read and visually inspected. Incoming/legacy copies byte-identical, SHA256 6438ee53b3fffb86f5e36508f265041d9235b8ee9f3e20dd99d46aae91c68a57; final generation 2 unchanged. Matching SI not located or verified, no SI declaration observed; later SI reopens review. All 27 references retained as citations; their external full texts not independently inspected.

Retained {p['records']} canonical records: {p['synthesis_routes']} synthesis routes, {p['supporting_procedures']} procedures and {p['contextual_observations']} interpretation record. {p['operations']} operations, {p['measurement_entries']} measurement entries, {p['reader_evidence_items']} reader items covering {p['source_audit_units']} units, {p['typed_facts']} typed facts, and {p['original_assets']} original crops including all ten figures. Independent source/canonical/reader/chemical/binding/apparatus audits and integrated/runtime/browser checks passed. Eighteen new identity/composition/specimen cards and the existing verified water reference cover all 57 material slots. All 105 operation scenes have source-specific apparatus/conditions. No source atomic coordinates or SAED were supplied or invented.

Scientific boundaries: solution A uses La2O3 1.1760 g/3.607 mmol, Yb2O3 0.3692 g/0.937 mmol and Er2O3 0.05370 g/0.140 mmol, dissolved in diluted nitric acid, warmed dry and redissolved in 30 mL deionized water. Solution B prints (NH4)2MoO4 1.961 g/9.37 mmol: mass/mole and nominal host feed stoichiometry conflict, both retained without repair. Added water is not measured final solution volume. B into A at 20–30 drops/min, then 20 min stirring; 100 mL Teflon vessel, 180 °C/1 h, 6000 rpm/10 min, two water washes, air dry. Main 800 °C route has 20 °C/min ramp, 5 h hold and natural cooling; nano-annealing atmosphere remains unreported. Five 600/700/800/900/1000 °C comparisons do not establish individually quantified precursor batches. Bulk route uses La2O3/MoO3/Yb2O3/Er2O3 with La:Yb:Er 77:20:3, pressed pellet, air 1200 °C/5 h; absolute charges and Mo ratio missing. Grinding control has no invented equipment or size.

Only the 800 °C powder is explicitly tetragonal with a minor unidentified second phase (ICDD45-0407). Scherrer52.5 nm (peak28.053°, widths0.186°/0.104°), TEM40–60 nm and intensity-based particle-analyzer45–65 nm/mean53 nm remain distinct metrics/specimen contexts. Figure2 scale bars300/100 nm retain pre/postanneal identity. Generic analysis figures are not automatically assigned the800 °C batch. Down-conversion374 nm excitation yields525/549 nm; up-conversion980 nm has519/541/653 nm. Source50 mW laser specification is not irradiance, photon dose or every power-sweep setting. Near-IR absorption10238 cm-1/976 nm preserves wavenumber axis semantics. Figure7 actual Er markers1,2,3,4,5,7% exclude invented6%;4% plotted/prose disagreement retained. Figure8 caption520 versus519 nm elsewhere and precise/rounded fitted slopes remain explicit. OriginalFigure9 levels include4F9/2 and4I9/2. Mechanisms, lifetime/surface explanations, proposed applications and efficiency rhetoric are not measured quantum yield, lifetime or demonstrated assays/devices.

Actual reviewed subset: {s['canonical_records']} canonical records, {s['synthesis_route_variant_records']} routes, {s['public_material_hubs']} material hubs, {s['total_canonical_source_groups']} source groups. Training eligibility: {json.dumps(inv['training_eligibility'])}. These are not independent-experiment or full-corpus completion counts. Continue oldest saved local arrival across both folders, no downloads, existing heartbeat. Deferred chatbot/DFT/new theory work remains deferred.

'''
mem=M/'MEMORY.md';old=mem.read_text(encoding='utf8');assert entry.splitlines()[0]not in old;mem.write_text(entry+old,encoding='utf8')
skill=M/'skills/mattersyn-paper-to-site/references/incoming-corpus.md';heading='## Doped phosphors, comparison recipes and optical scope'
lesson='''

## Doped phosphors, comparison recipes and optical scope

Lessons from Yi et al. (2002), DOI 10.1021/cm0115416:

- Preserve a printed reagent formula, mass and mole amount separately when they disagree, including conflicts between the stated feed and nominal final host. Do not silently correct doses or infer exact stock molarities from added solvent volume. Nominal host/dopant notation is not refined occupancy.
- A common preparation can be displayed for each annealing comparison, but individual batch charges, ramps, cooling and atmospheres need their own reported/inherited/missing distinctions. Stage art and chemical reference captions must obey those distinctions. Bulk comparators may use different precursors and atmospheres and need a separate route.
- Keep generic analysis specimens separate when their precise annealing/batch linkage is unreported. TEM particle diameter, Scherrer crystallite size and an intensity-weighted particle-analyzer distribution cannot be merged merely because their central values agree. Retain before/after scale bars and impurity statements; do not invent SAED, atomic coordinates or refined phase purity.
- Read actual concentration markers and fit legends: a stated range does not establish every integer condition, and caption/body/curve discrepancies must remain visible. A laser power rating is not sample irradiance, a power sweep or an absolute yield. Proposed energy transfer, surface/lifetime explanations and application motivations remain author interpretations unless measured.
- When full synthesis records embed upstream stock preparation, distinguish precursor inventory stages needed by the training selector from physical operation stages; verify eligibility against the actual task exporter. Do not promote ambiguous size/outcome contexts to paired labels merely to increase training counts.
'''
t=skill.read_text(encoding='utf8');assert heading not in t;skill.write_text(t+lesson,encoding='utf8')
(B/'memory-skill-checkpoint.json').write_text(json.dumps({'saved_at':datetime.now(timezone.utc).isoformat(),'memory':str(mem),'project_skill_reference':str(skill),'project_skill_sha256':hashlib.sha256(skill.read_bytes()).hexdigest(),'installed_skill_sync':'pending'},indent=2)+'\n',encoding='utf8')
print('Memory and project skill saved; installed sync pending.')
