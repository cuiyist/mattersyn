"""Read-only public source discovery; no cookies, browser profile or authentication."""
from pathlib import Path
import urllib.request,json,hashlib
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parent/'sun2004-discovery';R.mkdir(exist_ok=True)
jobs=[('publisher-main','https://pubs.acs.org/doi/pdf/10.1021/ja0380852',None),('publisher-si','https://pubs.acs.org/doi/suppl/10.1021/ja0380852/suppl_file/ja0380852si20031027_103500.pdf',None),('figshare-search','https://api.figshare.com/v2/articles/search',{'resource_doi':'10.1021/ja0380852','page_size':10}),('openalex','https://api.openalex.org/works/https://doi.org/10.1021/ja0380852',None)]
def run(j):
 name,url,payload=j
 try:
  req=urllib.request.Request(url,data=json.dumps(payload).encode() if payload else None,headers={'User-Agent':'MatterSyn-research-source-check/1.0','Content-Type':'application/json'} if payload else {'User-Agent':'MatterSyn-research-source-check/1.0'})
  with urllib.request.urlopen(req,timeout=40) as r:data=r.read();code=r.status;final=r.url;ct=r.headers.get('Content-Type','')
  suffix='.pdf' if data.startswith(b'%PDF') else '.json' if 'json' in ct else '.html'
  path=R/(name+suffix);path.write_bytes(data)
  return {'name':name,'requested_url':url,'resolved_url':final,'status':code,'content_type':ct,'bytes':len(data),'saved_path':str(path),'sha256':hashlib.sha256(data).hexdigest()}
 except Exception as e:return {'name':name,'requested_url':url,'error':str(e)}
results=list(ThreadPoolExecutor(max_workers=4).map(run,jobs))
(R/'discovery-log.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
for n in ['figshare-search','openalex']:
 p=R/(n+'.json')
 if p.exists():
  d=json.loads(p.read_text())
  print(n,json.dumps(d if n=='figshare-search' else {k:d.get(k) for k in ['id','title','open_access','best_oa_location','locations']},ensure_ascii=False))
