"""Source-scoped Ghosh component references; local assets only, no frozen source edits."""
import molecule_helpers as H
from molecule_helpers import *
for p in [C/'package-manifest.json',C/'record-manifest.json',P/'source-facts.json',P/'source-inventory.json',P/'package-freeze.json',P/'source-independent-audit/independent-audit-v2.json',S/'dist/chemical-viewer.mjs']:bind(p)
ck('Frozen canonical v1',sha(C/'package-manifest.json')=='9ba2ccdfb35dcf81faa4da964221074febba24b7f8705d64b6f65d14fd2f3ee7')
ck('Passed source revision2',sha(P/'source-independent-audit/independent-audit-v2.json')=='366bb63e0011c3c1b44d5940e0d1e0f396c04e57ab786cf72ac527cc3d1fd6e0')
records={};slots={}
for x in read(C/'record-manifest.json')['records']:
 ck(x['record_id']+' frozen',sha(x['path'])==x['sha256']);bind(x['path']);records[x['record_id']]=read(x['path'])
for rid,r in records.items():
 for i,m in enumerate(r['materials']):slots.setdefault(m['id'],[]).append((rid,i,m))
ck('88 slots /25 identities',sum(map(len,slots.values()))==88 and len(slots)==25)
base={e['id']:e for e in read(REG/'registry.json')['entries']};snap(REG/'registry.json','registry.json');source_url='https://doi.org/10.1021/ja212032q'
GRAPH={
 'oa':('CCCCCCCC/C=C\\CCCCCCCC(=O)O','C18H34O2','oleic-acid'),
 'ode':('C=CCCCCCCCCCCCCCCCC','C18H36','1-octadecene'),
 'od':('CCCCCCCCCCCCCCCCCC','C18H38',None),
 'ola':('CCCCCCCC/C=C\\CCCCCCCCN','C18H37N','oleylamine'),
 'doa':('CCCCCCCCNCCCCCCCC','C16H35N',None),
 'top':('CCCCCCCCP(CCCCCCCC)CCCCCCCC','C24H51P','top'),
 'topo':('CCCCCCCCP(=O)(CCCCCCCC)CCCCCCCC','C24H51OP','topo'),
 'top-se':('CCCCCCCCP(=[Se])(CCCCCCCC)CCCCCCCC','C24H51PSe','topse'),
 'ethanol':('CCO','C2H6O','ethanol'), 'hexane':('CCCCCC','C6H14','hexane'),
 'toluene':('Cc1ccccc1','C7H8','toluene'), 'acetone':('CC(C)=O','C3H6O','acetone'),
 'liquid-nitrogen':('N#N','N2','norberg2004-nitrogen-reference')}
