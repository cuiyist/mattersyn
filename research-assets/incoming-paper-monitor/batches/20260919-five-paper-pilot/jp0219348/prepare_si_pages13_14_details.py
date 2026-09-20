from pathlib import Path
import json,hashlib,sys
sys.dont_write_bytecode=True
sys.path.insert(0,r'[local path redacted]')
from PIL import Image
R=Path(__file__).resolve().parent;O=R/'reader-assets/si-pages13-14-independent';assets=[]
for label,base,box in [('p14-R16','p14-Rbody.png',(0,698,775,795))]:
 im=Image.open(O/base).crop(box);im=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST);p=O/(label+'-detail.png');im.save(p)
 assets.append({'label':label,'source_crop':base,'source_crop_box':list(box),'scale':3,'operation':'Original pixels, rectangular crop and nearest-neighbor magnification only.','output':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(R/'si-pages13-14-independent-detail-manifest.json').write_text(json.dumps(assets,indent=2)+'\n',encoding='utf-8')
