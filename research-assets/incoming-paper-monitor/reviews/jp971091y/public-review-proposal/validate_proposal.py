"""Private source-proposal boundary, link and original-byte verification."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ptr(v,p):
    for k in p.split('/')[1:]:v=v[int(k)] if isinstance(v,list) else v[k.replace('~1','/').replace('~0','~')]
    return v
def main():
    l=read(B/'dabbousi1997.json');cov=read(B/'source-item-coverage.json');items={x['id']:x for s in l['reader_sections'] for x in s['items']};checks=[]
    def check(name,ok):checks.append({'name':name,'passed':bool(ok)})
    check('13 main pages; SI unverified',len(l['documents'])==1 and l['documents'][0]['page_count']==13 and l['review_scope']=='supplied_main_only_si_unverified' and l['supporting_information']['status']=='not_located_or_verified')
    check('No automatic scientific/training/publication promotion',not l['source_review_promoted'] and not l['training_eligible'] and l['publication_status']=='private_proposal_not_published')
    records={v['record_ids'][0]:read(B.parent/'canonical-drafts'/f'{v["record_ids"][0]}.json') for v in l['recipe_inventory']}
    check('17 typed records;2 routes10 procedures5 observations',len(records)==17 and [sum(r['record_type']==t for r in records.values()) for t in ['literature_protocol','procedure','observation']]==[2,10,5])
    for v in l['recipe_inventory']:check(v['id']+' type',v['record_type']==records[v['record_ids'][0]]['record_type'])
    for k,x in items.items():
        check(k+' sourced and not auto-training',x['evidence'] and all(e['source_id']=='dabbousi1997' and 1<=e['pdf_page']<=13 for e in x['evidence']) and not x['training_eligible'])
        check(k+' record references',all(c['record_id'] in records for c in x['canonical_links']))
        for z in x['sample_scope'].get('canonical_sample_links',[]):check(k+'/'+z['sample_id']+' sample join',ptr(records[z['record_id']],z['json_pointer'])['sample_id']==z['sample_id'])
    for u in cov['reader_units']:check(u['source_item_id']+' source item pointer',ptr(l,u['target'])['id']==u['source_item_id'])
    check('Forty references/notes; three direct notes',len(l['referenced_methods'])==40 and [r['reference_number'] for r in l['referenced_methods'] if r['direct_source_note_reviewed']]==[22,26,38])
    check('No imported experiments from references',all(not r['import_experimental_evidence'] and not r['cited_work_independently_reviewed_in_this_task'] for r in l['referenced_methods']))
    check('All25 original crops classified correctly',[len(l[k]) for k in ['figures','tables','equations','source_notes']]==[16,1,7,1] and sum(x['source_asset_type']=='equation' for x in l['equations'])==5)
    for category in ['figures','tables','equations','source_notes']:
        for a in l[category]:check(a['id']+' original hash and labels',sha(B.parent/'crop-assets'/Path(a['public_asset']).name)==a['public_asset_sha256'] and bool(a['sample_scope']) and bool(a['quantitative_context']) and not a['training_eligible'])
    orig=items['size-temperature-pairs']['original_assets'][0]
    check('Note22 reader link hash',sha(B.parent/'crop-assets'/Path(orig['public_asset']).name)==orig['sha256'] and orig['public_asset']==l['source_notes'][0]['public_asset'])
    table=l['tables'][0]['structured_rows']
    check('Table blank cells remain null',all(table[i][k] is None for i,k in [(0,'wds_measured_Zn_Cd'),(0,'polymer_saxs_calculated_Zn_Cd'),(0,'waxs_calculated_Zn_Cd'),(3,'polymer_saxs_fit_size_A'),(4,'polymer_saxs_relative_spread_percent')]))
    check('Table major axes and spread boundaries',[(r['tem_major_axis_A'],r['tem_relative_spread_percent']) for r in table]==[(39,8.2),(43,11),(47,10),(55,13),(72,19)])
    check('One source temperature family,six pairs',len(items['size-temperature-pairs']['facts'])==6 and 'seventh temperature' in items['size-temperature-pairs']['text'])
    check('Particle amount not CdSe stoichiometric amount','particle moles' in items['zns-charge']['text'] and 'not a reported amount of CdSe formula units' in items['zns-charge']['text'])
    check('Unknown shell precursor loading not invented','Absolute stock molarity and per-sample doses are not printed' in items['zns-feed-design']['text'])
    check('Addition window not inherited into CdS','5–10 min' in items['cds-feed']['text'] and 'do not replace' in items['cds-feed']['text'])
    check('CdS storage amount basis unresolved','no explicit mass/volume basis' in items['cds-addition-storage']['text'])
    check('Solution-SAXS cohort not main table',l['figures'][10]['cohort_keys']==['solution-saxs'] and l['tables'][0]['cohort_keys']==['coverage-main'])
    check('Solution ratio conflict explicit','5.6' in items['solution-saxs-cohort']['text'] and '5.3' in items['solution-saxs-cohort']['text'])
    check('SAXS spread/mean conflict explicit','0.12' in items['solution-saxs-fitting']['text'] and '0.11' in items['solution-saxs-fitting']['text'] and 'upper distribution rather than a mean' in items['solution-saxs-fitting']['text'])
    check('Figure14 model only and size conflict',not next(x for x in l['figures'] if x['id']=='figure-14')['sample_links'] and 'diameter' in items['zns-cds-confinement']['text'] and 'radius' in items['zns-cds-confinement']['text'])
    check('CdS size conflict all three reports',all(v in items['cds-optical-comparison']['text'] for v in ['33.5–35','~30','~16']))
    check('Fitting offsets not measurements','fitting parameters' in items['electronic-model-assumptions']['text'] and 'not experimentally measured offsets' in items['electronic-model-assumptions']['text'])
    check('Original grayscale preserved','grayscale' in items['six-dispersion-photograph']['text'] and 'do not synthetically recolor' in items['six-dispersion-photograph']['text'])
    check('No digitized intermediate yields','No exact yield is transcribed' in items['coverage-pl']['text'])
    check('All escape depths in direct note',all(v in items['escape-depths']['text'] for v in ['15 Å','10 Å','21 Å','23.7 Å','13.2 Å','31.2 Å','9.6 Å','26.8 Å','28.9 Å']))
    check('Printed Guinier convention retained','R_G²/5' in ' '.join(items['solution-saxs-fitting']['notes']))
    xps_claims=['xps-composition','auger-parameters','xps-intensity-model','xps-finite-size-correction']
    check('XPS claims never point to physical Table1 products',all(z['sample_id'].startswith('xps-') and z['sample_id'].endswith('-context') for k in xps_claims for z in items[k]['sample_scope']['canonical_sample_links']))
    check('Baseline repetition is not an independent experiment',all('without representing an independent replicate' in ' '.join(items[k]['notes']) and 'physical identity with the later exposure film is unresolved' in ' '.join(items[k]['notes']) for k in ['air-exposure-method','air-exposure-results','xps-composition']))
    ap=B.parent/'source-audit.json'
    if ap.exists():
        audit=read(ap)
        check('Independent source-audit unit map present',bool(cov['source_audit_unit_map']))
        for u in cov['source_audit_unit_map']:check('Audit '+u['source_audit_pointer'],bool(ptr(audit,u['source_audit_pointer'])) and all(bool(ptr(l,p)) for p in u['public_targets']))
    else:check('Independent source audit available',False)
    failures=[c for c in checks if not c['passed']]
    result={'status':'passed_private_proposal_checks' if not failures else 'findings','checked_utc':datetime.now(timezone.utc).isoformat(),'checks_passed':len(checks)-len(failures),'check_count':len(checks),'failures':failures,'scope':'Private reader links,scope boundaries and exact source bytes. Independent canonical audit and reader/publication acceptance remain separate.','proposal_sha256':sha(B/'dabbousi1997.json'),'coverage_sha256':sha(B/'source-item-coverage.json'),'checks':checks}
    (B/'proposal-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['status','checks_passed','check_count','failures','proposal_sha256']}))
    return bool(failures)
if __name__=='__main__':raise SystemExit(main())