SYMBOLS={
 'cdo':('Cadmium oxide','CdO',['CdO · listed starting reagent','Upstream cadmium-oleate preparation absent','No dissolved or molecular geometry'],'Solid compound identity; no isolated Cd=O molecule or product lattice is asserted.'),
 'sulfur':('Elemental sulfur','S',['Elemental sulfur · powder','Allotrope and dissolved species unknown','Distinct from the S/OD stock'],'No S8 ring, polymeric sulfur, dissolved speciation or nanocrystal coordinates are assigned.'),
 'selenium':('Elemental selenium','Se',['Elemental selenium · pellets','Allotrope not reported','Distinct from named TOP–Se'],'Listed elemental precursor; TOP–Se preparation is not supplied and no Se-to-TOP reaction is fabricated.'),
 'cd-oleate':('Cadmium oleate precursor',None,['Cadmium oleate · source-named precursor','Coordination and hydration unreported','Cd:OA formulations are not complex formulae'],'No discrete Cd–O geometry, hydration state, coordination number or unique dissolved complex is assigned.'),
 'argon':('Argon atmosphere','Ar',['Argon · core heat-up atmosphere','Flow and purity not reported','No universal shell-growth atmosphere assigned'],'Elemental gas identity only; the atmosphere scope remains the reported core heat-up.'),
 'r6g':('Rhodamine 6G reference',None,['Rhodamine 6G · QY reference','Counterion and whole-salt formula unspecified','Reference purity is not product quantum yield'],'No unreported salt, dye concentration, solvent or charge-state assay is assigned.'),
 'glass':('Glass coverslip',None,['Acetone-cleaned glass coverslip','Optical specimen support','Composition and surface unreported'],'No silica lattice or molecular glass composition is assigned.'),
 'silicon':('Silicon diffraction support','Si',['Background-less silicon slide','X-ray diffraction support','Not the nanocrystal product structure'],'The source names silicon support; no orientation, surface termination or lattice is supplied here.'),
 'diamond':('Diamond ATR cell','C',['Diamond ATR measurement cell','Infrared support/contact surface','Not a reaction ingredient'],'No sample crystal model or atomic cell is generated.'),
 'immersion-oil':('Immersion oil',None,['Oil for the 100× optical objective','Composition not reported','Not a synthesis liquid'],'No guessed hydrocarbon or silicone mixture is substituted for the unreported optical oil.'),
 'cdse-core':('CdSe core material','CdSe',['CdSe cores · source material family','2.2 / 3 / 4 / 5.5 nm growth branches','Separate 7 nm control; no shared-batch claim'],'Nominal material identity only. No universal diameter, ligation, phase, lattice or product/sample binding.'),
 'cdse-cds':('CdSe/CdS core/shell material','CdSe/CdS',['CdSe core / CdS shell family','Variable thickness, morphology and phase','No atomic surface or universal sample join'],'Symbolic architecture only; no fixed Cd:Se:S stoichiometry, ligand coverage or measured atomic geometry.')}
LIMITS={
 'oa':'A named cis-oleic-acid reference illustrates the 90% reagent; no batch-specific isomer assay, surface-bound oleate geometry or impurity composition is inferred.',
 'ola':'A named cis-oleylamine reference illustrates a technical-grade reagent. No numerical purity, batch-specific isomer assay, ligand coverage or bound orientation is assigned.',
 'ode':'Terminal-alkene 1-octadecene is distinct from saturated octadecane; source grade and amounts remain separate from the reference graph.',
 'od':'Linear octadecane connectivity is the conventional interpretation of the source label, literally printed as 1-octadecane. No new 3D conformer or source geometry is generated.',
 'doa':'Di-n-octylamine connectivity represents the named secondary amine; its two octyl substituents are not branched carbon-chain isomers. No grade, supplier or 3D conformation is inferred. The SI oleylamine/NH2 naming conflict remains unresolved.',
 'top':'Free TOP reference, distinct from TOP–Se; source preparation/speciation and purity are separately scoped.',
 'topo':'Free TOPO reference, distinct from TOP. One cached illustrative conformer is not a surface-bound arrangement.',
 'top-se':'Named tri-n-octylphosphine selenide connectivity only. The precursor stock may contain other species; upstream preparation and exact solution speciation are unavailable. Cached embedding-only 3D is not promoted.',
 'hexane':'Straight-chain n-hexane is an illustrative named reference. The source reports hexane without grade, isomer assay, dose or measured solution geometry.',
 'toluene':'Named solvent reference; cold-quench temperature and volume are unreported and are not inferred from the model.',
 'ethanol':'Named precipitant reference; grade and wash volumes are not reported.',
 'acetone':'Glass-cleaning solvent reference, not a synthesis input; grade and cleaning volume are unreported.',
 'liquid-nitrogen':'NIST 14N2 reference distance 1.09768 Å represents one molecule, not liquid-phase packing. Used as detector coolant; no synthesis atmosphere or specimen addition is implied.'}
ck('Complete source identities',set(GRAPH)|set(SYMBOLS)==set(slots))
def fg(mol):
 out=[]
 for label,pat in [('Primary amine','[NX3;H2]'),('Secondary amine','[NX3;H1]'),('Carboxylic acid','[CX3](=[OX1])[OX2H]'),('Alkene','[CX3]=[CX3]'),('Phosphine centre','[PX3]'),('Phosphine oxide head','P=O'),('Phosphine selenide head','P=[Se]'),('Alcohol','[CX4][OX2H]'),('Carbonyl','[CX3]=[OX1]'),('Aromatic ring','c1ccccc1'),('Dinitrogen triple bond','N#N')]:
  ids=sorted({i for x in mol.GetSubstructMatches(Chem.MolFromSmarts(pat))for i in x})
  if ids:out.append({'label':label,'atomIndices':ids,'bondIndices':[b.GetIdx()for b in mol.GetBonds()if b.GetBeginAtomIdx()in ids and b.GetEndAtomIdx()in ids]})
 return out
