"""Private position/occupancy model from audited Tables1–2; no ordered microstate or training admission."""
from pathlib import Path
from datetime import datetime,timezone
from itertools import combinations
import hashlib,json,math,re,sys
sys.dont_write_bytecode=True
sys.path.insert(0,r'[local path redacted]')
import gemmi
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'structure-candidate';OUT.mkdir(exist_ok=True)
if (OUT/'package-freeze.json').exists():
    archive=ROOT/'structure-candidate-revision-1'
    if '--revise-after-archive' not in sys.argv or any(
        not (archive/p.name).is_file() or (archive/p.name).read_bytes()!=p.read_bytes()
        for p in OUT.iterdir() if p.is_file() and p.name in
        {'package-freeze.json','average-model.json','author-validation.json','heo2003-average-position-occupancy.cif'}):
        raise SystemExit('Preserve and explicitly reopen the frozen candidate before rebuilding.')
def binding(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
data=json.loads((ROOT/'main-tables.json').read_text(encoding='utf8'))
table1,table2,table3=data['tables'][:3]
rows=table2['rows']; a=next(r for r in table1['shared_rows'] if r['row_id']=='lattice-a')['quantities']['a0']['value']
def coordinate(row):return [row['quantities'][k]['value'] for k in ('x','y','z')]
def modulo(v):return tuple(round(float(x)%1,8)%1 for x in v)
def orbit(row,sg):return sorted({modulo(op.apply_to_xyz(coordinate(row))) for op in sg.operations()})
setting_probes=[]
for name in ('F d -3 m:1','F d -3 m:2'):
    sg=gemmi.find_spacegroup_by_name(name)
    counts=[{'label':r['atom_label'],'calculated':len(orbit(r,sg)),'source_multiplicity':r['wyckoff']['multiplicity']} for r in rows]
    setting_probes.append({'name':sg.xhm(),'hall':sg.hall,'multiplicities':counts,
        'all_source_multiplicities_match':all(c['calculated']==c['source_multiplicity'] for c in counts)})
assert [p['name'] for p in setting_probes if p['all_source_multiplicities_match']]==['F d -3 m:2']
sg=gemmi.find_spacegroup_by_name('F d -3 m:2')
orbits={r['atom_label']:orbit(r,sg) for r in rows};origin={r['atom_label']:coordinate(r) for r in rows}
def norm(v):return math.sqrt(sum(x*x for x in v))
def subtract(v,w):return [x-y for x,y in zip(v,w)]
def transpose(m):return [list(row) for row in zip(*m)]
def matmul(m,n):return [[sum(m[i][k]*n[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def nearest_vectors(center,label):
    delta=[[v-round(v) for v in subtract(x,center)] for x in orbits[label]]
    lengths=[norm(v)*a for v in delta];minimum=min(v for v in lengths if v>1e-5)
    return [[x*a for x in v] for v,d in zip(delta,lengths) if abs(d-minimum)<1e-6],minimum
def angle(v,w):return math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(v,w))/norm(v)/norm(w)))))
geometry=[]
for block in table3['blocks']:
    for row in block['rows']:
        label=row['raw_cells'][0];q=row['quantity'];parts=label.split('–')
        if label=='mean of (Si,Al)–O':
            calculated=sum(nearest_vectors(origin['(Si,Al)'],f'O({i})')[1] for i in range(1,5))/4
        elif len(parts)==2:
            calculated=nearest_vectors(origin[parts[0]],parts[1])[1]
        else:
            left,center,right=parts;v,_=nearest_vectors(origin[center],left);w,_=nearest_vectors(origin[center],right)
            values=[angle(x,y) for x in v for y in w if norm(subtract(x,y))>1e-6]
            assert values and max(values)-min(values)<1e-5,(label,values)
            calculated=sum(values)/len(values)
        reported=q['value'];uncertainty=(q.get('uncertainty') or {}).get('value')
        rounding_tolerance=0.006 if q['unit']=='degree' else 0.0006
        tolerance=max(3*(uncertainty or 0),rounding_tolerance)
        geometry.append({'label':label,'calculated':calculated,'source_value':reported,'source_raw':row['raw_cells'][1],
            'unit':q['unit'],'absolute_difference':abs(calculated-reported),'signed_difference':calculated-reported,
            'source_reported_esd':uncertainty,'absolute_deviation_in_source_esd':abs(calculated-reported)/uncertainty if uncertainty else None,
            'tolerance':tolerance,'tolerance_policy':'Three reported Table3 ESDs or printed-coordinate rounding allowance, whichever is larger; not exact central-value reproduction or propagated coordinate uncertainty.',
            'within_one_reported_esd_or_rounding':abs(calculated-reported)<=max(uncertainty or 0,rounding_tolerance),
            'within_three_reported_esds_or_rounding':abs(calculated-reported)<=tolerance})
