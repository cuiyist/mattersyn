from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent;A=O.parent/'apparatus';P=A.parents[1]
def read(p):return json.loads(p.read_text('utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf-8')
assert not (O/'independent-audit.json').exists(),'Preserve existing audit; use revision for later changes.'
pkg=read(O/'package-checks.json');run=read(O/'runtime-checks.json');pixels=read(O/'preview-replay.json')
assert all(x['status']=='passed' for x in [pkg,run,pixels])
bound=dict(pkg['bound_files'])
for n in ['package-checks.json','runtime-checks.json','preview-replay.json','check_runtime.mjs','check_package.py','replay_previews.py','finalize_audit.py']:
 p=O/n;bound[str(p)]=sha(p)
for p,h in bound.items():assert sha(Path(p))==h,p
manual=[
 {'scope':'Cs-oleate preparation, five stages','source':['main p.2'],'finding':'407 mg Cs2CO3 and 18 mL ODE are charges in a 50 mL three-neck flask. Initial degassing, additional 15 min, 1.74 mL dry OA under Ar, 150 °C dissolution, RT/vacuum storage, and at least 30 min preconditioning are separated. No final molarity, pressure or numerical storage time is invented.'},
 {'scope':'Hot-injection series, four stages','source':['main pp.2–4'],'finding':'156 mg anhydrous MnCl2 with dry ODE/OA/OlAm, 25 mL flask, 120 °C/1.5 h vacuum treatment and five demonstrated temperature/loading/aliquot pairs retained. Injection and hold show the same five paired alternatives, not a Cartesian grid or ten runs. Five seconds precedes external ice-water cooling.'},
 {'scope':'Primary isolation, three stages','source':['main p.2','SI p.3 Figure S1'],'finding':'8550 rpm/5 min without antisolvent yields the retained precipitate; supernatant is discarded. Vacuum desiccation is typically overnight without numerical conversion; hexane redispersion has unknown primary volume.'},
 {'scope':'Purification controls, three stages','source':['main p.2'],'finding':'Hexane-only 2 mL and 8600–14000 rpm retains the no-visible-precipitation result and depicts no pellet. IPA OR ethyl acetate remains two trials at 1:2 portions; MeOAc 1:1 with 12000 rpm is distinct. No shared physical aliquot or missing spin time is invented.'},
 {'scope':'Unisolated degradation control','source':['SI p.3 Figure S1d'],'finding':'One hour in air applies to unisolated crude NCs in ODE, not purified-dispersion storage.'},
 {'scope':'XRD preparation, acquisition and refinement','source':['main pp.2–3','SI pp.6–7'],'finding':'20×20 mm cover glass, Cu Kα 1.5406 Å, 45 kV/40 mA, 4–62° 2θ, 0.0262° steps and 17 s per step remain acquisition settings. Similar film thickness is unquantified. Supplied coordinate tables are retained but not treated as an approved interactive model or DFT input.'},
 {'scope':'TEM deposition and acquisition','source':['main pp.2–3'],'finding':'20 µL deposition follows absorbance 0.2 at 280 nm; carbon-coated copper grid and JEM-F200 at 200 kV retained. No exact common aliquot with optical/XRD measurements or synthesized microscopy is asserted.'},
 {'scope':'Optical acquisition and TRPL analysis','source':['main pp.2–3,8'],'finding':'UV-3600 and FLS1000 methods remain distinct with 100 Hz microflash setting. Printed lifetime/model conflicts remain qualified; analysis icon supplies no new decay curve.'},
 {'scope':'TA loading, acquisition and fits','source':['main pp.3,7 Figure6','SI p.11 FigureS6'],'finding':'2 mm quartz cuvette and approximately 150 fs retained. Figure6 has 300 nm/80 µW, three explicitly named specimens and 445/550 nm probes by phase; S6 is only 180@NCs//0.7 with 300/370/420 nm pumps and 600 nm probe. Heavy water belongs to continuum generation, not NC solvent. Biexponential/triexponential models remain phase scoped.'},
 {'scope':'ICP digestion, dilution and standards','source':['main p.3'],'finding':'Concentrated nitric-acid digestion is destructive; 2% acid denominator remains unspecified. Ultrapure water 18.2 MΩ cm and separate Cs/Mn 0.001–1000 µg/L standards remain measurement preparation, not synthesis feed composition.'},
 {'scope':'LTPL deposition, acquisition and fit','source':['main pp.3,8 Figure7'],'finding':'Silica-supported 180@NCs//0.5 remains separate from hexane dispersion. Cooling to 30 K precedes warming measurements; 30–293 K with stated 20 K increments and 380 nm excitation is kept literally. The 100–300 K fitting interval is distinct.'},
 {'scope':'Structural and optical aging','source':['main pp.3,8–9','SI p.13'],'finding':'Dark ambient approximately 40% RH/25 °C, film XRD, dispersion PL and aged TEM remain separate contexts. Rhombohedral three-month and cubic nine-week structural observations are not merged with one-week/20-day/55-day optical observations. No phase-fraction or exact age inference is drawn for aged microscopy.'},
 {'scope':'DFT analysis','source':['main p.5'],'finding':'HSE06/25% HF/ZORA and separate cubic/rhombohedral meshes are author computation settings. Magnetic state is not presented as measured magnetism; refinement tables do not become verified calculation inputs or NC coordinates.'},
 {'scope':'LSC film, assembly, measurement and reassessment','source':['main pp.3,9–10 Figure9'],'finding':'Unencapsulated film on glass is separate from exact synthesis-loading assignments. Glass edge directly contacts silicon diode; surrounding diode is covered. Approximate dimensions, illumination power/spot and -5 to 0.5 V remain qualified. Bare-glass, illuminated NC and dark controls are distinct. Only the explicitly same film is reassessed after 11 weeks.'}
]
result={
 'schema':'mattersyn-independent-apparatus-audit/1','source_id':'matuhina2023','doi':'10.1021/acsanm.2c04342','reviewer':'/root/peng1998_reader_assets','author':'/root','status':'passed','created_at':datetime.now(timezone.utc).isoformat(),
 'proposal_freeze_sha256':sha(A/'package-freeze.json'),'package_freeze_sha256':sha(A/'package-freeze.json'),'module_sha256':sha(A/'matuhina2023-protocol.mjs'),
 'source_freeze_sha256':sha(P/'package-freeze.json'),'source_audit_sha256':sha(P/'source-independent-audit/independent-audit-v2.json'),'canonical_package_sha256':sha(P/'canonical-proposal/v1/package-manifest.json'),
 'open_findings':[],'author_corrections_required':False,
 'counts':{'operation_records':14,'scenes':39,'operation_quantities':67,'paired_condition_options':5,'option_quantity_appearances':30,'display_rows':168,'supporting_checks':pkg['checks']+run['checks']+pixels['pixel_checks'],'hash_source_package_checks':pkg['checks'],'actual_function_checks':run['checks'],'preview_pixel_checks':pixels['pixel_checks'],'manual_source_scopes':len(manual)},
 'actual_source_scope':{'main_pdf_pages_viewed':[2,3,4,5,7,8,9,10],'si_pdf_pages_viewed':[3,6,7,11,13],'all_original_source_bytes_rehashed':True,'source_packet_read':['source-facts.json: all protocol operations, quantities and relevant facts/conflicts','canonical operation records and all 39 binding entries','scene configs, module code, visible text and complete rendered scene objects'],'complete_26_page_source_audit_repeated':False,'prior_complete_source_audit_remains_separate':True},
 'actual_visual_scope':{'all_39_scenes_viewed':True,'contact_sheets_viewed':list(range(1,11)),'final_frozen_contacts_reopened':True,'all_39_svg_to_png_replayed':True,'all_replayed_pixels_match':True,'readability':'All titles, notes and condition groups readable; no visible text clipping found on the frozen previews.','no_fabricated_measurement_graph_or_atomic_scene':True,'independent_browser_test':False,'author_private_browser_receipt':'Bound as author evidence only; integrated browser review is a separate later gate.'},
 'manual_source_checks':manual,
 'scope_limits':['This audit approves the source-specific private apparatus proposal and executed module bindings only.','Canonical/reader v1 has a separate independent reviewer; this receipt does not replace that review. Any later canonical revision requires a bounded dependency rebind check.','Product illustrations authored by this reviewer are excluded from this independent apparatus audit.','No molecule, atomic model, CIF, training, public integration, deployment or integrated browser approval is conferred.'],
 'bound_files':bound
}
save(O/'independent-audit.json',result)
md=f'''# Matuhina 2023 apparatus independent audit

Passed without author corrections. Freeze `{result['proposal_freeze_sha256']}` is unchanged.

Reviewed all **39 scenes / 14 records**, all **67 operation quantities**, five paired preparation options shown at injection and hold (**30 appearances**), and **168 display rows**. All ten final contact sheets were actually viewed. Independent execution and source/hash checks total **{result['counts']['supporting_checks']:,}**; all 39 regenerated previews match the original PNG pixels exactly.

Targeted original-source review covered main pages 2, 3, 4, 5, 7, 8, 9 and 10 and SI pages 3, 6, 7, 11 and 13. The earlier complete source audit remains separate. The fourteen manual scopes are recorded in the JSON, including precipitate retention, failed precipitation, paired schedules, external coolant, separate TA series, destructive digestion, LTPL, aging, DFT and same-film device reassessment.

No open apparatus finding. This is a private apparatus/source-binding approval, not a canonical, molecular, atomic, training or publication approval. The separate canonical review and later integrated browser review remain required. This reviewer did not audit their own product proposal.

Exact source, canonical, module, preview and checker hashes are bound in `independent-audit.json`. No author, source, Site or ledger files were changed.
'''
(O/'independent-audit.md').write_text(md,'utf-8')
print(json.dumps({'status':'passed','audit_sha256':sha(O/'independent-audit.json'),'checks':result['counts']['supporting_checks'],'bound_files':len(bound)}))
