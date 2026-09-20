from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;M=B.parents[3];S=M/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
p=read(B/'publication-checkpoint.json');assert p['deployment_status']=='succeeded';inv=read(S/'data/inventory-summary.json');s=inv['summary']
entry=f'''## 2026-09-19 — PbS quantum dots in glass added to the existing MatterSyn atlas

Published existing public MatterSyn Site version {p['public_live_version']}, dataset {p['dataset_version']}, commit {p['source_commit']} at {p['published_at']}. New material hub: {p['material_url']}. Six annealing variants join the same periodic-table atlas and the PbS component page. Whole-composite attribution and equal method cards are preserved. Native proof: research-assets/incoming-paper-monitor/reviews/jp0208743/publication-checkpoint.json.

Dantas, Qu, Silva and Morais, Anti-Stokes Photoluminescence in Nanocrystal Quantum Dots, J. Phys. Chem. B 2002, 106, 7453–7457, DOI 10.1021/jp0208743: all five supplied main pages text-read and visually inspected. Incoming/legacy mains are byte-identical, SHA256 c8fd35a429bf636fcccc5dfeb3211cea44299e911fbfc80e1a308c75b7b04917; final generation 2 unchanged. Matching SI not located or verified; no declaration observed. Later SI reopens review. All 21 references retained as citations; their full external papers were not independently inspected.

{p['records']} records: {p['synthesis_routes']} annealing routes, {p['supporting_procedures']} shared preparation/analysis/model procedures and {p['contextual_observations']} observations. Retained {p['operations']} operations, {p['measurement_entries']} measurement entries, {p['reader_evidence_items']} reader items covering {p['source_audit_units']} units, {p['typed_facts']} typed reader facts and {p['original_assets']} original crops including all seven figures. All independent source/canonical/reader/chemical/binding/apparatus audits and actual-build/runtime/browser checks passed. Molecular/reference assets include honest oxide formula-unit diagrams, source identity gaps, six illustrative embedded-particle specimens and reused verified carbonate connectivity. No atomic PbS coordinates, measured phase or missing diffraction are fabricated.

Scientific boundaries: shared precursor glass uses printed SiO2–Na2CO3–ZnO–Al2O3–PbO2–B2O3 powders, all amounts/proportions and sulfur reagent identity/introduction stage unknown. PbO2 is not corrected to PbO. Literal aluminum crucible at 1400 °C for 2 h remains a vessel-description concern, not silently rewritten as alumina. Fast cooling has no medium/rate; 350 °C for 3 h relieves stress. Six 600 °C anneals are SG1/2/3/4 = 1/3/6/12 h and AFM1/2 = 5/30 h. Shared preparation is displayed on each route with inherited provenance; six independently identified fusion batches are not implied. Unknown synthesis atmosphere is not argon merely because the laser is Ar-ion.

Optical estimates 24/27/40 Å for SG1/2/3 retain the prose size versus model-axis radius ambiguity. Figure 4 grain heights 40.19/291.24 Å and substrate depths 1.57/0 Å belong to AFM1/2, alongside rounded prose sizes; these are not lateral particle diameters or the same specimens as SG. Figure 1 SG1 inset axis extends to 3.5 eV although prose says both spectra 0.5–3.0 eV. Model curves are author calculations, not experimental bands. SG1 power exponent about 0.86 and the kW/cm² axis are preserved without invented beam area. The 2.476 eV narrow line has a proposed resonant-Raman origin, not a confirmed independently acquired Raman spectrum. TS-TPA, phonon/Auger arguments and surface-state mechanism remain hypotheses. No demonstrated laser threshold, quantum yield or raw curve digitization is implied.

Actual reviewed subset: {s['canonical_records']} canonical records, {s['synthesis_route_variant_records']} routes, {s['shared_preparation_workup_characterization_assay_procedures']} procedures, {s['contextual_observation_records']} observations, {s['public_material_hubs']} material hubs and {s['total_canonical_source_groups']} source groups. Training task exports: {json.dumps(inv['training_eligibility'])}. These counts do not establish independent experiments or full-corpus completion. Continue oldest saved initial arrival across both local folders with the existing heartbeat, no downloads; chatbot/DFT/new theory-comparison extensions stay deferred.

'''
mem=M/'MEMORY.md';old=mem.read_text(encoding='utf-8');assert entry.splitlines()[0]not in old;mem.write_text(entry+old,encoding='utf-8')
skill=M/'skills/mattersyn-paper-to-site/references/incoming-corpus.md';heading='## Melt-derived glass and size-metric provenance'
lesson='''

## Melt-derived glass and size-metric provenance

Lessons from Dantas et al. (2002), DOI 10.1021/jp0208743:

- A precursor batch list is not a stoichiometric final-glass formula. Keep powder identities, missing mixture proportions, unspecified dopant source and uncertain introduction timing separate from the host and embedded nanocrystal identity. Do not replace a printed oxide or questionable crucible material with a chemically more familiar alternative without verified evidence.
- Expose shared preparation on each treatment route when this makes the complete process understandable, but mark inherited conditions and common upstream lineage. Several annealing durations and analytical cohorts do not prove separately identified melt batches. Heating, fast cooling, stress relief, sample cutting and polishing require their own states; do not invent a quench medium, polishing solvent or atmosphere.
- Preserve the dimensional meaning of every size: a theoretical radius axis, generic prose size, AFM grain height, lateral feature size and substrate-reference depth are different quantities. Similar values from different cohorts are comparisons, not evidence of physical specimen identity. Ambiguous size metrics must not become diameter-conditioned training labels.
- Keep theoretical energy-level plots, fitted power-law exponents, instrument settings and measured spectra distinguishable. A near-excitation line attributed to resonant Raman is a source hypothesis, not proof of a separate Raman acquisition. Preserve axis/prose conflicts, explicit power-density units and absent beam geometry or raw values.
- For unspecified solid phases, a formula-unit composition drawing is preferable to inventing a discrete oxide molecule or atomic lattice. Only show valid reference structures when already verified, and label their independence from the source specimens.
'''
t=skill.read_text(encoding='utf-8');assert heading not in t;skill.write_text(t+lesson,encoding='utf-8')
(B/'memory-skill-checkpoint.json').write_text(json.dumps({'saved_at':datetime.now(timezone.utc).isoformat(),'memory':str(mem),'project_skill_reference':str(skill),'project_skill_sha256':hashlib.sha256(skill.read_bytes()).hexdigest(),'installed_skill_sync':'pending'},indent=2)+'\n',encoding='utf-8')
print('Memory and project skill saved; installed skill sync pending.')
