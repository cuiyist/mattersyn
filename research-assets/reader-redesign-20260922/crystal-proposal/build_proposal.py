"""Generate an isolated reference proposal; never modifies the site checkout.

Run with the bundled Python. Gemmi 0.7.5 is imported from this proposal's
runtime directory and is used for CIF parsing and symmetry expansion.
"""
from pathlib import Path
from collections import Counter
import json, hashlib, math, itertools, shutil, sys, csv

ROOT=Path(__file__).resolve().parent
SITE=Path(r'[local path redacted]')
sys.path.insert(0,str(ROOT/'runtime'))
import gemmi
ASSETS=ROOT/'assets'/'crystal-references'
(ASSETS/'models').mkdir(parents=True,exist_ok=True)
(ASSETS/'provenance').mkdir(exist_ok=True)
DATE='2026-09-22'

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
materials=[read(p) for p in sorted((SITE/'data/materials').glob('*.json'))]
assert len(materials)==50
by_formula={m['formula']:m for m in materials}
routes={r['record_id']:r for m in materials for r in m['records'] if r.get('is_synthesis_route')}
registry=read(SITE/'assets/crystal-references/registry.json')
def route_ids(formula): return sorted(r['record_id'] for r in by_formula[formula]['records'] if r.get('is_synthesis_route'))
def scopes(formula): return sorted(m['id'] for m in materials if any(r['record_id'] in route_ids(formula) for r in m['records']))
GENERAL='Independent periodic reference, not refined coordinates of these synthesis samples. It does not establish a sample phase, particle size, surface, defects, ligands, strain, or interface.'
config=[]
def ref(id,formula,phase,cif,expected,scope,**extra):
 config.append(dict(id=id,formula=formula,phase=phase,cif=cif,expected=expected,scope=scope,**extra))

