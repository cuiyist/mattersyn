"""Persisted author verification of generated output, without executing generators."""
from pathlib import Path
import json,hashlib,sys,math
O=Path(__file__).resolve().parent;J=O.parents[1];M=J.parents[4]
sys.path[:0]=[str(M/'research-assets/rdkit-runtime'),str(M/'research-assets/corpus-20260917/runtime')]
from rdkit import Chem,rdBase
from rdkit.Chem import rdMolDescriptors
from PIL import Image,ImageDraw
import pymupdf
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(p,v):(O/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
def pointer(r,p):
 for k in p.strip('/').split('/'):r=r[int(k)] if isinstance(r,list) else r[k.replace('~1','/').replace('~0','~')]
 return r
def molmodel(d,coords=False):
 rw=Chem.RWMol()
 for a in d['atoms']:
  x=Chem.Atom(a['element']);x.SetFormalCharge(a.get('formalCharge',0));x.SetIsotope(a.get('isotope',0))
  if 'implicitHydrogenCount' in a:x.SetNoImplicit(True);x.SetNumExplicitHs(a['implicitHydrogenCount'])
  rw.AddAtom(x)
 for b in d['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
 m=rw.GetMol();Chem.SanitizeMol(m)
 if coords:
  c=Chem.Conformer(len(d['atoms']));c.Set3D(True)
  for i,a in enumerate(d['atoms']):c.SetAtomPosition(i,(a['x'],a['y'],a['z']))
  m.AddConformer(c)
 return m
inp=read(O/'input-bindings.json');bound={}
for k,v in inp.items():
 if isinstance(v,dict) and 'path' in v and 'sha256' in v:ck('input '+k,sha(v['path'])==v['sha256']);bound[v['path']]=v['sha256']
for x in inp['snapshots']:ck('snapshot '+x['snapshot'],sha(x['snapshot'])==x['sha256']);bound[x['snapshot']]=x['sha256']
records={}
for p,h in inp['canonical_records'].items():ck('record hash '+p,sha(p)==h);r=read(p);records[r['record_id']]=r;bound[p]=h
entries=read(O/'registry-additions.json')['entries'];byid={x['id']:x for x in entries};byMID={x['provenance']['sourceMaterialId']:x for x in entries};quals={x['material_id']:x for x in read(O/'reference-qualification.json')['references']};old={x['id']:x for x in read(O/'reference-snapshots/registry-base.json')['entries']}
patterns={'Formamidinium resonance group':'[NH2+]=[CH][NH2]','Acetate carboxylate':'[CX3](=[OX1])[O-]','Carboxylic acid':'C(=O)[OH]','Cis reference alkene':'[C]=[C]','Primary amine':'[NX3;H2;+0]','Terminal alkene':'[CH2]=[CH]','Aromatic ring':'c1ccccc1','Nitrile':'C#N','Dinitrogen triple bond':'N#N'}
assets=[]
for e in entries:
 mid=e['provenance']['sourceMaterialId'];ck('Closed entry gates '+mid,e['binding_approved'] is False and e['published'] is False and e['eligible_training'] is False)
 for k in ['svgPath','model2dPath','model3dPath']:
  if not e[k]:continue
  p=O/e[k];ck('asset exact '+str(p),sha(p)==e['assetHashes'][k]);assets.append({'path':str(p),'relative_path':e[k],'public_path':'assets/chemical-registry/'+e[k],'sha256':sha(p),'kind':'source_qualified_reference','whole_source_page':False})
  if k=='svgPath':continue
  d=read(p);mol=molmodel(d);target=Chem.MolFromSmiles(quals[mid]['reference_smiles'])
  ck('formula '+p.name,rdMolDescriptors.CalcMolFormula(mol)==quals[mid]['formula']);ck('connectivity '+p.name,Chem.MolToSmiles(Chem.RemoveHs(mol),isomericSmiles=False)==Chem.MolToSmiles(target,isomericSmiles=False))
  ck('charge '+p.name,sum(x.GetFormalCharge() for x in mol.GetAtoms())==quals[mid]['net_charge']);ck('fragments '+p.name,len(Chem.GetMolFrags(mol))==quals[mid]['fragment_count'])
  ck('model gate '+p.name,d['eligible_training'] is False)
  for i,a in enumerate(d['atoms']):
   ck('atom finite/index '+p.name+str(i),all(math.isfinite(a[x]) for x in ['x','y','z']) and a.get('index',i)==i)
  for i,b in enumerate(d['bonds']):
   ck('bond indices/order '+p.name+str(i),0<=b['a']<len(d['atoms']) and 0<=b['b']<len(d['atoms']) and b['a']!=b['b'] and b['order'] in [1,1.5,2,3])
  for g in d['functionalGroups']:
   valid={tuple(sorted(t)) for t in mol.GetSubstructMatches(Chem.MolFromSmarts(patterns[g['label']]))}
   ck('group chemistry '+p.name+g['label'],tuple(g['atomIndices']) in valid)
   ck('group bonds '+p.name+g['label'],g['bondIndices']==[b.GetIdx() for b in mol.GetBonds() if b.GetBeginAtomIdx() in g['atomIndices'] and b.GetEndAtomIdx() in g['atomIndices']])
  oid=quals[mid]['provenance'].get('retainedRegistryId')
  if oid:
   prior=read(O/'reference-snapshots'/old[oid][k]);ck('retained arrays '+p.name,d['atoms']==prior['atoms'] and d['bonds']==prior['bonds'])
  if k=='model3dPath':
   ck('3D only qualified reference '+mid,mid!='formamidine-acetate' and d['coordinateUnits']=='angstrom')
   for i,b in enumerate(d['bonds']):
    a,c=d['atoms'][b['a']],d['atoms'][b['b']];distance=math.sqrt(sum((a[x]-c[x])**2 for x in ['x','y','z']));ck('finite plausible bond '+mid+str(i),.65<distance<2.0)
   if mid in ['oa','oam']:
    stereo=molmodel(d,True);Chem.AssignStereochemistryFrom3D(stereo);ck('retained Z geometry '+mid,Chem.MolToSmiles(Chem.RemoveHs(stereo))==Chem.MolToSmiles(target))
   if mid=='nitrogen':ck('NIST distance/isotopologue',d['referenceDistanceAngstrom']==1.09768 and d['referenceIsotopologue']=='14N2' and abs(math.dist([d['atoms'][0][x] for x in ['x','y','z']],[d['atoms'][1][x] for x in ['x','y','z']])-1.09768)<1e-10)
 if mid not in quals:ck('symbol remains without atoms '+mid,e['model2dPath'] is None and e['model3dPath'] is None and not e['functionalGroups'])
 ck('registry model group synchronization '+mid,not e['model2dPath'] or e['functionalGroups']==read(O/e['model2dPath'])['functionalGroups'])
bindings=read(O/'bindings-proposal.json');slots=read(O/'material-slot-map.json')['slots'];seen=set();quantity_count=0
def qcheck(q):
 global quantity_count
 quantity_count+=1;ck('typed pointer '+q['record_id']+q['json_pointer'],pointer(records[q['record_id']],q['json_pointer'])==q['quantity'])
for n in slots:
 rid,mid=n['record_id'],n['material_id'];r=records[rid];seen.add((rid,mid));ck('exact slot '+rid+mid,pointer(r,n['json_pointer'])==n['canonical_identity']);ck('binding pair '+rid+mid,bindings['recordBindings'][rid][mid]==n['registry_id'] and bindings['bindingNotes'][rid][mid]==n);ck('entry digest '+mid,jsha(byid[n['registry_id']])==n['entry_sha256'])
 for q in n['quantity_links']+n['grade_context_links']:qcheck(q)
 for opt in n['condition_option_links']:
  ck('paired complete option '+opt['condition_option_id'],next(x for x in r['condition_options'] if x['id']==opt['condition_option_id'])==opt['condition_option']);qcheck(opt['quantity_link'])
 ck('private binding '+rid+mid,n['binding_approved'] is False)
ck('exact full slot universe',seen=={(rid,m['id']) for rid,r in records.items() for m in r['materials']} and len(slots)==26)
stocks=read(O/'stock-component-map.json')['stocks'];contexts=read(O/'solution-components-proposal.json')['contexts'];ck('stock instances',len(stocks)==5 and len(contexts)==5 and sum(len(s['components']) for s in stocks)==12)
for s,cx in zip(stocks,contexts):
 rid=s['record_id'];r=records[rid];ck('stock payload exact '+rid+s['stock_id'],pointer(r,s['json_pointer'])==s['canonical_stock']);ck('empty source concentrations',s['concentrations']=={});ck('context identity',cx['record_id']==rid and [c['material_id'] for c in cx['components']]==[c['material_id'] for c in s['components']])
 for c in s['components']:
  ck('component exact',pointer(r,c['json_pointer'])['quantities']==c['source_quantities']);ck('component material join',pointer(r,c['material_json_pointer'])['id']==c['material_id'])
  for q in c['quantity_links']:qcheck(q)
 for q in s['solution_quantity_links']:qcheck(q);ck('aliquot remains .51 mL',q['quantity']['value']==.51 and q['quantity']['unit']=='mL')
 if s['stock_id'].startswith('wash'):
  ck('wash parts stay relative',all(q['quantity']['unit']=='volume_parts' for c in s['components'] for q in c['quantity_links']))
ck('exact source grades',[next(n for n in slots if n['material_id']==m)['grade_context_links'][0]['quantity']['raw_text'] for m in ['formamidine-acetate','oa','oam','ode','toluene','acetonitrile','hexane']]==['99','99','70','>90','99.8','99.8','95'])
for a in read(O/'stock-illustration-proposal.json')['formulations']:
 p=O/a['path'];ck('stock SVG hash',sha(p)==a['sha256']);assets.append({'path':str(p),'relative_path':a['path'],'public_path':'assets/chemical-registry/'+a['path'],'sha256':sha(p),'kind':'formulation_illustration','whole_source_page':False})
ck('exact public asset count',len(assets)==30 and len({x['public_path'] for x in assets})==30)
save('public-assets-proposal.json',{'schema':'mattersyn-public-assets/1','status':'unapproved_author_candidates','assets':assets,'exclusions':['Original PDFs, SI, full pages, text, private reference snapshots and author previews.'],'published':False})
save('effective-public-assets.json',{'status':'unapproved_author_candidates','base_package':'current initial proposal','assets':assets})
save('effective-file-map.json',{'status':'unapproved_author_candidates','effective_files':{n:{'path':str(O/n),'sha256':sha(O/n)} for n in ['registry-additions.json','bindings-proposal.json','material-slot-map.json','stock-component-map.json','solution-components-proposal.json','stock-illustration-proposal.json','input-bindings.json']}})
# Re-render actual SVGs and compare decoded pixels; stock and reference previews must be fresh.
for directory,preview in [('svg','previews'),('stock-svg','stock-previews')]:
 for p in (O/directory).glob('*.svg'):
  d=pymupdf.open(stream=p.read_bytes(),filetype='svg');pix=d[0].get_pixmap(alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);actual=Image.open(O/preview/(p.stem+'.png')).convert('RGB');ck('preview replay '+p.name,im.size==actual.size and im.tobytes()==actual.tobytes())
panels=[p for d in ['previews','conformer-previews','stock-previews'] for p in sorted((O/d).glob('*.png'))];contactmap=[]
for start in range(0,len(panels),4):
 canvas=Image.new('RGB',(1600,1320),'#e4ecf0');draw=ImageDraw.Draw(canvas)
 for i,p in enumerate(panels[start:start+4]):
  im=Image.open(p);im.thumbnail((790,610));x=(i%2)*800+(800-im.width)//2;y=(i//2)*660+30;canvas.paste(im,(x,y));draw.text(((i%2)*800+10,(i//2)*660+8),str(p.relative_to(O)),fill='black')
 cp=O/'contacts'/f'contact-{start//4+1:02}.png';canvas.save(cp);contactmap.append({'path':str(cp),'sha256':sha(cp),'panels':[{'path':str(p),'sha256':sha(p)} for p in panels[start:start+4]]})
save('contact-index.json',{'panel_count':len(panels),'contacts':contactmap})
save('author-validation.json',{'status':'passed_author_checks','independent_approval':False,'rdkit_version':rdBase.rdkitVersion,'check_count':len(checks),'quantity_reference_count':quantity_count,'counts':{'identities':13,'material_slots':26,'stock_instances':5,'unique_stock_formulations':4,'stock_components':12,'public_assets':30,'static_panels':len(panels)},'bound_inputs':bound,'checks':checks})
print(json.dumps({'status':'passed_author_checks','checks':len(checks),'quantity_links':quantity_count,'panels':len(panels),'assets':len(assets)}))
