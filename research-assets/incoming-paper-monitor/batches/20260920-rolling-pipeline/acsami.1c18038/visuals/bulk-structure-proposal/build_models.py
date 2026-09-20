"""Private source-table reconstruction; never edits canonical/source inputs.
Run with Miniforge Python; cached Gemmi is read-only.
"""
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '[local path redacted]')
sys.path.insert(0, '[local path redacted]')
import gemmi
import numpy as np
import json, hashlib, re, math, itertools
from pathlib import Path
from decimal import Decimal
from collections import Counter

OUT = Path(__file__).resolve().parent
L = OUT.parent.parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p, x): Path(p).write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
tables = {t['id']:t for t in json.loads((L/'source-tables.json').read_text(encoding='utf-8'))['tables']}
checks=[]
def check(name, ok, details=None):
    checks.append({'check':name, 'passed':bool(ok), 'details':details})
    if not ok: raise ValueError(name+': '+str(details))
def scaled_token(c):
    m=re.fullmatch(r'([+-]?\d+(?:\.\d+)?)(?:\((\d+)\))?',c['raw_text'].replace('−','-'))
    if not m: raise ValueError(c)
    v=Decimal(m[1])*Decimal(str(c['printed_to_value_scale']))
    return format(v,'f')+('('+m[2]+')' if m[2] else '')
def angle(a,b,c):
    u=a-b; v=c-b
    return math.degrees(math.acos(np.clip(np.dot(u,v)/np.linalg.norm(u)/np.linalg.norm(v),-1,1)))
