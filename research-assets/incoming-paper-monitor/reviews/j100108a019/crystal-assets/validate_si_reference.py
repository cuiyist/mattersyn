"""Independently validate reference files, CIF round-trips and nonperiodic crop."""
import sys,json,hashlib,math,itertools,collections,re,html
from pathlib import Path
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
import gemmi,pymupdf
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
errors=[];checks=0
def check(test,message):
 global checks
 checks+=1
 if not test:errors.append(message)
unit=read(B/'models/si-diamond-ideal-unit-cell.json')
finite=read(B/'models/si-diamond-illustrative-sphere-3nm.json')
registry=read(B/'registry-additions.json');entry=registry['entries'][0]
A=unit['cell']['a'];target=A*math.sqrt(3)/4
frac=[a['fractional'] for a in unit['atoms']]
canonical=lambda xyz:tuple(round(v%1,8) for v in xyz)
expected={canonical(f) for f in frac}
check(len(unit['atoms'])==len(expected)==8,'Eight unique conventional sites')
check(all(a['element']=='Si' and a['occupancy']==1 for a in unit['atoms']),'Full-occupancy silicon only')
check(all(0<=v<1 for f in frac for v in f),'Half-open fractional cell')
check(A==5.43 and unit['cell']['b']==A and unit['cell']['c']==A,'Quoted bulk parameter retained exactly as reference input')
check(all(unit['cell'][k]==90 for k in ['alpha','beta','gamma']),'Cubic angles')
for i,a in enumerate(unit['atoms']):
 check(all(abs(a[k]-A*a['fractional'][j])<1e-8 for j,k in enumerate(['x','y','z'])),'Fractional-to-Cartesian conversion '+str(i))
 # Independent minimum-image test, not the builder's neighbor-list values.
 distances=[]
 for j,b in enumerate(unit['atoms']):
  if i==j:continue
  d=[b['fractional'][k]-a['fractional'][k] for k in range(3)]
  d=[v-round(v) for v in d];distances.append(A*math.sqrt(sum(v*v for v in d)))
 check(abs(min(distances)-target)<1e-10,'Nearest-neighbor distance '+str(i))
 check(sum(abs(d-target)<1e-9 for d in distances)==4,'Four minimum-image nearest neighbors '+str(i))
for k,neighbors in unit['periodicNeighborLists'].items():
 check(len(neighbors)==4,'Four recorded periodic neighbors '+str(k))
 for neighbor in neighbors:
  i=int(k);j=neighbor['atom'];shift=neighbor['imageShift']
  reverse={'atom':i,'imageShift':[-v for v in shift]}
  check(any(n['atom']==reverse['atom'] and n['imageShift']==reverse['imageShift'] for n in unit['periodicNeighborLists'][str(j)]),'Periodic reciprocity')
check(len(unit['periodicBonds'])==16,'Sixteen undirected periodic neighbor edges')
symmetry={canonical(op.apply_to_xyz([0,0,0])) for op in gemmi.find_spacegroup_by_name('F d -3 m:1').operations()}
check(symmetry==expected,'Independent space-group expansion matches eight sites')
roundtrips=[]
for name,asu_count,sg in [('si-diamond-ideal-reference.cif',1,227),('si-diamond-ideal-expanded-p1.cif',8,1)]:
 doc=gemmi.cif.read(str(B/name));block=doc.sole_block();st=gemmi.make_small_structure_from_block(block)
 expanded=st.get_all_unit_cell_sites();got={canonical((s.fract.x,s.fract.y,s.fract.z)) for s in expanded}
 check(len(st.sites)==asu_count,name+' expected explicitly listed site count')
 check(got==expected and len(expanded)==8,name+' reconstructs eight unique sites')
 check(all(s.element.name=='Si' and s.occ==1 for s in expanded),name+' elemental counts/occupancy')
 check(abs(st.cell.a-A)<1e-10 and abs(st.cell.b-A)<1e-10 and abs(st.cell.c-A)<1e-10,name+' lattice parameter')
 check(int(block.find_value('_space_group_IT_number'))==sg,name+' exported symmetry declaration')
 text=doc.as_string();again=gemmi.cif.read_string(text).sole_block();st2=gemmi.make_small_structure_from_block(again)
 got2={canonical((s.fract.x,s.fract.y,s.fract.z)) for s in st2.get_all_unit_cell_sites()}
 check(got2==expected,name+' parse/write/parse coordinates round-trip')
 check('NOT an experimental CIF' in (B/name).read_text(encoding='utf-8'),name+' explicit reference warning')
 roundtrips.append({'file':name,'sha256':sha(B/name),'listedSites':len(st.sites),'expandedSiteCount':len(expanded),'spaceGroupNumber':sg,'roundTripPassed':got2==expected})