ref('ceo2-fluorite-cod-9009008','CeO2','fluorite','9009008.cif',{'Ce':4,'O':8},'Fluorite CeO2 comparison. This does not identify the phase or oxygen-vacancy concentration of the as-prepared Pati solvent-series specimens.')
ref('ag-fcc-cod-9008459','Ag','face-centered cubic','9008459.cif',{'Ag':4},'Bulk FCC Ag reference. For Ag/Si, Ag and Si are separate component references; no epitaxial relationship, interfacial strain, or particle coordinates are reconstructed.')
ref('ge-diamond-cod-9008567','Ge','diamond cubic','9008567.cif',{'Ge':8},'Bulk diamond Ge reference. It does not reconstruct the patterned Ge/Si islands, their strain or their interface.')
ref('fapbi3-pbesol-ordered-reference','FAPbI3','computed pseudo-cubic framework (P1 ordered model)','wmd-FAPbI3.cif',{'C':1,'N':2,'H':5,'Pb':1,'I':3},'Computed PBEsol reference with one ordered formamidinium orientation. The asymmetric cell and P1 model must not be labeled an experimental cubic, tetragonal, or delta-phase refinement. Finite-temperature FA orientational disorder, alpha/delta mixtures, PbI2 impurities, and sample-specific phase fractions are absent.',computed=True)
ref('cds-wurtzite-cod-9008862','CdS','wurtzite','9008862.cif',{'Cd':2,'S':2},'Bulk wurtzite CdS comparison. Wurtzite and zinc-blende alternatives must be labeled separately and do not resolve a route with uncertain or mixed phase. Shell interfaces and shell strain are not reconstructed.',selection='phase_choice')
ref('cds-zinc-blende-cod-9000067','CdS','zinc blende','9000067.cif',{'Cd':4,'S':4},'Bulk cubic CdS (hawleyite) comparison. Wurtzite and zinc-blende alternatives must be labeled separately; no phase assignment is inferred for an unspecified specimen.',selection='phase_choice')
ref('cdte-zinc-blende-cod-9008840','CdTe','zinc blende (alternative phase)','9008840.cif',{'Cd':4,'Te':4},'Optional alternative-phase comparator only. Banerjee2003 reports wurtzite CdTe on nanotubes; this cubic reference is not the reported phase and must not be the default sample model. No CdTe/MWNT interface is reconstructed.',selection='explicit_alternative_only',unbound=True)
ref('pt-fcc-cod-9008480','Pt','face-centered cubic','9008480.cif',{'Pt':4},'Independent bulk FCC Pt comparison; no refined atomic coordinates or facets of the Shah synthesis specimen are supplied.')
ref('sno2-cassiterite-cod-9009082','SnO2','cassiterite (rutile type)','9009082.cif',{'Sn':2,'O':4},'Bulk cassiterite SnO2 comparison. Hydroxylation, oxygen vacancies, precursor state and nanoparticle surfaces are not represented.')
ref('znal2o4-gahnite-cod-9015620','ZnAl2O4','normal spinel','9015620.cif',{'Zn':8,'Al':16,'O':32},'Undoped gahnite endpoint with source inversion parameter 0.000 and Co content 0.00 apfu. This ordered Zn/Al reference does not assign cation inversion, Co occupancy, defect populations, or route-dependent disorder to the Sommer specimens.')
ref('pbs-rocksalt-cod-9013403','PbS','rock salt','9013403.cif',{'Pb':4,'S':4},'Bulk rock-salt PbS reference at source temperature 298 K. It does not describe the amorphous glass network or the PbS/glass interface.')
ref('zns-zinc-blende-cod-1100043','ZnS','zinc blende','1100043.cif',{'Zn':4,'S':4},'Bulk cubic ZnS component comparison. No shell polytype, lattice strain, grading, thickness, or epitaxial registry is inferred.',selection='phase_choice')
ref('zns-wurtzite-cod-1100044','ZnS','wurtzite','1100044.cif',{'Zn':2,'S':2},'Bulk wurtzite ZnS alternative component comparison. Do not conflate this bulk unit cell with a strained ZnS shell.',selection='phase_choice')
ref('znse-zinc-blende-cod-9008857','ZnSe','zinc blende','9008857.cif',{'Zn':4,'Se':4},'Bulk cubic ZnSe component comparison. No phase assignment, interface registry or shell strain is inferred for a route without matching evidence.',selection='phase_choice')
ref('znse-wurtzite-cod-9008879','ZnSe','wurtzite','9008879.cif',{'Zn':2,'Se':2},'Bulk wurtzite ZnSe component comparison. The unit cell is independent of the underlying CdSe core and does not reconstruct a coherent core/shell interface.',selection='phase_choice')
ref('inas-zinc-blende-cod-9008851','InAs','zinc blende','9008851.cif',{'In':4,'As':4},'Independent bulk zinc-blende InAs comparison; particle geometry and ligands from the synthesis are not included.')
ref('csmncl3-rhombohedral-cod-2107040','CsMnCl3','rhombohedral R-3m, hexagonal axes','2107040.cif',{'Cs':9,'Mn':9,'Cl':27},'Rhombohedral reference relevant only as a comparison to the higher-temperature rhombohedral contexts. Matuhina nc150 is assigned cubic, whereas nc180/nc200 are assigned rhombohedral. This model must not be the default for the full series or the cubic context.',selection='sample_context_choice',sample_context_ids=['nc180-07','nc180-05','nc180-035','nc200'])
ref('si-diamond-cod-9008565','Si','diamond cubic','9008565.cif',{'Si':8},'Bulk diamond silicon reference, separate from SiOx and amorphous oxide. For Ge/Si and Ag/Si it represents only the Si component. It does not establish crystallinity or atomic coordinates of the smallest Littau particles.')

def cif_text(block,key):
 value=block.find_value(key)
 return gemmi.cif.as_string(value).strip() if value else None
def vec(pos): return [round(pos.x,10),round(pos.y,10),round(pos.z,10)]
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cart(frac,vectors): return [sum(frac[j]*vectors[j][i] for j in range(3)) for i in range(3)]

