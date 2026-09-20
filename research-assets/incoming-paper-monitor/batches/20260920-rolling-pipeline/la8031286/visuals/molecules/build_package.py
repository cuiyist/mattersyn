"""Pati source-qualified private chemical references. No Site writes or network."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,sys,html,textwrap,math,datetime
O=Path(__file__).resolve().parent;P=O.parents[1];M=P.parents[4];R=M/'recipe-atlas/dist/assets/chemical-registry';C=P/'canonical-proposal/v1'
assert not (O/'package-freeze.json').exists(),'Frozen package must be preserved.'
sys.dont_write_bytecode=True
sys.path[:0]=[str(M/'research-assets/rdkit-runtime'),str(M/'research-assets/corpus-20260917/runtime')]
from rdkit import Chem,rdBase
from rdkit.Chem import rdDepictor,rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
import pymupdf
from PIL import Image,ImageDraw
for n in ['models','svg','previews','stock-svg','stock-previews','conformer-previews','contacts','reference-snapshots/models','reference-snapshots/svg','reference-snapshots/raw','reference-snapshots/entries']:(O/n).mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(p,v):
 p=O/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def esc(s):return html.escape(str(s),quote=True)
def tx(x,y,s,size=18,anchor='start'):return f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" text-anchor="{anchor}" fill="#294658">{esc(s)}</text>'
def wrap(s,x,y,width=105,size=17,line=24):return ''.join(tx(x,y+i*line,t,size) for i,t in enumerate(textwrap.wrap(s,width)))
def raster(svg,p):
 d=pymupdf.open(stream=svg.encode(),filetype='svg');d[0].get_pixmap(alpha=False).save(str(p));d.close()
checks=[];snapshots=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
def snap(p,rel):
 p=Path(p);dst=O/'reference-snapshots'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():ck('Immutable snapshot '+rel,sha(dst)==sha(p))
 else:dst.write_bytes(p.read_bytes())
 snapshots.append({'original_path':str(p),'snapshot':str(dst.relative_to(O)),'sha256':sha(dst)})
 return dst
source=read(P/'source-facts.json');materials={m['id']:m for m in source['materials']};ck('All 20 source material identities',len(materials)==20)
ck('Canonical frozen boundary',sha(C/'package-manifest.json')=='5986df83c2313f8e5418d0c46c049d86e2ef62dbd049359c7a53a5010e312281')
basepath=O/'reference-snapshots/registry-base.json'
if not basepath.exists():snap(R/'registry.json','registry-base.json')
base={e['id']:e for e in read(basepath)['entries']}
spec={
 'cerium-nitrate':('[Ce+3].O=[N+]([O-])[O-].O=[N+]([O-])[O-].O=[N+]([O-])[O-].O.O.O.O.O.O','H12CeN3O15',None),
 'tea':('N(CCO)(CCO)CCO','C6H15NO3',None),
 'ethanol':('CCO','C2H6O','ethanol'),
 'propanol':('CCCO','C3H8O','1-propanol'),
 'butanol':('CCCCO','C4H10O','1-butanol'),
 'acetone':('CC(=O)C','C3H6O','acetone'),
 'nitrogen-bet':('N#N','N2','ghosh2012-liquid-nitrogen-reference'),
 'hydrate-water':('O','H2O','water')}
limits={
 'cerium-nitrate':'Formal formula components: one Ce3+, three nitrate anions and six water molecules. Layout is arbitrary; no Ce–O coordination, hydrate lattice or dissolved species is assigned. The six waters are not a separately charged solvent.',
 'tea':'Named triethanolamine reference: N(CH2CH2OH)3, C6H15NO3. The paper prints (C2H5OH)3N; that unresolved formula conflict remains in the source and canonical data. This free neutral graph does not reconstruct a cerium complex or protonation equilibrium.',
 'ethanol':'Free ethanol reference. Only ethanol is explicitly called anhydrous; the source gives 99.9% without a percentage basis. Stock solute and solvent references do not establish solution speciation.',
 'propanol':'Free 1-propanol reference, with the hydroxyl on the terminal carbon. The source reports 99.9%; an anhydrous grade is not separately stated. This is not isopropanol.',
 'butanol':'Free 1-butanol reference, with a straight four-carbon chain and terminal hydroxyl. The source reports 99.9%; no separately stated anhydrous grade is inferred.',
 'acetone':'Free acetone reference for the wash after ambient drying. Supplier, grade and quantity are unreported. It is not the precipitation solvent.',
 'nitrogen-bet':'Dinitrogen reference for nitrogen sorption interpretation only. The cached NIST 14N2 distance is 1.09768 angstrom; source gas isotopic composition, purity and pressure program are unknown. No synthesis atmosphere is inferred.',
 'hydrate-water':'One free-water reference for precursor-associated molecular water. Six waters belong to the nitrate hydrate formula; no separate water charge, water activity or hydration-shell geometry is reported.'}
scope={
 'cerium-nitrate':'Cerium nitrate hexahydrate, 99%; Aldrich Chemicals USA.',
 'tea':'Triethanolamine, 98%; Aldrich Chemicals USA. Named identity and printed formula remain distinct.',
 'ethanol':'Anhydrous ethanol, 99.9%; Fisher Chemicals. Separate nitrate and TEA stocks; matching alcohol wash.',
 'propanol':'1-Propanol, 99.9%; Fisher Chemicals. Separate nitrate and TEA stocks; matching alcohol wash.',
 'butanol':'1-Butanol, 99.9%; Fisher Chemicals. Separate nitrate and TEA stocks; matching alcohol wash.',
 'acetone':'Wash after ambient drying; supplier, grade and amount unreported.',
 'ammonium-hydroxide':'Filtrate-completeness test only. Added amount and solution concentration are unreported.',
 'filter-paper':'Whatman 42 suction filter; reported pore diameter 2.5 micrometres. It is not retained product.',
 'burette':'Reported feed vessel for the nitrate stock. Capacity and construction material are not stated.',
 'erlenmeyer':'Reported receiving flask for TEA solution. Capacity and construction material are not stated.',
 'pipet':'Preweighed 1 mL pipet for the rough powder-packing density estimate only.',
 'air':'Reported TGA environment. This does not specify the atmosphere of calcination.',
 'nitrogen-bet':'Nitrogen sorption context; gas grade and pressure program are not reported.',
 'hydrate-water':'Precursor-associated water in the author mechanism; no separately added water.',
 'ceria':'CeO2 phase assigned locally by microscopy and to calcined XRD. Whole as-prepared composition is unresolved.',
 'ce-tea-complex':'Proposed [Ce(TEA)2(NO3)](NO3)2 analogue based on cited La complex; no solved structure supplied.',
 'cerium-hydroxide':'Ce(OH)4 is a proposed as-prepared mixture component, not an independently isolated precursor.',
 'hydrated-ceria':'CeO2·nH2O is a proposed component with unknown hydration number n.',
 'hydroxo-complex':'Variable [Ce(H2O)x(OH)y](4-y)+ appears in the mechanism. Coordination and x/y remain unresolved.',
 'protonated-tea':'The printed reaction contains (C2H5OH)3NH+. Its formula conflict remains unresolved; no isolated product is established.'}
symbols={
 'ammonium-hydroxide':['Ammonium hydroxide solution','Diagnostic reagent for the retained filtrate','Composition and equilibrium speciation unresolved'],
 'filter-paper':['Whatman 42 filter paper','2.5 micrometre pore diameter','Support identity; no polymer-chain or pore model'],
 'burette':['Burette','Nitrate stock feed','Capacity and glass composition unknown'],
 'erlenmeyer':['Erlenmeyer flask','TEA stock receiver','Capacity and glass composition unknown'],
 'pipet':['Preweighed pipet · 1 mL','Powder packing-density context','No vessel construction or volume calibration model'],
 'air':['Air · gas mixture','TGA environment only','Composition, flow and humidity not specified'],
 'ceria':['CeO2 · source-assigned phase','Local microscopy / calcined diffraction evidence','No recovered atomic structure or whole-powder purity claim'],
 'ce-tea-complex':['Proposed Ce–TEA nitrate complex','[Ce(TEA)2(NO3)](NO3)2','No coordination graph, stoichiometric assay or coordinates'],
 'cerium-hydroxide':['Proposed Ce(OH)4 component','Author interpretation of the as-prepared powder','No isolated compound or atomic structure'],
 'hydrated-ceria':['Proposed CeO2·nH2O component','Hydration number n unknown','No invented hydrate or water arrangement'],
 'hydroxo-complex':['Proposed [Ce(H2O)x(OH)y](4-y)+','Variable x/y; unresolved coordination','Mechanistic context, not a solved molecular species'],
 'protonated-tea':['Printed protonated-precipitant formula','(C2H5OH)3NH+ · retained literally','No graph assigned from the conflicting formula']}
ck('Complete distinct identity plan',set(spec)|set(symbols)==set(materials) and not(set(spec)&set(symbols)))
def modelmol(m):
 rw=Chem.RWMol()
 for a in m['atoms']:
  at=Chem.Atom(a['element']);at.SetFormalCharge(a.get('formalCharge',0));at.SetIsotope(a.get('isotope',0))
  if 'implicitHydrogenCount' in a:at.SetNoImplicit(True);at.SetNumExplicitHs(a['implicitHydrogenCount'])
  rw.AddAtom(at)
 for b in m['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
 mol=rw.GetMol();Chem.SanitizeMol(mol);return mol
def canonical(m):return Chem.MolToSmiles(Chem.RemoveHs(m))
def groups(m):
 out=[]
 for name,patt in [('Alcohol group','[CX4][OX2H]'),('Tertiary amine nitrogen','[NX3;H0]'),('Ketone carbonyl','[CX3](=[OX1])'),('Nitrate resonance group','[N+](=O)([O-])[O-]'),('Cerium(III) formula ion','[Ce+3]'),('Dinitrogen triple bond','N#N')]:
  for match in m.GetSubstructMatches(Chem.MolFromSmarts(patt)):
   ids=sorted(match);out.append({'label':name,'atomIndices':ids,'bondIndices':[b.GetIdx() for b in m.GetBonds() if b.GetBeginAtomIdx() in ids and b.GetEndAtomIdx() in ids]})
 for atom in m.GetAtoms():
  if atom.GetSymbol()=='O' and atom.GetTotalNumHs(includeNeighbors=True)==2:
   ids=[atom.GetIdx()]+[a.GetIdx() for a in atom.GetNeighbors() if a.GetSymbol()=='H'];out.append({'label':'Water formula component','atomIndices':sorted(ids),'bondIndices':[b.GetIdx() for b in m.GetBonds() if b.GetBeginAtomIdx() in ids and b.GetEndAtomIdx() in ids]})
 return out
models={};qual=[]
for mid,(smiles,formula,cached) in spec.items():
 mol=Chem.MolFromSmiles(smiles);ck(mid+' formula',rdMolDescriptors.CalcMolFormula(mol)==formula)
 prov={'identityBasis':'Source-named reference connectivity / literal hydrate formula components; no source coordinates.','referenceSmiles':smiles,'primaryReference':None,'retainedRegistryId':cached}
 if cached:
  e=base[cached];save('reference-snapshots/entries/'+cached+'.json',e)
  for field in ['svgPath','model2dPath','model3dPath']:
   if e.get(field):ck(cached+' exact cached '+field,sha(R/e[field])==e['assetHashes'][field]);snap(R/e[field],e[field])
  ck(mid+' cached 2D graph',canonical(modelmol(read(R/e['model2dPath'])))==canonical(mol))
  urls=([f'https://pubchem.ncbi.nlm.nih.gov/compound/{e["pubchemCid"]}'] if e.get('pubchemCid') else ['https://webbook.nist.gov/cgi/cbook.cgi?ID=C7727379&Mask=1000'])
  prov.update(primaryReference=urls[0],retainedEntrySha256=jsha(e),retainedModel2dSha256=sha(R/e['model2dPath']))
  for suffix in ['-pubchem-2d.sdf','-properties.json']:
   f=M/'research-assets/quality-20260918/molecules/raw'/(cached+suffix)
   if f.exists():snap(f,'raw/'+f.name)
  if mid=='butanol':snap(M/'research-assets/1-butanol-pubchem-263-3d.sdf','raw/1-butanol-pubchem-263-3d.sdf')
  if mid=='acetone':
   q=M/'research-assets/incoming-paper-monitor/reviews/j100108a019/molecular-assets/raw'
   for name in ['acetone-pubchem-2d.sdf','acetone-properties.json']:snap(q/name,'raw/'+name)
  if mid=='nitrogen-bet':
   q=M/'research-assets/incoming-paper-monitor/batches/20260920-rolling-pipeline/ja212032q/visuals/molecules/reference-snapshots/primary/liquid-nitrogen'
   for name in ['nitrogen-nist-web-tool-excerpt.txt','nitrogen-nist-extracted-reference.json']:snap(q/name,'raw/'+name)
 rdDepictor.Compute2DCoords(mol);cf=mol.GetConformer();gg=groups(mol)
 atoms=[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':cf.GetAtomPosition(a.GetIdx()).x,'y':cf.GetAtomPosition(a.GetIdx()).y,'z':0.0,'formalCharge':a.GetFormalCharge(),'isotope':a.GetIsotope(),'implicitHydrogenCount':a.GetTotalNumHs()} for a in mol.GetAtoms()]
 bonds=[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble()} for b in mol.GetBonds()]
 m2={'id':'pati2009-'+mid+'-reference','name':materials[mid]['name']+' reference','formula':formula,'sourceFormula':materials[mid]['source_formula_or_abbreviation'],'representation':'2d','has3D':False,'allowRotation':False,'indexConvention':'zero-based','coordinateUnits':'arbitrary drawing units','atoms':atoms,'bonds':bonds,'functionalGroups':gg,'caption':limits[mid],'modelType':'Reference connectivity or disconnected formula components','computedBy':'RDKit '+rdBase.rdkitVersion,'sourceType':'Reference graph, not measured coordinates','source':prov,'connectivitySmiles':smiles,'eligible_training':False}
 path2='models/pati2009-'+mid+'-2d.json';save(path2,m2);path3=None
 if cached and base[cached].get('model3dPath'):
  old=read(R/base[cached]['model3dPath']);m3=deepcopy(old);ck(mid+' 3D connectivity',canonical(modelmol(old))==canonical(mol))
  m3.update(id=m2['id'],name=m2['name'],caption=old.get('modelType','Reference geometry')+'. '+limits[mid],notes=[limits[mid]],source={'primary_reference':prov['primaryReference'],'retained_model_sha256':sha(R/base[cached]['model3dPath'])},eligible_training=False,functionalGroups=groups(modelmol(old)))
  ck(mid+' original geometry unchanged',m3['atoms']==old['atoms'] and m3['bonds']==old['bonds'])
  path3='models/pati2009-'+mid+'-3d.json';save(path3,m3)
 models[mid]={'mol':mol,'formula':formula,'groups':gg,'model2dPath':path2,'model3dPath':path3,'provenance':prov}
 qual.append({'source_material_id':mid,'reference_smiles':smiles,'reference_formula':formula,'literal_source_formula':materials[mid]['source_formula_or_abbreviation'],'fragment_count':len(Chem.GetMolFrags(mol)),'net_charge':sum(a.GetFormalCharge() for a in mol.GetAtoms()),'model2dPath':path2,'model3dPath':path3,'cached_identity':cached,'limitations':limits[mid],'provenance':prov})
entries=[]
for mid,m in materials.items():
 eid='pati2009-'+mid+'-reference';g=models.get(mid);h=770
 if g:
  formula='Ce(NO3)3·6H2O' if mid=='cerium-nitrate' else g['formula'];kind='ionic_components' if mid=='cerium-nitrate' else 'molecule';caption=scope[mid]+' '+limits[mid]
  draw=rdMolDraw2D.MolDraw2DSVG(1000,350);draw.drawOptions().padding=.12;draw.drawOptions().includeRadicals=False
  colors={i:(.72,.86,.86) for gr in g['groups'] for i in gr['atomIndices']};rdMolDraw2D.PrepareAndDrawMolecule(draw,g['mol'],highlightAtoms=list(colors),highlightAtomColors=colors);draw.FinishDrawing();svgmol=draw.GetDrawingText();svgmol=svgmol[svgmol.index('>',svgmol.index('<svg'))+1:svgmol.rindex('</svg>')]
  body='<g transform="translate(50,140)">'+svgmol+'</g>'
  if mid=='cerium-nitrate':
   # Legible multiplicities depict the same ten disconnected graph fragments;
   # these box positions never represent a hydrate coordination arrangement.
   nitrate=next(f for f in Chem.GetMolFrags(g['mol'],asMols=True) if any(a.GetSymbol()=='N' for a in f.GetAtoms()))
   nd=rdMolDraw2D.MolDraw2DSVG(290,245);nd.drawOptions().padding=.18;rdMolDraw2D.PrepareAndDrawMolecule(nd,nitrate);nd.FinishDrawing();ns=nd.GetDrawingText();ns=ns[ns.index('>',ns.index('<svg'))+1:ns.rindex('</svg>')]
   body=''
   for x,label in [(55,'1 cerium(III) ion'),(405,'3 nitrate anions'),(755,'6 water molecules')]:
    body+=f'<rect x="{x}" y="160" width="290" height="305" rx="15" fill="#f4f8fa" stroke="#c7d9e1"/>'+tx(x+145,195,label,19,'middle')
   body+=tx(200,337,'Ce³+',42,'middle')+'<g transform="translate(405,207)">'+ns+'</g>'+tx(900,337,'H₂O',42,'middle')
   body+=tx(550,449,'× 3',20,'middle')+tx(900,420,'× 6',20,'middle')
  tag='Named-identity graph; printed formula differs' if mid=='tea' else ('Disconnected formula components; arbitrary positions' if mid=='cerium-nitrate' else 'Reference molecule; no solution complex assigned')
  body+=tx(550,516,tag,18,'middle')
  lim=limits[mid]
 else:
  kind='symbolic_context';formula=m['source_formula_or_abbreviation'] if mid in ['ceria','ce-tea-complex','cerium-hydroxide','hydrated-ceria','hydroxo-complex','protonated-tea'] else None
  caption=scope[mid]+' Symbolic source context only; no molecular, product or surface coordinates are assigned.';lim='Symbolic source identity only. No reconstructed molecule, chain, material lattice or specimen coordinates.'
  body='<rect x="50" y="160" width="1000" height="345" rx="20" fill="#eff6f8" stroke="#bfd4dd"/>'
  for j,s in enumerate(symbols[mid]):body+=tx(550,245+j*77,s,23 if j==0 else 19,'middle')
 # Both the literal formula and the name-derived reference are plainly visible.
 display=formula or 'Composition / discrete species not specified'
 if mid=='tea':display='Reference C6H15NO3 · source prints (C2H5OH)3N'
 boxlines=textwrap.wrap(scope[mid],105)+['']+textwrap.wrap(lim,105);h=max(h,567+len(boxlines)*23+40)
 body+='<rect x="28" y="548" width="1044" height="'+str(h-575)+'" rx="10" fill="#edf5f8"/>'
 for j,s in enumerate(boxlines):body+=tx(48,580+j*23,s,17)
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{h}" viewBox="0 0 1100 {h}"><title>{esc(m["name"])}</title><desc>{esc(caption)}</desc><rect x="1" y="1" width="1098" height="{h-2}" rx="20" fill="white" stroke="#cbdde5"/>{tx(35,50,m["name"],26)}<path d="M35 75H1065" stroke="#d1e0e7"/>{tx(550,113,display,22,"middle")}{body}</svg>'
 path='svg/'+eid+'.svg';(O/path).write_text(svg,'utf8');raster(svg,O/'previews'/(eid+'.png'))
 primary=g['provenance']['primaryReference'] if g else None
 e={'id':eid,'name':m['name'],'aliases':[m['name']],'formula':formula,'displayFormula':display,'sourceFormula':m['source_formula_or_abbreviation'],'depictionKind':kind,'pubchemCid':base[spec[mid][2]].get('pubchemCid') if g and spec[mid][2] else None,'sourceUrls':['https://doi.org/10.1021/la8031286']+([primary] if primary else []),'svgPath':path,'model2dPath':g['model2dPath'] if g else None,'model3dPath':g['model3dPath'] if g else None,'functionalGroups':g['groups'] if g else [],'caption':caption,'limitations':[scope[mid],lim],'provenance':{'sourceDoi':'10.1021/la8031286','sourceMaterialId':mid,'sourceLocators':m['evidence'],'sourceFactsSha256':sha(P/'source-facts.json'),'canonicalFormulaRetainedSeparately':True,'referenceQualification':g['provenance'] if g else {'identityBasis':'Literal source context; unresolved structure remains symbolic.'},'measuredCoordinates':False},'binding_approved':False,'independentScientificAudit':'pending','published':False,'eligible_training':False}
 e['assetHashes']={k:sha(O/e[k]) for k in ['svgPath','model2dPath','model3dPath'] if e[k]};entries.append(e)
save('registry-additions.json',{'schemaVersion':'1.0','source_id':'pati2009','status':'private_author_proposal','binding_approved':False,'entries':entries})
stockrefs=[]
for s in source['stocks']:
 solute=s['components'][0]['material_id'];solvent=s['components'][1]['material_id'];conc=s['quantities'][0];title=('Cerium nitrate' if solute=='cerium-nitrate' else 'Triethanolamine')+' stock in '+materials[solvent]['name'].replace('Anhydrous ','')
 lines=[f"Reported stock concentration: {conc['raw_text']} {conc['unit']}.",'A 100 mL portion is subsequently transferred in the precipitation; it is not the reported stock preparation volume.','Preparation mass, total stock volume and storage are not reported.','Separate component references do not assign dissolved speciation or introduce additional reagent charges.']
 if solute=='cerium-nitrate':lines+=['Six waters belong to the hydrate formula, not an independently added water stock.']
 else:lines+=['The TEA graph follows the named identity; the printed formula conflict is preserved.']
 body='';y=300
 for line in lines:body+=wrap(line,55,y,101,19,27);y+=len(textwrap.wrap(line,101))*27+18
 h=y+35
 for x,label,role in [(55,materials[solute]['name'],'SOLUTE'),(585,materials[solvent]['name'],'SOLVENT')]:body+=f'<rect x="{x}" y="115" width="460" height="140" rx="15" fill="#eef6f8" stroke="#bed4de"/>'+tx(x+230,160,role,16,'middle')+tx(x+230,213,label,22,'middle')
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{h}"><rect width="1100" height="{h}" fill="white"/>{tx(35,55,title,26)}{body}</svg>'
 rel='stock-svg/pati2009-'+s['id']+'.svg';(O/rel).write_text(svg,'utf8');raster(svg,O/'stock-previews'/('pati2009-'+s['id']+'.png'));stockrefs.append({'stock_id':s['id'],'source_stock':s,'svg_path':rel,'sha256':sha(O/rel),'binding_approved':False})
for mid,g in models.items():
 if not g['model3dPath']:continue
 model=read(O/g['model3dPath']);xy=[(a['x']+.31*a['z'],a['y']+.17*a['z']) for a in model['atoms']];lo=[min(p[k] for p in xy) for k in [0,1]];hi=[max(p[k] for p in xy) for k in [0,1]];scale=min(780/max(hi[0]-lo[0],1),300/max(hi[1]-lo[1],1));pts=[(150+(p[0]-lo[0])*scale,160+(p[1]-lo[1])*scale) for p in xy];body=''
 for b in model['bonds']:
  a,z=pts[b['a']],pts[b['b']];body+=f'<path d="M{a[0]} {a[1]}L{z[0]} {z[1]}" stroke="#8ba2b1" stroke-width="4"/>'
 for a,(x,y) in zip(model['atoms'],pts):
  body+=f'<circle cx="{x}" cy="{y}" r="{8 if a["element"]=="H" else 15}" fill="'+{'O':'#e69193','H':'#e7edf2','C':'#9bb5c7','N':'#8d9dde'}[a['element']]+'" stroke="#456271"/>'
  if a['element']!='H':body+=tx(x,y+5,a['element'],13,'middle')
 h=750;svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{h}"><rect width="1100" height="{h}" fill="white"/>{tx(35,50,materials[mid]["name"]+" · retained reference geometry",24)}{body}{wrap(model["caption"],45,555,106,18,26)}</svg>';raster(svg,O/'conformer-previews'/(mid+'.png'))
panels=sorted((O/'previews').glob('*.png'))+sorted((O/'stock-previews').glob('*.png'))+sorted((O/'conformer-previews').glob('*.png'))
for start in range(0,len(panels),6):
 items=panels[start:start+6];canvas=Image.new('RGB',(1500,((len(items)+1)//2)*560),'#e8eef1');d=ImageDraw.Draw(canvas)
 for j,p in enumerate(items):
  im=Image.open(p);im.thumbnail((730,510));x=(j%2)*750+(750-im.width)//2;y=(j//2)*560+30;canvas.paste(im,(x,y));d.text(((j%2)*750+10,(j//2)*560+7),p.stem,fill='#294658')
 canvas.save(O/'contacts'/f'contact-{start//6+1:02}.png')
snap(M/'recipe-atlas/dist/chemical-viewer.mjs','chemical-viewer.mjs')
save('source-stock-reference-proposal.json',{'stocks':stockrefs,'binding_approved':False})
save('reference-qualification.json',{'author':'/root/peng1998_reader_assets','source_id':'pati2009','models':qual,'snapshots':snapshots,'new_network_lookups':0,'new_3d_generated':False,'atomic_product_models':False,'source_assay_inferred':False,'identity_conflict':'Named triethanolamine C6H15NO3 graph is distinct from printed (C2H5OH)3N. The canonical/source formula is unchanged. Protonated printed TEA remains symbolic.'})
save('input-bindings.json',{'source_files':{str(P/n):sha(P/n) for n in ['source-facts.json','source-inventory.json','package-freeze.json','source-independent-audit/independent-audit.json']},'canonical_record_manifest':{'path':str(C/'record-manifest.json'),'sha256':sha(C/'record-manifest.json')},'canonical_package_manifest':{'path':str(C/'package-manifest.json'),'sha256':sha(C/'package-manifest.json')},'snapshot_originals_are_provenance_only':True})
save('generation-checks.json',{'author':'/root/peng1998_reader_assets','status':'passed_author_checks','checks':checks,'check_count':len(checks),'counts':{'identities':len(entries),'models2d':len(models),'models3d':sum(bool(g['model3dPath']) for g in models.values()),'symbols':len(symbols),'previews':len(panels)},'independent_approval':False})
print(json.dumps({'status':'generated','checks':len(checks),'identities':len(entries),'models2d':len(models),'models3d':sum(bool(g['model3dPath']) for g in models.values()),'panels':len(panels)}))