context=unit['atomsWithPeriodicNeighborContext']
for i in range(8):check(len(context[i]['bonds'])==4,'Periodic context gives four visible neighbors to base site '+str(i))
check(sum(not a['isPeriodicImage'] for a in context)==8,'Context images do not alter base cell count')

aa=finite['atoms'];positions=[(a['x'],a['y'],a['z']) for a in aa]
check(not finite['periodic'] and finite['cell'] is None and finite['cellVectors'] is None,'Finite model has no periodic cell')
check(len(aa)==705 and len(set(positions))==len(aa),'Finite crop count and uniqueness')
check(all(a['element']=='Si' and a['occupancy']==1 for a in aa),'Finite silicon only')
check(all(all(math.isfinite(v) for v in p) for p in positions),'Finite coordinates are finite numbers')
radius=finite['construction']['radiusAngstrom']
check(radius==15 and finite['construction']['envelopeDiameterNm']==3,'Single nanometer-to-angstrom conversion')
check(all(sum(v*v for v in p)<=radius*radius+1e-9 for p in positions),'Every atom lies inside chosen envelope')
reconstructed=set()
for t in itertools.product(range(-4,5),repeat=3):
 for f in expected:
  p=tuple(round((f[k]+t[k])*A,8) for k in range(3))
  if sum(v*v for v in p)<=radius*radius+1e-9:reconstructed.add(p)
check(reconstructed==set(positions),'Independent sphere enumeration reproduces exactly the finite sites')
max_diameter=0;minimum_pair=math.inf
for i,a in enumerate(aa):
 check(a['index']==a['serial']==i,'Finite contiguous indices '+str(i))
 check(len(a['bonds'])==len(a['bondOrder']) and len(a['bonds'])<=4,'Finite coordination/index arrays '+str(i))
 for j in a['bonds']:
  check(0<=j<len(aa) and i in aa[j]['bonds'],'Finite neighbor reciprocity')
  check(abs(math.dist(positions[i],positions[j])-target)<1e-7,'Finite neighbor length')
 for j in range(i):
  dist=math.dist(positions[i],positions[j]);max_diameter=max(max_diameter,dist);minimum_pair=min(minimum_pair,dist)
check(abs(minimum_pair-target)<1e-7,'Finite minimum separation has no duplicate/overlapping atoms')
check(max_diameter<=2*radius+1e-8,'Finite maximum span stays within envelope')
visited={0};stack=[0]
while stack:
 for j in aa[stack.pop()]['bonds']:
  if j not in visited:visited.add(j);stack.append(j)
check(len(visited)==len(aa),'Finite lattice crop is connected')
xyz=(B/'downloads/si-diamond-illustrative-sphere-3nm.xyz').read_text(encoding='utf-8').splitlines()
check(int(xyz[0])==len(aa) and len(xyz[2:])==len(aa),'XYZ atom count')
xyz_positions=[tuple(map(float,line.split()[1:])) for line in xyz[2:]]
check(xyz_positions==positions,'XYZ coordinates round-trip')
for key,path in [('cifSha256',entry['cifPath']),('modelSha256',entry['modelPath']),('finiteModelSha256',entry['finiteModelPath'])]:
 check(sha(B/path)==entry[key],key+' matches')
check(set(entry['record_ids'])=={'littau-1993-si-aerosol-6p0','littau-1993-si-aerosol-2p0'},'Only phase-supported formulations bound')
check(entry['referenceOnly'] and not entry['trainingEligible'] and not entry['measuredSampleStructure'],'Registry reference-only gates')
for model in [unit,finite]:
 check(model['evidence_type']=='illustrative' and not model['training_eligible'] and not model['measured_sample_structure'],'Model not measured or training label')
check(all(a['role']=='illustrative' and a['sample_id'] is None and not a['eligible_as_measured_label'] for assets in read(B/'proposed-record-structure-assets.json')['record_structure_assets'].values() for a in assets),'Proposed record assets excluded from measured supervision')
for p in [B/'registry-additions.json',B/'provenance.json',B/'proposed-record-structure-assets.json',*list((B/'models').glob('*.json'))]:
 check(not re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]|file://',p.read_text(encoding='utf-8')),p.name+' public metadata has no machine path')

