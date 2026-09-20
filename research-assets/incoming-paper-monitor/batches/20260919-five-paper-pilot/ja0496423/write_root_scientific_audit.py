"""Record the root's actual independent source audit; no author or Site edits."""
from pathlib import Path
import datetime as dt
import hashlib
import json

P = Path(__file__).resolve().parent
def read(name): return json.loads((P/name).read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
inv, facts, coverage, crops = map(read, ['source-inventory.json','source-facts.json','page-coverage.json','reader-assets/crop-manifest.json'])
docs = read('intake-manifest.json')['documents']
for d in docs: assert sha(Path(d['path'])) == d['sha256']
for a in crops['assets']: assert sha(Path(a['path'])) == a['sha256']
uids={u['id'] for u in inv['units']}
assert len(uids)==126 and len(facts['facts'])==95 and len(inv['operations'])==21
assert all(f['source_unit_id'] in uids and f['eligible_training'] is False for f in facts['facts'])
assert all(a['source_unit_ids'] and all(x in uids for x in a['source_unit_ids']) for a in crops['assets'])
assert len(crops['assets'])==12
audit={
 'schema':'mattersyn-independent-source-audit/1','source_id':'gu2004','doi':'10.1021/ja0496423',
 'reviewer':'/root','extraction_author':'/root/peng1998_reader_assets','independent':True,
 'at':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'passed','open_findings':[],
 'scope':'Full supplied-source extraction and original crop audit only; not canonical, reader, training, structure-download or publication approval.',
 'source_documents':[{'role':d['role_candidate'],'path':d['path'],'sha256':d['sha256'],'verified_unchanged':True} for d in docs],
 'pages':[{'role':role,'pdf_page':n,'text_read':True,'visually_inspected':True} for role,nums in [('main',[1,2]),('si',[1,2,3])] for n in nums],
 'reviewed_source_unit_ids':[u['id'] for u in inv['units']],
 'reviewed_fact_ids':[f['id'] for f in facts['facts']],
 'reviewed_operation_ids':[o['id'] for o in inv['operations']],
 'reviewed_material_ids':[m['id'] for m in inv['materials']],
 'reviewed_sample_ids':[s['id'] for s in inv['samples']],
 'reviewed_reference_ids':[r['id'] for r in inv['references']],
 'reviewed_assets':[{'id':a['id'],'sha256':a['sha256'],'independently_viewed':True,'axes_scales_captions_checked':True} for a in crops['assets']],
 'scientific_checks':[
  'Title, DOI, dates, bylines, main/SI identity and full supplied-page coverage agree. SI is broader than the short main declaration.',
  'All SI reagent grades and upstream Cd(acac)2 quantities checked, including printed CdCl2 80.5%, 2.28g/10mmol, 4.1mL/40mmol acetylacetone, 3mL triethylamine, 2.8g product and 80degC vacuum drying. Hydrate, percentage yield and drying time are not invented.',
  'All21 operations and quantitative fields checked in order: two diol charges, qualitative ether boiling point, separate 100degC and 280degC holds, both ethanol precipitations, retained clarified hexane fraction and final nitrogen storage.',
  'Labels1/2/3/4 and analytical controls retain their identity. Failed intact-shell isolation and tentative metastable morphology are preserved; no separate successful shell recipe is fabricated.',
  'TEM scale bars5/10/5nm, intermediate2/20nm scales, reported particle/component dimensions, HRTEM and all CdS/FePt SAED ring assignments agree. Missing precursor-1 SAED original and absent CIF/XRD are disclosed.',
  'SI XRF all6 inset rows, energies, mol percentages, blank Rh, coefficient0.0478 and the main1:1:3:3.6 ratio checked independently. The unresolved numerical mismatch is correctly retained.',
  'Magnetic100Oe/11K,5K/.85kOe,30s/1e-10s model inputs and author-derived2.4e6erg/cm3 agree. Final applied field is not transferred to the SI FePt control.',
  'Absorption293nm/369nm shoulder, emission438nm, quantum yield3.2%, excitation365nm and11% reference standard agree, with hexane scope and unreported lamp wavelength preserved.',
  'All main figures/panels, Scheme1, SI figures and magnetic-model crop independently viewed; complete captions, axes and scales are readable at original output dimensions. No redrawn or digitized experimental trace is claimed.',
  'Ten numbered main references with subentries plus one SI reference are preserved as26 expanded entries, including the internal matched-SI reference. External full-text access is not claimed.',
  'Properties, mechanisms, proposed extensions and missing acquisition/sample details remain separately scoped; all training admission flags are false.'
 ],
 'retained_source_limitations':[
  'Main versus SI XRF quantification discrepancy unresolved; no unique corrected product composition.',
  'CdCl2 printed grade/hydration basis, numerical first-stage temperature, centrifugation settings and analytical batch/aliquot identities unreported.',
  'Intermediate shell assignments are tentative; failed isolation is not counted as a complete shell synthesis.',
  'Phase assignments do not provide measured atomic coordinates or an exact structure-recipe pair.',
  'Raw curves remain original images; numerical curve digitization and external reference reading are outside this audit.'
 ],
 'bound_files':{n:sha(P/n) for n in ['source-inventory.json','source-facts.json','page-coverage.json','extraction-notes.md','reader-assets/crop-manifest.json']},
 'published':False,'training_eligible':False,'next_gate':'Canonical records, complete five-section reader content and visuals, integration audit, browser review and publication.'
}
(P/'source-scientific-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(P/'source-scientific-audit.md').write_text('# Gu2004 independent source audit — passed\n\n/root independently read and visually inspected all2main+3SI pages and checked the126 source units,95typed facts,21operations,17materials,5sample nodes,26expanded references and12original crops authored by /root/peng1998_reader_assets. Source PDF and package hashes are bound in the JSON audit. No extraction corrections remain open.\n\nThe main/SI XRF mismatch, tentative shell intermediates, unresolved CdCl2 assay/hydration basis, missing numeric ether boiling temperature and analytical batch links remain explicit source limitations. Their honest preservation passes extraction review; it does not resolve those scientific uncertainties. Raw curves were not digitized.\n\nCanonical and reader integration, molecule/apparatus illustrations, browser validation and publication remain pending. No exact structure pair or training admission is approved.\n',encoding='utf-8')
print(json.dumps({'status':audit['status'],'facts':len(facts['facts']),'source_units':len(inv['units']),'assets':len(crops['assets']),'published':False}))