H.fg=fg
def identity(mid,formula,name=None,kind='molecule'):
 m=slots[mid][0][2];eid='ghosh2012-'+mid+'-reference'
 return {'id':eid,'name':name or m['name'],'aliases':[m['name']],'formula':formula,'displayFormula':formula,'depictionKind':kind,'pubchemCid':None,'svgPath':'svg/'+eid+'.svg','model2dPath':None,'model3dPath':None,'functionalGroups':[],'sourceUrls':[source_url],'caption':'Source-qualified identity reference; not measured solution or surface geometry.','limitations':[LIMITS.get(mid,'No product atomic geometry or unreported species is assigned.')],'provenance':{'sourceDoi':'10.1021/ja212032q','sourceMaterialId':mid,'sourceLocators':m['evidence'],'canonicalIdentityFormula':m['formula'],'measuredCoordinates':False,'sourceAuditSha256':sha(P/'source-independent-audit/independent-audit-v2.json')},'binding_approved':False,'independentScientificAudit':'pending','published':False,'eligible_training':False}
def modelmol(raw,geometry=False):
 mol=graph_from_model(raw)
 if geometry:
  c=Chem.Conformer(mol.GetNumAtoms());c.Set3D(True)
  for i,a in enumerate(raw['atoms']):c.SetAtomPosition(i,(a['x'],a['y'],a['z']))
  mol.AddConformer(c);Chem.AssignStereochemistryFrom3D(mol)
 return mol
for mid,(smiles,formula,cached)in GRAPH.items():
 mol=Chem.MolFromSmiles(smiles);ck(mid+' formula',rdMolDescriptors.CalcMolFormula(mol)==formula);e=identity(mid,formula)
 e['caption']=LIMITS[mid];e['provenance']['identityBasis']='Conventional source-named 2D identity; drawing units, not measured coordinates.'
 if cached:
  old=base[cached];save('reference-snapshots/entry-'+cached+'.json',old)
  for k in ['svgPath','model2dPath','model3dPath']:
   if old.get(k):ck(cached+' cache '+k,sha(REG/old[k])==old['assetHashes'][k]);snap(REG/old[k],old[k])
  raw=read(REG/old['model2dPath']);ck(mid+' cached graph',Chem.MolToSmiles(Chem.RemoveHs(graph_from_model(raw)),isomericSmiles=False)==Chem.MolToSmiles(mol,isomericSmiles=False))
  e['pubchemCid']=old.get('pubchemCid');e['sourceUrls']=list(dict.fromkeys([source_url]+[u for u in old.get('sourceUrls',[])if 'pubchem' in u or 'nist' in u]))
  e['provenance'].update(retainedRegistryId=cached,retainedEntrySha256=jsha(old),retainedModel2dSha256=sha(REG/old['model2dPath']),connectivitySmiles=smiles,identityBasis='Exact cached named connectivity; source grade, role and quantities separately linked.')
  qual={'material_id':mid,'cached_id':cached,'cached_entry_snapshot':'reference-snapshots/entry-'+cached+'.json','graph_identity_matches':True,'other_paper_display_metadata_removed':True}
  if old.get('model3dPath')and mid!='top-se':
   raw3=read(REG/old['model3dPath']);ck(mid+' exact 3D stereochemical reference',canon(modelmol(raw3,True))==canon(mol));new=deepcopy(raw3)
   new.update(id=e['id'],name=e['name'],caption='Retained reference coordinates; '+LIMITS[mid],notes=['Original atom, bond and coordinate arrays unchanged. '+LIMITS[mid]],functionalGroups=fg(graph_from_model(raw3)),source={'referenceUrls':e['sourceUrls'],'retainedModelType':raw3.get('modelType'),'method':raw3.get('method'),'conformerGeneration':raw3.get('conformerGeneration')})
   e['model3dPath']='models/'+e['id']+'-3d.json';save(e['model3dPath'],new)
   ck(mid+' unchanged 3D arrays',new['atoms']==raw3['atoms']and new['bonds']==raw3['bonds']);qual.update(retainedModel3dSha256=sha(REG/old['model3dPath']),atomic_arrays_unchanged=True)
   lengths=[math.dist([new['atoms'][b['a']][k]for k in ['x','y','z']],[new['atoms'][b['b']][k]for k in ['x','y','z']])for b in new['bonds']]
   ck(mid+' finite plausible coordinates',all(math.isfinite(a[k])for a in new['atoms']for k in ['x','y','z'])and all(.6<x<2.4 for x in lengths))
   if mid=='liquid-nitrogen':ck('NIST nitrogen distance',abs(lengths[0]-1.09768)<1e-8)
  qualifications.append(qual)
 body=m2d(e,mol);render(e,frame(e,body,'2D identity · highlighted functional groups · source grade and role separately qualified'))
 if mid=='doa':
  n=next(a for a in mol.GetAtoms()if a.GetSymbol()=='N');ck('Dioctylamine secondary NH',n.GetTotalNumHs()==1 and n.GetDegree()==2);rw=Chem.RWMol(mol);rw.RemoveAtom(n.GetIdx());ck('Two straight eight-carbon substituents',sorted(len(x)for x in Chem.GetMolFrags(rw.GetMol()))==[8,8]and all(a.GetDegree()<=2 for a in mol.GetAtoms()))
 if mid=='od':ck('Octadecane saturated linear C18',mol.GetNumAtoms()==18 and all(a.GetDegree()<=2 for a in mol.GetAtoms())and all(b.GetBondTypeAsDouble()==1 for b in mol.GetBonds()))
