from pathlib import Path
import sys,json,hashlib,math,re
sys.dont_write_bytecode=True
sys.path.insert(0,r'[local path redacted]')
import gemmi
BASE=Path(__file__).resolve().parent
specs=[
 ('zno-wurtzite','9004178','ZnO','Wurtzite ZnO','ZnO wurtzite bulk reference',{'Zn':2,'O':2},'Fu2007 reports wurtzite ZnO; this COD single-crystal reference is external, not the S1 nanocrystal or its measured lattice.',[]),
 ('ir-fcc','9008470','Ir','Face-centered cubic Ir','FCC iridium bulk reference',{'Ir':4},'Stowell2005 Figure 1B/D supports FCC for OA/oleylamine specimens; this reference must not assign that phase to every ligand formulation.',[]),
 ('inp-zinc-blende','1010146','InP','Zinc blende InP','Zinc-blende InP bulk reference',{'In':4,'P':4},'Tessier2015 zinc-blende evidence belongs to the separately discussed 20 min reference-condition sample; exact identity with the 30 min Reference 1 protocol product is unresolved. This external reference does not fill that gap.',['The historic reference lattice a=5.861 angstrom is not a measurement of the selected 2015 quantum dots.']),
 ('cspbbr3-orthorhombic','4510745','CsPbBr3','Orthorhombic perovskite CsPbBr3','Orthorhombic CsPbBr3 bulk reference',{'Cs':4,'Pb':4,'Br':12},'Zhang2019 main p.9142 reports orthorhombic perovskite; TDPA-specific XRD is SI Figure S2f. The paper cites ICSD98751. This independent COD4510745 reference is not that ICSD entry or the TDPA specimen.',['Do not replace the orthorhombic crystal with a cubic ideal perovskite merely because the paper uses cubic facet nomenclature.']),
 ('coo-rocksalt','1533087','CoO','Rocksalt CoO','Rocksalt CoO bulk reference',{'Co':4,'O':4},'Saha2019 main pp.2423–2424 reports cubic CoO core. This external reference has a=4.263 angstrom, different from paper values 4.258 and 4.246 angstrom; no lattice was silently refit to the paper.',['Separate core-phase reference only; no measured core/shell interface is reconstructed.']),
 ('cofe2o4-spinel','1533163','CoFe2O4','Cubic cobalt ferrite, partially inverse spinel','Partially inverse CoFe2O4 bulk reference',{'Co':8,'Fe':16,'O':32},'Saha2019 reports an inverse-spinel CoFe2O4 shell, without atomic-coordinate refinement or site occupancies. COD1533163 is an external partially inverse reference, with its own mixed-site occupancies and a=8.3806 angstrom rather than the paper shell value 8.373 angstrom.',['Mixed Co/Fe sites are statistical crystallographic occupancy, not simultaneous colocated physical atoms.','The tetrahedral cation site is Co0.255/Fe0.745 and octahedral site Co0.3725/Fe0.6275. Do not relabel this as a perfectly ordered inverse spinel.','Use fractionalSites with mixed-site labels/colors; do not silently choose a species, randomly sample occupancies, or present this as a unique atomistic microstate.'])
]
refs=[];checks=[]
def value(block,key):
 raw=block.find_value(key)
 return gemmi.cif.as_string(raw) if raw else None
