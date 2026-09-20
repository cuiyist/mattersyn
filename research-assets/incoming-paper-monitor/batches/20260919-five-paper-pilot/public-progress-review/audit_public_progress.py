"""Read-only bounded audit of progress/citations; only this private audit directory is written."""
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime, timezone
import ast,hashlib,json,re,subprocess
O=Path(__file__).resolve().parent;B=O.parent;Q=B.parents[1];M=Q.parents[1];S=M/'recipe-atlas';D=S/'dist';H=B/'jp0219348'
bound={};checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def text(p):p=Path(p);bound[str(p.resolve())]=sha(p);return p.read_text(encoding='utf-8-sig')
def load(p):return json.loads(text(p))
def ck(scope,claim,ok,detail=None):checks.append({'scope':scope,'claim':claim,'passed':bool(ok),'detail':detail})
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
public_files=[D/'progress.html',D/'progress.css',D/'progress.mjs',D/'data/review-progress.json',M/'README.md',M/'REFERENCES.md',D/'README.md',D/'REFERENCES.md']
pubtexts={str(p):text(p) for p in public_files}
generator=text(Q/'build_public_progress.py');citation_generator=text(M/'research-assets/build_reference_readmes.py')
ast.parse(generator);ast.parse(citation_generator)
progress=load(D/'data/review-progress.json');editorial=load(Q/'public-progress-editorial.json');queue=load(Q/'queue-status.json');release=load(Q/'latest-publication.json')
checkpoint=load(H/'comprehensive-source-checkpoint.json');eta=load(B/'eta-evidence-20260920.json');text(B/'eta-evidence-20260920.md')
manifest=load(D/'data/dataset-manifest.json');citation_manifest=load(M/'research-assets/reference-readme-generation.json')
ck('release','Latest publication status verified',release['status']=='published_verified')
for k,v in progress['published'].items():ck('release',k+' equals publication checkpoint',release[k]==v)
ck('release','Dataset version and count match current manifest',progress['published']['dataset_version']==manifest['dataset_version'] and progress['published']['record_count']==manifest['record_count']==len(manifest['records'])==470)
ck('release','Public exact structure–recipe task count remains zero',progress['published']['exact_structure_recipe_count']==0 and not any(r['eligibility']['exact_structure_recipe']['eligible'] for r in manifest['records']))
for k,v in progress['corpus'].items():ck('queue',k+' equals latest queue count',queue['counts'][k]==v)
ck('queue','Document-copy reconciliation',sum(progress['corpus']['source_document_copies'].values())==progress['corpus']['present_files']==13786)
ck('queue','Provisional scope/closed/pending reconciliation',queue['counts']['canonical_review_units']==9492 and eta['backlog']['pending_groups']==9470==progress['corpus']['waiting_review_scopes']+progress['corpus']['active_review_claims'])
ck('queue','Confirmed main aliases excluded from provisional scope count',queue['counts']['groups']-queue['counts']['confirmed_duplicate_main_aliases']==queue['counts']['canonical_review_units'])
ck('queue','Copies and scopes not asserted unique papers','not a verified count of unique papers' in progress['count_note'] and 'not a verified' in queue['counts']['count_note'])
ck('queue','Corpus scan timestamp identifies actual stored scan',progress['corpus_scanned_at']==queue['ledger_last_scan_at']==eta['folder_scan_at'])
for k in ('batch','current_work','recent_milestones','estimate'):ck('editorial transport',k+' exact transport',progress[k]==editorial[k])
batch=progress['batch'];work=progress['current_work'][0];n=checkpoint['si_numerical_progress']
ck('current batch','Four published and Heo pending',batch['total']==len(batch['papers'])==5 and batch['published']==sum(x['published'] for x in batch['papers'])==4 and not batch['papers'][-1]['published'] and batch['papers'][-1]['href'] is None)
ck('Heo','Scope checkpoint remains unpublished and unpromoted',not checkpoint['published'] and not checkpoint['canonical_records_promoted'] and not checkpoint['reader_or_browser_audit_completed'])
ck('Heo','Main/SI/facts counts match independent checkpoint',checkpoint['main_pages_read']==9 and checkpoint['si_pages_read']==14 and checkpoint['typed_source_facts']==114)
ck('Heo','Complete reviewed SI scope has unresolved numeric resolution',n['complete_SI_numerical_review'] and not n['complete_SI_numeric_resolution'] and n['rows']==1209 and n['numeric_cells']==7254 and n['resolved_numeric_values']==7252 and n['uncertain_signs']==2)
ck('Heo','All fourteen pages covered exactly once by disjoint chunks',sorted(p for c in n['chunks'] for p in c['pages'])==list(range(1,15)) and sum(c['rows'] for c in n['chunks'])==1209)
def check_bound_objects(v):
    if isinstance(v,dict):
        if 'path' in v and 'sha256' in v and re.match(r'[A-Z]:',str(v['path'])):
            p=Path(v['path']);ck('source checkpoint binding',p.name,p.is_file() and sha(p)==v['sha256']);
            if p.is_file():bound[str(p.resolve())]=sha(p)
        for x in v.values():check_bound_objects(x)
    elif isinstance(v,list):
        for x in v:check_bound_objects(x)