entries=[]
validations=[]
provenance=[]
for c in config:
 source=ROOT/'source-cache'/c['cif']
 block=gemmi.cif.read_file(str(source)).sole_block()
 struct=gemmi.make_small_structure_from_block(block)
 cell=struct.cell
 vectors=[vec(cell.orthogonalize(gemmi.Fractional(*v))) for v in [(1,0,0),(0,1,0),(0,0,1)]]
 atoms=[]
 for i,a in enumerate(struct.get_all_unit_cell_sites()):
  f=[x%1.0 for x in [a.fract.x,a.fract.y,a.fract.z]]
  f=[0.0 if abs(x)<1e-8 or abs(x-1)<1e-8 else round(x,10) for x in f]
  xyz=cart(f,vectors)
  atoms.append(dict(element=a.element.name,x=xyz[0],y=xyz[1],z=xyz[2],occupancy=a.occ,site=a.label,label=a.label+'_'+str(i+1),mixed_site=False,components=[dict(element=a.element.name,occupancy=a.occ,asymmetric_site_label=a.label)],fractional=f,color=None,properties=dict(site_label=a.label,occupancies={a.element.name:a.occ},statistical_site=False)))
 counts=Counter()
 for a in atoms: counts[a['element']]+=a['occupancy']
 assert dict(counts)==c['expected'],(c['id'],counts,c['expected'])
 assert all(math.isfinite(n) for a in atoms for n in [a['x'],a['y'],a['z'],a['occupancy']])
 assert cell.volume>0 and all(0<a['occupancy']<=1 for a in atoms)
 assert len({(a['element'],*a['fractional']) for a in atoms})==len(atoms)
 minimum=float('inf')
 for i,a in enumerate(atoms):
  for j,b in enumerate(atoms):
   for shift in itertools.product([-1,0,1],repeat=3):
    if i==j and shift==(0,0,0): continue
    delta=[a['fractional'][k]-b['fractional'][k]+shift[k] for k in range(3)]
    v=cart(delta,vectors)
    minimum=min(minimum,math.sqrt(dot(v,v)))
 assert minimum>0.65,(c['id'],minimum)
 codid=source.stem
 if c.get('computed'):
  src=dict(database='WMD-group/hybrid-perovskites',entry='2014_cubic_halides_PBEsol/FAPbI3.cif',record_url='https://github.com/WMD-group/hybrid-perovskites/blob/master/2014_cubic_halides_PBEsol/FAPbI3.cif',cif_url='https://raw.githubusercontent.com/WMD-group/hybrid-perovskites/master/2014_cubic_halides_PBEsol/FAPbI3.cif',authors=['WMD group repository contributors'],title='PBEsol optimized pseudo-cubic FAPbI3 reference',journal=None,year=None,doi=None,license='GPL-2.0; original repository LICENSE.md retained',license_file='provenance/wmd-LICENSE.md',source_readme='provenance/wmd-README.md',related_publications=['https://doi.org/10.1063/1.4824147','https://doi.org/10.1021/acs.jpclett.5b01432'],publication_scope='Repository README lists these uses; no specific paper-to-file refinement identity is asserted.')
  source_type='computed_reference'
 else:
  src=dict(database='Crystallography Open Database',entry=codid,record_url=f'https://www.crystallography.net/cod/{codid}.html',cif_url=f'https://www.crystallography.net/cod/{codid}.cif',authors=[gemmi.cif.as_string(v) for v in block.find_values('_publ_author_name')],title=cif_text(block,'_publ_section_title'),journal=cif_text(block,'_journal_name_full'),year=cif_text(block,'_journal_year'),doi=cif_text(block,'_journal_paper_doi'),license='Source CIF permits scientific-community use with attribution to the original publication; original notice retained.')
  source_type='literature_bulk_reference'
 src.update(cif_file=c['cif'],sha256=sha(source),retrieved_date=DATE,source_formula=cif_text(block,'_chemical_formula_sum'),formula_units_Z=cif_text(block,'_cell_formula_units_Z'),cell_measurement_temperature_K=cif_text(block,'_cell_measurement_temperature'),diffraction_temperature_K=cif_text(block,'_diffrn_ambient_temperature'),journal_volume=cif_text(block,'_journal_volume'),journal_page_first=cif_text(block,'_journal_page_first'),journal_page_last=cif_text(block,'_journal_page_last'))
 name=c['formula']+' '+c['phase']+' reference'
 phase_scope=c['scope']+' '+GENERAL
 model=dict(id=c['id'],name=name,formula=c['formula'],atoms=atoms,cell={k:getattr(cell,k) for k in ['a','b','c','alpha','beta','gamma']},cellVectors=vectors,spaceGroup=struct.spacegroup_hm,spaceGroupNumber=struct.spacegroup_number,units='angstrom',periodic=True,representation='conventional_unit_cell_sites',mixedOccupancy=False,mixedSiteSymbol=None,source=src,sourceType=source_type,phaseScope=phase_scope,scope=phase_scope,caption=name+'. '+phase_scope,training_eligible=False,measured_sample_structure=False,renderingNotes=['Fractional sites are expanded using the symmetry operations of the original CIF, including its origin choice; no structure relaxation or coordinate fitting was performed.','Cartesian coordinates equal the source-cell fractional coordinates multiplied by the source cell vectors. Sites are wrapped into one half-open periodic unit cell.','Display bonds, if added, are geometric guides only. Boundary-wrapped molecular fragments do not imply broken chemical bonds.','A periodic unit cell is not a complete finite nanocrystal. No particle cut, dopant substitution, surface termination or ligand decoration is generated.'])
 if c.get('computed'): model['renderingNotes'].append('The FA orientation is one ordered computational configuration. It is not an experimental occupancy or finite-temperature orientational ensemble.')
 out=ASSETS/'models'/(c['id']+'.json')
 write(out,model)
 shutil.copyfile(source,ASSETS/c['cif'])
 entry=dict(id=c['id'],name=name,formula=c['formula'],record_ids=[] if c.get('unbound') else route_ids(c['formula']),material_ids=scopes(c['formula']),description=name+'. '+GENERAL,scope=phase_scope,phaseScope=phase_scope,sourceType=source_type,sourceUrl=src['record_url'],cifPath=c['cif'],modelPath='models/'+out.name,spaceGroup=struct.spacegroup_hm,spaceGroupNumber=struct.spacegroup_number,mixedOccupancy=False,cifSha256=sha(source),modelSha256=sha(out),referenceOnly=True,trainingEligible=False,measuredSampleStructure=False,referenceType=source_type,structureAssetRole='external_reference_unit_cell',displayPolicy=c.get('selection','independent_reference'),defaultForSample=False)
 if c.get('sample_context_ids'):
  entry['sample_context_ids']=c['sample_context_ids']
  for rid in entry['record_ids']:
   record=read(SITE/'data/records'/(rid+'.json'))
   actual={p['sample_id'] for p in record.get('products',[]) if p.get('phase',{}).get('value')=='rhombohedral'}
   assert set(c['sample_context_ids'])<=actual,(rid,c['sample_context_ids'],actual)
 if c.get('unbound'): entry['bindingStatus']='Withheld from route bindings; optional explicitly chosen alternative only.'
 if c.get('computed'): entry['additionalDownloads']=[{'label':'Original WMD license','path':'provenance/wmd-LICENSE.md'},{'label':'Source repository README','path':'provenance/wmd-README.md'}]
 entries.append(entry)
 validations.append(dict(id=c['id'],status='pass',cif_sha256=sha(source),model_sha256=sha(out),source_asymmetric_sites=len(struct.sites),expanded_sites=len(atoms),occupancy_weighted_counts=dict(counts),expected_counts=c['expected'],volume_angstrom3=cell.volume,minimum_periodic_distance_angstrom=round(minimum,5),space_group_number=struct.spacegroup_number,valid_route_bindings=all(r in routes for r in entry['record_ids']),checks=['CIF parsed by Gemmi 0.7.5','symmetry expansion includes CIF origin choice','expanded composition equals expected formula times Z','finite coordinates and positive cell volume','unique element/fractional sites and occupancies in (0,1]','minimum periodic interatomic distance >0.65 angstrom','unchanged source-CIF SHA256 and generated-model SHA256','route bindings exist in material inventory']))
 provenance.append(dict(id=c['id'],source=src,phaseScope=phase_scope))

