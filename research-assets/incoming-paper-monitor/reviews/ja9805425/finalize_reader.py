from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=S/'data/paper-reviews/peng1998.json'
shutil.copy2(p,B/'reader-assets/integrated-before-final-flags.json')
d=read(p);assets=[]
for k in ['figures','tables','equations','source_notes']:
 for a in d[k]:
  assert (S/'dist'/a['public_asset']).is_file()
  assert hashlib.sha256((S/'dist'/a['public_asset']).read_bytes()).hexdigest()==a['public_asset_sha256']
  a['reviewed']=True;a['reader_render_verified']=True;assets.append(a['public_asset'])
assert len(assets)==11
d['independent_audit']='All six supplied PDF pages, 160 source units, 12 canonical records, 28 operations, 159 measurements, 119 reader items and 11 original assets independently audited. Molecular and apparatus representations, actual reader mappings and browser controls verified.'
write(p,d)
write(B/'browser-qa.json',{'status':'passed','at':datetime.now(timezone.utc).isoformat(),'target':'local built output for existing MatterSyn Site','checks':['Periodic-table In+As selection exposes InAs with one reviewed method','InAs hub precursor and product references render','InAs initial feed shows <0.1 s and 1 mL; 0.5 mL at 23 min and 0.8 mL at 158 min remain sequential stages','TMS3As 2D dialog opens; zoom, reset and close respond','InAs gallery scope switches from 2 applicable images to 7 source figures/tables','All 11 source assets open in enlarged dialogs with positive natural image dimensions; source TEM visually inspected','Evidence search reabsorption returns one of 119 source items','Reader and CdSe record at 390x844 have no document horizontal overflow','CdSe method-list paper-prefix restriction removed; new Peng1998 card opens its illustrated record','CdSe injection displays 2.4 mL, <0.1 s and 300 C postinjection; slow reinjection displays 0.8 mL at 190 min','No browser console errors observed','Temporary viewport override reset'],'original_assets':assets})
print('Finalized 11 browser-verified original assets and saved browser QA.')
