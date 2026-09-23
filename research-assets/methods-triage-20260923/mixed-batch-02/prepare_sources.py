"""Bounded source preparation, not a classification or completeness claim."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, re, time, zipfile
from xml.etree import ElementTree as ET
import pypdfium2 as pdfium

OUT=Path(__file__).resolve().parent
PRIVATE=OUT/'private'; PRIVATE.mkdir(exist_ok=True)
ASSETS=OUT.parents[1]
RUN=ASSETS/'pair-priority-screen-20260922/ranker-proposal/final-run-v2'
DOC=ASSETS/'incoming-paper-monitor/deadline-20260920/workflow-20260920T0412/screen/documents.jsonl'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert not (OUT/'selection.json').exists(), 'Do not reset timing or selection'
started=datetime.now(timezone.utc).isoformat(); tick=time.perf_counter()
rows=[json.loads(s) for s in (RUN/'ranked-scopes.jsonl').open(encoding='utf8')]
docs={r['file_key']:r for r in map(json.loads,DOC.open(encoding='utf8'))}
selected=[]
for prefix in ('R_','U_'):
    pool=[r for r in rows if r['priority_band'].startswith(prefix) and r['review_status_in_partition']!='complete' and not r['source_hold'] and not r['manual_text_hold']]
    for i in (1,len(pool)//4+1,len(pool)//2+1,3*len(pool)//4+1,len(pool)-2): selected.append(pool[i])
selection={'started_at':started,'author':'/root','selection_method':'five neighboring rank positions to prior endpoints/quartiles in each R/U band; purposive, not representative or random','ranker_sha256':sha(RUN/'ranked-scopes.jsonl'),'documents_sha256':sha(DOC),'scopes':selected}
save(OUT/'selection.json',selection)
files={}; inputs=[]
cue=re.compile(r'\b(experimental|methods?|preparation|synthesis|synthesized|synthesised|supporting information|supplementary|XRD|diffraction|TEM|coordinates|crystal structure)\b',re.I)
for n,r in enumerate(selected,1):
    own=[]
    for key in r['file_keys']:
        d=docs[key]; p=Path(d['source_path']); h=sha(p)
        assert h==d['sha256'], (key,'source changed')
        own.append({'file_key':key,'sha256':h,'path':str(p),'historical_role':d['role_candidate']})
        if h in files: continue
        f={'path':str(p),'sha256':h,'format':d['detected_format'],'pages':[],'content_pairing':'pending','visually_inspected_pages':[]}
        if d['detected_format']=='pdf':
            pdf=pdfium.PdfDocument(str(p))
            for i in range(len(pdf)):
                page=pdf[i]; tp=page.get_textpage(); text=tp.get_text_range(); tp.close(); page.close()
                out=PRIVATE/f'{h[:12]}-p{i+1:03d}.txt';out.write_text(text,encoding='utf8')
                f['pages'].append({'pdf_page':i+1,'text_path':str(out),'text_sha256':sha(out),'cue_lines':[s.strip()[:200] for s in text.splitlines() if cue.search(s)][:12]})
            pdf.close()
        elif d['detected_format']=='docx':
            with zipfile.ZipFile(p) as z:
                xml=z.read('word/document.xml'); tree=ET.fromstring(xml)
                text='\n'.join(''.join(t.itertext()) for t in tree.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
            out=PRIVATE/f'{h[:12]}-document.txt';out.write_text(text,encoding='utf8')
            f['ooxml_text']={'part':'word/document.xml','text_path':str(out),'text_sha256':sha(out),'page_boundaries_available':False}
        else: f['unresolved_format']=True
        files[h]=f
    inputs.append({'case':n,'rank':r['candidate_inspection_rank'],'group_id':r['group_id'],'band':r['priority_band'],'files':own})
save(PRIVATE/'sources.json',{'started_at':started,'preparation_finished_at':datetime.now(timezone.utc).isoformat(),'preparation_seconds':time.perf_counter()-tick,'files':files,'inputs':inputs,'prepared_text_is_not_claimed_read':True})
print(json.dumps({'cases':inputs,'unique_sources':len(files),'source_preparation_seconds':time.perf_counter()-tick},ensure_ascii=False,indent=2))
