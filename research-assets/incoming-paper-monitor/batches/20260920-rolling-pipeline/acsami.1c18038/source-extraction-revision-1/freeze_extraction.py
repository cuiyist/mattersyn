"""Validate and freeze only the author's supplied-PDF extraction; never touches audit files."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
from collections import Counter
import json,hashlib,re,math
from PIL import Image
P=Path(__file__).resolve().parent
NOW=datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n):return json.loads((P/n).read_bytes())
def write(n,o):(P/n).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
s=load('source-facts.json');t={x['id']:x for x in s['tables']};f={x['id'].removeprefix('lian2021-'):x for x in s['facts']};payload=load('complete-source-payloads.json');docs={d['document_id']:d for d in payload['documents']};inv=load('source-inventory.json');assets=load('original-assets-manifest.json');coverage=load('page-coverage.json');checks=[]
def ck(name,ok,details=None):
 checks.append({'name':name,'passed':bool(ok),'details':details});assert ok,(name,details)
for a in payload['source_copies']:ck('actual-source-bytes '+a['original_filename'],sha(a['source_path'])==a['sha256'])
ck('coverage34',len(coverage['pages'])==34 and all(x['text_read_in_full']and x['native_page_image_visually_inspected']for x in coverage['pages']))
for pg in coverage['pages']:
 for k in ['text','render']:ck(k+' cache identity '+pg['document_role']+str(pg['pdf_page']),sha(pg[k+'_path'])==pg[k+'_sha256'])
 ck('page-specific substantive notes '+pg['document_role']+str(pg['pdf_page']),len(pg['scope_notes'])>60)
for n,want in [(1,36),(2,29),(3,32),(4,38),(5,40),(6,32),(7,36),(8,32),(9,36)]:
 tab=t['table-s'+str(n)];ck('Table S'+str(n)+' rows',len(tab['rows'])==want)
 labels=[r['row_label']for r in tab['rows']];ck('Table S'+str(n)+' unique row identities',len(set(labels))==len(labels))
 for r in tab['rows']:
  for c in r['cells']:
   ev=c['evidence'][0];ck(c['id']+' locator',ev['source_sha256']==docs['si']['source_sha256'] and 1<=ev['pdf_page']<=26)
   if n>1:
    ck(c['id']+' raw token on exact source line',c['raw_text']in r['source_raw_line'])
    ck(c['id']+' exact original line',r['source_raw_line']==docs['si']['pages'][ev['pdf_page']-1]['text'].splitlines()[r['source_line']-1])
   raw=c['raw_text'];m=re.fullmatch(r'(-?\d+(?:\.\d+)?)\((\d+)\)',raw)
   if m:
    sc=Decimal(str(c['printed_to_value_scale']));v=Decimal(m[1]);esd=Decimal(m[2])*Decimal(10)**(-len(m[1].split('.')[1])if'.'in m[1]else 0)
    ck(c['id']+' value scale',c['value']==float(v*sc));ck(c['id']+' uncertainty scale',c['uncertainty']==float(esd*sc))
   if c.get('column')in['x','y','z']:ck(c['id']+' fractional scale',c['printed_to_value_scale']==1e-4 and c['unit']=='fractional_coordinate')
   if str(c.get('column','')).startswith('U'):ck(c['id']+' ADP scale',c['printed_to_value_scale']==1e-3 and c['unit']=='angstrom^2')
ck('table copies identical',s['tables']==load('source-tables.json')['tables'])
ck('total891tablecells',sum(len(r['cells'])for tab in t.values()for r in tab['rows'])==891)
for coords,adps,counts in [(6,8,{'Sb':1,'Cl':5,'N':2,'C':24}),(7,9,{'Sb':2,'Cl':8,'N':2,'C':24})]:
 names=[r['row_label']for r in t[f'table-s{coords}']['rows']]
 ck('coordinate/ADP atom order '+str(coords),names==[r['row_label']for r in t[f'table-s{adps}']['rows']])
 ck('heavy atom inventory '+str(coords),Counter(re.match(r'[A-Z][a-z]?',n)[0]for n in names)==counts)
 for bn in ([2,4]if coords==6 else[3,5]):
  for row in t[f'table-s{bn}']['rows']:ck('geometry atom references '+str(bn)+' '+row['row_label'],all(a in names for a in row['atoms']))
 ck('literal ADP order '+str(adps),t[f'table-s{adps}']['columns']==['U11','U22','U33','U23','U13','U12'])
ck('negative fractional coordinate preserved',next(r for r in t['table-s6']['rows']if r['row_label']=='C00W')['cells'][1]['value']==-.0042)
ck('fractional coordinates not wrapped',any(c['value']>1 for n in[6,7]for r in t[f'table-s{n}']['rows']for c in r['cells'][:3]))
for fid,idx,value,unit in [('acquisition-beta',0,.4,'MeV'),('nc-stock',2,2000,'uL'),('nc-injection',0,500,'uL'),('nc-recovery',0,7000,'rpm'),('nc-recovery',1,3,'min'),('a-plqe',0,96.8,'%'),('nc-plqe',0,89.3,'%'),('spincoat-deposit',3,80,'degC'),('spincoat-deposit',4,30,'min')]:
 q=f[fid]['quantities'][idx];ck('source-critical quantity '+fid+str(idx),q['value']==value and q['unit']==unit)
ck('thermal inequality preserved',f['thermal-stability']['quantities'][0]['comparison']=='>')
ck('force inequality preserved',f['dft-method']['quantities'][-1]['comparison']=='<')
ck('PSapproximation preserved',f['chemicals']['quantities'][-1]['approximate'])
ck('all five blend ratio parts including zeros',[q['components']for q in f['composite-mixing']['quantities'][:5]]==[[1,0],[1,3],[1,2],[2,3],[0,1]])
ck('nanocrystal uncertainty unassigned',f['nc-phase-size']['quantities'][1]['uncertainty_definition']=='not specified')
ck('no B numericzeroPLQE',all(q['meaning']!='PLQE'for q in f['b-nonemission']['quantities']))
ck('DFT gap computation scope',f['dft-gaps']['claim_class']=='author_interpretation')
ck('calculationmeshnotinverted',f['dft-method']['quantities'][1]['components']==[2,4,4]and f['dft-method']['quantities'][2]['components']==[4,4,4])
ck('source comparisons retained',set(c['id']for c in s['conflicts'])=={'C1','C2','C3','C4'})
ck('missing attachments explicit',any(x['id']=='G9'and'ZIP'in x['description']and'MP4'in x['description']for x in s['gaps']))
ck('no approved training/model',s['training_admission']=={'approved':False,'requested_tasks':[],'exact_recipe_structure_pair':False,'atomistic_model_qualified':False})
ck('five preparation protocols',sum(p['kind']in['synthesis','synthesis_variant','film_processing']for p in s['protocols'])==5)
ck('distinctstocksnoinventedconcentrations',len(s['stocks'])==5 and all(x.get('concentration')is None for x in s['stocks']))
ck('frozen inventory pointers resolve',all(s[u['json_pointer'].split('/')[1]][int(u['json_pointer'].split('/')[2])]['id']==u['id']for u in inv['inventory_units']))
factids={x['id']for x in s['facts']}
for pr in s['protocols']:
 for o in pr['operations']:
  ck('operation linked facts '+o['id'],all(x in factids for x in o['source_fact_ids']))
  for qv in o['quantities']:ck('operation typed quantity source '+o['id']+' '+qv['meaning'],any(qv==q0 for fid in o['source_fact_ids']for q0 in next(x for x in s['facts']if x['id']==fid)['quantities']))
assetids={a['id']for a in assets['assets']}
ck('53selectedassets',len(assetids)==53)
for key in['figures','tables','equations']:
 for u in s[key]:ck('all sourceobject assets '+u['id'],bool(u['asset_ids'])and all(x in assetids for x in u['asset_ids']))
for a in assets['assets']:
 ck('original crop hash '+a['id'],sha(a['path'])==a['sha256'])
 ck('original crop dimensions '+a['id'],list(Image.open(a['path']).size)==a['pixel_dimensions'])
 ck('no wholepage selected '+a['id'],not a['whole_source_page']and a['bbox_normalized']!=[0,0,1,1])
 a['manual_visual_review']='Extraction author viewed every crop on9contact sheets; four adjusted equation/table headings directly re-viewed at native crop resolution; all original34page images had been read/viewed.'
ck('mainrefs1to27',[r['number']for r in s['references']if r['document_role']=='main']==list(range(1,28)))
ck('sirefs1to3',[r['number']for r in s['references']if r['document_role']=='si']==[1,2,3])
ck('reference footer excluded',all('www.acsami.org Research Article'not in r['citation']for r in s['references']))
write('original-assets-manifest.json',assets)
diag=[]
for n in[2,3]:
 by={}
 for r in t[f'table-s{n}']['rows']:
  if r['atoms'][0].startswith('Sb'):by.setdefault(r['atoms'][0],[]).append(r['cells'][0]['value'])
 for atom,vals in by.items():
  mean=sum(vals)/len(vals);delta=sum(((x-mean)/mean)**2 for x in vals)/len(vals)
  diag.append({'table':f'table-s{n}','site':atom,'bond_count':len(vals),'derived_mean_angstrom':mean,'derived_delta_d':delta,'kind':'author_arithmetic_diagnostic_not_reported_scalar','source_values_unchanged':True})
for n,den in[(4,7),(5,4)]:
 by={}
 for r in t[f'table-s{n}']['rows']:
  if r['atoms'][1].startswith('Sb')and r['cells'][0]['value']<120:by.setdefault(r['atoms'][1],[]).append(r['cells'][0]['value'])
 for atom,vals in by.items():diag.append({'table':f'table-s{n}','site':atom,'near90_angle_count':len(vals),'derived_sigma2_deg2':sum((v-90)**2 for v in vals)/den,'selection':'Angles near90 rather than near180, using source selected-angle count and denominator; no source value replaced.'})
write('source-consistency-diagnostics.json',{'schema':'mattersyn-source-author-diagnostics/1','author':'/root/backlog_eta','source_tables_sha256':sha(P/'source-tables.json'),'diagnostics':diag,'interpretation':'A reproduces the main distortion to printed precision. B main metrics most nearly match Sb02, but this source-centre assignment is not explicit; retain C1 and both complete sites. Main Stokes shift221nm differs by1nm from612-392; retain C2. Both listed space groups are centrosymmetric; no claim that A lacks inversion.','atomistic_model_approval':False,'independent_audit_status':'pending'})
visual={'schema':'mattersyn-source-crop-author-review/1','author':'/root/backlog_eta','reviewed_at':NOW,'status':'author_viewed_independent_audit_pending','actual_manual_scope':{'source_pages_text_read':34,'source_pages_images_viewed':34,'selected_crops_viewed_on_contact_sheets':53,'contact_sheets_viewed':9,'adjusted_crops_directly_viewed':['si-distortion-angles','table-s6-heading','table-s8-a','table-s9-a'],'all_table_rows_read_on_native_page_images':True},'bound_assets':{a['path']:a['sha256']for a in assets['assets']},'contact_sheets':{str(p):sha(p)for p in sorted((P/'private').glob('crop-contact-*.png'))},'limitations':['This records actual author reading/viewing; it is not an independent audit or browser review.','Figures and curves remain source artwork; plotted points were not digitized.']}
write('author-visual-review.json',visual)
validation={'schema':'mattersyn-extraction-author-validation/1','author':'/root/backlog_eta','validated_at':NOW,'status':'passed_author_checks_independent_audit_pending','counts':s['counts'],'checks_count':len(checks),'checks':checks,'actual_manual_scope':visual['actual_manual_scope'],'independent_audit':False,'bound_core_files':{str(P/n):sha(P/n)for n in['source-facts.json','source-inventory.json','source-tables.json','page-coverage.json','pairing-review.json','relevance-screening.json','original-assets-manifest.json','source-consistency-diagnostics.json','author-visual-review.json']}}
write('author-validation.json',validation)
notes=f'''# Lian 2021 supplied-source extraction\n\nDOI10.1021/acsami.1c18038. Author: /root/backlog_eta. This is a private author extraction; independent review, canonical admission and model qualification remain pending.\n\nAll8main and26SI PDF pages were read and individually visually inspected. The exact title/nine authors and main/SI content continuity support pairing. Main declares an additional crystal ZIP and scintillation MP4. A filename-identifier search across both source roots found only the paired PDFs; unlabelled files are not ruled out. No cited attachment was downloaded.\n\nThe extraction contains57facts/134fact quantities,9tables/311typed rows/891cells(885numeric),15materials,5stock descriptions,9protocols/21operations,14sample contexts,21figures including graphical abstract,1scheme,6equations,30reference entries and53selected original crops. All nine crystallographic tables retain raw tokens, atom IDs, uncertainty scales and page/block locators. S1 compound/reference fields are six nonnumeric cells; no null numeric result was fabricated.\n\nThe five preparation procedures are bulk A growth, bulk B variant, A LARP nanocrystals, five-ratio composite films and separate precursor spin-coating. The remaining protocol groups concern acquisition and DFT. Bulk stoichiometry and DMF charges remain distinct from LARP and spin-coating stocks; solvent charge does not prove final stock volume. NC PLQE89.3% is a dried-powder result; bulk PLQE96.8% is a single-crystal result. Non-emissive B,5min colloidal settling and separate film controls are retained. The beta electron energy is0.4MeV.\n\nC1 preserves the main B mean/distortion values beside two independent SI Sb sites; author diagnostics suggest Sb02 but do not assign it as a source fact. C2 preserves221nm Stokes shift beside612/392nm numbers. C3 prevents the parity narrative being turned into a false noncentrosymmetric-A claim. C4 leaves the6.43±0.17nm uncertainty type unknown. Ten explicit missingness items cover reproducibility, figures/raw arrays, physical sample joins, model files and attachments.\n\nS6/S7 supply68heavy-atom coordinate rows and S8/S9 supply68ADP rows. No hydrogens or occupancy columns are supplied. These are bulk-crystal source tables, not nanocrystal coordinates, a complete supplied CIF, relaxed DFT coordinates, or an approved recipe–structure training pair. No spectrum/pattern array was invented.\n\nSource-render/, private/text/ and complete-source-payloads.json contain whole-source material and must remain private. Reader-assets contains selected crops with exact rectangles and source hashes; no public import is approved by this extraction.\n\nAuthor checks: {len(checks)} passed. All53crops were viewed on9contact sheets; four tightened/expanded heading crops were additionally opened directly after correction. A distinct reviewer must bind the final freeze.\n'''
(P/'extraction-notes.md').write_text(notes,encoding='utf-8')
names=['prepare_sources.py','source_author_data.py','build_extraction.py','freeze_extraction.py','complete-source-payloads.json','source-facts.json','source-inventory.json','source-tables.json','page-coverage.json','pairing-review.json','relevance-screening.json','original-assets-manifest.json','source-consistency-diagnostics.json','author-visual-review.json','author-validation.json','extraction-notes.md']
files=[P/n for n in names]+list((P/'private').rglob('*'))+list((P/'source-render').glob('*.png'))+list((P/'reader-assets').glob('*.png'))
files=sorted({p.resolve()for p in files if p.is_file()})
bound={str(p):sha(p)for p in files}
for a in payload['source_copies']:bound[a['source_path']]=a['sha256']
manifest={'schema':'mattersyn-source-extraction-freeze/1','source_id':s['source_id'],'doi':s['doi'],'title':s['title'],'author':'/root/backlog_eta','frozen_at':NOW,'revision':1,'source_generation':1,'bundle_sha256':s['bundle_sha256'],'status':'author_complete_supplied_pdfs_independent_audit_pending','counts':s['counts'],'author_check_count':len(checks),'bound_files':bound,'bound_file_count':len(bound),'private_scope':['No Site/sharedledger/source edits.','Full source payloads/page images and text caches private.','Absent citedZIP/MP4 not read.','Independent audit, canonical records, browser and atomic-model gates not completed by this package.'],'independent_audit':False}
write('package-freeze.json',manifest)
print(json.dumps({'package':str(P/'package-freeze.json'),'sha256':sha(P/'package-freeze.json'),'source_facts_sha256':sha(P/'source-facts.json'),'source_tables_sha256':sha(P/'source-tables.json'),'bound_files':len(bound),'checks':len(checks)},ensure_ascii=False))
