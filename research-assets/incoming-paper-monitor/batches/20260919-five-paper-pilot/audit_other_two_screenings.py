from pathlib import Path
import json, hashlib
from datetime import datetime, timezone
from pypdf import PdfReader

B=Path(r'[local path redacted]')
roots=[Path(r'[local path redacted]'),Path(r'[local path redacted]')]
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

details={
 'jp0473669':{
  'title':'Study of Synthesis Variables in the Nanocrystal Growth Behavior of Tin Oxide Processed by Controlled Hydrolysis',
  'coverage':{'main':{'text_pages_actually_read':[2,6],'visual_pages_actually_inspected':[1,2,6],'selected_visual_text_read':{'1':['Title, six-author byline, journal, DOI, abstract'],'2':['Complete Experimental Procedure'],'6':['Conclusion ending, acknowledgment and reference list; absence of SI announcement on final page']}},'si':{'text_pages_actually_read':[],'visual_pages_actually_inspected':[]}},
  'evidence':[
   {'role':'main','page':1,'locator':'Title/byline, journal and DOI footer','finding':'Actual main identifies the reported title, Ribeiro and five coauthors, J. Phys. Chem. B 2004,108,15612–15617 and DOI10.1021/jp0473669. The abstract describes current-study room-temperature tin-chloride hydrolysis and concentration/pH variables.'},
   {'role':'main','page':2,'locator':'Experimental Procedure, first paragraph','finding':'Direct source procedure: SnCl2·2H2O in absolute ethanol at room temperature; deionized-water dialysis; clear SnO2 colloid at approximatelypH8.5; initial tin concentration0.0025–0.1M. More detail is cited to references7/25, but synthesis is present rather than absent.'},
   {'role':'main','page':2,'locator':'Experimental Procedure, second paragraph','finding':'A0.025M precursor-derived colloid is acidified using dilute nitric acid, aged24h, redispersed using tetrabutylammonium hydroxide0.4M aqueous stock and sonicated2min. Missing doses and dialysis details in the screening are honestly retained.'},
   {'role':'main','page':6,'locator':'Final article page and references7/25','finding':'The final page contains the conclusion/acknowledgment/references, without a Supporting Information announcement. References7/25 support the stated external method dependency; they were not read as external papers.'}
  ],
  'retention_conclusion':'Supported. An explicit but incomplete present-study SnO2 preparation and controlled treatment sequence exists; incompleteness is not an exclusion reason.',
  'pairing_conclusion':'Main role is supported by actual title/byline/DOI and experimental content. No local SI candidate was found in either named source folder or the supplied same-DOI candidate snapshot. SI nonexistence is not asserted.',
  'missing_si_language_conclusion':'Honest and appropriately bounded: not located locally, existence unverified. No requirement to invent or download an SI before retaining this recipe-bearing main.',
  'limits':['Only main pages1,2,6 were visually audited, and extracted text pages2,6 read. This does not independently certify the author’s full scientific coverage of pages3–5.','The audit validates retention and identity, not every figure, numeric property, model formula, sample join or eventual route count.']
 },
 'ja048427j':{
  'title':'Synthesis of Colloidal Mn2+:ZnO Quantum Dots and High-TC Ferromagnetic Nanocrystalline Thin Films',
  'coverage':{'main':{'text_pages_actually_read':[3,12],'visual_pages_actually_inspected':[1,2,3,12],'selected_visual_text_read':{'1':['Title, six-author byline, journal, DOI and abstract'],'2':['Materials subsection and source atmosphere context'],'3':['Sample Preparation and relevant Figure1 context'],'12':['Conclusion and complete SI announcement']}},'si':{'text_pages_actually_read':[1,4],'visual_pages_actually_inspected':[1,2,3,4],'selected_visual_text_read':{'1':['Complete title/byline and affiliations'],'2':['Running manuscript identifier and TablesS1–S3 headings/scope'],'3':['FigureS1 caption and model/sample scope'],'4':['FiguresS2–S3 captions, TableS4 and references']}}},
  'evidence':[
   {'role':'main','page':1,'locator':'Title, byline and DOI','finding':'Actual main names Norberg,Kittilstved,Amonette,Kukkadapu,Schwartz,Gamelin; DOI10.1021/ja048427j; JACS2004,126,9387–9398. It describes direct colloidal Mn2+:ZnO synthesis and spin-coated films.'},
   {'role':'main','page':3,'locator':'II.B Sample Preparation, first paragraph','finding':'Actual preparation adds1.7equiv0.55M ethanolic tetramethylammonium hydroxide to0.10M Mn/Zn acetate inDMSO, with room-temperature stirring; discusses growth/ripening, precipitation/washing/capping and a separate surface-bound-Mn control. This is direct recipe content.'},
   {'role':'main','page':3,'locator':'II.B second and third paragraphs','finding':'Surface cleaning uses dodecylamine180°C approximately30min underN2; films are spin-coated onto1×0.5cm fused silica and annealed525°C2min after each layer. FilmA40coats versusB/C20coats. This supports retained processing protocols with the stated missing quantities.'},
   {'role':'main','page':12,'locator':'Supporting Information Available','finding':'Main announces three ligand-field tables, doping statistics, filmA–C temperature-dependent magnetic hysteresis and additional films magnetic data.'},
   {'role':'si','page':1,'locator':'Supporting Information title and authors','finding':'Exact source title and same six authors in order establish strong content-based pairing.'},
   {'role':'si','page':[2,3,4],'locator':'Running ja048427j identifier; TablesS1–S4/FiguresS1–S3','finding':'Internal manuscript code matches. SI content covers the exact declared ligand-field, doping-statistics and film-magnetism topics. Fourth table contains supplementary magnetic values, compatible with the three specifically described ligand-field tables.'}
  ],
  'retention_conclusion':'Supported. Direct colloidal preparation, surface-control/treatment and film processing are explicitly present; a separately cited TOPO method does not invalidate the supplied procedures.',
  'pairing_conclusion':'Supported by actual complete title and author correspondence, internal manuscript code, specific main declaration and SI sample/data matches. Incoming/legacy main copies and SI copies are separately byte-identical.',
  'missing_si_language_conclusion':'Honest: supplied four-page SI is matched, while the report does not certify every possible ancillary file. Main pages6–11 remain explicitly unreviewed by the screening author, so no full-paper completion is claimed.',
  'limits':['This audit read identity, synthesis and supporting-content passages; it is not an independent full12-page source audit.','Nominal versus incorporated dopant fractions, statistical equations, magnetic mechanism/values and all later cohort joins require complete source extraction and independent scientific audit.']
 }
}

