"""Build an ideal diamond-Si reference, not an experimental structure.

All writes remain in this private package. No database CIF, paper or theory
calculation is retrieved. The quoted bulk comparison parameter is from Littau.
"""
import sys,json,hashlib,math,itertools,collections,html
from pathlib import Path
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent
REVIEW=BASE.parent
sys.path.insert(0,'[local path redacted]')
import gemmi
for d in ['models','downloads','review']:(BASE/d).mkdir(exist_ok=True)
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
A=5.43
NN=math.sqrt(3)*A/4
FRACTIONS=[(0,0,0),(0,.5,.5),(.5,0,.5),(.5,.5,0),(.25,.25,.25),(.25,.75,.75),(.75,.25,.75),(.75,.75,.25)]
CELL={'a':A,'b':A,'c':A,'alpha':90.0,'beta':90.0,'gamma':90.0}
VECTORS=[[A,0,0],[0,A,0],[0,0,A]]
SG=gemmi.find_spacegroup_by_name('F d -3 m:1')
DOI='https://doi.org/10.1021/j100108a019'
RID='littau-1993-si-diamond-ideal-reference'
FINID='littau-1993-si-diamond-illustrative-sphere-3nm'
SOURCE_SHA='dd498b93be57a3701beedb3302c5111e85b58f4e73db40be8e8c58b1622a592e'
SOURCE={'doi':'10.1021/j100108a019','url':DOI,'document_id':'doc-01944414b621171a9ec0',
 'source_sha256':SOURCE_SHA,'locator':'Main PDF p. 5, printed p. 1228, Results A, lattice-parameter comparison; main p. 4 Figure 6 caption.',
 'reported_parameter':{'name':'bulk comparison lattice parameter a0','value':A,'unit':'angstrom','status':'reported_bulk_reference'},
 'sample_comparison':'The paper reports 6.0 and 2.0 lattice positions unchanged within 0.25% of the quoted bulk value. This is not an exact independently refined sample cell or an atomic-coordinate determination.'}
LIMITS=['Locally constructed ideal reference, not an experimental CIF or measured nanocrystal atomic coordinates.',
 'The lattice parameter 5.43 angstrom is the paper\'s quoted bulk comparison value, not an exact measured value assigned to either formulation.',
 'All Si occupancies are set to one as an ideal-model assumption.',
 'No oxide-shell atoms, SiO2 crystal phase, ligands, hydrogen termination, surface reconstruction, strain, defects, aggregation or interfacial structure are modeled.',
 'No electronic-structure, energy minimization, DFT or theoretical property prediction is performed.',
 'Reference geometry is excluded from measured-structure labels and recipe-training targets.']

def base_atom(index,position,fractional=None):
 atom={'index':index,'serial':index,'element':'Si','elem':'Si','x':round(position[0],8),'y':round(position[1],8),'z':round(position[2],8),
 'occupancy':1.0,'site':'Si'+str(index+1),'label':'Si','mixed_site':False,
 'properties':{'reference_only':True,'measured_sample':False},'bonds':[],'bondOrder':[]}
 if fractional is not None:atom['fractional']=list(fractional)
 return atom
def connect(atoms):
 edges=[]
 for i,a in enumerate(atoms):
  for j,b in enumerate(atoms[:i]):
   distance=math.dist([a[c] for c in ['x','y','z']],[b[c] for c in ['x','y','z']])
   if abs(distance-NN)<1e-7:
    a['bonds'].append(j);a['bondOrder'].append(1);b['bonds'].append(i);b['bondOrder'].append(1)
    edges.append({'a':j,'b':i,'order':1,'distanceAngstrom':round(distance,10)})
 return edges

atoms=[base_atom(i,[A*v for v in f],f) for i,f in enumerate(FRACTIONS)]
incell=connect(atoms)
periodic_neighbors={i:[] for i in range(8)};periodic_edges={}
for i,f in enumerate(FRACTIONS):
 for j,g in enumerate(FRACTIONS):
  for shift in itertools.product([-1,0,1],repeat=3):
   distance=A*math.sqrt(sum((g[k]+shift[k]-f[k])**2 for k in range(3)))
   if abs(distance-NN)<1e-10:
    periodic_neighbors[i].append({'atom':j,'imageShift':list(shift),'distanceAngstrom':NN})
    key=min((i,j,*shift),(j,i,*[-v for v in shift]))
    periodic_edges[key]={'a':key[0],'b':key[1],'imageShiftOfB':list(key[2:]),'distanceAngstrom':NN}
context_keys=[(i,0,0,0) for i in range(8)]
for neighbors in periodic_neighbors.values():
 for neighbor in neighbors:
  key=(neighbor['atom'],*neighbor['imageShift'])
  if key not in context_keys:context_keys.append(key)
