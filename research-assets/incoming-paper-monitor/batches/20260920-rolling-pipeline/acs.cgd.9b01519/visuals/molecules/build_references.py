"""Sommer source-qualified working references. No network/Site/source writes."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
from collections import Counter
import hashlib,html,json,math,sys,textwrap
O=Path(__file__).resolve().parent;P=O.parents[1];M=P.parents[4];S=M/'recipe-atlas';R=S/'dist/assets/chemical-registry'
sys.dont_write_bytecode=True
sys.path.insert(0,str(M/'research-assets/rdkit-runtime'));sys.path.insert(0,str(M/'research-assets/corpus-20260917/runtime'))
from rdkit import Chem,rdBase
from rdkit.Chem import rdDepictor,rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
import pymupdf
from PIL import Image,ImageDraw
assert not (O/'package-freeze.json').exists(),'Preserve a freeze; revise separately.'
for name in ['models','svg','previews','contacts','stock-svg','stock-previews','conformer-previews','reference-snapshots']:(O/name).mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,obj):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def esc(x):return html.escape(str(x),quote=True)
def tx(x,y,s,size=19,anchor='start',fill='#294558'):return f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" text-anchor="{anchor}" fill="{fill}">{esc(s)}</text>'
def wrap(s,x,y,width=93,size=18,line=25):return ''.join(tx(x,y+i*line,t,size) for i,t in enumerate(textwrap.wrap(s,width)))
def raster(svg,path):
 doc=pymupdf.open(stream=svg.encode(),filetype='svg');doc[0].get_pixmap(alpha=False).save(str(path));doc.close()
checks=[];inputs={};snapshots=[]
def ck(label,ok):checks.append({'check':label,'passed':bool(ok)});assert ok,label
def snap(p,rel):
 p=Path(p);dest=O/'reference-snapshots'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():assert sha(dest)==sha(p),'Immutable snapshot differs: '+str(dest)
 else:dest.write_bytes(p.read_bytes())
 inputs[str(p)]=sha(p);snapshots.append({'source':str(p),'snapshot':str(dest.relative_to(O)),'sha256':sha(p)});return dest
source=read(P/'source-facts.json');freeze=read(P/'package-freeze.json')
ck('Source identity',source['source_id']=='sommer2020' and source['doi']=='10.1021/acs.cgd.9b01519')
for name in ['source-facts.json','source-inventory.json','package-freeze.json','intake-identity.json']:
 inputs[str(P/name)]=sha(P/name)
snap(R/'registry.json','registry-base.json');base={e['id']:e for e in read(R/'registry.json')['entries']}
materials={x['id']:x for x in source['materials']};ck('28 identities',len(materials)==28)
water={'demin-feed-water','demin-wash-water','insitu-water','millipore-water','deionized-background'}
ethanol={'ethanol-96','ethanol-99'}
graph_specs={
 'water':('O','H2O','water'),'ethanol':('CCO','C2H6O','ethanol'),
 'zn-nitrate':('O.O.O.O.O.O.O=[N+]([O-])[O-].O=[N+]([O-])[O-].[Zn+2]','H12N2O12Zn','zinc-nitrate-hexahydrate'),
 'al-nitrate':('[Al+3].O=[N+]([O-])[O-].O=[N+]([O-])[O-].O=[N+]([O-])[O-].O.O.O.O.O.O.O.O.O','H18AlN3O18',None),
 'naoh':('[Na+].[OH-]','HNaO','sodium-hydroxide'),
 'nitrate-context':('O=[N+]([O-])[O-]','NO3-',None),
}
limits={
 'water':'One free-water reference; no hydration shell, solution aggregate or purity is inferred. Water grade and use are qualified separately for each source context.',
 'ethanol':'One ethanol reference, not the complete commercial liquid. The paper reports separate 96% wash and 99% microscopy grades; their percentage bases and other constituents are not specified.',
 'zn-nitrate':'Formal Zn2+ + 2 NO3- + 6 H2O formula components. Hydration count is source-reported; disconnected drawing positions are not zinc coordination, crystal packing or dissolved speciation.',
 'al-nitrate':'Formal Al3+ + 3 NO3- + 9 H2O formula components. The source names the nonahydrate; no isolated hydrated complex, lattice or solution coordination is recovered.',
 'naoh':'Formal Na+ and OH- component reference only. No covalent Na-O bond, ion pair or hydration geometry is asserted. Concentrations do not supply missing weighed NaOH charges.',
 'nitrate-context':'One resonance representation of the nitrate anion, not a separate reagent addition or measured geometry. Equivalent nitrate resonance forms are not different source species.',
}
symbol_lines={
 'zno-feed':['Purchased nanosized ZnO','Approximately 30 nm starting powder','Distinct from reaction-generated ZnO'],
 'aloh3':['Al(OH)3 starting solid','Purity and solid form not reported','No isolated molecule or hydroxide surface model'],
 'quartz-vessel':['Quartz reaction-vessel material','Nominal vessel and fill volumes remain separate','No atomic quartz structure or apparatus dimensions inferred'],
 'sapphire-tube':['Sapphire sensor immersion tube','Microwave temperature/pressure sensor housing','Distinct from the in situ sample capillary'],
 'ptfe-autoclave':['Teflon-lined stainless-steel autoclave','Liner / container identity only','Not a soluble ingredient or atomic surface model'],
 'sapphire-capillary':['Single-crystal sapphire sample capillary','In situ measurement support','No specimen or substrate atomic coordinates'],
 'glass-capillary':['Glass diffraction capillary','Ex situ synchrotron specimen support','Glass composition and surface structure unresolved'],
 'tem-grid':['Copper grid + Formvar/carbon support','200 mesh microscopy support','No polymer repeat sequence or surface coordinates'],
 'lab6-660a':['LaB6 NIST 660A reference','Laboratory XRD resolution standard','Separate from the PDF 660b reference'],
 'lab6-660b':['LaB6 NIST 660b reference','PDF / reciprocal-space resolution standard','Separate from the laboratory 660A reference'],
 'ceria-reference':['CeO2 reference solid','Synchrotron resolution / wavelength standard','Not a reaction ingredient or sample model'],
 'baso4-reference':['BaSO4 reference solid','Optical diffuse-reflectance reference','No source crystal coordinates supplied'],
 'spinel-product':['ZnAl2O4 spinel material family','Sizes / phases / defects are sample-specific','No atomic structure or sample binding proposed here'],
 'zno-intermediate':['Reaction-generated ZnO context','Intermediate or impurity, source-specific','Does not inherit the purchased powder size'],
 'alooh-impurity':['AlOOH impurity context','Separate from Al(OH)3 starting powder','No phase fraction or geometry inferred'],
 'zinc-aquo-context':['Proposed aqueous zinc precursor entities','Protonation and association remain unresolved','No exact hydrate, charge or recovered molecular graph'],
 'al-dimer-context':['Proposed octahedral aluminum dimer','Variable protonation/hydration in source model','No exact molecular graph or coordinates assigned'],
}
ck('Every source ID covered',water|ethanol|{'zn-nitrate','al-nitrate','naoh','nitrate-context'}|set(symbol_lines)==set(materials))
def mol_from_model(raw):
 rw=Chem.RWMol()
 for a in raw['atoms']:
  atom=Chem.Atom(a['element']);atom.SetFormalCharge(a.get('formalCharge',0));atom.SetIsotope(a.get('isotope',0));rw.AddAtom(atom)
 for b in raw['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
 mol=rw.GetMol();Chem.SanitizeMol(mol);return mol
def canon(m):return Chem.MolToSmiles(Chem.RemoveHs(m))
def groups(m):
 out=[]
 for name,pattern in [('Nitrate resonance group','[N+](=O)([O-])[O-]'),('Hydroxide ion','[OH-]'),('Sodium ion','[Na+]'),('Zinc(II) ion','[Zn+2]'),('Aluminum(III) ion','[Al+3]'),('Alcohol group','[CX4][OX2H]')]:
  for ids in m.GetSubstructMatches(Chem.MolFromSmarts(pattern)):
   ids=sorted(ids);out.append({'label':name,'atomIndices':ids,'bondIndices':[b.GetIdx() for b in m.GetBonds() if b.GetBeginAtomIdx() in ids and b.GetEndAtomIdx() in ids]})
 return out
models={};qualified=[]
for key,(smiles,formula,cached) in graph_specs.items():
 mol=Chem.MolFromSmiles(smiles);ck(key+' formula',rdMolDescriptors.CalcMolFormula(mol)==formula)
 provenance={'identity_basis':'Conventional formal component representation of explicitly named source identity; no experimental coordinates.','source_url':'https://doi.org/10.1021/acs.cgd.9b01519'}
 if cached:
  entry=base[cached];save('reference-snapshots/entry-'+cached+'.json',entry)
  for field in ['svgPath','model2dPath','model3dPath']:
   if entry.get(field):ck(cached+' cache hash '+field,sha(R/entry[field])==entry['assetHashes'][field]);snap(R/entry[field],entry[field])
  raw=read(R/entry['model2dPath']);ck(key+' cached graph matches named components',canon(mol_from_model(raw))==canon(mol))
  provenance.update(retained_registry_id=cached,retained_model2d_sha256=sha(R/entry['model2dPath']),original_entry_snapshot='reference-snapshots/entry-'+cached+'.json')
  if entry.get('pubchemCid'):provenance['primary_reference']='https://pubchem.ncbi.nlm.nih.gov/compound/'+str(entry['pubchemCid'])
 rdDepictor.Compute2DCoords(mol);conf=mol.GetConformer();gg=groups(mol)
 # Explicitly space disconnected hydrate components. These are arbitrary 2D
 # display offsets, never intermolecular distances or coordination geometry.
 if key in ('zn-nitrate','al-nitrate'):
  frags=Chem.GetMolFrags(mol);nitrate_frags=[f for f in frags if any(mol.GetAtomWithIdx(i).GetSymbol()=='N' for i in f)]
  waters=[f for f in frags if len(f)==1 and mol.GetAtomWithIdx(f[0]).GetSymbol()=='O']
  metal=[f for f in frags if len(f)==1 and mol.GetAtomWithIdx(f[0]).GetSymbol() in ('Zn','Al')]
  placements=[(f,(-len(nitrate_frags)/2+j+.5)*4.5,2.0) for j,f in enumerate(nitrate_frags)]
  placements += [(f,(j%5-2)*2.8,-2.3-(j//5)*2.8) for j,f in enumerate(waters)]
  placements += [(f,-8.0,2.0) for f in metal]
  for ids,cx,cy in placements:
   mx=sum(conf.GetAtomPosition(i).x for i in ids)/len(ids);my=sum(conf.GetAtomPosition(i).y for i in ids)/len(ids)
   for i in ids:
    v=conf.GetAtomPosition(i);conf.SetAtomPosition(i,(v.x-mx+cx,v.y-my+cy,0.0))
 atoms=[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':conf.GetAtomPosition(a.GetIdx()).x,'y':conf.GetAtomPosition(a.GetIdx()).y,'z':0.0,'formalCharge':a.GetFormalCharge(),'isotope':a.GetIsotope(),'implicitHydrogenCount':a.GetTotalNumHs()} for a in mol.GetAtoms()]
 bonds=[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble()} for b in mol.GetBonds()]
 mp='models/sommer2020-'+key+'-2d.json';model={'id':'sommer2020-'+key+'-reference','name':key,'formula':formula,'representation':'2d','has3D':False,'allowRotation':False,'indexConvention':'zero-based','coordinateUnits':'arbitrary drawing units','atoms':atoms,'bonds':bonds,'functionalGroups':gg,'caption':limits[key],'modelType':'Source-qualified connectivity or disconnected formal components','computedBy':'RDKit '+rdBase.rdkitVersion,'sourceType':'Reference connectivity; not measured sample geometry','source':provenance,'connectivitySmiles':smiles,'notes':[limits[key]],'eligible_training':False}
 save(mp,model);models[key]={'model2dPath':mp,'model3dPath':None,'groups':gg,'mol':mol,'formula':formula,'provenance':provenance}
 if key in ('water','ethanol'):
  raw=read(R/base[cached]['model3dPath']);new=deepcopy(raw)
  new.update(id='sommer2020-'+key+'-reference',name='Water' if key=='water' else 'Ethanol',caption='Retained cached illustrative conformer, not measured sample coordinates. '+limits[key],sourceType='PubChem connectivity with retained locally computed illustrative coordinates',source={'primary_reference':provenance['primary_reference'],'retained_model_sha256':sha(R/base[cached]['model3dPath'])},notes=[limits[key]],eligible_training=False,functionalGroups=groups(mol_from_model(raw)))
  ck(key+' exact retained3D arrays',new['atoms']==raw['atoms'] and new['bonds']==raw['bonds']);ck(key+' retained3D graph',canon(mol_from_model(raw))==canon(mol))
  ck(key+' finite 3D',all(math.isfinite(a[k]) for a in raw['atoms'] for k in ('x','y','z')))
  for b in raw['bonds']:ck(key+' bond length',.6<math.dist([raw['atoms'][b['a']][k] for k in ('x','y','z')],[raw['atoms'][b['b']][k] for k in ('x','y','z')])<1.8)
  path='models/sommer2020-'+key+'-3d.json';save(path,new);models[key]['model3dPath']=path
 qualified.append({'reference_key':key,'graph_smiles':smiles,'formula':formula,'fragment_count':len(Chem.GetMolFrags(mol)),'net_formal_charge':sum(a.GetFormalCharge() for a in mol.GetAtoms()),'model2dPath':mp,'model3dPath':models[key]['model3dPath'],'cached_identity':cached,'source_neutral_display':True,'qualification':limits[key]})
# The new nitrate and aluminum-salt drawings reuse the exact nitrate connectivity present in cached zinc nitrate.
nitrate=Chem.MolFromSmiles(graph_specs['nitrate-context'][0]);znmol=models['zn-nitrate']['mol'];almol=models['al-nitrate']['mol']
ck('Two nitrate fragments in zinc salt',sum(canon(x)==canon(nitrate) for x in Chem.GetMolFrags(znmol,asMols=True))==2)
ck('Three nitrate fragments in aluminum salt',sum(canon(x)==canon(nitrate) for x in Chem.GetMolFrags(almol,asMols=True))==3)
ck('Hydrate counts6/9',sum(canon(x)=='O' for x in Chem.GetMolFrags(znmol,asMols=True))==6 and sum(canon(x)=='O' for x in Chem.GetMolFrags(almol,asMols=True))==9)
for key in ['zn-nitrate','al-nitrate','naoh']:ck(key+' no cation coordination bonds',all(b.GetBeginAtom().GetSymbol() not in ('Zn','Al','Na') and b.GetEndAtom().GetSymbol() not in ('Zn','Al','Na') for b in models[key]['mol'].GetBonds()))
rawdir=M/'research-assets/quality-20260918/molecules/raw'
for key in ['water','ethanol','zinc-nitrate-hexahydrate']:
 for suffix in ['-properties.json','-pubchem-2d.sdf']:
  p=rawdir/(key+suffix);dest=snap(p,'primary/'+p.name)
  if p.suffix=='.sdf':
   m=Chem.SDMolSupplier(str(dest),removeHs=False)[0];gkey='zn-nitrate' if key.startswith('zinc') else key;ck(key+' primary cached SDF graph',canon(m)==canon(models[gkey]['mol']))
entries=[]
def graph_body(m,key):
 if key in ('zn-nitrate','al-nitrate'):
  m=Chem.MolFromSmiles(graph_specs['nitrate-context'][0]);rdDepictor.Compute2DCoords(m)
  drawer=rdMolDraw2D.MolDraw2DSVG(360,220);opts=drawer.drawOptions();opts.padding=.15
  rdMolDraw2D.PrepareAndDrawMolecule(drawer,m);drawer.FinishDrawing();ss=drawer.GetDrawingText();ss=ss[ss.index('>',ss.index('<svg'))+1:ss.rindex('</svg>')]
  metal,n,water=('Zn2+',2,6) if key=='zn-nitrate' else ('Al3+',3,9)
  return (tx(550,180,'Disconnected formula components',22,'middle')+tx(155,310,metal,35,'middle')+tx(275,310,'+',30,'middle')+tx(360,310,str(n)+' ×',30,'middle')+'<g transform="translate(390,200)">'+ss+'</g>'+tx(775,310,'+',30,'middle')+tx(925,310,str(water)+' H2O',35,'middle')+tx(550,450,'Coefficients count formula components; no coordination bonds are drawn.',19,'middle'))
 drawer=rdMolDraw2D.MolDraw2DSVG(990,330);opts=drawer.drawOptions();opts.padding=.10
 gg=groups(m);palette=[(.85,.68,.35),(.49,.72,.77),(.64,.55,.80)];colors={i:palette[j%3] for j,g in enumerate(gg) for i in g['atomIndices']}
 rdMolDraw2D.PrepareAndDrawMolecule(drawer,m,highlightAtoms=list(colors),highlightAtomColors=colors);drawer.FinishDrawing();ss=drawer.GetDrawingText();ss=ss[ss.index('>',ss.index('<svg'))+1:ss.rindex('</svg>')]
 return '<g transform="translate(55,150)">'+ss+'</g>'
for mid,m in materials.items():
 key='water' if mid in water else 'ethanol' if mid in ethanol else mid;graph=models.get(key);eid='sommer2020-'+mid+'-reference';formula=m['source_formula_or_abbreviation']
 if graph:
  kind='molecule' if key in ('water','ethanol') else 'ionic_components';caption=m['scope_note']+' '+limits[key];body=graph_body(graph['mol'],key);model2d=graph['model2dPath'];model3d=graph['model3dPath'];fg=graph['groups'];provenance=graph['provenance']
 else:
  kind='symbolic_context';caption=m['scope_note']+' Symbolic material identity only; no molecular, crystal, solution or product geometry is assigned.';model2d=model3d=None;fg=[];provenance={'identity_basis':'Literal source material/context label; no coordinate model.'}
  body='<rect x="60" y="155" width="980" height="330" rx="18" fill="#f1f7fa" stroke="#b9d0db"/>'
  for j,line in enumerate(symbol_lines[mid]):body+=tx(550,245+j*78,line,24 if j==0 else 21,'middle')
 display=formula if formula else 'Composition / exact species not specified'
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="700" viewBox="0 0 1100 700"><title>{esc(m["name"])}</title><desc>{esc(caption)}</desc><rect x="1" y="1" width="1098" height="698" rx="20" fill="white" stroke="#cbdde5"/>{tx(36,48,m["name"],25)}<path d="M36 75H1064" stroke="#d5e3e8"/>{tx(550,115,display,23,"middle")}{body}<rect x="30" y="520" width="1040" height="148" rx="10" fill="#eef5f8"/>{wrap(m["scope_note"],50,550,102,17,23)}{wrap("Reference identity only. No exact solution species or source atomic structure is reconstructed.",50,628,103,16,21)}</svg>'
 path='svg/'+eid+'.svg';(O/path).write_text(svg,encoding='utf8');raster(svg,O/'previews'/(eid+'.png'))
 entry={'id':eid,'name':m['name'],'aliases':[m['name']],'formula':formula,'displayFormula':formula,'depictionKind':kind,'pubchemCid':base['water']['pubchemCid'] if key=='water' else base['ethanol']['pubchemCid'] if key=='ethanol' else base['zinc-nitrate-hexahydrate']['pubchemCid'] if key=='zn-nitrate' else None,'sourceUrls':['https://doi.org/10.1021/acs.cgd.9b01519']+([provenance['primary_reference']] if provenance.get('primary_reference') else []),'svgPath':path,'model2dPath':model2d,'model3dPath':model3d,'functionalGroups':fg,'caption':caption,'limitations':[m['scope_note'],limits[key] if graph else 'Symbolic context only; no molecule, product coordinates or exact specimen binding.'],'provenance':{'sourceDoi':'10.1021/acs.cgd.9b01519','sourceMaterialId':mid,'sourceLocators':m['evidence'],'sourceFactsSha256':sha(P/'source-facts.json'),'sourceGeneration':2,'referenceQualification':provenance,'measuredCoordinates':False},'binding_approved':False,'independentScientificAudit':'pending','published':False,'eligible_training':False}
 entry['assetHashes']={k:sha(O/entry[k]) for k in ['svgPath','model2dPath','model3dPath'] if entry.get(k)};entries.append(entry)
save('registry-additions.json',{'schema_version':'1.0','source_id':'sommer2020','status':'working_unapproved_source_and_canonical_gates_pending','binding_approved':False,'entries':entries})
def qfmt(q):
 raw=q.get('raw_text');return (str(raw) if raw is not None else 'Not reported')+(' '+q['unit'] if q.get('unit') and q['unit']!='ratio_parts' else '')
stocks=[]
for stock in source['stocks']:
 lines=[stock['notes'],'Scope: '+stock['sample_scope']]+[q['meaning']+': '+qfmt(q) for q in stock['quantities']]
 rows=[];y=170
 for line in lines:
  pieces=textwrap.wrap(line,100);rows.append(wrap(line,55,y,100,18,25));y+=len(pieces)*25+17
 height=max(590,y+100);body=''.join(rows)
 comp=' + '.join(materials[x]['name'] if x in materials else x+' (inherited stock)' for x in stock['components'])
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{height}" viewBox="0 0 1100 {height}"><title>{esc(stock["name"])}</title><rect x="1" y="1" width="1098" height="{height-2}" rx="18" fill="white" stroke="#cbdde5"/>{tx(35,45,stock["name"],25)}{wrap(comp,40,88,110,17,23)}{body}{tx(40,height-35,"Source stock context only; component models do not establish solution speciation.",16)}</svg>'
 path='stock-svg/sommer2020-'+stock['id']+'.svg';(O/path).write_text(svg,encoding='utf8');raster(svg,O/'stock-previews'/('sommer2020-'+stock['id']+'.png'))
 stocks.append({'source_stock_id':stock['id'],'source_stock_snapshot':stock,'svg_path':path,'sha256':sha(O/path),'canonical_bindings':'pending','binding_approved':False})
save('source-stock-reference-proposal.json',{'status':'working_unapproved','stocks':stocks,'no_repeated_stock_charges':True,'notes':'Nested MW stocks remain inherited formulations. Exact canonical slot/component quantities will be bound after canonical freeze; whole charges and1mL aliquots are not equated.'})
save('reference-qualification.json',{'status':'author_working_unapproved','source_scope':'Main only; SI unlocated/unverified','models':qualified,'actual_source_read_scope':{'text_pages':[2,7,8],'visual_pages':[2,7,8],'not_complete_source_audit':True},'no_new_3d_generated':True,'no_atomic_product_models':True,'source_and_canonical_audits_pending':True,'snapshots':snapshots})
save('input-bindings.json',{'status':'working','inputs':inputs,'source_freeze_sha256':sha(P/'package-freeze.json'),'source_facts_sha256':sha(P/'source-facts.json'),'canonical_record_manifest':None})
save('generation-checks.json',{'status':'passed_author_working','checks':checks,'counts':{'source_identities':len(entries),'source_stocks':len(stocks),'new_2d_models':6,'retained_3d_models':2,'symbolic_cards':len(symbol_lines)},'independent_approval':False})
# Two previews project the unchanged free-compound coordinates; no new geometry.
for key in ('water','ethanol'):
 model=read(O/models[key]['model3dPath']);xy=[(a['x']+.31*a['z'],a['y']+.17*a['z'])for a in model['atoms']]
 lo=[min(p[k]for p in xy)for k in (0,1)];hi=[max(p[k]for p in xy)for k in (0,1)];sc=min(700/max(hi[0]-lo[0],1),320/max(hi[1]-lo[1],1));pts=[(180+(p[0]-lo[0])*sc,150+(p[1]-lo[1])*sc)for p in xy];body=''
 for b in model['bonds']:
  a,z=pts[b['a']],pts[b['b']];body+=f'<path d="M{a[0]} {a[1]}L{z[0]} {z[1]}" stroke="#8da3b2" stroke-width="7"/>'
 for a,(x,y)in zip(model['atoms'],pts):body+=f'<circle cx="{x}" cy="{y}" r="23" fill="'+{'O':'#e69193','H':'#e6eef3','C':'#99b3c4'}[a['element']]+'" stroke="#466273"/>'+tx(x,y+7,a['element'],20,'middle')
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="700"><rect width="1100" height="700" fill="white"/>{tx(40,50,key.capitalize()+" · unchanged illustrative reference coordinates",26)}{body}{wrap(model["caption"],45,555,102,19,29)}</svg>';raster(svg,O/'conformer-previews'/f'{key}.png')
# Contact sheets remain private. They are author-review aids, not source imagery.
files=list(sorted((O/'previews').glob('*.png')))+list(sorted((O/'stock-previews').glob('*.png')))+list(sorted((O/'conformer-previews').glob('*.png')))
for batch in range(0,len(files),6):
 canvas=Image.new('RGB',(1500,((min(6,len(files)-batch)+1)//2)*560),'#e8eef1');draw=ImageDraw.Draw(canvas)
 for j,p in enumerate(files[batch:batch+6]):
  im=Image.open(p);im.thumbnail((730,505));x=(j%2)*750+(750-im.width)//2;y=(j//2)*560+30;canvas.paste(im,(x,y));draw.text(((j%2)*750+10,(j//2)*560+7),p.stem,fill='#294558')
 canvas.save(O/'contacts'/f'contact-{batch//6+1:02}.png')
save('working-checkpoint.json',{'status':'working_references_created_unapproved','created_at':datetime.now(timezone.utc).isoformat(),'counts':{'source_material_ids':28,'source_stocks':7,'identity_svgs':28,'stock_svgs':7,'model2d_files':6,'model3d_files':2,'previews':37},'pending':['Final actual visual author review of37 previews','Independent source audit and canonical freeze','Exact material-slot/stock component bindings','Persisted scientific/geometry/viewer validation','Independent molecule audit'],'source_facts_sha256':sha(P/'source-facts.json'),'registry_sha256':sha(O/'registry-additions.json'),'script_sha256':sha(Path(__file__))})
print(json.dumps({'status':'working_unapproved','identities':len(entries),'stocks':len(stocks),'checks':len(checks),'registry_sha256':sha(O/'registry-additions.json')}))
