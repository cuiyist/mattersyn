"""Evans source-scoped chemical identities; local retained references only."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
from datetime import datetime,timezone
import json,hashlib,html,math,sys,re
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;B=O.parents[1];ROOT=B.parents[4]
sys.path.insert(0,str(ROOT/'research-assets/rdkit-runtime'));sys.path.insert(0,str(ROOT/'research-assets/corpus-20260917/runtime'))
from rdkit import Chem
from rdkit.Chem import rdDepictor,rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
import pymupdf
from PIL import Image,ImageDraw
import numpy as np
SITE=ROOT/'recipe-atlas';REG=SITE/'dist/assets/chemical-registry';C=B/'canonical-proposal/v2'
if (O/'package-freeze.json').exists():raise SystemExit('Frozen package; preserve a new revision instead of rebuilding.')
for d in ['svg','models','previews','contacts','reference-snapshots','source-evidence']:(O/d).mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def esc(x):return html.escape(str(x),quote=True)
def norm(x):return re.sub('[^a-z0-9]+','-',str(x).lower()).strip('-')
def tx(x,y,s,n=18,color='#365263',anchor='middle'):return f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{n}" fill="{color}" text-anchor="{anchor}">{esc(s)}</text>'
inputs={};snapshots=[]
def bind(p):p=Path(p);inputs[str(p)]=sha(p)
def snap(p,rel):
 p=Path(p);out=O/'reference-snapshots'/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(p.read_bytes());bind(p);snapshots.append({'original_path':str(p),'sha256':sha(p),'snapshot_path':str(out.relative_to(O))});return out
MAN=read(C/'record-manifest.json');I=read(B/'source-inventory.json');A=read(B/'source-scientific-audit.json');F=read(B/'source-extraction-revision-2/source-facts.json')
for p in [C/'record-manifest.json',B/'source-inventory.json',B/'source-extraction-revision-2/source-facts.json',B/'source-scientific-audit.json',B/'proposal-freeze-v2.json',B/'cif-source-inventory.json',SITE/'dist/chemical-viewer.mjs']:bind(p)
records={x['record_id']:read(x['path']) for x in MAN['records']}
for x in MAN['records']:assert sha(x['path'])==x['sha256'];bind(x['path'])
units={x['id']:x for x in I['units']};srcmaterials={x['id']:x for x in I['materials']}
base={e['id']:e for e in read(REG/'registry.json')['entries']};bind(REG/'registry.json')
slots={}
for rid,r in records.items():
 for i,m in enumerate(r['materials']):slots.setdefault(m['id'],[]).append((rid,i,m))
assert len(slots)==50 and sum(map(len,slots.values()))==123
for aid in ['scheme-1','table-1','figure-S1','figure-S2','figure-S3','figure-S12','figure-S13']:
 p=B/'reader-assets/selected-originals'/(aid+'.png');(O/'source-evidence'/(aid+'.png')).write_bytes(p.read_bytes());bind(p)
ENTRIES=[];QUAL=[];CHECKS=[]
def identity(mid,name=None,kind='molecule'):
 m=slots[mid][0][2];e={'id':'evans2010-'+norm(mid)+'-reference','name':name or m['name'],'aliases':[m['name']],'formula':m['formula'],'displayFormula':m['formula'],'depictionKind':kind,'pubchemCid':None,'svgPath':'svg/evans2010-'+norm(mid)+'-reference.svg','model2dPath':None,'model3dPath':None,'functionalGroups':[],'sourceUrls':['https://doi.org/10.1021/ja103805s'],'caption':'Source-scoped chemical reference; not a measured solution species.','limitations':['No solution speciation, aggregation, surface coordination or preparation yield is inferred from this illustration.'],'provenance':{'sourceDoi':'10.1021/ja103805s','sourceLocators':m['evidence'],'sourceMaterialId':mid,'sourceAuditSha256':sha(B/'source-scientific-audit.json'),'measuredCoordinates':False},'binding_approved':False,'independentScientificAudit':'pending','published':False,'eligible_training':False};return e
def frame(e,body,footer):
 title=e['name'];size=26 if len(title)<52 else 21
 return f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="600" viewBox="0 0 1100 600"><title>{esc(title)}</title><desc>{esc(e["caption"])}</desc><rect x="1" y="1" width="1098" height="598" rx="22" fill="#ffffff" stroke="#cbdde5"/>{tx(40,48,title,size,anchor="start")}<path d="M40 70H1060" stroke="#d5e3e8"/>{tx(550,104,e.get("displayFormula") or "Composition unresolved",20)}{body}<rect x="32" y="537" width="1036" height="42" rx="9" fill="#edf5f7"/>{tx(550,564,footer,17)}</svg>'
def render(e,svg):
 (O/e['svgPath']).write_text(svg,encoding='utf-8');doc=pymupdf.open(stream=svg.encode(),filetype='svg');doc[0].get_pixmap(matrix=pymupdf.Matrix(1,1),alpha=False).save(str(O/'previews'/(e['id']+'.png')))
 e['assetHashes']={k:sha(O/e[k]) for k in ['svgPath','model2dPath','model3dPath'] if e.get(k)};ENTRIES.append(e)
def symbols(e,lines,footer):
 body='<rect x="160" y="158" width="780" height="330" rx="22" fill="#f4f8fa" stroke="#cbdde5"/>'
 for j,line in enumerate(lines):body+=tx(550,218+j*64,line,32 if j==0 else 23,'#87549e' if j==0 else '#365263')
 render(e,frame(e,body,footer))
def groups(mol):
 out=[]
 for label,pattern in [('Phosphorus center','[#15]'),('Selenium functionality','[#34]'),('Carbonyl / carboxyl functionality','[CX3](=[OX1])[OX2,OX1]'),('Carbonyl functionality','[CX3]=[OX1]')]:
  ids=sorted({a for match in mol.GetSubstructMatches(Chem.MolFromSmarts(pattern)) for a in match})
  if ids:out.append({'label':label,'atomIndices':ids,'bondIndices':[b.GetIdx() for b in mol.GetBonds() if b.GetBeginAtomIdx() in ids and b.GetEndAtomIdx() in ids]})
 return out
def model2d(e,mol,basis):
 Chem.SanitizeMol(mol);rdDepictor.Compute2DCoords(mol);conf=mol.GetConformer();fg=groups(mol)
 atoms=[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':conf.GetAtomPosition(a.GetIdx()).x,'y':conf.GetAtomPosition(a.GetIdx()).y,'z':0.0,'formalCharge':a.GetFormalCharge(),'isotope':a.GetIsotope(),'implicitHydrogenCount':a.GetTotalNumHs()} for a in mol.GetAtoms()]
 bonds=[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':1.5 if b.GetIsAromatic() else b.GetBondTypeAsDouble()} for b in mol.GetBonds()]
 e['model2dPath']='models/'+e['id']+'-2d.json';e['functionalGroups']=fg
 save(e['model2dPath'],{'id':e['id'],'name':e['name'],'formula':e['formula'],'representation':'2d','has3D':False,'allowRotation':False,'indexConvention':'zero-based','coordinateUnits':'arbitrary drawing units','modelType':'Source-supported connectivity; generated 2D layout','caption':e['caption'],'connectivitySmiles':Chem.MolToSmiles(mol),'atoms':atoms,'bonds':bonds,'functionalGroups':fg,'source':basis,'notes':e['limitations']})
 drawer=rdMolDraw2D.MolDraw2DSVG(1000,390);opts=drawer.drawOptions();opts.padding=.09;opts.addStereoAnnotation=True
 for a in mol.GetAtoms():
  if a.GetAtomicNum()==0:opts.atomLabels[a.GetIdx()]='R'
 colors={};palette=[(.84,.65,.28),(.64,.43,.74),(.22,.65,.62),(.79,.42,.51)]
 for i,g in enumerate(fg):
  for ai in g['atomIndices']:colors[ai]=palette[i%len(palette)]
 rdMolDraw2D.PrepareAndDrawMolecule(drawer,mol,highlightAtoms=list(colors),highlightAtomColors=colors);drawer.FinishDrawing();svg=drawer.GetDrawingText();opening=svg.index('>',svg.index('<svg'))+1;inner='<g transform="translate(50,125)">'+svg[opening:svg.rindex('</svg>')]+'</g>'
 render(e,frame(e,inner,'2D connectivity reference · highlighted functional groups · no measured geometry'))
 CHECKS.append({'identity':e['id'],'canonical_smiles':Chem.MolToSmiles(mol),'computed_formula':rdMolDescriptors.CalcMolFormula(mol),'atom_count':mol.GetNumAtoms(),'bond_count':mol.GetNumBonds(),'formal_charge':sum(a.GetFormalCharge() for a in mol.GetAtoms()),'isotope_2_hydrogens':sum(a.GetAtomicNum()==1 and a.GetIsotope()==2 for a in mol.GetAtoms())})
 return mol
# Exact retained source-neutral entries. The original assets remain immutable snapshots.
REUSE={'oa':'oleic-acid','ode':'1-octadecene','acetone':'acetone','toluene':'toluene','toluene-grade-unspecified':'toluene','topse':'topse','tbp':'tbp','compound-2':'oleic-acid'}
for mid,eid in REUSE.items():
 old=base[eid];e=identity(mid);snap(REG/'registry.json','registry.json') if not (O/'reference-snapshots/registry.json').exists() else None
 save('reference-snapshots/entry-'+eid+'.json',old)
 for key in ['svgPath','model2dPath','model3dPath']:
  if old.get(key):assert sha(REG/old[key])==old['assetHashes'][key];snap(REG/old[key],old[key])
 raw=read(REG/old['model2dPath']);smiles=old.get('provenance',{}).get('smiles') or raw.get('connectivitySmiles') or raw.get('smiles')
 if not smiles:
  rw=Chem.RWMol()
  for a in raw['atoms']:
   atom=Chem.Atom(a['element']);atom.SetFormalCharge(a.get('formalCharge',0));atom.SetIsotope(a.get('isotope',0));rw.AddAtom(atom)
  for b in raw['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
  mol=rw.GetMol();Chem.SanitizeMol(mol)
 else:mol=Chem.MolFromSmiles(smiles)
 e['pubchemCid']=old.get('pubchemCid');e['provenance'].update(reusedRegistryId=eid,originalEntrySha256=sha(O/'reference-snapshots'/('entry-'+eid+'.json')),identityBasis='Exact named molecular connectivity from retained qualified registry; source-specific material purity and role remain at the canonical slot.')
 e['caption']='Named '+e['name']+' molecular connectivity reference. The source reagent or stock may contain impurities; the drawing does not represent the complete mixture.'
 if mid=='compound-2':e['limitations'].append('Table 1 calls compound 2 oleic acid with R=C17H33; this reference expands that named identity, not an unknown new R group.')
 if mid=='topse':e['limitations'].append('The TOPSe molecule is distinct from the impurity-containing stock. Cached embedding-only 3D geometry is deliberately not promoted here.')
 model2d(e,mol,{'retained_registry_id':eid,'retained_model2d_sha256':old['assetHashes']['model2dPath'],'source_urls':old.get('sourceUrls',[])})
 QUAL.append({'canonical_material_id':mid,'reference_id':eid,'decision':'exact_named_connectivity_reused_in_new_source_scoped_2d','original_model2d_sha256':old['assetHashes']['model2dPath'],'model3d_reused':False})
# Source diagrams and unambiguous source chemical names support these reference graphs.
PH='c1ccccc1'
NEW={
'dpp':('[PH](c1ccccc1)c1ccccc1','C12H11P'), 'compound-7':('[PH](c1ccccc1)c1ccccc1','C12H11P'),
'dppse':('[PH](=[Se])(c1ccccc1)c1ccccc1','C12H11PSe'),
'tep':('CCP(CC)CC','C6H15P'), 'tipp':('CC(C)P(C(C)C)C(C)C','C9H21P'), 'dipp':('CC(C)[PH]C(C)C','C6H15P'),
'tpp':('P(c1ccccc1)(c1ccccc1)c1ccccc1','C18H15P'),
'tippse':('CC(C)P(=[Se])(C(C)C)C(C)C','C9H21PSe'), 'tepse':('CCP(=[Se])(CC)CC','C6H15PSe'), 'tppse':('P(=[Se])(c1ccccc1)(c1ccccc1)c1ccccc1','C18H15PSe'),
'dop':('CCCCCCCC[PH]CCCCCCCC','C16H35P'),'dbp':('CCCC[PH]CCCC','C8H19P'), 'dopo':('[PH](=O)(CCCCCCCC)CCCCCCCC','C16H35OP'),'dopse':('[PH](=[Se])(CCCCCCCC)CCCCCCCC','C16H35PSe'),
'tms':('C[Si](C)(C)C','C4H12Si'),'h3po4':('OP(=O)(O)O','H3O4P'),
'toluene-d8':('[2H]C([2H])([2H])c1c([2H])c([2H])c([2H])c([2H])c1[2H]','C7H8'),
'compound-3':('O=C(*)OP(c1ccccc1)c1ccccc1',None), 'compound-4':('[PH](=O)(c1ccccc1)c1ccccc1','C12H11OP'),
'compound-5':('O=C(*)OC(=O)*',None),'compound-8':('O=C(*)OP(=[Se])(c1ccccc1)c1ccccc1',None),
'compound-12':('P(c1ccccc1)(c1ccccc1)P(c1ccccc1)c1ccccc1','C24H20P2'),'compound-13':('OP(=O)(c1ccccc1)c1ccccc1','C12H11O2P')}
for mid,(smiles,formula) in NEW.items():
 e=identity(mid);e['caption']='2D reference connectivity from the source-named compound and source structural diagrams; the layout is generated locally and does not establish measured molecular geometry.'
 e['provenance'].update(connectivityBasis='Verified source name, Table 1, Scheme 1 and/or supporting-information reagent/impurity assignment; no external lookup.',connectivitySmiles=smiles)
 if mid in ['compound-3','compound-5','compound-8']:e['limitations'].append('R is the source abbreviation C17H33. The abbreviated graph does not invent a full-chain conformer, stereochemistry or atom coordinates for the R group.');e['depictionKind']='abbreviated_connectivity'
 if mid=='toluene-d8':e['limitations'].append('Eight hydrogen sites are explicitly deuterium. Isotope labels establish composition only, not a new measured geometry.')
 if mid in ['dppse','dopse','dopo','compound-4']:e['limitations'].append('The P–H functionality and terminal P=Se/P=O source representation are retained; no tautomer population or solution equilibrium is inferred.')
 mol=Chem.MolFromSmiles(smiles);assert mol is not None,mid;model2d(e,mol,{'doi':'10.1021/ja103805s','sourceMaterialId':mid,'sourceEvidence':slots[mid][0][2]['evidence'],'source_diagram_assets':['table-1','scheme-1'] if mid.startswith('compound-') or mid in ['dpp','dppse'] else ['figure-S1','figure-S2','figure-S3'] if mid in ['dop','dbp','dopo','dopse'] else []})
 if formula:assert rdMolDescriptors.CalcMolFormula(mol)==formula,(mid,rdMolDescriptors.CalcMolFormula(mol),formula)
 if mid=='toluene-d8':assert sum(a.GetAtomicNum()==1 and a.GetIsotope()==2 for a in mol.GetAtoms())==8
 if mid in ['dpp','compound-7','dppse','dop','dbp','dipp','dopo','dopse','compound-4']:assert sum(a.GetTotalNumHs() for a in mol.GetAtoms() if a.GetAtomicNum()==15)==1,mid
SYMBOL={
'cdo':('CdO','Cadmium oxide · bulk reagent','No oxide lattice or molecule assigned'),
'pbo':('PbO','Lead oxide · bulk reagent','No oxide polymorph or lattice assigned'),
'se':('Se','Elemental selenium shot','No allotrope or finite atomic structure assigned'),
'pb-metal':('Pb','Reported lead-metal context','No Pb lattice or particle geometry assigned'),
'pbse':('PbSe','Quantum-dot composition context','No sample-resolved atomic coordinates supplied'),
'cdse':('CdSe','Quantum-dot composition context','No sample-resolved atomic coordinates supplied'),
'cd-oleate':('Cd(oleate)2','Metal salt / precursor identity','Coordination, aggregation and solution species unreported'),
'pb-oleate':('Pb(oleate)2','Metal salt / precursor identity','Coordination, aggregation and solution species unreported'),
'top-tech':('TOP · technical grade','Named TOP component + phosphorus impurities','Commercial 90% label is not the measured impurity distribution'),
'top-strem':('TOP · Strem','Named TOP component + phosphorus impurities','Commercial 97% label is not the measured impurity distribution'),
'top-unspecified':('TOP · lot unspecified','Named TOP component; impurity composition unresolved','Do not assign a commercial lot or a purified molecular state'),
'unknown-p-impurities':('Unidentified P-containing species','No unique formula or connectivity','No unassigned NMR peak is converted into a chemical identity')}
for mid,(center,line,footer) in SYMBOL.items():
 e=identity(mid,kind='mixture' if mid.startswith('top-') or mid=='unknown-p-impurities' else 'ionic_identity' if mid.endswith('oleate') else 'material_identity');e['caption']=line+'. '+footer+'.';e['limitations'].append(footer+'.');symbols(e,[center,line,'Symbolic source identity; no invented geometry'],footer)
for mid in [k for k in slots if k.startswith('intermediate-')]:
 e=identity(mid,kind='author_hypothesis');e['caption']='Author-proposed intermediate from the source mechanism. It was not isolated and is not assigned a measured geometry.';e['limitations']+=['Source scheme connectivity is a mechanistic proposal, not proof of a stable solution species.','No atomistic model or optimized intermediate is supplied.'];symbols(e,['Proposed intermediate '+mid.split('-')[-1],e['formula'],'Author mechanism · unisolated species'],'Hypothesis only · inspect the original scheme for its proposed connectivity')
# N2 uses the previously independently qualified source-neutral bond identity.
e=identity('n2');old=base['norberg2004-nitrogen-reference'];snap(REG/old['model2dPath'],old['model2dPath']);e['caption']='Dinitrogen connectivity reference. Nitrogen roles and handling conditions remain specific to each Evans operation.';e['provenance'].update(reusedRegistryId=old['id'],referenceModel2dSha256=old['assetHashes']['model2dPath']);model2d(e,Chem.MolFromSmiles('N#N'),{'retained_registry_id':old['id'],'reference_sha256':old['assetHashes']['model2dPath']});QUAL.append({'canonical_material_id':'n2','decision':'qualified_N2_connectivity_only','rejected_geometry':'Old generic 1.460 Å N2 model is not used.','model3d_reused':False})
# Source molecular species 9: transform the reported fractional coordinates only.
e=identity('species9','Molecular species 9 · source crystal',kind='source_crystallographic_model');ci=read(B/'cif-source-inventory.json');scalar={s['tag']:s['token']['value'] for s in ci['scalars']}
num=lambda s:float(str(s).split('(')[0])
a,b,c=[num(scalar['_cell_length_'+k]) for k in 'abc'];al,be,ga=[math.radians(num(scalar['_cell_angle_'+k])) for k in ['alpha','beta','gamma']]
avec=(a,0,0);bvec=(b*math.cos(ga),b*math.sin(ga),0);cx=c*math.cos(be);cy=c*(math.cos(al)-math.cos(be)*math.cos(ga))/math.sin(ga);cvec=(cx,cy,math.sqrt(c*c-cx*cx-cy*cy))
rows=next(l['rows'] for l in ci['loops'] if '_atom_site_label' in l['tags']);atoms=[]
for i,row in enumerate(rows):
 d={k:v['value'] for k,v in row.items()};frac=[num(d['_atom_site_fract_'+k]) for k in 'xyz'];pos=[sum(frac[j]*[avec,bvec,cvec][j][k] for j in range(3)) for k in range(3)];atoms.append({'index':i,'element':d['_atom_site_type_symbol'],'label':d['_atom_site_label'],'x':pos[0],'y':pos[1],'z':pos[2],'fractional_coordinates':frac,'occupancy':num(d['_atom_site_occupancy']),'source_calc_flag':d['_atom_site_calc_flag'],'coordinate_basis':'calculated riding H in the source refinement' if d['_atom_site_type_symbol']=='H' else 'reported crystallographic refinement coordinate'})
index={x['label']:x['index'] for x in atoms};bonds=[];excluded=[];distances=[]
for row in next(l['rows'] for l in ci['loops'] if '_geom_bond_distance' in l['tags']):
 d={k:v['value'] for k,v in row.items()}
 if d['_geom_bond_site_symmetry_2']!='.':excluded.append(d);continue
 i,j=index[d['_geom_bond_atom_site_label_1']],index[d['_geom_bond_atom_site_label_2']];aa,bb=atoms[i],atoms[j];dist=math.sqrt(sum((aa[k]-bb[k])**2 for k in 'xyz'));reported=num(d['_geom_bond_distance']);raw=d['_geom_bond_distance'];su_match=re.search(r'\((\d+)\)',raw);su=int(su_match[1])*10**(-len(raw.split('(')[0].split('.')[-1])) if su_match else 0;tol=max(.001,3*su);assert abs(dist-reported)<=tol,(d,dist,tol)
 bonds.append({'a':i,'b':j,'order':1,'source_distance_raw':raw,'rendered_line_semantics':'Source geometry-table connection; order=1 is a single visual stick, not a chemical bond-order or coordination-valence assignment.'});distances.append({'labels':[aa['label'],bb['label']],'calculated_from_fractional':dist,'source_distance':reported,'source_standard_uncertainty':su,'absolute_difference':abs(dist-reported),'comparison_tolerance_angstrom':tol,'tolerance_basis':'Maximum of 0.001 A coordinate/printed precision tolerance and three source-reported distance standard uncertainties; no coordinate adjustment performed.'})
assert Counter(x['element'] for x in atoms)==Counter({'C':24,'H':20,'P':2,'Pb':1,'Se':4})
e['formula']='C24H20P2PbSe4';e['displayFormula']='Pb(Se2PPh2)2 · C24H20P2PbSe4';e['caption']='Source molecular species-9 single-crystal refinement. Coordinates are transformed from the supplied CIF; 20 hydrogens use the reported calculated riding model. This is not a PbSe or CdSe quantum dot.';e['provenance'].update(measuredCoordinates=True,coordinateSource='Source crystallographic refinement, including modelled H',sourceCifSha256=ci['source_sha256'],sourceCifInventorySha256=sha(B/'cif-source-inventory.json'),transformation='Reported triclinic fractional-to-Cartesian cell transform; no force-field optimization, bond inference or QD mapping.')
e['limitations']+=['Original nonstandard CIF prefix is preserved locally; this JSON is a documented coordinate transform, not a repaired original CIF.','The asymmetric-unit molecule only is shown. Symmetry-related intermolecular contacts are excluded from the molecular view and retained in the transform report.','Stick order is a visual connection only; source geometry distances do not specify chemical bond order.','No 3D model is assigned to unisolated intermediates, DPPSe crystals, CdSe QDs or PbSe QDs.'];e['model3dPath']='models/'+e['id']+'-3d.json';fg=[{'label':'Pb/Se/P coordination core','atomIndices':[x['index'] for x in atoms if x['element'] in ['Pb','Se','P']],'bondIndices':[i for i,z in enumerate(bonds) if atoms[z['a']]['element'] in ['Pb','Se','P'] and atoms[z['b']]['element'] in ['Pb','Se','P']]}];e['functionalGroups']=fg
save(e['model3dPath'],{'id':e['id'],'name':e['name'],'formula':e['formula'],'representation':'3d','has3D':True,'allowRotation':True,'coordinateUnits':'angstrom','indexConvention':'zero-based','modelType':'Source single-crystal refinement transformed from fractional coordinates','caption':e['caption'],'atoms':atoms,'bonds':bonds,'functionalGroups':fg,'notes':e['limitations'],'source':e['provenance']})
save('species9-transform-validation.json',{'source_cif_sha256':ci['source_sha256'],'cell_vectors_angstrom':[avec,bvec,cvec],'atom_count':51,'hydrogen_riding_count':20,'retained_intra_asymmetric_unit_connections':len(bonds),'excluded_symmetry_related_connections':excluded,'distance_checks':distances,'max_distance_error_angstrom':max(x['absolute_difference'] for x in distances),'source_model_role':'molecular species9 only','training_eligible':False})
# Project unchanged source coordinates into a static schematic preview.
xyz=np.array([[x[k] for k in 'xyz'] for x in atoms]);centered=xyz-xyz.mean(axis=0);_,_,axes=np.linalg.svd(centered,full_matrices=False);project=(centered@axes[:2].T).tolist();lo=[min(p[k] for p in project) for k in [0,1]];hi=[max(p[k] for p in project) for k in [0,1]];scale=min(870/(hi[0]-lo[0]),350/(hi[1]-lo[1]));pos=[(550+(p[0]-(hi[0]+lo[0])/2)*scale,325-(p[1]-(hi[1]+lo[1])/2)*scale) for p in project];body=''
for z in bonds:
 pa,pb=pos[z['a']],pos[z['b']];body+=f'<path d="M{pa[0]:.2f} {pa[1]:.2f}L{pb[0]:.2f} {pb[1]:.2f}" stroke="#7992a0" stroke-width="2.5"/>'
for x,p in zip(atoms,pos):
 color={'Pb':'#83599d','Se':'#b6a42b','P':'#cf8646','C':'#4e6776','H':'#dae6eb'}[x['element']];radius=9 if x['element']!='H' else 4;body+=f'<circle cx="{p[0]:.2f}" cy="{p[1]:.2f}" r="{radius}" fill="{color}" stroke="#fff"/>'
 if x['element'] not in ['C','H']:body+=tx(p[0],p[1]-13,x['label'],15)
render(e,frame(e,body,'Source crystal refinement · riding H retained · molecular species 9 only'))
by_mid={e['provenance']['sourceMaterialId']:e for e in ENTRIES};assert set(by_mid)==set(slots),(set(slots)-set(by_mid))
bindings={'schemaVersion':'1.0.0','source_id':'evans2010','status':'private_author_proposal_pending_independent_binding_audit','recordBindings':{},'bindingNotes':{},'binding_approved':False,'published':False,'eligible_training':False};slotmap=[];stockmap=[]
for rid,r in records.items():
 bindings['recordBindings'][rid]={};bindings['bindingNotes'][rid]={}
 for i,m in enumerate(r['materials']):
  entry=by_mid[m['id']];cap=entry['caption']+' Canonical role: '+m['role'].replace('_',' ')+'; stage: '+m['stage'].replace('_',' ')+'.';notes=m['notes']
  if m['quantities'].get('purity'):cap+=' Source commercial purity: '+str(m['quantities']['purity']['value'])+'%; not an analytical impurity distribution or product yield.'
  b={'record_id':rid,'material_id':m['id'],'json_pointer':f'/materials/{i}','canonical_record_sha256':sha(C/(rid+'.json')),'registry_id':entry['id'],'entry_sha256':hashlib.sha256(json.dumps(entry,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'canonical_identity':{k:deepcopy(m[k]) for k in ['name','formula','role','stage','quantities','evidence']},'viewOverrides':{'name':m['name'],'caption':cap,'limitations':list(dict.fromkeys(entry['limitations']+notes))},'binding_approved':False,'source_specific_join':'Same chemical depiction across slots does not establish the same physical specimen, lot or solution state.'}
  bindings['recordBindings'][rid][m['id']]=entry['id'];bindings['bindingNotes'][rid][m['id']]=b;slotmap.append(b)
 for j,s in enumerate(r['stocks']):
  comps=[]
  for k,cx in enumerate(s['components']):
   mi=next(i for i,m in enumerate(r['materials']) if m['id']==cx['material_id']);comps.append({'material_id':cx['material_id'],'registry_id':by_mid[cx['material_id']]['id'],'json_pointer':f'/stocks/{j}/components/{k}','material_json_pointer':f'/materials/{mi}','source_quantities':deepcopy(cx['quantities']),'binding_approved':False})
  stockmap.append({'record_id':rid,'stock_id':s['id'],'json_pointer':f'/stocks/{j}','canonical_record_sha256':sha(C/(rid+'.json')),'components':comps,'concentrations':deepcopy(s['concentrations']),'scope':s['scope'],'binding_approved':False,'display_limit':'Components are separate chemical references. No fixed solvation shell, coordination or molecular population is assigned.'})
save('registry-additions.json',{'schemaVersion':'1.0.0','source_id':'evans2010','entries':ENTRIES,'status':'private_author_proposal_pending_independent_audit'})
save('bindings-proposal.json',bindings);save('material-slot-map.json',slotmap);save('stock-component-map.json',stockmap);save('reuse-qualification.json',{'decisions':QUAL,'snapshots':snapshots,'no_network_lookup':True});save('chemical-graph-checks.json',CHECKS)
previews=[]
for e in ENTRIES:previews.append({'id':e['id'],'path':str(O/'previews'/(e['id']+'.png')),'sha256':sha(O/'previews'/(e['id']+'.png'))})
contacts=[]
for ci in range(0,len(previews),8):
 canvas=Image.new('RGB',(1320,1460),'#eaf1f5');d=ImageDraw.Draw(canvas)
 for j,p in enumerate(previews[ci:ci+8]):
  im=Image.open(p['path']);im.thumbnail((640,340));x=(j%2)*660+10;y=(j//2)*365+8;canvas.paste(im,(x,y));d.text((x+10,y+343),p['id'],fill='#15384b')
 path=O/'contacts'/f'contact-{ci//8+1}.png';canvas.save(path);contacts.append({'path':str(path),'sha256':sha(path),'entry_ids':[p['id'] for p in previews[ci:ci+8]]})
save('preview-manifest.json',{'previews':previews,'contact_sheets':contacts,'actual_visual_review':'pending'})
for p,h in inputs.items():assert sha(p)==h,p
save('generation-manifest.json',{'source_id':'evans2010','author':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'status':'generated_pending_actual_visual_check_and_independent_audit','counts':{'entries':len(ENTRIES),'model2d':sum(bool(e['model2dPath']) for e in ENTRIES),'model3d':sum(bool(e['model3dPath']) for e in ENTRIES),'material_slots':len(slotmap),'stock_slots':len(stockmap),'stock_components':sum(len(x['components']) for x in stockmap),'previews':len(previews)},'input_hashes':inputs,'no_source_canonical_reader_site_mutation':True,'no_downloads':True,'no_api_charges':True,'script_sha256':sha(__file__)})
print(json.dumps(read(O/'generation-manifest.json')['counts']))
