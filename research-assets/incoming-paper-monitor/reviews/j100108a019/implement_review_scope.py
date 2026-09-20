"""One-time explicit-scope migration and reader-label changes; no new review claims."""
import json
from pathlib import Path

ROOT = Path(r'[local path redacted]')
inventory = json.loads((ROOT/'data/inventory-summary.json').read_text(encoding='utf-8'))
ids = {p['source_group'] for p in inventory['per_paper']
       if p['review_status']=='full_supplied_main_and_matched_si_review'}
assert ids == {'feld2019','fu2007','nakonechnyi2017','saha2019','stowell2005'}
for pid in sorted(ids):
    path = ROOT/'data/paper-reviews'/f'{pid}.json'
    review = json.loads(path.read_text(encoding='utf-8'))
    assert {d['role'] for d in review['documents']} == {'main','si'}
    assert review.get('review_scope') in (None,'supplied_main_and_matched_si')
    review['review_scope'] = 'supplied_main_and_matched_si'
    path.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def replace(relative, old, new):
    path = ROOT/relative
    text = path.read_text(encoding='utf-8')
    if old not in text:
        assert new in text, (relative, old[:90])
        return
    assert text.count(old)==1, (relative,old[:90])
    path.write_text(text.replace(old,new),encoding='utf-8',newline='\n')

replace('scripts/build_reader_views.py',
        '<option value="full_documents_reviewed">Full main + SI reviewed</option>',
        '<option value="full_documents_reviewed">Full main + matched SI reviewed</option><option value="main_only_reviewed">Full main reviewed · SI unverified</option>')
replace('scripts/build_reader_views.py',
        'PAPER AND SUPPORTING INFORMATION', 'SOURCE DOCUMENT REVIEW')
replace('dist/library-app.mjs',
        "p.reviewStatus==='full_documents_reviewed'?'Full main + SI reviewed':",
        "p.fullDocumentReview?.label|| (p.reviewStatus==='main_only_reviewed'?'Full main reviewed · SI unverified':p.reviewStatus==='full_documents_reviewed'?'Full main + matched SI reviewed':")
replace('dist/library-app.mjs',
        "'Indexed · detailed review pending','atlas-status'",
        "'Indexed · detailed review pending'),'atlas-status'")
replace('dist/library-app.mjs',
        "const fully=papers.filter(p=>p.fullDocumentReview);$('full-review-state').textContent=fully.length+' papers have complete supplied main/SI reading and visual review, covering '+fully.reduce((n,p)=>n+p.fullDocumentReview.pages,0)+' pages. Remaining papers still require full-document review; source omissions and unresolved links remain visible.';",
        "const fully=papers.filter(p=>p.fullDocumentReview),matched=fully.filter(p=>p.fullDocumentReview.scope==='supplied_main_and_matched_si'),mainOnly=fully.filter(p=>p.fullDocumentReview.scope==='supplied_main_only_si_unverified');$('full-review-state').textContent=matched.length+' papers have complete supplied main + matched SI review ('+matched.reduce((n,p)=>n+p.fullDocumentReview.pages,0)+' pages). '+mainOnly.length+' have complete supplied-main review with SI unverified ('+mainOnly.reduce((n,p)=>n+p.fullDocumentReview.pages,0)+' pages). Remaining papers still require full-document review; source omissions and unresolved links remain visible.';")
replace('dist/paper-app.mjs',
        "p.fullDocumentReview?'Full supplied main article and SI read and visually reviewed; experimental omissions remain explicit.':",
        "p.fullDocumentReview?(p.fullDocumentReview.label||'Supplied-document review')+'. Experimental omissions remain explicit.':")
replace('dist/material-hub.mjs',
        "p.reviewStatus==='selected_recipes_reviewed'?'Selected recipe contribution reviewed':",
        "p.fullDocumentReview?.label||(p.reviewStatus==='selected_recipes_reviewed'?'Selected recipe contribution reviewed':")
replace('dist/material-hub.mjs',
        "'Indexed literature · recipe contribution unverified','atlas-status'",
        "'Indexed literature · recipe contribution unverified'),'atlas-status'")
replace('dist/material-hub.mjs',
        "'Full main + SI review · original figures →'",
        "(p.fullDocumentReview.label||'Source document review')+' · original figures →'")
replace('dist/material-guide.mjs',
        "'Complete main/SI review, tables and source conflicts →'",
        "(c.review_scope_label||'Supplied-document review')+' · tables and source conflicts →'")
replace('dist/material-guide.mjs',
        "'Primary paper and supplements ↗'", "'Primary paper ↗'")
replace('scripts/build_inventory.py',
        "'10 direct synthesis systems and 3 component-only hubs; shared records are not duplicated.'",
        "str(summary['direct_synthesis_target_systems'])+' direct synthesis systems and '+str(summary['component_only_hubs'])+' component-only hubs; shared records are not duplicated.'")
replace('scripts/build_inventory.py',
        "'74 pages across five sources. Other review scopes remain separate.'",
        "str(summary['formal_full_review_pages'])+' pages across '+str(summary['formal_full_main_and_matched_si_reviews'])+' sources. Other review scopes remain separate.'")
replace('scripts/build_inventory.py',
        "    body += ''.join('<tr><td>'+esc(a)",
        "    rows.insert(-1,('Complete supplied main reviews; SI unverified',summary.get('formal_full_main_reviews_si_unverified',0),str(summary.get('formal_full_main_only_review_pages',0))+' main-article pages. No claim of SI review or absence.'))\n    body += ''.join('<tr><td>'+esc(a)")
print('Explicit review scopes and reader labels updated; no records promoted or published.')