for f in ['wmd-README.md','wmd-LICENSE.md']: shutil.copyfile(ROOT/'source-cache'/f,ASSETS/'provenance'/f)
write(ROOT/'registry-additions.json',dict(schema_version='mattersyn-reference-registry/1',entries=entries))
write(ROOT/'provenance.json',provenance)
write(ROOT/'validation.json',dict(date=DATE,gemmi_version=gemmi.__version__,all_passed=all(v['valid_route_bindings'] for v in validations),models=validations))

# Extend only safe existing independent reference bindings. The existing files
# are not overwritten; the integrator must preserve their hashes and sources.
extensions=[]
for eid,formula,scope in [
 ('inp-zinc-blende','InP','Independent zinc-blende bulk comparison, not a refined product structure or cluster geometry.'),
 ('ir-fcc','Ir','Independent bulk FCC Ir reference. Additional Stowell precursor routes must not inherit the OA-only XRD/sample context.'),
 ('zno-wurtzite','ZnO','Independent undoped wurtzite ZnO comparison. New Fu route bindings do not imply measured atomic coordinates or identical morphology.'),
 ('sashchiuk-2004-pbse-ideal-reference','PbSe','Constructed rock-salt reference, optional comparison for Evans PbSe QDs only. It is not the atomic structure of Evans magic-size clusters.')]:
 old=next(e for e in registry['entries'] if e['id']==eid)
 ids=[r for r in route_ids(formula) if r not in old['record_ids'] and 'msc-family' not in r]
 if ids: extensions.append(dict(id=eid,add_record_ids=ids,sourceType='constructed_lattice_reference' if 'ideal-reference' in eid else 'literature_bulk_reference',phaseScope=scope,defaultForSample=False,requires_per_binding_scope=True))
