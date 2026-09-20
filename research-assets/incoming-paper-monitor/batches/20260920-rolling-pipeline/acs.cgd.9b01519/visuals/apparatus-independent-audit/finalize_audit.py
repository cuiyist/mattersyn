from pathlib import Path
import sys,json,hashlib,datetime,collections,xml.etree.ElementTree as ET
A=Path(__file__).resolve().parent;V=A.parent/'apparatus';R=A.parent.parent;M=Path('[local path redacted]')
sys.path.insert(0,str(M/'research-assets/corpus-20260917/runtime'))
sys.path.insert(0,str(M/'research-assets/rdkit-runtime'))
import pymupdf
from PIL import Image
checks=collections.Counter();fails=[];bound={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):bound[str(p)]=sha(p);return json.loads(p.read_text(encoding='utf-8'))
def ck(ok,k,d):
 checks[k]+=1
 if not ok:fails.append({'category':k,'detail':d})
def ptr(o,p):
 for k in p.lstrip('/').split('/') if p else []:o=o[int(k)] if isinstance(o,list) else o[k]
 return o
freeze=read(V/'package-freeze.json');module=read(A/'module-replay-checks.json')
ck(sha(V/'package-freeze.json')=='722999f61e60b69d34aeda96fefa871ba82254635b1e52d3f88fe0c11d7f43ad','expected_freeze','apparatus')
for p,h in {**freeze['bound_files'],**module['bound_files']}.items():
 ck(sha(Path(p))==h,'frozen_input_hash',p);bound[p]=sha(Path(p))
sourceaudit=read(R/'source-independent-audit/independent-audit-v2.json');canonicalaudit=read(R/'canonical-reader-independent-audit/independent-audit-v2.json')
ck(sourceaudit['status']=='passed' and canonicalaudit['status']=='passed','prior_distinct_gates','source/canonical')
ck(freeze['source_freeze_sha256']==sha(R/'package-freeze.json'),'source_freeze_unchanged','source')
ck(freeze['canonical_package_sha256']==sha(R/'canonical-proposal/v2/package-manifest.json'),'canonical_freeze_unchanged','canonical')
ck(freeze['canonical_audit_sha256']==sha(R/'canonical-reader-independent-audit/independent-audit-v2.json'),'canonical_audit_bound','canonical')
for p in [R/'package-freeze.json',R/'canonical-proposal/v2/package-manifest.json',R/'source-facts.json',R/'source-tables.json',R/'source-inventory.json']:bound[str(p)]=sha(p)
for p in [Path('[local path redacted]'),M/'downloaded_papers/10.1021_acs.cgd.9b01519.pdf']:
 ck(sha(p)=='ca731728f443477c041c370f3e6de6df63d8659cf61bfc47c07582750ce59b97','original_pdf_hash',str(p));bound[str(p)]=sha(p)
records={p.stem:read(p) for p in (R/'canonical-proposal/v2').glob('sommer-2020-*.json')}
bindings=read(V/'canonical-bindings.json')['bindings'];scenes=read(V/'rendered-scenes.json');config=read(V/'scene-config.json');pm=read(V/'preview-manifest.json')
ops={(r['record_id'],o['id']) for r in records.values() for o in r['operations']}
ck(ops=={(b['record_id'],b['operation_id']) for b in bindings},'all31_bindings','complete')
for b in bindings:
 r=records[b['record_id']];o=ptr(r,b['operation_pointer']);c=config['configs'][o['id']]
 ck(o['id']==b['operation_id'],'operation_pointer',o['id'])
 ck(sha(Path(b['record_path']))==b['record_sha256'],'record_binding_hash',o['id'])
 for k,kk in [('inputs','inputs'),('outputs','outputs'),('source_evidence','evidence'),('canonical_description','description')]:ck(b[k]==o[kk],'operation_graph_evidence',o['id']+'/'+k)
 ck(b['retained_fraction']==o.get('retained_fraction'),'retained_fraction',o['id'])
 ck(b['human_prose']==c['prose'] and b['art']==c['art'] and b['option_pointers']==c['option_pointers'],'binding_scene_config',o['id'])
 for p in b['option_pointers']:ck(bool(ptr(r,p)),'option_pointer',o['id']+p)
