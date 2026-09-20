import fs from 'node:fs';
import path from 'node:path';
const base='[local path redacted]';
const dist=path.join(base,'recipe-atlas/dist');
const replacements=[
 ['Their linewidths are reported as nearly equal','Their linewidths are reported as equal'],
 ['their linewidths are reported as nearly equal','their linewidths are reported as equal'],
 ['The authors report size statistics from multiple particles, not a measurement of just one dot.','The ±5% and ±6% describe population size spreads. The authors note that these widths are limited by uncertainty in locating particle edges.'],
 ['QUALITATIVE OBSERVATION · P. 8709','QUALITATIVE OBSERVATION · P. 8710']
];
for(const name of ['index.html','characterization.mjs']){
 let text=fs.readFileSync(path.join(dist,name),'utf8');for(const [a,b]of replacements)text=text.replaceAll(a,b);fs.writeFileSync(path.join(dist,name),text);
}
let html=fs.readFileSync(path.join(dist,'index.html'),'utf8');
html=html.replace('The idealized model omits the paper’s stacking faults, surface cap and detailed facets; it is not a reconstruction of the TEM particle.','The idealized model omits the paper’s stacking faults, surface cap and detailed facets; it is not a reconstruction of the TEM particle. TOP–TOPO describes the synthesis cap; TEM preparation uses a pyridine dispersion, without specifying the imaged particles’ exact ligand coverage.');
fs.writeFileSync(path.join(dist,'index.html'),html);
fs.appendFileSync(path.join(dist,'characterization.css'),'\n#product{margin-bottom:65px}#properties{margin-bottom:65px}#properties .insight-grid{margin-bottom:28px}@media(max-width:760px){.site-header{height:auto;min-height:86px;padding-top:17px;padding-bottom:17px}.site-header nav{flex-basis:100%}#product,#properties{margin-bottom:45px}}\n');
const data=JSON.parse(fs.readFileSync(path.join(base,'research-assets/murray1993-characterization.json'),'utf8').replace(/^\uFEFF/,''));
delete data.source.local_pdf;delete data.recommended_page_groups;
data.displayed_figure_assets={figures:[3,5,6,11,15],manifest:'murray1993-figures/figure-manifest.json',policy:'Faithful cropped raster extracts of original published panels; axes, internal labels and scale bar retained. No redrawing or curve digitization.'};
fs.writeFileSync(path.join(dist,'assets/murray1993-characterization.json'),JSON.stringify(data,null,2)+'\n');
const recipePath=path.join(dist,'assets/murray1993-recipe.json');
const recipe=JSON.parse(fs.readFileSync(recipePath,'utf8').replace(/^\uFEFF/,''));
recipe.characterization_record={file:'murray1993-characterization.json',scope:'Main-article structural characterization and optical properties; record-specific sample links and measurement/model distinctions.',displayed_figures:[3,5,6,11,15],raman:'Not reported in inspected main article; SI unverified.'};
fs.writeFileSync(recipePath,JSON.stringify(recipe,null,2)+'\n');
const readmePath=path.join(base,'recipe-atlas/README.md');
let readme=fs.readFileSync(readmePath,'utf8');
readme=readme.replace('## Preserved example: Alivisatos group, 2000','## Structural characterization and properties\n\nThe featured page has four main sections: Precursors, Protocols, Final structures and Properties, followed by a Sources appendix. `characterization.mjs` and `characterization.css` provide independent structural and optical figure selectors plus an accessible enlarged-figure dialog with zoom and fit controls. The existing crystal viewer remains a separate illustrative model.\n\nFive faithful, visually inspected 300-dpi figure extracts retain the original labels, axes and TEM scale bar: TEM Figure 6, XRD Figure 11, experiment/model comparison Figure 15, absorption Figure 3 and absorption/PL Figure 5. Public provenance is recorded in `dist/assets/murray1993-figures/figure-manifest.json`; the full article and local machine paths are excluded from deployed assets.\n\n`dist/assets/murray1993-characterization.json` records experimental conditions, figure-specific observations, source discrepancies and missing properties. SAED is text-only; cited EXAFS is prior work; EDX describes discarded byproducts. Raman is not reported in the inspected main article, and SI remains unverified. Figure 15’s one-versus-1.3 fault-count discrepancy is preserved. Equal nominal optical/TEM sizes do not establish specimen identity.\n\n## Preserved example: Alivisatos group, 2000');
fs.writeFileSync(readmePath,readme);
const skillRoot=path.join(base,'skills/mattersyn-paper-to-site');
const skillPath=path.join(skillRoot,'SKILL.md');
let skill=fs.readFileSync(skillPath,'utf8').replace(/^\uFEFF/,'');
const start=skill.indexOf('Useful page surfaces, selected to fit the paper:');const end=skill.indexOf('\nDrive text, scene selection',start);
if(start<0||end<0)throw Error('Skill section missing');
skill=skill.slice(0,start)+`Use the user's preferred four main sections, with paper identity above and a Sources appendix below:

1. **Precursors:** chemical names, formulas, roles, structures, functional-group highlights and provenance.
2. **Protocols:** meaningful stages and separate branches; a different apparatus/action scene for each stage with adjacent conditions.
3. **Final structures:** measured morphology, dimensions, phase and structural characterization such as TEM, XRD or SAED, followed by a rotatable/zoomable reference crystal model when useful.
4. **Properties:** source-reported measurements such as absorption, photoluminescence, Raman, electrical or magnetic behavior, with sample identity and acquisition conditions.

Include selected original characterization figures with readable scales/axes, short explanations and enlarged views when available. Distinguish measured data, the paper's simulations and the website's illustrative models. Missing techniques remain absent or explicitly unreported in the inspected sources; a requested example such as Raman does not justify inventing a spectrum. Sources, unresolved details, structured downloads and preserved examples belong in the appendix.
`+skill.slice(end);
fs.writeFileSync(skillPath,skill);
const visualPath=path.join(skillRoot,'references/visuals-and-models.md');
let visual=fs.readFileSync(visualPath,'utf8').replace(/^\uFEFF/,'');
visual=visual.replace('## Apparatus scenes',`## Characterization and properties

Separate structural evidence (for example TEM, diffraction, phase and morphology) from material properties (for example absorption, emission and Raman). Associate each figure or result with its own reported sample or series, measurement conditions, and main/SI locator. Similar nominal sizes do not prove cross-figure identity.

For selected original figures, render or crop faithfully from the verified PDF and retain axes, legends, panel labels and scale bars. Inspect source pages and extracted panels, provide attribution and source links, and record crop/page provenance. Never generate, cosmetically redraw or enhance a micrograph or spectrum as if it were measured evidence. Enlarging an original figure is preferable to an invented interactive curve; digitization, if requested, needs a separate derived-data label and uncertainty.

Give nonexperts a concise explanation of what the technique probes and how to read the displayed figure. Label experimental traces and author simulations separately, preserve source inconsistencies, and avoid claiming a unique atomic reconstruction from a model fit. Text-only characterization stays text-only; cited prior work and byproduct measurements must not become newly measured product results. An unreported technique is missing only within the inspected source scope, especially while SI is unresolved.

## Apparatus scenes`);
fs.writeFileSync(visualPath,visual);
console.log('Scientific record, four-section skill, figure provenance and project README updated.');