write(ROOT/'existing-binding-extensions.json',extensions)

# Explicit custom viewer inventory. These are not generic-registry entries and
# must not be miscounted as absent or as complete refined training examples.
custom=[
 dict(id='heo2003-average',record_ids=['heo-2003-in66-route','heo-2003-single-crystal-acquisition','heo-2003-average-structure'],material_ids=['in66si100al92o384-e3d988','in-8bc1d5'],source='heo2003-average-viewer.mjs',kind='source_average_occupancy',note='Source average crystal structure with partial/mixed site occupancies; not one ordered atom arrangement. In-containing zeolite reference, not a bulk indium-metal unit cell.'),
 dict(id='lian2021-bulk-a-partial',record_ids=['lian-2021-bulk-a-route','lian-2021-bulk-characterization'],material_ids=['c12h28n-2sbcl5-bfd42d'],source='lian2021-bulk-viewer.mjs',kind='source_table_partial_nonhydrogen',note='Bulk A non-H coordinates from source tables; H and occupancies absent. Same physical aliquot linkage is not established. NC-A route is not covered by this source refinement.'),
 dict(id='lian2021-bulk-b-partial',record_ids=['lian-2021-bulk-b-route','lian-2021-bulk-characterization'],material_ids=['c12h28n-sbcl4-58ecef'],source='lian2021-bulk-viewer.mjs',kind='source_table_partial_nonhydrogen',note='Bulk B non-H coordinates from source tables; H and occupancies absent. Same physical aliquot linkage is not established.'),
 dict(id='cdse-legacy-wurtzite',record_ids=['murray-1993-cdse-method1','murray-1993-cdse-method2','peng-2000-cdse-high-aspect','peng-2000-cdse-typical'],material_ids=['cdse-d923c5'],source='material-app.mjs; shape-app.js; assets/cdse-structures',kind='legacy_reference_and_illustrative_crop',note='Legacy CdSe reader pages contain wurtzite references and illustrative particle crops; this does not mean their generic record pages have bound viewers.'),
 dict(id='cdse-legacy-zinc-blende',record_ids=[],material_ids=['cdse-d923c5','cdse-cds-34750d','cdse-znse-0f8c68'],source='assets/crystal-reference.json; app.js; nakonechnyi-2017.js',kind='constructed_lattice_reference',note='Existing ideal zinc-blende basis with published a=6.077 angstrom; not an independently refined nanocrystal or new CIF. Legacy showcase coverage is not route-wide generic binding.'),
 dict(id='evans-species9-molecular',record_ids=['evans-2010-species9-crystallization','evans-2010-molecular9-structure'],material_ids=[],source='evans2010-products.mjs',kind='molecular_crystal_fragment',note='Source-derived molecular species 9 viewer; NOT a CdSe, PbSe QD, or magic-size-cluster product unit cell.')]
write(ROOT/'custom-viewer-inventory.json',custom)