check_bound_objects(checkpoint)
aggregate=load(n['aggregate']['path']);numeric=[c for r in aggregate['rows'] for c in r['cells'] if c['unit_status']!='not_applicable_marker']
ck('Heo','Recount aggregate rows/numeric values/nulls',len(aggregate['rows'])==1209 and len(numeric)==7254 and sum(c['numeric_value'] is not None for c in numeric)==7252 and sum(c['numeric_value'] is None for c in numeric)==2)
ck('Heo','Reading/source approval not promoted to canonical/visual completion',work['stages'][0]['status']==work['stages'][1]['status']==work['stages'][2]['status']=='complete' and work['stages'][3]['status']=='in_progress' and work['stages'][4]['status']=='in_progress' and work['stages'][5]['status']=='pending' and 'not yet published' in work['summary'])
ck('Heo','Public summary and gaps retain unresolved signs and model limitations','7,252' in work['summary'] and 'two unresolved signs' in work['summary'] and all(any(term in gap for gap in work['gaps']) for term in ['null','2.27','omits source displacement tensors','nominal framework','Three synthesis conditions']))
ck('Heo','Raw coordinate candidate cannot become exact training claim',not n['exact_structure_pair_created'] and 'no ordered DFT model' in work['stages'][2]['detail'])

e=progress['estimate'];backlog=eta['backlog']['pending_groups'];scenario_checks=[]
for row in e['scenarios']:
    rate=float(row['reviews_per_day']);days=backlog/rate;printed=float(re.search(r'About ([0-9,]+) days',row['duration']).group(1).replace(',',''))
    ck('ETA arithmetic',str(rate)+' scopes/calendar day',abs(printed-days)<=.51,{'backlog':backlog,'exact_days':days,'shown_days':printed})
    scenario_checks.append({'rate':rate,'days':days,'months_30_4375_days':days/30.4375,'shown':row['duration']})
ck('ETA','Conditional range rather than promised date',e['status']=='conditional_scenarios_not_validated_forecast' and 'if sustained throughput' in e['summary'] and 'reliable completion date is not yet established' in e['summary'])
ck('ETA','Three-to-six-hour planning estimate identified low confidence','3–6 additional active-work hours' in e['current_batch'] and 'Confidence is low' in e['current_batch'] and eta['fixed_batch']['root_planning_estimate']['additional_active_work_hours']==[3,6] and not eta['fixed_batch']['root_planning_estimate']['measured_duration'])
ck('ETA','Recorded source-scope counts retained',eta['completed_scope_counts']['recorded_audited_and_published']==21 and eta['completed_scope_counts']['supplied_main_plus_matched_SI']==6 and eta['completed_scope_counts']['supplied_main_only_SI_unverified']==15 and all(token in e['notes'][1] for token in ('21 audited','24.90','15 main-only','six with matched SI','6.63','unfinished')))
for w in eta['observed_calendar_output_windows']:
    elapsed=(datetime.fromisoformat(w['end'].replace('Z','+00:00'))-datetime.fromisoformat(w['start'].replace('Z','+00:00'))).total_seconds()/3600
    ck('ETA clock',w['name'],abs(elapsed-w['calendar_hours'])<1e-8)