assert all(g['within_three_reported_esds_or_rounding'] for g in geometry)
geometry_tensions=[g for g in geometry if not g['within_one_reported_esd_or_rounding']]

# Literal tensors are retained and diagnosed; no permutation is introduced to force symmetry.
tensor_checks=[]
for row in rows:
    q=row['quantities'];u=[[q['U11']['value'],q['U12']['value'],q['U13']['value']],
        [q['U12']['value'],q['U22']['value'],q['U23']['value']],
        [q['U13']['value'],q['U23']['value'],q['U33']['value']]]
    changes=[];stabilizers=0
    for op in sg.operations():
        d=[v-round(v) for v in subtract(op.apply_to_xyz(coordinate(row)),coordinate(row))]
        if max(abs(v) for v in d)<1e-7:
            stabilizers+=1;r=[[v/op.DEN for v in line] for line in op.rot]
            transformed=matmul(matmul(r,u),transpose(r))
            changes.append(max(abs(transformed[i][j]-u[i][j]) for i in range(3) for j in range(3)))
    minors=[u[0][0],u[0][0]*u[1][1]-u[0][1]**2,
        u[0][0]*(u[1][1]*u[2][2]-u[1][2]**2)-u[0][1]*(u[0][1]*u[2][2]-u[1][2]*u[0][2])+u[0][2]*(u[0][1]*u[1][2]-u[1][1]*u[0][2])]
    tensor_checks.append({'label':row['atom_label'],'source_pointer':f"/tables/1/rows/{rows.index(row)}/quantities",
        'literal_U_cartesian_cubic_axes_A2':u,'leading_principal_minors':minors,'positive_definite':all(v>0 for v in minors),
        'stabilizer_operations':stabilizers,'max_exact_site_symmetry_residual_A2':max(changes),
        'exact_site_symmetry_consistent':max(changes)<1e-10,
        'source_values_changed':False})

notes=[
    'This is a curator-generated position/occupancy CIF transcribed from Tables1–2, not an author-supplied CIF.',
    'Fd-3m origin choice 2 is resolved by the printed Wyckoff labels and coordinates; all nine multiplicities and all 23 Table 3 geometries are independently testable.',
    'One central-value geometry discrepancy remains: O(2)-In(IIa)-O(2) calculated from the printed coordinates is 107.1602 degrees, while Table 3 reports 111.7(20) degrees, a difference of 4.5398 degrees or 2.27 reported ESDs. The other 22 Table 3 geometries agree within one reported ESD or printed-coordinate rounding. The broad screening threshold of three ESDs does not resolve this discrepancy; source coordinates and angle are both retained unchanged.',
    'Final fixed occupancies belong to the reported final coordinate model. Earlier freely varied occupancies are retained separately in the main-table dataset and are not mixed into this model.',
    'The framework is represented by colocated statistical Si/Al site components of 0.5 each, following Table 2 footnote c. This is the averaged Si96Al96 model, not a resolution of nominal Si100Al92.',
    'In(II) and In(IIa) remain partially occupied sites. They do not establish a simultaneous ordered microscopic arrangement, local cluster statistics or charge compensation.',
    'No oxidation states, sulfur positions, counterions, ligands, defects or missing atoms are invented.',
    'This CIF deliberately contains positions and occupancies only. The complete source-literal anisotropic tensors remain in the linked main-table JSON; their exact site-symmetry inconsistencies are diagnosed separately without repairing source values.',
    'This geometric export does not reproduce the authors charge-dependent scattering factors, anomalous-dispersion corrections or calculated reflection intensities. It is not a replacement for the full diffraction/refinement dataset.',
    'Source synthesis-condition conflicts remain unresolved. Exact structure-recipe training and ordered DFT input admission remain false.'
]
def cif_coord(row,k):
    q=row['quantities'][k];value=f"{q['value']:.5f}"
    uncertainty=q.get('uncertainty')
    return value+(f"({uncertainty['raw_digits']})" if uncertainty else '')
lines=['data_heo2003_average_position_occupancy',"_audit_creation_method 'MatterSyn transcription from published Tables 1 and 2'",
    "_chemical_name_common 'In66-X average refined position and occupancy model'",
    "_chemical_formula_sum 'Al96 In66 O384 Si96'",'_cell_formula_units_Z 1',
    '_cell_length_a 24.942(4)','_cell_length_b 24.942(4)','_cell_length_c 24.942(4)',
    '_cell_angle_alpha 90','_cell_angle_beta 90','_cell_angle_gamma 90',
    "_space_group_name_H-M_alt 'F d -3 m:2'",f"_space_group_name_Hall '{sg.hall}'",'_space_group_IT_number 227',
    '_diffrn_ambient_temperature 294',"_journal_paper_doi '10.1021/jp0219348'",
    '_publ_section_exptl_refinement',';','\n'.join(notes),';',
    'loop_','_space_group_symop_id','_space_group_symop_operation_xyz']
