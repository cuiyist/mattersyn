"""Bounded local identity reconciliation; no source, Site or queue writes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re, subprocess, shutil

B=Path(__file__).resolve().parent
MAT=B.parents[3]
SITE=MAT/'recipe-atlas'
CORPUS=MAT/'research-assets/corpus-20260917'
DOI='10.1021/cm9503137'
EXPECTED='cde428b3707ab7e0fe1a24cd747e6c884d6903265d4d745a93e36d60e553321f'
TITLE='Synthesis of Luminescent Thin-Film CdSe/ZnSe Quantum Dot Composites Using CdSe Quantum Dots Passivated with an Overlayer of ZnSe'
ROOTS={'incoming':Path('[local path redacted]'),'legacy':MAT/'downloaded_papers'}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return re.sub(r'[^a-z0-9]','',(s or '').lower())
def stamp():return datetime.now(timezone.utc).isoformat()
def actual(p,root):
    before=p.stat();digest=sha(p);after=p.stat()
    stable=(before.st_size,before.st_mtime_ns,before.st_birthtime_ns)==(after.st_size,after.st_mtime_ns,after.st_birthtime_ns)
    assert stable and digest==EXPECTED
    return {'source_root':root,'path':str(p),'filename':p.name,'role':'main','role_basis':'Eight-page journal main article verified against native page count and rendered title/final pages','bytes':before.st_size,'mtime_ns':before.st_mtime_ns,'birthtime_ns':before.st_birthtime_ns,'sha256':digest,'actual_hash_computed_utc':stamp(),'stat_stable_during_hash':stable}

def main():
    manifest_path=CORPUS/'private/document-manifest.json'
    manifest=read(manifest_path)
    library=read(SITE/'data/corpus/library-source.json')
    queue=read(MAT/'research-assets/incoming-paper-monitor/ledger.json')
    docs=[d for d in manifest['documents'] if d.get('sha256')==EXPECTED or any((a.get('doi') or '').lower()==DOI for a in d.get('paperAssociations',[])) or norm((d.get('likelyTitle') or {}).get('value',''))==norm(TITLE)]
    papers=[p for p in library['papers'] if p.get('doi','').lower()==DOI or norm(p.get('title',''))==norm(TITLE)]
    assert len(docs)==1 and len(papers)==1
    doc,paper=docs[0],papers[0]
    filenames={k:[p for p in root.rglob('*') if p.is_file() and 'cm9503137' in p.name.lower()] for k,root in ROOTS.items()}
    local_files=[actual(p,k) for k,paths in filenames.items() for p in paths]
    assert len(local_files)==2
    legacy=next(x for x in local_files if x['source_root']=='legacy')
    textpath=CORPUS/doc['textPath'];text=textpath.read_text(encoding='utf-8')
    main=next(x for x in local_files if x['source_root']=='incoming')
    info=subprocess.run([shutil.which('pdfinfo'),main['path']],capture_output=True,text=True,check=True).stdout
    page_count=int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1))
    assert page_count==8==doc['pageCount']
    logs=[]
    for root,folder in ROOTS.items():
        for p in sorted(folder.glob('*.jsonl')):
            with p.open(encoding='utf-8',errors='replace') as f:
                for n,line in enumerate(f,1):
                    if 'cm9503137' in line.lower():
                        try:value=json.loads(line)
                        except json.JSONDecodeError:value={'unparsed_matching_line':line.strip()}
                        logs.append({'source_root':root,'path':str(p),'line':n,'entry':value})
    exact=[];mentions=[];reviews=[]
    for p in sorted((SITE/'data/records').glob('*.json')):
        r=read(p)
        if any(s.get('doi','').lower()==DOI for s in r.get('sources',[])):
            mentions.append(r['record_id'])
            if any(s.get('doi','').lower()==DOI and s['id']==r['lineage']['source_group'] for s in r['sources']):exact.append(r['record_id'])
    for p in sorted((SITE/'data/paper-reviews').glob('*.json')):
        r=read(p)
        if r.get('doi','').lower()==DOI:reviews.append(r['paper_id'])
    public_paper=read(SITE/'dist/data/papers'/f'{paper["id"]}.json')
    group=queue['groups']['10.1021_cm9503137']
    terms=['supporting information','supplementary','supplemental','microfiche','information available']
    fresh='\n'.join((B/f'plain-page-{i}.txt').read_text(encoding='utf-8') for i in range(1,9))
    result={
      'schema':'mattersyn-local-source-identity-1','checked_utc':stamp(),
      'scope':'Bounded local source identity, duplicate-copy and SI-candidate reconciliation only. Root separately reads and extracts the scientific content. No download, queue mutation or Site write.',
      'doi':DOI,'title':TITLE,'authors':['Michal Danek','Klavs F. Jensen','Chris B. Murray','Moungi G. Bawendi'],'corresponding_authors':['Klavs F. Jensen'],
      'journal':'Chemistry of Materials','journal_abbreviation':'Chem. Mater.','year':1996,'volume':8,'issue':1,'printed_pages':{'first':173,'last':180},'pdf_page_count':page_count,
      'identity_evidence':[
        {'locator':'Main PDF p. 1, printed p. 173','method':'Rendered-page visual inspection','supports':['exact title','four authors','corresponding author marker','year 1996','volume 8','pagination 173–180','received/revised/advance abstract dates'],'render_sha256':sha(B/'main-1.png')},
        {'locator':'Main PDF p. 8, printed p. 180','method':'Rendered-page visual inspection','supports':['volume 8, issue 1, year 1996','final page 180','article code CM9503137','closing acknowledgments and no displayed SI declaration'],'render_sha256':sha(B/'main-8.png')},
        {'locator':'Native PDF page information and hash-bound corpus manifest','method':'pdfinfo and verified source file metadata/hash','supports':['eight native PDF pages','427513 bytes','unencrypted PDF 1.4']}
      ],
      'doi_binding':{'status':'corroborated_local_identity','basis':['Both supplied filenames encode 10.1021/cm9503137.','Legacy DOI/document association and download log map this title and PDF to this DOI.','Printed final-page manuscript code CM9503137 matches the DOI suffix.'],'full_doi_string_found_in_main_text':DOI in text.lower() or DOI in fresh.lower(),'external_publisher_resolution_performed':False},
      'printed_dates':{'received':'July 10, 1995','revised_manuscript_received':'October 5, 1995','abstract_advance_publication':'November 15, 1995','locator':'Main PDF p. 1, title block and bottom footnote','note':'Article publication year is 1996. Received/revised and advance-abstract dates do not replace the journal issue year. PDF file creation/modification dates are not publication or folder arrival dates.'},
      'local_files':local_files,'known_main_copy_count':2,'unique_main_content_count':1,'main_sha256':EXPECTED,
      'si':{'status':'not_located_or_verified','matched_local_si_count':0,'main_si_duplicate_count':0,'declaration_search_terms_and_hit_counts':{t:len(re.findall(re.escape(t),text,re.I)) for t in terms},'fresh_main_extraction_si_term_hit_counts':{t:len(re.findall(re.escape(t),fresh,re.I)) for t in terms},'closing_matter_visually_checked':True,'claim':'No SI candidate was located by local filename, DOI-associated corpus/queue metadata, title candidate, cached hash alias, or download-log searches. The legacy successful download entry records an empty SI list. No SI declaration search terms appear in either cached or fresh main extraction. This does not prove that SI never existed.','limits':'No downloads, whole-corpus re-extraction, or content search of every unindexed or arbitrarily named incoming file was performed. Unknown unindexed aliases cannot be excluded.'},
      'cached_identity_reuse':{'manifest_document_id':doc['id'],'manifest_path':str(manifest_path),'main_text_path':str(textpath),'main_text_sha256':sha(textpath),'cached_text_characters':len(text),'legacy_size_mtime_exact_match':doc['fingerprint']=={'bytes':legacy['bytes'],'mtimeNs':legacy['mtime_ns']},'cached_sha256_matches_both_actual_files':all(f['sha256']==doc['sha256'] for f in local_files),'manifest_same_hash_matches':[{'document_id':d['id'],'filename':d['sourceRelativeFilename']} for d in manifest['documents'] if d.get('sha256')==EXPECTED],'evidence_candidate_path':str(CORPUS/doc['evidenceCandidatePath']),'candidate_extraction_not_reviewed':True},
      'existing_identity':{'paper_id':paper['id'],'document_id':doc['id'],'library_title_candidate':paper['titleMetadata'],'library_year_before_review':paper['year'],'title_matched_groups':[{'paper_id':p['id'],'doi':p['doi']} for p in papers],'public_library_status':public_paper.get('reviewStatus'),'public_library_materials':public_paper.get('materials'),'canonical_record_ids':exact,'contextual_canonical_mentions':mentions,'formal_review_ids':reviews,'existing_local_public_paper_route':'paper.html?id='+paper['id'],'deployment_checked':False,'recommended_metadata_update':'Retain the existing paper/document IDs. Upgrade title and year provenance from extraction heuristic to rendered first/final-page verification during integration. Do not create a new paper identity for the incoming byte-identical copy.'},
      'download_log_evidence':logs,
      'queue_read_only_observation':{'group_id':'10.1021_cm9503137','queue_order':group['queue_order'],'generation':group['generation'],'fingerprint_generation':group.get('fingerprint',{}).get('generation'),'reconciliation_requires_refingerprint':group['generation']!=group.get('fingerprint',{}).get('generation'),'files':[{'key':k,'role':queue['files'][k]['role'],'source_id':queue['files'][k]['source_id'],'sha256':queue['files'][k].get('sha256')} for k in group['files']],'confirmed_aliases':{k:v for k,v in queue['group_aliases'].items() if 'cm9503137' in k or 'cm9503137' in str(v)},'note':'Queue inspected read-only. Its generation and selected-group fingerprint already agree; this identity check does not change claim, milestone or completion state.'},
      'scientific_review_complete':False,'source_identity_complete_for_supplied_main':True,'published':False
    }
    assert result['cached_identity_reuse']['legacy_size_mtime_exact_match']
    assert result['cached_identity_reuse']['cached_sha256_matches_both_actual_files']
    (B/'source-identity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Local source identity: Danek et al. (1996)','',f'Checked: {result["checked_utc"]}','',f'**{TITLE}.** Michal Danek, Klavs F. Jensen, Chris B. Murray and Moungi G. Bawendi. *Chemistry of Materials* **1996**, 8(1), 173–180. DOI candidate bound to local source: `{DOI}`.','',
      'The first and final rendered pages confirm title, authors, journal issue, eight-page extent and final manuscript code **CM9503137**. The full DOI is not printed in the extracted text; filenames, local corpus association and successful download log corroborate its binding. No external publisher resolution was performed.','',
      '**Two local files are one main-article content**, independently rehashed with unchanged pre/post file metadata:', '',
      *[f'- `{f["path"]}` — {f["bytes"]:,} bytes.' for f in local_files], '',f'SHA-256 for both: `{EXPECTED}`.','',
      '**SI: not located or verified.** No matching SI filename, DOI-associated document, title alias, cached same-hash alias or local download-log entry was found. The legacy `_download_log.jsonl` entry explicitly records `si: []`; this is a download result, not proof of publisher absence. No SI declaration terms were found in the cached or fresh main extraction; closing matter was visually checked. Arbitrarily named/unindexed files were not exhaustively content-searched.','',
      f'Reuse existing paper ID `{paper["id"]}` and document ID `{doc["id"]}`. No prior primary canonical records or formal source review was present at this snapshot. The public local source page was `{public_paper.get("reviewStatus")}`. Title/year metadata remain candidate provenance until root integration upgrades them.','',
      f'Hash-verified cached text: `{textpath}`. Its recorded legacy bytes/mtime match the actual file exactly. The cached extraction and its evidence candidates are indexes, not a completed scientific review.','',
      f'Queue order {group["queue_order"]}; generation {group["generation"]}; fingerprint generation {group.get("fingerprint",{}).get("generation")}. The legacy alias is already reconciled. Queue/claim/source/Site files were not changed.','',
      'Received July 10, 1995; revised October 5, 1995; advance abstract November 15, 1995. The journal publication year is **1996**. PDF metadata dates and download dates do not replace that year.','',
      'This report completes supplied-main identity reconciliation only. Full scientific extraction, sample verification, reader integration, final review and publication are separate tasks.'
    ]
    (B/'source-identity.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'status':'identity_reconciled','paper_id':paper['id'],'document_id':doc['id'],'main_copies':len(local_files),'unique_main_hashes':len({f['sha256'] for f in local_files}),'matched_si':0,'pages':page_count,'canonical_records':exact,'formal_reviews':reviews,'json_sha256':sha(B/'source-identity.json')},ensure_ascii=False))

if __name__=='__main__':main()
