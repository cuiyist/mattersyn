"""Freeze the private Evans molecular proposal after author checks."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent;B=O.parents[1];C=B/'canonical-proposal/v3'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (O/'package-freeze.json').exists()
reg=read(O/'registry-additions.json');cm=read(C/'record-manifest.json')
assert read(O/'author-validation.json')['status'].startswith('passed')
assert read(O/'viewer-contract-author-check.json')['status'].startswith('passed')
assert read(O/'author-visual-inspection.json')['actual_visual_check'] is True
notes='''# Evans 2010 — private chemical reference proposal

This package supplies all 123 material slots and 41 components in 13 stock slots across the 32 audited canonical v3 records. Fifty source-scoped entries comprise 32 two-dimensional connectivity graphs, one source crystallographic molecular model, and 17 symbolic material, mixture or mechanistic identities. All binding approval flags remain false pending a distinct independent visual and binding audit.

Nine identity uses retain exact cached named connectivity (including two distinct toluene contexts and the oleic-acid compound-2 context). Their existing 3D conformers are not promoted. Newly generated 2D layouts make the named phosphorus/selenium functionality visible, retaining secondary-phosphine P–H and eight explicit deuterium sites in toluene-d8. Abbreviated compounds 3, 5 and 8 retain the source's R=C17H33 convention. Commercial TOP and unidentified impurities remain explicit mixture/symbol cards; metal oleates do not acquire an invented coordination shell.

Molecular species 9 is the sole 3D model: all 51 original atom sites are transformed from the source CIF's fractional coordinates using its triclinic cell. Twenty hydrogens retain their calculated riding-model status. The 56 source geometry-table connections within the asymmetric-unit molecular model use visual sticks without assigning bond order; symmetry-related contacts remain in the transform report. A separate metric-tensor replay checks every one of 1,275 interatomic distances. This is C24H20P2PbSe4 / Pb(Se2PPh2)2, not an atomic model of a PbSe or CdSe quantum dot. No force-field relaxation, inferred dopant site or exact QD structure–recipe pair is created.

The author opened all seven final contact sheets covering every preview and native high-risk previews. A static SVG framing issue and the viewing projection of species 9 were improved before freezing; source connectivity and coordinate values were not changed by those presentation fixes. The existing viewer's pure lookup/override function passed 905 checks on actual entries, material slots and stock components. This is not a mounted-browser or mouse-interaction test.

Canonical v2 was the initial authoring input. Its later independent audit corrected only the distillation residual-pot flow. The original molecular bindings are preserved under binding-history/canonical-v2, and the final proposal is rebound to audited canonical v3. Four material slots and two stock slots changed their record hash (ten changes including duplicated binding-note records); no chemical identity, component assignment, caption, SVG or model changed. generation-manifest.json records its earlier generation stage rather than overriding this final boundary.

The public_asset_proposal list is deliberately explicit: only the 50 new SVGs and 33 new model JSONs are candidate interactive assets. Original documents, full-page renders, raw-text caches, cached registry snapshots, and private audit inputs must not be copied as public assets. The registry and binding documents are proposals for controlled integration after audit. Site, shared ledger, original sources and frozen canonical/reader files were not edited.
'''
(O/'README.md').write_text(notes,encoding='utf-8')
public=[]
for e in reg['entries']:
 for k in ['svgPath','model2dPath','model3dPath']:
  if e.get(k):public.append({'registry_id':e['id'],'kind':k,'private_path':str(O/e[k]),'registry_relative_path':e[k],'sha256':sha(O/e[k])})
assert len(public)==83
save(O/'public-asset-proposal.json',{'status':'private_candidates_pending_independent_audit','assets':public,'asset_count':83,'registry_proposal':'registry-additions.json','material_stock_binding_proposal':'bindings-proposal.json','original_documents_in_public_proposal':False,'whole_page_or_full_text_assets':False})
inputs=[B/'proposal-freeze-v3.json',C/'record-manifest.json',B/'source-extraction-revision-2/source-extraction-freeze.json',B/'source-extraction-revision-2/source-facts.json',B/'source-inventory.json',B/'source-scientific-audit.json',B/'cif-source-inventory.json',B/'proposal-independent-audit/independent-audit-v3.json',Path(r'[local path redacted]')]
inputs += [Path(r['path']) for r in cm['records']]
inputs += [B/'reader-assets/selected-originals'/(name+'.png') for name in ['scheme-1','table-1','figure-S1','figure-S2','figure-S3','figure-S12','figure-S13']]
bound=[{'path':str(p),'sha256':sha(p),'role':'read_only_input'} for p in inputs]
outputs=sorted(p for p in O.rglob('*') if p.is_file() and p.name!='package-freeze.json' and '__pycache__' not in p.parts)
bound += [{'path':str(p),'sha256':sha(p),'role':'private_author_output_or_retained_reference'} for p in outputs]
save(O/'package-freeze.json',{'schema':'mattersyn-private-molecular-proposal/1','source_id':'evans2010','author':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'status':'author_validated_frozen_for_distinct_independent_audit','counts':read(O/'generation-manifest.json')['counts'],'symbolic_entries':17,'named_cached_connectivity_uses':9,'new_2d_connectivity_entries':23,'source_molecular_3d_entries':1,'canonical_version':3,'canonical_manifest_sha256':sha(C/'record-manifest.json'),'source_audit_sha256':sha(B/'source-scientific-audit.json'),'canonical_reader_independent_audit_sha256':sha(B/'proposal-independent-audit/independent-audit-v3.json'),'registry_sha256':sha(O/'registry-additions.json'),'bindings_sha256':sha(O/'bindings-proposal.json'),'author_validation_sha256':sha(O/'author-validation.json'),'viewer_contract_check_sha256':sha(O/'viewer-contract-author-check.json'),'actual_author_visual_review':True,'author_consistency_checks':read(O/'author-validation.json')['checks'],'pure_viewer_function_checks':905,'public_asset_proposal_count':83,'bound_files':bound,'independent_audit':'pending','binding_approved':False,'mounted_browser_test':'not_performed','published':False,'training_eligible':False,'exact_qd_structure_recipe_pairs':0})
print(json.dumps({'freeze':sha(O/'package-freeze.json'),'bound_files':len(bound),'registry':sha(O/'registry-additions.json'),'bindings':sha(O/'bindings-proposal.json'),'public_assets':83}))
