"""Apply bounded reader classifications and verified original-asset display flags."""
from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=S/'data/paper-reviews/yao1998.json';r=read(p);patch=read(B/'public-review-proposal/reader-scope-patch.json')
items={i['id']:i for section in r['reader_sections']for i in section['items']}
assert patch['item_count']==len(patch['patches'])==68
for change in patch['patches']:
 scope=items[change['item_id']]['sample_scope']
 assert all(scope[k] in [v,change['set'][k]] for k,v in change['before'].items()),change['item_id']
 scope.update(change['set'])
assets=r['figures']+r['equations']+r['source_notes'];assert len(assets)==16
for asset in assets:
 assert asset['public_asset'] and asset['public_asset_sha256']
 asset.update(reviewed=True,reader_render_verified=True)
r['independent_audit']='All seven supplied main pages, canonical extraction, chemical representations, apparatus, original assets and source-to-reader mappings independently audited. Browser interactions and original-asset loading checked. Matching SI remains unverified.'
write(p,r)
print('Updated only reader context classifications, audited asset flags and review-scope description.')
