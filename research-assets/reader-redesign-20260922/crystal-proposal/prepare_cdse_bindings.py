"""Reuse existing CdSe assets; no network access and no site writes."""
from pathlib import Path
from collections import Counter
import json,hashlib,math,itertools
ROOT=Path(__file__).parent
SITE=Path(r'[local path redacted]')
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
registry=read(SITE/'assets/crystal-references/registry.json')
wz=next(x for x in registry['entries'] if x['id']=='cdse-wurtzite-cod-9016056')
modelpath=SITE/'assets/crystal-references'/wz['modelPath']
cifpath=SITE/'assets/crystal-references'/wz['cifPath']
assert sha(modelpath)==wz['modelSha256']
assert sha(cifpath)==wz['cifSha256']
modern=read(modelpath)
legacy_wz=read(SITE/'assets/cdse-structures/cdse-unit-cell-viewer.json')
assert modern['cellVectors']==legacy_wz['latticeVectors']
for a,b in zip(modern['atoms'],legacy_wz['atoms']):
 assert a['element']==b['elem']
 assert all(abs(a[k]-b[k])<1e-12 for k in ['x','y','z'])
material=read(SITE/'data/materials/cdse-d923c5.json')
routes=[r['record_id'] for r in material['records'] if r.get('is_synthesis_route')]
zb_ids=[r for r in routes if r.startswith('nakonechnyi-2017-zb-')]
excluded=['murray-1993-cdse-small-species']
wz_ids=[r for r in routes if r not in zb_ids+excluded]
base='Independent bulk wurtzite CdSe unit cell from COD 9016056 (Freeman, Mair and Barnea, 1977), reusing the validated CdSe viewer. This is not a measured synthesis-sample structure and does not determine its phase, defects, size, ligands, shell strain or interface.'
binding_scopes={}
for rid in wz_ids:
 if rid in wz['record_ids']: continue
 if rid.startswith('murray-1993-'):
  note='This retains the reference shown on the legacy Murray method page. The shared legacy 3.5 × 3.0 nm illustrative crop is not assigned to this individual method or its product.'
 elif rid.startswith('peng-2000-'):
  note='This retains the legacy Peng reader comparison. Rod shape and source micrographs do not turn this cell into measured particle coordinates or assign a particular figure specimen to the selected recipe.'
 elif rid.startswith('nakonechnyi-2017-wz-'):
  note='The record reports a wurtzite product context. The bulk reference is independent; it is not a refinement of that product or any overgrown shell.'
 else:
  note='This comparison does not fill a missing specimen-phase assignment. In composites it represents the CdSe component only; no overlayer or coherent interface is constructed.'
 binding_scopes[rid]=base+' '+note
delta=dict(id=wz['id'],add_record_ids=sorted(binding_scopes),sourceType='literature_bulk_reference',defaultForSample=False,bindingScopes=binding_scopes,existing_assets=dict(cifPath=wz['cifPath'],modelPath=wz['modelPath'],cifSha256=sha(cifpath),modelSha256=sha(modelpath)),merge_instruction='Union add_record_ids into the existing entry record_ids and merge bindingScopes; preserve existing bindings, scopes, assets and hashes. Do not replace the whole registry entry.')
write(ROOT/'cdse-wurtzite-binding-extension.json',delta)

# Adapt the pre-existing cubic reference exactly. It is an ideal construction,
# not a new retrieved refinement; the explicit P1 export lists all eight sites.
original=SITE/'assets/crystal-reference.json'
old=read(original)
v=old['latticeVectors']
atoms=[]
for i,a in enumerate(old['fractionalAtoms']):
 f=[a[k] for k in ['x','y','z']]
 xyz=[sum(f[j]*v[j][k] for j in range(3)) for k in range(3)]
 atoms.append(dict(element=a['element'],x=xyz[0],y=xyz[1],z=xyz[2],fractional=f,occupancy=1,site=a['element']+str(i+1),properties={'constructed_reference':True}))