for mid,(name,formula,lines,limit)in SYMBOLS.items():
 e=identity(mid,formula,name,'symbolic_context');e['caption']=limit;e['limitations']=[limit,'Symbolic identity only; no molecular or nanocrystal coordinates, discrete complex or product/sample binding.'];body='<rect x="75" y="155" width="950" height="360" rx="23" fill="#f2f8fa" stroke="#b4cbd7"/>'
 for j,line in enumerate(lines):body+=tx(550,240+j*78,line,27 if j==0 else 22)
 render(e,frame(e,body,'Source material / support identity · no inferred crystal or surface geometry'))
by_mid={e['provenance']['sourceMaterialId']:e for e in entries}
# Preserve actual local primary cache records, without any new retrieval.
raw=M/'research-assets/quality-20260918/molecules/raw';primary_rows=[]
for mid,(_,_,cached)in GRAPH.items():
 if not cached:continue
 candidates=[raw/(cached+'-properties.json'),raw/(cached+'-pubchem-2d.sdf')]
 extra={'top-se':['trioctylphosphine-selenide-pubchem-12163534-2d.sdf'],'top':['trioctylphosphine-pubchem-20851-2d.sdf'],'topo':['trioctylphosphine-oxide-pubchem-65577-2d.sdf','topo-rdkit-etkdgv3-mmff94s-illustrative-3d.sdf'],'oa':['oleic-acid-pubchem-445639-3d.sdf'],'ola':['oleylamine-pubchem-5356789-3d.sdf'],'ode':['1-octadecene-pubchem-8217-3d.sdf'],'toluene':['toluene-pubchem-1140-3d.sdf']}
 candidates += [M/'research-assets'/n for n in extra.get(mid,[])]
 if mid=='acetone':candidates += list((M/'research-assets/incoming-paper-monitor/reviews/j100108a019/molecular-assets/raw').glob('acetone-*'))
 if mid=='liquid-nitrogen':candidates += [M/'research-assets/incoming-paper-monitor/batches/20260919-five-paper-pilot/ja0496423/visuals/molecules/raw'/n for n in ['nitrogen-nist-extracted-reference.json','nitrogen-nist-web-tool-excerpt.txt']]
 for p in sorted(set(candidates),key=str):
  if not p.exists():continue
  dst=snap(p,'primary/'+mid+'/'+p.name);row={'material_id':mid,'snapshot_path':str(dst.relative_to(O)),'sha256':sha(dst),'new_retrieval':False}
  if p.suffix=='.sdf':
   mm=Chem.SDMolSupplier(str(dst),removeHs=False)[0];ck(mid+' cached SDF connectivity '+p.name,Chem.MolToSmiles(Chem.RemoveHs(mm),isomericSmiles=False)==Chem.MolToSmiles(Chem.MolFromSmiles(GRAPH[mid][0]),isomericSmiles=False));row['graph_checked']=True
  primary_rows.append(row)
