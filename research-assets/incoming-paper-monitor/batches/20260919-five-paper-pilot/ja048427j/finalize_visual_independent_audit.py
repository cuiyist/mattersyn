"""Freeze auditor-owned findings, manual scope and verified file bindings only."""
import pathlib,json,hashlib,datetime
P=pathlib.Path(__file__).resolve().parent;V=P/'visuals'
def sha(f):return hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
def rd(f):return json.loads(pathlib.Path(f).read_text(encoding='utf-8-sig'))
mechanical=rd(P/'visual-independent-checks.json');module=rd(P/'visual-independent-module-checks.json')
assert not mechanical['failures'] and not module['failures']
manifest=rd(V/'visual-package-manifest.json');expected='f1af224e8a64c9a5a628dbcc86bed71046afb387ec61850f63a9415650f1e657'
assert sha(V/'visual-package-manifest.json')==expected
bound=dict(mechanical['bound_files']);checks=[]
def bind(f,h=None):
 f=pathlib.Path(f);actual=sha(f)
 if h is not None:
  assert actual==h,(f,actual,h)
  checks.append({'check':'Frozen artifact hash','path':str(f),'passed':True})
 bound[str(f)]=actual
for f,h in list(bound.items()):bind(f,h)
for row in manifest['files']+manifest['upstream']:bind(row['path'],row['sha256'])
for f in [V/'visual-package-manifest.json',V/'visual-author-validation.json',P/'audit_visual_package.py',P/'audit_visual_module.mjs',P/'visual-independent-checks.json',P/'visual-independent-module-checks.json',pathlib.Path(__file__)]:bind(f)
unit=rd(V/'products/models/norberg-undoped-zno-unit-cell.json');original=rd(V/'products/reference-origin/zno-wurtzite-original-metadata.json')
for k in ['atoms','cell','cellVectors','spaceGroup','spaceGroupNumber','units','periodic','source']:
 assert unit[k]==original[k];checks.append({'check':'Unit-cell original geometry/source preserved: '+k,'passed':True})
for new,old in [('norberg2004-topo-component','topo'),('norberg2004-nitrogen-reference','gu2004-nitrogen-reference')]:
 for dim in ['2d','3d']:
  n=rd(V/'molecules/models'/f'{new}-{dim}.json');o=rd(V/'molecules/reused/models'/f'{old}-{dim}.json')
  for k in ['atoms','bonds','functionalGroups','coordinateUnits']:
   assert n[k]==o[k];checks.append({'check':new+' '+dim+' viewed base geometry exact: '+k,'passed':True})
for f in ['main-02.png','main-03.txt','main-04.txt','main-05.txt','main-06.txt','main-08.txt','si-03.txt','si-04.txt']:
 if (P/f).exists():bind(P/f)
rp=rd(V/'reference-preview-manifest.json');rv=rd(V/'apparatus/render-validation.json')
viewed=[{'path':str(V/'apparatus'/c['file']),'sha256':c['sha256'],'kind':'contact sheet; every constituent scene visually inspected'} for c in rv['contact_sheets']]
viewed += [{'path':c['file'],'sha256':c['sha256'],'kind':'contact sheet; every constituent reference/card visually inspected'} for c in rp['contacts']]
viewed += [{'path':str(V/f),'sha256':sha(V/f),'kind':'corrected full-size preview reopened'} for f in ['apparatus/review/norberg-2004-surface-control--norberg-2004-surface-control-op-3.png','products/review/norberg2004-cleaned-final-colloids.png']]
resolved=[
 {'id':'visual-1-nitrogen-reference','finding':'Old reused N2 geometry had N–N = 1.460 Å and was unsuitable as a physical reference. Its broad graph/formula checks were insufficient.','resolution':'Author replaced the candidate with the locally retained NIST ground-state 14N2 reference, 1.09768 Å. Actual returned NIST row and unit/isotope headers were read. Exact coordinates, triple bond and uncertainty of source isotope composition checked. Old candidate is explicitly rejected and archived; it is excluded from current bindings. New model notes/sourceType now describe Norberg thermal cleaning, without inherited Gu storage instructions.','status':'resolved'},
 {'id':'visual-2-host-reference-scope','finding':'Unmodified external ZnO unit-cell model still named Fu2007 and its S1 specimen in current scope.','resolution':'Author normalized source-scope metadata. The original model and hash remain in reference-origin; atoms, unit cell, vectors, space group and primary source are exactly unchanged. Norberg receives only an external undoped host reference.','status':'resolved'},
 {'id':'visual-3-dropwise-lioh','finding':'Surface-control LiOH scene omitted the explicitly source-reported dropwise addition.','resolution':'Author added visible dropwise title/condition and droplet artwork. Corrected full-size PNG reopened; 0.002 equiv, unknown equivalent basis and missing concentration/volume remain.','status':'resolved'},
 {'id':'visual-4-coating-completeness','finding':'Cleaned precursor card called A–C instructions complete despite missing spin settings.','resolution':'Author changed the text to the reported coating sequence. Corrected card reopened; no scientific quantities changed.','status':'resolved'}]
