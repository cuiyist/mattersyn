"""Independent read-only candidate validation; writes only this auditor's reports."""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction
from itertools import product, combinations
from collections import Counter, defaultdict
import json, math, re, sys, hashlib
sys.dont_write_bytecode=True
sys.path.insert(0,r'[local path redacted]')
import gemmi

C=Path(__file__).resolve().parent; H=C.parent
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[];bound={};findings=[]
def check(label,ok,detail=None):
    checks.append({'check':label,'passed':bool(ok),**({'detail':detail} if detail is not None else {})})
    if not ok:findings.append({'id':f'check-{len(checks)}','severity':'required_correction','summary':label,'detail':detail})
def bind(p,h=None):
    p=Path(p).resolve();v=sha(p);bound[str(p)]=v
    if h:check('SHA256 '+str(p),v==h)
    return v
freeze=load(C/'package-freeze.json')
bind(C/'package-freeze.json','fef2f3fd8416b0b57f05f7223b04c53634964aed3fd628e50f0aca27af676df0')
for x in freeze['files']:bind(x['path'],x['sha256'])
tab=load(H/'main-tables.json'); author=load(C/'author-validation.json'); model=load(C/'average-model.json')
inv=load(H/'source-inventory.json'); source_audit=load(H/'source-scientific-audit.json')
for p in [H/'source-inventory.json',H/'main-table-assets.json',H/'source-facts.json',H/'main-03.txt',H/'main-05.txt',H/'main-06.txt',H/'main-07.txt']:bind(p)
for d in inv['source_documents'].values():bind(d['path'],d['sha256'])
assets=load(H/'main-table-assets.json')
for n in [1,2,3]:
    asset=next(x for x in assets['assets'] if x['table_number']==n)
    bind(H/f'reader-assets/main-table-{n}.png',asset['sha256'])
    check('Table '+str(n)+' image bound to actual main PDF and original crop',asset['source_sha256']==inv['source_documents']['main']['sha256'] and asset['kind']=='original_table_crop' and asset['caption_and_footnotes_included'])
for item in source_audit['audited_artifacts']:
    if Path(item['path']).name in ['main-tables.json','source-facts.json','source-inventory.json','main-table-assets.json']:bind(item['path'],item['sha256'])

# Independent manual reading of original Table 2: no author-generated coordinates used as ground truth.
# label, Wyckoff multiplicity/letter, x/y/z printed tokens, U11/U22/U33/U12/U13/U23 printed values, fixed cell count.
manual=[
 ('T',192,'i',['-5168(8)','12413(8)','3640(7)'],[108,68,90,-23,-11,-1],192),
 ('O1',96,'h',['-10116(20)','0','10116(20)'],[210,184,210,-71,31,-71],96),
 ('O2',96,'g',['26(24)','26(24)','14727(29)'],[193,193,189,6,6,56],96),
 ('O3',96,'g',['-2337(28)','7097(19)','7097(19)'],[122,143,143,-3,27,27],96),
 ('O4',96,'g',['7826(22)','7826(22)','31976(29)'],[197,197,154,40,40,50],96),
 ('InU',8,'a',['12500','12500','12500'],[146,146,146,0,0,0],8),
 ('InIp',32,'e',['6289(3)','6289(3)','6289(3)'],[159,159,159,-18,-18,-18],32),
 ('InII',32,'e',['25149(5)','25149(5)','25149(5)'],[271,271,271,-23,-23,-23],25),
 ('InIIa',32,'e',['23480(194)','23480(194)','23480(194)'],[295,295,295,229,229,229],1),
]
source_labels=['(Si,Al)','O(1)','O(2)','O(3)','O(4)','In(U)','In(I′)','In(II)','In(IIa)']
def token(t):
    m=re.fullmatch(r'(-?\d+(?:\.\d+)?)(?:\((\d+)\))?',t);assert m,t
    value=Fraction(m[1]); esd=Fraction(int(m[2]),10**len(m[1].split('.')[1])) if m[2] and '.' in m[1] else Fraction(int(m[2])) if m[2] else None
    return value,esd
