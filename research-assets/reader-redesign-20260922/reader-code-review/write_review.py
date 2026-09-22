from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
P=Path(__file__).resolve().parent;S=P.parents[2]/'recipe-atlas';D=S/'dist'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inventory=json.loads((P/'static-inventory.json').read_text('utf8'))
snap=P/'reviewed-code-snapshot';snap.mkdir(exist_ok=True)
bound={}
for name in ['reader-app.mjs','reader-structures.mjs','protocol-references.mjs','reader-utils.mjs','chemical-viewer.mjs','protocol-visuals.mjs']:
 target=snap/name;target.write_bytes((D/name).read_bytes());bound[str(target)]=sha(target)
for rel in ['data/structure-recipe-coverage.json','data/validation-report.json','data/reader-presentation.json','data/materials-index.json']:
 bound[str(D/rel)]=sha(D/rel)
metrics=json.loads((D/'data/structure-recipe-coverage.json').read_text('utf8'))
assert metrics['counts']=={'sample_coordinate_assets':1,'records_with_sample_coordinates':2,'source_verified_explicit_links':1,'exact_task_ready_records':0}
assert len(metrics['records'])==675
assert all(not r['exact_structure_recipe']['eligible'] for r in metrics['records'])
assert all((D/'records'/(r+'.html')).exists() for h in inventory['hubs'] for r in h['routes'])
findings=[
 {'id':'READER-01','priority':1,'status':'partially_corrected_two_sources_open','file':'reader-app.mjs','scope':'reviewURL fallback',
  'problem':'The current fallback still constructs paper-review.html?id=tessier2015 and ?id=zhang2019 when presentation.data_links.full_review is null. Neither review JSON exists. Murray/Peng legacy targets were corrected by root during this review.',
  'examples':['tessier2015-inp-incl3-reference1','zhang2019-cspbbr3-tdpa-only'],
  'correction':'When full_review is unavailable, use the source DOI or an existing complete data/evidence page. Do not infer a paper-review route. Figure-specific reader_url should take precedence when provided.'},
 {'id':'READER-02','priority':1,'status':'correction_proposed_not_applied','file':'reader-structures.mjs','scope':'particleArt and particle specimen groups',
  'problem':'The selector groups facts by specimen but art and heading still use the route-wide material formula. Braun initial CdS cores are therefore illustrated as CdS/HgS/CdS layered particles; Banerjee CdTe washings receive the CdTe/MWNT heading. Unknown-only product contexts are omitted because groups are seeded from non-null facts.',
  'examples':['braun-2001-system-i/a-cds-core','braun-2001-system-ii/a-cds-core','braun-2001-system-iii/a-cds-core','banerjee-2003-growth/washings','sommer-2020-acs-route: all seven contexts have no non-null productFacts'],
  'correction':'Seed groups from productContexts and canonical products, then attach matching facts. Select composition and morphology only from that specimen; use an explicitly unassigned placeholder otherwise. Do not infer shell/dopant placement from the route formula.',
  'proposal':'reader-particle-proposal.mjs','proposal_test_checks':853},
 {'id':'READER-03','priority':1,'status':'open','file':'protocol-references.mjs','scope':'case-insensitive short formula matches and ids.add from prose',
  'problem':"Elemental formula In is matched case-insensitively to the ordinary word 'in'. In Heo host mounting this creates an Indium metal link and adds it to the step chemical chips although canonical inputs contain only na-x and pyrex.",
  'examples':[{'record_id':'heo-2003-in66-route','operation_id':'host','text':'in a fine Pyrex capillary','actual_inputs':['na-x','pyrex'],'spurious_material':'in-metal'}],
  'correction':'Use case-sensitive formula tokens for short element symbols (or omit ambiguous symbols); retain full-name matching. Build step input chips solely from explicit input/stock-component IDs, not prose matches. Prose reference links must not mutate input scope.'},
 {'id':'READER-04','priority':2,'status':'open','file':'reader-app.mjs','scope':'canonical stock/context matching',
  'problem':'At least five existing exact stock/component contexts fail the id/title heuristic. The canonical stock uses fallback components and the qualified context is appended as a separate second panel, violating the requested one stock/one matching illustration behavior.',
  'examples':[s for s in inventory['stock_matches'] if not s['matched_context_id'] and s['candidate_ids']],
  'correction':'Use an explicit reviewed record_id + stock_id -> context_id mapping, including the five listed existing identities, rather than normalizing display names. Do not attach unrelated solution contexts merely by formula.'}
]
report={'status':'changes_required','reviewer':'/root/backlog_eta','author_of_reviewed_code':'/root','reviewed_at_utc':datetime.now(timezone.utc).isoformat(),
 'scope':'Bounded independent static code/data transport review of shared reader, structures, protocol popovers and legacy navigation. Particle correction is an author proposal and has not received independent approval. No browser, publication or new scientific source audit claimed.',
 'coverage':{'material_hubs':50,'synthesis_routes':123,'missing_hubs':0,'missing_route_presentation':0,'all_route_data_html_targets_exist':True,'all_original_figure_asset_paths_in_presentation_readable':True},
 'metrics':{'actual_public_report_counts':metrics['counts'],'representation_counts':metrics['asset_representation_counts'],'record_reasons':len(metrics['records']),'evans_no_auto_promotion':True,'result':'Matches tested metric proposal; unknown task completeness is explicitly unassessed, not asserted complete or treated as missing coordinates.'},
 'findings':findings,'open_findings':[x['id'] for x in findings],
 'notes':['Initial inventory observed seven hardcoded unavailable review routes. Root corrected five Murray/Peng routes while the review was in progress; the initial inventory is retained, not presented as the current link count.',
          'Not every differently worded sample composition is an error; examples were selected where phase/component scope actually differs.',
          '139 stock names have no heuristic match, but most have no registered context. Only five exact suffix candidates with corresponding source stock identities are claimed as confirmed duplicate-panel cases.',
          'Root is concurrently adding record bootstrap and testing the browser. All record data HTML targets exist; default-reader execution and visual layout remain root browser gates.'],
 'bound_files':bound}