def qfmt(q):
 def v(x):return str(int(x))if isinstance(x,(int,float))and x==int(x)else str(x)
 if q.get('value')is not None:s=v(q['value'])
 elif q.get('minimum')is not None and q.get('maximum')is not None:s=v(q['minimum'])+'–'+v(q['maximum'])
 elif q.get('minimum')is not None:s=('> 'if q.get('minimum_exclusive')else'≥ ')+v(q['minimum'])
 elif q.get('maximum')is not None:s=('< 'if q.get('maximum_exclusive')else'≤ ')+v(q['maximum'])
 else:return q.get('raw_text')or'Not reported'
 return('≈ 'if q.get('approximate')else'')+s+(' '+q.get('unit','')if q.get('unit')else'')
def qlink(rid,ptr,label,kind):
 x=records[rid]
 for t in ptr.strip('/').split('/'):x=x[int(t)]if isinstance(x,list)else x[t]
 return {'record_id':rid,'json_pointer':ptr,'field':label,'meaning':kind,'quantity':deepcopy(x),'display_value':qfmt(x)}
# Explicit semantic mapping; generic word matching does not assign a dose to every input.
QMAP={
 ('core-standard-route','topo'):[('core-charge','topo_mass')],('core-standard-route','ode'):[('core-charge','ode_volume'),('core-inject','ode_injection_volume')],('core-standard-route','cd-oleate'):[('core-charge','cd_oleate_amount')],('core-standard-route','top-se'):[('core-inject','top_se_amount')],('core-standard-route','ola'):[('core-inject','oleylamine_volume')],
 ('core-large-variant','cd-oleate'):[('large-feed','additional_cd_oleate')],('core-large-variant','top-se'):[('large-feed','additional_top_se')],
 ('optimized-shell-route','cdse-core'):[('shell-charge','washed_core_amount')],('optimized-shell-route','ola'):[('shell-charge','oleylamine_volume')],('optimized-shell-route','od'):[('shell-charge','od_volume')],('optimized-shell-route','cd-oleate'):[('shell-passivate','cd_passivation_equivalent')],
 ('constant-s-variant','sulfur'):[('constant-s-grow','sulfur_total_equivalent')]}
def refs_for(rid,mid):
 out=[]
 for opid,k in QMAP.get((rid.removeprefix('ghosh-2012-'),mid),[]):
  oi,op=next((i,o)for i,o in enumerate(records[rid]['operations'])if o['id']==opid);assert k in op['parameters'];out.append(qlink(rid,f'/operations/{oi}/parameters/{k}',k,'source_operation_charge_or_equivalent'))
 return out
gr={};source_rid='ghosh-2012-source-materials'
for mid,n in {'cdo':1,'oa':2,'ode':3,'od':4,'sulfur':5,'selenium':6,'top':7,'topo':8}.items():
 i=next(i for i,m in enumerate(records[source_rid]['measurements'])if m['id']=='ghosh2012-materials-q'+str(n));gr[mid]=qlink(source_rid,f'/measurements/{i}/value','source_purity','source_wide_grade_not_product_yield')
