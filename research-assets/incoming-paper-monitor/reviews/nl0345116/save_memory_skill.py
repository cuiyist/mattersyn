from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;M=B.parents[3];S=M/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf8'))
p=read(B/'publication-checkpoint.json');assert p['deployment_status']=='succeeded';inv=read(S/'data/inventory-summary.json');s=inv['summary']
entry=f'''## 2026-09-19 — PbSe particles and assemblies added to the existing MatterSyn atlas

Published the SAME existing public MatterSyn Site version {p['public_live_version']}, dataset {p['dataset_version']}, commit {p['source_commit']} at {p['published_at']}. New PbSe hub in the existing periodic-table atlas: {p['material_urls']['PbSe']}. Reader: {p['paper_url']}. User reminder honored: new materials belong in this existing Site. Proof: research-assets/incoming-paper-monitor/reviews/nl0345116/publication-checkpoint.json.

Sashchiuk, Amirav, Bashouti, Krueger, Sivan and Lifshitz, PbSe Nanocrystal Assemblies: Synthesis and Structural, Optical, and Electrical Characterization, Nano Letters 2004, 4(1), 159–165, DOI 10.1021/nl0345116 (online November 26, 2003). All seven supplied main pages text-read and visually inspected. Two byte-identical copies across incoming and legacy folders, main SHA256 72684e3bf22a2ef173ea1d6d6e31648a1222b2b15bc069bb8fe6cef8d1876a33; final generation 2 unchanged. SI not located or verified; no SI used. All 67 references retained as citations, without claiming their external full texts were read. Later or changed evidence reopens scope.

Retained {p['records']} canonical records: {p['synthesis_routes']} growth routes, {p['supporting_procedures']} procedures and {p['contextual_observations']} observations; {p['operations']} operations and {p['measurement_entries']} measurement entries. Reader {p['reader_evidence_items']} items covers {p['source_audit_units']} source units, with {p['typed_facts']} typed facts. All five figures and eight excerpts retained ({p['original_assets']} assets), including actual SAED Figures 1E/2C, HRTEM, absorption and electrical I–V. Twelve new chemical/identity entries plus six reused references cover 42 material slots. Independent source, canonical, reader, chemical, ideal-crystal, binding and apparatus audits passed, along with actual build/runtime/browser checks.

Scientific boundaries: Se/Pb-cHxBu/TBP mass ratios 0.25:0.6:50, 0.5:1.2:50 and 1:2.5:50 are not absolute charges, stock molarity or injected amount. Pb-cHxBu is printed lead-cyclohexanebutirate; exact molecular identity unresolved. Selenium allotrope and stock speciation unknown; TBP is tributylphosphine. Stock prepared at room temperature under inert glovebox conditions. Inject into 6.0 g TOPO (90% OR 99%) at 150 °C under argon flow; immediate decrease to 118 °C. Low branch 118 °C/15 min then rapid cooling to 70 °C; extended branch heated to 150 °C, up to 150 min. Gradual/fast heating wording and caption/body/summary ratios conflict explicitly. Aliquot withdrawal every few minutes into 1 mL methanol and repeated methanol–butanol redissolution/centrifugation are not a fully specified bulk workup; butanol isomer, solvent ratio and separation settings unknown.

Individual particle size, spherical assembly diameter, wire width/length and constituent cube size remain separate. Figure 1A ~5 nm is an ~5 min aliquot, not the 15 min endpoint. Figure 2 wire caption and text ratios conflict. High-concentration 40 min wires are explicitly not shown. Source rock-salt a = 6.1 Å / (200) spacing 3.05 Å supports an explicitly constructed ideal reference, not sample coordinates. Eight-site conventional cell is exported fully expanded as P1 (ideal prototype Fm-3m); finite 4096-atom PbSe block has a chosen 4.88 nm cell envelope and 4.575 nm atom-center span. CIF/XYZ and two-color rotatable viewer retain referenceOnly, no measured-coordinate or training eligibility. No ligand positions or assembled-wire atom reconstruction invented.

Device fabrication is separate: p-doped Si/200 nm oxide, literal trimethylsilane name (not substituted with chlorotrimethylsilane), optical markers, wire spin coating, SEM localization, PMMA/annealing, EBL, Ti/Au evaporation and resist removal. Three wire dimensions and room-temperature I–V retained; reported resistivity 0.15 Ω·cm and conductivity ~7 Ω^-1·cm^-1 have source precision. General SEM 4 kV versus Figure 5B 10.0 kV label remains explicit. Gate/temperature dependence deferred by authors. Absorption broadening/redshift and dipole/transport mechanisms retain measured versus author-calculated status. Printed model equations, unusual dielectric grouping and microeV scales retained with dimensional concerns; no silently repaired theory or raw curves.

Actual reviewed subset now {s['canonical_records']} records, {s['synthesis_route_variant_records']} routes, {s['public_material_hubs']} hubs and {s['total_canonical_source_groups']} source groups. Training eligibility: {json.dumps(inv['training_eligibility'])}. These are not independent-experiment counts or whole-corpus completion. Continue saved oldest local arrival, one paper end-to-end, no downloads, existing heartbeat. Future chatbot, DFT tools and broader theory comparisons remain deferred.

'''
mem=M/'MEMORY.md';old=mem.read_text(encoding='utf8');assert entry.splitlines()[0]not in old;mem.write_text(entry+old,encoding='utf8')
skill=M/'skills/mattersyn-paper-to-site/references/incoming-corpus.md';heading='## Assembly morphology, device fabrication and ideal references'
lesson='''

## Assembly morphology, device fabrication and ideal references

Lessons from Sashchiuk et al. (2004), DOI 10.1021/nl0345116:

- Mass ratios do not establish absolute charges, injected amounts or concentrations. Preserve differing caption, main-text and summary ratios without averaging or selecting a preferred value. Keep a trajectory interval separate from a uniquely timed batch.
- Separate individual crystallite dimensions, assembly diameters, wire dimensions and building-block sizes. Single-crystal-like SAED from an ordered assembly does not prove an atomically fused, defect-free wire. Keep microdiffraction described but not shown distinct from supplied original SAED.
- Device fabrication and its surface changes are separate from colloidal synthesis and microscopy preparation. Do not assign a TEM grid to SEM, a numerical anneal to unspecified processing, or a more plausible silylation reagent to an ambiguous printed name. Literal molecular depiction and unresolved chemical identity must remain explicit.
- Source-specific apparatus scenes must preserve composition through time: no nanocrystals before precursors enter; assembly stages should use a cluster/chain motif rather than silently resembling isolated particles. Source images and illustrative motifs remain distinct.
- When the source gives a rounded lattice parameter but no coordinates, an explicitly constructed ideal prototype can aid readers. Use a valid symmetry-aware CIF or a fully expanded P1 export; label the ideal prototype separately. Check periodic coordination and finite atom counts, state visualization envelope versus atom-center span, and exclude all generated geometry from measured-structure labels. Finite models need species-specific colors, explicit nonperiodicity and no invented surface ligands.
- Preserve original equation crops when printed powers, dielectric grouping or energy units are questionable. A dimensional concern belongs beside the literal source expression; do not quietly replace it with a physically preferred formula. Author models, measured curves, cited bulk parameters and prospective gate/temperature experiments require separate evidence roles.
'''
t=skill.read_text(encoding='utf8');assert heading not in t;skill.write_text(t+lesson,encoding='utf8')
(B/'memory-skill-checkpoint.json').write_text(json.dumps({'saved_at':datetime.now(timezone.utc).isoformat(),'memory':str(mem),'project_skill_reference':str(skill),'project_skill_sha256':hashlib.sha256(skill.read_bytes()).hexdigest(),'installed_skill_sync':'pending'},indent=2)+'\n',encoding='utf8')
print('Project memory and reusable skill saved; installed sync pending.')
