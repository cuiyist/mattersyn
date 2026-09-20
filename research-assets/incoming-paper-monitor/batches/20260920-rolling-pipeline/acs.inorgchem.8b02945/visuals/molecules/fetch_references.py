"""Read public chemical-identity metadata only. Never downloads research papers."""
from pathlib import Path
from urllib.request import Request, urlopen
from datetime import datetime, timezone
import json, hashlib

O = Path(__file__).resolve().parent / 'reference-snapshots' / 'primary'
O.mkdir(parents=True, exist_ok=True)
cids = [999,7301,12198003,272683,2733352,8003,241,6344]
url = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/' + ','.join(map(str,cids)) + '/property/MolecularFormula,CanonicalSMILES,IsomericSMILES,InChI/JSON'
p = O/'pubchem-identities.json'
if not p.exists():
    with urlopen(Request(url,headers={'User-Agent':'MatterSyn scientific reference qualification'}),timeout=45) as response:
        raw=response.read()
    data=json.loads(raw)
    assert sorted(x['CID'] for x in data['PropertyTable']['Properties'])==sorted(cids)
    p.write_bytes(raw)
    (O/'retrieval.json').write_text(json.dumps({'retrieved_at':datetime.now(timezone.utc).isoformat(),'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'purpose':'Reference molecular connectivity, not paper evidence or measured sample geometry.'},indent=2)+'\n','utf8')
print(p.read_text('utf8'))
