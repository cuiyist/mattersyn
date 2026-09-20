"""Independent structural/path validation and actual SVG render contact sheets."""
import sys,json,re,hashlib,math,xml.etree.ElementTree as ET
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parents[1]/'corpus-20260917/runtime'))
import pymupdf
from PIL import Image,ImageDraw,ImageFont
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
registry=read(R/'registry.json');bindings=read(R/'bindings.json');entries={x['id']:x for x in registry['entries']}
errors=[];checks=0
def check(ok,msg):
 global checks
 checks+=1
 if not ok:errors.append(msg)
check(len(entries)==len(registry['entries']),'Unique registry IDs')
for e in entries.values():
 check(bool(e['sourceUrls']),e['id']+' has source URL')
 for k in ['svgPath','model2dPath','model3dPath']:
  if not e.get(k):continue
  p=(R/e[k]).resolve();check(p.is_relative_to(R) and p.exists(),e['id']+' valid '+k)
  check(sha(p)==e['assetHashes'][k],e['id']+' asset hash '+k)
 svg=(R/e['svgPath']).read_text(encoding='utf-8');xml=ET.fromstring(svg)
 check(not re.search(r'<script|onload=|javascript:|(?:href|src)="https?://',svg,re.I),e['id']+' passive self-contained SVG')
 check(xml.get('viewBox')=='0 0 840 360' or xml.get('width')=='840px',e['id']+' declared diagram dimensions')
 if e['depictionKind']!='molecule':check(e['model3dPath'] is None,e['id']+' no invented 3D for nondiscrete identity')
 for key in ['model2dPath','model3dPath']:
  if not e.get(key):continue
  m=read(R/e[key]);aa=m['atoms'];bb=m['bonds'];check(m['id']==e['id'],e['id']+' model ID')
  check(bool(aa) and all(all(math.isfinite(a[x]) for x in ['x','y','z']) for a in aa),e['id']+' finite atoms '+key)
  check(all(0<=b['a']<len(aa) and 0<=b['b']<len(aa) and b['a']!=b['b'] and b['order'] in [1,1.5,2,3] for b in bb),e['id']+' bond indices/orders '+key)
  for g in m['functionalGroups']:
   check(all(0<=x<len(aa) for x in g['atomIndices']),e['id']+' group atoms '+key)
   check(all(0<=x<len(bb) and {bb[x]['a'],bb[x]['b']}<=set(g['atomIndices']) for x in g['bondIndices']),e['id']+' group bonds '+key)
  if key=='model3dPath':check(m.get('representation')=='3d' and m.get('has3D') and m.get('allowRotation'),e['id']+' 3D flags')
for rid,mm in bindings['recordBindings'].items():
 p=R.parents[2]/'recipe-atlas/data/records'/(rid+'.json')
 if not p.exists():p=R.parent/'cofe2o4/canonical'/(rid+'.json')
 r=read(p)
 check(sha(p)==bindings['sourceRecordSha256'][rid],rid+' source record unchanged')
 check(set(mm)=={m['id'] for m in r['materials']},rid+' all material IDs bound')
 check(all(v in entries for v in mm.values()),rid+' bindings resolve')
 check(len(mm)==len(r['materials']),rid+' no duplicate material IDs')
for filename in ['registry.json','bindings.json','molecules-3d.json']:
 check(not re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]|file://', (R/filename).read_text(encoding='utf-8')),filename+' no public absolute filesystem paths')
check(not read(R/'generation-report.json')['optionalModelIssues'],'No optional model errors')
check(entries['cobalt-acetate']['pubchemCid']==6277 and entries['iron-acetate']['pubchemCid']==18344,'Incoming acetates correctly identified; no acetylacetonate substitution')
check(not entries['ir-mecp-cod']['model3dPath'] and not entries['ir-mecp-cod']['model2dPath'],'Haptic Ir coordination not fabricated')

# Render actual product SVGs, including all formula cards, for visual review.
review=R/'actual-svg-review';review.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
names=list(entries)
for i,id in enumerate(names):
 e=entries[id];doc=pymupdf.open(stream=(R/e['svgPath']).read_bytes(),filetype='svg');pix=doc[0].get_pixmap(alpha=False);pix.save(str(review/(id+'.png')))
for page in range(math.ceil(len(names)/15)):
 canvas=Image.new('RGB',(1260,1200),'white');draw=ImageDraw.Draw(canvas)
 for i,id in enumerate(names[page*15:(page+1)*15]):
  im=Image.open(review/(id+'.png')).convert('RGB');im.thumbnail((408,184));x=(i%3)*420;y=(i//3)*240
  canvas.paste(im,(x+6,y+31));draw.text((x+8,y+6),id[:45],font=font,fill='#112a3a')
 canvas.save(review/('contact-'+str(page+1)+'.png'))
report={'status':'passed' if not errors else 'failed','checks':checks,'errors':errors,'registrySha256':sha(R/'registry.json'),'bindingsSha256':sha(R/'bindings.json'),'summary':registry['summary'],'actualSvgContactSheets':math.ceil(len(names)/15),'visualReviewStatus':'pending manual inspection','primaryConnectivityVerifiedDuringGeneration':True,'formulaChargeAndIndicesVerifiedDuringGeneration':True,'unresolvedIdentityLookup':['Ir haptic precursor PubChem name lookup returned404; source paper identity retained without invented connectivity'],'limits':['Reference molecule is not a unique solution species or ligand-binding structure.','Hydrates and ionic components have no 3D geometry.','Unspecified hexanol isomer and prepared precursor mixtures remain formula/identity only.']}
(R/'validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['status','checks','errors','actualSvgContactSheets']},indent=2));raise SystemExit(bool(errors))
