"""Dataset discovery page, generated from validated manifest counts."""
import json
from pathlib import Path


def _outcome_text(value):
    if not isinstance(value,dict):return str(value)
    shown=value.get('value')
    if shown is None:
        low,high=value.get('minimum'),value.get('maximum')
        shown=(str(low) if low is not None else '—')+'–'+(str(high) if high is not None else '—')
    unit=value.get('unit')
    return str(shown)+((' '+str(unit)) if unit else '')

def structure_coverage_html(report,esc,pair_rows=()):
    outcomes=report.get('structure_outcome_coverage')
    coverage=report.get('structure_recipe_coverage')
    if not coverage:
        return '<section class="record-section"><h2>Structure and recipe coverage</h2><p>Coordinate availability and recipe-link metrics have not been generated for this build. Unavailable counts are not zero.</p></section>'
    counts=coverage['counts']
    pair_counts=(outcomes or {}).get('counts',{})
    metrics=[]
    if outcomes:
        metrics.append(('recipe_structure_rows','Source-checked synthesis–structure rows',pair_counts))
        metrics.append(('source_groups','Source groups represented',pair_counts))
    metrics.extend([('sample_coordinate_assets','Measured-product coordinate assets',counts),('source_verified_explicit_coordinate_links','Coordinate assets linked to an explicit recipe',counts),('exact_task_ready_records','Exact-coordinate training-ready records',counts)])
    result='<section class="record-section"><h2>Structure and recipe coverage</h2><div class="dataset-summary">'
    for key,label,source_counts in metrics:
        value=source_counts.get(key)
        result+='<div><strong>'+('—' if value is None else str(value))+'</strong><span>'+esc(label)+'</span></div>'
    result+='</div>'
    if outcomes:
        result+='<p>A synthesis–structure row is one source-reviewed recipe record explicitly linked to an identified sample, with evidence for its composition and at least one phase, morphology, dimension or other allowlisted structural result. A CIF is not required. One row may contain several measurements. Counts are canonical record/sample rows: repeated physical samples across papers have not yet been deduplicated, so these are not independent batch counts.</p>'
        result+='<a class="data-download" href="data/synthesis-structure-pairs.json">Inspect every counted row and its source locators ↓</a>'
        if pair_rows:
            result+='<details class="pair-row-browser"><summary>Browse all '+esc(str(pair_counts.get('recipe_structure_rows',len(pair_rows))))+' synthesis–structure rows</summary><div class="table-scroll"><table class="reagent-table"><thead><tr><th>Source</th><th>Sample / composition</th><th>Synthesis route</th><th>Structural outcome</th></tr></thead><tbody>'
            for row in pair_rows:
                outcomes=[]
                for fact in row.get('product_structure_fields',[]):outcomes.append(fact['kind'].replace('_',' ')+': '+_outcome_text(fact['value']))
                for measurement in row.get('structural_measurements',[]):outcomes.append(measurement['property'].replace('_',' ')+': '+_outcome_text(measurement['value']))
                source='<a href="'+esc(row['record_page_path'])+'">'+esc(row['title'])+' ↗</a><small>'+esc(str(row['year'] or ''))+' · '+esc(row['source_group'])+'</small>'
                composition=row.get('composition',{}).get('value') or 'Composition not stated in the row'
                sample=esc(row.get('source_sample_label') or row['sample_id'])+'<small>'+esc(composition)+' · sample '+esc(row['sample_id'])+'</small>'
                route=esc(row['method'] or 'Route details in record')
                result+='<tr><td>'+source+'</td><td>'+sample+'</td><td>'+route+'</td><td>'+esc('; '.join(outcomes))+'<small><a href="'+esc(row['record_page_path'])+'#structures">Evidence and source locators ↗</a></small></td></tr>'
            result+='</tbody></table></div></details>'
    result+='<p>Coordinate assets, recipe-linked structural outcomes and task-ready coordinate records are separate counts. A source-checked synthesis–structure row does not by itself qualify for a particular training task.</p>'
    kinds=coverage.get('asset_representation_counts',{})
    linked_kinds=coverage.get('explicit_link_representation_counts',{})
    names={'molecular_structure':'molecular structures','experimental_periodic_structure':'experimental periodic structures','finite_sample_structure':'finite sample structures','unclassified':'representation not yet classified'}
    if kinds:
        result+='<p>Available sample-coordinate assets: '+esc('; '.join(str(n)+' '+names.get(k,k) for k,n in sorted(kinds.items())))+'.'
        if linked_kinds:result+=' Explicit recipe links: '+esc('; '.join(str(n)+' '+names.get(k,k) for k,n in sorted(linked_kinds.items())))+'.'
        result+='</p>'
    molecular=counts.get('molecular_structure_assets')
    if molecular is not None:
        molecular_text='; '.join(str(n)+' '+names.get(k,k) for k,n in sorted(coverage.get('molecular_asset_representation_counts',{}).items()))
        result+='<p>Available molecular structure assets: '+esc(molecular_text or str(molecular))+'; these are not included in measured-product coordinate or exact-coordinate training counts.</p>'
    result+='<p>Coordinate availability is checked against local published assets. External bulk references and illustrative viewers are excluded. Exact-coordinate training admission additionally requires an approved measured structure, an explicit requested task, and an independently audited profile of required recipe fields. Missing optional or characterization fields are not automatically treated as missing synthesis conditions.</p>'
    result+='<a class="data-download" href="data/structure-recipe-coverage.json">Inspect record-level availability, linkage and exclusion reasons ↓</a></section>'
    return result