rr,i=next((rid,i)for rid,r in records.items()for i,m in enumerate(r['measurements'])if 'rhodamine' in m['property'].lower()and 'purity' in m['property'].lower());gr['r6g']=qlink(rr,f'/measurements/{i}/value','reference_dye_purity','source_wide_grade_not_product_yield')
bindings={'schemaVersion':'1.0','source_id':'ghosh2012','status':'private_author_proposal_pending_independent_molecular_audit','recordBindings':{},'bindingNotes':{},'binding_approved':False,'published':False,'eligible_training':False};slot_rows=[]
source_mats={m['id']:m for m in read(P/'source-facts.json')['materials']}
for rid,r in records.items():
 if not r['materials']:continue
 bindings['recordBindings'][rid]={};bindings['bindingNotes'][rid]={}
 for i,m in enumerate(r['materials']):
  mid=m['id'];e=by_mid[mid];refs=refs_for(rid,mid);grades=[deepcopy(gr[mid])]if mid in gr else[]
  caption=m['name']+'; '+m['role'].replace('_',' ')+'; '+m['stage'].replace('_',' ')+'. '+source_mats[mid]['scope_note']
  if grades:caption+=' Reported source purity: '+grades[0]['display_value']+'.'
  if refs:caption+=' Source-scoped quantities: '+'; '.join(x['field'].replace('_',' ')+': '+x['display_value']for x in refs)+'.'
  else:caption+=' No separate dose is assigned to this slot.'
  caption+=' '+e['limitations'][0]+' Storage conditions are not reported in the supplied sources.'
  context=[]
  wanted={('solvent-ligand-series','ola'):['initial_amine','associated_shell_count'],('solvent-ligand-series','oa'):['oa_after_fourteen_layers','associated_shell_count','cd_oa_option_1','cd_oa_option_2'],('solvent-ligand-series','od'):['dilution_starting_shell_count','initial_dot_concentration','diluted_dot_concentration'],('stoichiometry-series','oa'):['withdrawal','oa_factor','oa_change_shell_span'],('optimized-shell-route','oa'):['initial_cycle_span','initial_cd_oa','later_cd_oa']}.get((rid.removeprefix('ghosh-2012-'),mid),[])
  for mi,measurement in enumerate(r['measurements']):
   if measurement['property']in wanted:context.append(qlink(rid,f'/measurements/{mi}/value',measurement['property'],'reported_comparison_or_formulation_context_not_new_material_dose'))
  if context:caption+=' Separate formulation/comparison context: '+'; '.join(q['field'].replace('_',' ')+': '+q['display_value']for q in context)+'. These describe the named comparison, not an additional charge or a universal formulation.'
  note={'record_id':rid,'material_id':mid,'json_pointer':f'/materials/{i}','canonical_record_sha256':sha(C/(rid+'.json')),'registry_id':e['id'],'entry_sha256':jsha(e),'canonical_identity':deepcopy(m),'quantity_links':refs,'grade_context_links':grades,'formulation_context_links':context,'viewOverrides':{'name':m['name'],'caption':caption,'limitations':deepcopy(e['limitations'])},'binding_approved':False,'source_specific_join':'Exact material slot only; dose references remain action-specific, source-wide grade separately labeled. No stock reaction, storage condition or product/sample binding is invented.'}
  bindings['recordBindings'][rid][mid]=e['id'];bindings['bindingNotes'][rid][mid]=note;slot_rows.append(note)