raw_xyz={r[0]:[token(t)[0]/100000 for t in r[3]] for r in manual}
cifpath=C/'heo2003-average-position-occupancy.cif';block=gemmi.cif.read(str(cifpath)).sole_block()
def scalar(k):return gemmi.cif.as_string(block.find_value(k))
def column(k):return [gemmi.cif.as_string(x) for x in block.find_loop(k)]
check('CIF parses as a single block',bool(block.name))
for key in ['a','b','c']:check('Cell '+key+' source value and ESD',scalar('_cell_length_'+key)=='24.942(4)')
for key in ['alpha','beta','gamma']:check('Cubic symmetry-derived cell angle '+key,scalar('_cell_angle_'+key)=='90')
check('Ambient measurement temperature, not synthesis temperature',scalar('_diffrn_ambient_temperature')=='294')
check('CIF Hall, H-M and number consistent with origin choice 2',scalar('_space_group_name_Hall')=='-F 4vw 2vw 3' and scalar('_space_group_name_H-M_alt')=='F d -3 m:2' and scalar('_space_group_IT_number')=='227')
check('CIF formula is average conventional-cell composition',scalar('_chemical_formula_sum')=='Al96 In66 O384 Si96' and scalar('_cell_formula_units_Z')=='1')

# Parse actual CIF symmetry strings into rational affine operations independently of the author expansion.
def parse_op(s):
    matrix=[];offset=[]
    for expr in s.split(','):
        v=[0,0,0];shift=Fraction(0)
        for term in re.findall(r'[+-]?[^+-]+',expr):
            if any(c in term for c in 'xyz'):
                m=re.fullmatch(r'([+-]?)([xyz])',term);assert m,term
                v['xyz'.index(m[2])]= -1 if m[1]=='-' else 1
            else:shift+=Fraction(term)
        matrix.append(v);offset.append(shift)
    return matrix,offset
opstrings=column('_space_group_symop_operation_xyz');ops=[parse_op(s) for s in opstrings]
check('192 unique explicit CIF symmetry operations',len(ops)==192 and len(set(opstrings))==192)
check('Explicit operation set agrees with independent Gemmi group database',set(opstrings)=={x.triplet() for x in gemmi.find_spacegroup_by_name('F d -3 m:2').operations()})
def apply(op,p):
    m,v=op;return tuple((sum(Fraction(m[i][j])*p[j] for j in range(3))+v[i])%1 for i in range(3))
def orbit(p,ops=ops):return sorted({apply(o,p) for o in ops})
orbits={k:orbit(v) for k,v in raw_xyz.items()}
origin_results=[]
for choice in [1,2]:
    altops=[parse_op(o.triplet()) for o in gemmi.find_spacegroup_by_name(f'F d -3 m:{choice}').operations()]
    counts={r[0]:len(orbit(raw_xyz[r[0]],altops)) for r in manual}
    origin_results.append({'origin_choice':choice,'counts':counts,'all_multiplicities_match':all(counts[r[0]]==r[1] for r in manual)})
check('Only origin 2 reproduces all nine source multiplicities',[x['origin_choice'] for x in origin_results if x['all_multiplicities_match']]==[2])
headers=['label','type_symbol','symmetry_multiplicity','Wyckoff_symbol','fract_x','fract_y','fract_z','occupancy']
cols={h:column('_atom_site_'+h) for h in headers};cifrows={x['label']:x for x in [dict(zip(headers,v)) for v in zip(*(cols[h] for h in headers))]}
check('Ten asymmetric species rows for nine source positions',len(cifrows)==10)
expected_counts=Counter(); expanded=[]
for i,(name,mult,wyck,toks,us,fixed) in enumerate(manual):
    check(name+' orbit multiplicity from explicit operations',len(orbits[name])==mult)
    species=[('TSi','Si',Fraction(1,2)),('TAl','Al',Fraction(1,2))] if name=='T' else [(name,'O' if name.startswith('O') else 'In',Fraction(fixed,mult))]
    for label,element,occ in species:
        r=cifrows[label]
        check(label+' identity, multiplicity and Wyckoff',r['type_symbol']==element and int(r['symmetry_multiplicity'])==mult and r['Wyckoff_symbol']==wyck)
        check(label+' fixed occupancy conversion',Fraction(r['occupancy'])==occ)
        expected_counts[element]+=occ*mult
        for j,key in enumerate(['fract_x','fract_y','fract_z']):
            v,e=token(r[key]); sv,se=token(toks[j]);check(label+' '+key+' exact source coordinate and ESD',v==sv/100000 and e==(se/100000 if se is not None else None))
    q=tab['tables'][1]['rows'][i]['quantities']
    check(name+' source-table coordinate data matches independent visual reading',all(abs(q[k]['value']-float(raw_xyz[name][j]))<1e-12 for j,k in enumerate(['x','y','z'])))
    check(name+' literal tensor data matches independent visual reading',all(abs(q[k]['value']-us[j]/10000)<1e-12 for j,k in enumerate(['U11','U22','U33','U12','U13','U23'])))
    for xyz in orbits[name]:expanded.append((source_labels[i],tuple(float(v) for v in xyz)))