context=[]
for k,(site,*shift) in enumerate(context_keys):
 p=[A*(FRACTIONS[site][d]+shift[d]) for d in range(3)]
 atom=base_atom(k,p);atom.update({'isPeriodicImage':any(shift),'parentCellSite':site,'imageShift':shift});context.append(atom)
connect(context)
edges=[]
for axis in range(3):
 for side1,side2 in itertools.product([0,1],repeat=2):
  start=[side1,side2];start.insert(axis,0);end=list(start);end[axis]=1
  edges.append({'start':dict(zip(['x','y','z'],[v*A for v in start])),'end':dict(zip(['x','y','z'],[v*A for v in end]))})
unit={'id':RID,'name':'Ideal diamond-Si reference unit cell','formula':'Si','modelType':'Ideal geometric bulk reference',
 'atoms':atoms,'fractionalSites':[{'label':'Si'+str(i+1),'element':'Si','fractional':list(f),'occupancy':1.0} for i,f in enumerate(FRACTIONS)],
 'cell':CELL,'cellVectors':VECTORS,'spaceGroup':'F d -3 m:1','spaceGroupNumber':227,'originChoice':1,
 'units':'angstrom','coordinateUnits':'angstrom','periodic':True,'representation':'conventional_unit_cell_sites',
 'referenceOnly':True,'training_eligible':False,'exact_structure_recipe_eligible':False,'measured_sample_structure':False,
 'evidence_type':'illustrative','mixedOccupancy':False,'elementCounts':{'Si':8},'source':SOURCE,
 'caption':'Ideal diamond-Si reference at the paper\'s quoted bulk a0 = 5.43 angstrom. Constructed geometry, not an experimental sample structure.',
 'construction':{'method':'FCC lattice with basis (0,0,0) and (1/4,1/4,1/4); conventional cubic cell.',
 'fractionalCoordinateSource':'Standard ideal diamond motif constructed explicitly; not coordinates extracted from Littau or downloaded from a structural database.',
 'symmetryCheck':'Gemmi '+gemmi.__version__+' F d -3 m origin choice 1 expands (0,0,0) into exactly these eight sites.'},
 'nearestNeighborDistanceAngstrom':NN,'periodicNeighborLists':periodic_neighbors,'periodicBonds':list(periodic_edges.values()),
 'bondsWithinCell':incell,'atomsWithPeriodicNeighborContext':context,'unitCellEdges':edges,'limitations':LIMITS,
 'renderingNotes':['The eight stored sites belong to a half-open conventional cell; periodic neighbors are separate context, not extra cell atoms.',
 'periodicBonds include image shifts. Do not draw them between unshifted atoms as though every neighbor lies inside the same cell.',
 'The existing crystal-viewer unit/supercell path can consume atoms, cell and cellVectors directly.']}
dump(BASE/'models/si-diamond-ideal-unit-cell.json',unit)

def cif_text(expanded=False):
 name='littau_si_ideal_expanded_p1' if expanded else 'littau_si_ideal_diamond'
 text=f'''data_{name}
_audit_creation_method
;Locally constructed ideal diamond-Si reference. NOT an experimental CIF.
No atom coordinates were measured or refined for this model.
The lattice parameter is Littau 1993's quoted BULK comparison value.
No oxide shell, surface termination, strain or defects are modeled.
;
_chemical_name_common 'Ideal diamond-silicon reference, not a synthesis specimen'
_chemical_formula_sum 'Si'
_cell_formula_units_Z 8
_cell_length_a 5.43
_cell_length_b 5.43
_cell_length_c 5.43
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
_publ_section_comment
;Source of bulk comparison parameter: doi:10.1021/j100108a019,
main PDF page 5, printed page 1228. Reported 6.0 and 2.0 lattice
positions agree within 0.25% of bulk a0=5.43 angstrom.
This ideal coordinate model is newly generated for illustration.
The finite sphere is a separate nonperiodic model and is not this CIF.
;
'''
 if expanded:
  text+="_space_group_name_H-M_alt 'P 1'\n_space_group_IT_number 1\n_space_group_name_Hall 'P 1'\n"
  text+="# Explicitly expanded eight-site cell. Parent ideal motif has F d -3 m:1 symmetry (No. 227).\n"
  text+="loop_\n_space_group_symop_id\n_space_group_symop_operation_xyz\n1 'x,y,z'\n"
 else:
  text+="_space_group_name_H-M_alt 'F d -3 m:1'\n_space_group_IT_number 227\n_space_group_name_Hall '"+SG.hall+"'\n"
  text+="loop_\n_space_group_symop_id\n_space_group_symop_operation_xyz\n"
  for i,op in enumerate(SG.operations()):text+=str(i+1)+" '"+op.triplet()+"'\n"
 text+='loop_\n_atom_site_label\n_atom_site_type_symbol\n_atom_site_fract_x\n_atom_site_fract_y\n_atom_site_fract_z\n_atom_site_occupancy\n'
 for i,f in enumerate(FRACTIONS if expanded else [FRACTIONS[0]]):text+='Si'+str(i+1)+' Si '+' '.join(f'{v:.8f}' for v in f)+' 1\n'
 return text
