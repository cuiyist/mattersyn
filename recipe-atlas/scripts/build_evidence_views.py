"""Render reviewed figure evidence without turning contextual figures into recipe labels."""
import json, html
from pathlib import Path
from build_reader_views import shell
from asset_display import load_overrides
ROOT=Path(__file__).resolve().parents[1]
esc=lambda x:html.escape(str(x),quote=True)
def facts(value):
    if isinstance(value,dict):return '<dl class="evidence-facts">'+''.join('<div><dt>'+esc(k.replace('_',' '))+'</dt><dd>'+facts(v)+'</dd></div>' for k,v in value.items())+'</dl>'
    if isinstance(value,list):return '<ul>'+''.join('<li>'+facts(v)+'</li>' for v in value)+'</ul>'
    if value is None:return 'Not reported'
    if isinstance(value,bool):return 'Yes' if value else 'No'
    return esc(value)
def dialog():
    return '''<dialog id="evidence-dialog" class="evidence-dialog" aria-label="Original published figure"><div class="evidence-tools"><button id="evidence-close">Close ×</button><button id="evidence-minus" aria-label="Zoom out">−</button><output id="evidence-zoom">100%</output><button id="evidence-plus" aria-label="Zoom in">+</button><button id="evidence-fit">Fit figure</button></div><div id="evidence-viewport" tabindex="0"><img id="evidence-large-image" alt=""></div><p id="evidence-caption"></p></dialog>'''
def figbutton(src,caption,source_url=None,display_note=None):
    if source_url:return '<a class="evidence-image-button" href="'+esc(source_url)+'" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="'+esc(src)+'" alt="Source-link card; original figure not reproduced"><span>Read the source figure ↗</span></a><p class="atlas-footnote">'+esc(display_note or'Original figure not reproduced. This card is a source link, not measured data.')+'</p>'
    return '<button class="evidence-image-button" data-evidence-image="'+esc(src)+'" data-caption="'+esc(caption)+'"><img loading="lazy" src="'+esc(src)+'" alt="'+esc(caption)+'"><span>Enlarge original figure ↗</span></button>'
def figure_display(f,overrides):
    if f.get('display_asset'):
        a=f['display_asset'];return a['file'],a.get('source_url'),a.get('display_note')
    a=f['original_figure_asset'];row=overrides.get(a.get('file'))
    return(row['display_path'],row['source_url'],row['display_note'])if row else(a['file'],None,None)
def main():
    overrides=load_overrides(ROOT)
    a=json.loads((ROOT/'dist/data/paper-evidence/murray1993.json').read_text(encoding='utf-8'))
    body='<nav class="material-hub-nav"><a href="index.html">Periodic table</a> → <a href="cdse.html">CdSe</a> → Figure archive</nav><div class="dataset-heading"><span class="eyebrow">MURRAY, NORRIS & BAWENDI · JACS 1993</span><h1>Characterization and structural models</h1><p>All 15 figures from the main article, with sample-specific evidence and acquisition methods.</p></div><p class="coverage-note">The original paper reports SAED in text, but shows no SAED pattern. Figures remain paper-level evidence: their assignments to Method 1 or Method 2 are unresolved. Experimental observations and the authors’ simulations are identified separately.</p><div class="download-links"><a href="https://doi.org/10.1021/ja00072a025">Primary paper ↗</a><a href="data/paper-evidence/murray1993.json" download>Download evidence JSON ↓</a><a href="nakonechnyi-2017-saed.html">Core/shell SAED from Nakonechnyi et al. →</a></div><div class="figure-archive">'
    for f in a['figures']:
        src,source_url,display_note=figure_display(f,overrides);cap='Figure '+str(f['figure'])+'. '+f['caption_paraphrase']
        body+='<article class="figure-archive-card" id="figure-'+str(f['figure'])+'"><span class="mini-label">'+esc(f['category'].replace('_',' '))+'</span><h2>Figure '+str(f['figure'])+'</h2>'+figbutton(src,cap,source_url,display_note)+'<p>'+esc(f['caption_paraphrase'])+'</p><p class="atlas-footnote">'+esc(f.get('evidence_kind',''))+' · Printed page '+esc(f['source'].get('printed_page',''))+'</p><details><summary>Sample, measurements and interpretation</summary>'+facts({'sample':f.get('sample'), 'findings':f.get('scoped_quantitative_facts_and_findings'), 'training_exclusion_reason':f.get('training_exclusion_reason')})+'</details></article>'
    body+='</div><section class="record-section"><h2>Measurement methods</h2>'+facts(a['measurement_methods'])+'</section><section class="record-section"><h2>Text-only and cited evidence</h2>'+facts(a['text_only_and_prior_work_evidence'])+'</section><section class="record-section"><h2>Additional source observations</h2>'+facts(a['additional_article_evidence'])+'</section>'+dialog()
    (ROOT/'dist/murray-1993-characterization.html').write_text(shell('Murray 1993 figure archive',body,'evidence-gallery.mjs'),encoding='utf-8',newline='\n')
    n=a['related_paper_saed_check']['nakonechnyi2017'];s=n['saed'];src,source_url,display_note=figure_display(s,overrides)
    body='<nav class="material-hub-nav"><a href="index.html">Periodic table</a> → <a href="cdse.html">CdSe</a> → Core/shell SAED</nav><div class="dataset-heading"><span class="eyebrow">NAKONECHNYI ET AL. · 2017 · SUPPORTING INFORMATION S3</span><h1>Selected-area electron diffraction</h1><p>Original Figure S2: CdSe/CdS and CdSe/ZnSe core/shell particles.</p></div><p class="coverage-note">'+esc(s['scope_warning'])+'</p>'+figbutton(src,s['caption_paraphrase'],source_url,display_note)+'<div class="saed-panels">'+''.join('<article><h2>Panel '+esc(p['panel'])+'</h2><p>'+esc(p['product'])+'</p><p>Core: '+esc(p['core'])+'<br>Shell: '+esc(p['shell'])+'</p></article>' for p in s['panels'])+'</div><p>'+esc(s['sample_link_status'])+'</p><div class="download-links"><a href="https://doi.org/10.1021/acs.chemmater.7b00354">Primary paper ↗</a><a href="https://acs.figshare.com/doi/suppl/10.1021/acs.chemmater.7b00354">Supporting information ↗</a><a href="data/paper-evidence/nakonechnyi2017-saed.json" download>SAED evidence JSON ↓</a><a href="records/nakonechnyi-2017-zb-cdse-cds-seeded-growth.html">Reviewed CdSe/CdS growth record →</a></div>'+dialog()
    (ROOT/'dist/nakonechnyi-2017-saed.html').write_text(shell('Core/shell SAED',body,'evidence-gallery.mjs'),encoding='utf-8',newline='\n')
if __name__=='__main__':main()
