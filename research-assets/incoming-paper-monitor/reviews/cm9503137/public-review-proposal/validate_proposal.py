"""Private source-proposal structural and semantic-boundary checks."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ptr(v,p):
    for x in p.split('/')[1:]:v=v[int(x)] if isinstance(v,list) else v[x.replace('~1','/').replace('~0','~')]
    return v
def main():
    l=read(B/'danek1996.json');c=read(B/'source-item-coverage.json');a=read(B.parent/'source-audit.json');checks=[]
    def check(name,ok):checks.append({'name':name,'passed':bool(ok)})
    items={i['id']:i for s in l['reader_sections'] for i in s['items']}
    assets={i['id']:i for k in ['figures','tables','equations'] for i in l[k]}
    check('Eight main pages, no SI claim',len(l['documents'])==1 and l['documents'][0]['role']=='main' and l['documents'][0]['page_count']==8 and l['review_scope']=='supplied_main_only_si_unverified')
    check('No review/training/publication promotion',l['source_review_promoted'] is False and l['training_eligible'] is False and l['publication_status']=='private_proposal_not_published')
    check('66 reader items and79 reader/asset units',len(items)==66 and len(c['reader_units'])==79)
    check('121 scientific source units mapped',len(c['source_audit_unit_map'])==121)
    for u in c['source_audit_unit_map']:
        check('Audit pointer '+u['source_audit_pointer'],bool(ptr(a,u['source_audit_pointer'])) and all(bool(ptr(l,p)) for p in u['public_targets']))
    for u in c['reader_units']:check('Reader pointer '+u['source_item_id'],bool(ptr(l,u['target'])))
    rids={v['record_ids'][0] for v in l['recipe_inventory']}
    check('12 exact typed proposed records',len(rids)==12 and all(read(B.parent/'canonical-drafts'/f'{v["record_ids"][0]}.json')['record_type']==v['record_type'] for v in l['recipe_inventory']))
    for i in items.values():
        check(i['id']+' evidence and canonical joins',all(e['source_id']=='danek1996' and 1<=e['pdf_page']<=8 for e in i['evidence']) and all(x['record_id'] in rids for x in i['canonical_links']))
        check(i['id']+' not automatic training label',i['training_eligible'] is False)
    check('18 numbered references',sorted(int(k.split('-')[1]) for k in items if k.startswith('reference-'))==list(range(1,19)))
    check('References citation-only',all(x['import_experimental_evidence'] is False and x['cited_work_independently_reviewed_in_this_task'] is False for x in l['referenced_methods']))
    check('11 figures, 1 embedded table, 1 unnumbered reaction',len(l['figures'])==11 and len(l['tables'])==1 and len(l['equations'])==1 and l['tables'][0]['parent_id']=='figure-1')
    check('Table rows and uncertainty conflict preserved',[(r['sample'],r['size_nm'],r['relative_spread_percent']) for r in l['tables'][0]['structured_rows']]==[('a',4.0,12),('b',4.4,11),('c',5.0,13),('d',6.8,13)] and '10%' in items['figure1-size-series']['text'] and '12%' in items['figure1-size-series']['text'])
    check('Thermodynamic reaction not synthetic reaction','not the actual' in ' '.join(l['equations'][0]['notes']) and not l['equations'][0]['sample_links'])
    check('0.4 and4.0 film cohorts separate',assets['figure-7']['cohort_keys']==['films-figure7-8'] and assets['figure-10']['cohort_keys']==['film-figure10'] and '0.4' in items['film-variant-assignments']['text'] and '4.0' in items['coated-film-ple']['text'])
    check('High-temperature film conditions not collapsed','250 °C' in items['film-variant-assignments']['text'] and '270 °C' in items['film-variant-assignments']['text'])
    check('Annealing conflict not normalized','400 °C' in items['source-conflicts']['text'] and '450 °C' in items['source-conflicts']['text'] and '30 min' in items['comparative-experiments']['text'])
    check('Solution and film yields separate',assets['figure-5']['cohort_keys']==['solution-optics'] and assets['figure-11']['cohort_keys']==['films-figure11'] and 'not an absolute quantum-yield percentage' in items['film-coverage-yield']['text'])
    check('AES ratio and shell model retained','4.8' in items['surface-bulk-ratio']['text'] and '7.0' in items['surface-bulk-ratio']['text'] and 'not a resolved TEM shell thickness' in items['surface-bulk-ratio']['text'])
    check('Embedded thermal exposure not total deposition duration','5–60 min' in items['film-10k']['text'] and 'not a specified common deposition time' in items['film-10k']['text'])
    check('Unknown feed loading stays unknown','absolute precursor amounts' in items['feed-stock']['text'] and 'not specified' in items['feed-stock']['text'])
    check('Upstream cited procedures remain partial','partial supporting procedure' in items['seed-route']['text'])
    check('Source printed degassing order preserved','thaw–pump–freeze' in items['electrospray-preparation']['text'])
    check('19 distinct cohort keys',len(l['cohort_inventory'])==19 and len({x['key'] for x in l['cohort_inventory']})==19)
    for key,asset in assets.items():
        path=B.parent/'crop-assets'/Path(asset['public_asset']).name
        check(key+' asset hash and exclusion',sha(path)==asset['public_asset_sha256'] and asset['training_eligible'] is False)
    failures=[x for x in checks if not x['passed']]
    result={'status':'passed_private_proposal_checks' if not failures else 'failed','checked_utc':datetime.now(timezone.utc).isoformat(),'checks_passed':len(checks)-len(failures),'check_count':len(checks),'failures':failures,'scope':'Structural pointers, byte provenance and selected semantic boundaries only; canonical-science-to-reader and browser/publication acceptance remain separate.','proposal_sha256':sha(B/'danek1996.json'),'coverage_sha256':sha(B/'source-item-coverage.json'),'checks':checks}
    (B/'proposal-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['status','checks_passed','check_count','failures','proposal_sha256']}))
    return bool(failures)
if __name__=='__main__':raise SystemExit(main())
