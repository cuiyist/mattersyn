"""Bounded read-only audit of Heath1996 canonical records and reader joins.

Site and source documents are read-only. Only this private folder receives output.
This does not repeat the six-page scientific audit or replace browser/publication QA.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import copy, hashlib, html, json, re, sys
sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
REVIEW = OUT.parent
SITE = REVIEW.parents[3] / 'recipe-atlas'
sys.path.insert(0, str(SITE / 'scripts'))
from dataset_lib import validate_record, eligibility, training_view, build_groups, digest, fmt
from build_paper_reviews import validate as validate_review

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def plain(s): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()
def pointer(obj, path):
    for part in path.split('/')[1:]:
        key=part.replace('~1','/').replace('~0','~')
        obj=obj[int(key)] if isinstance(obj,list) else obj[key]
    return obj

def main():
    checks=[]; findings=[]; notes=[]; hashes={}
    def check(name, condition, detail=''):
        checks.append({'name':name,'passed':bool(condition),'detail':detail})
        if not condition:findings.append({'check':name,'detail':detail})
    def bind(path):
        hashes[str(path.relative_to(SITE)) if path.is_relative_to(SITE) else str(path.relative_to(REVIEW))]=sha(path)
    ids=['heath-1996-ge-100nm-wells','heath-1996-ge-150nm-wells','heath-1996-ge-characterization','heath-1996-ge-unpatterned-growth-context']
    routes=ids[:2]; char=ids[2]; pilot=ids[3]
    records={rid:read(SITE/'data/records'/f'{rid}.json') for rid in ids}
    ledger=read(SITE/'data/paper-reviews/heath1996.json')
    oldledger=read(REVIEW/'public-review-proposal/heath1996.json')
    science_audit=read(REVIEW/'canonical-records-audit.json')
    review_audit=read(REVIEW/'source-audit.json')
    coverage=read(REVIEW/'public-review-proposal/source-item-coverage.json')
    manifest=read(SITE/'dist/data/dataset-manifest.json')
    validation=read(SITE/'dist/data/validation-report.json')
    manifest_records={r['record_id']:r for r in manifest['records']}
    all_records=[read(p) for p in sorted((SITE/'data/records').glob('*.json'))]
    groups=build_groups(all_records)
    items={i['id']:i for sec in ledger['reader_sections'] for i in sec['items']}
    olditems={i['id']:i for sec in oldledger['reader_sections'] for i in sec['items']}
    figures={f['id']:f for f in ledger['figures']}
    canonical_deltas={}
    html_text={}
    measurement_links=[]

    check('prior canonical scientific audit passed',science_audit['status']=='passed_bounded_scientific_draft_audit' and not science_audit['outstanding_findings'])
    for rid,r in records.items():
        src=SITE/'data/records'/f'{rid}.json';built=SITE/'dist/data/records'/f'{rid}.json';page=SITE/'dist/records'/f'{rid}.html'
        draftpath=REVIEW/'canonical-drafts'/f'{rid}.json';draft=read(draftpath)
        for p in [src,built,page,draftpath]:bind(p)
        check(rid+' audited draft hash',sha(draftpath)==science_audit['reviewed_hashes'][draftpath.name])
        errs=validate_record(r)
        check(rid+' schema and graph',not errs,repr(errs))
        check(rid+' generated JSON exact canonical bytes',src.read_bytes()==built.read_bytes())
        delta=[k for k in set(r)|set(draft) if r.get(k)!=draft.get(k)]
        canonical_deltas[rid]=delta
        check(rid+' audited science unchanged',set(delta)<= {'sources','quality'},repr(delta))
        check(rid+' source promotion scope',r['quality']['review_status']=='source_reviewed' and r['sources'][0]['id']=='heath1996')
        check(rid+' dataset manifest integrity',manifest_records[rid]['record_sha256']==digest(r))
        text=plain(page.read_text(encoding='utf-8'));html_text[rid]=text
        check(rid+' main-only label on record page','SI not located or verified' in text)
        check(rid+' source review link','paper-review.html?id=heath1996' in page.read_text(encoding='utf-8'))
        check(rid+' measured atomic structure absent',not r['structure_assets'] and 'No sample-resolved atomic coordinates' in text)
        check(rid+' manifest eligibility',manifest_records[rid]['eligibility']==eligibility(r))
        expected={'precursor_selection','partial_protocol'} if rid in routes else set()
        check(rid+' exact requested training tasks',set(r['quality']['requested_tasks'])==expected)
        actual={k for k,v in eligibility(r).items() if v['eligible']}
        check(rid+' actual training tasks',actual==expected,repr(actual))
        rows=[plain(row) for row in re.findall(r'<tr>(.*?)</tr>',page.read_text(encoding='utf-8'),re.S)]
        check(rid+' measurement rows present',sum(1 for row in rows if any(m['property'].replace('_',' ') in row for m in r['measurements']))==len(r['measurements']))
        for m in r['measurements']:
            check(rid+'/'+m['id']+' rendered value/sample',any(m['property'].replace('_',' ') in row and plain(fmt(m['value'])) in row and m['sample_id'] in row for row in rows))
            check(rid+'/'+m['id']+' sample resolves',m['sample_id'] in {p['sample_id'] for p in r['products']})
            if rid==pilot:target='unpatterned-comparison'
            elif rid==char:target='reported-spectroscopic-checks'
            elif m['id']=='oxide-thickness':target='substrate-and-mask'
            elif m['id'] in ['template-opening','template-depth']:target='rie-templates'
            elif rid==routes[0]:target='100nm-size-bounds' if m['sample_id'] in ['fig6-dot','second-dot'] else '100nm-imaged-cohort'
            else:target='150nm-outcomes' if m['id']=='islands-per-well' else '150nm-statistics'
            measurement_links.append({'record_id':rid,'measurement_id':m['id'],'sample_id':m['sample_id'],'reader_item_id':target,'source_evidence':m['evidence']})
            check(rid+'/'+m['id']+' reader evidence link',target in items and rid in [x['record_id'] for x in items[target]['canonical_links']])
        for task in expected:
            view=training_view(r,task)
            check(rid+'/'+task+' no outcome inputs',set(view['input'])=={'composition','method'})
            if task=='precursor_selection':
                check(rid+' germane metalloid precursor exported',view['output']['precursors']==[{'name':'Germane','formula':'GeH4','role':'metalloid_precursor'}])
            else:
                check(rid+' partial protocol preserves gaps',view['output']['missing_fields']==r['quality']['missing_fields'] and bool(r['quality']['missing_fields']))
                check(rid+' partial protocol excludes characterization operations',all(x['stage']!='characterization' for x in view['output']['operations']))

    check('23 distinct measurement entries',sum(len(r['measurements']) for r in records.values())==23 and len(measurement_links)==23)
    check('4 record types preserved',Counter(r['record_type'] for r in records.values())==Counter({'protocol_variant':2,'procedure':1,'observation':1}))
    check('one Heath source group and evaluation split',{r['lineage']['source_group'] for r in records.values()}=={'heath1996'} and len({groups[rid] for rid in ids})==1 and len({manifest_records[rid]['split'] for rid in ids})==1)
    check('all corpus records 172 and source groups 12',len(all_records)==172 and len(set(groups.values()))==12 and manifest['record_count']==172 and manifest['group_count']==12)
    eligible_totals={task:sum(eligibility(r)[task]['eligible'] for r in all_records) for task in eligibility(all_records[0])}
    check('actual eligibility totals and validation agree',eligible_totals==validation['eligible_by_task'],repr(eligible_totals))
    check('focused precursor gate yields 37 and partial protocol 53',eligible_totals['precursor_selection']==37 and eligible_totals['partial_protocol']==53)
    check('forbidden Heath tasks disabled',all(not eligibility(r)[t]['eligible'] for r in records.values() for t in ['size_conditioned_recipe','exact_structure_recipe','success_prediction','optical_outcome']))
    for rid in routes:
        grow=next(o for o in records[rid]['operations'] if o['id']=='grow')
        q=grow['parameters']
        check(rid+' shared deposition quantities',q['stock_gas_flow']['value']==90 and q['stock_gas_flow']['unit']=='sccm' and q['deposition_pressure']['minimum']==1 and q['deposition_pressure']['maximum']==2 and q['deposition_pressure']['unit']=='mTorr' and q['growth_temperature']['value']==600 and q['exposure_duration']['value']==5)
    check('100 nm phase remains unassigned',next(p for p in records[routes[0]]['products'] if p['sample_id']=='ge-islands')['phase']['value'] is None)
    check('150 nm epitaxy source scoped','epitaxially' in next(p for p in records[routes[1]]['products'] if p['sample_id']=='ge-islands')['phase']['value'].lower())
    check('pilot no invented full protocol',records[pilot]['operations']==[] and all(p['recipe_link']!='explicit' for p in records[pilot]['products']))
    check('spectroscopy remains cohort context',all(m['sample_id']=='patterned-cohort' for m in records[char]['measurements']) and all(p['recipe_link']=='general_context' for p in records[char]['products']))
    check('Raman and NIR correctly typed',[(m['property'],m['value']['value']) for m in records[char]['measurements']]==[('raman_mode_wavenumber',301),('surface_state_absorption_wavenumber',5890)])

    errors=validate_review(ledger)
    check('public review structural validator',not errors,repr(errors))
    check('review main-only scope',ledger['review_scope']=='supplied_main_only_si_unverified' and ledger['supporting_information']['status']=='not_located_or_verified')
    check('six main pages, no SI inventory',sum(d['page_count'] for d in ledger['documents'])==6 and all(d['role']=='main' for d in ledger['documents']))
    check('all four records linked in review',{rid for e in ledger['recipe_inventory'] for rid in e['record_ids']}==set(ids))
    check('stale canonical audit gaps removed',not any('Canonical source-join audit and reader integration remain pending' in gap for e in ledger['recipe_inventory'] for gap in e.get('gaps',[])))
    check('44 reader items, six figures, three equations, no tables',len(items)==44 and len(ledger['figures'])==6 and len(ledger['equations'])==3 and not ledger['tables'])
    check('17 reference entries retained',len([k for k in items if re.fullmatch(r'reference-\d+',k)])==17)
    check('89 audit units, 53 reader/asset units',len(coverage['source_audit_unit_map'])==89 and len(coverage['reader_units'])==53)
    for unit in coverage['source_audit_unit_map']:
        try:
            pointer(review_audit,unit['source_audit_pointer'])
            [pointer(ledger,t) for t in unit['public_targets']]
            ok=True
        except (KeyError,IndexError,ValueError):ok=False
        check('source coverage '+unit['source_audit_pointer'],ok)
    for unit in coverage['reader_units']:
        try:ok=bool(pointer(ledger,unit['target']))
        except (KeyError,IndexError,ValueError):ok=False
        check('reader target '+unit['source_item_id'],ok)
    for key,item in items.items():
        # Root changed provenance wording from pending to reviewed, not the science.
        check(key+' source content unchanged',{k:v for k,v in item.items() if k!='canonical_links'}=={k:v for k,v in olditems[key].items() if k!='canonical_links'})
        check(key+' source links resolve',all(e['source_id']=='heath1996' for e in item['evidence']) and all(l['record_id'] in ids and pointer(records[l['record_id']],l.get('json_pointer','')) for l in item['canonical_links']))
        check(key+' not an automatic training label',item['training_eligible'] is False)
    assets=ledger['figures']+ledger['equations']
    crop_manifest=read(REVIEW/'crop-assets/manifest.json')
    original={x['id']:x for x in crop_manifest['items']}
    for item in assets:
        path=SITE/'dist'/item['public_asset'];bind(path)
        check(item['id']+' original crop hash',sha(path)==item['public_asset_sha256']==original[item['id']]['sha256'])
        check(item['id']+' not training label',item['training_eligible'] is False)
    check('Figure 2 remains ambiguous and unassigned',figures['figure-2']['sample_links']==[char] and figures['figure-2']['formulation_labels']==[] and '100' in figures['figure-2']['sample_scope'] and '150' in figures['figure-2']['sample_scope'])
    check('Figures 3-5 only 150 nm route and characterization',all(set(figures[f'figure-{i}']['sample_links'])=={routes[1],char} for i in [3,4,5]))
    check('Figure 6 only 100 nm route and characterization',set(figures['figure-6']['sample_links'])=={routes[0],char})
    expected_visible={routes[0]:['figure-1','figure-6'],routes[1]:['figure-1','figure-3','figure-4','figure-5'],char:[f'figure-{i}' for i in range(1,7)],pilot:[]}
    for rid in ids:
        scope=ledger['record_formulation_labels'][rid]
        visible=[f['id'] for f in ledger['figures'] if rid in f['sample_links'] or set(scope)&set(f['formulation_labels'])]
        check(rid+' selected figure scope',visible==expected_visible[rid],repr(visible))
    render=(SITE/'dist/paper-review.mjs').read_text(encoding='utf-8')
    check('full review figure renderer exposes scope, quantitative context, locators',all("'"+k+"'" in render for k in ['sample_scope','quantitative_context','source_locators']))
    check('characterization reader_item_ids rendering supported','reader_item_ids' in render)
    hub_counts={}
    for slug,formula in [('ge-si-d31843','Ge/Si'),('ge-954edb','Ge'),('si-243a7b','Si')]:
        p=SITE/'dist/data/materials'/f'{slug}.json';bind(p);hub=read(p)
        listed={r['record_id'] for r in hub['evidence_records']};rs=set(hub['record_ids'])
        check(formula+' all four scoped evidence records',set(ids)<=listed)
        check(formula+' only two Heath synthesis routes',rs & set(ids)==set(routes))
        check(formula+' scoped evidence preserves record types',all(e['record_type']==records[e['record_id']]['record_type'] for e in hub['evidence_records'] if e['record_id'] in ids))
        check(formula+' main-only paper label',next(p for p in hub['papers'] if p['doi']=='10.1021/jp951903v')['fullDocumentReview']['scope']=='supplied_main_only_si_unverified')
        check(formula+' direct vs component correctly classified',hub['component_only']==(formula!='Ge/Si'))
        check(formula+' direct record membership',set(hub['direct_record_ids'])==(set(routes) if formula=='Ge/Si' else set()))
        check(formula+' explicit scope note',bool(hub['evidence_scope_notes']))
        hub_counts[formula]={'route_records':len(hub['record_ids']),'evidence_records':len(hub['evidence_records']),'paper_count':hub['paper_count'],'component_only':hub['component_only']}
    check('Si remains shared component with five routes/two papers',hub_counts['Si']['route_records']==5 and hub_counts['Si']['paper_count']==2)
    for path in [SITE/'data/paper-reviews/heath1996.json',SITE/'dist/data/paper-reviews/heath1996.json',SITE/'dist/data/paper-review-index.json',SITE/'dist/data/materials-index.json',SITE/'dist/data/dataset-manifest.json',SITE/'dist/data/validation-report.json',SITE/'scripts/dataset_lib.py',SITE/'scripts/build_paper_reviews.py',SITE/'dist/paper-review.mjs',SITE/'dist/material-guide.mjs',SITE/'dist/material-hub.mjs',SITE/'dist/source-evidence.mjs',SITE/'dist/illustrated-record.mjs',REVIEW/'canonical-records-audit.json',REVIEW/'source-audit.json',REVIEW/'public-review-proposal/source-item-coverage.json']:
        bind(path)
    built_review=read(SITE/'dist/data/paper-reviews/heath1996.json');built_review.pop('review_scope_label',None)
    check('generated review equals canonical ledger plus scope label',built_review==ledger)
    notes=[
        'This is a bounded canonical-to-reader data, generated HTML, source-join and renderer-contract audit, not a repeated six-page source reading or independent browser visual acceptance.',
        'All four Heath records remain in one source/evaluation group and split. Two template variants are not two independent exposure runs. Characterization and unpatterned context are not additional synthesis routes.',
        'The existing supplied-main scientific and canonical audits support the records; matching SI remains not located or verified. Browser validation, deployment, and final queue completion remain root responsibilities.',
        'The root normalized germane to metalloid_precursor and extended both eligibility and export allowlists; this bounded audit confirms GeH4 is actually exported for both routes, rather than relying on requested task names.',
        'Figure/sample content remains original and source-scoped: Figure 2 is unresolved, Figure 5 uses model pseudo-time, Figure 6 gives individual-object bounds, and Raman/NIR values remain shared-cohort prose observations.'
    ]
    result={'status':'passed_bounded_canonical_to_reader_audit' if not findings else 'findings','generated_at_utc':datetime.now(timezone.utc).isoformat(),'source_id':'heath1996','doi':'10.1021/jp951903v','scope':'Current local integrated reader dataset; no publication claim','checks_passed':sum(c['passed'] for c in checks),'check_count':len(checks),'findings':findings,'canonical_deltas_vs_audited_drafts':canonical_deltas,'record_count':4,'measurement_count':23,'reader_item_count':44,'source_audit_units':89,'reader_asset_units':53,'figure_count':6,'equation_count':3,'reference_count':17,'evaluation_group':groups[ids[0]],'evaluation_split':manifest_records[ids[0]]['split'],'source_group_count':len(set(groups.values())),'eligible_by_task':eligible_totals,'hub_counts':hub_counts,'measurement_to_reader_links':measurement_links,'checks':checks,'notes':notes,'artifact_sha256':hashes}
    (OUT/'canonical-to-reader-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report=['# Heath1996 bounded canonical-to-reader audit','',f"Status: **{result['status']}** — {result['checks_passed']}/{result['check_count']} checks passed.",'',f"Snapshot: {result['generated_at_utc']}",'','Four canonical records, 23 measurements, 44 reader items, 89 source-audit units, 53 reader/asset units, six figures, three equations and 17 numbered references were checked against the current local reader artifacts.','',f"All four records remain in {result['evaluation_group']} / {result['evaluation_split']}; the full dataset has 12 evaluation groups. Only the two template variants qualify for precursor selection and partial protocol. The global eligible totals are {eligible_totals}.",'','The inventory proposal is at `../inventory-proposal/inventory-summary.json`; its separate validator reconciles 172 records, 37 routes, 9 controls, 24 procedures, 2 observations, 100 benchmark rows, 17 hubs (12 direct / 5 component) and the unchanged 7,373-document legacy corpus.','']
    report += ['- '+n for n in notes]
    report += ['','## Findings','']+[('- '+json.dumps(f,ensure_ascii=False)) for f in findings] if findings else report+['','No unresolved findings in this bounded static/data audit. Browser appearance, interaction and publication are separate gates.']
    (OUT/'canonical-to-reader-audit.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['status','checks_passed','check_count','record_count','measurement_count','evaluation_group','source_group_count','findings']},ensure_ascii=False))
    return bool(findings)

if __name__=='__main__':raise SystemExit(main())
