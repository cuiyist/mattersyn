"""Verify independent handoff hashes and save the exact still-incomplete scope."""
import json,hashlib
from pathlib import Path

BASE=Path(__file__).resolve().parent
PROJECT=BASE.parents[3]
SITE=PROJECT/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

coverage=read(BASE/'coverage-ledger.json')
assert coverage['source_extraction_sha256']==sha(BASE/'source-extraction.json')
assert coverage['reader_evidence_sha256']==sha(BASE/'reader-evidence.json')
assert coverage['reader_spec_sha256']==sha(BASE/'reader-integration-spec.json')
assert coverage['counts']['unassigned_leaves']==coverage['counts']['multiply_assigned_leaves']==0
scope=read(BASE/'reader-assets/review-scope-audit.json')
assert scope['status']=='passed_in_bounded_scope' and not scope['must_fix']
for relative,expected in scope['reviewed_source_hashes'].items():
    assert sha(SITE/relative)==expected,relative
assert sha(BASE/'reader-assets/aerosol-protocol.mjs')==sha(SITE/'dist/aerosol-protocol.mjs')
chemical=read(BASE/'molecular-assets/validation-report.json')
assert chemical['status']=='passed' and not chemical['errors']
for filename,key in [('registry-additions.json','registryAdditionsSha256'),('bindings-additions.json','bindingsAdditionsSha256'),('source-catalog.json','sourceCatalogSha256')]:
    assert sha(BASE/'molecular-assets'/filename)==chemical[key]

v=read(BASE/'reader-preparation-validation.json')
v['independent_review_scope_audit']='passed_in_bounded_scope; five frontend DOM/text fixtures, not real browser layout'
v['independent_handoff_hashes_verified']=True
v['source_item_reconciliation']=coverage['counts']
write(BASE/'reader-preparation-validation.json',v)
c=read(BASE/'checkpoint.json')
c['staged_item_coverage']=coverage['counts']
c['source_item_coverage_status']='All staged source items accounted for privately. Reader prose/import and source-to-render validation remain pending; no claim of full public coverage.'
for item in c['current_work_items']:
    if item['label']=='Evidence coverage and reader context':
        item['status']='private item reconciliation complete; reader import pending'
        item['scope']='164 staged units / 1,235 leaves accounted for exactly once; 171 reader items, 12 figures, Table I, 9 conflicts and 12 reference contexts. This is staged-source coverage, not a rendered-site audit.'
    if item['label']=='Review scope and publication counts':
        item['status']='implemented locally and independently checked'
        item['scope']='Five regression tests, five frontend DOM/text fixture checks and existing builds/links/counts pass. Audit hashes verified by root. Real Littau source joins and browser layout remain pending.'
c['next_action']=c['next_action'].replace('finish reader-evidence and coverage-ledger handoff, then','use the completed reader-evidence and coverage-ledger handoff to')
write(BASE/'checkpoint.json',c)
m=read(BASE/'milestones.json')
for stage,filename in [('extract','coverage-ledger.json'),('extract','reader-evidence.json'),('audit','coverage-ledger.json'),('audit','reader-assets/review-scope-audit.json')]:
    path=str(BASE/filename)
    if path not in m[stage]['evidence']:m[stage]['evidence'].append(path)
m['extract']['note']+=' Private staged-item reconciliation now accounts for164units/1,235leaves with171reader items; root hash checks passed. Reader prose/import and source-to-view coverage remain unfinished.'
m['audit']['note']+=' Explicit source-scope implementation independently checked with fixture DOM/text and unchanged audit hashes; whole generated Littau contribution and browser checks remain pending.'
write(BASE/'milestones.json',m)

notes='''
Final preparation handoff: all three asset/coverage subtasks have finished; do not report them as still running. `coverage-ledger.json` accounts for164staged units/1,235leaves exactly once, with171reader items,12figures,TableI,9source conflicts and12reference contexts. This reconciles the staged extraction, not the final website. Root verified evidence/spec hashes and the independent review-scope audit's11implementation hashes. That bounded audit found no must-fix issue and checked five frontend DOM/text fixture pathways; real Littau integration and browser QA remain. No source paper, training record or publication status was promoted.

'''
memory=PROJECT/'MEMORY.md'
t=memory.read_text(encoding='utf-8')
marker='## 2026-09-18 — time estimates are planning ranges'
if notes.strip() not in t:t=t.replace(marker,notes+marker,1)
memory.write_text(t,encoding='utf-8')
n=BASE/'NEXT_ACTION.md'
t=n.read_text(encoding='utf-8')
if 'Final preparation handoff: all three' not in t:t+='\n'+notes
n.write_text(t,encoding='utf-8')
print('Verified handoff hashes; coverage reconciled; integrate/publish remain incomplete.')
