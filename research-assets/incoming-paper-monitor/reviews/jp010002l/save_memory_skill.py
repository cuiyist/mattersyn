from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;M=B.parents[3];S=M/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
p=read(B/'publication-checkpoint.json');assert p['deployment_status']=='succeeded'
inv=read(S/'data/inventory-summary.json');s=inv['summary'];r=read(S/'data/paper-reviews/braun2001.json')
entry=f'''## 2026-09-19 — CdS/HgS quantum-dot quantum wells added to the existing MatterSyn atlas

The user's standing reminder remains: new materials join the existing MatterSyn website, its periodic table and material hubs. Published version {p['public_live_version']}, dataset {p['dataset_version']}, commit {p['source_commit']} at {p['published_at']}. New CdS/HgS/CdS hub: {p['material_url']}. Three Braun methods also appear on the existing CdS page and a clearly labeled HgS component page. Same public Site and audience retained. Native proof: research-assets/incoming-paper-monitor/reviews/jp010002l/publication-checkpoint.json.

Braun, Burda and El-Sayed, Variation of the Thickness and Number of Wells in the CdS/HgS/CdS Quantum Dot Quantum Well System, J. Phys. Chem. A 2001,105,5548–5551, DOI10.1021/jp010002l: all four supplied main pages read and visually inspected. Both local main copies are byte-identical, SHA256 00ac817e60651f0e7f9faabe85ba18372ac37fea1f0f5d174779c982064b4184. Source generation 2 remained unchanged at final post-publication fingerprint. No SI declaration observed in the supplied main; matching SI not located or verified. Closure covers the supplied main only, and later SI reopens review. All nineteen references/notes retained as uninspected cited sources.

Nine records: three synthesis routes, three acquisition procedures and three contextual observations. Preserved 45 operations,75 measurements,85 reader items covering132 source units,179 typed facts and eight original crops (four figures and four experimental excerpts). Twelve chemical/product references added, two reused;25 material bindings and three architecture bindings. Source, canonical, reader, crop, molecular, binding and apparatus audits passed, followed by actual-build and representative browser checks. Exact hashes and validation scopes are private in the review folder.

Scientific boundaries: A–B–C, A–B–C–B–C and A–B–C–C–C–B–C remain distinct layer sequences. B replaces an outer CdS layer with HgS and leaves displaced Cd²⁺ in solution; C immediately after B uses that dissolved inventory. Only C after C calls for an additional, unquantified Cd dose. Equal outer radius in exchange diagrams prevents the appearance of deposition. Step A's3.5nm core and system/Figure1 3.2nm core conflict explicitly. Missing salts/counterions, hexametaphosphate form/dose, H₂S solution concentration/volume, pH reagents, synthesis temperature and workup are not invented. The~30s acidification time is not total growth time. Gas volume has no assumed standard pressure/temperature.

The source's room-temperature statement belongs to optical experiments; the PL Nd:YAG pump settings are separate from the OPO output and femtosecond transient-absorption excitation. Keep the rotating glass-cell thickness, sapphire-generated continuum, optical-delay resolution and pulse energy in their proper contexts. Water-reference Raman subtraction is not a nanocrystal Raman property. Figure1 contains architecture/wavefunction schematics and cited morphology, with no supplied TEM, XRD, SAED or measured atomic structure. Figure2's missing intermediate trace, Figure4's inset bleach label versus stimulated-emission interpretation, and source coupling interpretation remain explicit. No CIF, digitized raw spectrum, unreported phase or exact recipe–structure label invented.

Actual dataset totals: {s['canonical_records']} records, {s['synthesis_route_variant_records']} synthesis-route variants, {s['shared_preparation_workup_characterization_assay_procedures']} procedures, {s['contextual_observation_records']} observations, {s['public_material_hubs']} public material hubs and {s['total_canonical_source_groups']} source groups. Training exports: {json.dumps(inv['training_eligibility'])}. These are task entries and reviewed-subset counts, not independent experiments or full-corpus totals. Continue the oldest eligible local arrival in both folders through the existing heartbeat, no downloads, same CdSe standard. Future chatbot, DFT and theory-comparison work remains deferred.

'''
mem=M/'MEMORY.md';old=mem.read_text(encoding='utf-8');assert not old.startswith(entry.splitlines()[0]);mem.write_text(entry+old,encoding='utf-8')
skill=M/'skills/mattersyn-paper-to-site/references/incoming-corpus.md'
heading='## Repeated layer exchange and optical acquisition context'
lesson='''

## Repeated layer exchange and optical acquisition context

Lessons from Braun et al. (2001), DOI10.1021/jp010002l; apply where the inspected source supports them:

- Represent surface replacement differently from deposition. An exchange diagram must conserve its illustrative outer radius, and displaced ions that remain in solution must remain available to a subsequent operation. Repeat-block notation does not authorize extra reagent additions or workup. Conditional precursor additions belong only to their stated branches; missing doses remain unknown.
- Keep an acidification onset distinct from total crystal-growth duration, nominal system core dimensions distinct from conflicting general-preparation sizes, and gas volume distinct from a mole amount without pressure/temperature reference conditions. A generic ion name cannot identify its salt, counterion or hydrate; a stabilizer name need not identify one discrete polymer structure.
- Separate synthesis conditions from analytical room temperature, laser-pump pulse settings from OPO output characterization, delay-stage resolution from instrumental response, pulse energy from fluence, and optical hardware from synthesis ingredients. Preserve the source's own signal-label conflicts.
- A water-reference subtraction that removes Raman background does not supply a Raman spectrum of the material. An architecture drawing or cited wavefunction sketch is not microscopy, measured atomic geometry or an exact-structure training target. Missing intermediate traces and raw matrices remain explicit without invented interpolation or digitization.
- Keep the new material discoverable through the existing periodic table and retain equal method cards on relevant existing component hubs, with whole-heterostructure attribution. Source-level completeness and batch-level training eligibility remain separate judgments.
'''
t=skill.read_text(encoding='utf-8');assert heading not in t;skill.write_text(t+lesson,encoding='utf-8')
out={'saved_at':datetime.now(timezone.utc).isoformat(),'memory':str(mem),'project_skill_reference':str(skill),'project_skill_sha256':hashlib.sha256(skill.read_bytes()).hexdigest(),'installed_skill_sync':'pending'}
(B/'memory-skill-checkpoint.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print('Saved publication evidence and reusable scientific workflow; installed skill synchronization pending.')
