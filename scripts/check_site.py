"""Validate local generated links, record/page parity and export privacy."""
import json,re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote
from dataset_lib import ROOT,digest,OPTICAL_FEATURES

class Page(HTMLParser):
    def __init__(self,text):
        super().__init__();self.ids=[];self.links=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.append(a['id'])
        for k in ['href','src']:
            if a.get(k):self.links.append(a[k])

def main():
    dist=ROOT/'dist';errors=[];files=list(dist.rglob('*.html'))
    parsed={p:Page(p.read_text(encoding='utf-8')) for p in files}
    for p,page in parsed.items():
        if len(page.ids)!=len(set(page.ids)):errors.append(str(p)+' duplicate HTML ID')
        for href in page.links:
            u=urlsplit(href)
            if u.scheme or u.netloc:continue
            target=(dist/unquote(u.path).lstrip('/') if u.path.startswith('/') else p.parent/unquote(u.path)).resolve() if u.path else p
            if not target.exists():errors.append(str(p.relative_to(dist))+' missing '+href);continue
            if u.fragment and target.suffix=='.html':
                info=parsed.get(target) or Page(target.read_text(encoding='utf-8'))
                if unquote(u.fragment) not in info.ids:errors.append(str(p.relative_to(dist))+' missing fragment '+href)
    records=[json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'data/records').glob('*.json')]
    manifest=json.loads((dist/'data/dataset-manifest.json').read_text(encoding='utf-8'));meta={r['record_id']:r for r in manifest['records']}
    for r in records:
        public=json.loads((dist/'data/records'/(r['record_id']+'.json')).read_text(encoding='utf-8'))
        if r!=public or digest(r)!=meta[r['record_id']]['record_sha256']:errors.append('Record/export hash mismatch '+r['record_id'])
        if 'C:\\Users\\' in json.dumps(public) or 'C:/Users/' in json.dumps(public):errors.append('Local path in public record')
    optical=[json.loads(s) for s in (dist/'data/exports/optical_outcome.jsonl').read_text(encoding='utf-8').splitlines()]
    for row in optical:
        if set(row['input']['features'])!=OPTICAL_FEATURES:errors.append('Optical feature allowlist mismatch')
        if 'CC BY-NC' not in json.dumps(row['provenance']):errors.append('Lost source license')
    if errors:raise SystemExit('\n'.join(errors))
    print(f'Passed: {len(files)} pages, {len(records)} canonical/public hashes, {len(optical)} optical export rows; local assets, fragments and privacy.')
if __name__=='__main__':main()
