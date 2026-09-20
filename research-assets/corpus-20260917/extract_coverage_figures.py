import concurrent.futures
import hashlib
import json
import math
import subprocess
from pathlib import Path
from pypdf import PdfReader

BASE = Path('[local path redacted]')
OUT = BASE / 'research-assets/corpus-20260917'
POPPLER = Path('[local path redacted]')
DPI = 300
SOURCES = {
    'murray1993': (BASE / 'research-assets/murray1993-main.pdf', '10.1021/ja00072a025'),
    'nak2017_si': (BASE / 'downloaded_papers/10.1021_acs.chemmater.7b00354_si_1.pdf', '10.1021/acs.chemmater.7b00354'),
}
SPECS = [
    ('murray1993', 'figure-01-size-selective-precipitation', 1, 3, 8708, [357,42,520,310]),
    ('murray1993', 'figure-02-cde-absorption', 2, 4, 8709, [80,48,286,262]),
    ('murray1993', 'figure-04-optical-gap-experiment-theory', 4, 4, 8709, [329,367,555,588]),
    ('murray1993', 'figure-07-tem-stacking-faults', 7, 5, 8710, [326,372,555,566]),
    ('murray1993', 'figure-08-tem-orientation-faults', 8, 6, 8711, [70,43,281,249]),
    ('murray1993', 'figure-09-tem-particle-packing', 9, 6, 8711, [326,43,555,327]),
    ('murray1993', 'figure-10-cde-xrd', 10, 6, 8711, [339,356,541,606]),
    ('murray1993', 'figure-12-xrd-phase-models', 12, 8, 8713, [92,44,257,345]),
    ('murray1993', 'figure-13-xrd-shape-models', 13, 8, 8713, [325,43,557,338]),
    ('murray1993', 'figure-14-xrd-small-particle-models', 14, 8, 8713, [321,394,558,582]),
    ('nak2017_si', 'figure-S2-core-shell-saed', 'S2', 3, 'S3', [130,314,481,664]),
]

def extract(spec):
    key, name, fig, page, printed, bounds = spec
    pdf, doi = SOURCES[key]
    outdir = OUT / key
    outdir.mkdir(exist_ok=True)
    target = outdir / name
    x,y = [math.floor(v * DPI/72) for v in bounds[:2]]
    right,bottom = [math.ceil(v * DPI/72) for v in bounds[2:]]
    subprocess.run([str(POPPLER), '-f', str(page), '-l', str(page), '-singlefile', '-r', str(DPI), '-x', str(x), '-y', str(y), '-W', str(right-x), '-H', str(bottom-y), '-png', str(pdf), str(target)], check=True, capture_output=True)
    target = target.with_suffix('.png')
    box = PdfReader(pdf).pages[page-1].mediabox
    return {'source_key':key,'doi':doi,'source_pdf':str(pdf), 'source_pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(), 'figure':fig,'pdf_page':page,'printed_page':printed,'page_size_points':[float(box.width),float(box.height)],'bounds_top_left_points_requested':bounds,'bounds_top_left_points_actual':[x*72/DPI,y*72/DPI,right*72/DPI,bottom*72/DPI], 'file':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'dpi':DPI,'pixel_size':[right-x,bottom-y],'original_published_figure':True,'visually_verified':False,'includes_caption':False}

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    figures=list(pool.map(extract,SPECS))
manifest={'method':'Direct original PDF rectangular rasterization using Poppler; no scientific redraw, AI generation, annotation addition, curve digitization, contrast adjustment, or enhancement. Axis labels, legends, panel labels and scale bars are retained.','bounds_convention':'[left,top,right,bottom] in points from upper-left page origin; 72 points per inch.','figures':figures}
(OUT/'crop-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Extracted',len(figures),'figures to',OUT)