for expanded,name in [(False,'si-diamond-ideal-reference.cif'),(True,'si-diamond-ideal-expanded-p1.cif')]:
 (BASE/name).write_text(cif_text(expanded),encoding='utf-8')

RADIUS=15.0
finite=[]
N=math.ceil(RADIUS/A)+1
for tx,ty,tz in itertools.product(range(-N,N+1),repeat=3):
 for site,f in enumerate(FRACTIONS):
  p=[A*(f[k]+[tx,ty,tz][k]) for k in range(3)]
  if sum(v*v for v in p)<=RADIUS**2+1e-10:
   atom=base_atom(len(finite),p);atom['parentCellSite']=site;atom['cellTranslation']=[tx,ty,tz];finite.append(atom)
finite_bonds=connect(finite)
hist=dict(sorted(collections.Counter(len(a['bonds']) for a in finite).items()))
finite_model={'id':FINID,'name':'Illustrative diamond-Si sphere, chosen 3 nm envelope','formula':'Si',
 'atoms':finite,'bonds':finite_bonds,'cell':None,'cellVectors':None,'units':'angstrom','coordinateUnits':'angstrom',
 'periodic':False,'representation':'finite_illustrative_particle','modelType':'Unrelaxed spherical crop of ideal diamond lattice',
 'referenceOnly':True,'training_eligible':False,'exact_structure_recipe_eligible':False,'measured_sample_structure':False,
 'evidence_type':'illustrative','source':SOURCE,
 'caption':'Illustrative spherical crop with a chosen 3 nm envelope. Size and shape are visualization choices, not a measured Littau specimen or a fitted sample model.',
 'construction':{'parentModelId':RID,'latticeParameterAngstrom':A,'centerAngstrom':[0,0,0],'radiusAngstrom':RADIUS,
 'envelopeDiameterNm':3.0,'diameterBasis':'Arbitrary display choice, not a reported measurement assigned to either formulation.',
 'shape':'sphere','shapeBasis':'Illustrative clipping envelope, not an experimental morphology assignment.',
 'algorithm':'Tile the ideal eight-site conventional cell and retain sites whose Euclidean distance from the origin is at most 15 angstrom.',
 'relaxation':'None','surfacePassivation':'None'},
 'elementCounts':{'Si':len(finite)},'coordinationHistogram':hist,
 'bondMeaning':'Geometric nearest-neighbor edges at a*sqrt(3)/4; unit order is for visualization and is not a measured bond-order determination.',
 'limitations':LIMITS+['Finite surfaces are artificially truncated and unpassivated; undercoordinated atoms are expected.',
 'The generated atom count is a geometric count, not a measured particle composition or number of atoms in an experimental specimen.'],
 'renderingNotes':['Use atoms directly in a nonperiodic 3Dmol model; do not tile this model or draw a periodic cell around it.',
 'Each atom includes elem, serial, bonds and bondOrder for direct 3Dmol addAtoms compatibility.',
 'Never use this 3 nm view to overwrite source TEM sizes, XRD coherence lengths or HPLC equivalent diameters.']}
dump(BASE/'models/si-diamond-illustrative-sphere-3nm.json',finite_model)
xyz=[str(len(finite)),'ILLUSTRATIVE NONPERIODIC ideal diamond-Si crop; chosen 3 nm spherical envelope; a_bulk=5.43 A; no shell/passivation; not a measured particle']
xyz += ['Si '+' '.join(f'{a[k]:.8f}' for k in ['x','y','z']) for a in finite]
(BASE/'downloads/si-diamond-illustrative-sphere-3nm.xyz').write_text('\n'.join(xyz)+'\n',encoding='utf-8')