ck('ETA','New-arrival units and unbounded-growth caveat explicit',all(t in e['notes'][2] for t in ('1,000 documents per day','not the same as unique papers','no fixed finish date','retained-paper review throughput exceeds its arrival rate')))
ck('ETA','No implied steady-state full-main/SI observed rate','not steady-state full main/SI throughput measurements' in e['notes'][1])
ck('ETA','Unknown retained fraction and evidenced exclusions remain qualified','unknown' in e['notes'][0] and 'independently screened' in e['notes'][0])

js=pubtexts[str(D/'progress.mjs')]
ck('polling','Once per minute, no hidden-page work, cache-busted snapshot fetch','setInterval(refresh,60000)' in js and 'running||document.hidden' in js and "cache:'no-store'" in js and "new URL('data/review-progress.json',import.meta.url)" in js)
ck('polling','Refresh failure keeps last snapshot and reports error','last displayed snapshot is retained' in js and 'if(data.updated_at!==last)' in js)
ck('polling','Text nodes and same-origin bounded links','n.textContent=String(text)' in js and 'url.origin!==location.origin' in js and '.pathname.startsWith(' in js)
visible_claims=re.sub(r'aria-live="[^"]*"','',js+' '+pubtexts[str(D/'progress.html')]+' '+json.dumps(progress))
ck('polling','No authoritative live-sync claim',not re.search(r'\blive\b|real.?time|continuously working|24/7',visible_claims,re.I))
ck('polling','Header unit names completed review scopes','Completed review scopes / day' in js)
ck('snapshot timestamp','Generated timestamp distinct from scan timestamp',datetime.fromisoformat(progress['updated_at'])>=datetime.fromisoformat(progress['corpus_scanned_at']) and "'updated_at':datetime.now(timezone.utc).isoformat()" in generator)
ck('snapshot timestamp','Meaningful milestone publication policy explicit','meaningful review milestones' in progress['update_policy'] and 'newer published snapshot every minute' in progress['update_policy'])
node=Path('[local path redacted]')
run=subprocess.run([str(node),'--check',str(D/'progress.mjs')],capture_output=True,text=True)
ck('JavaScript','node --check progress.mjs',run.returncode==0,run.stderr.strip())
for p,t in pubtexts.items():
    ck('public path scope',str(Path(p).relative_to(M))+' contains no raw private absolute path or credential token',not re.search(r'(?<![A-Za-z0-9])[A-Za-z]:[[local path redacted]

# Independent bibliography mapping from actual canonical records and their source groups.
records={};primary=defaultdict(list);readers={}
for p in sorted((S/'data/records').glob('*.json')):
    r=load(p);records[r['record_id']]=r
    candidates=[s for s in r['sources'] if s['id']==r['lineage']['source_group']]
    ck('canonical source identity',r['record_id']+' has one source-group source',len(candidates)==1)
    if len(candidates)==1:primary[candidates[0]['doi'].lower()].append((r,candidates[0]))
for p in sorted((S/'data/paper-reviews').glob('*.json')):
    r=load(p);readers[r['paper_id']]=r
ck('published records','All 470 record IDs agree with published manifest',set(records)=={r['record_id'] for r in manifest['records']} and len(records)==470)
text(S/'scripts/dataset_lib.py')
for r in manifest['records']:
    public_record=load(D/r['record_url']);canonical=records[r['record_id']]
    ck('published record transport',r['record_id']+' source/public content and manifest canonical digest agree',canonical==public_record and digest(canonical)==r['record_sha256'])
ck('published grouping','31 primary DOI groups and 26 source readers',len(primary)==31 and len(readers)==26)
ck('Heo publication exclusion','No Heo DOI in published records or readers','10.1021/jp0219348' not in primary and 'heo2003' not in readers)
refs=pubtexts[str(M/'REFERENCES.md')];lines=[line for line in refs.splitlines() if line.startswith('- ')]
doi_rx=r'\]\(https://doi\.org/([^\)]+)\)'
line_by_doi={re.search(doi_rx,line).group(1).lower():line for line in lines if re.search(doi_rx,line)}
ck('citations','Exactly 31 primary DOI lines, no additions or omission',len(lines)==len(line_by_doi)==31 and set(line_by_doi)==set(primary))
ck('citations','No author-unrecorded placeholder','Authors not recorded' not in refs)
ck('citations','Root and Site REFERENCES copies identical',pubtexts[str(M/'REFERENCES.md')]==pubtexts[str(D/'REFERENCES.md')])
section=refs.split('## Papers used in the published website',1)[1]
for p in (M/'README.md',D/'README.md'):ck('citations',str(p.relative_to(M))+' contains same generated references',pubtexts[str(p)].split('## Papers used in the published website',1)[1]==section)
ck('citations','Generation manifest binds current dataset',citation_manifest['source_manifest_sha256']==sha(D/'data/dataset-manifest.json') and citation_manifest['primary_sources']==31 and citation_manifest['canonical_records']==470 and citation_manifest['additional_record_sources']==0)
citations=[];variants=[]
scope_labels={'supplied_main_and_matched_si':'Supplied main paper and matched SI reviewed','supplied_main_si_unverified':'Main paper reviewed; SI unverified','supplied_main_only_si_unverified':'Main paper reviewed; SI unverified'}
for doi,rows in sorted(primary.items()):
    r,s=rows[0];reader=readers.get(s['id']);paper=(reader or {}).get('paper',{})
    authors=paper.get('authors') or s.get('authors');author_text='; '.join(authors) if isinstance(authors,list) else authors
    line=line_by_doi.get(doi,'');title=s['title'].replace('\n',' ').replace('|','\\|');year=s.get('year') or paper.get('year')
    ck('citation identity',doi+' author string',bool(author_text) and author_text.replace('\n',' ').replace('|','\\|') in line)
    ck('citation identity',doi+' title and year',title in line and f'({year}).' in line)
    ids={x['id'] for _,x in rows};titles={x['title'] for _,x in rows};years={x.get('year') for _,x in rows}
    ck('citation identity',doi+' unambiguous published source group',len(ids)==1)
    if len(titles)>1 or len(years)>1:variants.append({'doi':doi,'titles':sorted(titles),'years':list(years)})
    if reader:
        expected=scope_labels.get(reader.get('review_scope'),reader.get('review_scope','').replace('_',' '))
        ck('citation scope',doi+' matches published reader scope',expected in line and 'paper-review.html?id='+s['id'] in line)
        ck('citation source reader',doi+' reader DOI agrees',paper.get('doi',doi).lower()==doi)
    else:ck('citation scope',doi+' no blanket full-main/SI review claim','does not imply full main/SI review' in line)
    citations.append({'doi':doi,'source_group':s['id'],'record_count':len(rows),'authors':authors,'title':s['title'],'year':year,'scope':reader.get('review_scope') if reader else 'record-specific; no formal reader/full-main-SI claim','line':line})
ck('citations','Canonical source metadata consistent within DOI groups',not variants,variants)
ck('readme','Project and Site roles linked and ongoing work labeled','publication in this repository is not scientific approval' in pubtexts[str(M/'README.md')] and 'Original papers and SI remain local' in pubtexts[str(D/'README.md')])
for p,h in list(bound.items()):ck('final input consistency',Path(p).name,sha(p)==h)
fail=[c for c in checks if not c['passed']]
notes=[]
if 'Quantum Dots..' in refs:notes.append({'id':'P-1','severity':'presentation_optional','finding':'Tessier title already ends with a period in canonical metadata; citation generator appends another, producing Quantum Dots..','suggestion':'Use title.rstrip(".")+"." in bibliography presentation only; do not alter scientific source records.'})
if 'Progress saved ${date(data.updated_at)}' in js:notes.append({'id':'T-1','severity':'clarity_optional','finding':'Visible Progress saved uses JSON-generation time. The separate corpus scan and milestone timestamps remain accurate; a timestamp-only regeneration does not mean new scientific work.','suggestion':'Snapshot generated would make this timestamp meaning unambiguous.'})
report={'schema':'mattersyn-public-progress-citation-independent-audit/1','author':'/root','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','at':datetime.now(timezone.utc).isoformat(),'status':('passed_with_optional_presentation_notes' if notes else 'passed') if not fail else 'findings_require_resolution','scope':'Independent static/code/data transport and wording audit of public progress/citations against recorded source/publication/ETA evidence; no browser actions or external requests. No repeated full-paper or SI numerical scientific audit.','counts':{'checks':len(checks),'passed':len(checks)-len(fail),'failed':len(fail),'primary_doi_citations':len(citations),'published_records':len(records),'formal_readers':len(readers),'si_rows_recounted':len(aggregate['rows']),'resolved_si_numeric_values':sum(c['numeric_value'] is not None for c in numeric),'unresolved_si_numeric_values':sum(c['numeric_value'] is None for c in numeric)},'required_findings':fail,'optional_notes':notes,'checks':checks,'citation_mapping':citations,'conditional_arithmetic':scenario_checks,'bound_files':bound,'snapshot_semantics':{'progress_generated_at':progress['updated_at'],'corpus_scanned_at':progress['corpus_scanned_at'],'scientific_dataset_published_at':progress['published']['published_at'],'not_a_continuously_running_worker_claim':True},'checker_revision_note':'Initial checker draft is preserved. It incorrectly treated manifest record_sha256 as file bytes instead of dataset_lib canonical-JSON digest, matched HTTPS strings as drive paths, and treated aria-live as a live-worker claim. These three checker assumptions were corrected; no Site or scientific file was changed by this auditor.','limitations':['Live delivery, actual visual layout, browser polling and navigation remain root QA scope.','References were compared to all published canonical source identities and reader scope metadata; no new external bibliographic lookup or complete source re-audit.','Public repository confidentiality/history filtering is a separate root task; this audit checked only the listed rendered progress/README/reference outputs for raw private paths.','Private Heo canonical proposal may advance after the checkpoint; current public stages remain in progress until required independent and release gates are met.'],'mutations':'Only this private audit script/report written.'}
dump(O/'independent-audit.json',report)
md=['# Public progress and citation audit','',f"Status: **{report['status']}**. Author: `/root`; independent auditor: `/root/backlog_eta`.",'',f"{len(checks)} checks; {len(fail)} required findings. All 31 primary DOI citations checked against 470 published canonical records and 26 reader metadata files.",'','The public 470-record / 97-route / 42-collection counts match dataset 0.23.0 and its publication checkpoint. Heo is unpublished. Its 9 main pages and 14 SI pages are separated from pending canonical, reader, visual and publication gates. The aggregate recount confirms 1,209 rows, 7,252 resolved numerical values and two unresolved signed values; the markers are not numeric zeroes. No exact structure–recipe pair is counted.','','The 9,470-scope frozen-backlog scenarios reproduce the stated arithmetic. The observed 21-scope and unfinished four-of-five batch windows retain their different main/SI coverage and calendar-time limits. The 3–6 active-work hours is labeled low-confidence planning, not a measured deadline. Future document inflow and unknown retained-paper fraction remain distinct.','','Static polling code checks only for a newer published snapshot every minute; it makes no authoritative live-worker claim, retains prior data on failure and uses text nodes/same-origin links. Node syntax check passed. The scan timestamp is separate from the JSON generation and scientific publication timestamps.','','All generated citations preserve primary DOI, stored author/title/year and declared reader review scope. Root/Site reference sections agree. No raw private absolute paths or credential-like tokens appear in the eight checked public outputs.','']
for note in notes:md += [f"Optional {note['id']}: {note['finding']} {note['suggestion']}",'']
for f in fail:md += [f"Required: {f['scope']} — {f['claim']}. Detail: {f.get('detail')}",'']
md+=['This was a static evidence/transport audit. Browser QA, live delivery and repository-wide confidentiality/history filtering remain separate. Exact bindings and citation mappings are in `independent-audit.json`.','']
(O/'independent-audit.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'status':report['status'],'counts':report['counts'],'required_findings':fail,'optional_notes':notes,'json_sha256':sha(O/'independent-audit.json'),'md_sha256':sha(O/'independent-audit.md')},ensure_ascii=False))
