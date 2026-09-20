"""Package COD reference and exact illustrative viewer coordinates; validate CIFs."""
import collections,hashlib,itertools,json,math,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'validation-runtime'))
import gemmi

source=ROOT.parent/'cdse-wurtzite-cod-9016056.cif'
raw=json.loads((ROOT/'exact-viewer-cluster.json').read_text())
ref=raw['reference'];atoms=raw['atoms'];basis=ref['fractionalAtoms'];vectors=ref['latticeVectors']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
jsonsave=lambda file,value:(ROOT/file).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
cart=lambda f:[sum(f[i]*vectors[i][d] for i in range(3)) for d in range(3)]
counts=collections.Counter(a['elem'] for a in atoms)
original=ROOT/'cdse-wurtzite-cod-9016056-original.cif'
shutil.copyfile(source,original)
assert sha(source)==sha(original)
assert source.read_bytes()==(ROOT/'cod-original-public-response.cif').read_bytes()

def cif_header(block,a,b,c,alpha,beta,gamma,formula,Z,description):
    return f'''# CIF1.1
data_{block}
_chemical_name_common '{description}'
_chemical_formula_sum '{formula}'
_space_group_name_H-M_alt 'P 1'
_space_group_IT_number 1
_cell_length_a {a:.12f}
_cell_length_b {b:.12f}
_cell_length_c {c:.12f}
_cell_angle_alpha {alpha}
_cell_angle_beta {beta}
_cell_angle_gamma {gamma}
_cell_formula_units_Z {Z}
loop_
_space_group_symop_id
_space_group_symop_operation_xyz
1 'x,y,z'
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_occupancy
'''

unitfile=ROOT/'cdse-wurtzite-unit-cell-expanded-p1.cif'
text='''# Symmetry-expanded bulk unit cell derived from COD 9016056.
# Physical parent structure: wurtzite P63mc, No. 186. P1 is an export convention.
# Source DOI: 10.1107/S0567739477000977, Freeman, Mair and Barnea (1977).
# Exact 1/3 and 2/3 replace the source CIF's five-decimal symmetry fractions.
# Source lattice a=4.299 A, c=7.010 A and u=0.37679 are preserved.
# This is a bulk reference, not measured coordinates of a quantum dot.
'''+cif_header('CdSe_bulk_wurtzite_expanded',ref['a'],ref['b'],ref['c'],90,90,120,'Cd Se',2,'CdSe bulk wurtzite reference in expanded P1 representation')
unitatoms=[]
element_indices=collections.Counter()
for b in basis:
    e=b['element'];element_indices[e]+=1
    text+=f"{e}{element_indices[e]} {e} {b['x']:.15f} {b['y']:.15f} {b['z']:.15f} 1\n"
    p=cart([b['x'],b['y'],b['z']]);idx=len(unitatoms)
    unitatoms.append({'elem':e,'x':p[0],'y':p[1],'z':p[2],'index':idx,'serial':idx,'bonds':[],'bondOrder':[],'fractional':[b['x'],b['y'],b['z']]})
unitfile.write_text(text,encoding='ascii')

# Directly preserve buildCrystal order and coordinates; no fit or relaxation.
xyz=ROOT/'cdse-3p5-by-3p0-nm-illustrative-cluster.xyz'
xyz.write_text(str(len(atoms))+'\n'+f'ILLUSTRATIVE bare ellipsoid crop from COD9016056; Cd{counts["Cd"]}Se{counts["Se"]}; units=angstrom; exact buildCrystal coordinate order; nominal 3.5x3.0 nm; not measured QD; ligands/faults/reconstruction omitted\n'+''.join(f"{a['elem']} {a['x']:.12f} {a['y']:.12f} {a['z']:.12f}\n" for a in atoms),encoding='ascii')
vacuum=80.0;shift=[vacuum/2]*3
clusterfile=ROOT/'cdse-3p5-by-3p0-nm-illustrative-cluster-vacuum.cif'
text='''# ILLUSTRATIVE FINITE CLUSTER, NOT AN EXPERIMENTAL CRYSTAL STRUCTURE.
# The 80 x 80 x 80 A P1 cell below is an ARTIFICIAL VACUUM BOX for file storage.
# It is NOT the CdSe unit cell, crystal lattice parameter, or measured supercell.
# Coordinates are the same as buildCrystal(reference, sampleRecords.tem6),
# translated by (+40,+40,+40) A to place the finite cluster inside the box.
# Nominal ellipsoid diameters: 35 A along c, 30 A perpendicular to c.
# Ligands, stacking faults, surface reconstruction and relaxation are omitted.
# Surface Cd/Se imbalance is a geometric crop artifact, not a measured composition.
# Parent bulk structure: COD 9016056, DOI 10.1107/S0567739477000977.
'''+cif_header('CdSe_illustrative_finite_cluster_in_artificial_vacuum',vacuum,vacuum,vacuum,90,90,90,f'Cd{counts["Cd"]} Se{counts["Se"]}',1,'Illustrative CdSe finite cluster in artificial vacuum box')
for i,a in enumerate(atoms):
    f=[(a[d]+shift[j])/vacuum for j,d in enumerate(['x','y','z'])]
    text+=f"{a['elem']}{i+1} {a['elem']} {f[0]:.15f} {f[1]:.15f} {f[2]:.15f} 1\n"