gap_by_formula={
 'CdTe':'Wurtzite CdTe coordinates remain missing. Cubic COD 9008840 is an unbound alternative, not the reported phase.',
 'CdTe/MWNT':'Wurtzite CdTe reference and MWNT wall/chirality model missing; cubic CdTe alternative does not close either gap.',
 'MWNT':'A nanotube requires curvature, wall count, chirality and stacking context; no justified atomistic nanotube model supplied.',
 'HgS':'HgS component reference remains missing; alpha-cinnabar and beta-metacinnabar must not be conflated.',
 'CdS/HgS/CdS':'CdS component comparisons supplied; HgS reference and actual multilayer interface/strain remain missing.',
 'SiO2':'No justified periodic phase supplied for the mesoporous/amorphous silica host. Do not substitute quartz.',
 'CdS/SiO2':'CdS unit-cell comparisons supplied; amorphous silica network and interface are not atomistically reconstructed.',
 'PbS/glass':'PbS comparison supplied; glass composition/network and interface are not a periodic PbS unit cell.',
 'Fe\u2013O':'Oxide stoichiometry/phase varies or is unresolved; no magnetite/maghemite/wustite coordinates assigned by formula alone.',
 'Fe\ufffdO':'Oxide stoichiometry/phase varies or is unresolved; no magnetite/maghemite/wustite coordinates assigned by formula alone.',
 'FePt':'Ordered L10 tetragonal FePt is not interchangeable with a disordered FCC alloy; no justified FePt model supplied.',
 'FePt/CdS':'CdS comparisons supplied; FePt chemical order and the heterodimer interface remain unresolved.',
 'In':'The existing Heo viewer is an In-containing zeolite average structure, not an elemental-indium particle model.',
 'In66Si100Al92O384':'Average fractional occupancies are available in the custom viewer; an ordered In-cluster microstate is not determined.',
 '(C12H28N)2SbCl5':'Partial bulk-A source coordinates exist; NC-A atomic structure, H sites, occupancies and identical-aliquot proof remain absent.',
 '(C12H28N)SbCl4':'Partial bulk-B non-H source coordinates exist; occupancies, H sites and identical-aliquot proof remain absent.',
 'Si/SiOx':'Diamond Si comparison available; SiOx shell stoichiometry/network and core-shell interface are not reconstructed.',
 'CsMnCl3':'Rhombohedral comparison supplied for nc180/nc200; the cubic nc150 structure remains missing. Do not use one default for the series.',
 'FAPbI3':'Computed P1 ordered pseudo-cubic comparison only. Experimental polymorph coordinates, FA disorder, phase fractions and sample refinement remain absent.',
 'Mn:ZnO':'Undoped ZnO host only; Mn positions/occupancy and dopant-defect correlations are not measured.',
 'ZnO:Co':'Undoped ZnO host only; Co positions/occupancy are not assigned.',
 'ZnO:Ni':'Undoped ZnO host only; Ni positions/occupancy are not assigned.',
 'La2(MoO4)3:Yb,Er':'No verified tetragonal host CIF obtained. Retrieved COD 2107003 is monoclinic C2/c and withheld. Yb/Er occupancies and positions are unknown.',
 'CdS/polymer':'CdS comparisons supplied; polymer conformation, ligand grafting and interface remain unmodeled.',
 'CdSe/ZnS/siloxane':'Component references only; siloxane network, interface and strained shell atomic geometry remain absent.',
 'CdSe':'Wurtzite reference and legacy constructed cubic reference exist. Not every route is bound; magic-size/very-small species must not inherit bulk atom arrangements.',
 'PbSe':'Rock-salt reference covers selected routes; Evans magic-size clusters remain without product coordinates.',
 'ZnAl2O4':'Normal-spinel endpoint comparison only; sample-specific inversion/disorder is not resolved.',
 'CeO2':'Fluorite reference does not establish phase of the as-prepared solvent-series samples or oxygen-vacancy concentration.',
 'Ge/Si':'Separate Ge/Si cells only; island strain, shape and interface registry remain absent.',
 'Ag/Si':'Separate Ag/Si cells only; supported particle structure and epitaxial registry remain absent.',
 'CoO/CoFe2O4':'Separate component cells and average mixed Co/Fe occupancy only; interface and one ordered cation arrangement are not determined.',
 'CoFe2O4':'Current reference uses statistical Co/Fe site mixing; do not turn it into a specific ordered configuration.'}