for rid,cid,formula,phase,name,expected,link,limits in specs:
 path=BASE/(cid+'.cif'); block=gemmi.cif.read(str(path)).sole_block(); st=gemmi.make_small_structure_from_block(block)
 sites=[]
 for s in st.get_all_unit_cell_sites():
  f=[v%1 for v in [s.fract.x,s.fract.y,s.fract.z]]
  f=[0.0 if abs(v-1)<1e-7 or abs(v)<1e-7 else v for v in f]
  match=next((t for t in sites if all(min(abs(x-y),1-abs(x-y))<1e-4 for x,y in zip(t['fractional'],f))),None)
  comp={'element':s.element.name,'occupancy':s.occ,'asymmetric_site_label':s.label}
  if match:
   if not any(x['element']==comp['element'] and x['asymmetric_site_label']==comp['asymmetric_site_label'] for x in match['components']):match['components'].append(comp)
  else:sites.append({'fractional':[round(v,8) for v in f],'components':[comp]})
 totals={}
 atoms=[]
 for i,s in enumerate(sites):
  s['id']='site-'+str(i+1);s['occupancy_sum']=sum(c['occupancy'] for c in s['components']);s['mixed']=len(s['components'])>1
  s['label']='/'.join(c['element'] for c in s['components']) if s['mixed'] else s['components'][0]['element']
  pos=st.cell.orthogonalize(gemmi.Fractional(*s['fractional']));s['cartesian']=[round(pos.x,8),round(pos.y,8),round(pos.z,8)]
  for c in s['components']:
   totals[c['element']]=totals.get(c['element'],0)+c['occupancy']
   atoms.append({'element':c['element'],'x':s['fractional'][0],'y':s['fractional'][1],'z':s['fractional'][2],'occupancy':c['occupancy'],'site_id':s['id'],'mixed_site':s['mixed']})
 vectors=[]
 for f in [(1,0,0),(0,1,0),(0,0,1)]:
  p=st.cell.orthogonalize(gemmi.Fractional(*f));vectors.append([p.x,p.y,p.z])
 authors=[gemmi.cif.as_string(a) for a in block.find_values('_publ_author_name')]
 doi=value(block,'_journal_paper_doi'); sgno=int(value(block,'_space_group_IT_number'))
 source={'database':'Crystallography Open Database','entry':cid,'record_url':f'https://www.crystallography.net/cod/{cid}.html','cif_url':f'https://www.crystallography.net/cod/{cid}.cif','cif_file':cid+'.cif','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'authors':authors,'title':value(block,'_publ_section_title'),'journal':value(block,'_journal_name_full'),'year':int(value(block,'_journal_year')),'doi':doi,'license':'COD CC0; acknowledge original structural-data authors','retrieved_date':'2026-09-18'}
 ref={'schema_version':'mattersyn-external-crystal-reference/1','id':rid,'name':name,'formula':formula,'phase':phase,'modelType':'Symmetry-expanded external COD bulk crystal reference','evidence_type':'external_reference','measured_sample_structure':False,'training_eligible':False,'exact_structure_recipe_eligible':False,'caption':name+'; external reference, not measured atomic coordinates of the synthesis sample.','coordinateUnits':'angstrom','spaceGroup':value(block,'_symmetry_space_group_name_H-M'),'spaceGroupNumber':sgno,'a':st.cell.a,'b':st.cell.b,'c':st.cell.c,'alpha':st.cell.alpha,'beta':st.cell.beta,'gamma':st.cell.gamma,'latticeVectors':vectors,'formulaUnitsPerCell':int(value(block,'_cell_formula_units_Z')),'referenceTemperatureK':value(block,'_diffrn_ambient_temperature'),'fractionalSites':sites,'fractionalAtoms':atoms,'weightedElementCounts':{k:round(v,8) for k,v in totals.items()},'source':source,'paper_link_scope':link,'renderingNotes':['Render a periodic unit-cell/supercell reference; do not invent a nanoparticle size, shape, ligand shell, interface, strain or defect state.','Fractional atoms are CIF site components; mixed occupancies require grouped-site rendering.','Coordinates are expanded from the source CIF using Gemmi '+gemmi.__version__+' and deduplicated modulo lattice translations; the original CIF bytes are unchanged.']+limits,'mixedOccupancy':any(s['mixed'] for s in sites)}
 errors=[]
 for e,n in expected.items():
  if abs(totals.get(e,0)-n)>1e-6:errors.append(f'{e} count {totals.get(e)} != {n}')
 if set(totals)!=set(expected):errors.append('Unexpected elements')
 if any(abs(s['occupancy_sum']-1)>1e-6 for s in sites):errors.append('Site occupancies do not total one')
 if any(not(0<=v<1) for s in sites for v in s['fractional']):errors.append('Fractional coordinate out of range')
 checks.append({'id':rid,'space_group_number':sgno,'unit_cell_sites':len(sites),'site_components':len(atoms),'weighted_counts':ref['weightedElementCounts'],'expected_counts':expected,'mixed_occupancy':ref['mixedOccupancy'],'errors':errors})
 (BASE/(rid+'.json')).write_text(json.dumps(ref,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');refs.append(ref)
(BASE/'references.json').write_text(json.dumps({'schema_version':'mattersyn-external-crystal-reference/1','scope':'External bulk crystal references only. No actual-sample atomic labels; excluded from recipe-supervision targets.','references':refs,'excluded_materials':[{'formula':'Fe–O','reason':'Feld2019 phase/stoichiometry unresolved; no universal phase reference assigned.'}],'rejected_database_candidates':[{'cod_id':'5910063','reason':'Card states CoFe2O4 but computed coordinate composition is Co16Fe8O32; incompatible stoichiometry; not used.'},{'cod_id':'4124455','reason':'Ir formula metadata conflicts with an Ir carbonyl chloride title; not used.'}]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(BASE/'validation.json').write_text(json.dumps({'parser':'gemmi '+gemmi.__version__,'checks':checks,'errors':sum(len(c['errors']) for c in checks)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
