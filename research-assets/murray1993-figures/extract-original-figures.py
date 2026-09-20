"""Render original PDF figure rectangles with Poppler, without pixel editing."""
import hashlib, json, math, subprocess
from pathlib import Path
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent
PDF=ROOT.parent/'murray1993-main.pdf'
POPPLER=Path(r'[local path redacted]')
DPI=300
FIGURES=[
    {'figure':3,'pdfPage':4,'printedPage':8709,'id':'figure-03-absorption-size-series',
     'requestedBoundsTopLeftPoints':[346,46,542,329],
     'caption':'Original Figure 3. Room-temperature absorption spectra of CdSe nanocrystals in hexane, with diameters approximately 12-115 Å (1.2-11.5 nm).',
     'scientificContentType':'experimental optical absorption spectra',
     'labelsRetained':['Wavelength (nm)','Absorbance (arbitrary units)','Individual size labels in Å']},
    {'figure':5,'pdfPage':5,'printedPage':8710,'id':'figure-05-absorption-photoluminescence',
     'requestedBoundsTopLeftPoints':[67,42,287,268],
     'caption':'Original Figure 5. Room-temperature absorption and band-edge photoluminescence of 35 Å (3.5 nm) diameter CdSe nanocrystals; the paper reports no deep-trap luminescence for this sample.',
     'scientificContentType':'experimental absorption and photoluminescence spectra',
     'labelsRetained':['Wavelength (nm)','Absorbance (arbitrary units)','Intensity (arbitrary units)','Absorption and Fluorescence arrows']},
    {'figure':6,'pdfPage':5,'printedPage':8710,'id':'figure-06-tem',
     'requestedBoundsTopLeftPoints':[323,42,556,328],
     'caption':'Original Figure 6. Bright-field TEM with lattice contrast of dispersed, slightly prolate CdSe nanocrystals. The caption reports a 35.0 Å ±5% long axis and a 30 Å ±6% perpendicular axis. Original 20 nm scale bar retained.',
     'scientificContentType':'experimental transmission electron microscopy image',
     'labelsRetained':['Original 20 nm scale bar']},
    {'figure':11,'pdfPage':7,'printedPage':8712,'id':'figure-11-xrd-size-series',
     'requestedBoundsTopLeftPoints':[98,45,272,310],
     'caption':'Original Figure 11. Powder X-ray diffraction spectra for CdSe diameters (a) 12, (b) 18, (c) 20, (d) 37, (e) 42, (f) 83, and (g) 115 Å, with bulk wurtzite reference peak positions (h).',
     'scientificContentType':'experimental powder X-ray diffraction series with bulk reference peak positions',
     'labelsRetained':['2θ','Intensity (arbitrary units)','Series labels (a)-(h)','Wurtzite Miller-index labels']},
    {'figure':15,'pdfPage':9,'printedPage':8714,'id':'figure-15-experimental-model-xrd',
     'requestedBoundsTopLeftPoints':[344,45,548,277],
     'caption':'Original Figure 15. Experimental powder XRD (dotted) for approximately 37 Å (3.7 nm), approximately 1000-atom CdSe nanocrystals, compared with the paper’s simulated XRD (solid) incorporating stacking faults, a 1.3 aspect ratio, and surface disorder.',
     'scientificContentType':'original published comparison of experimental data and authors’ structural simulation',
     'labelsRetained':['2θ','Intensity (arbitrary units)','Experimental and simulated curves'],
     'interpretationNote':'The solid curve is the original paper authors’ simulation, not an AI-generated curve. The figure caption says one stacking fault per crystallite; the adjacent discussion describes a 1.3-fault average. The short display caption avoids concealing that source discrepancy.'},
]

reader=PdfReader(PDF)
metadata={'sourcePdf':str(PDF),'sourcePdfSha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),
          'sourceTitle':'Synthesis and Characterization of Nearly Monodisperse CdE (E = Sulfur, Selenium, Tellurium) Semiconductor Nanocrystallites',
          'authors':['C. B. Murray','D. J. Norris','M. G. Bawendi'],'year':1993,
          'journalCitation':'J. Am. Chem. Soc. 1993, 115, 8706-8715',
          'doi':'10.1021/ja00072a025','sourceUrl':'https://doi.org/10.1021/ja00072a025',
          'assetType':'original published scientific figure extract',
          'extractionMethod':'Poppler pdftoppm direct PDF rasterization of rectangular crop, RGB PNG, no redraw, image generation, interpolation-based enhancement, or pixel editing',
          'dpi':DPI,'boundsConvention':'[left, top, right, bottom] in PDF points from upper-left page origin; 1 point = 1/72 inch',
          'captionPolicy':'Captions in this metadata are source-based descriptions; original caption text is outside each image crop.',
          'figures':FIGURES}
for f in FIGURES:
    page=reader.pages[f['pdfPage']-1]
    width,height=float(page.mediabox.width),float(page.mediabox.height)
    left,top,right,bottom=f['requestedBoundsTopLeftPoints']
    x,y=math.floor(left*DPI/72),math.floor(top*DPI/72)
    endx,endy=math.ceil(right*DPI/72),math.ceil(bottom*DPI/72)
    cropwidth,cropheight=endx-x,endy-y
    f['pageSizePoints']=[width,height]
    f['cropPixelsAtRenderDpi']={'x':x,'y':y,'width':cropwidth,'height':cropheight}
    actual=[x*72/DPI,y*72/DPI,endx*72/DPI,endy*72/DPI]
    f['actualBoundsTopLeftPoints']=actual
    f['actualBoundsPdfBottomLeftPoints']=[actual[0],height-actual[3],actual[2],height-actual[1]]
    f['file']=f['id']+'.png'
    f['path']=str(ROOT/f['file'])
    f['originalFigureNotAiGenerated']=True
    command=[str(POPPLER),'-f',str(f['pdfPage']),'-l',str(f['pdfPage']),'-singlefile','-r',str(DPI),'-x',str(x),'-y',str(y),'-W',str(cropwidth),'-H',str(cropheight),'-png',str(PDF),str(ROOT/f['id'])]
    subprocess.run(command,check=True)
    f['sha256']=hashlib.sha256((ROOT/f['file']).read_bytes()).hexdigest()
    print(f['file'],cropwidth,cropheight)
(ROOT/'figure-manifest.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
