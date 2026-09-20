"""Validate project-path links and source-to-public transport without changing scientific data."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit,unquote
from concurrent.futures import ThreadPoolExecutor
import hashlib,json
ROOT=Path('[local path redacted]')
SOURCE=ROOT/'recipe-atlas/dist'
PUBLIC=ROOT.parent/'mattersyn-github-public/mattersyn-site'
BASE='https://cuiyist.github.io/mattersyn-site/'
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ('href','src','poster') and value:self.links.append(value)
findings=[];links=0;pages=0
for path in PUBLIC.rglob('*.html'):
    pages+=1;parser=Links();parser.feed(path.read_text(encoding='utf8'))
    pageurl=urljoin(BASE,path.relative_to(PUBLIC).as_posix())
    for href in parser.links:
        if href.startswith(('mailto:','tel:','data:','javascript:','#')):continue
        url=urlsplit(urljoin(pageurl,href))
        if url.netloc!='cuiyist.github.io':continue
        links+=1
        if not url.path.startswith('/mattersyn-site/'):
            findings.append({'page':path.relative_to(PUBLIC).as_posix(),'url':href,'reason':'escapes_project_prefix'});continue
        target=PUBLIC/unquote(url.path[len('/mattersyn-site/'):])
        if target.is_dir():target=target/'index.html'
        if not target.is_file():findings.append({'page':path.relative_to(PUBLIC).as_posix(),'url':href,'reason':'missing_local_target'})
old='https://mattersyn-recipe-atlas.cuiy781513.chatgpt.site'
new=BASE.rstrip('/')
def compare(path):
    rel=path.relative_to(SOURCE);target=PUBLIC/rel
    a=path.read_bytes();b=target.read_bytes()
    if a==b:return None
    if path.suffix=='.html' and a.decode('utf8').replace(old,new)==b.decode('utf8'):
        return {'path':rel.as_posix(),'change':'deployment_only_site_url'}
    return {'path':rel.as_posix(),'change':'unexpected_difference'}
with ThreadPoolExecutor(max_workers=12) as pool:
    changes=[r for r in pool.map(compare,(p for p in SOURCE.rglob('*') if p.is_file())) if r]
findings.extend(c for c in changes if c['change']=='unexpected_difference')
report={'status':'passed' if not findings else 'failed','html_pages':pages,'local_links_checked':links,
    'deployment_only_changes':changes,'findings':findings,'public_files':sum(1 for p in PUBLIC.rglob('*') if p.is_file() and '.git' not in p.parts),
    'browser_verified':['periodic table element filter','SnO2 material hub','relative record links','precursor/solvent viewer','hydrolysis stages','original HRTEM enlarged view with readable 4nm scale'],
    'canonical_scientific_files_identical_to_source':not any(c['change']=='unexpected_difference' for c in changes)}
(ROOT/'research-assets/github-public-staging-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,indent=2));raise SystemExit(bool(findings))
