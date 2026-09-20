"""Resumable private text indexing and sanitized bibliographic manifest, no recipe curation.

Run with the bundled Python. PyMuPDF is workspace-local in runtime/. Four worker
processes extract PDF text or DOCX XML. Legacy binary DOC is inventoried unsupported.
No downloaded author programs, macros, Word automation, OCR or network calls run.
"""
from __future__ import annotations
import argparse,collections,concurrent.futures,datetime,hashlib,html,json,logging,os,re,sys,time,unicodedata,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent.parent/'downloaded_papers'
PRIOR=ROOT.parent/'training-migration'
sys.path.insert(0,str(ROOT/'runtime'))
VERSION='corpus-text-1.1'
NOW='2026-09-17'
ELEMENTS=set('H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og'.split())
NAMES={'cadmium selenide':'CdSe','cadmium sulfide':'CdS','cadmium telluride':'CdTe','indium phosphide':'InP','indium arsenide':'InAs','lead sulfide':'PbS','lead selenide':'PbSe','lead telluride':'PbTe','zinc oxide':'ZnO','zinc sulfide':'ZnS','zinc selenide':'ZnSe','titanium dioxide':'TiO2','titanium oxide':'TiO2','cesium lead bromide':'CsPbBr3','caesium lead bromide':'CsPbBr3','cesium lead iodide':'CsPbI3','silver sulfide':'Ag2S','silver selenide':'Ag2Se','copper indium sulfide':'CuInS2','copper indium selenide':'CuInSe2','silicon':'Si','germanium':'Ge','iridium':'Ir','platinum':'Pt','palladium':'Pd','gold':'Au','silver':'Ag'}

class UnsupportedPayload(Exception):pass

def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def stable_id(prefix,text):return prefix+'-'+hashlib.sha256(text.encode('utf-8')).hexdigest()[:20]
def sha_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def atomic_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for attempt in range(20):
        try:os.replace(tmp,path);return
        except PermissionError:
            if attempt==19:raise
            time.sleep(.025)
def compact(s):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',html.unescape(str(s or '')))).strip()
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',str(s))).lower()
def plausible_title(s):
    s=compact(s)
    return bool(18<=len(s)<=360 and len(s.split())>=3 and not re.search(r'(?i)(no job name|microsoft (word|powerpoint)|untitled|^(?:supporting|supplementary|electronic supporting)|^This journal|\b(?:figure|fig\.)\s*S?\d|\bDOI\b|\bORIGINAL PAPER\b|^[a-z_]+[-\d.]+\s+\d+\.\.)',s) and not re.search(r'(?i)\.(docx?|pdf)$|[A-Z]:[\\/]|/users/',s) and sum(c.isalpha() for c in s)>15)
def title_from_heading(first):
    lines=[compact(x) for x in first.splitlines() if compact(x)]
    skip=re.compile(r'(?i)^(?:\d+[ .]|\d+$|vol\b|copyright|©|downloaded|see https|https?://|www\.|doi\s*:|received\b|accepted\b|published\b|revised\b|available\b|contents lists|journal homepage|full length article|original article|research article|article$|articles$|letter$|letters$|paper$|review$|open$|access$|read online|metrics|article recommendations|\*?s[ıi]?\s+supporting information|supporting information(?: for)?$|supplementary (?:information|material)(?: for)?$|electronic supplementary|cite this\b|science\s*direct|acs nano|nano lett\.|j\. am\.|chem\. mater\.|scientific reports|rsc advances|nanoscale$)')
    start=None
    for j,line in enumerate(lines[:35]):
        if skip.search(line) or len(line)<12:continue
        if re.search(r'(?i)^(?:pubs\.acs\.org|licensed under|licen[sc]e and permissions|view article|this journal|supplementary|supporting|electronic supporting)',line):continue
        if re.search(r'(?i)^ORIGINAL PAPER$|\bDOI[: ]|\((?:19|20)\d{2}\)\s*\d+[: ,]',line):continue
        if re.search(r'(?i)^(?:department|institute|school|university|abstract|author|keywords|materials and methods|experimental)',line):continue
        if line.count(',')>=3 or re.search(r'[†‡*].*[†‡*]',line):continue
        start=j;break
    if start is None:return None
    pieces=[]
    for line in lines[start:start+8]:
        if pieces and (skip.search(line) or re.search(r'(?i)^(?:abstract|department|institute|school|university|received|accepted|published|author|keywords|correspond)',line) or line.count(',')>=2 or re.search(r'[†‡*]|\s&\s',line) or len(line)>180):break
        pieces.append(line)
        if sum(map(len,pieces))>260:break
    title=compact(' '.join(pieces))
    return title if plausible_title(title) else None
