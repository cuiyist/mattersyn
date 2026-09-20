"""Save closure only after the native deployment proof exists and succeeded."""
from pathlib import Path
from datetime import datetime, timezone
import json

B = Path(__file__).resolve().parent
M = B.parents[3]
def read(p):
    return json.loads(p.read_text(encoding='utf-8'))
def write(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

p = read(B/'publication-checkpoint.json')
assert p['deployment_status'] == 'succeeded' and p['public_live_version'] == 16
assert p['source_commit'] == 'e69ee9bd8621f8bce9c2da39318cc00af54e29d7'
groups = {
 'read': ['source-manifest.json','source-identity.json','source-audit.json'],
 'extract': ['canonical-records-audit.json','public-review-proposal/source-item-coverage.json','crop-assets/manifest.json'],
 'audit': ['canonical-records-audit.json','reader-context-audit.json','molecular-source-audit.json','apparatus-source-audit.json','reader-assets/canonical-to-reader-audit.json'],
 'integrate': ['build-validation.json','schema-regression-tests.json','browser-qa.json','reader-assets/canonical-to-reader-audit.json','reader-assets/final-presentation-check.json'],
 'publish': ['publication-checkpoint.json']
}
milestones = {}
for stage, paths in groups.items():
    for path in paths:
        assert (B/path).is_file(), path
    milestones[stage] = {'status':'complete','evidence':[str(B/x) for x in paths], 'note':'Completed and published supplied-main scope: all six pages reviewed. Matching SI not located or verified; no SI-absence or full-corpus-completion claim.'}
write(B/'milestones.json', milestones)
c = read(B/'checkpoint.json')
c.update(checkpoint_at=datetime.now(timezone.utc).isoformat(), website_published=True, source_generation=2,
 public_live_version=16, dataset_version='0.9.0', publication_checkpoint=str(B/'publication-checkpoint.json'),
 source_commit=p['source_commit'], public_url=p['public_url'],
 current_work_items=[{'label':stage.capitalize(),'status':'complete','scope':value['note']} for stage,value in milestones.items()],
 next_action='Current paper closed for supplied-main scope. Continue oldest eligible existing local paper. Reopen this source if matching new or changed SI arrives. Keep existing MatterSyn website and public audience.')
c.pop('interruption',None)
write(B/'checkpoint.json',c)
entry = '''## 2026-09-19 — Veinot CdS synthesis and surface chemistry published

Published public Site version 16, dataset 0.9.0, commit e69ee9bd8621f8bce9c2da39318cc00af54e29d7 at 2026-09-19T09:16:55.174350+00:00. Same existing MatterSyn Site and public audience. Cd + S periodic-table discovery opens CdS (material?id=cds-fad408), now with QDOH and five surface esterification routes displayed equally; the three prior CdSe/CdS component methods remain. New materials continue to join this atlas, not a separate website. Release proof: research-assets/incoming-paper-monitor/reviews/cm970189m/publication-checkpoint.json.

Veinot, Ginzburg and Pietro (1997), DOI 10.1021/cm970189m: all six supplied main pages read and visually inspected; full source, canonical, reader, molecular and apparatus audits complete. Both local main copies are byte-identical, SHA256 eac4fe78e4bc3ab9c15e0409b69232e4294a0c07787d3ca650c378f6341d4adc. Generation 2 bundle unchanged at final 09:13:22Z fingerprint. Matching SI not located or verified. This closes only the supplied-main scope.

21 records = 6 routes + 1 deliberate control + 11 supporting procedures + 3 contextual observations. 232 measurement entries = 202 quantities + 30 qualitative facts; 133 operations with 41 action types. All 141 source units mapped to 101 reader items; six figures, three tables, Scheme 1 and the compound-family illustration retained as 11 original assets. All 15 references/notes inventoried. 115 chemical bindings use 47 new identities/cards and eight reused references. All 97 distinct apparatus frames inspected. Canonical, original-source and reader/runtime checks passed; local browser checks covered discovery, method switching, stock quantities, process scenes, molecular controls, surface cards, original TEM, source search and mobile layout. Exact audit scopes remain in the review folder.

Cadmium-acetate mass/mole inconsistency, QDOH optical-edge and capping-estimate conflicts, Table 1 timing/NMR ambiguities, and TEM aggregate/scale context remain explicit. Inherited esterification frameworks do not imply unreported absolute 2b–e charges. NMR conversion is not isolated mass yield. Molecular precursor products retain their organic formulas, and compound-level characterization does not establish individual batch identity. No CdS polymorph, atomistic coordinates, CIF, new exact-structure label, SAED or Raman spectrum was invented. Added typed qualitative facts, intended surface targets and source-neutral shared chemical captions; isotope labels preserve deuterium.

Dataset totals: 222 canonical records = 48 synthesis routes + 12 controls + 49 procedures + 13 observations + 100 benchmark rows; 19 material hubs = 14 direct synthesis systems + 5 component hubs; 15 total source groups. Five formal main-only reviews cover 40 pages; five matched-main/SI reviews cover 74 pages separately. Training exports: 48 precursor-selection, 64 partial-protocol, 6 size-conditioned, 0 exact-structure, 0 success and 95 optical-outcome examples. These are task exports, not independent experimental-run counts. Full-corpus material and recipe totals remain unknown.

At 09:13:06Z, the combined queue held 13,019 document copies (5,646 incoming and 7,373 legacy), 8,790 provisional groups and 8,785 provisional review units. These are indexing/worklist counts, not verified unique papers. All five Veinot milestones complete; continue oldest eligible local source using the existing five-minute heartbeat, retaining local-only review and backlog priority. Deferred chatbot, DFT and theory-comparison features remain deferred. Reusable surface-chemistry and qualitative-data lessons added to project skill and synchronized to the installed skill.

'''
memory = M/'MEMORY.md'
old = memory.read_text(encoding='utf-8')
if not old.startswith(entry.splitlines()[0]):
    memory.write_text(entry+old, encoding='utf-8')
print('Saved completed review milestones and MatterSyn memory.')