assert Counter(a['element'] for a in atoms)=={'Cd':4,'Se':4}
minimum=min(math.sqrt(sum(sum((a['fractional'][j]-b['fractional'][j]+shift[j])*v[j][k] for j in range(3))**2 for k in range(3))) for i,a in enumerate(atoms) for j,b in enumerate(atoms) for shift in itertools.product([-1,0,1],repeat=3) if i!=j or shift!=(0,0,0))
assert abs(minimum-math.sqrt(3)*old['a']/4)<1e-9
id='cdse-zinc-blende-existing-ideal-reference'
scope='Constructed zinc-blende CdSe reference reusing the existing site geometry: ideal fractional basis and a = 6.077 angstrom from the cited epitaxial-film literature. This is not a refined nanocrystal, fitted lattice parameter, surface or core/shell interface. The CIF is an explicit eight-site P1 export of the ideal F-43m prototype, not a measured P1 phase.'
model=dict(id=id,name='Constructed zinc-blende CdSe reference',formula='CdSe',cell={k:old[k] for k in ['a','b','c','alpha','beta','gamma']},cellVectors=v,atoms=atoms,spaceGroup='F -4 3 m (ideal prototype)',spaceGroupNumber=216,units='angstrom',periodic=True,representation='conventional_unit_cell_sites',mixedOccupancy=False,sourceType='constructed_lattice_reference',phaseScope=scope,scope=scope,caption=scope,source=dict(original_asset_path='assets/crystal-reference.json',original_asset_sha256=sha(original),lattice_parameter=old['latticeParameterSource'],basis_source=old['basisSource'],adaptation='Only schema conversion and Cartesian multiplication of the existing fractional sites; no fitted or newly retrieved coordinates.'),training_eligible=False,measured_sample_structure=False,reference_only=True,renderingNotes=old['renderingNotes'])
out=ROOT/'cdse-adapter-assets/crystal-references'
model_file=out/'models'/(id+'.json');write(model_file,model)
cif_file=out/(id+'.cif')
text=['# Constructed reference from existing MatterSyn assets/crystal-reference.json','# Not measured CdSe nanocrystal coordinates. Explicit P1 export of ideal F-43m basis.','# Original metadata SHA256 '+sha(original),'data_cdse_zinc_blende_constructed',"_chemical_formula_sum 'Cd4 Se4'","_symmetry_space_group_name_H-M 'P 1'",'_space_group_IT_number 1']
for k,tag in [('a','length_a'),('b','length_b'),('c','length_c'),('alpha','angle_alpha'),('beta','angle_beta'),('gamma','angle_gamma')]:text.append('_cell_'+tag+' '+str(old[k]))
text+=['loop_','_space_group_symop_operation_xyz',"'x,y,z'",'loop_','_atom_site_label','_atom_site_type_symbol','_atom_site_fract_x','_atom_site_fract_y','_atom_site_fract_z','_atom_site_occupancy']
for a in atoms:text.append(' '.join([a['site'],a['element'],*[str(f) for f in a['fractional']],'1']))
cif_file.write_text('\n'.join(text)+'\n',encoding='utf-8')
entry=dict(id=id,name='Constructed zinc-blende CdSe reference',formula='CdSe',record_ids=zb_ids,description=scope,scope=scope,phaseScope=scope,sourceType='constructed_lattice_reference',referenceType='locally_constructed_ideal_reference',sourceUrl=old['latticeParameterSource']['url'],sourceLinkLabel='Existing lattice-parameter citation',cifPath=cif_file.name,modelPath='models/'+model_file.name,spaceGroup='F -4 3 m (ideal prototype; CIF export P1)',spaceGroupNumber=216,cifExportSpaceGroupNumber=1,mixedOccupancy=False,cifSha256=sha(cif_file),modelSha256=sha(model_file),referenceOnly=True,trainingEligible=False,measuredSampleStructure=False,defaultForSample=False,displayPolicy='independent_reference',bindingScopes={rid:scope+' The source record labels this product zinc blende; this independent construction does not validate or refine that phase assignment.' for rid in zb_ids},additionalDownloads=[dict(label='Existing construction metadata',path='../crystal-reference.json')])
write(ROOT/'cdse-zinc-blende-registry-addition.json',dict(schema_version='mattersyn-reference-registry/1',entries=[entry]))
bound=set(wz['record_ids'])|set(delta['add_record_ids'])|set(zb_ids)
write(ROOT/'cdse-bindings-validation.json',dict(status='pass',wurtzite_assets_reused_byte_identically=True,wurtzite_matches_legacy_coordinates=True,wurtzite_existing_route_count=len(set(routes)&set(wz['record_ids'])),wurtzite_additional_route_count=len(delta['add_record_ids']),cubic_adapted_route_count=len(zb_ids),cdse_route_total=len(routes),cdse_routes_with_reference_after_merge=sorted(set(routes)&bound),explicitly_unbound=sorted(set(routes)-bound),both_murray_methods_covered=all(x in bound for x in ['murray-1993-cdse-method1','murray-1993-cdse-method2']),cubic_atom_count=len(atoms),cubic_composition=dict(Counter(a['element'] for a in atoms)),cubic_nearest_neighbor_angstrom=minimum,source_asset_sha256=sha(original),cubic_model_sha256=sha(model_file),cubic_cif_sha256=sha(cif_file),site_modified=False,network_requests=0))
print(json.dumps(read(ROOT/'cdse-bindings-validation.json'),indent=2))
