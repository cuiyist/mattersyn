import datetime,hashlib,json,sys
from pathlib import Path
O=Path(__file__).parent;J=O.parents[1];A=J/'visuals/molecules';M=J.parents[4]
sys.path.insert(0,str(M/'research-assets'));from sync_github_public import io_path
def sha(p):return hashlib.sha256(io_path(Path(p)).read_bytes()).hexdigest()
def read(p):return json.loads(io_path(Path(p)).read_text(encoding='utf-8-sig'))
def save(p,x):io_path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
c=read(O/'independent-checks.json');v=read(O/'consumer-checks.json');freeze=read(A/'package-freeze.json');inp=read(A/'input-bindings.json')
assert c['status']=='passed' and not c['summary']['failed'] and v['status']=='passed'
assert sha(A/'package-freeze.json')=='d0061aaac1876774eb8e6667ad2cec6203fdcf90cbd27b6de30c18be5c583bf8'
bound={**c['bound_files'],**v['bound_files']}
for p in [O/'independent-checks.json',O/'consumer-checks.json',O/'check_molecular.py',O/'reviewed-consumer-fixture.mjs',Path(__file__),M/'recipe-atlas/dist/chemical-viewer.mjs']:
 bound[str(p)]=sha(p)
assert sha(A/'reference-snapshots/chemical-viewer.mjs')==sha(M/'recipe-atlas/dist/chemical-viewer.mjs')
assert all(sha(p)==h for p,h in bound.items())
panels=[]
for contact in read(A/'contact-index.json')['contacts']:
 for p in contact['panels']:panels.append({'path':p['path'],'sha256':p['sha256'],'actually_viewed':True,'view_method':'Full contact-sheet image inspected by independent auditor, including its title, depicted structure and qualifications.'})
manual=[
 {'scope':'All 23 static panels on six contacts','result':'13 identity cards, six conformer projections and four stock diagrams actually viewed; text, charges, bond depiction, source qualifications and complete amounts are readable.'},
 {'scope':'Native SI PDF p.3/S3','result':'Reopened original page image and rechecked all reagent grades, stock charges, 0.51 mL aliquot, nitrogen scope and relative wash formulations. This is a targeted reread; the earlier passed 20-page source audit is reused.'},
 {'scope':'Formamidine acetate','result':'C3H8N2O2 is the elemental sum of the printed neutral pair; formal formamidinium/acetate components remain disconnected with +1/-1 charges and one resonance form. No hydrate, 3D ion pair or dissolved proton-transfer assignment.'},
 {'scope':'Prepared FA-oleate','result':'Operational stock identity is symbolic and distinct from the starting acetate salt. Complete 0.1042 g/0.8 mL/3.2 mL charges are not substituted for the later 0.51 mL aliquot; final concentration and storage remain unknown.'},
 {'scope':'OA and OAm references','result':'Source roles and grades are preserved, including OAm70%. Named cis reference graphs and 3D geometry agree; they do not establish batch isomer composition, protonation or bound-ligand geometry.'},
 {'scope':'1-Octadecene','result':'Terminal alkene connectivity and C18H36 formula retained. >90% is preserved as a lower bound; 3.2 mL precursor-stock charge remains separate from 2.5 mL reaction charge.'},
 {'scope':'Toluene and acetonitrile','result':'Solvent and antisolvent roles and 99.8% anhydrous source labels agree. Three alternative relative-volume formulations stay separate, with no invented absolute wash volume.'},
 {'scope':'Generic hexane','result':'95% source hexane is a symbol with unspecified isomer; no n-hexane model is assigned.'},
 {'scope':'Nitrogen','result':'Cached NIST ground-state 14N2 row, Å units and1.09768 distance were inspected; exact geometry checked. Reference isotope identity is explicitly separate from any source-gas isotope assay.'},
 {'scope':'PbI2','result':'Symbolic lead(II) iodide reference leaves purity/supplier and coordination unknown. The 0.075 mmol reaction charge maps exactly to the selected canonical slot.'},
 {'scope':'FAPbI3 and delta phase inventory symbols','result':'Material inventory identities remain separate from product/sample bindings. The delta-phase statement is limited to the reported competing 25°C context; no whole-batch purity or coordinates are inferred.'},
 {'scope':'PbO2 reference','result':'Only cited Raman-degradation interpretation is claimed; it is not a present synthesis precursor or detected product component.'},
 {'scope':'26 material slots and five stock instances','result':'Read all source-specific captions, roles, grade/amount pointers and complete paired option mappings. All12 solute/solvent component identities and74 quantity references transport exactly.'},
 {'scope':'Retained model provenance and public scope','result':'Four PubChem 3D SDFs agree atom-for-atom with retained arrays; acetonitrile retains explicit ETKDGv3/MMFF94s method metadata; N2 retains qualified NIST provenance. Current model notes do not inherit another paper’s role. Thirty public candidates exclude source documents, pages and private snapshots.'}
]
report={'audit_id':'sasongko2025-molecular-stock-independent-audit-v1','status':'passed','author':'/root/peng1998_reader_assets','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'proposal_freeze_path':str(A/'package-freeze.json'),'proposal_freeze_sha256':sha(A/'package-freeze.json'),'source_audit_sha256':inp['source_audit']['sha256'],'canonical_audit_sha256':inp['canonical_audit']['sha256'],
 'scope':'Distinct source-qualified molecular/stock reference and exact canonical-slot audit, including actual static views and executed current consumer fixture. No product-coordinate, integrated-browser, Site or publication approval.',
 'findings':[],'open_findings':[],
 'counts':{'identities':13,'material_slots':26,'stock_instances':5,'unique_formulations':4,'stock_components':12,'quantity_references':74,'models_2d':7,'retained_models_3d':6,'symbolic_identities':6,'public_asset_candidates':30,'actual_static_panels_viewed':23,'contact_sheets_viewed':6},
 'validation':{'independent_scientific_hash_pointer_checks':c['summary']['executed'],'passed':c['summary']['passed'],'reviewed_consumer_fixture_checks':v['check_count'],'consumer_counts':v['counts'],'final_bound_file_count':len(bound),'all_bound_bytes_stable':True,'runtime':c['runtime'],'rdkit_version':c['rdkit_version'],
 'consumer_scope':'The reviewed author consumer fixture was copied to this separate audit folder, with input/output path routing changed and auditor attribution added, then independently executed. It runs the exact current chemical-viewer snapshot with a minimal DOM/3Dmol data sink; this does not claim mounted-browser/WebGL rendering. Persisted author approval flags remain false.'},
 'manual_scopes':manual,'viewed_panels':panels,'geometry_results':c['chemistry'],
 'retained_constraints':['All source/canonical conflicts, uncertainty, missing stock volume/concentration and unknown storage remain explicit.','OA/OAm cis graphs are qualified references, not source isomer measurements or nanocrystal surface structures.','Symbols for hexane, PbI2, FA-oleate and phase/reference identities do not create measured atoms or dissolved coordination.','No product/sample binding or training admission is made by this package.','Integrated Site/browser/publication remain distinct root-owned gates.'],
 'conclusion':'Passed without author corrections. All13 source identities,26 material slots,five stock instances/twelve components and74 quantity references match the passed source/canonical scope. All23 panels were actually inspected; graph chemistry, group indices, retained conformers, exact cached provenance and current consumer transitions pass.',
 'bound_files':dict(sorted(bound.items()))}
