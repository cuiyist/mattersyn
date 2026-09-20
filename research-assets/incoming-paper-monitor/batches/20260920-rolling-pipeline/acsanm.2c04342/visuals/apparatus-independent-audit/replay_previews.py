from pathlib import Path
import sys,json,hashlib
O=Path(__file__).resolve().parent;A=O.parent/'apparatus';M=Path(r'[local path redacted]')
sys.path.insert(0,str(M/'research-assets/corpus-20260917/runtime'));sys.path.insert(0,str(M/'research-assets/rdkit-runtime'))
import pymupdf
from PIL import Image
checks=[]
for item in json.loads((A/'preview-manifest.json').read_text('utf-8'))['scenes']:
 doc=pymupdf.open(stream=(A/item['svg_path']).read_bytes(),filetype='svg')
 pix=doc[0].get_pixmap(matrix=pymupdf.Matrix(1.2,1.2),alpha=False)
 original=Image.open(A/item['png_path']).convert('RGB')
 assert original.size==(pix.width,pix.height),item['operation_id']
 assert original.tobytes()==pix.samples,item['operation_id']
 checks.append({'operation_id':item['operation_id'],'dimensions':[pix.width,pix.height],'pixels_equal':True,'svg_sha256':hashlib.sha256((A/item['svg_path']).read_bytes()).hexdigest(),'png_sha256':hashlib.sha256((A/item['png_path']).read_bytes()).hexdigest()})
out={'reviewer':'/root/peng1998_reader_assets','status':'passed','renderer':str(pymupdf.version),'scale':1.2,'actual_replays':len(checks),'pixel_checks':len(checks)*2,'scenes':checks}
(O/'preview-replay.json').write_text(json.dumps(out,indent=2)+'\n','utf-8');print(json.dumps({'replays':len(checks),'checks':len(checks)*2}))