for suffix,d in details.items():
    folder=B/suffix
    screen=folder/'screening.json'
    report=json.loads(screen.read_text(encoding='utf-8'))
    checks=[]
    sources=[]
    for doc in report['documents']:
        path=Path(doc['path']); raw=path.read_bytes(); pages=len(PdfReader(path).pages)
        checks += [{'name':f'{path.name}:{doc["location"]}:hash','passed':sha(path)==doc['sha256']},
                   {'name':f'{path.name}:{doc["location"]}:pdf_signature','passed':raw.startswith(b'%PDF-')},
                   {'name':f'{path.name}:{doc["location"]}:page_count','passed':pages==doc['page_count']},
                   {'name':f'{path.name}:{doc["location"]}:size','passed':len(raw)==doc['bytes']}]
        sources.append({'path':str(path),'sha256':sha(path),'detected_format':'pdf','page_count':pages,'role':doc['verified_role'],'location':doc['location']})
    candidates=sorted(str(p) for root in roots for p in root.iterdir() if p.is_file() and suffix.lower() in p.name.lower())
    checks.append({'name':'candidate_set_matches_reported_documents','passed':set(candidates)=={x['path'] for x in report['documents']}})
    checks.append({'name':'same_doi_candidate_snapshot_hash','passed':sha(folder/'ledger-candidate-snapshot.json')==report['local_candidate_check']['snapshot_sha256']})
    checks.append({'name':'recipe_retention_supported_by_actual_experimental_passages','passed':report['recipe_present']=='yes' and report['decision']=='retain_for_complete_source_extraction'})
    checks.append({'name':'main_role_supported_by_actual_title_authors_and_doi','passed':report['doi']=='10.1021/'+suffix and report['title']==d['title']})
    checks.append({'name':'completion_claim_bounded_to_screening','passed':'No complete canonical extraction' in report['scope']})
    files=[]
    for role,coverage in d['coverage'].items():
        for page in coverage['visual_pages_actually_inspected']:
            filename=f'{role}-{page:02d}.png' if suffix=='ja048427j' and role=='main' else f'{role}-{page}.png'
            path=folder/filename
            files.append({'kind':'actually_viewed_page_image','role':role,'pdf_page':page,'path':str(path),'sha256':sha(path)})
        for page in coverage['text_pages_actually_read']:
            path=folder/f'{role}-{page:02d}.txt'
            files.append({'kind':'actually_read_extracted_text','role':role,'pdf_page':page,'path':str(path),'sha256':sha(path)})
    audit={
      'schema_version':'mattersyn-screening-audit/1','author':'peng1998_reader_assets',
      'audited_at':datetime.now(timezone.utc).isoformat(),'doi':report['doi'],
      'status':'passed' if all(c['passed'] for c in checks) else 'findings',
      'scope':'Independent intake-only audit of another author’s recipe relevance, main/SI identity and missingness language. Not a full scientific extraction/canonical audit or publication approval.',
      'audited_report_path':str(screen),'audited_report_sha256':sha(screen),
      'screening_notes_sha256':sha(folder/'screening-notes.md'),
      'source_documents_rehashed':sources,'actual_audited_coverage':d['coverage'],
      'evidence':d['evidence'],'evidence_files':files,
      'local_candidate_search':{'roots':[str(x) for x in roots],'criterion':'Case-insensitive manuscript suffix in direct files, plus supplied exact-DOI ledger snapshot read','actual_candidates':candidates,'scope_limit':'No web search or global content-based search for arbitrarily named ancillary files.'},
      'retention_conclusion':d['retention_conclusion'],'pairing_conclusion':d['pairing_conclusion'],
      'missing_si_language_conclusion':d['missing_si_language_conclusion'],
      'checks':checks,'check_count':len(checks),'findings':[c for c in checks if not c['passed']],
      'remaining_limits':d['limits'],'other_author_report_modified':False,'source_files_modified':False,
      'site_modified':False,'live_ledger_modified':False,'downloads_performed':False
    }
    (folder/'screening-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'doi':report['doi'],'status':audit['status'],'checks':len(checks),'audit_path':str(folder/'screening-audit.json')}))
