from pathlib import Path
import json,hashlib,datetime
W=Path(__file__).resolve().parent
P=W.parents[1]
A=P/'visuals/molecules'
O=P/'visuals/molecules-independent-audit'
O.mkdir(exist_ok=True)
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
mech=read(W/'mechanical-checks.json');run=read(W/'consumer-checks.json')
assert mech['status']==run['status']=='passed'
bound={**mech['bound_files'],**run['bound_files']}
for f in ['mechanical-checks.json','consumer-checks.json','finalize_audit.py']:
 p=W/f;bound[str(p.resolve())]=sha(p)
for p,h in bound.items():assert sha(p)==h,(p,'changed before final audit')
freeze=sha(A/'package-freeze.json')
assert freeze=='91666cffcec1eac0851778cd5c64bd5bed2946593fe501c06bc36d8928e8856c'
scope=[
 {'id':'M1','topic':'Source identity and grade','result':'passed','detail':'Main pp. 2–3 were actually reopened. Cs2CO3 99.9%, OA 90%, technical oleylamine 70%, anhydrous MnCl2 99%, MeOAc >=98% and conventionally distilled, and generic hexane >=95% remain source-specific. No pure-batch isomer or unreported solvent-grade claim is introduced.'},
 {'id':'M2','topic':'Salt connectivity','result':'passed','detail':'Cs carbonate is two Cs+ ions plus a carbonate dianion; MnCl2 is Mn2+ plus two chloride ions. Atom counts, formal charges and disconnected graphs were independently reconstructed. These formal reference components assert neither crystal coordination nor dissolved speciation.'},
 {'id':'M3','topic':'Organic identities','result':'passed','detail':'Ten independently specified molecular graphs were compared with the model graphs. Methyl acetate and heavy water are explicit source-name-derived 2D references. Oleic acid and oleylamine have cis reference connectivity/geometry supported by cached primary records, with no isomer assay or surface geometry attributed to the paper. ODE and generic hexane remain symbolic because the source does not fix their isomers.'},
 {'id':'M4','topic':'Retained model provenance','result':'passed','detail':'All six retained 3D atom/bond arrays were compared with immutable snapshots. Cached primary SDF identities and OA/oleylamine/IPA coordinates were independently checked. The original nitric-acid 3D SDF was also located, hashed and checked: its four heavy-atom positions match; H remains implicit and no new H coordinates are asserted. Water and ethyl-acetate conformers remain explicitly computed reference models, not measured sample structures. Source-neutral functional-group annotation refinements were checked separately from unchanged atom/bond arrays.'},
 {'id':'M5','topic':'Water distinctions','result':'passed','detail':'Quench water, Milli-Q analytical water (18.2 megaohm cm) and heavy water for TA continuum generation remain separate source roles. Deuterium isotopes are explicit in the 2D graph. Resistivity is a grade property, not a concentration. Heavy water is not attached to the nanocrystal stock or sample solvent.'},
 {'id':'M6','topic':'Stocks and charge basis','result':'passed','detail':'All five stock objects and 15 component slots match exact canonical/source snapshots. Cesium stock whole charges (407 mg carbonate, 18 mL ODE, 1.74 mL OA) remain distinct from the 2/3/4 mL reaction aliquots and unknown final molarity. Mn precursor whole formulation is not multiplied into fictitious synthesis runs. Cs and Mn calibration series remain separate; 2% nitric acid has unspecified percentage basis and is the analytical matrix, not an asserted digestion acid strength.'},
 {'id':'M7','topic':'Supports and product-related symbols','result':'passed','detail':'Substrate, cuvette, microscopy grid, calibration, NC-family, idealized Cs/Mn oleate, and SI13 aged-phase symbols are non-atomic context cards. They do not fabricate product coordinates, surface ligands, a photodiode atomic model, or a new synthesis route. This audit qualifies material-slot illustrations only; independently audited product dispatch is separate.'},
 {'id':'M8','topic':'Actual static visual review','result':'passed','detail':'All 39 panels were actually inspected on all seven final contact sheets: 28 identities, five stock cards, six conformer projections. Graphs, formula/charge/isotope labels, technical grade/isomer/reference captions and stock limits were readable. No clipping or misleading phase geometry was found. The final preview and contact bytes are bound by the author freeze and this audit.'},
 {'id':'M9','topic':'Actual consumer execution','result':'passed','detail':'The frozen chemical-viewer module was independently executed for all 55 material slots, 28 dialogs, seven 3D-entry views using six reference conformers, 15 stock selections and 15 solution-context selections. Exact source captions, limitations, asset digests, coordinate/bond/group transport, controls and cross-source exclusions passed. Only in-memory copies had binding approval flags changed to exercise post-promotion display. Minimal DOM/3Dmol sinks were used; this is not a mounted-browser or WebGL appearance certification.'},
 {'id':'M10','topic':'Private and public boundaries','result':'passed','detail':'All 44 proposed public files are identity SVG or qualified model JSON. No paper/SI/full-page cache, newly generated product atomic model or training label is admitted. The original proposal remains unapproved/private in place; future Site import, browser validation and publication need separate checks.'}
]
result={
 'schema':'mattersyn-independent-molecule-source-audit/1','source_id':'matuhina2023',
 'reviewer':'/root/peng1998_reader_assets','author_reviewed':'/root/backlog_eta',
 'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed',
 'proposal_freeze_path':str((A/'package-freeze.json').resolve()),'proposal_freeze_sha256':freeze,
 'canonical_manifest_sha256':sha(P/'canonical-proposal/v1/package-manifest.json'),
 'canonical_independent_audit_sha256':sha(P/'canonical-reader-independent-audit/independent-audit-v1.json'),
 'effective_file_map_sha256':sha(A/'effective-file-map.json'),
 'effective_public_assets_sha256':sha(A/'effective-public-assets.json'),
 'open_findings':[],'author_corrections_required':[],
 'counts':{'identities':28,'material_slots':55,'stocks':5,'stock_components':15,
           'model_2d_files':10,'unchanged_cached_3d_arrays':6,'public_asset_candidates':44,
           'actually_viewed_panels':39,'actually_viewed_contact_sheets':7,'exact_quantity_links':mech['quantity_links']},
 'check_count':mech['checks']+run['check_count'],
 'checks_by_method':{'graph_source_hash_and_slot_checks':mech['checks'],'actual_consumer_execution':run['check_count'],
                    'additional_final_bound_file_rechecks':len(bound)},
 'actual_source_reading_scope':{'main_pages_reopened':[2,3],
   'si_phase_context_page_previously_actually_viewed':13,
   'scope_note':'Targeted source and provenance review for the molecular package; no claim of a new full 26-page extraction audit.'},
 'manual_scopes':scope,'bound_files':bound,
 'limitations':['No Site or frozen author files were edited.','No mounted browser, final integration, publication, product coordinates or training approval is granted.','Graph and source-name references do not establish solution speciation, hydration, coordination, surface binding or commercial mixture composition.'],
 'mounted_browser_approval':False,'publication_approval':False,'training_approval':False,
 'approval_scope':'Exact private molecule/slot/stock proposal and its 44 allowlisted candidate assets only.'}
(O/'independent-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
md=f'''# Matuhina molecular, material-slot and stock audit

Status: **passed**, with no author corrections or open findings.

The audit binds proposal freeze `{freeze}` and the unchanged, independently passed canonical v1. All 28 identities, 55 material slots, five stocks, 15 components and 44 proposed public assets were checked. The review includes {result['check_count']:,} supporting checks, plus {len(bound)} final bound-file hash rechecks, and actual visual inspection of all 39 panels on seven contact sheets.

'''
for s in scope:md+=f"## {s['topic']}\n\n{s['detail']}\n\n"
md+='## Audit boundaries\n\nThis is a distinct private scientific/reference/binding audit. It does not approve mounted-browser behavior, publication, training admission or product atomic coordinates. No frozen author, source, canonical, Site or ledger file was changed. Exact input hashes and per-method counts are in `independent-audit.json`; independent executable checks are in sibling `molecule-independent-audit`.\n'
(O/'independent-audit.md').write_text(md,'utf8')
print(json.dumps({'status':'passed','audit_path':str(O/'independent-audit.json'),'audit_sha256':sha(O/'independent-audit.json'),'checks':result['check_count'],'bound_files':len(bound)}))
