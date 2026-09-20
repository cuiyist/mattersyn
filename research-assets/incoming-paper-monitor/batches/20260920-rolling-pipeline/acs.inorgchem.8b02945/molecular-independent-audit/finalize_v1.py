from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent;F=O.parent;P=F/'visuals/molecules'
J=lambda p:json.loads(Path(p).read_text('utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (O/'independent-audit-v1.json').exists()
a=J(O/'molecular-checks-v1.json');b=J(O/'reference-provenance-checks-v1.json')
bound={**a['bound_files'],**b['bound_files']}
for p in sorted(O.glob('*')):
 if p.is_file():bound[str(p)]=sha(p)
for path,h in bound.items():assert sha(path)==h,path
findings=[
 {'id':'FMOL-01','severity':'required','status':'open','scope':['models/friedfeld2019-nitrogen-3d.json','models/friedfeld2019-liquid-nitrogen-3d.json'],'finding':'Both cached N2 models have N≡N distance 1.460 Å. A broad generic bond screen does not qualify this geometry.','correction':'Use the already retained Gu/NIST ground-state N2 reference (r_e 1.09768 Å), with provenance and distinct gas/coolant captions, or disable 3D. Preserve the original freeze.','evidence':'Independent coordinates are ±0.73 Å; retained NIST original returned table row and units were reread.'},
 {'id':'FMOL-02','severity':'required','status':'open','scope':['models/friedfeld2019-acetone-3d.json','models/friedfeld2019-acetonitrile-3d.json','models/friedfeld2019-chloroform-d-3d.json','models/friedfeld2019-diethyl-ether-3d.json','models/friedfeld2019-dry-ice-3d.json'],'finding':'Four top-level model source fields point at prior-paper DOIs. Four contextual notes refer to silicon washing, electrospray/pyridine, compound 2e NMR or ester solubility rather than this source.','correction':'Keep exact historical reuse metadata separately; source-neutralize current source fields and use Friedfeld-specific current role notes. Geometry and graph arrays should be identical.','discovery':'Auditor found prior DOI fields; author separately alerted the auditor to four stale notes, then the auditor opened and verified all current model notes.'},
 {'id':'FMOL-03','severity':'required','status':'open','scope':['stock-svg/friedfeld2019-indium-myristate-additive.svg'],'finding':'The full stock salt graph renders In3+ and the carboxylate labels too small at native 1100-pixel width.','correction':'Use the readable In3+ plus three ligand-component presentation already used for this identity card, with unchanged stock quantities and disconnected-component scope.','evidence':'Viewed full native stock preview in addition to contact sheet.'},
 {'id':'FMOL-04','severity':'required','status':'open','scope':['models/friedfeld2019-benzene-d6-2d.json','models/friedfeld2019-benzene-d6-3d.json','reference-qualification.json'],'finding':'CID 241 is unlabeled benzene C6H6 in the retained primary metadata, while the displayed graph correctly contains six deuterium atoms. The current provenance does not explicitly distinguish parent CID from isotopologue identity.','correction':'Label CID 241 as parent-connectivity reference, and six-D substitution as source-defined. Preserve all six-D graph/coordinate data.','evidence':'Retained PubChem response and independent graph/isotope checks agree on the parent-versus-derived distinction.'}
]
manual=[
 'Read all 39 registry captions, source-specific limitations, formulas and locators against the independently passed source-v2 materials.',
 'Viewed all eight final frozen contacts, encompassing every one of the 39 identity previews and five stock previews; reopened the indium-myristate stock at native size.',
 'Viewed all 21 conformers in independently generated x/y and x/z coordinate projections (four sheets); projections are audit diagnostics, not new scientific models.',
 'Read every model source, sourceType, method, generation and notes field; scoped historical-context findings explicitly.',
 'Checked carboxylic acids versus formal carboxylates, Grignard ionic fragments, In3+ salts, hydride/sulfate formal components, and no invented metal coordination.',
 'Checked carbonyl 13C positions, reactive 13CO2 versus dry ice, benzene-d6/toluene-d8/CDCl3 isotopes and unspecified 2-MeTHF stereochemistry.',
 'Checked representative MSC 20.0 mg / 0.00121 mmol and 1 mL charged solvent separately from the 20 mL reaction; current proposal is not valid for msc-injection-varied without a separate illustration.',
 'Checked all five stock solute/solvent pairs and ten component mappings; transferred volume is not final stock volume, and additive stock concentration remains unknown.',
 'Read retained NIST returned ground-state row, isotope header and angstrom unit; no new external lookup performed.'
]
r={'schema':'mattersyn-independent-molecular-audit/1','author':'/root','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'revision_required','independent_approval':False,'review_scope':'Source-qualified reference molecules and stock diagrams only; no canonical binding, browser, product-model or training approval.','source_id':'friedfeld2019','source_revision':2,'source_audit_sha256':sha(F/'source-independent-audit/independent-audit-v2.json'),'package_freeze':{'path':str(P/'package-freeze.json'),'sha256':sha(P/'package-freeze.json')},'counts':{'identities':39,'graphs_2d':30,'models_3d':21,'symbolic_identities':9,'stock_definitions':5,'stock_components':10,'original_preview_panels_viewed':44,'conformer_projections_viewed':42},'executed_checks':len(a['checks'])+len(b['checks']),'passed_checks':a['passed']+b['passed'],'failed_checks':a['failed']+b['failed'],'findings':findings,'actual_manual_scope':manual,'checks_are_not_manual_read_count':True,'canonical_material_bindings':'not included and not audited','remaining_gates':['Resolve four bounded finding categories in an immutable overlay and independently recheck.','Qualify exact future canonical material and stock bindings, including varied MSC injection.','Actual integrated browser controls and responsive layouts remain separate.'],'bound_files':bound}
(O/'independent-audit-v1.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
md='''# Friedfeld molecular proposal: revision required

Author: `/root`. Independent reviewer: `/root/backlog_eta`.

The frozen proposal was reviewed against independently passed source revision 2. All 39 identities, 30 connectivity models, 21 illustrative/reference conformers and five stock definitions were checked. All 44 original preview panels and 42 orthogonal conformer projections were actually viewed. Of 5,796 executed checks, 5,794 passed; the two failures identify the same N2 geometry issue.

Four bounded correction categories remain:

1. Replace or withhold both 1.460 Å N2 geometries. The retained qualified NIST reference is 1.09768 Å; gas and coolant scopes must remain distinct.
2. Separate historical reuse metadata from current model source fields and replace four unrelated contextual notes. Do not change the valid graph/coordinate arrays.
3. Enlarge the In3+ and carboxylate labels on the indium-myristate stock diagram using readable formal components.
4. Identify PubChem CID 241 as the unlabeled benzene parent reference for source-defined benzene-d6, not the isotopologue's identity CID.

No source quantity, formula, isotope-position, salt-connectivity or stock-component mismatch was found. All 44 preview rasters exactly reproduce the frozen SVG bytes. Six retained raw PubChem SDFs and the recorded newly generated conformers were independently compared; eight primary connectivity records were checked.

The original package remains unchanged. This review does not approve canonical slot bindings, integration/browser behavior, product atomic models or training tasks. In particular, the representative 20 mg MSC stock figure must not be bound to varied-concentration stocks.
'''
(O/'independent-audit-v1.md').write_text(md,'utf8')
print(json.dumps({'audit':str(O/'independent-audit-v1.json'),'sha256':sha(O/'independent-audit-v1.json'),'bound_files':len(bound),'findings':len(findings)}))
