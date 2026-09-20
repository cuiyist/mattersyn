"""Persist the already completed seven-page review and its local source identity."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=read(B/'source-render-manifest.json');identity=read(B/'source-identity.json')
assert all(p['text_read'] and p['visually_reviewed'] for p in r['pages'])
for p in r['pages']:
 p['text_sha256']=sha(B/p['text_file']);p['render_sha256']=sha(B/p['render_file'])
r.update(recorded_at=datetime.now(timezone.utc).isoformat(),doi=identity['doi'],title=identity['title'],year=identity['year'],scope='All seven supplied main pages read and visually reviewed; matching SI not located or verified.',independent_source_audit='source-audit.json',identity_audit='source-identity.json')
(B/'source-manifest.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Saved seven-page source manifest; final live source fingerprint remains a separate publication gate.')
