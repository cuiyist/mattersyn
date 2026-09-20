"""Read-only source rendering and deterministic original-evidence crops."""
from pathlib import Path
import hashlib,json,subprocess
from PIL import Image
from pypdf import PdfReader

BASE=Path(__file__).resolve().parent
OUT=BASE/'reader-assets'
OUT.mkdir(exist_ok=True)
PAGES=OUT/'pages';PAGES.mkdir(exist_ok=True)
POP=Path(r'[local path redacted]')
SOURCES={
 'main':(Path(r'[local path redacted]'),'ed5e5f4cc0db81c73fd9863922471bfd3d641ecd2a2793d4ea654e1a6d1550f3',12),
 'si':(Path(r'[local path redacted]'),'b357afa581c9d2e1e15b6dfc6520c4a81542b8d9d24fe6c1e590dd0a17f47dfc',4)}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'schema':'mattersyn-original-reader-assets/1','author':'/root/norberg2004_extract','render_engine':'Poppler pdftoppm','dpi':220,'sources':[],'assets':[]}
for role,(src,expected,count) in SOURCES.items():
 actual=sha(src); assert actual==expected,(role,actual)
 reader=PdfReader(src);assert len(reader.pages)==count
 other=Path(r'[local path redacted]')/src.name
 assert sha(other)==actual
 manifest['sources'].append({'role':role,'path':str(src),'sha256':actual,'page_count':count,'identical_copy':str(other),'identical_copy_sha256':sha(other)})
 if not all((PAGES/f'{role}-{p:02d}.png').exists() or (PAGES/f'{role}-{p}.png').exists() for p in range(1,count+1)):
  subprocess.run([str(POP),'-r','220','-png',str(src),str(PAGES/role)],check=True,capture_output=True)
 for i,page in enumerate(reader.pages,1):
  txt=BASE/f'{role}-{i:02d}.txt'; assert txt.exists()
  # Preserve the verified source-backed cache; no source files changed.
  png=PAGES/f'{role}-{i:02d}.png'
  if not png.exists(): png=PAGES/f'{role}-{i}.png'
  manifest['assets'].append({'id':f'{role}-page-{i}','kind':'full_page','source_role':role,'source_sha256':actual,'pdf_page':i,'path':str(png.relative_to(BASE)),'sha256':sha(png),'dimensions':Image.open(png).size,'text_cache':str(txt.relative_to(BASE)),'text_cache_sha256':sha(txt),'crop':None})

# Coordinates in the previously visually reviewed 978 x 1265 page renders;
# scale to original 220dpi render. Captions and axis labels are retained.
crops=[
 ('figure-1','main',3,(505,64,925,466)),
 ('figure-2','main',4,(85,66,500,365)),
 ('figure-3','main',4,(505,66,925,605)),
 ('figure-4','main',4,(505,615,925,930)),
 ('figure-5','main',5,(87,63,500,494)),
 ('figure-6','main',5,(505,68,925,485)),
 ('figure-7','main',5,(503,484,925,742)),
 ('figure-8','main',6,(85,66,472,407)),
 ('figure-9','main',6,(85,407,500,841)),
 ('figure-10','main',6,(504,71,925,330)),
 ('scheme-1','main',8,(505,63,873,283)),
 ('equation-1','main',7,(551,122,894,158)),
 ('equation-2','main',8,(108,737,479,774)),
 ('equation-3','main',9,(516,324,890,380)),
 ('equation-4','main',10,(505,543,925,638)),
 ('table-s1','si',2,(105,102,877,412)),
 ('table-s2','si',2,(105,465,877,777)),
 ('table-s3','si',2,(105,830,890,1117)),
 ('figure-s1-equations','si',3,(105,115,882,919)),
 ('figure-s2','si',4,(105,83,882,454)),
 ('figure-s3','si',4,(105,483,884,822)),
 ('table-s4','si',4,(105,841,881,1038)),
 ('sample-preparation','main',3,(85,64,500,730)),
 ('materials','main',2,(504,782,925,944))]
for aid,role,p,b in crops:
 pg=PAGES/f'{role}-{p:02d}.png'
 if not pg.exists():pg=PAGES/f'{role}-{p}.png'
 im=Image.open(pg); w,h=im.size
 box=tuple(round(v*s) for v,s in zip(b,[w/978,h/1265,w/978,h/1265]))
 dest=OUT/f'{aid}.png';im.crop(box).save(dest)
 manifest['assets'].append({'id':aid,'kind':'source_crop','source_role':role,'source_sha256':SOURCES[role][1],'pdf_page':p,'path':str(dest.relative_to(BASE)),'sha256':sha(dest),'dimensions':Image.open(dest).size,'crop':{'coordinate_system':'source rendered pixels, top-left origin','bounds':box,'page_dimensions':[w,h]},'content_status':'original figure/table/equation; no trace digitization or scientific alteration'})
(OUT/'asset-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'source_hashes_verified':4,'pages':16,'crops':len(crops),'asset_count':len(manifest['assets'])}))
