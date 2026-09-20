"""Close the scoped review only after verified native publication."""
from pathlib import Path
from datetime import datetime,timezone
import json
B=Path(__file__).resolve().parent;M=B.parents[3];S=M/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=read(B/'publication-checkpoint.json')
assert p['deployment_status']=='succeeded' and p['public_live_version']==17 and p['source_documents_unchanged']
assert p['source_commit']=='d3f60c4619dad299619616f9f938fd2a6989dbd3'
stages=read(B/'milestones.json')
assert all(stages[x]['status']=='complete'for x in ['read','extract','audit','integrate'])
stages['publish']={'status':'complete','evidence':[str(B/'publication-checkpoint.json')],'note':'Published on the existing public MatterSyn Site. Seven supplied main pages fully reviewed; matching SI not located or verified.'}
write(B/'milestones.json',stages)
c=read(B/'checkpoint.json');c.update(checkpoint_at=datetime.now(timezone.utc).isoformat(),website_published=True,public_live_version=17,dataset_version='0.10.0',publication_checkpoint=str(B/'publication-checkpoint.json'),source_commit=p['source_commit'],public_url=p['public_url'],source_fingerprint_at=p['source_fingerprint_at'],current_work_items=[{'label':k.capitalize(),'status':'complete','scope':v['note']}for k,v in stages.items()],next_action='Yao supplied-main review closed. Continue the oldest eligible existing local paper using the existing monitor. Reopen this source if matching new or changed SI arrives. Add reviewed materials to the same MatterSyn Site; do not start a separate website.')
write(B/'checkpoint.json',c)
entry=f'''## 2026-09-19 — CdS nanocrystals in chelate polymer particles published

Published public Site version 17, dataset 0.10.0, commit {p['source_commit']} at {p['published_at']}. Same existing MatterSyn Site and public audience. Selecting Cd and S exposes the new CdS/polymer hub (material?id=cds-polymer-e10fe3); both aqueous synthesis methods also appear as composite contributions on the existing CdS page. The user reminder to add materials to the existing atlas remains in force. Native publication proof: research-assets/incoming-paper-monitor/reviews/la970480g/publication-checkpoint.json.

Yao, Takada and Kitamura, Langmuir 1998, 14, 595–601, DOI 10.1021/la970480g: all seven supplied main pages read and visually reviewed. Corrected malformed legacy title and 1989 year from the actual paper. Both local main copies are identical, SHA256 6a7fb66fb56f6daa4aa677c91ddf0d78aa733b165b7537bbac4c4e1327defb06. Generation 2 bundle remained unchanged in the final post-publication fingerprint at {p['source_fingerprint_at']}. Matching SI not located or verified; closure is supplied-main only.

11 records comprise two CdS/Chelex100 synthesis routes, seven upstream/workup/characterization procedures and two contextual observation records. Retained 47 operations, 61 measurement entries, all 144 source units through 100 reader items, nine original figures, three numbered equations, four source excerpts, and all 33 references/notes. All 47 apparatus states, 31 chemical material bindings, 11 new chemical identities/cards and four reused identities were independently checked. Nonphysical model contexts have no product-image binding. No verified local cubic CdS reference exists, so the author-assigned zinc-blende phase is reported without invented CIF, atomistic interface, diffraction curve, SAED or Raman data.

Preserved source distinctions: wet host size versus CdS size and regional depths; TEM distributions versus XRD line-broadening estimates; nominal 0.5 M NaCl pretreatment versus unresolved post-addition concentration; two-hour stirring plus two-day standing versus the 48-hour optical clock; the unitless-as-printed 0.4 lognormal spread; −26 meV printed potential conflict; optical proxy-derived HS− diffusivity versus cited Chelex100 Na+ diffusivity. Diagnostic hydrosulfide acts on a separate supernatant aliquot. Observed wash-eluent pH is not a stop criterion. Lamp power is a hardware rating. Author models, cited inputs and curator outlook remain distinct from measured samples.

Record schema 1.2.0 adds an optional intended host. Actual task exports retain host context and separate electrolyte process materials. Only two precursor-selection and two partial-protocol examples were added; no new size-conditioned, exact-structure, success or optical-outcome labels. Dataset totals: 233 records = 50 routes + 12 controls + 56 procedures + 15 observations + 100 benchmark rows; 20 hubs = 15 direct synthesis systems + 5 component hubs; 16 source groups. Six formal main-only reviews cover 47 pages; five matched-main/SI reviews cover 74 pages separately. Training totals: 50 precursor-selection, 66 partial-protocol, 6 size-conditioned, 0 exact-structure, 0 success and 95 optical-outcome examples. These are task entries, not independent experiments.

Independent canonical, source, chemical, apparatus, crop and reader audits passed; exact scopes and hashes are private. Browser checks covered periodic-table discovery, both material pages, method switching, stock composition, molecular controls, source-specific scenes, all 16 original image loads, evidence search and mobile layout. Fixed the default figure associations (8/9 figures for sample a, 5/9 for sample b), reader model-context labels, and qualitative room-temperature display. Final checks passed for 247 pages, 233 canonical/public hashes and 19,767 quality checks. No remaining scientific findings; absent SI remains a source limitation.

At 10:05:24Z, the combined queue held 13,103 document copies (5,730 incoming + 7,373 legacy), 8,850 groups and 8,844 provisional review units. These remain indexing/worklist counts, not verified unique-paper/material/recipe totals. All five current-paper milestones are complete. Continue oldest eligible local arrival through the existing five-minute heartbeat, backlog first, local-only, one paper through publication before the next. Chatbot, DFT and theory-comparison features remain deferred. Polymer-host, source-context and figure-filter lessons are saved in the project skill and synchronized to the installed skill.

'''
memory=M/'MEMORY.md';old=memory.read_text(encoding='utf-8')
if not old.startswith(entry.splitlines()[0]):memory.write_text(entry+old,encoding='utf-8')
print('Saved published review closure and MatterSyn memory.')