def first_page_year(first):
    patterns=[r'Cite\s*[Tt]his:.*?\b((?:19|20)\d{2})\s*,',r'(?:Chem\. Mater\.|J\. Am\. Chem\. Soc\.|Nano Lett\.|ACS Nano|J\. AM\. CHEM\. SOC\.|ACS Appl\. Nano Mater\.|J\. Mater\. Chem\. C)\s*,?\s*((?:19|20)\d{2})\s*,',r'(?m)^.{0,60}(?:©|Copyright|Scientific Reports|Applied Surface Science|Chemical Engineering Journal).{0,40}?\b((?:19|20)\d{2})\b',r'(?m)^Published(?:\s+on Web|\s+online|\s+on)?[^\n]{0,50}\b((?:19|20)\d{2})']
    for pat in patterns:
        m=re.search(pat,first,re.I)
        if m and 1900<=int(m.group(1))<=2026:return {'value':int(m.group(1)),'confidence':'medium','evidenceType':'first_page_publication_or_citation_line','evidencePrivate':compact(m.group(0))[:200]}
    return {'value':None,'confidence':'unknown','evidenceType':None}
def material_mentions(title):
    if not title:return []
    t=unicodedata.normalize('NFKC',title);found={}
    excluded={'UV','IR','PL','PVP','PEI','PV','CV','BP','COF','MOF','NIR','SERS','ITO','FTO','XRD','NMR','TEM','SEM','LED','CIF','ICP','NP','NPs','NC','NCs','QD','QDs','NR','NRs','NW','NWs','NS','NSs','CD','CDs','CNDs','CQDs','GQDs','NCDs','SCDs','PNC','PNCs','UCNPs','UCNCs','UCQDs','CNTs','PNIPAm','RhB','HP1','HP2','CoV','CsPb'}
    roman=re.compile(r'^(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)(?:\d)?$')
    superheavy={'Rf','Db','Sg','Bh','Hs','Mt','Ds','Rg','Cn','Nh','Fl','Mc','Lv','Ts','Og'}
    # A formula mention is not evidence that this material was synthesized in the paper.
    for m in re.finditer(r'(?<![A-Za-z0-9])(?:[A-Z][a-z]?\d*){2,}(?![A-Za-z0-9])',t):
        token=m.group(0)
        if token in excluded or roman.fullmatch(token):continue
        formula=re.sub(r'(?:QDs?|NCs?|NPs?|NWs?|NRs?|NSs?|NPLs?)$','',token)
        suffix_normalized=formula!=token
        if not formula or formula in excluded or roman.fullmatch(formula):continue
        # All-uppercase prose/acronyms are not formulas merely because their letters are elements.
        if formula.isupper() and not any(c.isdigit() for c in formula) and formula not in {'BN','BCN','CN','CO','NO','HF','HCN'}:continue
        parts=re.findall(r'([A-Z][a-z]?)(\d*)',formula)
        if not parts or not all(e in ELEMENTS for e,n in parts):continue
        if any(e in superheavy for e,n in parts):continue
        if ''.join(e+n for e,n in parts)!=formula or (len({e for e,n in parts})<2 and not suffix_normalized):continue
        tail=t[m.end():m.end()+18]
        if re.match(r'\s*[−–-]?\s*[xyz]|\.\d|\(',tail):continue
        # Flattened superscript charges and TeX subscripts cannot be reconstructed reliably.
        if re.match(r'[+−–]|-(?:\s|$)|\}[_^]|[_^]|\)\s*[xyz]',tail):continue
        # A biological strain identifier can coincidentally tokenize as element symbols.
        if re.search(r'(?i)\b(?:sp\.|strain)\s*$',t[max(0,m.start()-24):m.start()]):continue
        if any(n=='0' for e,n in parts):continue
        found[formula]={'formula':formula,'elements':list(dict.fromkeys(e for e,n in parts)),'evidenceText':token,'evidenceScope':'title_nanocrystal_suffix_normalized' if suffix_normalized else 'title_mention','normalization':'Removed conventional nano-object suffix; no extra elements inferred.' if suffix_normalized else None,'confidence':'medium','verifiedRecipeContribution':False}
    for name,formula in NAMES.items():
        if name=='titanium oxide':continue  # An unspecified titanium oxide does not establish TiO2.
        m=re.search(r'(?i)\b'+re.escape(name)+r'\b',t)
        if not m:continue
        if name=='silver' and re.search(r'(?i)silver[- ]free',t):continue
        found.setdefault(formula,{'formula':formula,'elements':list(dict.fromkeys(re.findall(r'[A-Z][a-z]?',formula))),'evidenceText':m.group(0),'evidenceScope':'title_name_mention','confidence':'medium','verifiedRecipeContribution':False})
    return list(found.values())

