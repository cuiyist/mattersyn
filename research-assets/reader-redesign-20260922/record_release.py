from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=ROOT/'recipe-atlas/dist'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
refs=read(D/'assets/crystal-references/registry.json')['entries'];pres=read(D/'data/reader-presentation.json')
coverage=[]
for mid,m in pres['materials'].items():
    route_ids=m['record_ids'];matches=[r for r in refs if set(r.get('record_ids',[]))&set(route_ids)]
    coverage.append({'material_id':mid,'formula':m['formula'],'component_only':m.get('component_only',False),'route_ids':route_ids,'reference_entries':[{'id':r['id'],'formula':r['formula'],'source_type':r.get('sourceType','qualified_existing_reference'),'record_ids':sorted(set(r.get('record_ids',[]))&set(route_ids))} for r in matches],'unbound_routes':[rid for rid in route_ids if not any(rid in r.get('record_ids',[]) for r in matches)]})
(D/'data/reader-structure-coverage.json').write_text(json.dumps({'schema_version':'1.0','scope':'Actual independent reference bindings, not exact synthesis-sample coordinates. Source-average and partial-coordinate custom viewers are separate; an unbound route does not mean it has no structural evidence. Component references do not reconstruct a complete composite.','material_count':50,'unique_route_count':123,'materials':coverage},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
version={'version':'0.34.0','prepared_at':datetime.now(timezone.utc).isoformat(),'scope':'Shared Reader/Data redesign, source-scoped figures and references, separated structure-recipe metrics. No new paper review or training labels.'}
(D/'data/reader-release.json').write_text(json.dumps(version,indent=2)+'\n',encoding='utf8')
browser={'scope':'Browser navigation and DOM render smoke checks, not a new scientific review','materials_checked':50,'unique_method_routes_checked':123,'route_failures':0,'checked_sections_per_route':6,'horizontal_overflow_desktop':0,'console_errors_at_end':0,'interactive_checks':['FAPbI3 molecular all-atom labels, functional halos, reset, readable element legend','FAPbI3 Raman gallery and exact source-caption disclosure','FAPbI3 stock components nested beneath matching open/closed stock','390 x 844 phone-width inventory and crystal view; no page-level horizontal overflow','CeO2 chemical inventory excludes burette/flask/filter paper; filtration step opens equipment illustration','Murray Method1 unit-cell and optional Figure6 582-site finite illustration with qualified source scope'],'limitations':'DOM smoke checks do not prove every figure panel or molecular geometry was independently scientifically reviewed. Reference and thumbnail proposals have separate author validation, and four independent code/data findings have a passing correction recheck.'}
(W/'browser-verification.json').write_text(json.dumps(browser,indent=2)+'\n',encoding='utf8')
note='''

## 2026-09-22 — Shared Reader/Data website redesign, version 0.34.0

User authorized all proposed website revisions. The implementation now covers all 50 material/component hubs and 123 distinct synthesis routes. Reader and Data/evidence use the same canonical records; four older named CdSe method routes use the shared reader while their earlier complete evidence editions remain available. No corpus jobs were resumed and no additional paper is claimed reviewed.

Reader improvements: compact chemical depictions and molecular element labels/legends; protocol chemical popovers; apparatus separated from chemicals with equipment schematics; stock illustrations nested under matching collapsible headings using five explicit repaired stock/context bindings; specimen-scoped morphology and measured facts; phase/component unit-cell selectors, original structure/property galleries, and concise referenced intuition. FAPbI3 shows its seven property figures including Raman and a clearly computed ordered-FA P1 reference. The optional Murray Figure6 lattice crop remains an illustration, not either method's assigned product. No measured dopant placement or interface was invented.

Added 18 qualified reference models (17 initially bound, one cubic CdTe alternative deliberately unbound), restored existing CdSe wurtzite bindings, and adapted existing constructed CdSe cubic/finite assets without fitting new coordinates. Some specific phases still lack a verified cell: tetragonal La2(MoO4)3, wurtzite CdTe, cubic CsMnCl3 nc150 and other unresolved products. Amorphous materials are not given arbitrary periodic cells. All source and license qualifications travel with downloads.

The dataset page now separates 1 distinct molecular sample-coordinate asset, 1 explicit source-verified molecular recipe link, and 0 task-ready exact-structure records. Two records reference the same Evans molecular-species9 asset; this is not a CdSe/PbSe QD pair. Exact training admission uses a fail-closed independently audited task-specific profile, bound to canonical digest and exact coordinate bytes. No real profile was automatically admitted. Optional characterization gaps no longer function as an indiscriminate synthesis-completeness rule.

All 675 canonical records and six training export files retain their pre-change hashes. Integrated dataset tests: 68 passed. Shared metadata covers 456 source-figure entries, 452 with existing images; four Peng2000 descriptions retain their missing-original-image state. 175 compact molecular SVG derivatives preserve chemical paths/charges/labels; 627 originals remain unchanged. Independent review identified four code/data-scope issues and closed all four after corrections. Browser checks loaded all50hubs/all123methods; representative interactive and phone-width checks are documented separately.

Build and audit artifacts: `research-assets/reader-redesign-20260922/`, `recipe-atlas/scripts/build_reader_metadata.py`, `recipe-atlas/scripts/structure_recipe_metrics.py`, and explicit stock/thumbnail/reference metadata. The reusable skill now includes `references/reader-and-training-views.md` in both project and installed copies. Public synchronization continues through the existing source-exclusion projection; original PDFs/SI, raw documents, installed runtimes and credentials remain local. Publication/commit verification is recorded separately in the release delivery receipt.
'''
with (ROOT/'MEMORY.md').open('a',encoding='utf8') as f:f.write(note)
# Add a linked registry provenance inventory without claiming these references were newly reviewed synthesis papers.
section=['\n## Crystal reference models\n','Reference models support the Reader and are excluded from measured synthesis labels. Full unit-cell provenance, limitations and licenses are in the [reference registry](https://cuiyist.github.io/mattersyn-site/assets/crystal-references/registry.json).\n']
seen=set()
for r in refs:
    if not r.get('record_ids') or r['sourceUrl'] in seen:continue
    seen.add(r['sourceUrl']);section.append('- ['+r['name']+']('+r['sourceUrl']+'). '+r.get('sourceType','Qualified existing reference').replace('_',' ')+'.\n')
for name in ['README.md','REFERENCES.md']:
    for folder in [ROOT,D]:
        p=folder/name;s=p.read_text(encoding='utf8');s=s.split('\n## Crystal reference models\n')[0];p.write_text(s+'\n'.join(section),encoding='utf8')
print('Saved release inventory, browser-check scope, memory, and structure-source references.')
