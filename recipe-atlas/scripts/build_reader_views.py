"""Static reader entrypoints; scientific data is loaded from separate reviewed records."""
from pathlib import Path
import json
from source_coverage import source_metrics_html
ROOT=Path(__file__).resolve().parents[1]

def write_reader_entrypoints(directory):
    """Regenerate every primary Reader wrapper without touching evidence editions."""
    template=(ROOT/'templates/material-reader.html').read_text(encoding='utf-8')
    contexts={
        'material.html':' ',
        'cdse.html':' data-material-id="cdse-d923c5"',
        'murray-1993-method-1.html':' data-record-id="murray-1993-cdse-method1" ',
        'murray-1993-method-2.html':' data-record-id="murray-1993-cdse-method2" ',
        'alivisatos-2000.html':' data-record-id="peng-2000-cdse-typical" ',
        'nakonechnyi-2017.html':' data-record-id="nakonechnyi-2017-zb-cdse-core" ',
    }
    for filename,context in contexts.items():
        target=directory/filename
        content=template.replace('{{READER_CONTEXT}}',context)
        if not target.exists() or target.read_text(encoding='utf-8')!=content:
            target.write_text(content,encoding='utf-8',newline='\n')
def shell(title,body,script):
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+' · MatterSyn</title><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 40 40%27%3E%3Crect width=%2740%27 height=%2740%27 rx=%279%27 fill=%27%23295888%27/%3E%3Ctext x=%2720%27 y=%2728%27 text-anchor=%27middle%27 fill=%27white%27 font-size=%2726%27%3EM%3C/text%3E%3C/svg%3E"><link rel="stylesheet" href="styles.css"><link rel="stylesheet" href="academic.css"><link rel="stylesheet" href="dataset.css"><link rel="stylesheet" href="atlas.css?v=0.33.0-r2"><link rel="stylesheet" href="apparatus.css"><link rel="stylesheet" href="illustrated-guide.css?v=0.33.0-r2"></head><body><header class="site-header atlas-header"><a class="brand" href="index.html"><span class="brand-mark">M</span>MatterSyn</a><nav aria-label="Atlas navigation"><a href="index.html">Periodic table</a><a href="library.html">Source library</a><a href="dataset.html">Synthesis dataset</a></nav></header><main class="dataset-main">'+body+'</main><script src="vendor/3Dmol-min.js"></script><script type="module" src="'+script+'?v=0.33.0-r2"></script></body></html>'
def library_body(collection):
    library='<div class="dataset-heading"><span class="eyebrow">PUBLISHED SOURCE COLLECTION</span><h1>Source library</h1><p>Papers and supporting datasets contributing synthesis, characterization and properties to MatterSyn.</p></div>' + source_metrics_html(collection) + '<p class="coverage-note">The searchable list below contains reviewed-collection papers and published experimental series.</p><div class="library-summary"><div><strong id="paper-total">—</strong><span>Papers in the reviewed list</span></div><div><strong id="reviewed-total">—</strong><span>Detailed source readers</span></div></div><div class="atlas-results-head"><h2>Reviewed source list<small id="paper-count" aria-live="polite"></small></h2><div class="atlas-filters"><input id="paper-search" class="atlas-search" type="search" aria-label="Search papers by title, DOI or material" placeholder="Title, DOI or material"><select id="paper-status" aria-label="Source evidence scope"><option value="">All source scopes</option><option value="full_documents_reviewed">Main article and supporting information</option><option value="main_only_reviewed">Main article; SI unverified</option><option value="si_only_reviewed">Supporting information; main unverified</option><option value="selected_recipes_reviewed">Selected recipe and figures</option><option value="published_benchmark">Published experimental series</option></select></div></div><div id="paper-results" class="library-list"></div><div class="library-pagination"><button class="atlas-button" id="paper-prev">← Previous</button><span id="paper-page"></span><button class="atlas-button" id="paper-next">Next →</button></div>'
    return library

def main():
    collection=json.loads((ROOT/'dist/data/reader-collection.json').read_text(encoding='utf-8'))
    library=library_body(collection)
    paper='''<nav class="material-hub-nav"><a href="index.html">Periodic table</a><span>→</span><a href="library.html">Source library</a><span>→</span><span>Paper record</span></nav><div class="dataset-heading"><span class="eyebrow">SOURCE COVERAGE RECORD</span><h1 id="paper-title">Paper</h1><p><a id="paper-doi"></a></p><p id="paper-title-status"></p></div><p id="paper-review" class="coverage-note"></p><div id="paper-full-review" class="review-actions"></div><section class="record-section"><h2>Main article and supporting information</h2><p id="paper-coverage"></p><p id="paper-extraction"></p></section><section class="record-section"><h2>Material collections</h2><div id="paper-materials"></div><p class="atlas-footnote">Only source-reviewed synthesis contributions link to material pages. Unreviewed title mentions remain search candidates in the library.</p></section><section class="record-section"><h2>Synthesis and experimental records</h2><div id="paper-records"></div></section><p id="paper-source-note" class="coverage-note"></p>'''
    review='<nav class="material-hub-nav"><a href="index.html">Periodic table</a><span>→</span><a href="library.html">Source library</a><span>→</span><span>Full-document review</span></nav><div class="dataset-heading"><span class="eyebrow">SOURCE DOCUMENT REVIEW</span><h1 id="review-title">Source review</h1><p><a id="review-doi"></a></p></div><p class="coverage-note" id="review-summary">Loading reviewed source coverage…</p><div class="review-actions"><a id="review-download">Download machine-readable coverage JSON ↓</a><a href="library.html">Source library →</a></div><nav class="review-subnav"><a href="#documents">Pages reviewed</a><a href="#recipes">Recipes and controls</a><a href="#characterization">Characterization</a><a href="#figures">Original figures</a><a href="#gaps">Unresolved details</a></nav><div id="review-body"><section id="documents" class="record-section"></section><section id="recipes" class="record-section"></section><section id="characterization" class="record-section"></section><section id="figures" class="record-section"></section><section id="gaps" class="record-section"></section></div><dialog class="review-dialog" id="figure-dialog"><header><h2 id="figure-title">Original figure</h2><button id="figure-close" type="button">Close ×</button></header><img id="figure-large" alt="Original figure"></dialog>'
    (ROOT/'dist/paper-review.html').write_text(shell('Full-document review',review,'paper-review.mjs').replace('paper-review.mjs?v=0.33.0-r2','paper-review.mjs?v=0.40.2').replace('</head>','<link rel="stylesheet" href="paper-review.css?v=0.33.0-r2"></head>'),encoding='utf-8',newline='\n')
    for name,title,body,script in [('library.html','Source library',library,'library-app.mjs'),('paper.html','Paper coverage',paper,'paper-app.mjs')]:
        (ROOT/'dist'/name).write_text(shell(title,body,script),encoding='utf-8',newline='\n')
    write_reader_entrypoints(ROOT/'dist')
if __name__=='__main__':main()