stock_rows=[];contexts=[]
for rid,r in records.items():
 for si,st in enumerate(r['stocks']):
  comps=[]
  for ci,c in enumerate(st['components']):
   mid=c['material_id'];mi=next(i for i,m in enumerate(r['materials'])if m['id']==mid);refs=[qlink(rid,f'/stocks/{si}/components/{ci}/quantities/{k}',k,'whole_formulation_component_charge_not_additional_event')for k in c['quantities']]
   role='solvent'if mid in ['od','ode']else'ligand_cosolvent'if mid=='ola'else'free_acid_ligand_component'if mid=='oa'else'named_precursor_solute'
   comps.append({'material_id':mid,'registry_id':by_mid[mid]['id'],'role':role,'json_pointer':f'/stocks/{si}/components/{ci}','material_json_pointer':f'/materials/{mi}','source_quantities':deepcopy(c['quantities']),'quantity_links':refs,'binding_approved':False})
  cqs=[qlink(rid,f'/stocks/{si}/concentrations/{k}',k,'reported_stock_concentration_not_per_layer_dose')for k in st['concentrations']]
  summary=' + '.join(next(m['name']for m in r['materials']if m['id']==z['material_id'])+': '+('; '.join(q['display_value']for q in z['quantity_links'])or'component amount unreported')for z in comps)
  if cqs:summary+='; reported precursor concentration '+cqs[0]['display_value']
  limit='Whole formulation, not an additional charge event. Final mixture volume, per-layer delivered volume and dissolved speciation are unreported.'
  if st['id']=='top-se-injection':limit='Whole injection formulation, not an additional charge event. Final mixture volume, upstream TOP–Se preparation and dissolved speciation are unreported.'
  if st['id']=='cd-oleate-stock':limit+=' Cd:OA 1:4 for the first 5–8 cycles and then 1:10 are formulation ratios, not molecular complex stoichiometry.'
  if st['id']=='s-od-stock':limit+=' No sulfur allotrope or dissolved molecular species is assigned.'
  row={'record_id':rid,'stock_id':st['id'],'json_pointer':f'/stocks/{si}','canonical_record_sha256':sha(C/(rid+'.json')),'components':comps,'concentrations':deepcopy(st['concentrations']),'concentration_links':cqs,'scope':st['scope'],'evidence':deepcopy(st['evidence']),'solution_quantity_links':[],'display_summary':summary,'display_limit':limit,'binding_approved':False};stock_rows.append(row)
  ctx={'record_id':rid,'id':'ghosh2012-'+st['id'],'label':{'top-se-injection':'TOP–Se / oleylamine / ODE injection','s-od-stock':'Sulfur in octadecane','cd-oleate-stock':'Cadmium oleate / OA in octadecane'}[st['id']],'scope':summary+'. '+limit,'components':[{'material_id':c['material_id'],'registry_id':c['registry_id'],'role':c['role'],'label':next(m['name']for m in r['materials']if m['id']==c['material_id']),'viewOverrides':{'caption':summary+'. '+limit,'limitations':[limit,'Independent component references; no dissolved aggregate or surface geometry.']}}for c in comps],'binding_approved':False};contexts.append(ctx)
  body='';width=1000/len(comps)
  for j,c in enumerate(comps):
   x=45+j*width;e=by_mid[c['material_id']];body+=f'<rect x="{x}" y="145" width="{width-15}" height="230" rx="15" fill="#eff7fa" stroke="#bfd3dc"/>'+wrapped(c['role'].replace('_',' '),x+15,184,23,17,22)+tx(x+(width-15)/2,252,e['displayFormula']or'Cd-oleate identity',21)+wrapped('; '.join(q['display_value']for q in c['quantity_links'])or'Amount unreported',x+15,310,25,18,23)
  body+=wrapped(('Concentration: '+cqs[0]['display_value']+'. 'if cqs else'')+limit,45,415,99,17,23)
  e={'name':ctx['label'],'caption':ctx['scope'],'displayFormula':'Components separately inspectable · no inferred stock speciation'};svg=frame(e,body,'Source-bound formulation · quantities are not counted twice');(O/'stock-svg'/(st['id']+'.svg')).write_text(svg,encoding='utf-8');raster(svg,O/'stock-previews'/(st['id']+'.png'))
# Every retained 3D coordinate set receives an actual static preview for review.
for e in entries:
 if not e['model3dPath']:continue
 m=read(O/e['model3dPath']);xy=[(a['x']+.32*a['z'],a['y']+.16*a['z'])for a in m['atoms']];lo=[min(a[j]for a in xy)for j in [0,1]];hi=[max(a[j]for a in xy)for j in [0,1]];sc=min(820/max(hi[0]-lo[0],1),330/max(hi[1]-lo[1],1));pts=[(140+(a[0]-lo[0])*sc,160+(a[1]-lo[1])*sc)for a in xy];body=''
 for b in m['bonds']:
  a,z=pts[b['a']],pts[b['b']];body+=f'<path d="M{a[0]} {a[1]} L{z[0]} {z[1]}" stroke="#9badb8" stroke-width="5"/>'
 for a,(x,y)in zip(m['atoms'],pts):body+=f'<circle cx="{x}" cy="{y}" r="14" fill="'+{'C':'#688398','H':'#edf2f5','O':'#e27375','N':'#728dce','P':'#d0a156'}.get(a['element'],'#b494bd')+'" stroke="#78909e"/>'+tx(x,y+5,a['element'],12,'#153344')
 raster(frame(e,body,'Projection of unchanged cached reference coordinates · Å · not source-measured geometry'),O/'conformer-previews'/(e['id']+'.png'))