check('Weighted cell content Si96 Al96 O384 In66',dict(expected_counts)=={'Si':96,'Al':96,'O':384,'In':66})
check('680 distinct positions, 642 occupancy-weighted atoms',len(expanded)==680 and len({x[1] for x in expanded})==680 and sum(expected_counts.values())==642)
actual={(x['source_label'],tuple(round(v,8) for v in x['fractional'])) for x in model['fractionalSites']}
expected={(label,tuple(round(v,8) for v in xyz)) for label,xyz in expanded}
check('All JSON expanded coordinates equal independent explicit-CIF expansion',actual==expected and len(model['fractionalSites'])==680)
for x in model['fractionalSites']:
    row=manual[source_labels.index(x['source_label'])];name,mult,_,_,_,fixed=row
    expected_components=[('Si',.5),('Al',.5)] if name=='T' else [('O' if name.startswith('O') else 'In',fixed/mult)]
    check(x['id']+' components, grouped mixture and occupancy',[(y['element'],y['occupancy']) for y in x['components']]==expected_components and x['mixed']==(name=='T') and abs(x['occupancy_sum']-sum(z[1] for z in expected_components))<1e-12)
    check(x['id']+' finite Cartesian Angstrom coordinates',all(math.isfinite(v) and abs(v-f*24.942)<1e-10 for v,f in zip(x['cartesian'],x['fractional'])))
parsed=gemmi.make_small_structure_from_block(block)
parsecounts=Counter()
for x in parsed.get_all_unit_cell_sites():parsecounts[x.element.name]+=x.occ
check('Independent CIF parser expands to correct weighted species counts',dict(parsecounts)==dict(expected_counts))
check('872 species components are not claimed as 872 full atoms',len(parsed.get_all_unit_cell_sites())==872 and author['site_components']==872 and author['expanded_positions']==680)

# Independent source Table 3 reading, all 23 values, with one-ESD classification (not author's 3-ESD pass flag).
grows=[
 ('T','O1',1.636,.003),('T','O2',1.681,.004),('T','O3',1.732,.004),('T','O4',1.644,.003),('mean',1.673,.004),
 ('InIp','O3',2.170,.007),('InII','O2',2.600,.007),('InIIa','O2',2.246,.032),
 ('T','O1','T',146.8,.5),('T','O2','T',135.2,.5),('T','O3','T',126.6,.4),('T','O4','T',147.4,.5),
 ('O1','T','O2',113.9,.3),('O1','T','O3',108.4,.3),('O1','T','O4',113.5,.4),('O2','T','O3',102.5,.3),('O2','T','O4',107.8,.4),('O3','T','O4',110.5,.4),
 ('InU','InIp',2.6831,.0013),('InIp','InU','InIp',109.47,None),('O2','InII','O2',88.1,.3),('O2','InIIa','O2',111.7,2.0),('O3','InIp','O3',100.10,.23)]
def norm(v):return math.sqrt(sum(float(x)**2 for x in v))
def neighbor_vectors(center,other):
    c=raw_xyz[center]; found=[]
    for p in orbits[other]:
        d=[p[j]-c[j] for j in range(3)]
        d=[v-Fraction(math.floor(v+Fraction(1,2))) for v in d]
        if norm(d)>1e-10:found.append(tuple(float(v)*24.942 for v in d))
    low=min(norm(v) for v in found)
    return [v for v in found if abs(norm(v)-low)<1e-8],low