def component_systems(title):
    if not title:return []
    known={r['formula']:r for r in material_mentions(title)};out=[]
    for m in re.finditer(r'(?:[A-Z][A-Za-z0-9]*\s*/\s*)+[A-Z][A-Za-z0-9]*',unicodedata.normalize('NFKC',title)):
        parts=[s.strip() for s in m.group(0).split('/')]
        if len(parts)>1 and all(s in known for s in parts):out.append({'label':'/'.join(parts),'components':parts,'elements':list(dict.fromkeys(e for p in parts for e in known[p]['elements'])),'evidenceText':m.group(0),'evidenceScope':'explicit_title_component_system','relationship':'not_assigned; slash alone does not establish core-shell architecture','verifiedRecipeContribution':False})
    return out

def evidence_candidates(text,sha):
    parts=re.split(r'\n\n--- (PAGE \d+|OOXML PART [^\n]+) ---\n\n',text);out=[];total=0
    methods=re.compile(r'(?i)\b(synthesi[sz]|synthesis|experimental|preparation|hot.injection|injected|degass|precipitat|centrifug|reaction mixture|heated to)\b')
    chars=re.compile(r'(?i)\b(characterization|characterisation|X.ray diffraction|XRD|TEM|SEM|XPS|photoluminescence|absorption spectr|Raman|FTIR|crystal structure)\b')
    for k in range(1,len(parts),2):
        marker=parts[k];body=parts[k+1];lines=body.splitlines();seen=set()
        for j,line in enumerate(lines):
            labels=[]
            if methods.search(line):labels.append('method_candidate')
            if chars.search(line):labels.append('characterization_candidate')
            if not labels:continue
            begin=max(0,j-2);end=min(len(lines),j+7)
            if any(i in seen for i in range(begin,end)):continue
            seen.update(range(begin,end));total+=1
            if len(out)>=100:continue
            out.append({'id':f'evidence-{sha[:16]}-{total:04d}','sourceSha256':sha,'page':int(marker[5:]) if marker.startswith('PAGE ') else None,'ooxmlPart':marker[11:] if marker.startswith('OOXML PART ') else None,'lineStartWithinExtractionBlock':begin+1,'lineEndWithinExtractionBlock':end,'categories':labels,'status':'machine_candidate_not_reviewed','text':compact(' '.join(lines[begin:end]))[:1800]})
    return {'schemaVersion':'mattersyn-private-evidence-candidates/1','sourceSha256':sha,'candidateCountDetected':total,'candidatesSaved':len(out),'candidateCapPerDocument':100,'capped':total>100,'meaning':'Keyword windows only; no claims of full procedures, correct role, ingredient quantities or result linkage. Full text is retained for later curation.','candidates':out}

