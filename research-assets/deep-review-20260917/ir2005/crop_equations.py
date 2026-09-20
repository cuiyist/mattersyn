"""Original PDF-native equation crops; no raster/text reconstruction."""
from pathlib import Path
import json,hashlib,struct
import pypdfium2 as pdfium
R=Path(__file__).resolve().parent
source=R.parents[2]/'downloaded_papers/10.1021_nl050648f.pdf'
out=R/'equations';out.mkdir(exist_ok=True)
doc=pdfium.PdfDocument(source)
manifest=[]
for eq,page,bbox in [(1,2,[315,308,567,525]),(2,3,[315,492,567,741])]:
 x,y,x2,y2=[round(v*300/72) for v in bbox]
 dest=out/f'equation-{eq:02d}'
 rendered=doc[page-1].render(scale=300/72).to_pil()
 rendered.crop((x,y,x2,y2)).save(dest.with_suffix('.png'))
 path=dest.with_suffix('.png');raw=path.read_bytes()
 manifest.append({'equation':eq,'source_path':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'pdf_page':page,'printed_page':1202+page,'bounds_pdf_points_top_left':bbox,'dpi':300,'pixel_dimensions':list(struct.unpack('>II',raw[16:24])),'asset':str(path),'relative_asset':path.relative_to(R).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'original_equation':True,'definitions_included':True,'renderer':'PDFium via pypdfium2; original PDF page rasterized then cropped without content modification','render_notes':'Poppler first attempt omitted the proportionality glyph with a missing Symbol-font warning; PDFium used for these equation crops. No glyph was manually redrawn.','visually_reviewed':False})
(R/'equation-crop-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
