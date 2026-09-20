"""Targeted local Stiger source identity; no Site or source writes."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re
from pypdf import PdfReader
B=Path(__file__).resolve().parent;M=B.parents[3];C=M/'research-assets/corpus-20260917';SITE=M/'recipe-atlas'
DOI='10.1021/la980800b';TITLE='Investigations of Electrochemical Silver Nanocrystal Growth on Hydrogen-Terminated Silicon(100)'
MAIN=Path('[local path redacted]')
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(x):return re.sub('[^a-z0-9]','',str(x or '').lower())
expected=sha(MAIN);assert expected=='e581449713ddca5e0cb68d05593df476d0e5150b88bc7c6dcbdb269ac70881fb'
reader=PdfReader(MAIN);manifest=read(C/'private/document-manifest.json');lib=read(SITE/'data/corpus/library-source.json')
docs=[d for d in manifest['documents']if d.get('sha256')==expected or any(x.get('doi','').lower()==DOI for x in d.get('paperAssociations',[]))or norm((d.get('likelyTitle')or{}).get('value'))==norm(TITLE)]
papers=[p for p in lib['papers']if p.get('doi','').lower()==DOI or norm(p.get('title'))==norm(TITLE)]
roots={'incoming':MAIN.parent,'legacy':M/'downloaded_papers'};paths={}
for k,root in roots.items():
 for p in root.rglob('*980800*'):
  if p.is_file():paths[str(p)]=(k,p)
for d in docs:
 p=roots['legacy']/d['sourceRelativeFilename']
 if p.exists():paths[str(p)]=('legacy',p)
files=[]
for k,p in paths.values():
 s=p.stat();h=sha(p);t=p.stat();files.append({'root':k,'path':str(p),'basename':p.name,'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'birthtime_ns':s.st_birthtime_ns,'sha256':h,'stat_stable_during_hash':(s.st_size,s.st_mtime_ns)==(t.st_size,t.st_mtime_ns),'role':'main'if h==expected else'unverified_candidate'})
logs=[]
for k,root in roots.items():
 for p in root.glob('*.jsonl'):
  for n,line in enumerate(p.open(encoding='utf8',errors='replace'),1):
   if 'la980800b'in line.lower():
    try:entry=json.loads(line)
    except json.JSONDecodeError:entry={'unparsed':line.strip()}
    logs.append({'root':k,'basename':p.name,'line':n,'entry':entry})
text='\n'.join((B/f'page-{n}.txt').read_text(encoding='utf8')for n in range(1,10))
caches=[{'document_id':d['id'],'filename':d['sourceRelativeFilename'],'sha256':d['sha256'],'page_count':d['pageCount'],'cached_text_sha256':sha(C/d['textPath']),'matching_current_content':d['sha256']==expected,'cached_extraction_is_not_full_review':True}for d in docs]
existing=[]
for p in(SITE/'data/records').glob('*.json'):
 r=read(p)
 if any(s.get('doi','').lower()==DOI for s in r.get('sources',[])):existing.append(r['record_id'])
out={'schema':'mattersyn-local-source-identity-1','checked_utc':datetime.now(timezone.utc).isoformat(),'source_id':'stiger1999','doi':DOI,'title':TITLE,'authors':['R. M. Stiger','S. Gorer','B. Craft','R. M. Penner'],'corresponding_author':'R. M. Penner','journal':'Langmuir','year':1999,'volume':15,'issue':3,'printed_pages':[790,798],'pdf_page_count':len(reader.pages),'dates':{'received':'1998-07-01','final_form':'1998-10-27','published_web':'1998-12-09'},'main_sha256':expected,'pdf_metadata':dict(reader.metadata or {}),'identity_evidence':[{'locator':'Main PDF p.1, printed p.790: title, byline, journal banner, received/final dates, DOI and Web-publication footer','supports':['Title and four authors as initialed in source','Langmuir1999,15,790–798','Manuscript and online dates in1998 do not override journal year1999','Full DOI10.1021/la980800b'],'render_sha256':sha(B/'page-1.png')},{'locator':'Main PDF pp.2–9: running headers and closing code LA980800B','supports':['Issue3','Last printed page798','Matching terminal article code'],'render_sha256':sha(B/'page-9.png')}],'doi_binding':{'status':'verified_in_main_content','full_doi_in_extracted_main':DOI in text.lower(),'basis':'Printed first-page DOI, title, byline, running headers and closing article code corroborate local catalog association; filename is not sole identity evidence.'},'local_files':files,'main_copy_count':sum(f['role']=='main'for f in files),'unique_main_content_count':len({f['sha256']for f in files if f['role']=='main'}),'unverified_file_candidates':[f['path']for f in files if f['role']!='main'],'cached_identity_reuse':caches,'existing_identity':{'papers':[{'paper_id':p['id'],'title':p['title'],'year':p.get('year'),'year_correction':1999 if p.get('year')!=1999 else None}for p in papers],'canonical_records':existing},'download_log_evidence':logs,'si':{'status':'not_located_or_verified','matched_local_si_count':0,'declaration_term_hits':{s:len(re.findall(re.escape(s),text,re.I))for s in ['supporting information','supplementary','supplemental','microfiche','information available']},'scope':'Targeted basename in both local paper folders; DOI/title/hash-associated legacy catalog and collection-library candidates; matching root download logs; all nine supplied main pages. No arbitrary-alias entire-corpus PDF parsing or external search. Missing candidate is not proof SI never existed.'},'source_identity_complete_for_supplied_main':True,'scientific_review_complete':False,'published':False}
assert all(f['stat_stable_during_hash']for f in files)
(B/'source-identity.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'source-identity.md').write_text('# Stiger et al.1999: source identity\n\n'+TITLE+'\n\nR. M. Stiger, S. Gorer, B. Craft and R. M. Penner. Langmuir1999,15(3),790–798. DOI10.1021/la980800b. Nine main pages. Web publication was December9,1998; received July1 and final form October27,1998. Journal year is1999, correcting the legacy1997 guess.\n\nSHA256: '+expected+'\n\n'+ '\n'.join('- '+f['path']+' — '+f['role']for f in files)+'\n\nTwo byte-identical main copies; SI not located or verified. Reuse paper-1cd45a74373c35ebff89 and doc-ce850b8a9d096607f50b. Targeted local evidence and limitations are recorded in JSON. No Site changes or publication claim.\n',encoding='utf8')
print(json.dumps({'copies':out['main_copy_count'],'unique_contents':out['unique_main_content_count'],'papers':out['existing_identity']['papers'],'documents':caches,'si':out['si']['status'],'unverified':out['unverified_file_candidates']},indent=2))