def extract_document(task):
    """Worker only writes content-addressed private extraction cache."""
    started=time.monotonic();p=Path(task['absolutePath']);fp=task['fingerprint'];rid=task['id'];recpath=ROOT/'private'/'document-cache'/(rid+'.json')
    if recpath.exists():
        try:
            cached=json.loads(recpath.read_text(encoding='utf-8'))
            if cached.get('fingerprint')==fp and cached.get('pipelineVersion')==VERSION and not(task.get('retryFailed') and cached.get('extractionStatus') in ('extraction_failed','worker_failed','partial_page_errors')):
                if not cached.get('textPath') or (ROOT/cached['textPath']).exists():return {**cached,'resumeCacheHit':True}
        except Exception:pass
    result={'id':rid,'sourceRelativeFilename':task['relativeFilename'],'fingerprint':fp,'pipelineVersion':VERSION,'sha256':None,'declaredExtension':p.suffix.lower(),'detectedFormat':None,'extractionStatus':'pending','textPath':None,'pageCount':None,'pageCountKind':None,'pageResults':[],'characterCount':0,'metadataTitle':None,'firstPagePreviewPrivate':'','warnings':[],'errors':[],'extractionEngine':None,'updatedAt':stamp(),'resumeCacheHit':False}
    try:
        sha=sha_file(p);result['sha256']=sha;cc=ROOT/'private'/'content-cache'/(sha+'.json')
        if cc.exists():
            cached=json.loads(cc.read_text(encoding='utf-8'))
            if cached.get('pipelineVersion')==VERSION and (not cached.get('textPath') or (ROOT/cached['textPath']).exists()) and not(task.get('retryFailed') and cached.get('extractionStatus') in ('extraction_failed','worker_failed','partial_page_errors')):
                keys=['detectedFormat','extractionStatus','textPath','pageCount','pageCountKind','pageResults','characterCount','metadataTitle','firstPagePreviewPrivate','warnings','errors','extractionEngine','docxReportedPages','embeddedImageCount','paragraphCount','evidenceCandidatePath','evidenceCandidateCount','evidenceCandidateCountDetected','archiveMemberNamesPrivate']
                result.update({k:cached[k] for k in keys if k in cached});result['contentCacheHit']=True;atomic_json(recpath,result);return result
        head=p.open('rb').read(32)
        ext=p.suffix.lower();texts=[]
        if ext=='.doc':
            result.update({'detectedFormat':'legacy_doc' if head.startswith(bytes.fromhex('D0CF11E0A1B11AE1')) else 'unverified_doc','extractionStatus':'unsupported_legacy_doc','extractionEngine':None})
            result['warnings'].append('Legacy DOC not parsed; no Word automation or external converter launched.')
        elif ext=='.pdf':
            import pymupdf
            pymupdf.TOOLS.mupdf_display_errors(False);pymupdf.TOOLS.mupdf_display_warnings(False)
            result.update({'detectedFormat':'pdf','extractionEngine':'PyMuPDF '+pymupdf.VersionBind})
            if b'%PDF-' not in head:
                raise ValueError('Declared PDF has no PDF header in first 32 bytes')
            with pymupdf.open(p) as doc:
                if doc.needs_pass and not doc.authenticate(''):
                    result['extractionStatus']='password_required'
                else:
                    result['pageCount']=len(doc);result['pageCountKind']='pdf_native';result['metadataTitle']=doc.metadata.get('title')
                    for page_no in range(len(doc)):
                        try:
                            text=doc[page_no].get_text('text',sort=True);texts.append(f'\n\n--- PAGE {page_no+1} ---\n\n'+text)
                            result['pageResults'].append({'page':page_no+1,'characters':len(text),'status':'text' if text.strip() else 'no_extractable_text'})
                            if page_no==0:result['firstPagePreviewPrivate']=text[:14000]
                        except Exception as ex:
                            result['pageResults'].append({'page':page_no+1,'characters':0,'status':'error','errorType':type(ex).__name__});result['errors'].append({'page':page_no+1,'type':type(ex).__name__,'message':str(ex)[:400]})
                    result['characterCount']=sum(r['characters'] for r in result['pageResults'])
                    result['extractionStatus']='partial_page_errors' if result['errors'] else 'extracted' if result['characterCount']>0 else 'no_extractable_text'
                    if any(r['status']=='no_extractable_text' for r in result['pageResults']):result['warnings'].append('Some pages have no text layer; images/plots/formulas are not OCR-transcribed.')
        elif ext=='.docx':
            result.update({'detectedFormat':'docx','extractionEngine':'Python zipfile + ElementTree OOXML','pageCountKind':'unknown_without_rendering'})
            with zipfile.ZipFile(p) as z:
                names=z.namelist();result['embeddedImageCount']=sum(n.startswith('word/media/') for n in names)
                if 'word/document.xml' not in names:
                    result['archiveMemberNamesPrivate']=names
                    raise UnsupportedPayload('xlsx' if 'xl/workbook.xml' in names else 'zip')
                if 'docProps/core.xml' in names:
                    root=ET.fromstring(z.read('docProps/core.xml'));v=root.find('{http://purl.org/dc/elements/1.1/}title');result['metadataTitle']=v.text if v is not None else None
                if 'docProps/app.xml' in names:
                    root=ET.fromstring(z.read('docProps/app.xml'));v=root.find('{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Pages')
                    result['docxReportedPages']=int(v.text) if v is not None and (v.text or '').isdigit() else None
                total_paragraphs=0
                parts=['word/document.xml']+[n for n in names if re.fullmatch(r'word/(?:footnotes|endnotes|header\d+|footer\d+)\.xml',n)]
                W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}';M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
                for part in parts:
                    xml=ET.fromstring(z.read(part));paragraphs=[]
                    for para in xml.iter(W+'p'):
                        pieces=[]
                        for node in para.iter():
                            if node.tag in (W+'t',M+'t'):pieces.append(node.text or '')
                            elif node.tag==W+'tab':pieces.append('\t')
                            elif node.tag in (W+'br',W+'cr'):pieces.append('\n')
                        if pieces:paragraphs.append(''.join(pieces))
                    text='\n'.join(paragraphs);texts.append(f'\n\n--- OOXML PART {part} ---\n\n'+text);total_paragraphs+=len(paragraphs)
                    if part=='word/document.xml':result['firstPagePreviewPrivate']=text[:14000]
                    result['characterCount']+=len(text)
                result['paragraphCount']=total_paragraphs;result['extractionStatus']='extracted' if result['characterCount'] else 'no_extractable_text'
                result['warnings'].append('DOCX physical pagination unknown; OOXML paragraphs/tables/notes extracted, embedded images not OCR-transcribed.')
        else:result['extractionStatus']='unsupported_format'
        if texts and result['characterCount']:
            out=ROOT/'private'/'text'/(sha+'.txt');out.parent.mkdir(parents=True,exist_ok=True);tmp=out.with_name(out.name+f'.{os.getpid()}.tmp');payload=''.join(texts)
            if not out.exists() or out.read_text(encoding='utf-8')!=payload:
                tmp.write_text(payload,encoding='utf-8')
                for attempt in range(20):
                    try:os.replace(tmp,out);break
                    except PermissionError:
                        if attempt==19:raise
                        time.sleep(.025)
            result['textPath']=out.relative_to(ROOT).as_posix()
            ev=evidence_candidates(''.join(texts),sha);evpath=ROOT/'private'/'evidence-candidates'/(sha+'.json');atomic_json(evpath,ev);result['evidenceCandidatePath']=evpath.relative_to(ROOT).as_posix();result['evidenceCandidateCount']=ev['candidatesSaved'];result['evidenceCandidateCountDetected']=ev['candidateCountDetected']
    except UnsupportedPayload as ex:
        result['extractionStatus']='unsupported_mislabeled_payload';result['detectedFormat']=str(ex)
        result['warnings'].append('Declared DOCX is a '+str(ex)+' payload, outside PDF/DOCX text-extraction scope; private archive member names preserved.')
    except Exception as ex:
        result['extractionStatus']='extraction_failed';result['errors'].append({'type':type(ex).__name__,'message':str(ex)[:600]})
    result['elapsedSeconds']=round(time.monotonic()-started,3)
    if result['sha256']:atomic_json(ROOT/'private'/'content-cache'/(result['sha256']+'.json'),result)
    atomic_json(recpath,result)
    return result

