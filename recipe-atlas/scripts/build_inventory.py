"""Derive inventory counts from reviewed inputs and render reconciled membership."""
from pathlib import Path
from collections import Counter
import json, html, re
from build_reader_views import shell
from review_scope import MAIN_SI, MAIN_ONLY, SI_ONLY, MAIN_SELECTED_SI
from derive_inventory import generate
from source_coverage import collection_metrics_html

ROOT = Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def esc(s): return html.escape(str(s))
def link(label, url): return '<a href="'+esc(url)+'">'+esc(label)+'</a>'

def main():
    inventory = generate(ROOT)
    summary = inventory['summary']
    records = [read(p) for p in (ROOT/'data/records').glob('*.json')]
    byid = {r['record_id']:r for r in records}
    assert set(byid) == {rid for p in inventory['per_paper'] for rid in p['record_ids']}, 'Update audited inventory for new/removed records'
    assert len(records) == summary['canonical_records']
    for p in inventory['per_paper']:
        rr = [r for r in records if r['lineage']['source_group']==p['source_group']]
        assert {r['record_id'] for r in rr}==set(p['record_ids']), 'Inventory source assignment changed'
        assert dict(Counter(r['record_type'] for r in rr))==p['record_type_counts'], 'Inventory record types changed'
    hubs = read(ROOT/'dist/data/materials-index.json')['materials']
    assert len(hubs)==summary['public_material_hubs']
    assert {m['id'] for m in hubs}=={m['material_hub_id'] for m in inventory['per_material'] if m['public_hub_exists']}, 'Inventory material identities changed'
    route_ids = {r['record_id'] for m in hubs for r in read(ROOT/'dist/data/materials'/(m['id']+'.json'))['records']}
    assert len(route_ids)==summary['synthesis_route_variant_records']
    assert {byid[r]['material']['formula'] for r in route_ids}==set(inventory['material_system_lists']['direct_synthesis_targets'])
    reviews = read(ROOT/'dist/data/paper-review-index.json')['papers']
    main_si_reviews = [r for r in reviews if r['review_scope']==MAIN_SI]
    main_only_reviews = [r for r in reviews if r['review_scope']==MAIN_ONLY]
    assert len(main_si_reviews)==summary['formal_full_main_and_matched_si_reviews']
    assert {r['id'] for r in main_si_reviews}=={p.get('paper_id',p['source_group']) for p in inventory['per_paper'] if p['review_status']=='full_supplied_main_and_matched_si_review'}, 'Inventory main-plus-SI review scopes changed'
    assert sum(p['pages_read'] for p in main_si_reviews)==summary['formal_full_review_pages']
    assert len(main_only_reviews)==summary.get('formal_full_main_reviews_si_unverified',0)
    assert {r['id'] for r in main_only_reviews}=={p.get('paper_id',p['source_group']) for p in inventory['per_paper'] if p['review_status']=='full_supplied_main_review_si_unverified'}, 'Inventory main-only review scopes changed'
    assert sum(p['pages_read'] for p in main_only_reviews)==summary.get('formal_full_main_only_review_pages',0)
    si_only_reviews = [r for r in reviews if r['review_scope']==SI_ONLY]
    assert len(si_only_reviews)==summary.get('formal_full_si_reviews_main_unverified',0)
    assert {r['id'] for r in si_only_reviews}=={p.get('paper_id',p['source_group']) for p in inventory['per_paper'] if p['review_status']=='full_supplied_si_review_main_unverified'}, 'Inventory SI-only review scopes changed'
    assert sum(p['pages_read'] for p in si_only_reviews)==summary.get('formal_full_si_only_review_pages',0)
    selected_si_reviews = [r for r in reviews if r['review_scope']==MAIN_SELECTED_SI]
    assert len(selected_si_reviews)==summary.get('formal_main_and_selected_si_reviews',0)
    assert {r['id'] for r in selected_si_reviews}=={p.get('paper_id',p['source_group']) for p in inventory['per_paper'] if p['review_status']=='full_main_and_selected_si_independently_reviewed'}, 'Inventory selected-SI review scopes changed'
    assert sum(p['pages_read'] for p in selected_si_reviews)==summary.get('formal_main_and_selected_si_review_pages',0)
    library = read(ROOT/'dist/data/library-index.json')
    assert len(library['papers'])==summary['local_paper_groups_indexed']
    assert library['summary']['sourceDocumentCount']==summary['local_document_files_indexed']
    assert summary['full_corpus_recipe_count'] is None and summary['full_corpus_distinct_synthesized_material_count'] is None
    output = ROOT/'dist/data/inventory-summary.json'
    output.write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    collection = read(ROOT/'dist/data/reader-collection.json')
    cards = collection_metrics_html(collection)
    body = '<div class="dataset-heading"><span class="eyebrow">PUBLISHED COLLECTION</span><h1>Materials and synthesis inventory</h1><p>Source-linked material systems and synthesis contributions.</p></div>'+cards
    body += '<section class="record-section"><h2>Verified material systems</h2><p>Counts below use direct synthesis targets. Component contributions are cross-links to the same records, not additional recipes.</p><div class="table-scroll"><table class="reagent-table"><thead><tr><th>Material system</th><th>Direct routes / variants</th><th>Component contributions</th><th>Controls</th></tr></thead><tbody>'
    for m in inventory['per_material']:
        if not m['public_hub_exists']: continue
        label = m['material_system']+(' · component only' if m['public_hub_component_only'] else '')
        body += '<tr><td>'+link(label,m['material_hub_url'])+'</td><td>'+str(m['direct_synthesis_route_variant_count'])+'</td><td>'+str(m['component_route_contribution_count'])+'</td><td>'+str(m['contextual_control_count'])+'</td></tr>'
    body += '</tbody></table></div><p>Fe–O retains unresolved phase and stoichiometry. Core/shell products remain distinct material systems. A shell’s properties are not relabeled as properties of an isolated component.</p></section>'
    statuses = {'full_main_and_selected_si_independently_reviewed':'Complete supplied main + selected matched SI pages; remaining SI unreviewed','full_supplied_main_and_matched_si_review':'Complete supplied main + matched SI','full_supplied_main_review_si_unverified':'Complete supplied main; SI unverified','full_supplied_si_review_main_unverified':'Complete supplied SI; main unverified','legacy_main_article_review_si_unverified':'Main article reviewed; SI unverified','selected_recipe_and_figure_review':'Selected recipe and figures','published_numeric_benchmark':'Published experimental series'}
    body += '<section class="record-section"><h2>Reviewed-collection papers</h2><p>Source scopes and citations are available in the '+link('source library','library.html')+'.</p><div class="table-scroll"><table class="reagent-table inventory-papers"><thead><tr><th>Source and review scope</th><th>Routes</th><th>Controls</th><th>Procedures</th><th>Observations</th><th>Experimental rows</th><th>Experimental series</th></tr></thead><tbody>'
    for p in inventory['per_paper']:
        paper = next((v for v in library['papers'] if v['doi'].lower()==p['doi'].lower()),None)
        url = p.get('paper_review_url') or ('paper.html?id='+paper['id'] if paper else 'dataset.html')
        cell = link(p['title'],url)+'<small>'+str(p['year'])+' · '+link(p['doi'],p['url'])+'</small><small>'+esc(statuses.get(p['review_status'],p['review_status'].replace('_',' ')))+'</small>'
        body += '<tr><td>'+cell+'</td>'+''.join('<td>'+str(p.get(k,0))+'</td>' for k in ['synthesis_route_variant_count','contextual_control_count','procedure_count','contextual_observation_count','experimental_row_count','benchmark_row_count'])+'</tr>'
    body += '</tbody></table></div></section><section class="record-section"><h2>Review and website standard</h2><p>Each material page follows the CdSe standard: precursors and stocks; illustrated synthesis protocol; final structures and original characterization; properties; and referenced chemical intuition. Missing source information stays explicit. Crystal references, diagrams and author interpretations do not become measured training labels.</p><p>'+link('Download the inventory JSON ↓','data/inventory-summary.json')+' · '+link('Open the synthesis dataset →','dataset.html')+'</p></section>'
    page = shell('Materials and synthesis inventory',body,'inventory.mjs').replace('class="dataset-main"','class="dataset-main inventory-main"')
    (ROOT/'dist/inventory.html').write_text(page,encoding='utf-8',newline='\n')
    # Generated homepage summary is replaced, never accumulated on rebuild.
    home = ROOT/'dist/index.html';text=home.read_text(encoding='utf-8')
    text=re.sub(r'<!--inventory-summary-start-->.*?<!--inventory-summary-end-->','',text,flags=re.S)
    snippet='<!--inventory-summary-start--><section class="inventory-overview" aria-label="Website source coverage and reviewed collection">'+cards+'<p>'+link('Materials and recipes: view the reviewed inventory →','inventory.html')+'</p></section><!--inventory-summary-end-->'
    text=text.replace('<div class="element-controls">',snippet+'<div class="element-controls">',1)
    home.write_text(text,encoding='utf-8',newline='\n')
    print(f"Inventory reconciled: {summary['local_paper_groups_indexed']:,} paper groups; {summary['direct_synthesis_target_systems']} direct systems; {summary['synthesis_route_variant_records']} routes; unknown full-corpus totals preserved.")

if __name__=='__main__': main()
