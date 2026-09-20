"""Private author validation and one-time freeze; not independent scientific approval."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, re, io
from PIL import Image
import pypdfium2 as pdfium
import source_author_data as A

P=Path(__file__).resolve().parent
AUTHOR='/root/peng1998_reader_assets'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,v): (P/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def ptr(obj,p):
 for t in p.strip('/').split('/'):
  t=t.replace('~1','/').replace('~0','~'); obj=obj[int(t)] if isinstance(obj,list) else obj[t]
 return obj
assert not (P/'package-freeze.json').exists(), 'Immutable freeze already exists; preserve it and make a revision.'
checks=[]
def check(label, condition):
 checks.append({'check':label,'passed':bool(condition)})
 if not condition: raise AssertionError(label)
prep=read(P/'source-preparation.json'); facts=read(P/'source-facts.json'); inv=read(P/'source-inventory.json')
tab=read(P/'source-tables.json'); coverage=read(P/'page-coverage.json'); assets=read(P/'original-assets-manifest.json')
docs={d['role']:d for d in prep['documents']}; byfact={f['id']:f for f in facts['facts']}
expected={'main':'eb93e8ce4e893bde4215914cc7920bd7567388fdd895537334e80e5d3354d581','si':'1669359b67be6fcf7362dbf33d708d76b76d70e079b91b6c70d2856683de431e'}
check('intake manifest immutable hash',sha(prep['intake_manifest']['path'])==prep['intake_manifest']['sha256'])
intake=read(prep['intake_manifest']['path']); ip=next(x for x in intake['papers'] if x['paper_id']=='10.1021_la8031286')
check('source generation and bundle',ip['source_generation']==1 and ip['bundle_sha256']==prep['bundle_sha256']==facts['bundle_sha256'])
for role,d in docs.items():
 check(role+' original PDF bytes',sha(d['source_path'])==d['sha256']==expected[role])
 check(role+' PDF signature',Path(d['source_path']).read_bytes().startswith(b'%PDF-'))
 check(role+' intake original',any(x['source_path']==d['source_path'] and x['sha256']==d['sha256'] for x in ip['file_copies']))
 pdf=pdfium.PdfDocument(d['source_path']);check(role+' pages',len(pdf)==d['page_count']==4);pdf.close()
for row in coverage['pages']:
 check(row['document_role']+str(row['pdf_page'])+' text hash',sha(row['text_path'])==row['text_sha256'])
 check(row['document_role']+str(row['pdf_page'])+' render hash',sha(row['render_path'])==row['render_sha256'])
 check(row['document_role']+str(row['pdf_page'])+' actual author page review',row['text_read'] and row['visual_review'] and row['reviewer']==AUTHOR)
check('eight distinct pages',len({(p['document_role'],p['pdf_page']) for p in coverage['pages']})==8)
check('all source unit IDs unique',len({u['id'] for u in inv['inventory_units']})==len(inv['inventory_units'])==218)
payloads={'source-facts.json':facts,'source-tables.json':tab}
for unit in inv['inventory_units']:
 check(unit['id']+' pointer resolves',ptr(payloads[unit['payload_path']],unit['json_pointer']) is not None)
 for ev in unit['evidence']:
  check(unit['id']+' source locator',ev['document_role'] in docs and ev['source_sha256']==expected[ev['document_role']] and 1<=ev['pdf_page']<=4 and bool(ev['locator']))
for i,f in enumerate(facts['facts']):
 src=A.FACTS[i]
 check(f['id']+' author transcription binding',f['id']=='pati2009-'+src[0] and f['claim']==src[5] and f['sample_scope']==src[6])
 check(f['id']+' quantity count',len(f['quantities'])==len(src[7]))
 for j,q in enumerate(f['quantities']):
  meaning,raw,unit=src[7][j]
  check(f['id']+f' quantity {j} raw and scope',q['raw_text']==raw and q['unit']==unit and q['meaning']==meaning)
  check(f['id']+f' quantity {j} approximation',q['approximate']==raw.startswith('~'))
  check(f['id']+f' quantity {j} comparison',q['comparison']==(raw[0] if raw.startswith(('<','>')) else None))
  check(f['id']+f' quantity {j} evidence',q['evidence']==f['evidence'])
check('58 facts and 90 source quantities',len(facts['facts'])==58 and sum(len(f['quantities']) for f in facts['facts'])==90)
materialids={m['id'] for m in facts['materials']};sampleids={s['id'] for s in facts['sample_contexts']}
check('material inventory uniqueness',len(materialids)==len(facts['materials'])==20)
check('sample inventory uniqueness',len(sampleids)==len(facts['sample_contexts'])==22)
for stock in facts['stocks']:
 check(stock['id']+' component references',all(c['material_id'] in materialids and c['amount'] is None for c in stock['components']))
 check(stock['id']+' unknown preparation volume/storage',stock['final_volume'] is None and stock['storage'] is None)
 check(stock['id']+' transfer separate',stock['subsequent_transfer_volume']['value']==100 and stock['subsequent_transfer_volume']['unit']=='mL')
 check(stock['id']+' own concentration',stock['quantities'][0]['value']==(.1 if '-nitrate-' in stock['id'] else .4))
check('six solvent specific stocks',len(facts['stocks'])==6)
operations=[o for p in facts['protocols'] for o in p['operations']]
check('19 unique operations',len({o['id'] for o in operations})==len(operations)==19)
for p in facts['protocols']:
 check(p['id']+' sample references',all(s in sampleids for s in p['sample_ids']))
 for op in p['operations']:
  check(op['id']+' source facts',all(x in byfact for x in op['source_fact_ids']))
  for q in op['quantities']:
   check(op['id']+' exact quantity inheritance',any(q==fq for fid in op['source_fact_ids'] for fq in byfact[fid]['quantities']))
ob={o['id']:o for o in operations}
check('stock concentration partition',len(ob['prepare-nitrate']['quantities'])==len(ob['prepare-tea']['quantities'])==1)
check('drying duration not wash condition',not ob['alcohol-wash']['quantities'] and ob['ambient-dry']['quantities'][0]['value']==24)
check('diagnostic filtrate is separate',ob['diagnostic']['inputs']==['filtrate','ammonium-hydroxide'] and ob['diagnostic']['outputs']==['diagnostic-mixture'])
check('calcination unknown atmosphere', 'atmosphere' in ob['calcine']['missing_fields'])
check('no pure as-prepared composition',all(s['reported_whole_composition'] is None for s in facts['sample_contexts'] if s['id'].endswith('-as-prepared')))
for f in facts['figures']:
 for panel in f['panels']: check(f['id']+panel['label']+' sample',panel['sample_id'] in sampleids)
check('4 supplied figures only',[f['id'] for f in facts['figures']]==['figure-1','figure-2','figure-3','figure-s1'])
t=tab['tables'][0];check('raw table shape',len(t['raw_grid'])==6 and all(len(r)==6 for r in t['raw_grid']))
for i,row in enumerate(t['rows']):
 group=i//5; col=i%5+1
 check(row['id']+' printed label',row['source_group_header']==t['raw_grid'][group*3][0] and row['peak_label']+' '+row['oxidation_assignment_as_printed']==t['raw_grid'][group*3][col])
 for j,c in enumerate(row['cells']):
  check(row['id']+str(j)+' exact raw cell',c['raw_text']==t['raw_grid'][group*3+j+1][col] and c['value']==float(c['raw_text']) and c['unit']=='eV')
check('20 numeric table cells',sum(len(r['cells']) for r in t['rows'])==20)
check('main reference gap27 preserved',[r['number'] for r in facts['references'] if r['id'].startswith('main-')]==list(range(1,27))+[28])
check('four SI references',[r['number'] for r in facts['references'] if r['id'].startswith('si-')]==[1,2,3,4])
check('all ten conflicts',len(facts['conflicts'])==10 and {c['id'] for c in facts['conflicts']}=={'C'+str(i) for i in range(1,11)})
check('literal CeIII equation',facts['equations'][1]['raw_expression']=='Ce(III) = I_v0 + I_u0 + I_v + I_u′')
check('literal TEA formula',next(m for m in facts['materials'] if m['id']=='tea')['source_formula_or_abbreviation']=='(C2H5OH)3N')
check('no scientific model/task/publication admission',facts['training_eligibility'] is False and facts['independent_audit_status']=='pending' and assets['public_admission'] is False)

# Crop author receipt: all20 actual crops were viewed in contacts plus the five revised
# full-size images; this check replays unchanged native image crops, not model inference.
pdfs={r:pdfium.PdfDocument(d['source_path']) for r,d in docs.items()}
for a in assets['assets']:
 check(a['id']+' image hash',sha(a['path'])==a['sha256'])
 im=Image.open(a['path']);check(a['id']+' dimensions',list(im.size)==a['dimensions'])
 pg=pdfs[a['document_role']][a['pdf_page']-1]
 native=pg.render(scale=a['dpi']/72).to_pil().crop(a['crop_box_pixels'])
 check(a['id']+' replayed native crop pixels',native.mode==im.mode and native.size==im.size and native.tobytes()==im.tobytes())
 pg.close()
 check(a['id']+' selected excerpt not full page',not a['contains_complete_source_page'] and not a['scientific_image_pixels_modified'])
 a['actual_author_preview_review']=True
 a['author_preview_scope']='Actual contact-sheet view; revised Figure3, as-prepared XRD excerpt/continuation and mechanism excerpt/continuation additionally opened at full size.'
for pdf in pdfs.values():pdf.close()
assets['status']='author_reviewed_original_crops_pending_independent_audit'
save('original-assets-manifest.json',assets)
manual=[
 'All eight retained source pages read in text and visually inspected; source roles and useful recipe confirmed.',
 'All twenty selected crops actually viewed; Figure3 caption right edge repaired before freeze; two page-break excerpt pairs explicitly labelled.',
 'Six stocks preserve solvent-specific nitrate/TEA identities and separate concentrations/transfer volumes.',
 'Diagnostic filtrate does not become main precipitant; wash/dry/acetone order and unknown calcination atmosphere retained.',
 'Local TEM and SAED assignments do not establish a pure as-prepared bulk composition.',
 'All four Figure1 scale bars are5nm; calcined panel additionally labels111.',
 'DLS radii/diameters conflict retained; TEM crystallite, DLS particle and BET-derived diameter remain distinct.',
 'Thermal interpretation and literature temperatures remain distinct from the200C post-treatment.',
 'XPS short/long exposure and calcined/as-prepared scopes retained, including uncertain printed figure references.',
 'All twenty TableS1 numbers visually transcribed with literal spin-orbit labels; no repaired physics labels.',
 'Literal TEA reaction, CeIII unprimed Iv, calibration884.5/table884.8 and absent reference27 retained.',
 'No reconstructed yield, phase fractions, spectral arrays, atomic coordinates or training admission.'
]
receipt={'schema':'mattersyn-author-visual-receipt/1','author':AUTHOR,'at':datetime.now(timezone.utc).isoformat(),'status':'author_review_completed','scope':manual,'actual_page_views':8,'actual_selected_crop_views':20,'asset_hashes':{a['path']:a['sha256'] for a in assets['assets']},'independent_audit':False}
save('author-visual-review.json',receipt)
notes=(P/'extraction-notes.md').read_text(encoding='utf8').replace('Selected original crops are author candidates pending actual crop review and independent audit.','Twenty selected original crops were actually viewed and replayed against the original PDF pixels. They remain unapproved publication candidates pending independent scientific review.')
(P/'extraction-notes.md').write_text(notes,encoding='utf8')
report={'schema':'mattersyn-source-author-validation/1','author':AUTHOR,'status':'passed_author_checks','at':datetime.now(timezone.utc).isoformat(),'counts':inv['counts'],'checks_total':len(checks),'checks_passed':sum(x['passed'] for x in checks),'checks':checks,'manual_review':manual,'scope_limit':'Author transport/readability checks; not an independent scientific audit. No canonical/model/browser/publication admission.','failures':[]}
save('author-validation.json',report)
files=[p for p in P.iterdir() if p.is_file() and p.suffix in ['.py','.json','.md']]
files += list((P/'source-render').rglob('*'))+list((P/'reader-assets').rglob('*'))
files += [Path(d['source_path']) for d in docs.values()]+[Path(prep['intake_manifest']['path'])]
bound={str(p.resolve()):sha(p) for p in sorted(set(files)) if p.is_file()}
freeze={'schema':'mattersyn-source-extraction-freeze/1','author':AUTHOR,'at':datetime.now(timezone.utc).isoformat(),'source_id':'pati2009','doi':'10.1021/la8031286','version':1,'status':'frozen_pending_independent_source_audit','source_generation':1,'bundle_sha256':prep['bundle_sha256'],'counts':inv['counts'],'bound_files':bound,'author_validation_sha256':sha(P/'author-validation.json'),'private_full_source_paths':[str(P/'source-render'),*[d['source_path'] for d in docs.values()]],'pending_gates':['independent source/scientific audit','canonical authoring and independent review','source-qualified viewers','public projection/integration/browser review'],'source_uncertainties':['DLS radius/diameter definition','as-prepared bulk phases','TEA formula/reaction typography','mechanistic complex inconsistency','XPS exposure/labels/equations/calibration discrepancies','missing main reference27'],'public_admission':False,'training_admission':False}
save('package-freeze.json',freeze)
print(json.dumps({'freeze_sha256':sha(P/'package-freeze.json'),'facts_sha256':sha(P/'source-facts.json'),'inventory_sha256':sha(P/'source-inventory.json'),'bound_files':len(bound),'author_checks':len(checks),'counts':inv['counts']},indent=2))
