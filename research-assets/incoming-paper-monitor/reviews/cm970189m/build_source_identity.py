"""Read-only targeted local reconciliation; private outputs only."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re
B=Path(__file__).resolve().parent;MAT=B.parents[3];SITE=MAT/'recipe-atlas';C=MAT/'research-assets/corpus-20260917'
DOI='10.1021/cm970189m';EXPECTED='eac4fe78e4bc3ab9c15e0409b69232e4294a0c07787d3ca650c378f6341d4adc'
TITLE='Surface Functionalization of Cadmium Sulfide Quantum-Confined Nanoclusters. 3. Formation and Derivatives of a Surface Phenolic Quantum Dot'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return re.sub('[^a-z0-9]','',(s or '').lower())
def main():
 roots={'legacy':MAT/'downloaded_papers','incoming':Path('[local path redacted]')}
 manifest=read(C/'private/document-manifest.json');library=read(SITE/'data/corpus/library-source.json')
 docs=[d for d in manifest['documents'] if d.get('sha256')==EXPECTED or any(a.get('doi','').lower()==DOI for a in d.get('paperAssociations',[])) or norm((d.get('likelyTitle') or {}).get('value',''))==norm(TITLE)]
 papers=[p for p in library['papers'] if p.get('doi','').lower()==DOI or norm(p.get('title',''))==norm(TITLE)]
 paths={}
 for rid,root in roots.items():
  for p in root.rglob('*cm970189m*'):
   if p.is_file() and '_test_out' not in p.parts:paths[str(p)]=(rid,p)
 for d in docs:
  p=roots['legacy']/d['sourceRelativeFilename']
  if p.exists():paths[str(p)]=('legacy',p)
 files=[]
 for rid,p in paths.values():
  s=p.stat();h=sha(p);t=p.stat()
  files.append({'root':rid,'path':str(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'birthtime_ns':s.st_birthtime_ns,'sha256':h,'stat_stable_during_hash':(s.st_size,s.st_mtime_ns)==(t.st_size,t.st_mtime_ns),'role':'main' if h==EXPECTED else 'unverified_candidate'})
 logs=[]
 for rid,root in roots.items():
  for p in root.glob('*.jsonl'):
   for n,line in enumerate(p.open(encoding='utf-8',errors='replace'),1):
    if 'cm970189m' in line.lower():
     try:e=json.loads(line)
     except json.JSONDecodeError:e={'unparsed':line.strip()}
     logs.append({'root':rid,'filename':p.name,'line':n,'entry':e})
 primary=[];context=[];reviews=[]
 for p in (SITE/'data/records').glob('*.json'):
  r=read(p);ids=[s['id'] for s in r.get('sources',[]) if s.get('doi','').lower()==DOI]
  if ids:
   context.append(r['record_id'])
   if r['lineage']['source_group'] in ids:primary.append(r['record_id'])
 for p in (SITE/'data/paper-reviews').glob('*.json'):
  r=read(p)
  if r.get('doi','').lower()==DOI:reviews.append(r['paper_id'])
 caches=[]
 for d in docs:
  p=C/d['textPath'];f=next((f for f in files if f['root']=='legacy' and Path(f['path']).name==d['sourceRelativeFilename']),None)
  caches.append({'document_id':d['id'],'filename':d['sourceRelativeFilename'],'sha256':d['sha256'],'page_count':d['pageCount'],'text_path':str(p),'text_sha256':sha(p),'exact_size_mtime_match':bool(f and d['fingerprint']=={'bytes':f['bytes'],'mtimeNs':f['mtime_ns']}),'candidate_extraction_is_not_reviewed':True})
 text='\n'.join((B/f'plain-page-{i}.txt').read_text(encoding='utf-8') for i in range(1,7))
 result={'schema':'mattersyn-local-source-identity-1','checked_utc':datetime.now(timezone.utc).isoformat(),'source_id':'veinot1997','doi':DOI,'title':TITLE,'authors':['Jonathan G. C. Veinot','Madlen Ginzburg','William J. Pietro'],'corresponding_author':'William J. Pietro','journal':'Chemistry of Materials','year':1997,'volume':9,'issue':10,'printed_pages':[2117,2122],'pdf_page_count':6,'main_sha256':EXPECTED,'identity_evidence':[{'locator':'Main PDF p. 1, printed p. 2117, title and first-page footnotes','supports':['Full title and authors','Chem. Mater. 1997,9,2117–2122','Received April 2,1997; revised July 25,1997; advance abstract September 1,1997','Article code S0897-4756(97)00189-0'],'render_sha256':sha(B/'main-01.png')},{'locator':'Main PDF p. 6, printed p. 2122, closing page','supports':['Issue10','Final page2122','Terminal article code CM970189M','References and notes through15; no displayed SI declaration'],'render_sha256':sha(B/'main-06.png')}],'doi_binding':{'status':'local_metadata_corroborated','full_doi_found_in_extracted_main':DOI in text.lower(),'basis':'Matching local DOI associations/download metadata and printed terminal article code CM970189M. No external lookup performed.'},'local_files':files,'main_copy_count':sum(f['sha256']==EXPECTED for f in files),'unique_main_content_count':len({f['sha256'] for f in files if f['role']=='main'}),'unverified_file_candidates':[f['path'] for f in files if f['role']!='main'],'cached_identity_reuse':caches,'existing_identity':{'papers':[{'paper_id':p['id'],'title':p['title'],'year':p.get('year')} for p in papers],'primary_canonical_record_ids':primary,'contextual_canonical_mentions':context,'formal_source_review_ids':reviews},'download_log_evidence':logs,'si':{'status':'not_located_or_verified','matched_local_si_count':0,'declaration_term_hits':{s:len(re.findall(re.escape(s),text,re.I)) for s in ['supporting information','supplementary','supplemental','microfiche','information available']},'scope':'Targeted filenames across both authorized folders, DOI/title/hash-associated legacy manifest, cached text and matching download logs. All six supplied main pages read and visually checked. No whole-corpus OCR or external downloads. Absence of a candidate does not establish publisher SI absence; arbitrary unindexed aliases cannot be excluded.'},'source_identity_complete_for_supplied_main':True,'scientific_review_complete':False,'published':False}
 assert files and all(f['stat_stable_during_hash'] for f in files)
 (B/'source-identity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 lines=['# Veinot et al. 1997: local source identity','',f'**{TITLE}**. *Chem. Mater.* **1997**,9(10),2117–2122. DOI `{DOI}`. Canonical source ID `veinot1997`.','',f'Six supplied main pages. {result["main_copy_count"]} actual hashed main copies / {result["unique_main_content_count"]} unique main content. SHA256 `{EXPECTED}`.','',*[f'- `{f["path"]}` — {f["bytes"]:,} bytes; {f["role"]}.' for f in files],'',f'Existing local identities: {result["existing_identity"]}. Reuse these paper/document IDs. Cached source matches: {caches}.','','SI **not located or verified**. Targeted local names, DOI/title/hash associations, cached text and logs checked. This is not proof SI does not exist. No external lookup, download, source, Site or queue mutation.','','Identity is supported by the visually checked title page and terminal CM970189M code; the full DOI is not printed in extracted main text. All six pages have been inspected, but scientific extraction, canonical audit, reader review and publication are separate gates.']
 (B/'source-identity.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps({'source_id':'veinot1997','main_copies':result['main_copy_count'],'unverified_candidates':result['unverified_file_candidates'],'papers':result['existing_identity']['papers'],'documents':[d['document_id'] for d in caches],'existing_primary_records':primary,'existing_reviews':reviews,'si_status':result['si']['status'],'identity_sha256':sha(B/'source-identity.json')},ensure_ascii=False))
if __name__=='__main__':main()