for i,op in enumerate(sg.operations(),1):lines.append(f"{i} '{op.triplet()}'")
lines+=['loop_','_atom_site_label','_atom_site_type_symbol','_atom_site_symmetry_multiplicity',
    '_atom_site_Wyckoff_symbol','_atom_site_fract_x','_atom_site_fract_y','_atom_site_fract_z','_atom_site_occupancy']
asymmetric=[];expanded=[];totals={}
for i,row in enumerate(rows):
    mult=row['wyckoff']['multiplicity'];count=row['quantities']['occupancy: fixed']['value']
    species=[('Si',0.5),('Al',0.5)] if i==0 else [('O' if row['atom_label'].startswith('O') else 'In',count/mult)]
    site_label=['T','O1','O2','O3','O4','InU','InIp','InII','InIIa'][i]
    for element,occ in species:
        label=site_label+element if i==0 else site_label
        lines.append(' '.join([label,element,str(mult),row['wyckoff']['letter'],*[cif_coord(row,k) for k in ('x','y','z')],f'{occ:.8f}'.rstrip('0').rstrip('.')]))
        asymmetric.append({'cif_label':label,'source_label':row['atom_label'],'element':element,'occupancy':occ,
            'source_row_pointer':f'/tables/1/rows/{i}','fractional':coordinate(row),'multiplicity':mult})
    for j,xyz in enumerate(orbits[row['atom_label']]):
        components=[{'element':e,'occupancy':o,'source_label':row['atom_label']} for e,o in species]
        expanded.append({'id':f'{site_label}-{j+1}','fractional':list(xyz),'cartesian':[v*a for v in xyz],
            'components':components,'occupancy_sum':sum(o for e,o in species),'mixed':len(species)>1,
            'source_label':row['atom_label']})
        for e,o in species:totals[e]=totals.get(e,0)+o
cif=OUT/'heo2003-average-position-occupancy.cif';cif.write_text('\n'.join(lines)+'\n',encoding='utf8')
parsed=gemmi.make_small_structure_from_block(gemmi.cif.read(str(cif)).sole_block())
parsed_counts={}
for site in parsed.get_all_unit_cell_sites():parsed_counts[site.element.name]=parsed_counts.get(site.element.name,0)+site.occ
expected={'Si':96,'Al':96,'O':384,'In':66}
assert all(abs(parsed_counts.get(e,0)-n)<1e-8 for e,n in expected.items()) and set(parsed_counts)==set(expected)
model={'schema':'mattersyn-source-average-refinement-candidate/1','source_id':'heo2003',
    'status':'private_author_candidate_independent_review_pending','source_tables':binding(ROOT/'main-tables.json'),
    'source_main_audit':binding(ROOT/'source-scientific-audit.json'),'cif':binding(cif),'a':a,
    'spaceGroup':'F d -3 m:2','spaceGroupNumber':227,'origin_choice':2,
    'coordinate_scope':'source_refined_average_positions_with_fixed_partial_occupancies',
    'measured_sample_average_refinement':True,'unique_ordered_microstate':False,
    'exact_structure_recipe_eligible':False,'dft_input_eligible':False,'training_approved':False,
    'nominal_framework_source':'Si100Al92O384','refinement_weighted_counts':totals,
    'fractionalSites':expanded,'asymmetric_sites':asymmetric,'notes':notes}
(OUT/'average-model.json').write_text(json.dumps(model,indent=2)+'\n',encoding='utf8')
report={'schema':'mattersyn-average-model-author-validation/1','at':datetime.now(timezone.utc).isoformat(),
    'author':'/root','independent_audit':False,'source_tables':binding(ROOT/'main-tables.json'),
    'parser':'Gemmi '+gemmi.__version__,'setting_probes':setting_probes,'table3_geometry_checks':geometry,
    'source_tensor_diagnostics':tensor_checks,'cif':binding(cif),'parsed_weighted_counts':parsed_counts,
    'expanded_positions':len(expanded),'site_components':len(parsed.get_all_unit_cell_sites()),
    'position_occupancy_validation':'passed','literal_tensor_symmetry':'unresolved_source_inconsistencies_preserved',
    'geometry_summary':{'checked':len(geometry),'within_one_reported_esd_or_rounding':len(geometry)-len(geometry_tensions),
        'within_three_reported_esds_or_rounding':len(geometry),'unresolved_central_value_tensions':geometry_tensions,
        'source_coordinates_or_table_values_changed':False},
    'source_files_modified':False,'public_imported':False,'exact_structure_recipe_eligible':False}
(OUT/'author-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({'position_occupancy_validation':'passed','setting':sg.xhm(),'geometry_checks':len(geometry),
    'weighted_counts':parsed_counts,'positions':len(expanded),'tensor_symmetry_inconsistencies':[t['label'] for t in tensor_checks if not t['exact_site_symmetry_consistent']],
    'independent_audit_pending':True},indent=2))
