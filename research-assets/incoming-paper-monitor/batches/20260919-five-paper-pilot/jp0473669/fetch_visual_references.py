"""Cache bounded public chemical reference records; never fetch research papers."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, urllib.request, concurrent.futures
OUT=Path(__file__).resolve().parent/'visuals/molecules/raw'
OUT.mkdir(parents=True,exist_ok=True)
jobs=[]
for slug,cid in [('tin-dihydrate-ionic',10198436),('tin-dihydrate-alternate',61436),('nitric-acid',944),('tbaoh',2723671)]:
    base=f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}'
    jobs.extend([(slug+'-properties.json',base+'/property/MolecularFormula,IUPACName,CanonicalSMILES,IsomericSMILES/JSON'),(slug+'-pubchem-2d.sdf',base+'/SDF?record_type=2d')])
jobs.append(('nitric-acid-pubchem-3d.sdf','https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/944/SDF?record_type=3d'))
def fetch(job):
    name,url=job;p=OUT/name
    row={'file':str(p),'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat()}
    try:
        if p.exists(): data=p.read_bytes();row['status']='existing_cache'
        else:
            req=urllib.request.Request(url,headers={'User-Agent':'MatterSyn-reference-validation/1.0'})
            with urllib.request.urlopen(req,timeout=25) as response:data=response.read()
            p.write_bytes(data);row['status']='downloaded_primary_reference'
        row.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    except Exception as e: row.update(status='failed',error=str(e))
    return row
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(fetch,jobs))
(OUT/'retrieval-log.json').write_text(json.dumps({'scope':'Public chemical JSON/SDF only; no paper downloads','records':rows},indent=2)+'\n')
print(json.dumps(rows,indent=2))
