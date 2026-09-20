"""Validate source coverage, cache integrity and public/private separation."""
import collections,hashlib,json,random,re,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parent;SOURCE=ROOT.parent.parent/'downloaded_papers'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).lower()
public=load(ROOT/'public-bibliographic-manifest.json');private=load(ROOT/'private'/'document-manifest.json');inventory=load(ROOT/'private'/'inventory.json')
docs=private['documents'];errors=[]
def check(test,message):
    if not test:errors.append(message)
check(public['summary']['pipelineComplete'],'Pipeline not complete')
sourcefiles={p.relative_to(SOURCE).as_posix() for p in SOURCE.rglob('*') if p.is_file() and p.suffix.lower() in ('.pdf','.docx','.doc')}
check(len(docs)==len(sourcefiles)==7373,'Document count mismatch')
check({r['sourceRelativeFilename'] for r in docs}==sourcefiles,'Inventory coverage mismatch')
check(len({r['id'] for r in docs})==len(docs),'Duplicate document IDs')
check(len({p['id'] for p in public['papers']})==len(public['papers']),'Duplicate paper IDs')
ids={r['id'] for r in docs};paperids={r['id'] for r in public['papers']};unknown_pages=0;empty_pages=0;evidence_count=0
for r in docs:
    check(bool(re.fullmatch(r'[0-9a-f]{64}',r.get('sha256') or '')),f'Missing SHA256 {r["id"]}')
    check(r['extractionStatus']!='pending',f'Pending document {r["id"]}')
    if r['extractionStatus'] in ('extracted','partial_page_errors'):
        check(bool(r.get('textPath')) and (ROOT/r['textPath']).is_file(),f'Missing private text {r["id"]}')
        check(r.get('characterCount',0)>0,f'Extracted empty document {r["id"]}')
    if r.get('detectedFormat')=='pdf' and r['extractionStatus']=='extracted':
        check(len(r['pageResults'])==r['pageCount'],f'PDF page coverage mismatch {r["id"]}')
        check(sum(p['characters'] for p in r['pageResults'])==r['characterCount'],f'PDF character count mismatch {r["id"]}')
        empty_pages+=sum(p['status']=='no_extractable_text' for p in r['pageResults'])
    if r.get('detectedFormat')=='docx':
        check(r.get('pageCount') is None,f'DOCX physical pagination invented {r["id"]}');unknown_pages+=1
    if r.get('evidenceCandidatePath'):
        evpath=ROOT/r['evidenceCandidatePath'];check(evpath.is_file(),f'Missing evidence cache {r["id"]}')
        if evpath.is_file():
            ev=load(evpath);check(ev['sourceSha256']==r['sha256'],f'Evidence hash mismatch {r["id"]}');evidence_count+=ev['candidatesSaved']
            check(all(c['status']=='machine_candidate_not_reviewed' for c in ev['candidates']),f'Unreviewed evidence mislabeled {r["id"]}')
for r in public['documents']:
    check(r['id'] in ids,'Public document absent privately')
    check(all(i in paperids for i in r['paperIds']),'Broken public paper link')
for p in public['papers']:
    check(all(i in ids for i in p['documentIds']),f'Broken document link {p["id"]}')
    check(p['recipeCurationStatus']=='not_curated_by_this_pipeline',f'Public curation overclaim {p["id"]}')
    for m in p['materialTitleMentions']:
        check(not m['verifiedRecipeContribution'],f'Material contribution overclaim {p["id"]}')
        check(norm(m['evidenceText']) in norm(p['title'] or ''),f'Material evidence not in title {p["id"]}')
public_text=(ROOT/'public-bibliographic-manifest.json').read_text(encoding='utf-8')
for bad in ['C:\\','C:/','/Users/','firstPagePreviewPrivate','textPath','sourceRelativeFilename','evidenceCandidatePath','evidencePrivate','absolutePath']:
    check(bad not in public_text,'Private data marker in public manifest: '+bad)
# Deterministic source-byte check in each format, in addition to all per-document cache hashes.
rng=random.Random(20260917);sample=[]
for ext,num in [('.pdf',5),('.docx',5),('.doc',2)]:
    choices=sorted((r for r in docs if r['declaredExtension']==ext),key=lambda r:r['id']);sample+=rng.sample(choices,min(num,len(choices)))
for r in sample:
    h=hashlib.sha256()
    with (SOURCE/r['sourceRelativeFilename']).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    check(h.hexdigest()==r['sha256'],f'Source hash mismatch {r["id"]}')
out={'status':'passed' if not errors else 'failed','errors':errors,'sourceDocuments':len(docs),'paperCandidates':len(public['papers']),'publicManifestSha256':hashlib.sha256((ROOT/'public-bibliographic-manifest.json').read_bytes()).hexdigest(),'privateManifestSha256':hashlib.sha256((ROOT/'private'/'document-manifest.json').read_bytes()).hexdigest(),'statusCounts':dict(collections.Counter(r['extractionStatus'] for r in docs)),'allDocumentHashesPresent':all(r.get('sha256') for r in docs),'sourceHashesRecomputedSampleIds':[r['id'] for r in sample],'sourceHashSampleCount':len(sample),'nativePdfEmptyTextPages':empty_pages,'docxWithoutClaimedPhysicalPagination':unknown_pages,'privateCandidateWindowsIncludingDuplicateFiles':evidence_count,'coverageAndPublicPrivacyChecksPassed':not errors,'scope':'No semantic correctness, recipe completeness, extraction fidelity to figures, or contribution verification is claimed.'}
(ROOT/'validation-report.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
raise SystemExit(bool(errors))