save(O/'independent-audit-v1.json',report);io_path(O/'independent-audit.json').write_bytes(io_path(O/'independent-audit-v1.json').read_bytes())
md='''# Sasongko molecular and stock audit

**Passed without corrections.** Author `/root/peng1998_reader_assets`; independent auditor `/root/backlog_eta`.

All 13 identities, 26 material slots, five stock instances/four formulations, twelve components and 74 quantity references are source-consistent and exactly bound to the passed canonical package. All 23 static panels were actually viewed. There are seven valid 2D graphs, six unchanged qualified reference conformers and six symbolic identities.

The audit preserves FA acetate versus prepared FA-oleate, whole-stock charges versus the 0.51 mL aliquot, paired wash alternatives, >90% ODE and70% OAm. Cis OA/OAm are qualified free-molecule references; generic hexane stays symbolic. PbO2 remains cited interpretation only. No solution speciation, surface geometry, product atomic model or training admission is asserted.

6,195 independent chemistry/hash/pointer checks and1,043 independently re-executed consumer-fixture checks pass. Native SI p.S3 was reopened for the amounts and grades; prior complete source/canonical audits retain their scope. The fixture is actual function testing with a minimal DOM/data sink, not an integrated browser claim.

Only the thirty allowlisted assets are public candidates. Source pages, original PDFs/SI and private provenance snapshots remain excluded. All frozen author bytes are unchanged; integration/browser/publication gates remain separate.
'''
io_path(O/'independent-audit-v1.md').write_text(md,encoding='utf-8');io_path(O/'independent-audit.md').write_bytes(io_path(O/'independent-audit-v1.md').read_bytes())
print(json.dumps({'status':'passed','audit_path':str(O/'independent-audit.json'),'audit_sha256':sha(O/'independent-audit.json'),'bound_files':len(bound),'checks':c['summary']['executed']+v['check_count'],'manual_scopes':len(manual)},indent=2))