def source_groups():
    groups={};filelinks=collections.defaultdict(list);prior_titles={};priorfile=PRIOR/'local-corpus-index.json'
    def ensure(doi):
        doi=doi.lower().strip();return groups.setdefault(doi,{'id':stable_id('paper',doi),'doi':doi,'documents':{},'logStatuses':set()})
    if priorfile.exists():
        prior=json.loads(priorfile.read_text(encoding='utf-8'))
        for rec in prior['records']:
            g=ensure(rec['doi'])
            for field,role in [('mainFiles','main_candidate'),('siFiles','supporting_candidate')]:
                for fn in rec.get(field,[]):g['documents'].setdefault(fn,set()).add(role)
            for ev in rec.get('logEvidence',[]):g['logStatuses'].add(ev.get('status','unknown'))
    # Current logs supplement old index and preserve document-role candidates.
    for log in SOURCE.glob('*.jsonl'):
        for line in log.read_text(encoding='utf-8',errors='replace').splitlines():
            try:r=json.loads(line);g=ensure(r['doi'])
            except Exception:continue
            g['logStatuses'].add(r.get('status','unknown'))
            if r.get('pdf'):g['documents'].setdefault(r['pdf'],set()).add('main_candidate')
            for fn in r.get('si',[]):g['documents'].setdefault(fn,set()).add('supporting_candidate')
    q=PRIOR/'diverse-pilot-source-queue.json'
    if q.exists():
        for r in json.loads(q.read_text(encoding='utf-8'))['queue']:
            if r.get('title'):prior_titles[r['doi']]={'title':r['title'],'year':r.get('year')}
    override_path=ROOT/'verified-source-overrides.json'
    if override_path.exists():
        for fn,override in json.loads(override_path.read_text(encoding='utf-8')).items():
            path=SOURCE/fn
            if path.is_file() and sha_file(path)==override['sha256']:
                g=ensure(override['doi']);g['documents'].setdefault(fn,set()).add(override['role']);prior_titles[override['doi']]={'title':override['title'],'year':override['year']}
    for doi,g in groups.items():
        for fn,roles in g['documents'].items():filelinks[fn].append({'doi':doi,'paperId':g['id'],'roleCandidates':sorted(roles),'basis':'existing_download_log_or_prior_index'})
    return groups,filelinks,prior_titles

