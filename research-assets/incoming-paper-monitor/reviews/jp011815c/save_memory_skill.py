from pathlib import Path
import json
B=Path(__file__).resolve().parent
M=B.parent.parent.parent.parent
p=json.loads((B/'publication-checkpoint.json').read_text(encoding='utf-8'))
assert p['status']=='published' and p['deployment_status']=='succeeded'
heading='## 2026-09-19 — Pt, Ag and Ir supercritical-fluid synthesis published in the existing atlas'
text=f'''{heading}

Published existing public MatterSyn Site version 20, dataset 0.13.0, commit {p['source_commit']} at {p['published_at']}. Pt is now discoverable through the same periodic table at https://mattersyn-recipe-atlas.cuiy781513.chatgpt.site/material.html?id=pt-b602b7; the existing Ag and Ir pages gained the Shah2001 methods. Ag retains the Stiger Ag/Si contribution alongside nine new direct routes. All new material contributions continue to join this Site. Native proof: research-assets/incoming-paper-monitor/reviews/jp011815c/publication-checkpoint.json.

Shah, Husain, Johnston and Korgel, Nanocrystal Arrested Precipitation in Supercritical Carbon Dioxide, J. Phys. Chem. B 2001, 105, 9433–9440, DOI 10.1021/jp011815c: all eight supplied main pages read and visually reviewed. Two local copies are byte-identical, SHA256 2e6310ab5f5c6102ffa46e91dc3ccc2a180e6a6d17fd6a82ef448867edd79967. Generation 2 remained unchanged at the final post-publication fingerprint {p['source_fingerprint_at']}. Matching SI not located or verified; closure applies to supplied main only. All 48 references/notes retained as source references, not represented as independently read papers.

Nineteen canonical records comprise eleven synthesis routes (nine Ag, one Ir, one Pt), four supporting procedures and four contextual observations. Retained 74 operations, 111 measurement entries, 138 reader items covering 214 source units, 253 typed facts and 21 original assets (eleven figures, one table, three equations and six source excerpts/notes). Eighteen chemical/product references added, seven reused, 99 material slots linked and 13 product bindings supplied. Independent source, canonical, reader, original-crop, molecular and apparatus audits passed. Browser checks exercised representative discovery, method switching, molecular controls, pressure-cell stages, figure enlargement, evidence search and Ir reference lattice controls; the QA file records the exact scope. Do not promote every asset's reader-render flag from representative interaction checks.

Scientific limits: 27 mL working-volume cell versus fluid fill and injection-loop capacities; front reaction chamber versus backside CO2 pressure control; 138 bar fill versus 276 bar reaction; typical Ag mass ranges versus individual A–I row concentrations; common inherited Ir/Pt timing remains inferred. Preserve ambiguous printed Pt precursor name without guessed formula or geometry. C8 fluorothiol is distinct from the prior C10 comparator. Distribution spreads are not uncertainties. Ag-specific EDS and unassigned microscopy do not become Ir/Pt evidence through a shared acquisition procedure; equal rounded sizes do not establish batch identity. Optical comparisons, author models, ideal sticking assumptions, particle packing and atomistic symmetry remain distinct. No XRD, SAED, Ag/Pt coordinates or measured phase invented. Existing verified Ir bulk structure is a comparison only. Display shared reagent specifications once with all record links while preserving all typed facts in the canonical data.

Totals now 272 records = 64 routes + 14 controls + 68 procedures + 26 observations + 100 benchmark rows; 24 hubs = 19 direct systems + 5 component hubs; 19 source groups = 18 literature + one benchmark. Formal supplied-main-only reviews cover 8 papers/64 pages, and six matched-main/SI reviews cover 80 PDF pages separately. Training exports: 64 precursor-selection, 80 partial-protocol, 15 size-conditioned, zero exact-structure, zero success and 95 optical entries. These are task entries, not independent experiments or complete-corpus counts. All five evidence-backed milestones closed for this supplied main. Continue oldest eligible local arrival through the existing five-minute heartbeat, no downloads, same CdSe quality and same Site. Later SI reopens its source. Chatbot, DFT and theory-comparison work remains deferred.

'''
memory=M/'MEMORY.md'
old=memory.read_text(encoding='utf-8')
if heading not in old: memory.write_text(text+old,encoding='utf-8')
ref=M/'skills/mattersyn-paper-to-site/references/incoming-corpus.md'
addition=(B/'skill-lessons-draft.md').read_text(encoding='utf-8').replace('# Proposed addition: pressure-cell experiments and comparative evidence','## Pressure-cell experiments and comparative evidence').replace('Additional lessons from the independently audited Shah et al. (2001), DOI 10.1021/jp011815c, after comparison with the project skill\'s `references/incoming-corpus.md`:','Lessons from Shah et al. (2001), DOI 10.1021/jp011815c; apply when the inspected source supports these distinctions:')
addition+='\nFor shared reagent specifications, the reader may group identical facts and show their linked-record count. Preserve each canonical source pointer and record link; never use display deduplication to merge independent measurements or outcomes.\n'
old=ref.read_text(encoding='utf-8')
if '## Pressure-cell experiments and comparative evidence' not in old: ref.write_text(old.rstrip()+'\n\n'+addition,encoding='utf-8')
print('Publication memory and scoped project skill lessons saved.')
