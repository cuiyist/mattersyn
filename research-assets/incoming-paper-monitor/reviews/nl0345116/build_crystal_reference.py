from pathlib import Path
import json,hashlib,itertools,math
B=Path(__file__).resolve().parent; V=B/'visuals'; D=V/'crystal-reference'; D.mkdir(exist_ok=True)
def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ID='sashchiuk-2004-pbse-ideal-reference'; a=6.1
limits=['Constructed ideal rock-salt prototype using the paper rounded lattice parameter 6.1 Å; not measured or refined sample coordinates.','Full occupancies, ideal positions and absence of defects are model assumptions.','The eight-site conventional cubic cell is exported fully expanded with P1 symmetry to avoid requiring implicit symmetry expansion. The ideal prototype is Fm-3m.','No ligand atoms, surface reconstruction, measured wire geometry or electronic-structure relaxation are supplied.','The model is excluded from measured-structure and recipe-training labels.']
source={'doi':'10.1021/nl0345116','source_sha256':'72684e3bf22a2ef173ea1d6d6e31648a1222b2b15bc069bb8fe6cef8d1876a33','locator':'Main PDF pp. 3–4, Figures 2–3 and lattice-spacing discussion','reported_parameter':{'value':6.1,'unit':'Å','status':'reported_rounded_lattice_parameter'},'coordinates':'Constructed ideal prototype; not supplied by the paper'}
def atom(i,el,xyz,frac=None):
 q=dict(index=i,serial=i,element=el,elem=el,x=round(xyz[0],8),y=round(xyz[1],8),z=round(xyz[2],8),occupancy=1,site=el+str(i+1),label=el,mixed_site=False,bonds=[],bondOrder=[],properties={'reference_only':True,'measured_sample':False})
 if frac is not None:q['fractional']=frac
 return q
cell=[atom(i,'Pb' if sum(t)%2==0 else 'Se',[a*v/2 for v in t],[v/2 for v in t]) for i,t in enumerate(itertools.product(range(2),repeat=3))]
unit=dict(id=ID,name='Ideal rock-salt PbSe reference unit cell',formula='PbSe',modelType='Constructed ideal bulk reference',atoms=cell,cell={'a':a,'b':a,'c':a,'alpha':90,'beta':90,'gamma':90},cellVectors=[[a,0,0],[0,a,0],[0,0,a]],source=source,evidence_type='illustrative',training_eligible=False,measured_sample_structure=False,periodic=True,limitations=limits)
write(D/'models/pbse-ideal-unit-cell.json',unit)
cif=['data_pbse_ideal_expanded','_chemical_name_common \'Ideal rock-salt PbSe prototype; not measured coordinates\'','_chemical_formula_sum \'Pb4 Se4\'','_cell_length_a 6.1','_cell_length_b 6.1','_cell_length_c 6.1','_cell_angle_alpha 90','_cell_angle_beta 90','_cell_angle_gamma 90',"_space_group_name_H-M_alt 'P 1'",'_space_group_IT_number 1','loop_','_space_group_symop_operation_xyz',"'x,y,z'",'loop_','_atom_site_label','_atom_site_type_symbol','_atom_site_fract_x','_atom_site_fract_y','_atom_site_fract_z','_atom_site_occupancy']
for x in cell:cif.append(' '.join([x['site'],x['element'],*[str(v)for v in x['fractional']],'1']))
(D/'pbse-ideal-expanded-p1.cif').write_text('# Constructed ideal reference; DOI 10.1021/nl0345116 supplies rounded a=6.1 A.\n# Prototype Fm-3m, fully expanded eight-site P1 export. Not sample coordinates.\n'+'\n'.join(cif)+'\n',encoding='utf8')
atoms=[atom(i,'Pb'if sum(t)%2==0 else'Se',[(v-7.5)*a/2 for v in t])for i,t in enumerate(itertools.product(range(16),repeat=3))]
caption='Illustrative 8 × 8 × 8 cell PbSe block: 4.88 nm cell envelope; 4.575 nm atom-center span. Chosen visualization dimensions, not a fitted or measured particle. No surface ligands or assembly geometry reconstructed.'
finite=dict(id=ID+'-finite',formula='PbSe',representation='finite_illustrative_particle',periodic=False,evidence_type='illustrative',training_eligible=False,measured_sample_structure=False,atoms=atoms,caption=caption,source=source,limitations=limits,cell_envelope_nm=4.88,atom_center_span_nm=4.575)
write(D/'models/pbse-illustrative-block.json',finite)
p=D/'downloads/pbse-illustrative-block.xyz';p.parent.mkdir(exist_ok=True);p.write_text(str(len(atoms))+'\n'+caption+'\n'+'\n'.join(f"{q['element']} {q['x']} {q['y']} {q['z']}"for q in atoms)+'\n',encoding='utf8')
entry=dict(id=ID,name='Ideal rock-salt PbSe reference',formula='PbSe',record_ids=['sashchiuk-2004-'+k for k in ['individual-low','sphere-intermediate','wire-intermediate','wire-high']],description=limits[0],scope='Constructed ideal reference using reported rounded a = 6.1 Å. Source SAED/HRTEM supports rock-salt order; no sample coordinates or measured assembly atom model are supplied. P1 export expands all eight conventional-cell sites; ideal prototype Fm-3m.',sourceUrl='https://doi.org/10.1021/nl0345116',sourceLinkLabel='Paper supplying rounded lattice parameter',cifPath='pbse-ideal-expanded-p1.cif',modelPath='models/pbse-ideal-unit-cell.json',spaceGroup='P 1 (expanded ideal Fm-3m prototype)',spaceGroupNumber=1,prototypeSpaceGroupNumber=225,mixedOccupancy=False,referenceOnly=True,trainingEligible=False,measuredSampleStructure=False,referenceType='locally_constructed_ideal_reference',structureAssetRole='illustrative',finiteModelPath='models/pbse-illustrative-block.json',finiteCaption=caption,finiteModelPeriodic=False,additionalDownloads=[{'label':'Illustrative PbSe block XYZ','path':'downloads/pbse-illustrative-block.xyz','sha256':sha(p)}])
entry.update(cifSha256=sha(D/entry['cifPath']),modelSha256=sha(D/entry['modelPath']),finiteModelSha256=sha(D/entry['finiteModelPath']))
write(V/'crystal-reference-proposal.json',{'entries':[entry],'files':[{'path':str(p.relative_to(D)).replace('\\','/'),'sha256':sha(p)} for p in sorted(D.rglob('*'))if p.is_file()]})
checks=[]
for x in cell:
 neighbors=[]
 for y in cell:
  for im in itertools.product([-1,0,1],repeat=3):
   d=math.sqrt(sum((y[k]+im[j]*a-x[k])**2 for j,k in enumerate(['x','y','z'])))
   if abs(d-a/2)<1e-7:neighbors.append(y['element'])
 assert len(neighbors)==6 and all(e!=x['element']for e in neighbors)
checks.append('All eight sites have six opposite-species periodic neighbors at 3.05 Å.')
assert len(atoms)==4096 and sum(x['element']=='Pb'for x in atoms)==2048
assert len({(x['x'],x['y'],x['z'])for x in atoms})==4096
checks.append('Finite block has 2048 Pb + 2048 Se, unique coordinates and declared 4.575 nm atom span.')
write(V/'crystal-generator-checks.json',{'status':'passed_generator_checks_independent_audit_pending','checks':checks})
print('Built ideal PbSe unit cell, P1 CIF and explicit nonperiodic illustration; independent audit pending.')