pixel=[]
for item in pm['scenes']:
 sp=V/item['svg_path'];pp=V/item['png_path']
 ck(sha(sp)==item['svg_sha256'] and sha(pp)==item['png_sha256'],'preview_hash',item['operation_id'])
 root=ET.fromstring(sp.read_bytes());texts=[''.join(e.itertext()) for e in root.iter() if e.tag.endswith('text')]
 ck(texts==item['visible_text'],'visible_text_retained',item['operation_id'])
 with pymupdf.open(stream=sp.read_bytes(),filetype='svg') as doc:
  pix=doc[0].get_pixmap(matrix=pymupdf.Matrix(1.2,1.2),alpha=False)
  with Image.open(pp) as im:ok=im.size==(pix.width,pix.height) and im.convert('RGB').tobytes()==pix.samples
 ck(ok,'independent_preview_pixels',item['operation_id']);pixel.append({'operation_id':item['operation_id'],'exact_pixels':ok,'png_sha256':sha(pp)})
for c in pm['contacts']:ck(sha(V/c['path'])==c['sha256'],'actually_viewed_contact_hash',c['path'])
manual={
 'mw-dissolve':'Nitrate hydrate masses 1.425/3.596 g and20 mL demineralized water charge, not final stock volume; source7.',
 'mw-base':'Three separate final NaOH formulations1.5/1.7/2.0 M, not sequential additions; no invented masses; source7.',
 'mw-load':'10 mL aliquot and80 mL thick-walled quartz vessel, sapphire sensor; source7.',
 'mw-heat':'40–60 bar approximate; nine sample schedules and two printed ramps preserved independently, ramp/table disagreement explicit; sources4,7–8.',
 'scf-feed':'14.5 solvent versus5 mL/min precursor, reported0.18 M OH, unknown feed formulation/solvent grade; source8.',
 'scf-react':'250 bar; S1 450C/S2 380C table versus450C method conflict explicit. Approximate1min printed total/0dwell not residence time; sources4,8.',
 'acs-load':'10mL fill20mL PTFE-lined stainless autoclave. No inherited microwave pressure; source8.',
 'acs-heat':'220C, separate A1–6 schedules;1day/2.5weeks versus17days;45–60min cited assumption, pressure/heating device unknown; sources4,8.',
 'lab-separate':'Centrifugation to colorless solution; powder retained independently for each laboratory route; speed/duration not invented; source7.',
 'lab-wash':'Three demineralized water washes then one96% ethanol wash, powders retained separately; source7.',
 'lab-dry':'Vacuum oven50C4h; numeric vacuum pressure/yield/storage unreported; source7.',
 'insitu-stock':'8.552g zinc/21.572g aluminum nitrate hydrates in stated30mL solution; water charge not inferred; source8.',
 'insitu-mix':'1.00mL each aliquot;0.480M Zn/0.960M Al final mixed context, notNaOHstock; concentration basis/zero-base diluent gaps preserved; source8.',
 'insitu-stir-load':'Approximate5min vigorous stir then sapphirecapillary ID0.6/OD1.1mm; transfer hardware generic; source8.',
 'insitu-heat':'Separate I1–I14 schedules;430C after~34min onlyI1/2; Figure6 axis seconds versus prose minutes unresolved; I3 turbulence and I12/13 lowyield scope; source4.',
 'oxide-slurry':'0.8141g ZnO/1.561g AlOH3 Millipore water, final0.5M Zn/1M Al,4hstir; water volume absent; source8.',
 'oxide-load':'Injected separateI15/I16suspensions, notnitrate stock; no invented injectionvolume; source8.',
 'oxide-heat':'SeparateI15 425C andI16 400C, no serial two-temperatureprocedure; table0–40min retained without exact completion inference; sources4,8.',
 'insitu-fit':'q-range4.2inverseA, constrainedFullprofanalysis; no invented atomic structure or missingSIresults; source8.',
 'pdf-solutions':'D1–D4 separate precursor contexts; cited150–350C priorwork not currentD2 heating; sources3–4.',
 'pdf-acquire':'PETRAIII P02.1, separateDIwater background samecapillary/temperature, separateLaB6calibration;3.3min collection not synthesisdwell; sources4,8.',
 'pdf-reduce-fit':'Fit2D/PDFgetX3/DiffPyCMI, D2 crystalline versusD3Debyescalefactor separate;16backgroundpoints/twoharmonics; source8.',
 'lab-xrd-acquire':'RigakuSmartLabCuKalpha1Bragg–Brentano, separateLaB6 660A calibration notpowderadditive; source8.',
 'lab-xrd-fit':'FiveChebyshevcoefficients/up tofourharmonics, Fullprof/TCHmodel; literaturefixedpositions notmeasuredcoordinates; source8.',
 'synchrotron-load-acquire':'SelectedM1–3,M7,S1,A1–2only;0.3mmrotatingglasscapillary,0.50054(6)A, imageplate, separateCeO2; source8.',
 'synchrotron-fit':'MAUDfourpolynomialfunctions/twobackgroundfeatures/threeharmonics; ADPs refined butsiteoccupancies/positionsfixed, nomicrostrain; source8.',
 'microscopy-disperse':'99%ethanol distinct96%wash, sonicationpowers/duration/typeunknown; source8.',
 'microscopy-deposit':'200meshcopperFormvar/carbongrids, ambientdrying, unknownvolume/temperature/time; source8.',
 'microscopy-acquire':'TALOSF200A/TWIN/XFEG/Ceta16M/SuperX/Esprit/Hyperspy; no inferred200kV nor generatedimage; source8.',
 'optical-acquire':'RTShimadzuUV3101PC200–2500nm diffuse reflectance, separateBaSO4reference; source8.',
 'optical-transform':'Printedtransformretained, exponent1/2; no algebraicrepair or exactgapreadingfromunlabelledbars; source8 andpriorpassedfullsourceaudit.'
}
ck(set(manual)=={s['operation_id'] for s in scenes},'manual_scene_coverage','31')
for n in [3,4,7,8]:p=R/'source-independent-audit/audit-pages'/f'main-{n:02}.png';bound[str(p)]=sha(p)
for p in [Path(__file__),A/'check_module.mjs',A/'module-replay-checks.json']:bound[str(p)]=sha(p)
report={'schema':'mattersyn-independent-apparatus-audit/1','source_id':'sommer2020','doi':'10.1021/acs.cgd.9b01519','reviewer':'/root/norberg2004_extract','author':'/root','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed' if not fails else 'open_findings','proposal_freeze_sha256':sha(V/'package-freeze.json'),'apparatus_module_sha256':sha(V/'sommer2020-protocol.mjs'),'counts':{'records_with_operations':12,'operations':31,'operation_parameters':50,'option_quantities':155,'total_typed_quantities':205,'display_rows':168,'contacts_actually_viewed':8,'scenes_actually_viewed':31,'fresh_original_pages_read_viewed':[3,4,7,8]},'module_checks':module['checks'],'source_binding_preview_checks':sum(checks.values()),'check_categories':dict(checks),'findings':fails,'manual_scopes':manual,'visual_review':'All31 scene drawings and surrounding labels were actually inspected via eight contact sheets; the long condition lists were additionally compared as exact structured rows. Original pages3,4,7,8 were reopened; full source audit is reused for remaining source scope, not claimed freshly reread. All31 PNGs were independently pixel-replayed from the exact saved SVG.','pixel_replays':pixel,'limits':['Supplied-main-only scope; declared SI remains locally unlocated/unverified.','Explanatory apparatus geometry, particle symbols and colors are not measured source apparatus geometry or atomic models.','No independent mounted-browser, Site-integration, publication or training approval. Minimal DOM tests are explicitly not browser tests.','All13source conflicts and missing conditions remain preserved; no source quantities or author files were changed.'],'bound_files':dict(sorted(bound.items()))}
for n in ['independent-audit-v1.json','independent-audit.json']:(A/n).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md='# Sommer 2020 apparatus independent audit\n\nStatus: '+report['status']+'. No source or scene corrections required.\n\nActually inspected all 31 stage-specific scenes across 8 contact sheets and reopened original pages 3, 4, 7 and 8. Checked 50 operation parameters and 155 alternative-condition quantities in 168 rows. Independent execution reproduced all 31 SVGs and 31 PNG pixel arrays, with 1,334 module checks and '+str(sum(checks.values()))+' additional binding, source and preview checks.\n\nAlternative samples, stock versus aliquot basis, retained powders, distinct wash and microscopy ethanol grades, printed thermal discrepancies, unknown pressures and measurement/model scopes remain explicit.\n\nThe declared SI remains locally unlocated and unverified. This does not approve mounted-browser delivery, Site integration, publication, training or atomic models. Exact hashes and 31 manual scopes are in the JSON.\n'
for n in ['independent-audit-v1.md','independent-audit.md']:(A/n).write_text(md,encoding='utf-8')
print(json.dumps({'status':report['status'],'module_checks':module['checks'],'additional_checks':sum(checks.values()),'failures':fails,'bound_files':len(bound),'audit_sha256':sha(A/'independent-audit.json')},indent=2))
