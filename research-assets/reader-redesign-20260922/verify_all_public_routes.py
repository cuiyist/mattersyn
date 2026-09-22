"""Check every published Reader route against the local release; no scientific edits."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import urllib.parse
import urllib.request

WORK = Path(__file__).resolve().parent
DIST = WORK.parents[1] / 'recipe-atlas/dist'
BASE = 'https://cuiyist.github.io/mattersyn-site/'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
index = read(DIST / 'data/materials-index.json')
presentation = read(DIST / 'data/reader-presentation.json')
targets = [('material', m['id'], m['url']) for m in index['materials']]
targets += [('method', rid, f'records/{rid}.html') for rid in presentation['records']]
targets += [('shared', p, p) for p in [
    'reader-app.mjs', 'reader-structures.mjs', 'reader-particle.mjs',
    'reader.css', 'illustrated-record.mjs', 'data/materials-index.json',
    'data/reader-presentation.json', 'data/reader-release.json',
]]

def check(target):
    kind, identity, relative = target
    url = BASE + relative
    row = {'kind': kind, 'id': identity, 'url': url}
    try:
        request = urllib.request.Request(url, headers={
            'User-Agent': 'MatterSyn-all-route-verification', 'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read()
            row['http_status'] = response.status
            row['login_redirect'] = 'login' in response.geturl()
        local = (DIST / urllib.parse.urlsplit(relative).path).read_bytes()
        row['matches_release'] = raw == local
        row['sha256'] = hashlib.sha256(raw).hexdigest()
        row['passed'] = row['http_status'] == 200 and row['matches_release'] and not row['login_redirect']
    except Exception as exc:
        row.update(passed=False, error=str(exc))
    return row

with ThreadPoolExecutor(max_workers=8) as pool:
    rows = list(pool.map(check, targets))
report = {
    'verified_at': datetime.now(timezone.utc).isoformat(),
    'scope': 'Anonymous HTTP and release-byte verification for every active material and method URL plus shared renderer/metadata. Previous full-route browser checks are recorded separately; this is not a new paper or figure audit.',
    'material_pages': sum(r['kind'] == 'material' for r in rows),
    'method_pages': sum(r['kind'] == 'method' for r in rows),
    'shared_artifacts': sum(r['kind'] == 'shared' for r in rows),
    'status': 'passed' if all(r['passed'] for r in rows) else 'failed',
    'failures': [r for r in rows if not r['passed']],
    'results': rows,
}
(WORK / 'all-public-routes.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k != 'results'}, indent=2))
raise SystemExit(report['status'] != 'passed')
