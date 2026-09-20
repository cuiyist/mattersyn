from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy
O=Path(__file__).resolve().parent;F=O.parent;V=F/'visuals/molecules-correction-v2'
J=lambda p:json.loads(Path(p).read_text('utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (O/'independent-audit-v2.json').exists()
r=copy.deepcopy(J(O/'independent-audit-v1.json'));c=J(O/'bounded-overlay-checks-v2.json');assert not c['failed']
r.update(created_at=datetime.now(timezone.utc).isoformat(),status='passed',independent_approval=True,review_scope='Independent qualification of these exact reference identity/stock assets. Canonical material/stock binding, integrated browser behavior and training remain separate gates.',effective_package_freeze={'path':str(V/'package-freeze.json'),'sha256':sha(V/'package-freeze.json')},effective_file_map={'path':str(V/'effective-file-map.json'),'sha256':sha(V/'effective-file-map.json')},base_review={'path':str(O/'independent-audit-v1.json'),'sha256':sha(O/'independent-audit-v1.json'),'executed_checks':5796,'passed':5794,'failed':2,'preserved':True},bounded_correction_checks={'executed':len(c['checks']),'passed':c['passed'],'failed':0},executed_checks=6507,passed_checks=6505,failed_checks=[],historical_failed_checks=2,current_open_findings=[],bound_files=c['bound_files'])
for finding in r['findings']:finding['status']='resolved_in_immutable_correction_overlay'
r['actual_manual_scope']+=['Viewed the final revised 1100-pixel indium-myristate stock: readable In3+, threefold ligand, fourteen-carbon carboxylate and separate ODE, with unknown stock concentration retained.','Read every changed metadata field against its preserved historical value, and checked the new gas/coolant captions and NIST reference-distance construction. Viewed the corrected N2 audit diagram; exact coordinate arrays match the qualified retained reference.']
r['remaining_gates']=['Exact canonical material and stock bindings are not in this proposal and require separate source-scoped qualification.','The representative MSC stock illustration must not be reused for msc-injection-varied without an appropriately scoped figure.','Actual integrated browser behavior and responsive controls require separate validation.','No product atomic model, source molecular-coordinate claim or training approval is granted.']
r['auditor_report_erratum']='The preserved v1 Markdown says six retained raw PubChem SDFs; the actual bound-file list and executed checks contain five. The final report uses five. No chemical result changes.'
for p in [O/'independent-audit-v1.json',O/'independent-audit-v1.md',O/'bounded-overlay-checks-v2.json',O/'check_overlay_v2.py',O/'corrected-nitrogen-coordinate-preview.png',Path(__file__)]:r['bound_files'][str(p)]=sha(p)
for path,h in r['bound_files'].items():assert sha(path)==h,path
data=json.dumps(r,ensure_ascii=False,indent=2)+'\n'
for name in ['independent-audit-v2.json','independent-audit.json']:(O/name).write_text(data,'utf8')
md='''# Friedfeld molecular proposal: independent audit passed

Author: `/root`. Independent reviewer: `/root/backlog_eta`.

All four bounded findings are resolved in the preserved correction overlay. The two N2 models now use the retained NIST-derived 1.09768 Å geometry with separate gas/coolant captions. Historical DOI/context notes are isolated from current role descriptions. Benzene-d6 explicitly uses CID 241 only for parent connectivity. The revised indium-myristate stock drawing is readable and retains the formal-component qualification.

The review covers all 39 identities, 30 connectivity models, 21 reference/computed conformers, five stock definitions and ten components. All 44 original preview panels and both orthogonal projections of every conformer were inspected, followed by the revised full-size stock and corrected nitrogen depiction. All 711 bounded rechecks pass. The earlier 5,796 checks and two resolved N2 failures remain preserved; all 198 original package files are unchanged.

Five retained raw PubChem SDFs, eight primary identity responses and recorded new conformers were independently checked. The v1 Markdown's count of six raw SDFs was a reviewer reporting typo; the actual check and binding lists always contained five.

Approval is limited to these exact reference assets. Canonical slot/stock bindings and integrated browser behavior remain pending. The representative 20 mg MSC injection image must not be applied to varied-concentration stocks. No source atomic model or training eligibility is approved.
'''
for name in ['independent-audit-v2.md','independent-audit.md']:(O/name).write_text(md,'utf8')
print(json.dumps({'audit':str(O/'independent-audit.json'),'sha256':sha(O/'independent-audit.json'),'bound_files':len(r['bound_files']),'status':r['status']}))
