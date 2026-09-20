from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
O=Path(__file__).resolve().parent;B=O.parents[1];V=O.parent/'apparatus/v1';C=B/'canonical-proposal/v3'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
freeze=V/'package-freeze.json';assert sha(freeze)=='474a21a8b43326cc94058063c040019aa68810567a5c2592186f997c85e41025'
bound={};checks=0
def bind(p,expected=None,role='audited_input'):
 global checks
 p=Path(p);h=sha(p)
 if expected:assert h==expected,p
 bound[str(p)]={'path':str(p),'sha256':h,'role':role};checks+=1
bind(freeze)
for x in read(freeze)['files']:bind(V/x['path'],x['sha256'])
for x in read(freeze)['authoring_files']:bind(B/x['path'],x['sha256'],'author_source_read_only')
for x in read(V/'canonical-bindings.json')['bound_files']:bind(B/x['path'],x['sha256'])
canonical=read(C/'record-manifest.json')
for x in canonical['records']:bind(x['path'],x['sha256'])
for p in ['source-inventory.json','source-extraction-revision-2/source-facts.json','public-review-proposal/v3/evans2010.json']:bind(B/p)
originals=Path(r'[local path redacted]')
bind(originals/'10.1021_ja103805s.pdf','3867a60f67a10f4f28f9aa960ed4cd13b621d039e8472fcac6d10713a5e86f81','original_main_pdf')
bind(originals/'10.1021_ja103805s_si_1.pdf','017dfc31dcaa290c2a7c08a8a4dbb0a672b973449ec3a74e0e690141bd558ed9','original_si_pdf')
source_pages=['main-2']+[f'si-{i:02}' for i in [1,2,6,7,8,15,16,19,20]]
for stem in source_pages:
 bind(B/'reader-assets'/(stem+'.png'),role='actually_viewed_original_source_render')
 if (B/'reader-assets'/(stem+'.txt')).exists():bind(B/'reader-assets'/(stem+'.txt'),role='source_text_crosscheck_private')
