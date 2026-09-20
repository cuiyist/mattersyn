"""Bounded first-page inspection; no full-paper recipe extraction."""
import collections,concurrent.futures,hashlib,json,re,subprocess,random
from pathlib import Path
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parent
PAPERS=ROOT.parent.parent/'downloaded_papers'
BIN=r'[local path redacted]'
TEXT=ROOT/'first-page-text';TEXT.mkdir(exist_ok=True)
records={};log_counts={}
for log in sorted(PAPERS.glob('*.jsonl')):
    lines=log.read_text(encoding='utf-8').splitlines();log_counts[log.name]=len(lines)
    for line_no,line in enumerate(lines,1):
        try:r=json.loads(line)
        except ValueError:continue
        doi=r['doi'].lower();rec=records.setdefault(doi,{'doi':doi,'mainFiles':[],'siFiles':[],'logEvidence':[]})
        rec['logEvidence'].append({'log':log.name,'line':line_no,'status':r['status']})
        if r.get('pdf') and (PAPERS/r['pdf']).is_file() and r['pdf'] not in rec['mainFiles']:rec['mainFiles'].append(r['pdf'])
        for si in r.get('si',[]):
            if (PAPERS/si).is_file() and si not in rec['siFiles']:rec['siFiles'].append(si)
# Filename index supplies papers omitted from logs, without inferring metadata.
for p in PAPERS.glob('*.pdf'):
    if re.search(r'_si_\d+',p.stem):continue
    if not p.name.startswith('10.'):continue
    doi=p.stem.replace('_','/',1).lower()
    # Resolve file to log DOI when DOI itself contains additional slashes.
    existing=next((r for r in records.values() if p.name in r['mainFiles']),None)
    if existing:continue
    rec=records.setdefault(doi,{'doi':doi,'mainFiles':[],'siFiles':[],'logEvidence':[]})
    if p.name not in rec['mainFiles']:rec['mainFiles'].append(p.name)
    rec['siFiles']=[s.name for s in PAPERS.glob(p.stem+'_si_*')]
eligible=[r for r in records.values() if r['mainFiles'] and r['siFiles']]
groups=collections.defaultdict(list)
for r in eligible:
    doi=r['doi']
    key='acs-jacs' if re.match(r'10.1021/(ja|jacs)',doi) else 'acs-nanoletters' if re.match(r'10.1021/(nl|acs.nanolett)',doi) else 'acs-chemmater' if re.match(r'10.1021/(cm|acs.chemmater)',doi) else 'acs-nano' if re.match(r'10.1021/(nn|acsnano)',doi) else 'nature' if doi.startswith('10.1038/') else 'rsc' if doi.startswith('10.1039/') else 'other'
    groups[key].append(r)
# Deterministic broad sampling across journals rather than DOI alphabetic order.
quotas={'acs-jacs':24,'acs-nanoletters':22,'acs-chemmater':22,'acs-nano':12,'nature':7,'rsc':8,'other':5}
rng=random.Random(20260916);selected=[]
for key,quota in quotas.items():
    options=sorted(groups[key],key=lambda r:r['doi']);rng.shuffle(options);selected+=options[:quota]
assert len(selected)<=100
def inspect(r):
    file=PAPERS/r['mainFiles'][0];out=TEXT/(file.stem+'-page1.txt')
    if not out.exists():
        try:
            reader=PdfReader(file)
            r['pdfMetadataTitle']=str((reader.metadata or {}).get('/Title',''))
            text=reader.pages[0].extract_text() or ''
            out.write_text(text,encoding='utf-8')
            r['firstPageExtractionStatus']='ok'
        except Exception as ex:
            r['firstPageExtractionStatus']='failed';r['firstPageError']=str(ex)
    text=out.read_text(encoding='utf-8',errors='replace') if out.exists() else ''
    r['firstPageTextFile']=str(out);r['firstPageCharacters']=len(text)
    r['firstPagePreview']=text[:6500]
    return r
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:inspected=list(pool.map(inspect,selected))
summary={'filesByExtension':dict(collections.Counter(p.suffix for p in PAPERS.iterdir() if p.is_file())),
 'downloadLogRows':log_counts,'uniqueDoiRecords':len(records),'withExistingMainAndSI':len(eligible),
 'candidateBuckets':{k:len(v) for k,v in groups.items()},'firstPagesInspected':len(inspected),'samplingSeed':20260916,'samplingQuotas':quotas,
 'metadataLimit':'Download logs supply DOI/file/status only; titles, years and family labels require bounded first-page inspection. SI identity remains filename/log matched, not content verified.'}
(ROOT/'local-corpus-index.json').write_text(json.dumps({'summary':summary,'records':list(records.values())},indent=2)+'\n')
(ROOT/'first-page-candidate-audit.json').write_text(json.dumps({'summary':summary,'candidates':inspected},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
for r in inspected:
    lines=[x.strip() for x in r['firstPagePreview'].splitlines() if x.strip()]
    print(r['doi']+' | '+(r.get('pdfMetadataTitle') or ' / '.join(lines[:5]))[:220])
