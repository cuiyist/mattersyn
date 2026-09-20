"""Preserved molecular correction overlay; original author freeze untouched."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib,html,textwrap,math,sys
O=Path(__file__).resolve().parent;V=O.parent/'molecules';F=O.parents[1];M=F.parents[4]
sys.path[:0]=[str(M/'research-assets/rdkit-runtime'),str(M/'research-assets/corpus-20260917/runtime')]
import pymupdf
from rdkit import Chem
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D
assert not (O/'package-freeze.json').exists()
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(rel,x):p=O/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n','utf8')
base=read(V/'package-freeze.json');assert sha(V/'package-freeze.json')=='7c1a864dbdf6b3177d2aa907b4f3c5893232b0c7d213ab18312d12655d4f4c0f'
for rel,digest in base['bound_files'].items():assert sha(V/rel)==digest,rel
reg=read(V/'registry-additions.json');entries={e['provenance']['sourceMaterialId']:e for e in reg['entries']}
fixed={};changes=[]
reference=M/'recipe-atlas/dist/assets/chemical-registry/models/gu2004-nitrogen-reference-3d.json';n=read(reference)
save('reference-snapshots/gu2004-nitrogen-reference-3d.json',n)
a,b=n['atoms'];distance=math.dist([a[k] for k in ('x','y','z')],[b[k] for k in ('x','y','z')]);assert abs(distance-1.09768)<1e-12
for mid in ['nitrogen','liquid-nitrogen']:
 rel=entries[mid]['model3dPath'];old=read(V/rel);new=deepcopy(n)
 for k in ['id','name','sourceFormula','caption']:new[k]=old.get(k,entries[mid].get(k))
 new['caption']=entries[mid]['limitations'][1]+' NIST 14N2 internuclear distance 1.09768 Å; arbitrary orientation, not a measured source-gas or liquid structure.'
 new['notes']=entries[mid]['limitations']+['The source does not specify an isotopic assay.']
 new['sourceType']='Coordinates constructed from a published diatomic reference distance; not measured source coordinates'
 new['source']={'reference':'https://webbook.nist.gov/cgi/cbook.cgi?ID=C7727379&Mask=1000','reference_distance_angstrom':1.09768,'reference_isotopologue':'14N2','retained_reference_model_sha256':sha(reference)}
 new['historicalReuseProvenance']={'replaced_model_sha256':sha(V/rel),'reason':'Prior 1.460 Å cached geometry is inappropriate for N2 triple bond.'}
 new['eligible_training']=False;save(rel,new);fixed[rel]=str(O/rel)
 changes.append({'path':rel,'kind':'replace unsuitable N2 geometry with qualified reference distance','old_sha256':sha(V/rel),'new_sha256':sha(O/rel)})
for mid in ['acetonitrile','chloroform-d','diethyl-ether','dry-ice','acetone']:
 rel=entries[mid]['model3dPath'];old=read(V/rel);new=deepcopy(old)
 new['historicalReuseProvenance']={'retained_model_sha256':sha(V/rel),'previous_source_field':old.get('source'),'previous_context_notes':old.get('notes',[]),'scope':'Historical asset reuse only; previous paper conditions do not apply to this source.'}
 if mid!='acetone':
  new['source']={'kind':'Computed chemical reference','connectivity':old.get('connectivitySmiles'),'software':old.get('computedBy'),'method':old.get('method',old.get('conformerGeneration')),'coordinate_source':'Retained locally computed reference coordinates; not measured in Friedfeld2019 or the historical reuse paper.'}
 new['notes']=entries[mid]['limitations']
 assert new['atoms']==old['atoms'] and new['bonds']==old['bonds'] and new['functionalGroups']==old['functionalGroups']
 save(rel,new);fixed[rel]=str(O/rel);changes.append({'path':rel,'kind':'separate historical context from current chemical/computational reference','old_sha256':sha(V/rel),'new_sha256':sha(O/rel)})
qual=read(V/'reference-qualification.json')
for q in qual['models']:
 if q['source_material_id'] in ['nitrogen','liquid-nitrogen']:
  q['provenance']['historical_cached_reference']='The original nitrogen registry cache supplied an unsuitable 1.460 Å model; it is superseded by this geometry overlay.'
  q['provenance']['qualified_geometry_reference']={'url':'https://webbook.nist.gov/cgi/cbook.cgi?ID=C7727379&Mask=1000','reference_distance_angstrom':1.09768,'model_sha256':sha(reference)}
 if q['source_material_id']=='benzene-d6':
  q['provenance']['pubchem_cid']=None;q['provenance'].pop('primary_reference',None)
  q['provenance'].update(parent_connectivity_pubchem_cid=241,parent_connectivity_reference='https://pubchem.ncbi.nlm.nih.gov/compound/241',isotope_identity='Six deuterium substitutions specified by the source; CID241 is unlabeled benzene, not the isotopologue identity.')
save('reference-qualification.json',qual);fixed['reference-qualification.json']=str(O/'reference-qualification.json')
for suffix in ['2d','3d']:
 rel=f'models/friedfeld2019-benzene-d6-{suffix}.json';old=read(V/rel);new=deepcopy(old)
 new['source']['pubchem_cid']=None;new['source'].pop('primary_reference',None)
 new['source'].update(parent_connectivity_pubchem_cid=241,parent_connectivity_reference='https://pubchem.ncbi.nlm.nih.gov/compound/241',isotope_identity='Source-defined six-D substitution; CID241 supplies parent connectivity only.')
 assert old['atoms']==new['atoms'] and old['bonds']==new['bonds'];save(rel,new);fixed[rel]=str(O/rel)
 changes.append({'path':rel,'kind':'qualify benzene CID241 as parent connectivity only','old_sha256':sha(V/rel),'new_sha256':sha(O/rel)})
entries['benzene-d6']['limitations'].append('PubChem CID241 is the unlabeled benzene parent; six-D isotope substitution comes from the source identity.')
entries['benzene-d6']['caption']+=' PubChem CID241 supplies parent connectivity only; six deuteriums are source-defined.'
for e in reg['entries']:
 for k in ['model2dPath','model3dPath']:
  if e.get(k) in fixed:e['assetHashes'][k]=sha(O/e[k])
save('registry-additions.json',reg);fixed['registry-additions.json']=str(O/'registry-additions.json')

# Reuse the audited identity card's large 3x-ligand drawing in the stock context.
# Source stock numbers and source component definitions are preserved exactly.
stocks=read(V/'source-stock-reference-proposal.json');s=next(x for x in stocks['stocks'] if x['stock_id']=='indium-myristate-additive')
def esc(x):return html.escape(str(x),quote=True)
def tx(x,y,t,size=20,anchor='start'):return f'<text x="{x}" y="{y}" font-size="{size}" font-family="Arial,sans-serif" fill="#294658" text-anchor="{anchor}">{esc(t)}</text>'
def wrap(t,x,y,width=95,size=20):return ''.join(tx(x,y+28*i,l,size) for i,l in enumerate(textwrap.wrap(t,width)))
body=tx(40,52,'Indium myristate additive in ODE',28)+tx(40,103,'SOLUTE · Formal formula components',18)
body+=tx(105,250,'In3+',38,'middle')+tx(200,250,'+',28,'middle')+tx(285,250,'3 ×',30,'middle')
# The 30-graph source inventory retains all three explicit ligand components.
# The readable visual gives one enlarged reference ligand with its multiplicity.
body+=tx(710,160,'Myristate: CH3(CH2)12COO−',25,'middle')
salt=Chem.MolFromSmiles(read(V/entries['indium-myristate']['model2dPath'])['source']['reference_smiles'])
ligand=next(f for f in Chem.GetMolFrags(salt,asMols=True) if f.GetNumAtoms()>1)
assert sum(a.GetSymbol()=='C' for a in ligand.GetAtoms())==14
rdDepictor.Compute2DCoords(ligand);draw=rdMolDraw2D.MolDraw2DSVG(700,185);draw.drawOptions().padding=.12;draw.drawOptions().fixedFontSize=27
rdMolDraw2D.PrepareAndDrawMolecule(draw,ligand);draw.FinishDrawing();part=draw.GetDrawingText();part=part[part.index('>',part.index('<svg'))+1:part.rindex('</svg>')]
body+='<g transform="translate(345,166)">'+part+'</g>'
body+=wrap('Formal In3+ + three myristate anions; no In–O coordination or dissolved complex is assigned.',40,352,92)
body+=tx(40,462,'SOLVENT · 1-Octadecene · C18H36',23)
# Embed the unchanged reviewed ODE connectivity SVG rather than redraw its bonds.
ode=(V/entries['ode']['svgPath']).read_text('utf8');start=ode.index('<g transform="translate(50,130)">');end=ode.index('</g>',start)+4
body+='<g transform="translate(0,435) scale(1,.75)">'+ode[start:end]+'</g>'
body+=tx(40,800,'Stock concentration and preparation amount: not reported.',23)
body+=wrap('Reaction equivalents belong to the selected comparison; they are not a reported stock concentration. Solute and solvent views do not establish solution speciation.',40,855,91,20)
svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="980"><title>Indium myristate stock components</title><rect width="1100" height="980" fill="white"/>{body}</svg>'
rel=s['svg_path'];p=O/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(svg,'utf8');fixed[rel]=str(p)
old_hash=s['sha256'];s['sha256']=sha(p);save('source-stock-reference-proposal.json',stocks);fixed['source-stock-reference-proposal.json']=str(O/'source-stock-reference-proposal.json')
changes.append({'path':rel,'kind':'enlarge formal indium ion and threefold ligand display without source-stock changes','old_sha256':old_hash,'new_sha256':sha(p)})
doc=pymupdf.open(stream=svg.encode(),filetype='svg');(O/'previews').mkdir(exist_ok=True);doc[0].get_pixmap(alpha=False).save(str(O/'previews/indium-myristate-stock.png'));doc.close()
save('correction-history.json',{'author':'/root','base_freeze_sha256':sha(V/'package-freeze.json'),'changes':changes,'source_quantities_changed':False,'source_stock_objects_unchanged':all(a['source_stock']==b['source_stock'] for a,b in zip(read(V/'source-stock-reference-proposal.json')['stocks'],stocks['stocks'])),'eligible_training':False,'independent_audit':'pending'})
save('effective-file-map.json',{'base_directory':str(V),'overrides':{rel:{'path':path,'sha256':sha(Path(path))} for rel,path in fixed.items()},'base_freeze_sha256':sha(V/'package-freeze.json')})
print(json.dumps({'overridden_files':len(fixed),'reference_distance_angstrom':distance,'original_freeze_preserved':all(sha(V/p)==h for p,h in base['bound_files'].items()),'freeze_status':'not yet frozen; inspect revised stock before freeze'}))
