from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,math,copy
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;F=O.parent;P=F/'visuals/molecules';V=F/'visuals/molecules-correction-v2';M=F.parents[4]
sys.path[:0]=[str(M/'research-assets/rdkit-runtime'),str(M/'research-assets/corpus-20260917/runtime')]
from PIL import Image,ImageDraw,ImageFont
import pymupdf
J=lambda p:json.loads(Path(p).read_text('utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old_audit=J(O/'independent-audit-v1.json');bound=dict(old_audit['bound_files']);checks=[];diffs={}
def ck(n,v,d=None):checks.append(dict(check=n,passed=bool(v),detail=d))
def bind(p):p=Path(p);bound[str(p)]=sha(p);return p
def differences(a,b,p=''):
 if type(a)!=type(b):return [p]
 if isinstance(a,dict):
  out=[]
  for k in sorted(set(a)|set(b)):
   out += [p+'/'+k] if k not in a or k not in b else differences(a[k],b[k],p+'/'+k)
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return[p]
  return [z for i,(x,y) in enumerate(zip(a,b)) for z in differences(x,y,p+'/'+str(i))]
 return [] if a==b else [p]
for p,h in old_audit['bound_files'].items():ck('Original audit-bound file unchanged '+p,sha(p)==h)
base=J(P/'package-freeze.json');freeze=J(bind(V/'package-freeze.json'))
ck('Exact correction freeze',sha(V/'package-freeze.json')=='603e6365c8da98bcaa5cf14689245f69ddd43bae5f096e7ff7c5da4d89d5cb6c')
for rel,h in freeze['bound_files'].items():ck('Correction hash '+rel,sha(bind(V/rel))==h)
for rel,h in base['bound_files'].items():ck('All 198 original files preserved '+rel,sha(P/rel)==h)
mapping=J(V/'effective-file-map.json')['overrides'];ck('13 effective overrides',len(mapping)==13)
def eff(rel):return Path(mapping[rel]['path']) if rel in mapping else P/rel
for rel,item in mapping.items():
 ck('Effective mapping '+rel,sha(item['path'])==item['sha256'] and Path(item['path']).resolve()==(V/rel).resolve())
 if rel.endswith('.json'):diffs[rel]=differences(J(P/rel),J(item['path']))
reference=J(V/'reference-snapshots/gu2004-nitrogen-reference-3d.json')
new_models=[]
for mid in ['nitrogen','liquid-nitrogen']:
 rel=f'models/friedfeld2019-{mid}-3d.json';a=J(P/rel);b=J(eff(rel));new_models.append((mid,b))
 ck(mid+' exact qualified arrays',b['atoms']==reference['atoms'] and b['bonds']==reference['bonds'] and b['functionalGroups']==reference['functionalGroups'])
 ck(mid+' exact reference hash',b['source']['retained_reference_model_sha256']==sha(V/'reference-snapshots/gu2004-nitrogen-reference-3d.json'))
 ck(mid+' 1.09768 angstrom',abs(math.dist([b['atoms'][0][k] for k in 'xyz'],[b['atoms'][1][k] for k in 'xyz'])-1.09768)<1e-12)
 ck(mid+' neutral N2 graph',len(b['atoms'])==2 and all(x['element']=='N' and x['formalCharge']==0 and x['isotope']==0 for x in b['atoms']) and b['bonds'][0]['order']==3)
 ck(mid+' unchanged identity',[b[k] for k in ['id','name','formula','sourceFormula']]==[a[k] for k in ['id','name','formula','sourceFormula']])
 ck(mid+' new computed/reference labels',b['modelType']=='Reference-distance-derived diatomic geometry' and b['coordinateUnits']=='angstrom' and 'not measured' in b['sourceType'] and 'MMFF' not in json.dumps(b))
 ck(mid+' current scope',('gas identity' if mid=='nitrogen' else 'coolant identity') in b['caption'])
 ck(mid+' triple-bond group',[g['atomIndices'] for g in b['functionalGroups']]==[[0,1]] and b['functionalGroups'][0]['bondIndices']==[0])
for mid in ['acetonitrile','chloroform-d','diethyl-ether','dry-ice','acetone']:
 rel=f'models/friedfeld2019-{mid}-3d.json';a=J(P/rel);b=J(eff(rel))
 ck(mid+' geometry/groups/identity invariant',all(a[k]==b[k] for k in ['atoms','bonds','functionalGroups','formula','id','name','caption']))
 ck(mid+' metadata only',all(x.split('/')[1] in {'source','notes','historicalReuseProvenance'} for x in diffs[rel]))
 hist=b['historicalReuseProvenance'];ck(mid+' historical source and notes retained',hist['previous_source_field']==a['source'] and hist['previous_context_notes']==a.get('notes',[]) and hist['retained_model_sha256']==sha(P/rel))
 current={k:v for k,v in b.items() if k not in ['historicalReuseProvenance','referenceQualification']}
 ck(mid+' stale notes removed',not any(x in json.dumps(current).lower() for x in ['silicon ligand','electrospray','pyridine dispersion','2e proton','decanoyl ester','cm970189m','cm9503137','jp011815c']))
for dim in ['2d','3d']:
 rel=f'models/friedfeld2019-benzene-d6-{dim}.json';a=J(P/rel);b=J(eff(rel))
 ck(dim+' benzene-D unchanged graph/geometry',all(a[k]==b[k] for k in ['atoms','bonds','formula','functionalGroups']))
 ck(dim+' parent CID explicit',b['source']['pubchem_cid'] is None and b['source']['parent_connectivity_pubchem_cid']==241 and 'primary_reference' not in b['source'] and 'source' in b['source']['isotope_identity'].lower())
 ck(dim+' benzene-D source-only delta',all(x.startswith('/source/') for x in diffs[rel]))
regold=J(P/'registry-additions.json');reg=J(eff('registry-additions.json'))
for a,b in zip(regold['entries'],reg['entries']):
 mid=a['provenance']['sourceMaterialId'];delta=differences(a,b)
 ck(mid+' registry bounded deltas',all(x.startswith('/assetHashes/') or (mid=='benzene-d6' and x in ['/caption','/limitations']) for x in delta))
 for k,h in b['assetHashes'].items():ck(mid+' effective registry asset '+k,sha(eff(b[k]))==h)
 ck(mid+' binding/training pending',b['binding_approved'] is False and b['eligible_training'] is False)
qualold=J(P/'reference-qualification.json');qual=J(eff('reference-qualification.json'))
for a,b in zip(qualold['models'],qual['models']):
 mid=a['source_material_id'];delta=differences(a,b)
 ck(mid+' qualification-only delta',not delta or (mid in ['nitrogen','liquid-nitrogen','benzene-d6'] and all(x.startswith('/provenance/') for x in delta)))
stocksold=J(P/'source-stock-reference-proposal.json');stocks=J(eff('source-stock-reference-proposal.json'))
ck('All five exact source stock payloads and component maps preserved',all({k:v for k,v in a.items() if k!='sha256'}=={k:v for k,v in b.items() if k!='sha256'} for a,b in zip(stocksold['stocks'],stocks['stocks'])))
ck('Only selected stock hash changed',differences(stocksold,stocks)==['/stocks/2/sha256'])
for s in stocks['stocks']:ck(s['stock_id']+' effective stock hash',sha(eff(s['svg_path']))==s['sha256'])
svg=eff('stock-svg/friedfeld2019-indium-myristate-additive.svg');text=svg.read_text('utf8')
ck('Readable formal stock components','In3+' in text and '3 ×' in text and 'CH3(CH2)12COO' in text and 'no In–O coordination' in text and 'not reported' in text)
doc=pymupdf.open(stream=svg.read_bytes(),filetype='svg');pix=doc[0].get_pixmap(alpha=False);im=Image.open(V/'previews/indium-myristate-stock.png').convert('RGB')
ck('Revised stock preview pixel identity',im.size==(pix.width,pix.height) and im.tobytes()==pix.samples);doc.close()
for c in J(V/'correction-history.json')['changes']:ck('History exact old and new '+c['path'],sha(P/c['path'])==c['old_sha256'] and sha(eff(c['path']))==c['new_sha256'])
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22);im=Image.new('RGB',(1100,400),'white');dr=ImageDraw.Draw(im)
for i,(mid,m) in enumerate(new_models):
 y=70+i*180;dr.text((30,y-45),mid+' : NIST-derived N2 reference, 1.09768 Å',font=font,fill='#183e51')
 for z in [-4,0,4]:dr.line((370,y+z,700,y+z),fill='#3c62a5',width=2)
 for x in [370,700]:dr.ellipse((x-12,y-12,x+12,y+12),fill='#3c62a5');dr.text((x-9,y+18),'N',font=font,fill='#183e51')
 dr.text((30,y+50),'Arbitrary orientation; no source gas or liquid atomic structure.',font=font,fill='#183e51')
im.save(O/'corrected-nitrogen-coordinate-preview.png')
out=dict(author='/root',auditor='/root/backlog_eta',at=datetime.now(timezone.utc).isoformat(),checks=checks,passed=sum(x['passed'] for x in checks),failed=[x for x in checks if not x['passed']],deltas=diffs,bound_files=bound)
(O/'bounded-overlay-checks-v2.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'checks':len(checks),'passed':out['passed'],'failed':out['failed'],'bound_files':len(bound)}))