for name in ['inspect_reader.py','static-inventory.json','reader-particle-proposal.mjs','test-particle-proposal.mjs','particle-proposal-tests.json','write_review.py']:
 report['bound_files'][str(P/name)]=sha(P/name)
(P/'independent-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
lines=['# Bounded reader review','', '**Changes required.** All 50 hubs and 123 synthesis routes have presentation records and existing data-page targets. The actual metrics match the proposal: one molecular coordinate asset, one explicit documentary recipe link, zero task-ready records. No canonical or Site file was edited.','']
for f in findings:lines += [f"- **{f['id']} (P{f['priority']}):** {f['problem']} Fix: {f['correction']}"]
lines += ['', 'Particle correction proposal: copy `reader-particle-proposal.mjs` as `dist/reader-particle.mjs`, import `mountParticleContext`, and replace the entire particle branch in `mountReaderStructures.select` with `mountParticleContext(panel,r,presentation); return;`. Remove the old unused `particleArt`. It preserves unknown contexts and every existing fact; 853 pure-function checks passed against all 123 routes plus targeted core/washings/molecular cases. Integrated DOM/layout validation remains root work.', '', 'This is a code/data review, not browser approval or a repeat scientific source audit. Exact reviewed code copies are retained in `reviewed-code-snapshot/`; the initial inventory and corrections made during review remain separate.']
(P/'independent-review.md').write_text('\n'.join(lines)+'\n','utf8')
print(json.dumps({'report':str(P/'independent-review.json'),'sha256':sha(P/'independent-review.json'),'findings':len(findings),'proposal_sha256':sha(P/'reader-particle-proposal.mjs')}))
