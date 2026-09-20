"""Freeze author extraction only after actual page/crop inspection.

Does not confer independent scientific approval. Does not write outside this folder.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re

P=Path(__file__).resolve().parent
assert (P/'source-extraction-revision-1'/'preservation-manifest.json').exists(),'Preserve frozen revision before any correction.'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(name):return json.loads((P/name).read_bytes())
def write(name,value):(P/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
NOW=datetime.now(timezone.utc).isoformat()
F=read('source-facts.json');I=read('source-inventory.json');T=read('source-tables.json');C=read('page-coverage.json');A=read('original-assets-manifest.json');V=read('author-validation.json');D=read('complete-source-payloads.json')
checks=[]
def ck(name,passed):checks.append({'check':name,'passed':bool(passed)})
def pointer(value,path):
    for part in path.strip('/').split('/'):
        part=part.replace('~1','/').replace('~0','~')
        value=value[int(part)]if isinstance(value,list)else value[part]
    return value
for group in ['facts','materials','stocks','protocols','samples','figures','tables','schemes','equations','references']:
    rows=F[group];ck(group+' IDs unique',len(rows)==len({r['id']for r in rows}))
for unit in I['source_units']:
    if unit.get('extraction_pointer'):
        ck(unit['id']+' resolves exact extraction pointer',pointer(F,unit['extraction_pointer'])['id']==unit['id'])
ck('Typed tables identical between standalone and full extraction',F['tables']==T['tables'])
ck('Inventory material identities and stock contexts exact',I['materials']==F['materials']and I['stock_solution_contexts']==F['stocks'])
ck('Inventory protocol phases and sample contexts exact',I['protocols']==F['protocols']and I['sample_or_measurement_contexts']==F['samples'])
ck('No crop is marked complete page',len(A['assets'])==30 and all(a['original_selected_excerpt']and not a['complete_page']for a in A['assets']))
ck('Both distinct documents; four exact incoming/legacy originals',len(D['source_copies'])==4 and len({s['sha256']for s in D['source_copies']})==2)
for source in D['source_copies']:
    ck('Original unchanged '+source['file_key'],sha(source['source_path'])==source['sha256'])
for doc in D['documents']:
    for page in doc['pages']:
        for kind in ['text','render']:
            ck(f"{doc['document_id']} p{page['pdf_page']} {kind} hash",sha(page[kind+'_path'])==page[kind+'_sha256'])
for t in T['tables'][:3]:
    page=t['evidence'][0]['pdf_page']
    raw=(P/'private'/'text'/f'si-{page:02}.txt').read_text(encoding='utf-8')
    found={}
    for line in raw.splitlines():
        m=re.match(r'^\s*((?:Cd|S|N|C|O|H)\([^\)]+\))\s+(.+)$',line)
        if m:found[m[1]]=m[2].replace('−','-').split()
    for row in t['rows']:
        for j,c in enumerate(row['cells']):
            ck(c['id']+' raw token exact cached source',c['raw_text'].replace('−','-')==found[row['row_label']][j])
ck('THF oxygen in H-bond table retains O(1S) label',T['tables'][3]['rows'][1]['row_label']=='N(2)–H(2)…O(1S)#4')
ops={o['id']:o for pr in F['protocols']for o in pr['operations']}
ck('Aliquot collection does not inherit bulk precursor charge',set(q['meaning']for q in ops['qb-sample']['quantities'])=={'time1','time2','time3','time4','time5','aliquot'})
ck('Amine repassivation has no invented volume/temperature',ops['aliquot-repassivate']['quantities']==[])
ck('THF recovery carries wash conditions rather than heat charge',set(q['meaning']for q in ops['thf-wash']['quantities'])=={'wash count','toluene each wash'})
ck('No independent approval/training/atomic model created',not F['completion']['independent_scientific_audit']and not F['completion']['canonical_complete']and not F['completion']['published']and F['training_status']['requested_tasks']==[]and not F['structure_status']['exact_structure_recipe_admission'])
for a in A['assets']:ck(a['id']+' final selected asset unchanged',sha(a['path'])==a['sha256'])
V['checks'].extend(checks)
V['failures']=[c for c in V['checks']if not c['passed']]
assert not V['failures'],V['failures']
V['finalized_at']=NOW
V['rendered_crop_inspection']={
 'status':'author_inspected_complete','inspector':'/root/backlog_eta','selected_assets_inspected':30,
 'method':'All 30 original crops viewed on eight contact sheets after boundary correction; reaction-equations crop additionally opened directly at final bounds. Full native page images had already been individually viewed for all 27 pages. Caption/label clipping was corrected before freeze.',
 'contact_sheet_paths':[str(p)for p in sorted((P/'private'/'crop-checks').glob('contact-*.png'))],
 'direct_final_crop_paths':[str(P/'reader-assets'/'equations-1-3.png')],
 'limitations':'No assertion of independent scientific review or browser/integration approval.'}
V['check_count']=len(V['checks'])
write('author-validation.json',V)
notes=(P/'extraction-notes.md').read_text(encoding='utf-8')
notes=notes.replace('Final freeze follows rendered-crop checks; this file does not claim independent passage or publication.','The final 30 crops were inspected after clipping corrections. The hash-bound package freeze records completed author extraction; distinct scientific review, canonical mapping, model qualification and publication remain pending.')
(P/'extraction-notes.md').write_text(notes,encoding='utf-8')
root_names=['prepare_sources.py','source_author_data.py','build_extraction.py','make_crop_contacts.py','freeze_extraction.py','complete-source-payloads.json','pairing-review.json','relevance-screening.json','source-facts.json','source-inventory.json','source-tables.json','page-coverage.json','original-assets-manifest.json','author-validation.json','extraction-notes.md','source-correction-history.json','preserve_source_revision_1.py','record_source_corrections.py']
files=[P/n for n in root_names]
files.extend(p for directory in ['reader-assets','source-render','private/text','private/crop-checks']for p in(P/directory).rglob('*')if p.is_file())
files.extend(p for p in(P/'source-extraction-revision-1').iterdir()if p.is_file())
files.extend(Path(s['source_path'])for s in D['source_copies'])
files.append(P.parent/'intake-20260920T055502Z'/'intake-manifest.json')
bound={str(p.resolve()):sha(p)for p in sorted(set(files),key=str)}
freeze={
 'schema':'mattersyn-source-extraction-freeze/1','revision':2,'source_id':F['source_id'],'doi':F['doi'],'group_id':F['group_id'],
 'source_generation':2,'bundle_sha256':D['bundle_sha256'],'author':'/root/backlog_eta','frozen_at':NOW,
 'status':'author_extraction_complete_pending_independent_scientific_audit',
 'main_sha256':F['source_sha256'],'si_sha256':F['si_sha256'],'counts':F['counts'],
 'coverage':{'main_pages_read_and_visually_inspected':10,'si_pages_read_and_visually_inspected':17,'selected_original_crops_inspected':30,'author_checks_passed':len(V['checks'])},
 'bound_files':bound,'bound_file_count':len(bound),
 'private_complete_source_payloads':{'manifest':str(P/'complete-source-payloads.json'),'full_text_directory':str(P/'private'/'text'),'whole_page_render_directory':str(P/'source-render'),'classification':'Local-only complete source material. Exclude from public projection; selected excerpts require separate publication approval.'},
 'preparation_status_note':'complete-source-payloads.json records historical preparation state; page-coverage.json and this freeze record subsequently completed author reading.',
 'remaining_gates':['Distinct source/scientific and numerical audit','Canonical mapping and independent canonical audit','Any molecular/atomic-model qualification','Public excerpt projection, reader/visual integration and browser validation'],
 'revision_history':{'previous_freeze':str(P/'source-extraction-revision-1'/'package-freeze.json'),'previous_freeze_sha256':sha(P/'source-extraction-revision-1'/'package-freeze.json'),'corrections':str(P/'source-correction-history.json'),'corrections_sha256':sha(P/'source-correction-history.json')},
 'source_gaps':F['gaps'],'source_discrepancies':F['contradictions'],
 'no_source_mutation':True,'no_live_ledger_mutation':True,'no_site_mutation':True,'no_downloads':True,
 'independent_audit_approved':False,'training_admission':False,'published':False}
write('package-freeze.json',freeze)
for path,digest in bound.items():assert sha(path)==digest,path
print(json.dumps({'status':freeze['status'],'freeze_sha256':sha(P/'package-freeze.json'),'checks':len(V['checks']),'bound_files':len(bound),'source_facts_sha256':sha(P/'source-facts.json'),'counts':F['counts']},ensure_ascii=False))
