from pathlib import Path
import json,hashlib,sys
sys.dont_write_bytecode=True
sys.path.insert(0,r'[local path redacted]')
from PIL import Image
R=Path(__file__).resolve().parent;O=R/'reader-assets/si-pages11-12-independent';assets=[]
for label,base,box in [('p11-R35','p11-Rbottom.png',(0,516,763,611)),('p12-L12','p12-Ltop.png',(0,517,779,611)),('p11-R33','p11-Rbottom.png',(0,413,763,519))]:
 im=Image.open(O/base).crop(box);im=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST);p=O/(label+'-detail.png');im.save(p)
 assets.append({'label':label,'source_crop':base,'source_crop_box':list(box),'scale':3,'operation':'Original pixels, rectangular crop and nearest-neighbor magnification only.','output':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(R/'si-pages11-12-independent-detail-manifest.json').write_text(json.dumps(assets,indent=2)+'\n',encoding='utf-8')
