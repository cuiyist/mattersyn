"""Private Sasongko reference assets: no network, Site writes or generated 3D coordinates."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,sys,html,textwrap,math
O=Path(__file__).resolve().parent;J=O.parents[1];M=J.parents[4];R=M/'recipe-atlas/dist/assets/chemical-registry';C=J/'canonical-proposal/v1';S=J/'source-extraction-revision-2'
assert not (O/'package-freeze.json').exists()
sys.dont_write_bytecode=True
sys.path[:0]=[str(M/'research-assets/rdkit-runtime'),str(M/'research-assets/corpus-20260917/runtime')]
from rdkit import Chem,rdBase
from rdkit.Chem import rdDepictor,rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
import pymupdf
from PIL import Image,ImageDraw
for d in ['models','svg','previews','conformer-previews','stock-svg','stock-previews','contacts','reference-snapshots/entries','reference-snapshots/models','reference-snapshots/svg','reference-snapshots/primary']:(O/d).mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):(O/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def esc(t):return html.escape(str(t),quote=True)
def text(x,y,t,size=19,anchor='start'):return f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" text-anchor="{anchor}" fill="#294658">{esc(t)}</text>'
def raster(svg,p):
 d=pymupdf.open(stream=svg.encode(),filetype='svg');d[0].get_pixmap(alpha=False).save(str(p));d.close()
checks=[];snapshots=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
def snap(p,rel):
 p=Path(p);d=O/'reference-snapshots'/rel;d.parent.mkdir(parents=True,exist_ok=True)
 if d.exists():ck('preserved snapshot '+rel,sha(d)==sha(p))
 else:d.write_bytes(p.read_bytes())
 snapshots.append({'original_path':str(p),'snapshot':str(d),'sha256':sha(d)})
 return d
ck('Exact canonical freeze',sha(C/'package-freeze.json')=='3cab2fe6181dbf2149b2a0ac59f4a80d99c05cab4870342e141815c904549fb5')
ck('Exact source revision2 freeze',sha(S/'package-freeze.json')=='d34778349e9942a73a1d275536af354e93d52739692e689fe2f12d394db7fddc')
sf=read(S/'source-facts.json');materials={x['id']:x for x in sf['materials']};ck('13 source identities',len(materials)==13)
basepath=O/'reference-snapshots/registry-base.json'
if not basepath.exists():snap(R/'registry.json','registry-base.json')
base={x['id']:x for x in read(basepath)['entries']}
spec={
 'formamidine-acetate':{'smiles':'[NH2+]=C[NH2].CC(=O)[O-]','formula':'C3H8N2O2','cached':None},
 'oa':{'smiles':'CCCCCCCC/C=C\\CCCCCCCC(=O)O','formula':'C18H34O2','cached':'lian2021-oleic-acid-reference'},
 'oam':{'smiles':'CCCCCCCC/C=C\\CCCCCCCCN','formula':'C18H37N','cached':'ghosh2012-ola-reference'},
 'ode':{'smiles':'C=CCCCCCCCCCCCCCCCC','formula':'C18H36','cached':'friedfeld2019-ode-reference'},
 'toluene':{'smiles':'Cc1ccccc1','formula':'C7H8','cached':'friedfeld2019-toluene-reference'},
 'acetonitrile':{'smiles':'CC#N','formula':'C2H3N','cached':'friedfeld2019-acetonitrile-reference'},
 'nitrogen':{'smiles':'N#N','formula':'N2','cached':'friedfeld2019-nitrogen-reference'}}
scope={
 'pbi2':'Lead(II) iodide precursor; source supplier and purity are unspecified. Dissolved coordination and bulk crystal structure are not supplied.',
 'formamidine-acetate':'Formamidine acetate salt, 99%, Sigma-Aldrich. Whole FA-stock preparation uses 0.1042 g; this is distinct from the later 0.51 mL stock transfer.',
 'oa':'Oleic acid, 99%, Sigma-Aldrich. The 0.8 mL whole-stock charge is distinct from the selected 0.4, 0.6 or 0.8 mL QD-route charge.',
 'oam':'Oleylamine, 70%, Sigma-Aldrich. The QD route uses 0.2 mL; no batch-specific chain or isomer assay is reported.',
 'ode':'1-Octadecene, >90%, TCI. Whole-stock and QD-route quantities are separate; all chemicals are used without further purification.',
 'toluene':'Toluene, 99.8%, anhydrous, Sigma-Aldrich; washing solvent. No distillation, molecular-sieve treatment or storage condition is added.',
 'acetonitrile':'Acetonitrile, 99.8%, anhydrous, Sigma-Aldrich; washing antisolvent. Absolute washing amounts are unreported.',
 'hexane':'Hexane, 95%, anhydrous, Sigma-Aldrich; redispersion solvent. The source does not specify the n-isomer, volume or final concentration.',
 'nitrogen':'Nitrogen is the synthesis atmosphere and the FA-stock high-temperature atmosphere. Its purity, flow and pressure are unreported; acquisition atmosphere is not inherited.',
 'fa-oleate':'Prepared FA-oleate is an operational stock identity. No final stock concentration, solution coordination or storage is reported.',
 'fapbi3':'FAPbI3 is a source phase identity. Phase assignments depend on the particular growth or measurement context; no QD atomic coordinates are supplied.',
 'delta-fapbi3':'The source identifies δ-FAPbI3 as a competing component at 25 °C growth. This is not every product or a complete specimen composition.',
 'pbo2-reference':'PbO2 is a cited Raman-degradation interpretation, not a current detected QD component or synthesis precursor.'}
limits={
 'formamidine-acetate':'Formal disconnected formamidinium and acetate ions show named-salt connectivity and one resonance form. The printed neutral-pair formula is retained separately. This 2D drawing does not establish ion-pair geometry, proton-transfer equilibrium, hydrate, crystal or dissolved speciation.',
 'oa':'A named cis-(Z)-oleic-acid reference illustrates the free molecule. The source reports no cis/trans assay. This does not establish oleate coordination, surface coverage or a bound-ligand geometry.',
 'oam':'A named cis-(Z)-oleylamine reference illustrates one free component of the 70% reagent. It does not assay technical impurities, isomer populations, protonation or bound orientation.',
 'ode':'Free 1-octadecene reference with a terminal alkene. The >90% lower-bound purity is retained; no pure-batch or unique solution-conformer claim is made.',
 'toluene':'Free toluene reference; no solvent association, pure solution structure or adsorption geometry is implied.',
 'acetonitrile':'Free acetonitrile connectivity. The retained locally computed ETKDGv3/MMFF94s conformer is illustrative; no measured solvent or solution geometry is claimed.',
 'nitrogen':'Retained NIST ground-state 14N2 reference distance 1.09768 Å, with arbitrary orientation. This is not a source gas isotopic assay, measured molecule, liquid arrangement or reactor geometry.'}
symbols={
 'pbi2':('PbI2','Bulk salt identity','No discrete molecule or coordination model'),
 'hexane':('Hexane · isomer unspecified','Redispersion solvent','No n-hexane graph assigned'),
 'fa-oleate':('Prepared FA-oleate','Operational stock identity','Solution speciation and concentration unknown'),
 'fapbi3':('FAPbI3','Source phase identity','No QD coordinates or single-phase assignment here'),
 'delta-fapbi3':('δ-FAPbI3','Source-assigned competing phase','Context-specific identity; no atomic model'),
 'pbo2-reference':('PbO2','Cited Raman interpretation','Not detected as a current QD component')}
ck('All identities planned once',set(spec)|set(symbols)==set(materials) and not(set(spec)&set(symbols)))
primary_dirs={
 'oa':J.parent/'acsami.1c18038/visuals/molecules/reference-snapshots/primary/oleic-acid',
 'oam':J.parent/'ja212032q/visuals/molecules/reference-snapshots/primary/ola',
 'ode':J.parent/'ja212032q/visuals/molecules/reference-snapshots/primary/ode',
 'toluene':J.parent/'ja212032q/visuals/molecules/reference-snapshots/primary/toluene',
 'nitrogen':J.parent/'ja212032q/visuals/molecules/reference-snapshots/primary/liquid-nitrogen'}
def molmodel(m,coords=False):
 rw=Chem.RWMol()
 for a in m['atoms']:
  at=Chem.Atom(a['element']);at.SetFormalCharge(a.get('formalCharge',0));at.SetIsotope(a.get('isotope',0))
  if 'implicitHydrogenCount' in a:at.SetNoImplicit(True);at.SetNumExplicitHs(a['implicitHydrogenCount'])
  rw.AddAtom(at)
 for b in m['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
 mol=rw.GetMol();Chem.SanitizeMol(mol)
 if coords:
  conf=Chem.Conformer(len(m['atoms']));conf.Set3D(m.get('representation')=='3d')
  for i,a in enumerate(m['atoms']):conf.SetAtomPosition(i,(a['x'],a['y'],a['z']))
  mol.AddConformer(conf)
 return mol
def can(m):return Chem.MolToSmiles(Chem.RemoveHs(m),isomericSmiles=False)
patterns={'formamidine-acetate':[('Formamidinium resonance group','[NH2+]=[CH][NH2]'),('Acetate carboxylate','[CX3](=[OX1])[O-]')],'oa':[('Carboxylic acid','C(=O)[OH]'),('Cis reference alkene','[C]=[C]')],'oam':[('Primary amine','[NX3;H2;+0]'),('Cis reference alkene','[C]=[C]')],'ode':[('Terminal alkene','[CH2]=[CH]')],'toluene':[('Aromatic ring','c1ccccc1')],'acetonitrile':[('Nitrile','C#N')],'nitrogen':[('Dinitrogen triple bond','N#N')]}
def groups(mid,mol):
 out=[]
 for label,sm in patterns[mid]:
  matches=mol.GetSubstructMatches(Chem.MolFromSmarts(sm));ck(mid+' chemical highlight '+label,bool(matches))
  for ids in matches:out.append({'label':label,'atomIndices':sorted(ids),'bondIndices':[b.GetIdx() for b in mol.GetBonds() if b.GetBeginAtomIdx() in ids and b.GetEndAtomIdx() in ids]})
 return out
models={};quals=[]
for mid,sp in spec.items():
 mol=Chem.MolFromSmiles(sp['smiles']);ck(mid+' exact reference formula',rdMolDescriptors.CalcMolFormula(mol)==sp['formula']);eid='sasongko2025-'+mid+'-reference';cached=sp['cached'];prov={'identityBasis':'Source-named formal salt components; source-specified neutral-pair formula retains the same elemental sum. No external coordinate source.','referenceSmiles':sp['smiles'],'retainedRegistryId':cached,'sourceMaterialId':mid,'measuredCoordinates':False};old2=old3=None
 if cached:
  e=base[cached];save('reference-snapshots/entries/'+cached+'.json',e)
  for k in ['svgPath','model2dPath','model3dPath']:
   ck(cached+' cached hash '+k,sha(R/e[k])==e['assetHashes'][k]);snap(R/e[k],e[k])
  old2=read(R/e['model2dPath']);old3=read(R/e['model3dPath']);ck(mid+' retained 2D connectivity',can(molmodel(old2))==can(mol));ck(mid+' retained 3D connectivity',can(molmodel(old3))==can(mol))
  prov.update(identityBasis='Exact cached reference graph; current source role and grade are separate.',retainedModel2dSha256=sha(R/e['model2dPath']),retainedModel3dSha256=sha(R/e['model3dPath']))
  if mid in primary_dirs:
   for fp in sorted(primary_dirs[mid].iterdir()):
    if fp.is_file():snap(fp,'primary/'+mid+'/'+fp.name)
  if mid in ['oa','oam','ode','toluene']:
   sdf=next(primary_dirs[mid].glob('*3d.sdf'));pm=Chem.SDMolSupplier(str(sdf),removeHs=False)[0];ck(mid+' retained primary SDF graph',can(pm)==can(mol))
   pc=pm.GetConformer();ck(mid+' source SDF atom arrays exact',len(old3['atoms'])==pm.GetNumAtoms() and all(a['element']==pm.GetAtomWithIdx(i).GetSymbol() and all(abs(a[k]-getattr(pc.GetAtomPosition(i),k))<1e-7 for k in ['x','y','z']) for i,a in enumerate(old3['atoms'])))
  if mid in ['oa','oam']:
   ster=molmodel(old3,True);Chem.AssignStereochemistryFrom3D(ster);ck(mid+' retained 3D cis stereochemistry',Chem.MolToSmiles(Chem.RemoveHs(ster))==Chem.MolToSmiles(mol))
 if old2:atoms=deepcopy(old2['atoms']);bonds=deepcopy(old2['bonds']);mol2=molmodel(old2,True)
 else:
  rdDepictor.Compute2DCoords(mol);cf=mol.GetConformer();atoms=[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':cf.GetAtomPosition(a.GetIdx()).x,'y':cf.GetAtomPosition(a.GetIdx()).y,'z':0.0,'formalCharge':a.GetFormalCharge(),'isotope':a.GetIsotope(),'implicitHydrogenCount':a.GetTotalNumHs()} for a in mol.GetAtoms()];bonds=[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble()} for b in mol.GetBonds()];mol2=mol
 m2={'id':eid,'name':materials[mid]['name']+' reference','formula':sp['formula'],'sourceFormula':materials[mid]['source_formula_or_abbreviation'],'representation':'2d','has3D':False,'allowRotation':False,'coordinateUnits':'arbitrary drawing units','indexConvention':'zero-based','atoms':atoms,'bonds':bonds,'functionalGroups':groups(mid,mol2),'modelType':'Reference 2D connectivity; not a measured geometry','sourceType':'Qualified connectivity drawing','source':prov,'connectivitySmiles':sp['smiles'],'caption':limits[mid],'eligible_training':False}
 p2='models/'+eid+'-2d.json';save(p2,m2);p3=None
 if old3:
  m3={k:deepcopy(old3[k]) for k in ['atoms','bonds','coordinateUnits','indexConvention','modelType','pubchemCid','iupacName','sdfUrl','assetFile','method','computedBy','conformerGeneration','construction','referenceDistanceAngstrom','referenceIsotopologue','coordinateSource','sourceType'] if k in old3}
  m3.update(id=eid,name=m2['name'],formula=sp['formula'],representation='3d',has3D=True,allowRotation=True,caption=limits[mid]+' '+old3['modelType']+'.',notes=[limits[mid],'Original retained atom/bond/coordinate arrays are unchanged.'],source={'retained_model_sha256':prov['retainedModel3dSha256'],'retained_reference_provenance':deepcopy(old3.get('source'))},functionalGroups=groups(mid,molmodel(old3)),eligible_training=False)
  # Normalize only the public provenance wording; prior source-conditioned provenance is private in the snapshot.
  if mid=='acetonitrile':m3['source']={'software':old3['computedBy'],'method':old3['method'],'retained_model_sha256':prov['retainedModel3dSha256'],'coordinate_source':'Retained locally computed free-acetonitrile reference; no source sample geometry.'}
  if mid=='oam':m3['source']={'referenceUrls':['https://pubchem.ncbi.nlm.nih.gov/compound/5356789'],'retained_model_sha256':prov['retainedModel3dSha256']}
  p3='models/'+eid+'-3d.json';save(p3,m3);ck(mid+' coordinate arrays immutable',m3['atoms']==old3['atoms'] and m3['bonds']==old3['bonds'])
 models[mid]={'mol':mol2,'m2':m2,'p2':p2,'p3':p3,'provenance':prov}
 quals.append({'material_id':mid,'formula':sp['formula'],'reference_smiles':sp['smiles'],'literal_source_formula':materials[mid]['source_formula_or_abbreviation'],'fragment_count':len(Chem.GetMolFrags(mol)),'net_charge':sum(a.GetFormalCharge() for a in mol.GetAtoms()),'model2dPath':p2,'model3dPath':p3,'limitations':limits[mid],'provenance':prov})
def frame(mid,body,note,formula):
 lines=textwrap.wrap(scope[mid],108)+['']+textwrap.wrap(note,108);h=max(780,583+len(lines)*24+30)
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{h}" viewBox="0 0 1100 {h}"><rect x="1" y="1" width="1098" height="{h-2}" rx="18" fill="white" stroke="#c4d7df"/>'+text(36,50,materials[mid]['name'],26)+text(550,105,formula,23,'middle')+body+f'<rect x="28" y="548" width="1044" height="{h-575}" rx="12" fill="#edf5f8"/>'
 for i,l in enumerate(lines):svg+=text(48,580+i*24,l,17)
 return svg+'</svg>'
entries=[]
for mid,mat in materials.items():
 eid='sasongko2025-'+mid+'-reference';model=models.get(mid)
 if model:
  d=rdMolDraw2D.MolDraw2DSVG(1000,375);d.drawOptions().padding=.12;d.drawOptions().includeRadicals=False
  ids=sorted({i for g in model['m2']['functionalGroups'] for i in g['atomIndices']});rdMolDraw2D.PrepareAndDrawMolecule(d,model['mol'],highlightAtoms=ids,highlightAtomColors={i:(.73,.88,.87) for i in ids});d.FinishDrawing();s=d.GetDrawingText();s=s[s.index('>',s.index('<svg'))+1:s.rindex('</svg>')]
  body='<g transform="translate(50,130)">'+s+'</g>'+text(550,521,'Formal salt components · arbitrary 2D layout' if mid=='formamidine-acetate' else 'Free reference molecule · no solution or surface complex',18,'middle');formula=spec[mid]['formula'];kind='ionic_components' if mid=='formamidine-acetate' else 'molecule';lim=limits[mid]
 else:
  body='<rect x="55" y="160" width="990" height="345" rx="20" fill="#eef6f8" stroke="#c4d7df"/>'
  for i,l in enumerate(symbols[mid]):body+=text(550,245+i*80,l,28 if i==0 else 22,'middle')
  formula=mat['source_formula_or_abbreviation'] if mid not in ['hexane','fa-oleate'] else None;kind='symbolic_context';lim='Symbolic source identity only; no atomic coordinates, discrete complex, lattice or product binding is assigned.'
 svg=frame(mid,body,lim,formula or 'Discrete composition / isomer not established');sp='svg/'+eid+'.svg';(O/sp).write_text(svg,encoding='utf8');raster(svg,O/'previews'/(eid+'.png'))
 primary=[]
 if model and spec[mid]['cached']:
  old3=read(R/base[spec[mid]['cached']]['model3dPath'])
  if old3.get('pubchemCid'):primary=['https://pubchem.ncbi.nlm.nih.gov/compound/'+str(old3['pubchemCid'])]
  elif mid=='nitrogen':primary=['https://webbook.nist.gov/cgi/cbook.cgi?ID=C7727379&Mask=1000']
 caption=scope[mid]+' '+lim
 e={'id':eid,'name':mat['name'],'aliases':[mat['name']],'formula':formula,'displayFormula':formula or 'Unresolved composition / isomer','sourceFormula':mat['source_formula_or_abbreviation'],'depictionKind':kind,'svgPath':sp,'model2dPath':model['p2'] if model else None,'model3dPath':model['p3'] if model else None,'sourceUrls':['https://doi.org/10.1021/acs.jpcc.5c05144']+primary,'caption':caption,'limitations':[scope[mid],lim],'functionalGroups':model['m2']['functionalGroups'] if model else [],'provenance':{'sourceDoi':'10.1021/acs.jpcc.5c05144','sourceMaterialId':mid,'sourceLocators':mat['evidence'],'sourceFactsSha256':sha(S/'source-facts.json'),'measuredCoordinates':False,'referenceQualification':model['provenance'] if model else {'identityBasis':'Source identity only; unresolved material/speciation stays symbolic.'}},'binding_approved':False,'independentScientificAudit':'pending','published':False,'eligible_training':False}
 e['assetHashes']={k:sha(O/e[k]) for k in ['svgPath','model2dPath','model3dPath'] if e[k]};entries.append(e)
 if e['model3dPath']:
  m=read(O/e['model3dPath']);pts=[(a['x']+.24*a['z'],a['y']+.31*a['z']) for a in m['atoms']];lo=[min(x[i] for x in pts) for i in [0,1]];hi=[max(x[i] for x in pts) for i in [0,1]];sc=min(890/max(hi[0]-lo[0],1),320/max(hi[1]-lo[1],1));xy=[(550+(x-(lo[0]+hi[0])/2)*sc,320-(y-(lo[1]+hi[1])/2)*sc) for x,y in pts];bdy=''
  for b in m['bonds']:
   a,c=xy[b['a']],xy[b['b']];bdy+=f'<path d="M{a[0]} {a[1]}L{c[0]} {c[1]}" stroke="#69818e" stroke-width="{3 if b["order"]==1 else 5}"/>'
  for i,a in sorted(enumerate(m['atoms']),key=lambda x:x[1]['z']):
   x,y=xy[i];color={'C':'#4c6572','H':'#e8eef1','N':'#477ec2','O':'#d36d58'}[a['element']];bdy+=f'<circle cx="{x}" cy="{y}" r="{5 if a["element"]=="H" else 10}" fill="{color}" stroke="#718893"/>'
  bdy+=text(550,518,'Static projection of the exact retained reference geometry',18,'middle');sv=frame(mid,bdy,lim+' This preview is an arbitrary projection, not measured imagery.',formula);raster(sv,O/'conformer-previews'/(eid+'.png'))
save('registry-additions.json',{'schemaVersion':'1.0','source_id':'sasongko2025','status':'private_author_proposal','binding_approved':False,'entries':entries})
save('reference-qualification.json',{'source_id':'sasongko2025','references':quals,'symbolic_material_ids':list(symbols),'independent_approval':False,'new_3d_coordinates_generated':False})
save('input-bindings.json',{'source_freeze':{'path':str(S/'package-freeze.json'),'sha256':sha(S/'package-freeze.json')},'source_facts':{'path':str(S/'source-facts.json'),'sha256':sha(S/'source-facts.json')},'canonical_freeze':{'path':str(C/'package-freeze.json'),'sha256':sha(C/'package-freeze.json')},'canonical_audit':{'path':str(J/'canonical-independent-audit/independent-audit-v1.json'),'sha256':sha(J/'canonical-independent-audit/independent-audit-v1.json')},'source_audit':{'path':str(J/'source-independent-audit/independent-audit-v2.json'),'sha256':sha(J/'source-independent-audit/independent-audit-v2.json')},'snapshots':snapshots})
snap(M/'recipe-atlas/dist/chemical-viewer.mjs','chemical-viewer.mjs')
save('generation-checks.json',{'status':'passed_author_checks','independent_approval':False,'rdkit_version':rdBase.rdkitVersion,'check_count':len(checks),'checks':checks})
print(json.dumps({'entries':len(entries),'2d':len(models),'3d':sum(bool(x['model3dPath']) for x in entries),'symbolic':len(symbols),'checks':len(checks)}))
