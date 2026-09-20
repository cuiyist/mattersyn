"""Read-only bounded local source reconciliation; outputs private reports only."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re
B=Path(__file__).resolve().parent
MAT=B.parents[3]; SITE=MAT/'recipe-atlas'; C=MAT/'research-assets/corpus-20260917'
DOI='10.1021/jp971091y'; EXPECTED='dac183303049a3275d4f1874c66ac0ceece9895bc175f7f7e9727ef7c9cd8f9d'
TITLE='(CdSe)ZnS Core–Shell Quantum Dots: Synthesis and Characterization of a Size Series of Highly Luminescent Nanocrystallites'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(v):return re.sub('[^a-z0-9]','',(v or '').lower())
def main():
    roots={'legacy':MAT/'downloaded_papers','incoming':Path('[local path redacted]')}
    manifest=read(C/'private/document-manifest.json'); library=read(SITE/'data/corpus/library-source.json');queue=read(MAT/'research-assets/incoming-paper-monitor/ledger.json')
    docs=[d for d in manifest['documents'] if d.get('sha256')==EXPECTED or any(a.get('doi','').lower()==DOI for a in d.get('paperAssociations',[])) or norm((d.get('likelyTitle') or {}).get('value',''))==norm(TITLE)]
    papers=[p for p in library['papers'] if p.get('doi','').lower()==DOI or norm(p.get('title',''))==norm(TITLE)]
    paths={}
    for rid,root in roots.items():
        for p in root.rglob('*jp971091y*'):
            if p.is_file() and '_test_out' not in p.parts:paths[str(p)]=(rid,p)
    for d in docs:
        p=roots['legacy']/d['sourceRelativeFilename']
        if p.exists():paths[str(p)]=('legacy',p)
    files=[]
    for rid,p in paths.values():
        s=p.stat(); h=sha(p); t=p.stat();stable=(s.st_size,s.st_mtime_ns)==(t.st_size,t.st_mtime_ns)
        files.append({'root':rid,'path':str(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'birthtime_ns':s.st_birthtime_ns,'sha256':h,'stat_stable_during_hash':stable,'role':'main' if h==EXPECTED else 'unverified_candidate'})
    logs=[]
    for rid,root in roots.items():
        for p in root.glob('*.jsonl'):
            for n,line in enumerate(p.open(encoding='utf-8',errors='replace'),1):
                if 'jp971091y' in line.lower():
                    try:e=json.loads(line)
                    except json.JSONDecodeError:e={'unparsed':line.strip()}
                    logs.append({'root':rid,'filename':p.name,'line':n,'entry':e})
    records=[];context=[];reviews=[]
    for p in (SITE/'data/records').glob('*.json'):
        r=read(p);ids=[s['id'] for s in r.get('sources',[]) if s.get('doi','').lower()==DOI]
        if ids:
            context.append(r['record_id'])
            if r['lineage']['source_group'] in ids:records.append(r['record_id'])
    for p in (SITE/'data/paper-reviews').glob('*.json'):
        r=read(p)
        if r.get('doi','').lower()==DOI:reviews.append(r['paper_id'])
    text='\n'.join((B/f'plain-page-{i}.txt').read_text(encoding='utf-8') for i in range(1,14))
    caches=[]
    for d in docs:
        p=C/d['textPath'];f=next((f for f in files if f['root']=='legacy' and Path(f['path']).name==d['sourceRelativeFilename']),None)
        caches.append({'document_id':d['id'],'filename':d['sourceRelativeFilename'],'sha256':d['sha256'],'page_count':d['pageCount'],'text_path':str(p),'text_sha256':sha(p),'exact_size_mtime_match':bool(f and d['fingerprint']=={'bytes':f['bytes'],'mtimeNs':f['mtime_ns']}),'candidate_extraction_is_not_reviewed':True})
    g=queue['groups'].get('10.1021_jp971091y',{})
    result={'schema':'mattersyn-local-source-identity-1','checked_utc':datetime.now(timezone.utc).isoformat(),'source_id':'dabbousi1997','doi':DOI,'title':TITLE,'authors':['B. O. Dabbousi','J. Rodriguez-Viejo','F. V. Mikulec','J. R. Heine','H. Mattoussi','R. Ober','K. F. Jensen','M. G. Bawendi'],'corresponding_author':'M. G. Bawendi','journal':'The Journal of Physical Chemistry B','year':1997,'volume':101,'issue':46,'printed_pages':[9463,9475],'pdf_page_count':13,'main_sha256':EXPECTED,'identity_evidence':[{'locator':'Main PDF p. 1 (printed 9463), visually inspected','supports':['title','authors','journal/year/volume/pages','received March 27,1997','final form June26,1997','advance abstract September1,1997'],'render_sha256':sha(B/'main-01.png')},{'locator':'Main PDF p.13 (printed9475), visually inspected','supports':['issue46','lastpage9475','conclusion, acknowledgments, references and notes1–40','no displayed SI declaration'],'render_sha256':sha(B/'main-13.png')}],'doi_binding':{'status':'local_metadata_corroborated','full_doi_found_in_extracted_main':DOI in text.lower(),'basis':'Both named local source files and legacy DOI association/download log match this main article. Title-page journal article code S1089-5647(97)01091-2 is consistent with suffix. No external resolution performed.'},'local_files':files,'main_copy_count':sum(f['sha256']==EXPECTED for f in files),'unique_main_content_count':len({f['sha256'] for f in files if f['role']=='main'}),'unverified_file_candidates':[f['path'] for f in files if f['role']!='main'],'cached_identity_reuse':caches,'existing_identity':{'papers':[{'paper_id':p['id'],'title':p['title'],'year':p.get('year')} for p in papers],'primary_canonical_record_ids':records,'contextual_canonical_mentions':context,'formal_source_review_ids':reviews},'download_log_evidence':logs,'si':{'status':'not_located_or_verified','matched_local_si_count':0,'declaration_term_hits':{s:len(re.findall(re.escape(s),text,re.I)) for s in ['supporting information','supplementary','supplemental','microfiche','information available']},'scope':'Local matching filenames, DOI/title/hash-associated legacy manifest, main first/final pages, cached text, download logs and queue aliases. No whole-corpus OCR or external downloads. Empty SI download list and absence of local candidates do not prove publisher absence.'},'queue_read_only_observation':{'group_id':'10.1021_jp971091y','queue_order':g.get('queue_order'),'generation':g.get('generation'),'fingerprint_generation':g.get('fingerprint',{}).get('generation'),'aliases':{k:v for k,v in queue['group_aliases'].items() if 'jp971091y' in k or 'jp971091y' in str(v)}},'source_identity_complete_for_supplied_main':True,'scientific_review_complete':False,'published':False}
    assert files and all(f['stat_stable_during_hash'] for f in files)
    (B/'source-identity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Dabbousi et al.1997: local source identity','',f'**{TITLE}**. *J. Phys. Chem. B* **1997**,101(46),9463–9475. DOI `{DOI}`. Proposed canonical source ID: `dabbousi1997`.','',f'Thirteen main pages; {result["main_copy_count"]} actual hashed copies / {result["unique_main_content_count"]} unique main content. SHA256 `{EXPECTED}`.','',*[f'- `{f["path"]}`: {f["bytes"]:,} bytes; {f["role"]}.' for f in files],'','Title and closing pages visually checked. Full DOI is not printed in main extraction; DOI association is corroborated by local catalog/download records and matching source identity. Dates: received March27,1997; final form June26,1997; advance abstract September1,1997.','',f'Existing identity: `{result["existing_identity"]}`. Reuse existing paper/document IDs rather than adding another identity for the same main bytes.','','SI **not located or verified**. Matching local filenames, manifest DOI/title/hash associations, logs and queue aliases were checked. This is not proof no SI exists; arbitrary unindexed aliases cannot be excluded.','',f'Cached text records: `{caches}`.','',f'Local log matches: {len(logs)}. No Site/source/queue mutations or downloads. This report is identity reconciliation only; scientific extraction, reader audit and publication have separate gates.']
    (B/'source-identity.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'source_id':'dabbousi1997','copies':len(files),'papers':result['existing_identity']['papers'],'document_ids':[x['document_id'] for x in caches],'existing_canonical':records,'existing_reviews':reviews,'si':result['si'],'sha256':sha(B/'source-identity.json')},ensure_ascii=False))
if __name__=='__main__':main()