# Scientific orthographic previews of the exact generated coordinates.
def project(p):
 x,y,z=p;return (.940*x-.342*y,.220*x+.604*y-.766*z,.262*x+.720*y+.643*z)
def preview(atoms,path,title,subtitle,cell_edges=None):
 pp=[project([a[k] for k in ['x','y','z']]) for a in atoms]
 all_bounds=pp+([project([e[which][k] for k in ['x','y','z']]) for e in cell_edges for which in ['start','end']] if cell_edges else [])
 xs=[p[0] for p in all_bounds];ys=[p[1] for p in all_bounds]
 size=max(max(xs)-min(xs),max(ys)-min(ys));scale=450/size;cx=(max(xs)+min(xs))/2;cy=(max(ys)+min(ys))/2
 def point(p):q=project(p);return 420+(q[0]-cx)*scale,320+(q[1]-cy)*scale,q[2]
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="840" height="620" viewBox="0 0 840 620"><rect width="840" height="620" fill="#f7faff"/>'
 svg+='<text x="420" y="35" text-anchor="middle" font-family="Arial" font-size="23" fill="#203d52">'+html.escape(title)+'</text>'
 svg+='<text x="420" y="61" text-anchor="middle" font-family="Arial" font-size="15" fill="#456376">'+html.escape(subtitle)+'</text>'
 if cell_edges:
  for e in cell_edges:
   a=point([e['start'][k] for k in ['x','y','z']]);b=point([e['end'][k] for k in ['x','y','z']])
   svg+=f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" stroke="#92a8b6" stroke-width="1.5"/>'
 for i,a in enumerate(atoms):
  for j in a['bonds']:
   if j>=i:continue
   p=point([a[k] for k in ['x','y','z']]);q=point([atoms[j][k] for k in ['x','y','z']])
   opacity=.22 if a.get('isPeriodicImage') or atoms[j].get('isPeriodicImage') else .55
   svg+=f'<line x1="{p[0]:.2f}" y1="{p[1]:.2f}" x2="{q[0]:.2f}" y2="{q[1]:.2f}" stroke="#67859b" stroke-opacity="{opacity}" stroke-width="1.5"/>'
 for i in sorted(range(len(atoms)),key=lambda i:pp[i][2]):
  a=atoms[i];p=point([a[k] for k in ['x','y','z']]);opacity=.30 if a.get('isPeriodicImage') else .94;r=.37*scale
  svg+=f'<circle cx="{p[0]:.2f}" cy="{p[1]:.2f}" r="{r:.2f}" fill="#6b95b3" fill-opacity="{opacity}" stroke="#355b76" stroke-opacity="{opacity}" stroke-width=".5"/>'
 svg+='<text x="420" y="599" text-anchor="middle" font-family="Arial" font-size="15" fill="#456376">Illustrative generated geometry · no oxide shell or experimental atomic coordinates</text></svg>'
 path.write_text(svg,encoding='utf-8');doc=pymupdf.open(stream=svg.encode(),filetype='svg');doc[0].get_pixmap(alpha=False).save(str(path.with_suffix('.png')))
preview(context,B/'review/unit-cell-periodic-context.svg','Ideal diamond-Si reference cell','8 cell sites; faint markers are periodic neighbors; a = 5.43 Å',unit['unitCellEdges'])
preview(aa,B/'review/finite-sphere.svg','Illustrative silicon lattice crop','Chosen 3 nm spherical envelope · 705 ideal Si sites · not a measured particle')
report={'status':'passed' if not errors else 'failed','checks':checks,'errors':errors,'gemmiVersion':gemmi.__version__,
 'unitCell':{'sites':8,'spaceGroupNumber':227,'originChoice':1,'nearestNeighborsPerSite':4,'nearestNeighborAngstrom':target,'periodicEdges':16,'contextAtoms':len(context)},
 'finiteParticle':{'atoms':len(aa),'nearestNeighborEdges':len(finite['bonds']),'connected':len(visited)==len(aa),
 'envelopeDiameterNm':3.0,'maximumAtomCenterSpanNm':max_diameter/10,'maximumCenterRadiusNm':max(math.sqrt(sum(v*v for v in p)) for p in positions)/10,
 'coordinationHistogram':dict(sorted(collections.Counter(len(a['bonds']) for a in aa).items()))},
 'cifRoundTrips':roundtrips,'visualReview':'pending inspection of generated scientific previews; no Site/browser test',
 'limits':['This validates an ideal geometry, not the structure of a measured specimen.','All size/shape choices of the finite crop are illustrative.']}
dump(B/'validation.json',report)
print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(bool(errors))
