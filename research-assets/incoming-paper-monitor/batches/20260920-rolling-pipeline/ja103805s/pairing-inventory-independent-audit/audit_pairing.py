"""Independent, bounded Evans identity/pairing and checkpoint audit. Read-only sources."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re
from pypdf import PdfReader
O=Path(__file__).resolve().parent;E=O.parent;F=E/'checkpoint-freeze.json';C=E/'checkpoints/pairing-inventory-v1'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[];bound={}
def ck(ok,label):
 checks.append({'check':label,'passed':bool(ok)})
 if not ok:raise AssertionError(label)
def bind(p):p=Path(p);bound[str(p.resolve())]=sha(p);return p
freeze=load(F);pair=load(C/'pairing-review.json');inv=load(C/'source-inventory.json');prep=load(C/'source-preparation.json')
ck(sha(F)=='e3efb493e141e7b76ada2c6769170e9d43527715772e6f32835e1ca0266ad782','Parent-specified frozen checkpoint hash');bind(F)
for f in freeze['files']:
 p=bind(f['path']);ck(sha(p)==f['sha256'],'Exact checkpoint file '+p.name);ck(p.stat().st_size==f['bytes'],'Checkpoint size '+p.name)
for role,d in freeze['source_documents'].items():
 p=bind(d['path']);ck(sha(p)==d['sha256'],'Unchanged original '+role);ck(p.stat().st_size==d['bytes'],'Original size '+role)
 if role!='cif':
  ck(p.read_bytes().startswith(b'%PDF-'),'Detected PDF '+role);ck(len(PdfReader(p).pages)==d['page_count'],'Actual page count '+role)
for doc in prep['documents']:
 for k in ('text_pages','rendered_pages'):
  for f in doc.get(k,[]):
   p=bind(f['path']);ck(sha(p)==f['sha256'],'Unchanged prepared cache '+p.name)
ck(pair['source_documents']==freeze['source_documents'],'Pairing source identities agree')
ck(inv['all_training_admission'] is False and pair['canonical_or_training_approval'] is False,'No checkpoint training approval')
ck(inv['independent_scientific_audit']=='pending','Complete scientific audit remains pending')
ck(len(inv['page_inventory'])==24,'Inventory contains all 24 PDF page slots')
ck({(p['source_role'],p['pdf_page']) for p in inv['page_inventory']}=={('main',i) for i in range(1,4)}|{('si',i) for i in range(1,22)},'Inventory page slots unique and complete')
objects=inv['figure_table_scheme_inventory'];ck(len(objects)==23,'23 checkpoint figure/table/scheme objects')
expected={'figure-1','figure-2','table-1','scheme-1','scheme-2','scheme-S1','scheme-S13-unnumbered'}|{f'figure-S{i}' for i in range(1,17)}
ck({o['id'] for o in objects}==expected,'Checkpoint contains all declared figure/table/scheme IDs')
for o in objects:
 ck(o['source_sha256']==freeze['source_documents'][o['source_role']]['sha256'],'Object source hash '+o['id'])
 ck(1<=o['pdf_page']<=freeze['source_documents'][o['source_role']]['page_count'],'Object page bounds '+o['id'])
 ck(o['independent_review_status']=='pending','No object claimed audited '+o['id'])
 ck(Path(o['source_page_asset']).is_file(),'Original page image exists '+o['id'])
ck('CIF scalar fields and all atom/anisotropy/geometry loops' in inv['additional_source_units_to_type'],'Incomplete CIF semantic extraction explicitly pending at checkpoint')
texts={}
for role,pages in {'main':[1,3],'si':[1,15,16,17,19,20]}.items():
 for page in pages:
  p=bind(E/'reader-assets'/f'{role}-{page:02}.txt');texts[(role,page)]=p.read_text(encoding='utf-8-sig')
title='Mysteries of TOPSe Revealed: Insights into Quantum Dot Nucleation'
for key in [('main',1),('si',1)]:
 t=texts[key];ck(title in t,'Actual title '+str(key))
 for name in ['Christopher M. Evans','Meagan E. Evans','Todd D. Krauss']:ck(name in t,'Actual byline '+str(key)+' '+name)
ck('10.1021/ja103805s' in texts[('main',1)],'Printed main DOI')
ck('X-ray crystal structure of species 9' in texts[('main',3)],'Main explicitly declares species9 structural SI')
ck('Synthesis of PbSe QDs' in texts[('si',19)] and 'Synthesis of CdSe QDs' in texts[('si',19)],'SI actual two QD preparation headings')
ck('Single crystal of 9' in texts[('si',16)] and '500' in texts[('si',16)] and '100' in texts[('si',16)],'Separate species9 molecular-crystal preparation supplied')
cif=Path(freeze['source_documents']['cif']['path']).read_text(encoding='utf-8')
for token in ['data_krace01',"'C24 H20 P2 Pb Se4'",'9.0041(4)','11.0498(5)','12.8215(6)','80.593(1)','89.867(1)','82.296(1)','1246.89(10)','100.0(1)','29063','2.9969(4)','3.0350(4)','3.4029(4)']:
 ck(token in cif,'Actual CIF identity/cell/contact anchor '+token)
for name in ['Pb1','Se1','Se2','Se3','Se4','P1','P2']+[f'C{i}' for i in range(1,25)]:
 ck(re.search(r'^'+re.escape(name)+r'\s+(?:Pb|Se|P|C)\s+[-0-9]',cif,re.M) is not None,'Actual CIF atom label '+name)
ck(cif.index('_publ_section_references')<cif.index('data_krace01'),'Original nonstandard pre-block references retained')
ck('10.1021/ja103805s' not in cif and title not in cif,'CIF not falsely claimed to contain DOI/title')
ck(pair['cif_scope']['quantum_dot_structure_pair'] is False,'CIF/QD exclusion explicit')
assets=load(E/'selected-original-assets.json');tem=next(a for a in assets['assets'] if a['id']=='figure-S16');bind(E/'selected-original-assets.json');bind(tem['path']);ck(sha(tem['path'])==tem['sha256'],'Viewed final-author high-resolution TEM crop matches its manifest')
visual_scope={'main':[1,3],'si':[1,15,16,17,19,20]}
for role,pages in visual_scope.items():
 for page in pages:bind(E/'reader-assets'/(f'main-{page}.png' if role=='main' else f'si-{page:02}.png'))
finding={'id':'checkpoint-tem-scale-bar','status':'known_stale_value_excluded_from_checkpoint_approval','source_locator':'SI S20 Figure S16 right TEM scale bar','checkpoint_pointer':'/page_inventory/22/coverage_notes','checkpoint_value':'20 nm','visually_confirmed_high_resolution_value':'50 nm','scope':'Right scale bar only; neither bar is a particle diameter. The source source_image was not altered. Final extraction revision must bind the corrected value; no checkpoint overwrite.','evidence_path':tem['path'],'evidence_sha256':tem['sha256']}
manual=[
 {'scope':'Main/SI identity','locators':['Main PDF1 title, byline, DOI, journal footer','SI S1 title and byline','Main PDF3 SI declaration'],'result':'Full title and all three authors agree. Main explicitly declares QD synthesis details, NMR, observed products and species9 crystal structure; supplied SI contains those components.'},
 {'scope':'Molecular crystal versus QD coordinates','locators':['SI S15 Figure S12 and crystal/refinement paragraph','SI S16 Scheme S1 and slow-evaporation preparation','SI S17 Figure S13 and contact discussion','Original CIF header, cell/experiment/atom and matching geometry tags'],'result':'CIF belongs to species9 Pb(Se2PPh2)2, C24H20P2PbSe4. Matching atom labels, yellow rod dimensions,100.0(1)K,P-1,Bruker equipment,29063reflections and three cited Pb-Se distances support content pairing. It is not a PbSe/CdSe QD structure or an isolated structure of proposed1/6/14.'},
 {'scope':'Sample boundaries and relevance','locators':['SI S19 explicit PbSe/CdSe QD procedures','SI S20 Figures S15/S16'],'result':'The QD procedures establish synthesis relevance. Optical examples and TEM particle packing remain distinct from species9 molecular crystal. TEM superlattice packing is not an independently solved QD atomic structure.'},
 {'scope':'Checkpoint inventory boundaries','locators':['Frozen source-inventory.json','Frozen extraction-notes.md','Frozen page-coverage.json'],'result':'Page/object ledger is internally complete at inventory level. It explicitly leaves quantitative CIF extraction, dense spectra, full fact extraction and scientific audit pending. Cache/hash checking is not a claim to have read every page in this audit.'},
 {'scope':'TEM scale-bar correction','locators':['Actual high-resolution figure-S16.png','SI S20 full-page render'],'result':'The high-resolution original crop clearly reads50nm on the right; the earlier20nm inventory value is excluded. Left reads5nm. This audit does not approve the still-developing full extraction.'}
]
report={'schema':'mattersyn-independent-pairing-inventory-audit/1','source_id':'evans2010','auditor':'/root/peng1998_reader_assets','author':'/root/norberg2004_extract','at':datetime.now(timezone.utc).isoformat(),'status':'passed_pairing_and_inventory_boundaries_with_known_stale_scale_value_excluded','bound_checkpoint_sha256':sha(F),'checked_source_roles':['main_pdf','supporting_information_pdf','molecular_crystal_cif'],'counts':{'pdf_pages_in_bundle':24,'pdf_pages_actually_read_and_visually_inspected':8,'checkpoint_object_ids_checked':23,'mechanical_checks':len(checks),'manual_scopes':len(manual)},'actual_source_reading':{'text_pages':visual_scope,'visual_pages':visual_scope,'additional_visual_assets':[{'path':tem['path'],'sha256':tem['sha256'],'scope':'Both original TEM panels, scales and caption'}],'cif_scope':'Header/formula, cell/experiment metadata, source atom-label inventory and selected SI-matching geometry rows; not a full loop-value or atomic geometry audit.'},'manual_review':manual,'checks':checks,'findings':[finding],'open_pairing_findings':[],'remaining_gates':['Separate complete scientific audit of final extraction, all facts and selected assets','Full CIF raw loop transport/semantic validation and any structure-viewer qualification','Canonical, reader, model/binding and integration audits','No training/publication approval from this checkpoint audit'],'no_source_or_checkpoint_edits':True,'training_approved':False,'publication_approved':False,'bound_files':bound}
O.mkdir(exist_ok=True);(O/'independent-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=f'''# Evans 2010 pairing/inventory checkpoint audit

Passed the bounded source pairing and inventory-boundary review. The known stale right-TEM scale value is explicitly excluded from approval; this is not a complete scientific-extraction audit.

- Main:3 pages; SI:21 pages; supplied CIF. Original bytes and the specified checkpoint SHA are unchanged.
- Actually read and visually inspected main1,3 and SI1,15,16,17,19,20 (8 pages), plus the high-resolution Figure S16 crop. Other prepared pages were checked for identity/hash and inventory presence only.
- Matching full title/byline and the main SI declaration establish main/SI association. CIF pairing is content-supported by molecular composition, atom labels, crystal/acquisition metadata and contact distances; it lacks article DOI/title tags.
- CIF species9 is **C24H20P2PbSe4 / Pb(Se2PPh2)2**, not QD coordinates. Proposed1/6/14 and PbSe/CdSe QDs must not inherit it. SI S17's rocksalt-like contact argument is a proposed mechanism.
- The 23 object IDs and 24 page slots are internally complete at checkpoint level. This audit does not certify every source number or the author's full-page reading claim.
- Figure S16 right scale reads **50 nm** in the high-resolution original crop. The old20nm statement remains in the immutable early checkpoint and is specifically not certified here. The final author package should retain its correction history.

{len(checks)} mechanical checks and {len(manual)} actual manual scopes; {len(bound)} bound files. Full extraction, CIF semantics, canonical, viewer, training and publication gates remain separate. No source, checkpoint, Site or shared ledger was changed.
'''
(O/'independent-audit.md').write_text(md,encoding='utf-8');print(json.dumps({'status':report['status'],'checks':len(checks),'bound_files':len(bound),'audit_sha256':sha(O/'independent-audit.json')}))