record_ids=['littau-1993-si-aerosol-6p0','littau-1993-si-aerosol-2p0']
entry={'id':RID,'name':'Ideal diamond-Si bulk comparison reference','formula':'Si','record_ids':record_ids,
 'description':unit['caption'],'scope':'The 6.0 and 2.0 formulations have diamond-Si evidence. This ideal reference uses the paper\'s quoted bulk comparison value, not experimentally refined sample coordinates. The separate 3 nm sphere is an arbitrary illustration.',
 'sourceUrl':DOI,'sourceLinkLabel':'Paper supplying the bulk comparison parameter',
 'cifPath':'si-diamond-ideal-reference.cif','modelPath':'models/si-diamond-ideal-unit-cell.json',
 'spaceGroup':'F d -3 m:1','spaceGroupNumber':227,'mixedOccupancy':False,
 'cifSha256':sha(BASE/'si-diamond-ideal-reference.cif'),'modelSha256':sha(BASE/'models/si-diamond-ideal-unit-cell.json'),
 'referenceOnly':True,'trainingEligible':False,'measuredSampleStructure':False,
 'referenceType':'locally_constructed_ideal_reference','structureAssetRole':'illustrative',
 'finiteModelPath':'models/si-diamond-illustrative-sphere-3nm.json','finiteModelSha256':sha(BASE/'models/si-diamond-illustrative-sphere-3nm.json'),
 'finiteCaption':finite_model['caption'],'finiteModelPeriodic':False,
 'additionalDownloads':[{'label':'Expanded eight-site reference CIF (P1)','path':'si-diamond-ideal-expanded-p1.cif','sha256':sha(BASE/'si-diamond-ideal-expanded-p1.cif')},
 {'label':'Illustrative finite sphere XYZ','path':'downloads/si-diamond-illustrative-sphere-3nm.xyz','sha256':sha(BASE/'downloads/si-diamond-illustrative-sphere-3nm.xyz')}],
 'sourceLocator':SOURCE['locator'],'component_role':'Ideal crystalline silicon reference only; no oxide-shell model.'}
dump(BASE/'registry-additions.json',{'schema_version':'mattersyn-reference-registry/1','entries':[entry],
 'scope':'Locally constructed illustrative reference, not an external experimental database structure or measured sample CIF.',
 'excluded_record_ids':[{'record_id':'littau-1993-si-aerosol-1p0','reason':'Direct crystalline-core structure is not established; diffuse XRD does not justify a diamond-Si measured label.'},
 {'record_id':'littau-1993-aks41-context','reason':'Kept unbound by default. A future separately labeled contextual reference is possible, but AKS41 has no complete recipe or direct 5.43 angstrom sample determination.'}]})
record_assets={}
for rid in record_ids:
 record_assets[rid]=[
 {'id':RID,'role':'illustrative','sample_id':None,'url':'assets/crystal-references/si-diamond-ideal-reference.cif',
 'description':unit['caption'],'eligible_as_measured_label':False},
 {'id':FINID,'role':'illustrative','sample_id':None,'url':'assets/crystal-references/models/si-diamond-illustrative-sphere-3nm.json',
 'description':finite_model['caption'],'eligible_as_measured_label':False}]
dump(BASE/'proposed-record-structure-assets.json',{'record_structure_assets':record_assets,
 'action':'Append after independent review; do not overwrite existing measured evidence or change task eligibility.',
 'sourceRecordSha256':{rid:sha(REVIEW/'canonical-drafts'/(rid+'.json')) for rid in record_ids}})
dump(BASE/'provenance.json',{'source':SOURCE,'construction':unit['construction'],'finiteConstruction':finite_model['construction'],
 'gemmiVersion':gemmi.__version__,'assumptions':LIMITS,
 'explicitInferenceBoundaries':[
 'Ideal diamond coordinates and full occupancies are constructed, not reported atom coordinates.',
 'Space group 227 and origin choice 1 describe the constructed ideal motif; they are not a new refinement result from Littau.',
 'The source reports a comparison within 0.25%; this model does not assign an uncertainty or sample-specific a=5.43.',
 'The 3 nm spherical envelope and lattice-centered origin are display choices, not source size/shape labels.',
 'Periodic nearest-neighbor geometry and finite counts are derived from the ideal lattice, not measured properties.',
 'Both CIFs are generated references; neither is a downloaded experimental CIF. The P1 file is explicitly expanded.',
 'No shell, ligand, solution, interface, diffraction image or electronic structure is invented.'],
 'viewerCompatibility':{'unitCell':'Compatible with current crystal-viewer.mjs atoms/cell/cellVectors contract.',
 'finiteParticle':'3Dmol-compatible atom array; current crystal-viewer.mjs has no nonperiodic branch. Root must add a separate finite-mode path using atoms directly, without replication or cell lines.',
 'additionalDownloads':'Current viewer reads only cifPath; expose expanded CIF/XYZ and finite controls deliberately rather than assuming these optional fields are consumed.'}})
print(json.dumps({'unitCellAtoms':len(atoms),'periodicNearestNeighbors':[len(x) for x in periodic_neighbors.values()],
 'periodicEdges':len(periodic_edges),'contextAtoms':len(context),'finiteAtoms':len(finite),'finiteEdges':len(finite_bonds),'coordinationHistogram':hist,'nearestNeighborAngstrom':NN},indent=2))
