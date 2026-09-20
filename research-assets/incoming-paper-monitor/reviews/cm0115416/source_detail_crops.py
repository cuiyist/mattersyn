from pathlib import Path
import pypdfium2 as pdfium
B=Path(__file__).resolve().parent
p=pdfium.PdfDocument('[local path redacted]')
for n,box,name in [(4,(.50,.33,.95,.65),'figure9'),(4,(.50,.045,.95,.33),'figure8'),(2,(.52,.24,.93,.45),'figure2')]:
 image=p[n-1].render(scale=4).to_pil();w,h=image.size;image.crop(tuple(round(v*(w if j%2==0 else h)) for j,v in enumerate(box))).save(B/('source-detail-'+name+'.png'))