clusterfile.write_text(text,encoding='ascii')

# Complete periodic bonds, with a shift locating each neighbor's image cell.
periodic=[]
for i,a in enumerate(unitatoms):
    for j,b in enumerate(basis):
        for delta in itertools.product([-1,0,1],repeat=3):
            p=cart([b[d]+delta[k] for k,d in enumerate(['x','y','z'])])
            dist=math.dist([a[d] for d in ['x','y','z']],p)
            if a['elem']!=b['element'] and 2.45<dist<2.75:
                periodic.append({'a':i,'b':j,'neighborCellShift':list(delta),'distanceAngstrom':dist})
                if delta==(0,0,0):a['bonds'].append(j);a['bondOrder'].append(1)
assert collections.Counter(b['a'] for b in periodic)=={0:4,1:4,2:4,3:4}

# Optional immediate neighbor context makes tetrahedral coordination visible.
context=[];keys={}
for i,a in enumerate(unitatoms):
    keys[(i,(0,0,0))]=len(context);context.append(dict(a,baseAtomIndex=i,cellShift=[0,0,0],isPeriodicImage=False,bonds=[],bondOrder=[]))
for b in periodic:
    key=(b['b'],tuple(b['neighborCellShift']))
    if key not in keys:
        base=basis[b['b']];p=cart([base[d]+key[1][k] for k,d in enumerate(['x','y','z'])]);idx=len(context)
        context.append({'elem':base['element'],'x':p[0],'y':p[1],'z':p[2],'index':idx,'serial':idx,'baseAtomIndex':b['b'],'cellShift':list(key[1]),'isPeriodicImage':True,'bonds':[],'bondOrder':[]});keys[key]=idx
for i,a in enumerate(context):
    for j in range(i):
        b=context[j];dist=math.dist([a[d] for d in ['x','y','z']],[b[d] for d in ['x','y','z']])
        if a['elem']!=b['elem'] and 2.45<dist<2.75:
            a['bonds'].append(j);a['bondOrder'].append(1);b['bonds'].append(i);b['bondOrder'].append(1)
corners=[list(f) for f in itertools.product([0,1],repeat=3)]
points=[cart(f) for f in corners]
edges=[]
for i,f in enumerate(corners):
    for j,g in enumerate(corners[:i]):
        if sum(a!=b for a,b in zip(f,g))==1:
            edges.append({'start':dict(zip(['x','y','z'],points[j])),'end':dict(zip(['x','y','z'],points[i]))})
assert len(edges)==12
unitmodel={'id':'cdse-wurtzite-unit-cell','name':'Bulk wurtzite CdSe reference unit cell','coordinateUnits':'angstrom',
 'spaceGroup':'P63mc','spaceGroupNumber':186,'a':ref['a'],'b':ref['b'],'c':ref['c'],'alpha':90,'beta':90,'gamma':120,
 'latticeVectors':vectors,'fractionalAtoms':basis,'atoms':unitatoms,'atomsWithPeriodicNeighborContext':context,
 'unitCellEdges':edges,'unitCellCorners':points,'periodicNeighborBonds':periodic,
 'formulaUnitsPerCell':2,'uniqueAtomsPerCell':4,'uniqueComposition':{'Cd':2,'Se':2},
 'source':ref['source'],'sourceType':'experimental bulk crystallographic reference',
 'caption':'Bulk unit cell from COD 9016056; four unique atoms. Neighbor images, if shown, are periodic copies.',
 'notes':['Use atoms for four unique unit-cell sites. atomsWithPeriodicNeighborContext adds explicit neighboring images for coordination; do not count these as additional unit-cell sites.',
 '3Dmol AtomSpec arrays use elem/x/y/z and zero-based bonds/bondOrder. unitCellEdges may be passed as cylinder or line start/end vectors.',
 'P1 in the expanded CIF is an export representation, not a phase assignment. The physical bulk symmetry is P63mc (186).',
 'The original CIF five-decimal 1/3, 2/3 values are restored to exact symmetry fractions; measured u is preserved.']}
jsonsave('cdse-unit-cell-viewer.json',unitmodel)