def angle(u,v):return math.degrees(math.acos(max(-1,min(1,sum(a*b for a,b in zip(u,v))/norm(u)/norm(v)))))
geometry=[]
for idx,row in enumerate(grows):
    value,esd=row[-2:];names=row[:-2];unit='degree' if len(names)==3 else 'angstrom'
    if names==('mean',):calc=sum(neighbor_vectors('T',f'O{i}')[1] for i in [1,2,3,4])/4
    elif len(names)==2:calc=neighbor_vectors(*names)[1]
    else:
        left,center,right=names;uv,_=neighbor_vectors(center,left);vv,_=neighbor_vectors(center,right)
        av=[angle(u,v) for u in uv for v in vv if norm([a-b for a,b in zip(u,v)])>1e-8]
        check('Table 3 row '+str(idx+1)+' nearest-shell angle is unambiguous',max(av)-min(av)<1e-8)
        calc=sum(av)/len(av)
    diff=calc-value;z=abs(diff)/esd if esd else None
    geometry.append({'row':idx+1,'labels':list(names),'calculated_from_published_coordinate_central_values':calc,'source_central_value':value,'source_esd':esd,'unit':unit,'signed_difference':diff,'absolute_difference_over_reported_esd':z,'within_one_reported_esd':abs(diff)<=esd if esd else None,'within_three_reported_esd':abs(diff)<=3*esd if esd else None,'symmetry_fixed_rounding_check':abs(diff)<=.005 if esd is None else None})
    check('Table 3 row '+str(idx+1)+' independent calculation agrees with author numerical result',abs(calc-author['table3_geometry_checks'][idx]['calculated'])<1e-8)
check('22 of 23 central geometries agree within one source ESD or symmetry rounding',sum(x['within_one_reported_esd'] is True or x['symmetry_fixed_rounding_check'] is True for x in geometry)==22)
outliers=[x for x in geometry if x['absolute_difference_over_reported_esd'] is not None and x['absolute_difference_over_reported_esd']>1]
check('The only >1 ESD discrepancy is O2–InIIa–O2',len(outliers)==1 and outliers[0]['labels']==['O2','InIIa','O2'])

# Reproduce source-literal ADP positive-definiteness and invariance under the actual coordinate stabilizer.
def transpose(m):return list(zip(*m))
def multiply(a,b):return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def determinant(m):return m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])-m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0])
adps=[]
for i,(name,mult,w,tokens,u,n) in enumerate(manual):
    matrix=[[Fraction(u[0],10000),Fraction(u[3],10000),Fraction(u[4],10000)],[Fraction(u[3],10000),Fraction(u[1],10000),Fraction(u[5],10000)],[Fraction(u[4],10000),Fraction(u[5],10000),Fraction(u[2],10000)]]
    stabilizers=[op for op in ops if apply(op,raw_xyz[name])==tuple(x%1 for x in raw_xyz[name])]
    residuals=[]
    for rot,_ in stabilizers:
        v=multiply(multiply(rot,matrix),transpose(rot));residuals.append(max(abs(v[i][j]-matrix[i][j]) for i in range(3) for j in range(3)))
    minors=[matrix[0][0],matrix[0][0]*matrix[1][1]-matrix[0][1]**2,determinant(matrix)]
    check(name+' ADP diagnostic reproduced independently',all(v>0 for v in minors) and len(stabilizers)==author['source_tensor_diagnostics'][i]['stabilizer_operations'] and abs(float(max(residuals))-author['source_tensor_diagnostics'][i]['max_exact_site_symmetry_residual_A2'])<1e-12)
    adps.append({'source_label':source_labels[i],'positive_definite':all(v>0 for v in minors),'stabilizer_count':len(stabilizers),'exact_site_symmetry_residual_A2':float(max(residuals)),'source_literal_values_preserved':True})