render=read(O/'independent-render-manifest.json')
for x in render['scenes']:bind(x['preview_path'],x['preview_sha256'],'independent_scene_render')
for x in render['contacts']:bind(x['path'],x['sha256'],'actually_viewed_audit_contact')
for p in ['prepare_review.py','check_module.mjs','module-checks.json','independent-render-manifest.json',Path(__file__).name]:bind(O/p,role='independent_audit_support')
groups=[
 ('cd-oleate',[1,2,3],['SI S1'],'The 50 mL three-neck flask, flowing N2 and 220 °C are source-reported. The additional hour follows CdO dissolution; room-temperature cooling precedes acetone precipitation. The isolated solid is retained after centrifugation; settings remain unreported.'),
 ('pb-oleate',[4,5,6],['SI S1'],'Source PbO/OA/ODE amounts are preserved. The source explicitly inherits the remaining Cd-oleate preparation; conditions are labelled inherited rather than a separate measured recipe. FTIR is an identity-confirmation context with no invented bands or spectrum.'),
 ('topse',[7,8],['SI S1'],'30 mL/67 mmol TOP and 5.29 g/67 mmol Se are stirred overnight in a nitrogen glovebox. Viscous, impurity-containing TOPSe solution is retained without an invented purification or numeric overnight duration.'),
 ('dppse',[9,10,11],['SI S2'],'One-neck flask, septum removal, water-cooled condenser, slight N2 flow and 16 h reflux match the source. No numeric reflux temperature is introduced. Rotary evaporation and hot-toluene recrystallization retain diffraction-quality DPPSe as a distinct compound, without borrowing species9 coordinates.'),
 ('tippse',[12,13],['SI S2'],'Room-temperature overnight glovebox preparation retains the reported 500 µL TIPP/2.6 mmol, 0.205 g Se/2.6 mmol and 2.5 mL toluene. In-vacuo removal and hot-toluene recrystallization do not acquire pressure or temperature values.'),
 ('tepse',[14,15,16],['SI S2'],'Nitrogen glovebox charges and overnight treatment match. Excess selenium is removed first while solution/filtrate is retained; evaporation yields the solid. Hot-acetone recrystallization, filtration and cold-acetone washing retain product crystals.'),
 ('tppse',[17,18,19],['SI S2'],'Reported TPP/Se/toluene charges are preserved. Excess selenium removal retains the solution; toluene evaporation, hot-toluene recrystallization and cold-acetone washing remain in the proper order. Explanatory filtration/crystal symbols do not assign unreported pore size, morphology or dimensions.'),
 ('tertiary-negative-rescue',[20,21,22,23],['SI S2'],'The actual precursor is TIPPSe despite the source heading. J-Young NMR vessel, 120 °C/5 h no-reaction observation, and later 7 µL/48 µmol DIPP addition are distinct. The conflicting TIPPSe mass/amount is retained. Rescue temperature/time remain unreported. TEPSe and TPPSe are separate analogous replacements, never joint inputs. The generic heater is not labelled as a reported oil bath.'),
 ('topse-distillation',[24,25,26],['SI S6'],'The 10 mL charge, 50 mTorr and slow heating are preserved. A is 2 mL beginning at185 °C; the two separate unlabelled cuts are2 mL at190/195 °C. The approximately4 mL residual pot C is distinct from collected cuts in both drawing and corrected v3 state graph. Receiving-vessel silhouette is explanatory; the text retains the reported receiving flask.'),
 ('topse-b-stock',[27],['SI S6 and Figure S4'],'B is independently prepared1 M TOPSe/TOP, not a second distillation cut. The prose-versus-caption TOPSe/selenium starting-solute discrepancy is visible and is not silently resolved.'),
 ('pbse-msc-family',[28,29,30,31],['SI S7 and Figure S5'],'PbO/OA/ODE are heated at150 °C under N2 in a three-neck flask, then cooled to40 °C. Exactly one A/B/C source supplies1 mmol TOPSe; dilution is corrected for source purity while injection volume remains unknown. Forty minutes is a comparison time, not an invented series time grid. A substantial-MSC and C negligible-growth observations are qualitative.'),
 ('dpp-pb-control',[32,33,34],['SI S8; main p10974'],'Flame sealing under unspecified vacuum,140 °C oil bath, DPP/Pb/toluene-d8 charges and source Pb-oleate mass/amount conflict are retained. Pb metal formation is separate from QD growth. The TOPSe challenge has no completed experimental sequence invented for it.'),
 ('dpp-cd-negative',[35,36],['SI S8'],'The source calls this experiment analogous to the preceding sealed-tube procedure. The scene explicitly marks inherited heating, preserves separate Cd charges and140 °C, and keeps several days qualitative. No detection limit or numerical negative-yield datum is manufactured.'),
 ('species9-crystallization',[37,38,39],['SI S16; SI S15 Figure S12; main p10974'],'500 µL0.1 M DPPSe plus100 µL0.1 M Pb oleate in toluene at room temperature form molecular crystals after slow evaporation over several days. Unreported atmosphere and explanatory vessel geometry remain explicit. Nominal5:1 charges and >5:1 source wording remain separate. No QD lattice or unisolated intermediate is portrayed as these crystals.'),
 ('pbse-qd',[40,41,42,43],['SI S19; SI S20 Figure S15'],'DPPSe2.6 mg/10 µmol in2 mL toluene, OA12.6 µL/40 µmol and separate2 mL0.025 M Pb stock remain source-specific. The Pb-stock solvent is unreported. A Teflon-sealable1 cm cuvette is sealed under N2, removed from glovebox and heated in80 °C oil bath. Early MSCs and later QDs are distinct;20 min identifies the optical example. No spectrum or TEM specimen join is fabricated.'),
 ('cdse-qd',[44,45,46],['SI S19; SI S20 Figure S15'],'Each1 mL ODE stock has0.025 M precursor/25 µmol and630 µmol OA. The Cd stock reaches200 °C in a three-neck flask under flowing N2 before rapid DPPSe-stock injection. Colorless-to-yellow behavior and10 min optical example match. The diagram does not convert that example into a measured particle geometry or exact coordinate pair.')]
scenes=read(V/'rendered-scenes.json');assert len(scenes)==46
review=[]
for key,idxs,pages,note in groups:
 ids=[scenes[i-1]['operation_id'] for i in idxs]
 assert all(i.startswith('evans-2010-'+key+'-op-') for i in ids);checks+=1
 review.append({'record_id':'evans-2010-'+key,'operation_ids':ids,'original_source_locators':pages,'independent_manual_observation':note,'status':'pass'})