matrix=[]
for m in materials:
 mids=set(r['record_id'] for r in m['records'] if r.get('is_synthesis_route'))
 old=[e for e in registry['entries'] if mids.intersection(e.get('record_ids',[]))]
 # Generic matches on a composite record may describe another component; expose
 # formulas rather than making a boolean 'covered' claim.
 new=[e for e in entries if mids.intersection(e['record_ids'])]
 customs=[e for e in custom if m['id'] in e['material_ids']]
 ext=[e for e in extensions if mids.intersection(e['add_record_ids'])]
 oldroutes=mids.intersection({r for e in old for r in e['record_ids']})
 newroutes=mids.intersection({r for e in new for r in e['record_ids']}|{r for e in ext for r in e['add_record_ids']})
 gap=gap_by_formula.get(m['formula'],'Independent unit-cell comparison only; no measured nanocrystal atomic structure, surface, ligands or morphology inferred.')
 if '/' in m['formula'] and m['formula'] not in gap_by_formula: gap='Separate bulk component unit cells only. No measured core-shell interface, coherent strain, grading, complete particle or surface-ligand geometry.'
 row=dict(material_id=m['id'],formula=m['formula'],component_only=m.get('component_only',False),route_count=len(mids),route_ids=sorted(mids),current_generic_entries=[dict(id=e['id'],formula=e['formula']) for e in old],current_generic_route_count=len(oldroutes),current_custom_viewers=[dict(id=e['id'],kind=e['kind'],note=e['note']) for e in customs],proposed_entries=[dict(id=e['id'],formula=e['formula'],sourceType=e['sourceType'],displayPolicy=e['displayPolicy']) for e in new],existing_binding_extensions=[e['id'] for e in ext],proposed_additional_route_count=len(newroutes-oldroutes),routes_still_without_generic_reference_binding=sorted(mids-oldroutes-newroutes),specific_gap=gap)
 matrix.append(row)
write(ROOT/'all-material-gap-matrix.json',dict(material_count=len(matrix),unique_route_count=len(routes),counting_rule='A bound reference may cover only one component of a composite. Generic counts exclude custom/legacy viewers; source-average and partial-coordinate viewers are separately inventoried. No row means exact measured particle coverage.',materials=matrix))
with (ROOT/'all-material-gap-matrix.csv').open('w',encoding='utf-8-sig',newline='') as f:
 fields=['material_id','formula','route_count','current_generic_route_count','current_generic_entries','current_custom_viewers','proposed_entries','existing_binding_extensions','specific_gap']
 writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
 for row in matrix:
  obj={k:row[k] for k in fields}
  for k in ['current_generic_entries','current_custom_viewers','proposed_entries']: obj[k]='; '.join(x['id'] for x in obj[k])
  obj['existing_binding_extensions']='; '.join(obj['existing_binding_extensions'])
  writer.writerow(obj)
lines=['# Crystal reference coverage: all 50 material hubs','',f'Inventory: {len(routes)} unique synthesis routes across 50 hubs. A composite route appears under its component hubs. Counts describe viewer bindings, not evidence of atomic refinement.','', '| Material | Current generic refs | Custom / legacy | Proposed refs | Specific limits or gaps |','|---|---|---|---|---|']
for row in matrix:
 values=[row['formula'],', '.join(x['id'] for x in row['current_generic_entries']) or '\u2014',', '.join(x['id'] for x in row['current_custom_viewers']) or '\u2014',', '.join(x['id'] for x in row['proposed_entries']) or '\u2014',row['specific_gap']]
 lines.append('| '+' | '.join(v.replace('|','/') for v in values)+' |')
(ROOT/'all-material-gap-matrix.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
write(ROOT/'inventory-summary.json',dict(material_hubs=len(materials),unique_synthesis_routes=len(routes),existing_generic_entries=len(registry['entries']),new_reference_models=len(entries),new_bound_models=sum(bool(e['record_ids']) for e in entries),new_reference_bound_unique_routes=len({r for e in entries for r in e['record_ids']}),source_site_registry_sha256=sha(SITE/'assets/crystal-references/registry.json'),source_material_index_sha256=sha(SITE/'data/materials-index.json'),reference_only=True,training_eligibility_changed=False))
print(json.dumps(read(ROOT/'inventory-summary.json'),indent=2))