def render(report,manifest,head,header,esc,human,pair_rows=()):
    tasks=report['eligible_by_task']
    s=head('Synthesis records')+'<body>'+header()+'''<main class="dataset-main"><div class="dataset-heading"><span class="eyebrow">MATERIALS SYNTHESIS DATASET · PILOT COLLECTION</span><h1>Synthesis records</h1><p>Individual protocols and experimental observations, with traceable sources and task-specific training exports.</p></div><div class="dataset-summary">'''
    for n,label in [(report['curated_recipes'],'Reviewed protocols and controls'),(report['published_benchmark_rows'],'Imported benchmark experiment rows'),(report['families'],'Material families')]:
        s+='<div><strong>'+str(n)+'</strong><span>'+label+'</span></div>'
    s+='''</div><div class="record-notice"><p><strong>Benchmark scope:</strong> the imported experiment rows come from one published PbS study. They are a separate collection, not a restriction on the materials reviewed here.</p><p>Crystal-phase, morphology and size observations remain available even when no record is ready for exact-structure training. Coordinate availability, recipe linkage and task readiness are reported separately below.</p>'''
    s+='</div>'+structure_coverage_html(report,esc,pair_rows)
    s+='''<div class="dataset-filters"><label>Search records<input id="record-search" type="search" placeholder="Material, paper or method"></label><label>Material family<select id="family-filter"><option value="">All families</option>'''+''.join('<option>'+esc(f)+'</option>' for f in manifest['families'])+'''</select></label><label>Training task<select id="task-filter"><option value="">All records</option>'''+''.join('<option value="'+k+'">'+esc(human(k))+'</option>' for k in tasks)+'''</select></label><label>Collection<select id="type-filter"><option value="recipes">Recipes and experiment rows</option><option value="reviewed">Reviewed literature records</option><option value="benchmark">Published PbS benchmark</option><option value="procedure">Shared procedures</option><option value="observation">Contextual observations</option><option value="all">All records</option></select></label></div><p id="record-count" class="record-count" aria-live="polite"></p><div id="catalog-results" class="record-list"></div><div class="catalog-pagination"><button id="page-prev" type="button">← Previous</button><span id="page-label"></span><button id="page-next" type="button">Next →</button></div>'''
    s+='''<section id="exports" class="record-section"><div class="section-heading"><div><h2>Dataset downloads<small>One canonical record generates each page and its permitted training views.</small></h2></div></div><div class="export-grid"><a href="data/records.jsonl" download><strong>All canonical records ↓</strong><span>JSONL · protocols, observations and shared procedures</span></a><a href="data/record.schema.json" download><strong>Record schema ↓</strong><span>Typed quantities, evidence, sample links and explicit missingness</span></a><a href="data/dataset-manifest.json" download><strong>Dataset manifest ↓</strong><span>Hashes, source groups, versions and eligibility</span></a><a href="data/validation-report.json" download><strong>Validation report ↓</strong><span>Schema and scientific referential-integrity checks</span></a></div><div class="export-grid">'''+''.join('<a href="data/exports/'+k+'.jsonl" download><strong>'+esc(human(k))+' ↓</strong><span>'+str(v)+' eligible records · JSONL</span></a>' for k,v in tasks.items())+'''</div><div class="record-notice"><strong>Scope and reuse</strong><p>The reviewed records describe literature protocols, variants and controls, not independently reproduced experiments. Shared preparation, characterization and assay procedures are separate records. Contextual observations without a reconstructed synthesis are counted separately and have no enabled training tasks. The PbS collection contains 100 selected rows from one published study: 95 optical outcomes and five flagged failures. It is not 100 newly curated papers.</p><p>The PbS data are adapted from Voznyy et al. (2019), <a href="https://doi.org/10.1021/acsnano.9b03864.s002">official dataset</a>, under <a href="https://creativecommons.org/licenses/by-nc/4.0/">CC BY-NC 4.0</a>. Attribution and the noncommercial restriction travel with the exports. Changes: named columns and units, row IDs, selected subset, derived cohort labels, and null continuous targets for failure placeholders. Other article and figure rights remain separate.</p><p>All records from a connected source/recipe group stay together. The small collection and its source/lineage-group partitions do not establish reliable cross-study performance. Use a frozen, audited split manifest for any model comparison. The PbS benchmark below uses a separately documented within-study evaluation. No input examples use contextual figures or chemical-intuition text as experimental labels.</p></div></section>'''
    s+='<section class="record-section"><h2>Pilot source queue</h2><p>'+str(report.get('queue_count',0))+' remaining papers across '+str(report.get('queue_families',0))+' candidate families await full extraction. First-page screening is not recipe curation.</p><a class="data-download" href="data/pilot-source-queue.json" download>Download source queue ↓</a></section>'
    baseline=json.loads((Path(__file__).resolve().parents[1]/'dist/data/baseline-report.json').read_text(encoding='utf-8'))
    s+='''<section class="record-section"><h2>Baseline evaluation<small>PbS absorption-wavelength prediction</small></h2><p>Three compact models were evaluated using all 2,529 continuous-outcome rows from the published 2,552-row dataset. The 23 failure-coded rows were excluded from regression. The 100-page coverage subset was not used to estimate performance.</p><div class="table-scroll"><table class="reagent-table"><thead><tr><th>Evaluation</th><th>Mean predictor MAE</th><th>Ridge MAE</th><th>kNN MAE</th></tr></thead><tbody>'''
    for key,label in [('grouped_within_study_holdout','Held-out recipe groups'),('author_rule_cohort_transfer','Author-defined cohort transfer')]:
        m=baseline['evaluations'][key]['metrics'];s+='<tr><td>'+label+'</td>'+''.join('<td>'+format(m[k]['mae_nm'],'.2f')+' nm</td>' for k in ['training_mean','ridge','distance_weighted_knn'])+'</tr>'
    s+='''</tbody></table></div><p>Repeated physical recipes stay together. Scaling and parameter selection use training data only. These results concern one study and one optical property; they do not evaluate crystal-to-recipe generation, laboratory reproducibility, or cross-material generalization.</p><a class="data-download" href="data/baseline-report.json">Inspect methods, limitations and results ↗</a></section></main><script type="module" src="dataset-app.mjs"></script></body></html>'''
    return s
