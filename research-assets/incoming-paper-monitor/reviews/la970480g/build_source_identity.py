"""Targeted local identity and main/SI reconciliation; no source or Site writes."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re
from pypdf import PdfReader
B=Path(__file__).resolve().parent;M=B.parents[3];SITE=M/'recipe-atlas';C=M/'research-assets/corpus-20260917'
DOI='10.1021/la970480g';TITLE='Electrolyte Effects on CdS Nanocrystal Formation in Chelate Polymer Particles: Optical and Distribution Properties'
PRIMARY=Path('[local path redacted]')
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return re.sub('[^a-z0-9]','',str(s or '').lower())
expected=sha(PRIMARY);reader=PdfReader(PRIMARY)
roots={'incoming':PRIMARY.parent,'legacy':M/'downloaded_papers'}
manifest=read(C/'private/document-manifest.json');lib=read(SITE/'data/corpus/library-source.json')
docs=[d for d in manifest['documents'] if d.get('sha256')==expected or any(x.get('doi','').lower()==DOI for x in d.get('paperAssociations',[])) or norm((d.get('likelyTitle') or {}).get('value',''))==norm(TITLE)]
papers=[p for p in lib['papers'] if p.get('doi','').lower()==DOI or norm(p.get('title'))==norm(TITLE)]
paths={}
for kind,root in roots.items():
 for p in root.rglob('*la970480g*'):
  if p.is_file():paths[str(p)]=(kind,p)
for d in docs:
 p=roots['legacy']/d['sourceRelativeFilename']
 if p.exists():paths[str(p)]=('legacy',p)
files=[]
for kind,p in paths.values():
 s=p.stat();h=sha(p);t=p.stat()
 files.append({'root':kind,'path':str(p),'basename':p.name,'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'birthtime_ns':s.st_birthtime_ns,'sha256':h,'stat_stable_during_hash':(s.st_size,s.st_mtime_ns)==(t.st_size,t.st_mtime_ns),'role':'main' if h==expected else 'unverified_candidate'})
logs=[]
for kind,root in roots.items():
 for p in root.glob('*.jsonl'):
  for n,line in enumerate(p.open(encoding='utf8',errors='replace'),1):
   if 'la970480g' in line.lower():
    try:j=json.loads(line)
    except json.JSONDecodeError:j={'unparsed':line.strip()}
    logs.append({'root':kind,'basename':p.name,'line':n,'entry':j})
existing=[]
for p in (SITE/'data/records').glob('*.json'):
 r=read(p);ss=[s.get('id') for s in r.get('sources',[]) if s.get('doi','').lower()==DOI]
 if ss:existing.append({'record_id':r['record_id'],'primary_source':r.get('lineage',{}).get('source_group') in ss})
reviews=[]
for p in (SITE/'data/paper-reviews').glob('*.json'):
 r=read(p)
 if r.get('doi','').lower()==DOI:reviews.append(r.get('paper_id'))
text='\n'.join((B/f'page-{i}.txt').read_text(encoding='utf8') for i in range(1,8))
caches=[]
for d in docs:
 p=C/d['textPath']
 caches.append({'document_id':d['id'],'filename':d['sourceRelativeFilename'],'sha256':d['sha256'],'page_count':d['pageCount'],'cached_text_sha256':sha(p),'matching_current_content':d['sha256']==expected,'cached_extraction_is_not_full_review':True})
out={'schema':'mattersyn-local-source-identity-1','checked_utc':datetime.now(timezone.utc).isoformat(),'source_id':'yao1998','doi':DOI,'title':TITLE,'authors':['Hiroshi Yao','Yukako Takada','Noboru Kitamura'],'corresponding_author':'Noboru Kitamura','journal':'Langmuir','year':1998,'volume':14,'issue':3,'printed_pages':[595,601],'pdf_page_count':len(reader.pages),'dates':{'received':'1997-05-08','final_form':'1997-11-14','published_web':'1998-02-03'},'main_sha256':expected,'pdf_metadata':dict(reader.metadata or {}),'identity_evidence':[{'locator':'Main PDF p.1, printed p.595: title, byline, journal/date/footer','supports':['Full title and three authors','Langmuir 1998,14,595–601','Received and final-form dates in1997','Published on Web02/03/1998','Article code S0743-7463(97)00480-0'],'render_sha256':sha(B/'page-1.png')},{'locator':'Main PDF p.7, printed p.601: footer and closing article code','supports':['Issue3','Closing page601','LA970480G'],'render_sha256':sha(B/'page-7.png')}],'doi_binding':{'status':'content_and_local_metadata_corroborated','full_doi_in_extracted_main':DOI in text.lower(),'basis':'Printed terminal LA970480G, matching first-page article code and DOI/title-associated local catalog/download evidence. Filename is not sole identity evidence. No external lookup.'},'local_files':files,'main_copy_count':sum(f['role']=='main' for f in files),'unique_main_content_count':len({f['sha256'] for f in files if f['role']=='main'}),'unverified_file_candidates':[f['path'] for f in files if f['role']!='main'],'cached_identity_reuse':caches,'existing_identity':{'papers':[{'paper_id':p['id'],'title':p['title'],'year':p.get('year')} for p in papers],'canonical_records':existing,'formal_source_review_ids':reviews},'download_log_evidence':logs,'si':{'status':'not_located_or_verified','matched_local_si_count':0,'declaration_term_hits':{s:len(re.findall(re.escape(s),text,re.I)) for s in ['supporting information','supplementary','supplemental','microfiche','information available']},'scope':'Targeted names in both local folders, DOI/title/hash-associated legacy document catalog and collection library, matching download logs, all seven main pages. No arbitrary-alias whole-corpus PDF parsing or external lookup. Missing candidate is not proof publisher SI never existed.'},'source_identity_complete_for_supplied_main':True,'scientific_review_complete':False,'published':False}
assert all(f['stat_stable_during_hash'] for f in files)
(B/'source-identity.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'source-identity.md').write_text('# Yao et al.1998: local source identity\n\n'+TITLE+'\n\nHiroshi Yao, Yukako Takada and Noboru Kitamura. Langmuir1998,14(3),595–601. DOI10.1021/la970480g. Source ID yao1998. Seven supplied main pages were visually checked.1997 in the article code and received/final dates is not the publication year.\n\nMain SHA256: '+expected+'\n\n'+ '\n'.join('- '+f['path']+' — '+f['role']+', '+str(f['bytes'])+' bytes.' for f in files)+'\n\nSI not located or verified. Targeted local filename, catalog association, hash, title and log checks are detailed in source-identity.json. Existing paper/document IDs should be reused. Identity verification does not establish extraction, browser integration or publication completion.\n',encoding='utf8')
print(json.dumps({'source_id':out['source_id'],'copies':out['main_copy_count'],'unique_contents':out['unique_main_content_count'],'papers':out['existing_identity']['papers'],'documents':caches,'si_status':out['si']['status'],'unverified':out['unverified_file_candidates']},indent=2))
