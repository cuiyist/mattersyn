from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import hashlib,json,re,urllib.request
root=Path('[local path redacted]')
class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.links=[];self.figure_keys=[];self.stack=[];self.sections=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='section' and 'id' in a:self.sections.append(a['id'])
        if 'data-figure' in a:self.figure_keys.append(a['data-figure'])
        if tag in ('a','link','script','img'):
            self.links.append(a.get('href',a.get('src','')))
        if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):self.stack.append(tag)
    def handle_endtag(self,tag):
        assert self.stack and self.stack.pop()==tag,('unbalanced tag',tag)
page=Page();html=(root/'index.html').read_text(encoding='utf-8');page.feed(html)
assert not page.stack,page.stack
assert len(page.ids)==len(set(page.ids)),'duplicate IDs'
assert [x for x in page.sections if x!='evidence']==['reagents','journey','product','properties']
assert set(page.figure_keys)=={'tem','xrd','model','absorption','pl'}
for link in page.links:
    parts=urlsplit(link)
    if parts.scheme or parts.netloc or not link:continue
    if parts.path:assert (root/unquote(parts.path)).is_file(),link
    elif parts.fragment:assert parts.fragment in page.ids,link
for filename in ('murray-app.js','characterization.mjs'):
    script=(root/filename).read_text(encoding='utf-8')
    for item in re.findall(r"(?:getElementById\(|\$\()['\"]([^'\"]+)",script):
        assert item in page.ids or item=='planar-viewer',(filename,item)
manifest=json.loads((root/'assets/murray1993-figures/figure-manifest.json').read_text(encoding='utf-8'))
assert {f['figure'] for f in manifest['figures']}=={3,5,6,11,15}
for f in manifest['figures']:
    blob=(root/'assets/murray1993-figures'/f['file']).read_bytes()
    assert blob[:8]==b'\x89PNG\r\n\x1a\n'
    assert hashlib.sha256(blob).hexdigest()==f['sha256']
    assert int.from_bytes(blob[16:20],'big')==f['cropPixelsAtRenderDpi']['width']
    assert int.from_bytes(blob[20:24],'big')==f['cropPixelsAtRenderDpi']['height']
for name in ('murray1993-characterization.json','murray1993-figures/figure-manifest.json'):
    text=(root/'assets'/name).read_text(encoding='utf-8');json.loads(text)
    assert not re.search(r'C:[/\\]|Users[/\\]|Authorization|Bearer ',text),name
data=json.loads((root/'assets/murray1993-characterization.json').read_text(encoding='utf-8'))
assert data['source']['doi']=='10.1021/ja00072a025'
assert next(f for f in data['optical_properties'] if f['id']=='figure_5')['properties']['relative_luminescence_quantum_yield_percent_approx']==9.6
for route in ('','characterization.mjs','characterization.css','assets/murray1993-characterization.json','assets/murray1993-figures/figure-06-tem.png','assets/murray1993-figures/figure-05-absorption-photoluminescence.png'):
    with urllib.request.urlopen('http://127.0.0.1:5186/'+route) as response:assert response.status==200
print('PASS: four sections, balanced HTML, all local links/IDs, five authentic PNG hashes/dimensions, sanitized data, key optical value, local HTTP routes.')