check('Exactly three oxygen literal tensors violate exact stabilizer invariance',[x['source_label'] for x in adps if x['exact_site_symmetry_residual_A2']>0]==['O(2)','O(3)','O(4)'])
text=cifpath.read_text(encoding='utf-8');notes='\n'.join(model['notes'])
check('CIF explicitly omits ADPs and contains no invented isotropic or anisotropic values','_atom_site_aniso_' not in text and '_atom_site_U_iso_or_equiv' not in text and '_atom_site_B_iso_or_equiv' not in text and 'positions and occupancies only' in text and 'source-literal anisotropic tensors' in text)
for key in ['unique_ordered_microstate','exact_structure_recipe_eligible','dft_input_eligible','training_approved']:check('Model limitation '+key,model[key] is False)
check('Both CIF and model label curator-derived source-average model, not author supplied','curator-generated position/occupancy CIF' in text and 'not an author-supplied CIF' in text and 'curator-generated position/occupancy CIF' in notes)
check('Nominal framework conflict, disorder and unmodeled chemistry retained',all(x in text for x in ['Si96Al96','Si100Al92','partially occupied','charge compensation','No oxidation states, sulfur positions','not a replacement for the full diffraction/refinement dataset']))
check('No reflection-data substitution for coordinates','_refln_' not in text and 'calculated reflection intensities' in text)
minimum_split=neighbor_vectors('InII','InIIa')[1]

findings.append({'id':'G1','severity':'required_metadata_correction','summary':'Table 3 low-occupancy In(IIa) angle has an unresolved central-value discrepancy hidden by a broad three-ESD pass label.','source':'main Table 3, O(2)–In(IIa)–O(2), 111.7(20) degrees','evidence':outliers[0],'required_change':'Preserve all original coordinates and table values. Add this explicit source/candidate geometric discrepancy to model/CIF limitations and author-validation summary; label the acceptance criterion as three reported ESD rather than implying exact central-value or one-ESD agreement for all 23 geometries. Keep the 22 close matches distinct from this one tension.','scientific_disposition':'No coordinate repair or source-value correction is justified by this audit. Position/occupancy transcription and average setting remain supported; exact local angle is not resolved.'})
bind(__file__)
for p,h in list(bound.items()):check('Input unchanged at audit end: '+p,sha(p)==h)
result={'schema':'mattersyn-independent-average-structure-audit/1','created_at':datetime.now(timezone.utc).isoformat(),'author':'/root','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','independent':True,
 'status':'pending_narrow_geometry_discrepancy_label_correction','scope':'Independent scientific and numerical audit of the original frozen private position/occupancy candidate. Not a new full-source, full SI, DFT, exact-recipe, renderer or publication audit.',
 'counts':{'mechanical_checks':len(checks),'failed_mechanical_checks':sum(not x['passed'] for x in checks),'open_findings':len(findings),'source_atomic_rows':9,'cif_asymmetric_species_rows':10,'symmetry_operations':192,'expanded_positions':680,'species_components':872,'occupancy_weighted_atoms':642,'table3_geometries':23,'within_one_ESD_or_symmetry_rounding':22,'greater_than_one_ESD':1,'ADP_tensors_reviewed':9,'literal_ADP_exact_symmetry_inconsistencies':3,'bound_files':len(bound)},
 'manual_review':['Actually viewed original Table 1 image: selected/alternative space groups, lattice constant and ESD, measurement temperature and source-condition differences.','Actually viewed all nine Table 2 rows and footnotes: manually entered xyz/ESD, multiplicities, fixed occupancies and six Uij entries; checked final versus varied columns and mixed-Si/Al footnote.','Actually viewed all 23 Table 3 entries and footnotes, manually entered values/ESDs and compared independent nearest-neighbor geometry.','Read candidate builder, CIF provenance/limitation text, JSON grouping and author diagnostics; did not run the author builder. Prior source scientific audit is a dependency, not this candidate approval.'],
 'independent_method':'Gemmi 0.7.5 used only for CIF parsing and standard-setting comparison. Explicit CIF affine symmetry strings were separately parsed with Fraction arithmetic; all orbits, source comparisons, periodic Cartesian nearest neighbors, angles and ADP stabilizer transformations were computed by this independent script from manually read source tokens, without importing or executing author code.',
 'origin_checks':origin_results,'geometry_checks':geometry,'geometry_ESD_normalization_note':'Residual divided by the reported Table 3 angle/distance ESD only; this is not a propagated coordinate-covariance uncertainty, a new experimental fit or a statistical probability of source error.','ADP_checks':adps,'weighted_counts':{k:float(v) for k,v in expected_counts.items()},'open_findings':findings,'checks':checks,'bound_files':bound,
 'retained_limits':['An average position/occupancy CIF can preserve experimentally refined positions without supplying an ordered microscopic model. All training and DFT eligibility remains false.','Si96/Al96 is the source average refinement model, not a resolution of nominal Si100/Al92.','CIF omits all ADPs deliberately; exact source-literal O2/O3/O4 tensor invariance issues remain unresolved, not repaired. Positive-definite tensors are not automatically symmetry-compatible.','680 positions and 872 colocated species components represent 642 occupancy-weighted atoms; neither raw count is an ordered atom population.',f'In(II)/In(IIa) split-site nearest separation is {minimum_split:.8f} Å. Partly occupied positions cannot be interpreted as simultaneous fully occupied bonded atoms; local correlations remain unknown.','No oxidization-state/charge balance, sulfur or extra-ligand coordinates, oxygen vacancies or H sites are validated. No refinement intensities are regenerated.','Full SI completion and reflection sign uncertainties are separate; reflections do not become coordinates.'],
 'candidate_files_modified':False,'source_files_modified':False,'site_modified':False,'ledger_modified':False,'memory_modified':False,'github_modified':False,'training_approved':False,'dft_approved':False,'publication_approved':False}
