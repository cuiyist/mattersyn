"""Versioned independent apparatus review closure; writes private audit artifacts only."""
import json,hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inventory=read(BASE/'apparatus-audit/scene-inventory.json')
render=read(BASE/'apparatus-audit/render-inspection.json')
module=(BASE/'danek-protocol.mjs').read_text(encoding='utf-8')
assert inventory['module_sha256']==sha(BASE/'danek-protocol.mjs'), 'Regenerate scene exports for current module.'
findings=[
 {'id':'state-shell-scope','status':'resolved','finding':'Generic purification/film drawings previously risked assigning a shell to bare seeds or bare-dot films.','resolution':'hasShell is now record- and stage-specific; bare and overcoated film stacks are distinct; seed purification, redispersion and filtration show uncoated CdSe.'},
 {'id':'state-solvent-feed','status':'resolved','finding':'Cosolvent and dilution inputs and reagent-only vessels needed material-state specificity.','resolution':'Cosolvent/dilution start from liquid dispersions; only redispersion starts from a pellet. Butanol and stock-preparation vessels contain no particle symbols.'},
 {'id':'layout-electrospray','status':'resolved','finding':'Growth-zone box overpainted the ends of the positive-capillary and grounded-ring labels.','resolution':'Short labels are centered at x225 outside the chamber. Bare and overcoated static renders show complete text.'},
 {'id':'layout-layer-heat','status':'resolved','finding':'Heater waves crossed the glass-substrate label.','resolution':'Waves moved below the substrate. Base and cap-layer static renders show no text collision.'},
 {'id':'measurement-specimen','status':'resolved','finding':'A universal Dispersion label excluded measured films.','resolution':'UV/vis specimen is now labeled Specimen, preserving dispersion and film contexts.'},
 {'id':'measurement-availability','status':'resolved','finding':'The measurement footer promised a figure-gallery measurement for text-only AES/XRF observations.','resolution':'Footer now states that source observations and available figures are linked separately.'},
 {'id':'precipitation-collection','status':'resolved','finding':'Standalone precipitation ended in a collected pellet even though centrifugation is the next operation.','resolution':'Standalone precipitation now ends in a precipitated suspension; particle retention is shown for centrifugation.'}
]
title_fixed="title(centrifuge?'Particle collection':'Precipitation and redispersion')" not in module
findings.append({'id':'precipitation-title','status':'resolved' if title_fixed else 'advisory','finding':'The standalone precipitation title also named redispersion, which belongs to later operations.','resolution':'Standalone precipitation now has an action-specific title.' if title_fixed else 'Recommended cosmetic change: title the standalone action Particle precipitation.'})
checks=[
 {'check':'Five DOI and unsupported-action guards pass','passed':all(inventory['guard_checks'].values())},
 {'check':'All 36 returned SVG scenes parse and render; no text leaves the view box','passed':len(render['rows'])==36 and not any(x['out_of_page_spans'] for x in render['rows'])},
 {'check':'Technical figures identify geometry, colors, particle counts and layer proportions as illustrative','passed':all('illustrative' in x.get('caption','') for x in inventory['operations'] if x['covered'])},
 {'check':'All current material input/state fixes are present','passed':"particles:false" in module and "pellet:o.action==='redispersion'" in module and 'function hasShell' in module},
 {'check':'Measurement scope/availability wording is corrected','passed':"['UV/vis source','Specimen','Absorption']" in module and 'Source observations and available figures are linked separately.' in module},
 {'check':'Source thaw-pump-freeze wording and unspecified cycle count are preserved','passed':"'Thaw'" in module and "'Pump'" in module and "'Freeze'" in module and 'Several cycles; count not specified' in module},
 {'check':'Source anneal-temperature conflict is visible rather than resolved by invention','passed':'Body / caption temperature conflict' in module},
 {'check':'Unsupported current operations return null, with no invented generic process supplied','passed':len([x for x in inventory['operations'] if not x['covered']])==6}
]
out={
 'status':'passed_with_advisory' if any(x['status']=='advisory' for x in findings) else 'passed',
 'source_doi':'10.1021/cm9503137',
 'scope':'Independent source-consistency and static-render review of the private Danek apparatus module against all current operation drafts. This is not browser interaction/responsiveness QA or a new independent reread of all paper pages.',
 'source_pdf_sha256':'cde428b3707ab7e0fe1a24cd747e6c884d6903265d4d745a93e36d60e553321f',
 'module_sha256':sha(BASE/'danek-protocol.mjs'),
 'canonical_hashes':{p.stem:sha(p) for p in sorted((BASE/'canonical-drafts').glob('*.json'))},
 'source_locators':[
  {'pdf_page':2,'printed_page':174,'scope':'Materials, CdSe/ZnSe overgrowth and purification, dispersion preparation, ES-OMCVD apparatus/precursors/layer order, optical/composition acquisition.'},
  {'pdf_page':3,'printed_page':175,'scope':'HRTEM preparation and XRD geometry/support; comparative controls and scope of observed growth.'},
  {'pdf_page':4,'printed_page':176,'scope':'Figure 3 wurtzite comparison, unresolved ZnSe structure and Figure 4 caption/body annealing-temperature conflict.'}
 ],
 'coverage':{'canonical_records':len(list((BASE/'canonical-drafts').glob('*.json'))),'operations':len(inventory['operations']),'scene_operations':sum(x['covered'] for x in inventory['operations']),'no_scene_operations':[{k:x[k] for k in ['record_id','operation_id','action']} for x in inventory['operations'] if not x['covered']], 'static_render_count':len(render['rows']), 'initial_visual_review':'All 33 representative scenes across six contact sheets visually inspected.','final_targeted_visual_review':'Corrected electrospray, base/cap film layers, all measurement classes, precipitation, solvent/feed and bare/coated particle states visually inspected in regenerated sheets 1, 2, 4, 5 and 6.'},
 'checks':checks,'findings':findings,'must_fix_remaining':[],
 'limitations':['Static SVG rendering uses PyMuPDF and its available font fallback. Actual Site browser fonts, responsive wrapping, selectors and keyboard behavior remain root browser-QA responsibilities.','Six operations deliberately have no source-specific illustration. This audit does not claim complete illustration coverage of all 42 operations.','The conceptual diagrams do not encode measured shapes, particle numbers or layer thickness ratios. Canonical operation quantities remain the authority.','The public Site import is not independently hashed here; the audit is tied to the private module and private canonical hashes.'],
 'supporting_files':['apparatus-audit/scene-inventory.json','apparatus-audit/render-inspection.json','apparatus-audit/renders/','crystal-reference-audit.json']
}
(BASE/'apparatus-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Danek apparatus audit','',f"Status: **{out['status']}**. Module SHA-256: `{out['module_sha256']}`.",'',out['scope'],'', 'The module covers 36 of 42 operations in 12 private canonical records. All five source/action guard checks pass. All 36 SVGs parse and render without text outside the view box. The six unsupported operations return null safely.','', '## Findings','']
for f in findings:lines.append(f"- **{f['id']} — {f['status']}:** {f['resolution']}")
lines+=['','## Evidence and limits','','The prior full source inspection and current reread of experimental text on PDF pages 2–3 support apparatus, precursors, material states and acquisition labels. Page 4 supplies the annealing conflict and CdSe comparison scope. The corrected target scenes were visually rechecked. No new temperatures, times, pressure values, bath medium, exact particle counts or measured shell coordinates are introduced.','','Browser interaction and responsive-layout QA remain separate. The source-specific caption marks geometry, color, particle count and layer proportions as illustrative. The separate crystal-reference audit checks the unchanged COD9016056 CIF and the four-site coordinate conversion; it does not claim an experimentally measured Danek structure.','']
(BASE/'apparatus-audit.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({'status':out['status'],'module_sha256':out['module_sha256'],'findings':{s:sum(f['status']==s for f in findings) for s in ['resolved','advisory']}}))
