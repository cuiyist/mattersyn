from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;M=B.parents[3];S=M/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
p=read(B/'publication-checkpoint.json');assert p['deployment_status']=='succeeded';inv=read(S/'data/inventory-summary.json');s=inv['summary']
entry=f'''## 2026-09-19 — CdS in mesoporous silica added to the existing MatterSyn atlas

Published existing public MatterSyn Site version {p['public_live_version']}, dataset {p['dataset_version']}, commit {p['source_commit']} at {p['published_at']}. New material hub: {p['material_url']}. The CdS/SiO2 composite, SiO2 host and existing CdS component page preserve equal source-method cards and periodic-table discovery. Same Site identity and audience. Evidence: research-assets/incoming-paper-monitor/reviews/nl015685v/publication-checkpoint.json.

Besson et al., 3D Quantum Dot Lattice Inside Mesoporous Silica Films, Nano Letters 2002,2(4),409–414, DOI10.1021/nl015685v: all six supplied main pages read and visually inspected. Incoming/legacy main copies are byte-identical, SHA2569f1b5b781e7a36f1ec109eb14ee724bb6c99a8156b4bc6899cfffe8ab613c357; final source generation2 unchanged. Matching SI not located or verified; no SI declaration observed. Later SI reopens review. All43references/notes retained; cited external works were not independently inspected.

{p['records']} canonical records: {p['synthesis_routes']} routes, {p['supporting_procedures']} procedures and {p['contextual_observations']} contextual observations. Preserved {p['operations']} operations,{p['measurement_entries']} measurement entries,{p['reader_evidence_items']} reader items covering{p['source_audit_units']} source units,{p['typed_facts']} typed reader facts and{p['original_assets']} original crops (four figures and six source excerpts). Independent source/canonical/reader/crop/molecular/binding/apparatus audits and actual-build/browser checks completed. Unknown source quantities remain explicit. New TEOS conformer and disconnected CTAB/Cd-nitrate representations are references, not measured solution/crystal geometries; nitrate is not mislabeled as a nitro group.

Scientific boundaries: TEOS:water:ethanol1:5:3.8 is molar; pH1.25 belongs to the input water, acid unknown. Sol aging1h/60°C precedes CTAB (CTAB/TEOS0.1); ethanol dilution1:1 has no specified basis. Pyrex spin3000rpm and450°C air calcination have missing durations. Initial Cd-nitrate solution0.1M is not its final concentration after citrate/ammonia additions; citrate stock1M and1equiv additives remain distinct. pH9.5 loading, deionized rinse retaining the film, vacuum and slow H2S to atmospheric pressure repeat as a trajectory. No drying/isolated powder or numeric gas dose is invented. Pre-H2S Cd-loaded film has no sulfur product assignment. Unknown copolymer preparation remains separate from CTAB; inherited common loading is marked.

P6₃/mmc and approximatelya6.0/c6.8nm describe the mesoscopic pore/particle lattice, not atomic CdS. Figure3d is an image Fourier power spectrum, not SAED. Some CdS particles show blende-type111fringes; no measured atomic CIF or matching local crystal reference is supplied. XRDc6.9→6.8→7.2nm and HRTEMc~6.8nm retain their method scopes; XRD trace scaling×0.5/×5 is explicit. Optical sizes are derived from a cited calibration, not direct TEM sizes. Estimated13%CdS/15%porosity/about85%filling differs from qualitative total filling and visible residual empty pores. PL uses a separate silicon-wafer film; template identity is unassigned. Figure4 caption/prose upper-lower stage conflict remains unresolved, with originals retained. Room temperature is an optical condition, not an inferred synthesis temperature. Interpretation about vacancies/passivation/silica interactions is source hypothesis, not measured surface reconstruction.

Actual reviewed subset totals: {s['canonical_records']} records,{s['synthesis_route_variant_records']} routes,{s['shared_preparation_workup_characterization_assay_procedures']} procedures,{s['contextual_observation_records']} observations,{s['public_material_hubs']} hubs,{s['total_canonical_source_groups']} source groups. Training exports: {json.dumps(inv['training_eligibility'])}. These are task entries, not independent experiments or full-corpus completion. Host_matrix roles and explicit target-host labels distinguish the two CdS/SiO2 hosts in training; multi-outcome loading trajectories do not receive an arbitrary first-size-conditioned label. Continue oldest saved local arrival in both folders via existing heartbeat, no downloads; future chatbot/DFT/theory extensions remain deferred.

'''
mem=M/'MEMORY.md';old=mem.read_text(encoding='utf-8');assert entry.splitlines()[0]not in old;mem.write_text(entry+old,encoding='utf-8')
skill=M/'skills/mattersyn-paper-to-site/references/incoming-corpus.md';heading='## Porous hosts, repeated loading and lattice scale'
lesson='''

## Porous hosts, repeated loading and lattice scale

Lessons from Besson et al. (2002), DOI10.1021/nl015685v:

- Preserve host preparation, pore loading and substrate-specific characterization as separate branches. A cadmium-ion-impregnated silica film is not yet a CdS product. Rinsing retains the supported film, and repeated adsorption/precipitation cycles form a trajectory rather than independent synthesis batches. An unnamed copolymer host does not inherit the CTAB recipe.
- Distinguish input-water pH from mixed-sol pH; initial salt concentration from final concentration after additives; molar sol ratios from an unspecified dilution basis; and symbolic atmospheric-pressure endpoints from an assumed numeric pressure. Keep unreported acid, hydrate and polymer identities unresolved.
- Separate mesoscopic pore or nanoparticle-superlattice symmetry from atomic crystal symmetry. An image Fourier power spectrum is not acquired SAED. Explicitly distinguish atomic fringes, low-angle host diffraction, pore-size estimates and optically inferred particle dimensions; do not fabricate an atomic CIF.
- Preserve trace rescaling, caption/text assignment conflicts, method-dependent lattice parameters and differences between model-derived pore filling, qualitative completeness and visible empty pores. Do not silently assign a plotted PL curve to a specimen when its caption conflicts with prose.
- Audit functional-group semantics as well as formula/connectivity: a nitrate ion is not a nitro group. Use host_matrix roles and explicit target-host context in task exports when the source distinguishes templates. Multi-outcome trajectories need explicit outcome selection before size-conditioned training; never let a helper silently choose the first size.
'''
t=skill.read_text(encoding='utf-8');assert heading not in t;skill.write_text(t+lesson,encoding='utf-8')
(B/'memory-skill-checkpoint.json').write_text(json.dumps({'saved_at':datetime.now(timezone.utc).isoformat(),'memory':str(mem),'project_skill_reference':str(skill),'project_skill_sha256':hashlib.sha256(skill.read_bytes()).hexdigest(),'installed_skill_sync':'pending'},indent=2)+'\n',encoding='utf-8')
print('Memory and project skill saved; installed skill sync pending.')


