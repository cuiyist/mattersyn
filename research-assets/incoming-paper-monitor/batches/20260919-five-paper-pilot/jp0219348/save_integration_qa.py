"""Record performed browser checks; do not manufacture source/audit approvals."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
H=Path(__file__).resolve().parent
M=H.parents[4];S=M/'recipe-atlas';O=H/'site-integration-proposal'
assert S.is_dir()
now=datetime.now(timezone.utc).isoformat()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
qa={'schema':'mattersyn.browser-validation/1','at':now,'reviewer':'root','status':'passed','mechanism':'Codex in-app browser via cua_repl; actual controls exercised','local_origin':'http://127.0.0.1:5192',
 'checks':[
  'All 14 private apparatus scenes visually inspected; all 14 mobile scene layouts checked after label/viewBox repair.',
  'Integrated synthesis route: all 9 stage buttons exercised; source-specific conditions, diagram identities and enlargement checked; context links are 9 real record IDs.',
  'Integrated material hub has one synthesis method; unit-cell and repeated-cell controls work (680 and 5440 visible site markers).',
  'Private average-model preview layer control changed 680 to 648 markers and back; partial-occupancy caveats retained.',
  'Integrated XPS acquisition page has no crystal canvas; its analytical specimen does not inherit the average diffraction model.',
  'Integrated main/SI reader: lazy reflection-table load, unresolved-sign filter (2), negative filter (137), zero filter (1), all rows (1209), final hkl (5,27,29), and SI page 14 (49 rows) checked.',
  'SI unresolved rows retain signed null, both sign candidates, clear magnitude and source locator.',
  '390x844 mobile SI view has no page-level horizontal overflow; the wide reflection table scrolls in its own container.',
  'No browser error logs observed on integrated route, material, source reader or XPS page; viewport override reset.'
 ],'limitations':['Browser checks verify rendering and controls; independent scientific audit files certify their stated source scopes.','No published-site verification claimed here.'],
 'repairs_before_pass':['Empty chemical-binding maps and source-record hashes added for six context-only records; no new chemical assignments.','Route visibility separated from training-task eligibility with optional reader_role; all 470 previous record hashes and classifications preserved.','route_evidence_contexts normalized to record-ID array; narrative scope retained separately.']}
save(O/'browser-validation.json',qa)
p=S/'data/paper-reviews/heo2003.json';r=json.loads(p.read_text(encoding='utf8'))
r['presentation_gates']['browser_render']=True
save(p,r)
imp=json.loads((O/'site-import-manifest.json').read_text(encoding='utf8'))
imp.update(status='integrated_build_and_browser_passed_publication_pending',browser_validation_sha256=hashlib.sha256((O/'browser-validation.json').read_bytes()).hexdigest(),browser_checked_at=now)
save(O/'site-import-manifest.json',imp)
entry=f'''## 2026-09-20 — Heo full main/SI contribution integrated and audited; deployment pending

Saved {now}. Heo et al. (2003), DOI10.1021/jp0219348, has complete supplied9-page main/14-page SI coverage and separate passed scientific, canonical, molecular-binding, apparatus, product/SI, promotion/projection and code-delta audits. The local candidate is dataset0.24.0:480records,98route/variant records,44material hubs(33direct+11component),32sourcegroups and27formalreaders. Its10newrecords mean one synthesis route, three acquisition procedures and six analytical contexts, not ten experiments. All470previous records and all training eligibility counts are unchanged; exact structure–recipe pairs remain0. Actual local browser checks passed and are saved in jp0219348/site-integration-proposal/browser-validation.json. Deployment and claim closure remain pending until anonymous verification.

Heo includes14operation-specific diagrams,14materialslots/one stock,16selected scientific crops,7figures/5tables,473measurements and all1209SIreflectionrows. Two printed signs stay unresolved (signed null with both candidates);137negative observations and one zero are retained. The rotatable680-site/5440-site average position/occupancy model and curator-derived CIF are qualified average structures, not ordered nanoclusters or DFT-ready microstates. Nominal Si100Al92 differs from mixed-site Si96Al96; prose/Table1 condition conflicts and unresolved angle/ADP issues remain explicit. No false exact training pair was added. Whole-page scans and original paper/SI binaries remain local.

Screen-first, evidence-priority parallel workflow remains active with separate audits and batch publication. Evans2010 DOI10.1021/ja103805s has all24main/SI pages read/viewed,198sourceunits and457typedfacts frozen; independent scientific audit and private canonical/reader drafting continue. Its CIF is molecular compound9, not quantum-dot coordinates. A measured-fraction unit correction is being preserved as a separate revision. Raw complete-source-payloads.json is explicitly excluded by public_projection_policy2026-09-20.2. No paid API run or new paper download has started. Continue from the frozen packages rather than repeating completed reviews.

'''
p=M/'MEMORY.md';p.write_text(entry+p.read_text(encoding='utf8'),encoding='utf8')
print('Saved actual browser QA, reader gate and memory; publication remains pending.')