def enrich(result,associations,prior_titles):
    r=dict(result);r['paperAssociations']=associations;first=r.get('firstPagePreviewPrivate','')
    initial_lines=[compact(s) for s in first.splitlines() if compact(s)][:6]
    si=any(re.match(r'(?i)^(?:supporting information|supplementary information|electronic supplementary)',s) for s in initial_lines)
    r['firstPageSuggestsSupportingInformation']=si
    r['doiMatchesOnFirstPage']=[a['doi'] for a in associations if norm(a['doi']) in norm(first)]
    title=None;origin=None;confidence='unknown'
    primary=associations[0]['doi'] if len(associations)==1 else None
    if primary in prior_titles and any('main_candidate' in a['roleCandidates'] for a in associations):title=prior_titles[primary]['title'];origin='prior_bounded_first_page_review';confidence='medium_high'
    elif plausible_title(r.get('metadataTitle')):title=compact(r['metadataTitle']);origin='embedded_document_metadata';confidence='medium' if norm(title) in norm(first) else 'low'
    else:title=title_from_heading(first);origin='first_page_heading_heuristic' if title else None;confidence='low' if title else 'unknown'
    r['likelyTitle']={'value':title,'origin':origin,'confidence':confidence,'evidenceDocumentId':r['id'],'evidencePage':1 if r['detectedFormat']=='pdf' else None}
    r['likelyYear']=first_page_year(first)
    if primary in prior_titles and prior_titles[primary].get('year'):r['likelyYear']={'value':prior_titles[primary]['year'],'confidence':'medium_high','evidenceType':'prior_first_page_citation_review'}
    r['titleMaterialMentions']=material_mentions(title)
    r['titleComponentSystems']=component_systems(title)
    r['curationStatus']='document_text_indexed_not_recipe_curated';r['verifiedRecipeContribution']=False
    r['roleMismatchFlag']=si and any('main_candidate' in a['roleCandidates'] for a in associations)
    return r

