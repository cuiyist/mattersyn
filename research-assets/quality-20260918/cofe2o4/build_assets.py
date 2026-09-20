from pathlib import Path
import json, hashlib, subprocess
from pypdf import PdfReader
R=Path(__file__).resolve().parent
D=R.parents[2]/'downloaded_papers'
P=Path('[local path redacted]')
sources={'main':D/'10.1021_acs.jpcc.8b11124.pdf','si':D/'10.1021_acs.jpcc.8b11124_si_1.pdf'}
# Bounding rectangles are original PDF page coordinates in points, top-left origin.
items=[
 ('graphical-abstract','main',1,[373,250,567,395]),
 ('figure-1','main',3,[319,62,570,355]),
 ('figure-2','main',4,[56,62,307,342]),
 ('figure-3','main',5,[56,62,307,464]),
 ('figure-4','main',5,[319,62,570,354]),
 ('table-1','main',3,[319,543,570,690]),
 ('equation-1','main',3,[56,431,307,530]),
 ('equation-2','main',3,[319,350,570,429]),
 ('figure-s1','si',2,[68,64,528,367]),
 ('figure-s2','si',2,[65,391,532,642]),
 ('figure-s3','si',3,[65,63,532,498]),
 ('figure-s4','si',3,[88,502,530,778]),
]
(R/'crops').mkdir(exist_ok=True)
out=[]
for id,role,page,b in items:
 f=sources[role]; dpi=300; x,y,x1,y1=[round(t*dpi/72) for t in b]
 dest=R/'crops'/id
 subprocess.run([str(P),'-f',str(page),'-l',str(page),'-singlefile','-r',str(dpi),'-x',str(x),'-y',str(y),'-W',str(x1-x),'-H',str(y1-y),'-png',str(f),str(dest)],check=True,capture_output=True)
 png=dest.with_suffix('.png')
 out.append({'id':id,'document_role':role,'page':page,'source_path':str(f),'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'asset':str(png.relative_to(R)).replace('\\','/'),'sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'crop_bbox_pdf_points_top_left':b,'dpi':dpi,'renderer':'Poppler pdftoppm','transformation':'Original raster crop; no redrawing or data alteration','visual_review':False,'rights':'Original publisher/author figure; attribution does not itself grant public redistribution rights.'})
(R/'figure-provenance.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'assets':len(out),'page_sizes':{r:[list(p.mediabox) for p in PdfReader(str(f)).pages] for r,f in sources.items()}},default=float))
