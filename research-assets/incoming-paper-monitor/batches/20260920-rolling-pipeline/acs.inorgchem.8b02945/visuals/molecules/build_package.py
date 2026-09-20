"""Source-specific molecular references; private proposal, never writes Site.

Author checks qualify graphs, isotope positions and illustrative geometry.
An independent reviewer must separately approve the eventual bindings.
"""
from pathlib import Path
from copy import deepcopy
from collections import Counter
from datetime import datetime, timezone
import json, hashlib, html, textwrap, math, sys
O=Path(__file__).resolve().parent; F=O.parents[1]; M=F.parents[4]
sys.dont_write_bytecode=True
sys.path[:0]=[str(M/'research-assets/rdkit-runtime'),str(M/'research-assets/corpus-20260917/runtime')]
from rdkit import Chem, rdBase
from rdkit.Chem import AllChem, rdDepictor, rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
import pymupdf
from PIL import Image, ImageDraw

R=M/'recipe-atlas/dist/assets/chemical-registry'
assert not (O/'package-freeze.json').exists(), 'Preserve immutable package.'
for d in ['models','svg','previews','stock-svg','stock-previews','contacts','reference-snapshots/models']:(O/d).mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 p=O/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n','utf8')
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
ck('Immutable author source freeze',sha(F/'package-freeze.json')=='7599e47c1ef1d43d56b2f4f835e4b550a1ef652aecca2e9dd8e593abc5769c04')
V=F/'source-extraction-revision-2'
ck('Immutable source correction freeze',sha(V/'package-freeze.json')=='9f76d5810d3bd2caef97dca7c96fc6ae8ad0a8362bdab8f9ac2d4811867de816')
source=read(V/'source-facts.json');original_source=read(F/'source-facts.json')
ck('Source revision preserves all chemical identities and stocks',source['materials']==original_source['materials'] and source['stocks']==original_source['stocks'])
materials={m['id']:m for m in source['materials']}
base={x['id']:x for x in read(R/'registry.json')['entries']}
primary={p['CID']:p for p in read(O/'reference-snapshots/primary/pubchem-identities.json')['PropertyTable']['Properties']}