scientific=[
 'Main p. 2 materials match named hydrate identities, including Mn(OAc)2·4H2O, TMAH·5H2O and Mn(NO3)2·xH2O with x unknown. The 90% technical TOPO is shown as the pure reference constituent, not a reconstructed impurity mixture.',
 'Main p. 3 procedure retains 0.10 M combined acetates in DMSO, 0.55 M ethanolic TMAH and 1.7 equivalents; ethyl acetate precipitation, ethanol resuspension and heptane/ethanol wash cycle remain distinct.',
 'Initial dodecylamine capping does not acquire the later 180 °C cleaning conditions. Thermal cleaning uses nitrogen, approximately 30 min, cooling strictly below 80 °C, ethanol precipitation/washing and nonpolar redispersion. The growth-series d passage retains its explicitly stated 30 min.',
 'The surface-bound control begins with pure ZnO, approximately 2% added Mn relative to Zn and dropwise 0.002 equivalent LiOH with unspecified equivalent basis. No thermal stripping is assigned to this control.',
 'Films A–C retain the 0.20 ± 0.01% measured Mn precursor composition, 1 × 0.5 cm fused silica, 525 °C/2 min per-layer air anneal, A 40 coats and B/C 20 coats. D–F retain incomplete preparation and the Table S4 versus Figure S3b D/F trend conflict.',
 'The 0.02% feed growth/EPR series, 0.20% ICP film precursor, 1.1% TOPO/MCD specimen and estimated 0.13% versus reported 1.3% optical specimens remain separate. Sampling and remaining reaction bulk are not joined as returned analyzed aliquots.',
 'Oxidation variants remain separate: Mn acetate in DMSO, zinc acetate addition, anaerobic handling, sodium acetate control and manganese nitrate substitution. Unspecified anaerobic gas is not assigned nitrogen.',
 'Acquisition scenes preserve X/Q EPR, absorption, MCD, luminescence, powder/film XRD, HRTEM, ICP-AES and SQUID contexts and source settings. Simulated EPR traces and model-based magnetic interpretations remain distinct from observations and atomic coordinates.',
 'All 26 molecular model files pass independent expected-connectivity, formula, charge, index, functional-group endpoint and dimension/unit checks. Salt/hydrate components have no invented coordination bonds or 3D salt packing. Existing ordinary conformers are illustrative, not unique measured states; N2 uses the cited reference scalar.',
 'The local COD9004178 CIF names Kihara and Donnay (1985), 293 K, P63mc No. 186, a=b=3.2494 Å and c=5.2038 Å. All four symmetry-expanded sites and their Cartesian transforms were checked. The 4×4×3 crop contains exactly 96 Zn and 96 O; every translated atom, reciprocal Zn–O visualization link and XYZ row was checked.'
]
limitations=[
 'This passes the frozen private visual/source proposal only. No Site integration, installed binding_approved flags, browser interaction, deployment or publication is approved by this report.',
 'Apparatus geometry, supports, colors and particle symbols are explanatory. Unreported vessel dimensions, separation settings, ramp rates, gas pressure, solvent volumes and specimen joins remain unknown.',
 'No Mn coordinates, measured Norberg crystal cell, sample CIF, surface ligand geometry, dopant map, defects, passivation or source particle model is supplied. The external cell/crop is excluded from measured exact-structure training pairs.',
 'Original source figures remain the measured evidence. No new spectrum, SAED pattern, XRD profile or microscopy image was fabricated. Source SI notation and D/F trend conflicts are retained.',
 'Actual visual inspection used static PNG contact sheets for all 47 scenes and all 59 reference previews, with corrected assets reopened individually. No rotating browser model was inspected. New TOPO and nitrogen model geometry equals the visually inspected reused base models exactly; their source-specific metadata was separately read.',
 'This targeted visual audit reuses the independently passed full-source and canonical audits. It is not a repeat full-source extraction or new numerical digitization of plotted curves.'
]
result={'schema':'mattersyn.independent-visual-source-audit.v1','source_id':'norberg2004','doi':'10.1021/ja048427j','reviewer':'/root/backlog_eta','author':'/root/norberg2004_extract','independent':True,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed_private_visual_source_scope','author_manifest':{'path':str(V/'visual-package-manifest.json'),'sha256':expected},'counts':{'canonical_records':19,'apparatus_scenes':47,'material_slot_bindings':73,'qualified_existing_references':10,'source_scoped_entries':9,'specimen_context_cards':30,'product_record_bindings':10,'reference_previews':59,'contact_sheets_actually_viewed':28,'molecular_model_files':26,'external_reference_unit_cells':1,'finite_reference_atoms':192,'measured_norberg_atomic_structures':0,'mechanical_checks':mechanical['check_count'],'module_checks':module['count'],'final_binding_checks':len(checks)},'actual_manual_scope':{'all_scene_art_and_visible_conditions':True,'all_reference_and_specimen_previews':True,'main_materials_page_2_reopened':True,'main_preparation_and_characterization_page_3_reread':True,'source_scientific_audit_reused':True,'source_reader_and_canonical_lineage_review':'All 73 slot mappings and 47 operations checked; sample and source-condition boundaries reviewed against frozen evidence.','cached_primary_references_read':['COD9004178 complete CIF','NIST returned ground-state row, isotope and internuclear-distance units','Retained PubChem SDF graph checks for ethanol, ethyl acetate, toluene and TOPO'],'viewed_preview_groups':viewed,'browser_rotation':False},'scientific_checks':scientific,'resolved_findings':resolved,'open_findings':[],'remaining_limits':limitations,'mechanical_reports':[{'path':str(P/f),'sha256':sha(P/f)} for f in ['visual-independent-checks.json','visual-independent-module-checks.json']],'final_binding_checks':checks,'bound_files':[{'path':f,'sha256':h} for f,h in sorted(bound.items())],'site_changed':False,'source_or_canonical_changed_by_auditor':False,'publication_approved':False}
(P/'visual-source-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=['# Norberg 2004 independent visual/source audit','','**Passed for the frozen private proposal.** All four findings were corrected by the author and independently rechecked. No open scientific visual findings remain.','','Auditor: `/root/backlog_eta`; author: `/root/norberg2004_extract`.','','The audit binds `visuals/visual-package-manifest.json` SHA256 `'+expected+'` and every artifact listed in it. Four original main/SI copies and all 19 frozen canonical records were rehashed.','','Coverage: 47 scenes, all 73 material bindings, ten existing references, nine scoped entries, 30 specimen cards and ten product-record bindings. All 59 reference previews and 47 scene previews were actually inspected through 28 contact sheets; corrected LiOH and precursor cards were reopened full-size. All 26 molecular model files were checked. The external ZnO cell has four sites and its finite crop has 192 atoms.','','Independent checks: '+str(mechanical['check_count'])+' molecular/coordinate/hash/pointer checks; '+str(module['count'])+' module checks; '+str(len(checks))+' final binding and exact reused-geometry checks. All passed. Checks are consistency evidence, not a substitute for the visual and source reading.','','## Corrected findings','']
for x in resolved:md.append('- **'+x['id']+'**: '+x['finding']+' '+x['resolution'])
md += ['','## Scientific scope','']+['- '+s for s in scientific]+['','## Remaining limits','']+['- '+s for s in limitations]+['','Exact file hashes, manual viewing scope, resolved findings and check reports are retained in `visual-source-audit.json`.']
(P/'visual-source-audit.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
print(json.dumps({'audit_sha256':sha(P/'visual-source-audit.json'),'markdown_sha256':sha(P/'visual-source-audit.md'),'bound_files':len(bound),'final_checks':len(checks),'status':result['status']}))