ck('All identities/slots/stocks/components',len(entries)==25 and len(slot_rows)==88 and len(stock_rows)==3 and sum(len(x['components'])for x in stock_rows)==8)
for p,h in inputs.items():ck('Unchanged input '+p,sha(p)==h)
save('registry-additions.json',{'schemaVersion':'1.0','source_id':'ghosh2012','status':'private_author_proposal','entries':entries,'binding_approved':False});save('bindings-proposal.json',bindings)
save('material-slot-map.json',{'schema':'mattersyn-molecular-slot-proposal/1','material_slot_count':88,'identity_count':25,'slots':slot_rows,'independent_audit':'pending'})
save('stock-component-map.json',{'schema':'mattersyn-stock-component-proposal/1','stock_count':3,'component_count':8,'stocks':stock_rows,'independent_audit':'pending'});save('solution-components-proposal.json',{'schemaVersion':'1.0','contexts':contexts,'binding_approved':False})
save('reference-qualification.json',{'status':'author_checks_only','qualifications':qualifications,'retained_primary_artifacts':primary_rows,'new_2d_identity_references':['od','doa'],'rejected':[{'id':'base nitrogen 1.460 Å','reason':'Qualified NIST distance reference used instead.'},{'id':'TOPSe 3D','reason':'Embedding-only model intentionally not promoted; 2D identity suffices.'},{'id':'R6G chloride assumption','reason':'Counterion not source-qualified.'},{'id':'Cd-oleate discrete complex','reason':'Coordination, hydration and dissolved species unreported.'}],'normalization':'Other-paper roles/grades removed from display metadata; reference identity and actual source-grade notes remain distinct.'})
save('reference-snapshots/manifest.json',{'snapshots':snapshots,'note':'Immutable local cache copies; no new retrieval.'});save('input-bindings.json',inputs)
counts={'entries':len(entries),'material_slots':len(slot_rows),'stocks':len(stock_rows),'stock_components':8,'models_2d':13,'retained_illustrative_3d':sum(bool(e['model3dPath'])for e in entries),'symbolic_materials':12,'new_2d_graphs':2,'cached_graph_bindings':11,'new_product_bindings':0,'new_atomic_coordinates':0}
save('author-validation.json',{'schema':'mattersyn-molecule-author-validation/1','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'automated_author_checks_passed_manual_visual_review_pending','counts':counts,'check_count':len(checks),'checks':checks,'independent_molecular_audit':'pending','canonical_independent_audit':'pending_at_authoring','binding_approved':False,'browser_validation':'not_claimed','bound_files':inputs})
for folder,prefix in [('previews','identities'),('stock-previews','stocks'),('conformer-previews','conformers')]:
 imgs=sorted((O/folder).glob('*.png'))
 for start in range(0,len(imgs),6):
  canvas=Image.new('RGB',(1500,1410),'#dce7ed');draw=ImageDraw.Draw(canvas)
  for j,p in enumerate(imgs[start:start+6]):
   im=Image.open(p).convert('RGB');im.thumbnail((730,425));x=10+j%2*750;y=30+j//2*470;canvas.paste(im,(x,y));draw.text((x,y+430),p.stem,fill='#203a4b')
  canvas.save(O/'contacts'/f'{prefix}-{start//6+1:02}.png')
print(json.dumps({'counts':counts,'author_checks':len(checks),'status':'Generated; persisted checks and actual visual views pending.'}))
