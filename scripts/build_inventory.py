"""Render an independently audited inventory; reject stale counts before publishing."""
from pathlib import Path
from collections import Counter
import json, html, re
from build_reader_views import shell
from review_scope import MAIN_SI, MAIN_ONLY

ROOT = Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def esc(s): return html.escape(str(s))
def link(label, url): return '<a href="'+esc(url)+'">'+esc(label)+'</a>'

def main():
    inventory = read(ROOT/'data/inventory-summary.json')
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
    assert {r['id'] for r in main_si_reviews}=={p['source_group'] for p in inventory['per_paper'] if p['review_status']=='full_supplied_main_and_matched_si_review'}, 'Inventory main-plus-SI review scopes changed'
    assert sum(p['pages_read'] for p in main_si_reviews)==summary['formal_full_review_pages']
    assert len(main_only_reviews)==summary.get('formal_full_main_reviews_si_unverified',0)
    assert {r['id'] for r in main_only_reviews}=={p['source_group'] for p in inventory['per_paper'] if p['review_status']=='full_supplied_main_review_si_unverified'}, 'Inventory main-only review scopes changed'
    assert sum(p['pages_read'] for p in main_only_reviews)==summary.get('formal_full_main_only_review_pages',0)
    library = read(ROOT/'dist/data/library-index.json')
    assert len(library['papers'])==summary['local_paper_groups_indexed']
    assert library['summary']['sourceDocumentCount']==summary['local_document_files_indexed']
    assert summary['full_corpus_recipe_count'] is None and summary['full_corpus_distinct_synthesized_material_count'] is None
    output = ROOT/'dist/data/inventory-summary.json'
    output.write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    metrics = [('local_paper_groups_indexed','Local paper groups'),('local_document_files_indexed','Document files'),('direct_synthesis_target_systems','Verified synthesis systems'),('synthesis_route_variant_records','Reviewed routes / variants')]
    cards = '<div class="library-summary inventory-metrics">'+''.join('<div><strong>'+format(summary[k],',')+'</strong><span>'+label+'</span></div>' for k,label in metrics)+'</div>'
    body = '<div class="dataset-heading"><span class="eyebrow">LOCAL COLLECTION · VERIFIED INVENTORY</span><h1>Materials and synthesis inventory</h1><p>Counts from reviewed records, with unreviewed literature kept separate.</p></div>'+cards
    body += '<p class="coverage-note"><strong>The full collection’s material and recipe totals are not yet determined.</strong> Titles, extracted text and document counts cannot establish a synthesis recipe. Review proceeds one existing paper and its matching SI at a time. Materials without verified recipes remain blank; no new papers are downloaded.</p>'
    body += '<section class="record-section"><h2>What is counted</h2><div class="table-scroll"><table class="reagent-table"><thead><tr><th>Category</th><th>Count</th><th>Meaning</th></tr></thead><tbody>'
    rows = [('Synthesis routes and condition variants',summary['synthesis_route_variant_records'],'Source-reviewed protocol records; not necessarily complete laboratory SOPs or independent experiments.'),('Contextual controls and variants',summary['contextual_control_variant_records'],'Kept distinct from the published synthesis routes.'),('Supporting procedures',summary['shared_preparation_workup_characterization_assay_procedures'],'Precursor preparation, workup, characterization and assays.'),('Contextual observations',summary.get('contextual_observation_records',0),'Characterization of an earlier or incompletely specified preparation; not a reconstructed synthesis.'),('Published PbS benchmark rows',summary['published_benchmark_rows'],'Numeric rows from one study, counted separately from reconstructed recipes.'),('Canonical records in total',summary['canonical_records'],'The five record categories above; not a recipe or experiment count.'),('Material / component pages',summary['public_material_hubs'],str(summary['direct_synthesis_target_systems'])+' direct synthesis systems and '+str(summary['component_only_hubs'])+' component-only hubs; shared records are not duplicated.'),('Complete supplied main + SI reviews',summary['formal_full_main_and_matched_si_reviews'],str(summary['formal_full_review_pages'])+' pages across '+str(summary['formal_full_main_and_matched_si_reviews'])+' sources. Other review scopes remain separate.'),('Paper groups without canonical records',summary['local_groups_without_canonical_records'],'Awaiting recipe verification; recipe count is unknown, not zero.')]
    rows.insert(-1,('Complete supplied main reviews; SI unverified',summary.get('formal_full_main_reviews_si_unverified',0),str(summary.get('formal_full_main_only_review_pages',0))+' main-article pages. No claim of SI review or absence.'))
    body += ''.join('<tr><td>'+esc(a)+'</td><td>'+format(b,',')+'</td><td>'+esc(c)+'</td></tr>' for a,b,c in rows)+'</tbody></table></div></section>'
    body += '<section class="record-section"><h2>Verified material systems</h2><p>Counts below use direct synthesis targets. Component contributions are cross-links to the same records, not additional recipes.</p><div class="table-scroll"><table class="reagent-table"><thead><tr><th>Material system</th><th>Direct routes / variants</th><th>Component contributions</th><th>Controls</th></tr></thead><tbody>'
    for m in inventory['per_material']:
        if not m['public_hub_exists']: continue
        label = m['material_system']+(' · component only' if m['public_hub_component_only'] else '')
        body += '<tr><td>'+link(label,m['material_hub_url'])+'</td><td>'+str(m['direct_synthesis_route_variant_count'])+'</td><td>'+str(m['component_route_contribution_count'])+'</td><td>'+str(m['contextual_control_count'])+'</td></tr>'
    body += '</tbody></table></div><p>Fe–O retains unresolved phase and stoichiometry. Core/shell products remain distinct material systems. A shell’s properties are not relabeled as properties of an isolated component.</p></section>'
    statuses = {'full_supplied_main_and_matched_si_review':'Complete supplied main + matched SI','full_supplied_main_review_si_unverified':'Complete supplied main; SI unverified','legacy_main_article_review_si_unverified':'Main article reviewed; SI unverified','selected_recipe_and_figure_review':'Selected recipe and figures','published_numeric_benchmark':'Numeric benchmark'}
    body += '<section class="record-section"><h2>Paper-by-paper review inventory</h2><p>The remaining local paper groups are searchable in the '+link('source library','library.html')+'. Their synthesis counts remain unknown until reviewed.</p><div class="table-scroll"><table class="reagent-table inventory-papers"><thead><tr><th>Source and review scope</th><th>Routes</th><th>Controls</th><th>Procedures</th><th>Observations</th><th>Benchmark rows</th></tr></thead><tbody>'
    for p in inventory['per_paper']:
        paper = next((v for v in library['papers'] if v['doi'].lower()==p['doi'].lower()),None)
        url = p.get('paper_review_url') or ('paper.html?id='+paper['id'] if paper else 'dataset.html')
        cell = link(p['title'],url)+'<small>'+str(p['year'])+' · '+link(p['doi'],p['url'])+'</small><small>'+esc(statuses.get(p['review_status'],p['review_status'].replace('_',' ')))+'</small>'
        body += '<tr><td>'+cell+'</td>'+''.join('<td>'+str(p.get(k,0))+'</td>' for k in ['synthesis_route_variant_count','contextual_control_count','procedure_count','contextual_observation_count','benchmark_row_count'])+'</tr>'
    body += '</tbody></table></div></section><section class="record-section"><h2>Review and website standard</h2><p>Each material page follows the CdSe standard: precursors and stocks; illustrated synthesis protocol; final structures and original characterization; properties; and referenced chemical intuition. Missing source information stays explicit. Crystal references, diagrams and author interpretations do not become measured training labels.</p><p>'+link('Download the inventory JSON ↓','data/inventory-summary.json')+' · '+link('Open the synthesis dataset →','dataset.html')+'</p></section>'
    page = shell('Materials and synthesis inventory',body,'inventory.mjs').replace('class="dataset-main"','class="dataset-main inventory-main"')
    (ROOT/'dist/inventory.html').write_text(page,encoding='utf-8',newline='\n')
    # Generated homepage summary is replaced, never accumulated on rebuild.
    home = ROOT/'dist/index.html';text=home.read_text(encoding='utf-8')
    text=re.sub(r'<!--inventory-summary-start-->.*?<!--inventory-summary-end-->','',text,flags=re.S)
    snippet='<!--inventory-summary-start--><section class="inventory-overview" aria-label="Reviewed collection summary">'+cards+'<p>'+link('Materials and recipes: view the reviewed inventory →','inventory.html')+'</p></section><!--inventory-summary-end-->'
    text=text.replace('<div class="element-controls">',snippet+'<div class="element-controls">',1)
    home.write_text(text,encoding='utf-8',newline='\n')
    print(f"Inventory reconciled: {summary['local_paper_groups_indexed']:,} paper groups; {summary['direct_synthesis_target_systems']} direct systems; {summary['synthesis_route_variant_records']} routes; unknown full-corpus totals preserved.")

if __name__=='__main__': main()
