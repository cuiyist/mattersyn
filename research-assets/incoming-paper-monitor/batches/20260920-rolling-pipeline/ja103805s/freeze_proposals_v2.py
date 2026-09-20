"""Contract replay in an isolated private projection; never change Site or originals."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib,shutil,sys
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent;C=B/'canonical-proposal/v2';R=B/'public-review-proposal/v2';T=B/'proposal-contract-check/v2'
S=Path(r'[local path redacted]')
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cm=read(C/'record-manifest.json');rm=read(R/'reader-manifest.json');review=read(R/'evans2010.json');bindings=read(R/'reader-bindings-proposal.json');cov=read(C/'source-to-field-coverage.json')
bound={str(p):sha(p) for p in [B/'source-extraction-freeze.json',B/'source-facts.json',B/'source-inventory.json',B/'source-extraction-revision-2/source-extraction-freeze.json',B/'source-extraction-revision-2/source-facts.json',B/'source-scientific-audit.json',B/'build_canonical_proposal_v2.py',B/'build_reader_proposal_v2.py',Path(__file__),S/'scripts/build_paper_reviews.py',S/'scripts/dataset_lib.py',S/'scripts/schema_definition.py',S/'dist/source-evidence.mjs']}
for p in list(C.glob('*.json'))+list(R.glob('*.json')):bound[str(p)]=sha(p)
for x in bindings['original_assets']:bound[x['private_path']]=x['sha256']
for x in cm['records']:
 p=T/'data/records'/Path(x['path']).name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(x['path'],p)
for x in bindings['original_assets']:
 p=T/'dist'/x['public_asset'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(x['private_path'],p)
sys.path.insert(0,str(S/'scripts'))
import build_paper_reviews
from dataset_lib import validate_record,eligibility,build_groups
build_paper_reviews.ROOT=T
errors=build_paper_reviews.validate(review)
records=[read(x['path']) for x in cm['records']]
for r in records:errors+=validate_record(r)
assert not errors,errors
assert len(set(build_groups(records).values()))==1
assert all(not a['eligible'] for r in records for a in eligibility(r).values())
checks=0
for p,h in bound.items():assert sha(p)==h;checks+=1
old=read(B/'canonical-proposal/v1/record-manifest.json')
for x in old['records']:assert sha(x['path'])==x['sha256'];checks+=1
for n,h in read(B/'public-review-proposal/v1/reader-manifest.json')['outputs'].items():assert sha(B/'public-review-proposal/v1'/n)==h;checks+=1
# A source correction and fourteen lossless table/equation containers account
# for the v2 scientific deltas. Reagent recipes/numbers and specimen bounds stay.
scientific_deltas=[]
oldrec={x['record_id']:read(x['path']) for x in old['records']}
for r in records:
 prev=deepcopy(oldrec[r['record_id']]);now=deepcopy(r)
 for a in [prev,now]:
  a['sources'][0]['main_status']='SOURCE_REVIEW_STATUS';a['sources'][0]['si_status']='SOURCE_REVIEW_STATUS';a['quality']['missing_fields'][0]='SOURCE_REVIEW_STATUS'
 additions=[m for m in now['measurements'] if m['id'].startswith('inventory-tables-') or m['id'].startswith('inventory-equations-')]
 now['measurements']=[m for m in now['measurements'] if m not in additions]
 if r['record_id']=='evans-2010-molecular9-structure':
  target=next(m for m in now['measurements'] if m['id']=='evans2010-cif-diffrn-measured-fraction-theta-max-diffrn-measured-fraction-theta-max');assert target['value']['unit']=='dimensionless';target['value']['unit']='deg'
 assert prev==now,r['record_id'];checks+=1
 if additions:scientific_deltas.append({'record_id':r['record_id'],'added_lossless_inventory_measurement_ids':[m['id'] for m in additions]})
report={'status':'passed_current_reader_and_canonical_contract_replay','errors':errors,'additional_checks':checks,'scope':'Read-only current Site validators executed against a private 32-record/25-crop projection; no mounted browser or independent scientific audit claimed.','canonical_manifest_sha256':sha(C/'record-manifest.json'),'reader_manifest_sha256':sha(R/'reader-manifest.json'),'preserved_v1':True,'source_revision_2':'Exactly one typed source unit corrected; originals and v1 retained.','v2_proposal_changes_from_v1':['Source-audit status updated to the separately passed revision-2 gate.','One measured-fraction unit corrected through its exact canonical and reader fields.','Four complete curated table containers and ten worked-expression containers added; existing typed quantities are unchanged.','Reader stock-B section classification corrected; no recipe data changed.'],'added_inventory_payloads':scientific_deltas,'site_validator_path':str(S/'scripts/build_paper_reviews.py'),'site_validator_sha256':sha(S/'scripts/build_paper_reviews.py'),'independent_canonical_reader_audit':'pending','molecules_apparatus_products_browser_publication':'pending','training_rows':0,'exact_qd_structure_pairs':0}
save(B/'proposal-contract-check-v2.json',report)
notes='''# Evans 2010 — private canonical and reader proposal, revision 2

The source scientific audit passed revision 2. The original extraction is preserved; one CIF measured-fraction unit was corrected from degrees to dimensionless without changing any numeric value or original file.

The canonical proposal contains 32 records: three QD/MSC route families, thirteen supporting preparation/control families and sixteen observation contexts. These are not 32 independent synthesis experiments. The 46 operations preserve precursor preparation, distinct stock formulations, A/B/C alternatives, negative controls, retained fractions and explicit inheritance. All records remain imported_unreviewed with no requested training task.

The source-to-field map covers 457 facts through 3,621 typed bindings and all 198 source units. The supplied molecular species-9 CIF is represented as its own refinement context, including all 2,896 original loop-cell values. It is not a CdSe/PbSe QD atomic structure. The private lossless source map retains all raw tokens, line metadata and original curated objects.

The reader has five academic sections plus sources, 336 evidence items, 4,516 exact canonical fields, four curated tables and ten worked equations. Only the 25 selected original figure/table/scheme/calculation crops are proposed public assets. No original PDF/CIF, whole-page raster or full-text cache is included in the proposed public asset set. Route evidence contains real record-ID arrays; characterization contains resolvable reader-item IDs.

Source conflicts C1–C9, unreported conditions and specimen joins remain explicit. In particular: the TIPPSe and Pb-oleate mass/amount conflicts remain unreconciled; B is not a distillation cut; the Pb QD stock solvent is missing; Cd ratio and time-course samples are not equated; S16 bars are 5 and 50 nm, not particle sizes; the representative conversion calculation is not joined to the S19 recipe; the molecular-9 ratio threshold and printed conversion exponent conflicts remain.

Current Site schema and reader validators passed in a private projection. No mounted-browser, molecular, apparatus, crystal-asset, independent canonical/reader, training or publication approval is claimed. Those gates remain pending. No Site, shared queue, memory or original-source file was modified.
'''
(B/'proposal-notes-v2.md').write_text(notes,encoding='utf-8')
for p in [B/'proposal-contract-check-v2.json',B/'proposal-notes-v2.md']:bound[str(p)]=sha(p)
save(B/'proposal-freeze-v2.json',{'schema':'mattersyn-private-paper-proposals-freeze/1','source_id':'evans2010','version':2,'author':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'status':'source_audit_passed_canonical_reader_author_proposals_frozen_for_independent_review','canonical_manifest':{'path':str(C/'record-manifest.json'),'sha256':sha(C/'record-manifest.json')},'reader_manifest':{'path':str(R/'reader-manifest.json'),'sha256':sha(R/'reader-manifest.json')},'reader':{'path':str(R/'evans2010.json'),'sha256':sha(R/'evans2010.json')},'bound_files':[{'path':p,'sha256':h} for p,h in bound.items()],'source_audit_sha256':sha(B/'source-scientific-audit.json'),'private_validation_projection':str(T),'published':False,'training_eligible':False})
print('FREEZE',sha(B/'proposal-freeze-v2.json'));print('CONTRACT',sha(B/'proposal-contract-check-v2.json'));print('BOUND_FILES',len(bound))
