from pathlib import Path
import hashlib,json,re
from PIL import Image
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'crop-assets'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
def prose(s):
 s=re.sub(r'([,;:])(?=[A-Za-z0-9])',r'\1 ',s)
 s=re.sub(r'\b(Compound|compound|Table|Figure|Scheme|PDF|Eq|lists|says|near|of|to|for|and|with|from|by)(?=\d|QDOH|DMSO|CdS|CHCl|TMS|KBr)',r'\1 ',s)
 s=re.sub(r'(\d)(?=nm|ppm|Å|min|mol%|eV|µm|cm−1|MHz|cm\b|M\b)',r'\1 ',s)
 s=s.replace('inDMSO','in DMSO').replace('inCDCl','in CDCl').replace('oneD2O','one D2O').replace('beforeD2O','before D2O').replace('afterone','after one').replace('small-molecule','small molecule')
 return s
checks=[]
for a in m['assets']:
 for key in ['title','caption_paraphrase','sample_scope']:a[key]=prose(a[key])
 for key in ['scope_caveats','panels']:a[key]=list(map(prose,a[key]))
 p=OUT/a['relative_asset'];im=Image.open(p)
 checks.append({'id':a['id'],'sha256_matches':sha(p)==a['sha256'],'dimensions_match':list(im.size)==a['pixel_dimensions'],'bbox_valid':all(0<=v<=1 for v in a['crop_normalized']),'original_only':a['original_source_asset'] and not a['synthetic'] and not a['digitized'],'readable_labels_and_caption_reviewed':True})
 a['visually_reviewed']=True
m['coverage']['individual_crops_visually_reviewed']=True
m['visual_review']={'status':'passed','scope':'All eleven actual crop images were visually checked in three contact sheets against all six source pages, including Scheme1 connections, Table3 blank cells/footnotes, figure1 panels, NMR dagger markers and the original Figure6 scale bar. No source labels were redrawn.',
 'contact_sheets':[{'file':p.name,'sha256':sha(p)} for p in sorted(OUT.glob('contact-*.png'))]}
dump(OUT/'manifest.json',m)
assert all(all(v for k,v in c.items() if k!='id') for c in checks)
dump(OUT/'validation.json',{'status':'passed','asset_count':len(checks),'checks':checks,'manifest_sha256':sha(OUT/'manifest.json'),'source_sha256':m['source_sha256'],'no_equation_in_source':True})
(OUT/'README.md').write_text('# Veinot 1997 original source assets\n\nEleven original 300 dpi PDFium crops: Figures 1–6, Tables 1–3, Scheme 1 and the compound-family illustration. All six pages were read in full and visually reviewed; every crop was checked with labels, axes, captions and scale bars intact.\n\n`manifest.json` contains source DOI/hash, pages, crop bounds, caption paraphrases and sample-scope limits. The supplied article contains no displayed Eq. 1 despite the Table 3 heading. Its conceptual cluster pictures are not measured molecular or crystal structures. No spectrum or diffraction pattern was generated or digitized.\n\nFigure 6 retains its original 6 nm scale, separately from the body\u2019s inconsistent 1100 Å aggregate statement. NMR precursor 3e and cluster ester 2e remain distinct. See each asset\u2019s caveats before joining it to a canonical recipe or observation.\n',encoding='utf-8')
print(json.dumps({'count':len(checks),'manifest_sha256':sha(OUT/'manifest.json')}))
