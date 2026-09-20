from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,r'[local path redacted]')
from PIL import Image
R=Path(__file__).resolve().parent;O=R/'reader-assets/si-pages09-10-independent';rows=[]
for label,origin,box in [('p9-R13','p9-Rtop.png',(0,555,763,677)),('p9-R22','p9-Rtop.png',(0,978,763,1095)),('p10-R24','p10-Rbottom.png',(0,0,763,102))]:
 im=Image.open(O/origin);crop=im.crop(box);out=O/(label+'-detail.png');crop.resize((crop.width*2,crop.height*2),Image.Resampling.NEAREST).save(out);rows.append({'label':label,'source_crop':origin,'source_crop_box':box,'output':str(out),'operation':'Rectangular crop and 2x nearest-neighbor magnification only; original digits unchanged.','sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
(R/'si-pages09-10-disagreement-detail-manifest.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
