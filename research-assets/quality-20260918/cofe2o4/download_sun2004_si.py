from pathlib import Path
import urllib.request,json,hashlib
from pypdf import PdfReader
R=Path(__file__).resolve().parent/'sun2004-discovery';R.mkdir(exist_ok=True)
url='https://api.figshare.com/v2/articles/3353308'
meta=json.load(urllib.request.urlopen(url,timeout=30))
(R/'figshare-metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:meta.get(k) for k in ['title','doi','resource_doi','resource_title','license','description','files']}))
log=[]
for f in meta['files']:
 data=urllib.request.urlopen(f['download_url'],timeout=40).read()
 if not data.startswith(b'%PDF'):continue
 dest=R/('sun2004-'+f['name']);dest.write_bytes(data)
 reader=PdfReader(str(dest));text='\n\n'.join('=== PAGE '+str(i+1)+' ===\n'+(p.extract_text() or '') for i,p in enumerate(reader.pages))
 dest.with_suffix('.txt').write_text(text,encoding='utf-8')
 log.append({'url':f['download_url'],'file_name':f['name'],'path':str(dest),'sha256':hashlib.sha256(data).hexdigest(),'pages':len(reader.pages),'title_match_pending_visual_review':True})
 print(text)
(R/'download-log.json').write_text(json.dumps(log,indent=2),encoding='utf-8')