def publish_manifests(tasks,results,groups,prior_titles,initial,complete=False):
    docs={r['id']:r for r in results};byfile={r['sourceRelativeFilename']:r for r in results}
    tasks_by_doi=collections.defaultdict(list)
    for task in tasks:
        for assoc in task['associations']:tasks_by_doi[assoc['doi']].append(task)
    public_docs=[]
    for task in tasks:
        r=docs.get(task['id']);a=task['associations'];public_docs.append({'id':task['id'],'sha256':r.get('sha256') if r else None,'format':r.get('detectedFormat') if r else task['extension'][1:],'paperIds':[v['paperId'] for v in a],'roleCandidates':sorted(set(v for x in a for v in x['roleCandidates'])),'extractionStatus':r['extractionStatus'] if r else 'pending','pageCount':r.get('pageCount') if r else None,'pageCountKind':r.get('pageCountKind') if r else None,'characterCount':r.get('characterCount',0) if r else 0,'emptyTextPages':sum(x['status']=='no_extractable_text' for x in r.get('pageResults',[])) if r else 0,'roleMismatchFlag':r.get('roleMismatchFlag',False) if r else False,'errorCategories':sorted({e['type'] for e in r.get('errors',[])}) if r else [],'curationStatus':'not_recipe_curated'})
    papers=[]
    for doi,g in sorted(groups.items()):
        existing=[byfile[fn] for fn in g['documents'] if fn in byfile]
        candidate=[r for r in existing if r['likelyTitle']['value']]
        candidate.sort(key=lambda r:(not any('main_candidate' in a['roleCandidates'] for a in r['paperAssociations'] if a['doi']==doi),r['roleMismatchFlag'],{'medium_high':0,'medium':1,'low':2}.get(r['likelyTitle']['confidence'],3)))
        best=candidate[0] if candidate else None
        title=best['likelyTitle'] if best else {'value':None,'origin':None,'confidence':'unknown'}
        if not best and doi in prior_titles:title={'value':prior_titles[doi]['title'],'origin':'prior_bounded_first_page_review','confidence':'medium_high'}
        group_tasks=tasks_by_doi.get(doi,[]);links=[t['id'] for t in group_tasks]
        counts=dict(collections.Counter(r['extractionStatus'] for r in existing));pending=len(links)-len(existing)
        if pending:counts['pending']=pending
        papers.append({'id':g['id'],'doi':doi,'doiUrl':'https://doi.org/'+doi,'title':title['value'],'titleMetadata':title,'year':best['likelyYear']['value'] if best else prior_titles.get(doi,{}).get('year'),'yearConfidence':best['likelyYear']['confidence'] if best else 'unknown','documentIds':links,'coverage':{'localDocumentCount':len(links),'extractionStatusCounts':counts,'mainDocumentAvailable':any('main_candidate' in g['documents'].get(t['relativeFilename'],[]) for t in group_tasks),'supportingDocumentAvailable':any('supporting_candidate' in g['documents'].get(t['relativeFilename'],[]) for t in group_tasks),'doiConfirmedOnDocumentFirstPage':any(doi in r['doiMatchesOnFirstPage'] for r in existing)},'materialTitleMentions':material_mentions(title['value']),'materialContributionStatus':'title_mentions_only_not_verified_material_or_recipe_contribution','recipeCurationStatus':'not_curated_by_this_pipeline','trainingEligibility':'not_assessed','licenseStatus':'not_assessed; source full text not redistributed'})
        papers[-1]['titleComponentSystems']=component_systems(title['value'])
        main_hashes={r['sha256'] for r in existing if r.get('sha256') and 'main_candidate' in g['documents'].get(r['sourceRelativeFilename'],[])}
        si_hashes={r['sha256'] for r in existing if r.get('sha256') and 'supporting_candidate' in g['documents'].get(r['sourceRelativeFilename'],[])}
        papers[-1]['coverage']['mainSupportingExactDuplicate']=bool(main_hashes&si_hashes)
    status_counts=dict(collections.Counter(r['extractionStatus'] for r in results));summary={**initial,'updatedAt':stamp(),'pipelineComplete':complete,'processedDocuments':len(results),'pendingDocuments':len(tasks)-len(results),'extractionStatusCounts':status_counts,'paperCandidateCount':len(papers),'papersWithLocalDocuments':sum(bool(p['documentIds']) for p in papers),'papersWithLikelyTitle':sum(bool(p['title']) for p in papers),'papersWithTitleMaterialMentions':sum(bool(p['materialTitleMentions']) for p in papers),'roleMismatchDocuments':sum(r.get('roleMismatchFlag',False) for r in results),'uniqueContentHashes':len({r['sha256'] for r in results if r.get('sha256')}),'sha256ComputedDocuments':sum(bool(r.get('sha256')) for r in results),'nativePdfPages':sum(r.get('pageCount') or 0 for r in results),'privateTextCharacters':sum(r.get('characterCount',0) for r in results),'scopeLimit':'Indexing/extraction is not recipe curation. Title material mentions do not verify synthesis contributions. No OCR or legacy DOC conversion performed.'}
    public={'schemaVersion':'mattersyn-bibliographic-corpus/1','summary':summary,'papers':papers,'documents':public_docs,'publicSafety':'No local paths, source filenames, article full text or private evidence excerpts are included. Bibliographic titles and material-title mentions remain machine candidates.'}
    summary['documentsWithoutPaperCandidate']=sum(not t['associations'] for t in tasks)
    summary['papersWithMainSiContentDuplicate']=sum(p['coverage']['mainSupportingExactDuplicate'] for p in papers)
    summary['privateEvidenceCandidatesSaved']=sum(r.get('evidenceCandidateCount',0) for r in results)
    summary['evidenceCandidateMeaning']='Private keyword windows, not reviewed synthesis/characterization records.'
    summary['papersWithFirstPageDoiMatch']=sum(p['coverage']['doiConfirmedOnDocumentFirstPage'] for p in papers)
    summary['titleConfidenceCounts']=dict(collections.Counter(p['titleMetadata']['confidence'] for p in papers))
    summary['detectedFormatCounts']=dict(collections.Counter(r.get('detectedFormat') or 'unknown' for r in results))
    atomic_json(ROOT/'public-bibliographic-manifest.json',public)
    atomic_json(ROOT/'progress.json',summary)
    atomic_json(ROOT/'private'/'document-manifest.json',{'schemaVersion':'mattersyn-private-document-index/1','summary':summary,'documents':results})
    return summary

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=4);parser.add_argument('--limit',type=int);parser.add_argument('--retry-failed',action='store_true');args=parser.parse_args()
    groups,links,prior_titles=source_groups();files=sorted(p for p in SOURCE.rglob('*') if p.is_file());docs=[p for p in files if p.suffix.lower() in ('.pdf','.docx','.doc')];tasks=[]
    for p in docs:
        rel=p.relative_to(SOURCE).as_posix();a=links.get(rel,[])
        if not a:
            stem=re.sub(r'_si_\d+.*$','',p.stem);doi=stem.replace('_','/',1).lower() if stem.startswith('10.') and '_' in stem else None
            if doi and re.match(r'^10\.\d{4,9}/\S+$',doi):
                g=groups.setdefault(doi,{'id':stable_id('paper',doi),'doi':doi,'documents':{},'logStatuses':set()});role='supporting_candidate' if re.search(r'_si_\d+',p.stem) else 'main_candidate';g['documents'].setdefault(rel,set()).add(role);a=[{'doi':doi,'paperId':g['id'],'roleCandidates':[role],'basis':'filename_inference_unverified'}]
        st=p.stat();tasks.append({'id':stable_id('doc',rel.lower()),'absolutePath':str(p),'relativeFilename':rel,'extension':p.suffix.lower(),'fingerprint':{'bytes':st.st_size,'mtimeNs':st.st_mtime_ns},'associations':a,'retryFailed':args.retry_failed})
    initial={'startedAt':stamp(),'pipelineVersion':VERSION,'sourceDocumentCount':len(tasks),'sourceFileCount':len(files),'sourceFolderBytes':sum(p.stat().st_size for p in files),'documentsByExtension':dict(collections.Counter(t['extension'] for t in tasks)),'workerCount':max(1,min(args.workers,4)),'privateFullText':True,'networkUsedByPipeline':False}
    atomic_json(ROOT/'private'/'inventory.json',{'summary':initial,'documents':[{k:v for k,v in t.items() if k!='absolutePath'} for t in tasks],'ancillaryFiles':[p.relative_to(SOURCE).as_posix() for p in files if p not in docs]})
    results=[];selected=tasks[:args.limit] if args.limit else tasks;start=time.monotonic();last=0
    # Consume completed results immediately; each worker writes a resume cache before returning.
    with concurrent.futures.ProcessPoolExecutor(max_workers=initial['workerCount']) as pool:
        iterator=iter(selected);active={}
        def fill():
            while len(active)<initial['workerCount']*2:
                try:t=next(iterator)
                except StopIteration:break
                active[pool.submit(extract_document,t)]=t
        fill()
        with (ROOT/'private'/'run-events.jsonl').open('a',encoding='utf-8') as events:
            while active:
                done,_=concurrent.futures.wait(active,timeout=5,return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    task=active.pop(future)
                    try:r=future.result()
                    except Exception as ex:r={'id':task['id'],'sourceRelativeFilename':task['relativeFilename'],'sha256':None,'detectedFormat':None,'extractionStatus':'worker_failed','textPath':None,'pageCount':None,'characterCount':0,'errors':[{'type':type(ex).__name__,'message':str(ex)[:400]}]}
                    r=enrich(r,task['associations'],prior_titles);results.append(r);events.write(json.dumps({'at':stamp(),'id':r['id'],'status':r['extractionStatus'],'characters':r['characterCount'],'cacheHit':r.get('resumeCacheHit',False)})+'\n');events.flush()
                fill()
                elapsed=time.monotonic()-start
                if len(results)-last>=(1000 if args.retry_failed else 250) or (not active):
                    last=len(results);summary=publish_manifests(tasks,results,groups,prior_titles,initial,complete=(len(results)==len(tasks)))
                    print(json.dumps({'processed':len(results),'total':len(tasks),'elapsedSeconds':round(elapsed,1),'status':summary['extractionStatusCounts'],'titles':summary['papersWithLikelyTitle'],'materialTitleMentions':summary['papersWithTitleMaterialMentions']}),flush=True)
    print(json.dumps({'complete':len(results)==len(tasks),'processed':len(results),'publicManifest':str(ROOT/'public-bibliographic-manifest.json')}),flush=True)

if __name__=='__main__':main()
