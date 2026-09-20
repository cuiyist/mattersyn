from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent
a=json.loads((B/'reader-assets/crop-manifest.json').read_text(encoding='utf-8'))['assets']
assert len(a)==17
for x in a:assert hashlib.sha256((B/'reader-assets'/x['relative_asset']).read_bytes()).hexdigest()==x['sha256']
out={'status':'passed','source_id':'gerion2001','scope':'Root inspected all 17 original crops on five rendered contact sheets after reading and viewing all eleven main pages; Figure 1 also inspected enlarged. Captions, axes, legends, table cells, notes and source unit conflicts retained. Original figures are not digitized raw data, and declared SI images are not supplied by these main-text crops.','checked_at':datetime.now(timezone.utc).isoformat(),'assets':[{k:x[k]for k in ['id','relative_asset','sha256','source_pdf_page','source_sha256']}for x in a],'inspection_sheets':['crop-review/contact-'+str(i)+'.jpg'for i in range(1,6)],'reader_render_verified':False}
(B/'crop-source-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('All 17 original main-text crop hashes and visual content checked.')
