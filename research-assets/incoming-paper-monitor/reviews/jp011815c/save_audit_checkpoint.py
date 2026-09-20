from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assets=read(B/'reader-assets/crop-manifest.json')['assets']
for a in assets:assert sha(B/'reader-assets'/a['relative_asset'])==a['sha256']
write(B/'crop-source-audit.json',{'status':'passed','source_id':'shah2001','scope':'Root inspected all 21 original crops on six rendered sheets after complete main-page review. Captions, axis labels, equation terms, scale bars and Table 1 row labels remain visible. No spectra, images or theoretical curves digitized into invented experimental values.','assets':[{k:a[k]for k in ['id','relative_asset','sha256','source_pdf_page','source_sha256']}for a in assets],'visual_inspection_sheets':['crop-review/contact-'+str(i)+'.jpg'for i in range(1,7)],'checked_at':datetime.now(timezone.utc).isoformat()})
m=read(B/'milestones.json')
m['extract']={'status':'complete','evidence':[str(B/'canonical-record-manifest.json'),str(B/'canonical-records-audit.json')],'note':'19 source-linked drafts: 11 synthesis routes, 4 supporting procedures and 4 observations; 74 operations and 111 measurements.'}
m['audit']={'status':'partial','evidence':[str(B/p)for p in ['source-audit.json','canonical-records-audit.json','molecular-source-audit.json','crop-source-audit.json']],'note':'Independent source, canonical and molecular reviews passed with explicit source limits. Reader and final apparatus presentation audits remain.'}
write(B/'milestones.json',m)
c=read(B/'checkpoint.json');c.update(canonical_records_created=19,checkpoint_at=datetime.now(timezone.utc).isoformat(),current_work_items=[{'label':k.capitalize(),'status':v['status'],'scope':v['note']}for k,v in m.items()],next_action='Finish reader and apparatus audits, integrate into the existing MatterSyn Ag/Ir/Pt pages, validate the working pages, publish the existing Site, and close this claim only after source-fingerprint verification.')
write(B/'checkpoint.json',c)
print('Extraction complete; source/canonical/molecule/crop checks saved. Reader and publication gates remain.')
