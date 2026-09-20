"""Cache chemical identity/connectivity records only; never download papers."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import json, hashlib, urllib.request, datetime
OUT=Path(__file__).resolve().parent
RAW=OUT/'raw'; RAW.mkdir(exist_ok=True)
IDS={'sodium-sulfide':14804,'sodium-borohydride':4311764,'ethylene-oxide':6354,'ama':17869,'pdp-alcohol':140135,'biocytin-hydrazide':128197,'acetic-acid':176}
rows=[]
for name,cid in IDS.items():
    for kind,tail in [('properties','property/MolecularFormula,IUPACName,CanonicalSMILES,IsomericSMILES,InChI,InChIKey/JSON'),('2d','SDF?record_type=2d'),('3d','SDF?record_type=3d')]:
        if kind=='3d' and name in ['sodium-sulfide','sodium-borohydride','acetic-acid']: continue
        url=f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/{tail}'
        path=RAW/f'{name}-{kind}.{"json" if kind=="properties" else "sdf"}'
        row={'name':name,'cid':cid,'kind':kind,'url':url,'path':str(path),'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        try:
            if path.exists(): data=path.read_bytes(); row['cached']=True
            else:
                req=urllib.request.Request(url,headers={'User-Agent':'MatterSyn chemical-reference curator'})
                data=urllib.request.urlopen(req,timeout=25).read(); path.write_bytes(data)
            row.update(status='retrieved',sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
        except Exception as e: row.update(status='not_retrieved',error=str(e))
        rows.append(row)
        (OUT/'reference-retrieval.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
        print(name,kind,row['status'],flush=True)