# Independently parse all delivered CIFs using Gemmi, check source symmetry.
orig_structure=gemmi.make_small_structure_from_block(gemmi.cif.read_file(str(original)).sole_block())
assert len(orig_structure.sites)==2
assert orig_structure.spacegroup.number==186
unit=gemmi.make_small_structure_from_block(gemmi.cif.read_file(str(unitfile)).sole_block())
cluster=gemmi.make_small_structure_from_block(gemmi.cif.read_file(str(clusterfile)).sole_block())
assert len(unit.sites)==4 and len(cluster.sites)==len(atoms)
assert collections.Counter(s.element.name for s in unit.sites)=={'Cd':2,'Se':2}
assert collections.Counter(s.element.name for s in cluster.sites)==counts
expectedVolume=math.sqrt(3)/2*ref['a']**2*ref['c']
assert abs(unit.cell.volume-expectedVolume)<1e-9
maxerror=0
for a,s in zip(atoms,cluster.sites):
    xyz_back=cluster.cell.orthogonalize(s.fract)
    err=math.dist([xyz_back.x-40,xyz_back.y-40,xyz_back.z-40],[a[d] for d in ['x','y','z']])
    maxerror=max(maxerror,err)
assert maxerror<1e-9
rawxyz=xyz.read_text().splitlines();assert int(rawxyz[0])==len(atoms)
maxxyz=max(math.dist(list(map(float,row.split()[1:])),[a[d] for d in ['x','y','z']]) for row,a in zip(rawxyz[2:],atoms))
assert maxxyz<1e-9
for a in atoms:assert (a['x']**2+a['y']**2)/15**2+a['z']**2/17.5**2<=1+1e-12
assert len({(a['elem'],a['x'],a['y'],a['z']) for a in atoms})==len(atoms)
bonds=[math.dist([a[d] for d in ['x','y','z']],[atoms[j][d] for d in ['x','y','z']]) for a in atoms for j in a['bonds'] if j>a['index']]
extents={d:[min(a[d] for a in atoms),max(a[d] for a in atoms)] for d in ['x','y','z']}
validation={'parser':f'Gemmi {gemmi.__version__}','sourceCifCopyByteIdentical':True,'liveCodCifByteIdentical':True,
 'originalAsymmetricSiteCount':2,'originalSpaceGroupNumber':186,'expandedCellAtomCount':4,'expandedCellComposition':{'Cd':2,'Se':2},
 'unitCellVolumeAngstrom3':unit.cell.volume,'periodicCoordinationNumberEachSite':4,
 'unitCellNeighborBondRangeAngstrom':[min(b['distanceAngstrom'] for b in periodic),max(b['distanceAngstrom'] for b in periodic)],
 'clusterAtomCount':len(atoms),'clusterComposition':dict(counts),'clusterBondCount':len(bonds),
 'clusterBondRangeAngstrom':[min(bonds),max(bonds)],'duplicateAtoms':0,'allAtomsInsideRequestedEllipsoid':True,
 'cifRoundtripMaxCoordinateErrorAngstrom':maxerror,'xyzRoundtripMaxCoordinateErrorAngstrom':maxxyz,
 'clusterCoordinateExtentsAngstrom':extents,'artificialCifCellAngstrom':[vacuum]*3,'cifOriginTranslationAngstrom':shift,
 'minimumDistanceToVacuumBoxFaceAngstrom':min(min(lo+40,40-hi) for lo,hi in extents.values()),
 'vestaGuiTested':False,'formatNote':'Standard CIF with explicit atom types, occupancies, cell and symmetry fields; VESTA-specific session file not fabricated.'}
jsonsave('structure-validation.json',validation)
files=[]
for f,label,kind in [(original,'Original COD bulk unit-cell CIF','original-experimental-bulk-reference'),(unitfile,'Expanded four-site unit-cell CIF','derived-bulk-reference-p1-export'),(xyz,'Illustrative nanocrystal XYZ','finite-illustrative-cluster'),(clusterfile,'Illustrative nanocrystal CIF in artificial vacuum cell','finite-illustrative-cluster-artificial-vacuum')]:
    files.append({'file':f.name,'label':label,'kind':kind,'sha256':sha(f),'bytes':f.stat().st_size})
jsonsave('download-manifest.json',{'formula':'CdSe','parentReference':ref['source'],'downloads':files,'unitCellViewerFile':'cdse-unit-cell-viewer.json',
 'clusterNominalDimensionsNm':{'cAxis':3.5,'perpendicular':3.0},'clusterComposition':dict(counts),'coordinateUnits':'angstrom',
 'viewerCoordinateProvenance':{k:v for k,v in raw.items() if k not in ['reference','atoms']},
 'clusterCaveats':['Geometric crop of a bulk lattice for illustration; not a measured or relaxed quantum-dot structure.',
 'The 80 A orthogonal CIF cell is an artificial vacuum container, not the CdSe crystallographic unit cell.',
 'Ligands, stacking faults, surface reconstruction and thermal motion are omitted.',
 'The geometric cut produces Cd288Se294; this surface imbalance is not a claim about actual sample composition.',
 'Nominal ellipsoid boundary dimensions differ from atom-center coordinate extents.'],
 'validation':validation})
print(json.dumps(validation,indent=2))