assert sorted(i for _,ids,_,_ in groups for i in ids)==list(range(1,47));checks+=1
module=read(O/'module-checks.json');assert module['status'].startswith('passed');assert module['conditions']==153 and module['canonical_parameter_rows']==105;checks+=2
report={'schema':'mattersyn-independent-apparatus-audit/1','source_id':'evans2010','created_at':datetime.now(timezone.utc).isoformat(),'author_of_audited_package':'/root','independent_auditor':'/root/norberg2004_extract','status':'passed','audited_package':{'path':str(freeze),'sha256':sha(freeze)},'manual_scope':{'all_46_scene_previews_actually_viewed':True,'contact_sheets_viewed':8,'complete_condition_rows_read':153,'source_page_renders_actually_reopened':source_pages,'source_page_count':10,'record_families_reviewed':16,'review_method':'Read all emitted scene prose and rows, inspected every SVG via separate native rasterization/contact sheets, reread source preparation paragraphs and relevant original figures, and checked state/variant identity against audited canonical v3. Existing prior source/canonical audits supply broader extraction coverage; this audit does not claim a fresh full24-page reread.'},'scientific_scope_checks':review,'mechanical_checks':{'module_and_transport':module['checks'],'hash_binding_and_scope_consistency':checks,'svg_replays':46,'canonical_parameter_rows':105,'condition_rows':153,'deeply_frozen_inputs_unmutated':True,'foreign_source_wrong_record_and_unknown_operation_rejected':True},'findings':[],'required_corrections':[],'nonblocking_presentation_observations':['Some operation prose retains compressed spacing and repeated source-conflict qualifiers from the canonical fields. These remain readable with the responsive condition panel; a future wording-only polish may improve presentation without changing source fields.','A receiving vessel and generic heating envelope are explanatory silhouettes. The adjacent source facts retain receiving flask and unspecified heating geometry; these symbols are not treated as new apparatus evidence.'],'limits':['No independent live browser or mobile interaction test was performed in this audit; the separately bound root author-browser report is not relabelled independent.','Only this apparatus package is approved within scope; deployment, installed viewer integration and public browser QA require their own checks.','No new source measurement, particle size, spectrum, atomic geometry or exact QD structure–recipe pairing is approved.'],'bound_files':list(bound.values()),'source_canonical_author_files_unchanged':True,'independent_apparatus_source_approval':True,'publication_approval':False,'training_approval':False}
save(O/'independent-audit-v1.json',report)
md=f'''# Evans 2010 apparatus — independent audit passed

Auditor: `/root/norberg2004_extract`; author: `/root`.

The frozen v1 package `{sha(freeze)}` passes the scoped apparatus/source audit with no required correction. All46 scenes and153 condition rows were inspected. Eight independently rendered contact sheets cover every scene. Ten original source page images were reopened: mainp2 and SI1,2,6,7,8,15,16,19,20.

The review specifically confirms separate distillation cuts and residual pot C, independently prepared B, mutually exclusive A/B/C experiments, inherited Pb-oleate/Cd-control conditions, retained filtrate versus isolated solids, unreported vessel/temperature/atmosphere limits, negative controls and incomplete Pb-metal challenge, and the distinction between molecular species9 crystals, MSCs and QDs. Source discrepancies remain visible.

Read-only execution passed{module['checks']} module/transport assertions: all46 stored SVGs replayed identically, all105 canonical parameter rows and153 conditions matched, inputs stayed unchanged and foreign-source/wrong-record/unknown-operation calls were rejected. A further{checks} hash/scope assertions bind{len(bound)} files.

This is independent scientific/asset review, not an independent mounted-browser test. Root's existing author-browser checks remain separately identified. Integration, public browser QA, publication and training gates are outside this audit. Original source, canonical, reader and author apparatus files were not edited.
'''
(O/'independent-audit-v1.md').write_text(md,encoding='utf-8')
print(json.dumps({'audit_sha256':sha(O/'independent-audit-v1.json'),'bound_files':len(bound),'checks':checks,'status':'passed'}))
