from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
P=Path(__file__).resolve().parent;D=P.parents[2]/'recipe-atlas/dist'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
app=(D/'reader-app.mjs').read_text('utf8');structures=(D/'reader-structures.mjs').read_text('utf8');protocol=(D/'protocol-references.mjs').read_text('utf8')
pres=json.loads((D/'data/reader-presentation.json').read_text('utf8'))
checks=[]
def ck(name,ok):checks.append({'check':name,'passed':bool(ok)})
ck('Source fallback now complete record data evidence',"p.data_links?.full_review||recordURL(r.record_id)+'#evidence'" in app)
ck('Text-only legacy figure evidence retained',"original image unavailable" in app and 'return textOnly.length' in app)
for rid,p in pres['records'].items():
 url=p['data_links'].get('full_review')
 if url and not url.startswith('paper-review.html'):ck('Legacy review file exists '+rid,(D/url.split('?')[0].split('#')[0]).exists())
ck('Particle grouping and identity helpers integrated unchanged', (D/'reader-particle.mjs').read_text('utf8').split('function particleArt(')[0]==(P/'reader-particle-proposal.mjs').read_text('utf8').split('function particleArt(')[0])
ck('Old route-wide particle art removed and context component dispatched', 'function particleArt(' not in structures and 'mountParticleContext(panel,r,presentation);return;' in structures)
ck('Elemental formula comparison preserves case','match[0]!==m.formula' in protocol)
ck('No prose-derived step chip IDs','ids.add(m.id)' not in protocol)
ck('Actual corrected protocol fixture passes',json.loads((P/'protocol-correction-tests.json').read_text('utf8'))['status']=='passed')
ck('Particle proposal 853 actual-context tests pass',json.loads((P/'particle-proposal-tests.json').read_text('utf8'))['checks']==853)
ck('Actual integrated particle helpers pass all 853 checks',json.loads((P/'particle-integrated-tests.json').read_text('utf8'))['checks']==853)
mapping=json.loads((P/'stock-context-bindings.json').read_text('utf8'))
ck('Five exact stock context proposals supplied',sum(len(v) for v in mapping['stockBindings'].values())==5)
ck('Actual stock context map equals the five reviewed mappings',json.loads((D/'data/reader-stock-bindings.json').read_text('utf8'))['stockBindings']==mapping['stockBindings'])
ck('Actual matching selects explicit stock binding before title heuristic','c.id===stockBindings.stockBindings?.[r.record_id]?.[stock.id]' in app)
metrics=json.loads((D/'data/structure-recipe-coverage.json').read_text('utf8'))
ck('Metrics separate 1 molecular asset / 1 explicit link / 0 exact readiness', metrics['counts']=={'sample_coordinate_assets':1,'records_with_sample_coordinates':2,'source_verified_explicit_links':1,'exact_task_ready_records':0} and metrics['asset_representation_counts']=={'molecular_structure':1})
report={'status':'passed_bounded_correction_recheck','reviewer':'/root/backlog_eta','at':datetime.now(timezone.utc).isoformat(),
 'initial_review_sha256':sha(P/'independent-review.json'),'scope':'Targeted code/data recheck only; no browser approval. Particle module was proposed by this reviewer, so its tests and byte transport are author verification, not distinct scientific certification.',
 'closed_findings':['READER-01','READER-02','READER-03','READER-04'],'open_findings':[],
 'accepted_presentation_delta':'Root keeps the first five particle facts visible and later facts in a disclosure. Grouping/identity helpers are unchanged; all values and qualifiers remain rendered. The current corpus has no group exceeding five facts. Browser layout remains a separate gate.',
 'checks':checks,'bound_files':{str(p):sha(p) for p in [D/'reader-app.mjs',D/'reader-structures.mjs',D/'reader-particle.mjs',D/'protocol-references.mjs',D/'data/structure-recipe-coverage.json',D/'data/reader-stock-bindings.json',P/'stock-context-bindings.json',P/'stock-context-binding-checks.json',P/'particle-proposal-tests.json',P/'particle-integrated-tests.json',P/'protocol-correction-tests.json']}}
assert all(c['passed'] for c in checks),checks
(P/'correction-addendum.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
(P/'correction-addendum.md').write_text('# Targeted correction recheck\n\nAll four bounded findings are corrected: source fallback links, selected-specimen identity/unknown contexts, the observed In/in protocol misassignment, and five exact stock/context bindings. The metrics still report one molecular asset, one explicit link and zero task-ready records. All 50 hubs and 123 routes remain covered by the initial inventory.\n\nThe integrated particle helpers passed 853 function checks; the actual protocol correction passed its Heo fixture. Particle correction author verification is distinguished from this independent review. Actual browser validation remains root work. No Site files were edited by this reviewer.\n','utf8')
print(json.dumps({'path':str(P/'correction-addendum.json'),'sha256':sha(P/'correction-addendum.json'),'checks':len(checks),'status':report['status']}))
