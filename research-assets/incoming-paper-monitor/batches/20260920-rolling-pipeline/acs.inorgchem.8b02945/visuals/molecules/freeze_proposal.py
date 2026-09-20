"""Freeze a reviewable molecular proposal, not canonical approval."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent;F=O.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n','utf8')
assert not (O/'package-freeze.json').exists()
now=datetime.now(timezone.utc).isoformat()
save(O/'author-visual-review.json',{
 'author':'/root','at':now,'scope':'Private chemical-identity and stock proposal. No browser or integrated-record validation claimed.',
 'actually_inspected':['All eight contact sheets containing 39 identity and five stock layouts before final text/quantity refinements.','Final benzylmagnesium stock at full size after ASCII superscript minus correction; charge and CH2 hydrogens visible.','Final representative MSC injection stock at full size: 20.0 mg, 1.21e-3 mmol and 1 mL remain distinct from 20 mL reaction.'],
 'reference_work':'Eight primary PubChem identity records fetched as structured chemical metadata, not research papers. Existing reference geometries retained where suitable; new conformers use recorded RDKit ETKDG/MMFF or UFF methods.',
 'source_pages_root_visually_read':['main2','main3','main4','main5','main6','main7','si1','si2','si8','si9'],
 'source_scope_qualification':'Root presentation reading is partial. The independent source auditor, not this note, owns the complete 33-page comparison.',
 'source_distinctions':['Prior cluster structure is cited; no exact current product coordinates supplied.','TEM 2.6±0.5 nm has unspecified uncertainty statistic; FFT is not SAED.','NMR isotope positions, cluster/free ligand identities, coolant and reagent CO2, inert gas and coolant N2 remain separate.','Concentration variants must not inherit the representative 20 mg cluster charge.'],
 'remaining_gates':['Separate scientific molecular audit including all 3D models and display indices.','Bind canonical material and stock slots only after canonical version review.','Do not bind representative MSC stock figure to varied-concentration stock without a separate scoped illustration.','Actual integrated browser controls and responsive checks remain pending.'],
 'independent_approval':False,'eligible_training':False})
files={str(p.relative_to(O)):sha(p) for p in sorted(O.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
save(O/'package-freeze.json',{'schema':'mattersyn-molecular-proposal/1','source_id':'friedfeld2019','author':'/root','created_at':now,'status':'immutable_author_proposal_pending_independent_audit','bound_files':files,'counts':{'identities':39,'graphs2d':30,'models3d':21,'symbolic_identities':9,'stock_definitions':5},'source_revision_freeze':{'path':str(F/'source-extraction-revision-2/package-freeze.json'),'sha256':sha(F/'source-extraction-revision-2/package-freeze.json')},'source_base_freeze':{'path':str(F/'package-freeze.json'),'sha256':sha(F/'package-freeze.json')},'canonical_bindings':'pending','atomic_product_model':False,'eligible_training':False})
print(json.dumps({'sha256':sha(O/'package-freeze.json'),'bound_files':len(files),'independent_approval':False}))