# SMILES are reference graphs, never an assertion of solution speciation.
# Parent isotopologues supply connectivity only where the source specifies labeling.
spec={
 'indium-acetate':('[In+3].CC(=O)[O-].CC(=O)[O-].CC(=O)[O-]',None,None),
 'myristic-acid':('CCCCCCCCCCCCCC(=O)O','myristic-acid',None),
 'phenylacetic-acid':(primary[999]['SMILES'],None,999),
 'bnmgcl':(primary[2733352]['SMILES'],None,2733352),
 'methyltetrahydrofuran':(primary[7301]['SMILES'],None,7301),
 'labeled-co2':('O=[13C]=O',None,None),
 'labeled-acid':(primary[12198003]['SMILES'],None,12198003),
 'phosphine':(primary[272683]['SMILES'],None,272683),
 'indium-myristate':('[In+3].' + '.'.join(['CCCCCCCCCCCCCC(=O)[O-]']*3),None,None),
 'indium-labeled-phenylacetate':('[In+3].'+'.'.join(['c1ccccc1C[13C](=O)[O-]']*3),None,None),
 'ode':('C=CCCCCCCCCCCCCCCCC','1-octadecene',None),
 'toluene':('Cc1ccccc1','toluene',None),
 'pentane':(primary[8003]['SMILES'],None,8003),
 'ethyl-acetate':('CCOC(C)=O','ethyl-acetate',None),
 'acetonitrile':('CC#N','acetonitrile',None),
 'benzene-d6':('[2H]c1c([2H])c([2H])c([2H])c([2H])c1[2H]',None,241),
 'toluene-d8':('[2H]C([2H])([2H])c1c([2H])c([2H])c([2H])c([2H])c1[2H]','evans2010-toluene-d8-reference',None),
 'chloroform-d':('[2H]C(Cl)(Cl)Cl','chloroform-d',None),
 'calcium-hydride':('[Ca+2].[H-].[H-]',None,None),
 'nitrogen':('N#N','nitrogen',None),
 'thf':('C1CCOC1','thf',None),
 'liquid-nitrogen':('N#N','nitrogen',None),
 'dry-ice':('O=C=O','carbon-dioxide',None),
 'acetone':('CC(C)=O','acetone',None),
 'water':('O','water',None),
 'methanol':('CO','methanol',None),
 'hcl':('[H+].[Cl-]',None,None),
 'diethyl-ether':('CCOCC','diethyl-ether',None),
 'sodium-sulfate':('[Na+].[Na+].[O-]S(=O)(=O)[O-]',None,None),
 'dichloromethane':(primary[6344]['SMILES'],None,6344),
}
symbol_ids=set(materials)-set(spec)
ck('Exactly 39 source identities',len(materials)==39 and len(spec)==30 and len(symbol_ids)==9)
extra={
 'indium-acetate':'Formal In3+ and three acetate formula components. Coordination, aggregation and preparation are not supplied.',
 'indium-myristate':'Formal In3+ and three myristate formula components. This is not a solved dissolved complex; stock concentration is unreported.',
 'indium-labeled-phenylacetate':'Formal In3+ and three carbonyl-labeled phenylacetate formula components. No In–O bonds or coordination geometry are assigned.',
 'myristic-acid':'Free carboxylic acid, distinct from indium myristate and bound myristate ligands.',
 'bnmgcl':'Disconnected standardized Grignard formula components: benzyl anion, Mg2+ and chloride. No Mg–C bond, solvent coordination, aggregation or 3D arrangement is inferred.',
 'methyltetrahydrofuran':'The methyl group is adjacent to ring oxygen. Stereochemistry is unspecified; the depiction assigns neither an enantiomer nor a racemic assay.',
 'labeled-co2':'The carbon is 13C. Source gas enrichment is 99%; drawing one isotopologue is not a product isotope-assay claim. This reagent is separate from bath dry ice.',
 'labeled-acid':'The 13C label is at the carboxyl carbon, not the benzyl carbon or ring. The drawing does not establish product isotope enrichment.',
 'phosphine':'P(SiMe3)3: three P–Si bonds, each silicon with three methyl groups. Upstream preparation is cited only in the supplied paper.',
 'pentane':'Straight-chain pentane reference for the source name. The paper supplies no separate isomer-purity assay.',
 'benzene-d6':'Six deuterium atoms replace the six ring hydrogens. Reference isotopologue; enrichment is not specified.',
 'toluene-d8':'Eight deuterium atoms, three at the methyl group and five on the ring. Reference isotopologue; enrichment is not specified.',
 'chloroform-d':'One deuterium atom on carbon. Reference isotopologue; enrichment is not specified.',
 'calcium-hydride':'Formal Ca2+ and two hydride formula components; no solid lattice or solvent species is modeled.',
 'nitrogen':'One N2 molecule explains gas identity; flow, pressure and isotopic assay are not inferred.',
 'liquid-nitrogen':'One N2 molecule explains coolant identity, not liquid structure. This cooling bath is separate from the inert reaction atmosphere.',
 'dry-ice':'One CO2 molecule explains coolant identity, not a solid lattice. Bath dry ice is distinct from reactive 13CO2.',
 'hcl':'Formal H+ and Cl− components identify the aqueous acid. H+ is bookkeeping, not a claim of bare solvated protons or complete hydration structure.',
 'sodium-sulfate':'Two Na+ ions and a sulfate group represent formula components only. The paper does not specify hydration state.',
 'msc-myristate':'Cluster identity reported as In37P20(myristate)51; no atom positions, ligand arrangement or unique surface geometry are supplied.',
 'msc-phenylacetate':'In37P20(O2CCH2Ph)51 refers to a prior reported cluster structure. This source does not supply its coordinate file.',
 'msc-labeled':'Carbonyl-labeled phenylacetate cluster. The cited upstream synthesis and unknown atomic coordinates remain separate gaps.',
 'molecular-sieves':'The paper names 4 Å molecular sieves; exact composition, framework and atomic coordinates are unspecified.',
 'brine':'Source-named aqueous wash. Salt identity, concentration and volume are not sufficiently specified to assign a molecular formula or speciation.',
 'biobeads':'Named chromatography medium. This symbolic reference does not assign a polymer structure, column dimensions or eluent.',
 'tem-support':'Source-named carbon support, not the measured InP specimen. No grid metal or atomic carbon structure is assigned.',
 'inp':'InP identifies a source-assigned phase. It does not establish whole-specimen purity, an exact nanoparticle structure or a structure–recipe pair.',
 'indium-oxide':'In2O3 is a reported byproduct phase. No whole-product purity, exact atomic coordinates or isolated synthesis recipe is inferred.',
}
def graph(m):
 rw=Chem.RWMol()
 for a in m['atoms']:
  at=Chem.Atom(a['element']);at.SetFormalCharge(a.get('formalCharge',0));at.SetIsotope(a.get('isotope',0))
  if 'implicitHydrogenCount' in a:at.SetNoImplicit(True);at.SetNumExplicitHs(a['implicitHydrogenCount'])
  rw.AddAtom(at)
 for b in m['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
 mol=rw.GetMol();Chem.SanitizeMol(mol);return mol
def canon(m):return Chem.MolToSmiles(Chem.RemoveHs(m))
def groups(m):
 out=[]
 patterns=[('Carboxylic acid','[CX3](=[OX1])[OX2H]'),('Carboxylate','[CX3](=[OX1])[O-]'),('Ester','[CX3](=[OX1])[OX2][CX4]'),('Alcohol','[CX4][OX2H]'),('Ether','[CX4][OX2][CX4]'),('Ketone','[CX4][CX3](=[OX1])[CX4]'),('Terminal alkene','[CH2]=[CH]'),('Nitrile','[CX2]#[NX1]'),('Sulfate','[O-]S(=O)(=O)[O-]'),('Trimethylsilyl','[Si]([CH3])([CH3])[CH3]')]
 for label,p in patterns:
  for match in m.GetSubstructMatches(Chem.MolFromSmarts(p)):
   ids=sorted(match);out.append({'label':label,'atomIndices':ids,'bondIndices':[b.GetIdx() for b in m.GetBonds() if b.GetBeginAtomIdx() in ids and b.GetEndAtomIdx() in ids]})
 for a in m.GetAtoms():
  if a.GetIsotope():out.append({'label':str(a.GetIsotope())+a.GetSymbol()+' isotope label','atomIndices':[a.GetIdx()],'bondIndices':[]})
 return out
def model(m,mid,dim,provenance):
 cf=m.GetConformer()
 atoms=[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':cf.GetAtomPosition(a.GetIdx()).x,'y':cf.GetAtomPosition(a.GetIdx()).y,'z':cf.GetAtomPosition(a.GetIdx()).z,'formalCharge':a.GetFormalCharge(),'isotope':a.GetIsotope(),'implicitHydrogenCount':a.GetTotalNumHs()} for a in m.GetAtoms()]
 bonds=[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble()} for b in m.GetBonds()]
 return {'id':'friedfeld2019-'+mid+'-reference','name':materials[mid]['name'],'formula':rdMolDescriptors.CalcMolFormula(m,separateIsotopes=True),'sourceFormula':materials[mid]['source_formula_or_abbreviation'],'representation':dim,'has3D':dim=='3d','allowRotation':dim=='3d','coordinateUnits':'angstrom' if dim=='3d' else 'arbitrary drawing units','indexConvention':'zero-based','atoms':atoms,'bonds':bonds,'functionalGroups':groups(m),'caption':extra.get(mid,'Free molecular reference; no unique solution-state conformation is implied.'),'modelType':'Illustrative computed conformer' if dim=='3d' else 'Reference connectivity / formula components','source':provenance,'eligible_training':False}
def geometry_check(m,mid):
 cf=m.GetConformer();pt=[cf.GetAtomPosition(i) for i in range(m.GetNumAtoms())]
 ck(mid+' finite coordinates',all(math.isfinite(v) for p in pt for v in (p.x,p.y,p.z)))
 bonds={tuple(sorted([b.GetBeginAtomIdx(),b.GetEndAtomIdx()])) for b in m.GetBonds()}
 for a,b in bonds:ck(mid+f' bond length {a}/{b}',.6<pt[a].Distance(pt[b])<2.6)
 for a in range(len(pt)):
  for b in range(a):
   if (b,a) not in bonds:ck(mid+f' no overlap {a}/{b}',pt[a].Distance(pt[b])>.65)
def esc(s):return html.escape(str(s),quote=True)
def prose(s):
 for old,new in [('Purchased1M','Purchased 1 M'),('in2-Me-THF','in 2-Me-THF'),('99%13C','99% 13C'),('Three20mL','Three 20 mL'),('BathCO2','Bath CO2'),('1-ODE','1-ODE'),('explicitly1-ODE','explicitly 1-ODE'),('underN2','under N2'),('aqueousHCl','aqueous HCl'),('Aqueous1M','Aqueous 1 M'),('Aqueous1M','Aqueous 1 M'),('50mL','50 mL'),('cites43/45','cites 43/45'),('inODE','in ODE'),('reachpH2','reach pH 2'),('inject;20mL','inject; 20 mL')]:s=s.replace(old,new)
 return s
def tx(x,y,s,size=19,anchor='start'):return f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" text-anchor="{anchor}" fill="#294658">{esc(s)}</text>'
def wrap(s,x,y,width=101,size=18):return ''.join(tx(x,y+i*26,t,size) for i,t in enumerate(textwrap.wrap(s,width)))
def raster(svg,p):
 d=pymupdf.open(stream=svg.encode(),filetype='svg');d[0].get_pixmap(alpha=False).save(p);d.close()
def drawing(m,w=1000,h=300):
 d=rdMolDraw2D.MolDraw2DSVG(w,h);d.drawOptions().padding=.12;d.drawOptions().includeRadicals=False
 for a in m.GetAtoms():
  if a.GetSymbol()=='C' and a.GetFormalCharge()==-1 and a.GetTotalNumHs()==2:d.drawOptions().atomLabels[a.GetIdx()]='CH<sub>2</sub><sup>-</sup>'
 colors={i:(.55,.80,.79) for g in groups(m) for i in g['atomIndices']}
 rdMolDraw2D.PrepareAndDrawMolecule(d,m,highlightAtoms=list(colors),highlightAtomColors=colors);d.FinishDrawing();s=d.GetDrawingText();return s[s.index('>',s.index('<svg'))+1:s.rindex('</svg>')]
models={};qualifications=[];entries=[]
for mid,(smiles,cached,cid) in spec.items():
 mol=Chem.MolFromSmiles(smiles);ck(mid+' valid graph',mol is not None)
 prov={'identity_basis':'Source name or formula with qualified reference connectivity','reference_smiles':smiles,'pubchem_cid':cid,'source_doi':'10.1021/acs.inorgchem.8b02945','rdkit_version':rdBase.rdkitVersion,'measured_coordinates':False}
 if cid:prov['primary_reference']='https://pubchem.ncbi.nlm.nih.gov/compound/'+str(cid)
 if cached:
  e=base[cached];old2=read(R/e['model2dPath']);ck(mid+' cached connectivity',canon(graph(old2))==canon(mol))
  save('reference-snapshots/entry-'+cached+'.json',e)
  for k in ['model2dPath','model3dPath']:
   if not e.get(k):continue
   p=R/e[k];q=O/'reference-snapshots'/e[k];q.parent.mkdir(parents=True,exist_ok=True)
   if q.exists():ck(mid+' frozen cache '+k,sha(q)==sha(p))
   else:q.write_bytes(p.read_bytes())
  prov.update(retained_registry_id=cached,retained_2d_sha256=sha(R/e['model2dPath']),primary_references=e.get('sourceUrls',[]))
 if cid and mid!='benzene-d6':ck(mid+' primary formula',rdMolDescriptors.CalcMolFormula(mol)==primary[cid]['MolecularFormula'])
 ck(mid+' neutral total formula',sum(a.GetFormalCharge() for a in mol.GetAtoms())==0)
 if mid in ['labeled-acid','indium-labeled-phenylacetate']:
  labels=[a for a in mol.GetAtoms() if a.GetIsotope()==13]
  ck(mid+' carboxyl carbon isotope position',len(labels)==(3 if mid.startswith('indium') else 1) and all(a.GetSymbol()=='C' and sorted(n.GetSymbol() for n in a.GetNeighbors())==['C','O','O'] for a in labels))
 if mid in ['benzene-d6','toluene-d8','chloroform-d']:ck(mid+' D atom count',sum(a.GetIsotope()==2 for a in mol.GetAtoms())=={'benzene-d6':6,'toluene-d8':8,'chloroform-d':1}[mid])
 rdDepictor.Compute2DCoords(mol);m2=model(mol,mid,'2d',prov);p2='models/friedfeld2019-'+mid+'-2d.json';save(p2,m2);p3=None
 single=len(Chem.GetMolFrags(mol))==1
 if cached and base[cached].get('model3dPath'):
  old=read(R/base[cached]['model3dPath']);g=graph(old);ck(mid+' cached 3D connectivity',canon(g)==canon(mol))
  m3=deepcopy(old);m3.update(id=m2['id'],name=m2['name'],formula=m2['formula'],sourceFormula=m2['sourceFormula'],caption=m2['caption']+' '+old.get('caption',''),functionalGroups=groups(g),eligible_training=False)
  m3['referenceQualification']=dict(prov,retained_3d_sha256=sha(R/base[cached]['model3dPath']))
  ck(mid+' original coordinates retained',m3['atoms']==old['atoms'] and m3['bonds']==old['bonds'])
  cf=Chem.Conformer(g.GetNumAtoms())
  for i,a in enumerate(old['atoms']):cf.SetAtomPosition(i,(a['x'],a['y'],a['z']))
  g.AddConformer(cf);geometry_check(g,mid)
  p3='models/friedfeld2019-'+mid+'-3d.json';save(p3,m3)
 elif single and mid not in ['methyltetrahydrofuran','labeled-co2']:
  # Unspecified 2-MeTHF stereochemistry stays 2D; no chosen stereoisomer.
  g=Chem.AddHs(mol);g.RemoveAllConformers();opts=AllChem.ETKDGv3();opts.randomSeed=2019803
  embedded=AllChem.EmbedMolecule(g,opts);ck(mid+' ETKDG embedding',embedded==0)
  method='MMFF94' if AllChem.MMFFHasAllMoleculeParams(g) else 'UFF'
  supported=AllChem.MMFFHasAllMoleculeParams(g) if method=='MMFF94' else AllChem.UFFHasAllMoleculeParams(g)
  ck(mid+' force-field parameters available',supported)
  result=AllChem.MMFFOptimizeMolecule(g,maxIters=2000) if method=='MMFF94' else AllChem.UFFOptimizeMolecule(g,maxIters=2000)
  geometry_check(g,mid);ck(mid+' geometry connectivity',canon(g)==canon(mol))
  pv=dict(prov,embedding='ETKDGv3',seed=2019803,minimization=method,minimization_result=result,converged=result==0,unsupported_parameters=False)
  m3=model(g,mid,'3d',pv);m3['caption']='Illustrative computed conformer; not measured or uniquely representative of solution. '+m3['caption'];p3='models/friedfeld2019-'+mid+'-3d.json';save(p3,m3)
 models[mid]={'mol':mol,'model2dPath':p2,'model3dPath':p3,'formula':m2['formula'],'provenance':prov}
 qualifications.append({'source_material_id':mid,'reference_formula':m2['formula'],'literal_source_formula':m2['sourceFormula'],'fragment_count':len(Chem.GetMolFrags(mol)),'model2dPath':p2,'model3dPath':p3,'isotopes':dict(Counter(str(a.GetIsotope())+a.GetSymbol() for a in mol.GetAtoms() if a.GetIsotope())),'provenance':prov})

for mid,m in materials.items():
 g=models.get(mid);lim=extra.get(mid,'Free molecular reference; no unique solution-state conformation is implied.')
 caption=prose(m['scope_note'])+' '+lim;body='';formula=g['formula'] if g else None
 display={'calcium-hydride':'CaH2','sodium-sulfate':'Na2SO4','indium-acetate':'In(CH3CO2)3','indium-myristate':'In(C14H27O2)3','indium-labeled-phenylacetate':'In(O2−13CCH2Ph)3','labeled-acid':'PhCH2−13CO2H','labeled-co2':'13CO2','msc-myristate':'In37P20(myristate)51'}.get(mid,formula or m['source_formula_or_abbreviation'])
 if g:
  if mid in ['indium-acetate','indium-myristate','indium-labeled-phenylacetate']:
   ligand=next(f for f in Chem.GetMolFrags(g['mol'],asMols=True) if f.GetNumAtoms()>1);rdDepictor.Compute2DCoords(ligand)
   body=tx(190,290,'In3+',36,'middle')+tx(360,290,'+',30,'middle')+tx(480,290,'3 ×',30,'middle')+'<g transform="translate(530,170)">'+drawing(ligand,490,220)+'</g>'
  else:body='<g transform="translate(50,130)">'+drawing(g['mol'])+'</g>'
  body+=tx(550,465,'Reference connectivity · colored functional groups / isotope labels',17,'middle')
 else:
  body='<rect x="100" y="160" width="900" height="215" rx="18" fill="#edf5f8" stroke="#bdd2dd"/>'+wrap(lim,150,205,75,22)+tx(550,420,'Symbolic identity · atomic coordinates not assigned',18,'middle')
 body+=wrap(caption,45,515,104,18)
 height=max(740,570+len(textwrap.wrap(caption,104))*26)
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{height}" viewBox="0 0 1100 {height}"><title>{esc(m["name"])}</title><desc>{esc(caption)}</desc><rect width="1100" height="{height}" rx="18" fill="white"/>{tx(40,49,m["name"],26)}{tx(550,101,display,22,"middle")}{body}</svg>'
 eid='friedfeld2019-'+mid+'-reference';path='svg/'+eid+'.svg';(O/path).write_text(svg,'utf8');raster(svg,str(O/'previews'/(eid+'.png')))
 kind=('ionic_components' if len(Chem.GetMolFrags(g['mol']))>1 else 'molecule') if g else 'symbolic_identity'
 entry={'id':eid,'name':m['name'],'aliases':[m['name']],'formula':formula,'displayFormula':display,'sourceFormula':m['source_formula_or_abbreviation'],'depictionKind':kind,'svgPath':path,'model2dPath':g['model2dPath'] if g else None,'model3dPath':g['model3dPath'] if g else None,'functionalGroups':groups(g['mol']) if g else [],'caption':caption,'limitations':[m['scope_note'],lim],'sourceUrls':['https://doi.org/10.1021/acs.inorgchem.8b02945']+([g['provenance']['primary_reference']] if g and g['provenance'].get('primary_reference') else []),'provenance':{'sourceDoi':'10.1021/acs.inorgchem.8b02945','sourceMaterialId':mid,'sourceLocators':m['evidence'],'sourceFactsSha256':sha(V/'source-facts.json'),'measuredCoordinates':False},'binding_approved':False,'independentScientificAudit':'pending','published':False,'eligible_training':False}
 entry['assetHashes']={k:sha(O/entry[k]) for k in ['svgPath','model2dPath','model3dPath'] if entry[k]};entries.append(entry)
save('registry-additions.json',{'schemaVersion':'1.0','source_id':'friedfeld2019','status':'private_author_proposal','binding_approved':False,'entries':entries})
stocks=[]
for s in source['stocks']:
 body='';maxlines=0
 for idx,c in enumerate(s['components']):
  mid=c['material_id'];x=35+idx*535
  body+=tx(x+250,119,c['role'].upper(),16,'middle')
  body+=wrap(materials[mid]['name'],x+15,155,37,21)
  if mid in models:body+='<g transform="translate('+str(x)+',215)">'+drawing(models[mid]['mol'],500,210)+'</g>'
  else:body+=wrap(materials[mid]['source_formula_or_abbreviation'],x+35,260,31,22)+tx(x+250,340,'Symbolic precursor identity',17,'middle')
 y=478
 for q in s['quantities']+s.get('subsequent_transfer_volume',[]):
  line=q['meaning']+': '+q['raw_text']+' '+q['unit']+' (reported).';body+=wrap(line,45,y,96,19);y+=26*len(textwrap.wrap(line,96))+10
 if not s['quantities']:body+=tx(45,y,'Stock concentration and preparation amount: not reported.',19);y+=42
 line=prose(s['preparation']);body+=wrap(line,45,y,100,19);y+=26*len(textwrap.wrap(line,100))+32
 line='Component references are not a measured solution complex. '+s['scope_note'];body+=wrap(line,45,y,102,18);y+=26*len(textwrap.wrap(line,102))+40
 height=max(y,780)
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{height}"><rect width="1100" height="{height}" fill="white"/>{tx(35,48,prose(s["name"]),25)}{body}</svg>'
 p='stock-svg/friedfeld2019-'+s['id']+'.svg';(O/p).write_text(svg,'utf8');raster(svg,str(O/'stock-previews'/('friedfeld2019-'+s['id']+'.png')))
 stocks.append({'stock_id':s['id'],'source_stock':s,'svg_path':p,'sha256':sha(O/p),'component_registry_ids':['friedfeld2019-'+c['material_id']+'-reference' for c in s['components']],'binding_approved':False})
save('source-stock-reference-proposal.json',{'stocks':stocks,'binding_approved':False})
panels=sorted((O/'previews').glob('*.png'))+sorted((O/'stock-previews').glob('*.png'))
for start in range(0,len(panels),6):
 items=panels[start:start+6];canvas=Image.new('RGB',(1500,((len(items)+1)//2)*550),'#e8eef1');draw=ImageDraw.Draw(canvas)
 for j,p in enumerate(items):
  im=Image.open(p);im.thumbnail((730,510));x=(j%2)*750+(750-im.width)//2;y=(j//2)*550+30;canvas.paste(im,(x,y));draw.text(((j%2)*750+10,(j//2)*550+8),p.stem,fill='#294658')
 canvas.save(O/'contacts'/f'contact-{start//6+1:02}.png')
save('reference-qualification.json',{'author':'/root','source_id':'friedfeld2019','created_at':datetime.now(timezone.utc).isoformat(),'models':qualifications,'source_base_freeze_sha256':sha(F/'package-freeze.json'),'source_revision_freeze_sha256':sha(V/'package-freeze.json'),'source_facts_sha256':sha(V/'source-facts.json'),'scope':'Chemical reference identity and illustrative geometry only; canonical/stock bindings and independent approval pending.','source_coordinates_reconstructed':False,'eligible_training':False})
save('generation-checks.json',{'author':'/root','status':'passed_author_checks','check_count':len(checks),'checks':checks,'counts':{'identities':len(entries),'models2d':len(models),'models3d':sum(bool(g['model3dPath']) for g in models.values()),'symbols':len(symbol_ids),'stocks':len(stocks)},'independent_approval':False})
print(json.dumps({'identities':len(entries),'models2d':len(models),'models3d':sum(bool(g['model3dPath']) for g in models.values()),'stocks':len(stocks),'author_checks':len(checks),'independent_approval':False}))
