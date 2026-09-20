"""Root source-scoped publication URL resolution; do not alter source facts or private drafts."""
from pathlib import Path
import json,hashlib,copy
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';O=B/'integration-proposal'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert not (O/'publication-url-normalization.json').exists()
r=read(S/'data/paper-reviews/norberg2004.json');assets={}
def walk(x):
 if isinstance(x,dict):
  if x.get('public_asset'):assets.setdefault(Path(x['public_asset']).name,set()).add(x['public_asset'])
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(r);bindings=read(S/'dist/assets/chemical-registry/bindings.json');changes=[]
for p in (S/'data/records').glob('norberg-2004-*.json'):
 old=read(p);new=copy.deepcopy(old);delta=[]
 for i,link in enumerate(new['context_links']):
  if link['url'].startswith('../reader-assets/'):
   matches=assets.get(Path(link['url']).name,set());assert len(matches)==1,(p,link,matches)
   dest=next(iter(matches));assert (S/'dist'/dest).is_file();delta.append({'pointer':f'/context_links/{i}/url','old':link['url'],'new':'../'+dest,'asset_sha256':sha(S/'dist'/dest)});link['url']='../'+dest
 if delta:
  prior=sha(p);write(p,new);bindings['sourceRecordSha256'][p.stem]=sha(p);changes.append({'record_id':p.stem,'before_sha256':prior,'after_sha256':sha(p),'deltas':delta})
write(S/'dist/assets/chemical-registry/bindings.json',bindings)
write(O/'publication-url-normalization.json',{'status':'resolved_to_approved_source_assets','scope':'Only context-link publication URLs changed. Labels, relations, scientific fields and original asset pixels remain unchanged. Private promotion records are retained; these deployment URL deltas supersede their public record hashes.','records':changes})
print(json.dumps({'records':len(changes),'links':sum(len(c['deltas'])for c in changes)}))
