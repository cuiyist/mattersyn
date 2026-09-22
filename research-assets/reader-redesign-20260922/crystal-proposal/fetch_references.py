"""Read-only remote retrieval of crystallographic references; no paper PDFs/SI."""
from pathlib import Path
import urllib.request, urllib.parse, json, hashlib, concurrent.futures, sys

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / 'source-cache'
CACHE.mkdir(exist_ok=True)

def fetch(item):
    name, url = item
    target = CACHE / name
    try:
        if target.exists():
            data = target.read_bytes()
        else:
            req = urllib.request.Request(url, headers={'User-Agent': 'MatterSyn-reference-curation/1.0'})
            with urllib.request.urlopen(req, timeout=35) as response:
                data = response.read(5_000_001)
            if len(data) > 5_000_000:
                raise ValueError('Reference response exceeds cap')
            target.write_bytes(data)
        return {'file': name, 'url': url, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'status': 'retrieved'}
    except Exception as exc:
        return {'file': name, 'url': url, 'status': 'failed', 'error': str(exc)}

if __name__ == '__main__':
    items = []
    if len(sys.argv) > 1 and sys.argv[1] == 'query':
        for formula in ['Cd S','Cd Te','Zn S','Zn Se','Pb S','In As','O2 Sn','Al2 O4 Zn','La2 Mo3 O12','Pt','Fe Pt','Cs Cl3 Mn']:
            url = 'https://www.crystallography.net/cod/result.php?' + urllib.parse.urlencode({'formula': formula, 'format':'json'})
            items.append(('query-'+formula.replace(' ','-')+'.json', url))
    else:
        refs = json.loads((ROOT / 'retrieval-input.json').read_text(encoding='utf-8'))
        items = [(x['file'], x['url']) for x in refs]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(fetch, items))
    out = ROOT / ('query-receipts.json' if len(sys.argv)>1 and sys.argv[1]=='query' else 'retrieval-receipts.json')
    out.write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results,indent=2))