(C/'independent-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=f'''# Independent Heo average-model audit

Status: **pending one narrow metadata correction**. Author: `/root`; independent reviewer: `/root/backlog_eta`.

The original frozen position/occupancy candidate agrees with all nine visually read Table 2 rows, their coordinate uncertainties and final fixed occupancies. Explicit symmetry reproduces origin choice 2, all nine multiplicities, 680 distinct positions, 872 species components and weighted Si96 Al96 O384 In66 (642 atoms). Si/Al are correctly grouped as coincident 0.5 components; 25/32 and 1/32 indium occupancies are retained. Source-average, curator-derived, non-ordered, non-DFT and non-training labels are present.

All 23 Table 3 geometries were independently calculated from the source coordinate central values. **22 agree within one reported ESD or symmetry rounding.** O(2)–In(IIa)–O(2) gives **107.160199° versus 111.7(20)°**, a **−4.539801° difference, 2.269900 reported ESD**. The author's three-ESD threshold accepts it but does not establish central-value agreement. Required correction: state this discrepancy in the CIF/model limitations and author-validation summary, explicitly name the three-ESD criterion, and preserve all source numbers and coordinates unchanged.

All nine literal U tensors are positive definite, but O(2), O(3) and O(4) violate exact site-symmetry invariance by 0.005, 0.003 and 0.001 Å² respectively. These diagnostics reproduce independently. The CIF's deliberate omission of all ADPs is honestly labeled; it cannot be called a full reproduction of the authors' refinement or used to claim reproduced reflection intensities. No silent tensor permutation is approved.

The near In(II)/In(IIa) split-site separation ({minimum_split:.8f} Å) is not a simultaneous pair of fully occupied atoms. Local occupation correlations, ordered Si/Al positions, microscopic charge balance, sulfur/H/defect sites and DFT inputs remain unresolved. Recipe-condition conflicts still preclude exact structure–recipe admission.

Actual manual scope: original Table 1, all nine Table 2 rows/footnotes, all 23 Table 3 entries/footnotes, candidate provenance and omission labels. Mechanical scope: {len(checks)} checks; {sum(not x['passed'] for x in checks)} failed; {len(bound)} exact file bindings. The JSON records per-entry ESD residuals, origin checks, ADP diagnostics and the single required correction. Source files and all candidate bytes remain untouched. No full SI, browser, Site, training or publication approval is issued.
'''
(C/'independent-audit.md').write_text(md,encoding='utf-8')
print(json.dumps({'status':result['status'],'counts':result['counts'],'findings':[x['summary'] for x in findings],'json_sha256':sha(C/'independent-audit.json'),'md_sha256':sha(C/'independent-audit.md')},indent=2))
