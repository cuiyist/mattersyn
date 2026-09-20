"""Private source-only enlargement for four independent comparison differences."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,r'[local path redacted]')
sys.path.insert(0,r'[local path redacted]')
from PIL import Image
import hashlib,json
B=Path(__file__).resolve().parent;O=B/'reader-assets'/'si-independent-audit';O.mkdir(exist_ok=True)
specs=[('p01-L-r09-sigma','si-01-left-top.png',(530,417,690,472)),
       ('p01-R-r13-Fobs','si-01-right-top.png',(300,619,510,688)),
       ('p02-R-r16-Fcal','si-02-right-top.png',(150,785,325,850)),
       ('p02-R-r23-Fobs','si-02-right-top.png',(335,1135,520,1170))]
out=[]
for key,src,box in specs:
    p=B/'reader-assets'/'si-numerical'/src
    im=Image.open(p);crop=im.crop(box);dest=O/(key+'.png')
    crop.resize((crop.width*4,crop.height*4),Image.Resampling.NEAREST).save(dest)
    out.append({'id':key,'source_path':str(p),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'crop_box':box,'magnification':4,'resampling':'nearest_neighbor_no_reconstruction','path':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
(O/'detail-manifest.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out))
