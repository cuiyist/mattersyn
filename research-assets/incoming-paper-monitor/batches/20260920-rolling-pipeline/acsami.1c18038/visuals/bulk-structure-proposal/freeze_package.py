import json,hashlib,datetime
from pathlib import Path
O=Path(__file__).resolve().parent;L=O.parent.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
freeze=O/'package-freeze.json'
if freeze.exists():raise RuntimeError('Package already frozen; preserve and version any revision.')
for p,h in load(O/'input-bindings.json')['bound_files'].items():assert sha(p)==h,p
for name in ['geometry-validation.json','transport-validation.json','viewer-validation.json']:assert load(O/name)['status']=='passed'
screens=['bulk-a-asu.png','bulk-a-rotated.png','bulk-a-expanded.png','bulk-b-asu.png','bulk-b-expanded.png']
visual={
 'status':'passed_author_preview_scope','author':'/root/peng1998_reader_assets','tool':'mcp__cua_repl; native in-app browser tab on localhost',
 'preview_url':'http://127.0.0.1:5293/preview.html','actual_scope':['Read main pages 2 and 6 and SI pages 13–26 as full-page source images.','Viewed both asymmetric-unit panels and both geometric expansions.','Observed A drag rotation, B zoom and deterministic reset.','Confirmed 32/36 listed and 64/144 expanded marker descriptions, unknown-occupancy warnings, two separate Sb environments in B, source-only ASU links and no guessed expanded bonds.','Read the rendered bulk/sample/batch caveats and download URLs.','Corrected initial reset orientation accumulation and expansion framing before final captures.','Captured no browser warning/error entries during the checked preview session.'],
 'source_page_images':{str(L/'source-render'/f'main-{n:02d}.png'):sha(L/'source-render'/f'main-{n:02d}.png') for n in [2,6]},
 'final_screenshots':{str(O/'author-preview'/f):sha(O/'author-preview'/f) for f in screens},
 'module_sha256':sha(O/'lian2021-bulk-viewer.mjs'),'css_sha256':sha(O/'lian2021-bulk-viewer.css'),
 'earlier_preview_evidence':['author-preview/asu-initial.png is the initial smaller-framing capture.','author-preview/bulk-b-asu-zoom.png records the zoom interaction before the reset/framing polish; source geometry is unchanged.'],
 'browser_logs':load(O/'author-preview/browser-logs.json'),
 'not_claimed':['independent scientific approval','Site integration or mounted runtime approval','public deployment','all responsive viewports','complete crystal or DFT eligibility']}
visual['source_page_images'].update({str(L/'source-render'/f'si-{n}.png'):sha(L/'source-render'/f'si-{n}.png') for n in range(13,27)})
write(O/'author-visual-check.json',visual)
own={str(p.relative_to(O)).replace('\\','/'):sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='package-freeze.json'}
bound=load(O/'input-bindings.json')['bound_files']|visual['source_page_images']
write(freeze,{'schema':'mattersyn.private_bulk_structure_proposal.v1','source_id':'lian2021','author':'/root/peng1998_reader_assets','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'frozen_author_proposal_pending_independent_audit','own_files':own,'bound_files':bound,'counts':{'models':2,'listed_non_h_sites':68,'geometric_positions':208,'source_table_cells':891,'bindings':4,'public_files':6,'author_mechanical_checks':971+2367+668},'independent_audit_passed':False,'site_modified':False,'canonical_modified':False,'training_admitted':False,'original_documents_modified':False})
print(json.dumps({'freeze_sha256':sha(freeze),'own_files':len(own),'bound_inputs':len(bound),'models':{p.name:sha(p) for p in O.glob('lian2021-bulk-*-non-h.json')},'cifs':{p.name:sha(p) for p in O.glob('*.cif')},'bindings_sha256':sha(O/'product-bindings-proposal.json'),'module_sha256':sha(O/'lian2021-bulk-viewer.mjs')},indent=2))