limitations=[
 'This is a reconstruction of the published bulk-crystal non-hydrogen tables, not the original crystallographic deposition or a complete crystal model.',
 'Hydrogen coordinates and site occupancies are absent from the supplied tables. No hydrogen sites or occupancy values are inferred. Every site occupancy is null in JSON and ? in the partial CIF.',
 'Symmetry expansion gives geometric position markers only. Their count is not an occupancy-weighted atom count. Nominal composition and Z are reported independently.',
 'The source space-group symbols select standard Gemmi operations. P21/c uses the conventional unique-b setting; the supplied tables do not list the symmetry operators independently.',
 'Printed coordinates, standard uncertainties, Ueq and Uij values are retained. Markers are constant-size spheres, not thermal ellipsoids; ADPs are not used to invent missing atoms.',
 'This bulk A/B model is not a nanocrystal, dried-powder, colloid, film, surface, ligand or DFT model. It is not an exact structure–recipe training pair.',
 'The original crystal ZIP, reflection data and DFT inputs were not locally supplied. Structure comparison does not establish the physical identity of every bulk synthesis batch.',
 'The two independent Sb sites in B remain separate. The source narrative distortion value for B has an unresolved site assignment and is not attached to one chosen Sb centre.'
]
models=[]
for phase,ci,ai,bi,angi,sgname,expected in [('A',6,8,2,4,'P -1',64),('B',7,9,3,5,'P 21/c',144)]:
    meta={r['row_label']:next(c for c in r['cells'] if c['column']==phase) for r in tables['table-s1']['rows']}
    cp={k:meta[k]['value'] for k in ['a','b','c','alpha','beta','gamma']}
    cell=gemmi.UnitCell(*cp.values()); sg=gemmi.SpaceGroup(sgname); ops=list(sg.operations())
    matrix=np.array(cell.orth.mat.tolist())
    a,b,c,al,be,ga=cp.values(); al,be,ga=map(math.radians,[al,be,ga])
    cy=c*(math.cos(al)-math.cos(be)*math.cos(ga))/math.sin(ga)
    independent=np.array([[a,b*math.cos(ga),c*math.cos(be)],[0,b*math.sin(ga),cy],[0,0,math.sqrt(c*c-(c*math.cos(be))**2-cy**2)]])
    check(phase+' independent orthogonalization',np.max(np.abs(matrix-independent))<1e-10)
    coords=tables[f'table-s{ci}']; adps=tables[f'table-s{ai}']; admap={r['row_label']:r for r in adps['rows']}
    sites=[]
    for row in coords['rows']:
        cells={c['column']:c for c in row['cells']}; label=row['row_label']
        f=[cells[k]['value'] for k in ['x','y','z']]; cart=matrix@f
        uc={c['column']:c for c in admap[label]['cells']}
        u={k:v['value'] for k,v in uc.items()}
        ut=np.array([[u['U11'],u['U12'],u['U13']],[u['U12'],u['U22'],u['U23']],[u['U13'],u['U23'],u['U33']]])
        # CIF Uij values are referred to reciprocal-axis lengths in the exponent.
        rec=cell.reciprocal(); d=np.diag([rec.a,rec.b,rec.c]); ucart=matrix@d@ut@d@matrix.T
        ueq_calc=float(np.trace(ucart)/3)
        check(phase+' ADP positive definite '+label,np.linalg.eigvalsh(ucart).min()>0)
        ueq_tol=5*(cells['Ueq']['uncertainty'] or 0)+0.0001
        check(phase+' Ueq agreement '+label,abs(ueq_calc-cells['Ueq']['value'])<=ueq_tol,{'calculated':ueq_calc,'reported':cells['Ueq']['value'],'tolerance':ueq_tol})
        for q in list(cells.values())+list(uc.values()):
            tok=scaled_token(q);check(q['id']+' scaled value',abs(gemmi.cif.as_number(tok)-q['value'])<1e-12)
        sites.append({'id':label,'element':re.match(r'[A-Z][a-z]?',label)[0],'fractional':f,'fractional_su':[cells[k]['uncertainty'] for k in ['x','y','z']], 'cartesian':cart.tolist(),'occupancy':None,'source_coordinate_row':row,'source_adp_row':admap[label],'ueq_reported':cells['Ueq']['value'],'uij_reported':u,'ueq_from_tensor_check':ueq_calc})
    sm={s['id']:s for s in sites}; expanded=[]
    for s in sites:
        for oi,op in enumerate(ops):
            original=op.apply_to_xyz(s['fractional']); shift=[math.floor(v+1e-10) for v in original]; wrapped=[v-n for v,n in zip(original,shift)]
            expanded.append({'id':s['id']+'@'+str(oi+1),'source_label':s['id'],'element':s['element'],'symmetry_operation_id':oi+1,'symmetry_operation':op.triplet(),'unwrapped_fractional':original,'wrapping_translation':[-n for n in shift],'fractional':wrapped,'cartesian':(matrix@wrapped).tolist(),'occupancy':None})
    check(phase+' expanded marker count',len(expanded)==expected)
    mind=1e9; pair=None
    for i,x in enumerate(expanded):
        for y in expanded[:i]:
            df=np.array(x['fractional'])-y['fractional']
            # Exhaustive nearest lattice translation; no orthogonal-cell shortcut.
            dist=min(np.linalg.norm(matrix@(df+v)) for v in itertools.product([-1,0,1],repeat=3))
            if dist<mind:mind=float(dist);pair=[x['id'],y['id']]
    check(phase+' no coincident expanded positions',mind>0.5,{'minimum_A':mind,'pair':pair})
    bonds=[]; angles=[]
    for row in tables[f'table-s{bi}']['rows']:
        labs=row['row_label'].split('–'); q=row['cells'][0]
        calc=float(np.linalg.norm(np.array(sm[labs[0]]['cartesian'])-sm[labs[1]]['cartesian']))
        diff=calc-q['value']; tol=5*(q['uncertainty'] or 0)+0.002
        check(phase+' source bond '+row['row_label'],abs(diff)<=tol,{'difference':diff,'tolerance':tol})
        bonds.append({'sites':labs,'source_row':row,'calculated_A':calc,'difference_A':diff,'qualification_tolerance_A':tol})
    for row in tables[f'table-s{angi}']['rows']:
        labs=row['row_label'].split('–'); q=row['cells'][0]
        calc=angle(*[np.array(sm[k]['cartesian']) for k in labs]);diff=calc-q['value'];tol=5*(q['uncertainty'] or 0)+0.12
        check(phase+' source angle '+row['row_label'],abs(diff)<=tol,{'difference':diff,'tolerance':tol})
        angles.append({'sites':labs,'source_row':row,'calculated_deg':calc,'difference_deg':diff,'qualification_tolerance_deg':tol})
    model={'schema':'mattersyn.source_non_h_bulk_view.v1','id':'lian2021-bulk-'+phase.lower(),'phase':phase,'source_id':'lian2021','source_doi':'10.1021/acsami.1c18038','basis':'source_table_reconstruction','model_scope':'bulk_asymmetric_unit_and_geometric_symmetry_expansion','cell':cp,'cell_cartesian_matrix':matrix.tolist(),'reported_crystal_metadata':meta,'space_group':{'hm':sg.xhm(),'number':sg.number,'hall':sg.hall,'operations':[o.triplet() for o in ops],'operations_basis':'Gemmi '+gemmi.__version__+' standard setting from reported symbol'},'asymmetric_unit_sites':sites,'geometric_cell_positions':expanded,'source_bonds':bonds,'source_angles':angles,'counts':{'listed_non_h_sites':len(sites),'geometric_positions':len(expanded),'listed_elements':dict(Counter(s['element'] for s in sites)),'geometric_elements':dict(Counter(s['element'] for s in expanded)),'occupancy_weighted_atoms':None},'geometry_checks':{'minimum_periodic_separation_A':mind,'minimum_pair':pair,'maximum_bond_difference_A':max(abs(x['difference_A']) for x in bonds),'maximum_angle_difference_deg':max(abs(x['difference_deg']) for x in angles)},'limitations':limitations,'eligibility':{'independent_audit_passed':False,'complete_crystal':False,'measured_structure_training_label':False,'exact_structure_recipe_pair':False,'dft_ready':False,'nanocrystal_model':False},'source_tables_sha256':sha(L/'source-tables.json')}
    fname='lian2021-bulk-'+phase.lower()+'-non-h'
    write(OUT/(fname+'.json'),model)
    lines=['data_lian2021_bulk_'+phase.lower()+'_partial_non_h','# PARTIAL SOURCE-TABLE RECONSTRUCTION. Not the original deposited CIF.', '# Occupancies unknown; hydrogen sites absent. No complete/DFT/training claim.','_publ_section_exptl_refinement', ';', *limitations,';','_audit_creation_method \'Published table reconstruction using Gemmi '+gemmi.__version__+'\'','_publ_section_title \'Bulk '+phase+' non-H table reconstruction\'','_chemical_formula_sum \''+meta['empirical formula']['raw_text']+'\'','# Formula above is reported nominal composition, NOT the contents of this atom loop.']
    for k in ['a','b','c']:lines.append('_cell_length_'+k+' '+scaled_token(meta[k]))
    for k in ['alpha','beta','gamma']:lines.append('_cell_angle_'+k+' '+scaled_token(meta[k]))
    lines += ['_cell_volume '+scaled_token(meta['volume']),'_cell_formula_units_Z '+scaled_token(meta['Z']),'_diffrn_ambient_temperature '+scaled_token(meta['temperature'])]
    lines += ['_space_group_name_H-M_alt \''+sg.xhm()+'\'','_space_group_IT_number '+str(sg.number),'loop_','_space_group_symop_id','_space_group_symop_operation_xyz']
    lines += [str(i+1)+" '"+op.triplet()+"'" for i,op in enumerate(ops)]
    lines += ['loop_','_atom_site_label','_atom_site_type_symbol','_atom_site_fract_x','_atom_site_fract_y','_atom_site_fract_z','_atom_site_U_iso_or_equiv','_atom_site_occupancy']
    for s in sites:
        cs={c['column']:c for c in s['source_coordinate_row']['cells']}
        lines.append(' '.join([s['id'],s['element']]+[scaled_token(cs[k]) for k in ['x','y','z','Ueq']]+['?']))
    lines += ['loop_','_atom_site_aniso_label']+['_atom_site_aniso_'+k for k in ['U_11','U_22','U_33','U_23','U_13','U_12']]
    for s in sites:
        cs={c['column']:c for c in s['source_adp_row']['cells']}
        lines.append(' '.join([s['id']]+[scaled_token(cs[k]) for k in ['U11','U22','U33','U23','U13','U12']]))
    cif=OUT/(fname+'-partial.cif');cif.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    block=gemmi.cif.read_file(str(cif)).sole_block()
    check(phase+' CIF site count',len(block.find_values('_atom_site_label'))==len(sites))
    check(phase+' CIF occupancy unknown',list(block.find_values('_atom_site_occupancy'))==['?']*len(sites))
    for axis in ['x','y','z']:
        vals=block.find_values('_atom_site_fract_'+axis)
        check(phase+' CIF '+axis+' roundtrip',all(abs(gemmi.cif.as_number(v)-s['fractional'][['x','y','z'].index(axis)])<1e-12 for s,v in zip(sites,vals)))
    models.append(model)
write(OUT/'geometry-validation.json',{'status':'passed','scope':'author geometry and source-table transport checks, not independent audit','runtime':sys.executable,'gemmi_version':gemmi.__version__,'gemmi_file':gemmi.__file__,'gemmi_file_sha256':sha(gemmi.__file__),'checks':checks,'count':len(checks),'summary':{m['phase']:{'counts':m['counts'],'geometry':m['geometry_checks']} for m in models}})
print(json.dumps({'passed':len(checks),'summary':{m['phase']:m['geometry_checks'] for m in models}},indent=2))
