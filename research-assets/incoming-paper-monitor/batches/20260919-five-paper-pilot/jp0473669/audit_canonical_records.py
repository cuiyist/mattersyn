"""Independent audit of frozen Ribeiro canonical science; private outputs only."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib,json,sys
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent
S=Path(r'[local path redacted]')
sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record,eligibility,build_groups
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[];bound={}
def ck(label,ok):
    checks.append({'check':label,'passed':bool(ok)})
    assert ok,label
def bind(p):
    bound[str(Path(p))]=sha(p)
    return read(p) if str(p).endswith('.json') else None
def resolve(d,p):
    if p=='/':return d
    for k in p.strip('/').split('/'):
        k=k.replace('~1','/').replace('~0','~');d=d[int(k)] if isinstance(d,list) else d[k]
    return d
M=bind(B/'canonical-record-manifest.json');C=bind(B/'canonical-source-coverage.json')
IX=bind(B/'canonical-source-unit-index.json');D=bind(B/'source-facts.json');I=bind(B/'source-inventory.json')
A=bind(B/'source-scientific-audit.json');V=bind(B/'canonical-draft-validation.json')
bind(B/'build_canonical_drafts.py');bind(Path(__file__))
ck('frozen manifest exact',sha(B/'canonical-record-manifest.json')=='6d6a84fd9dec1e69345e8a4a90eedf4c4cf520d64e6561f18d294c024147b00a')
ck('source audit passed independently',A['status']=='passed' and A['independent_full_scientific_audit_performed'] and not A['open_findings'])
for n,h in A['author_file_hashes'].items():bind(B/n);ck('audited extraction hash '+n,sha(B/n)==h)
for p,h in M['source_pdf_hashes'].items():bind(p);ck('original main source '+p,sha(p)==h==D['source_sha256'])
for a in I['assets']:
    p=B/a['filename'];bind(p);ck('original crop '+a['id'],sha(p)==a['sha256']==A['asset_hashes'][a['id']])
for field,n in [('source_extraction_audit_sha256','source-scientific-audit.json'),('source_inventory_sha256','source-inventory.json'),('source_facts_sha256','source-facts.json'),('build_script_sha256','build_canonical_drafts.py')]:ck('manifest provenance '+field,M[field]==sha(B/n))
for field,n in [('dataset_validator_sha256','dataset_lib.py'),('schema_definition_sha256','schema_definition.py'),('record_helpers_sha256','record_helpers.py')]:bind(S/'scripts'/n);ck('same validator version '+field,M[field]==sha(S/'scripts'/n))
ck('coverage input hashes',C['source_facts_sha256']==sha(B/'source-facts.json') and C['source_inventory_sha256']==sha(B/'source-inventory.json') and C['source_units_sha256']==sha(B/'canonical-source-unit-index.json'))
R={}
for row in M['records']:
    r=bind(row['path']);rid=r['record_id'];R[rid]=r
    ck('canonical frozen hash '+rid,sha(row['path'])==row['sha256']==V['record_hashes'][rid])
    ck('schema semantics '+rid,not validate_record(r))
    ck('private and no task eligibility '+rid,r['quality']['review_status']=='imported_unreviewed' and r['quality']['requested_tasks']==[] and not any(x['eligible'] for x in eligibility(r).values()))
    ck('main-only and SI explicitly unverified '+rid,'SI existence remains unverified' in r['sources'][0]['si_status'] and r['quality']['missing_fields']==I['remaining_gaps'])
    ck('same source group and DOI '+rid,r['lineage']['source_group']=='ribeiro2004' and r['sources'][0]['doi']=='10.1021/jp0473669')
    ck('four source conflicts preserved '+rid,r['quality']['conflicts']==[x['description'] for x in I['evidence_conflicts']])
    ck('no atomic structures or invented physical batches '+rid,not r['structure_assets'] and all(p['batch_id'] is None for p in r['products']))
    ck('no measured-size target '+rid,r['intended_target']['size']['value'] is None and not any(m['property']=='diameter' for m in r['measurements']))
    ck('manifest inventories exact '+rid,row['operations']==[o['id'] for o in r['operations']] and row['samples']==[p['sample_id'] for p in r['products']] and row['measurements']==[m['id'] for m in r['measurements']])
F={x['id']:x for x in D['facts']}
ck('all 63 original facts mapped',len(C['facts'])==63 and {x['source_fact_id'] for x in C['facts']}==set(F))
statusmap={'reported_qualitative':'reported','cited_reference':'reported','cited_prior_work':'reported','author_model':'author_derived','author_interpretation':'author_derived'}
bounds={'stability':('maximum','months',False),'monitor-low':('maximum','h',False),'tem-n':('minimum','particles',False),'number-linear-scope':('maximum','mol/L',True)}
for row in C['facts']:
    f=F[row['source_fact_id']];key=f['id'].removeprefix('ribeiro2004-fact-')
    ck('original fact retained '+key,row['source_fact']==f and bool(row['canonical_bindings']))
    for link in row['canonical_bindings']:
        q=resolve(R[link['record_id']],link['pointer']);label=key+' '+link['record_id']+link['pointer'];v=f['value'];idx=link['source_array_index']
        ck('semantic status '+label,q['status']==statusmap.get(f['status'],f['status']))
        provenance=q.get('basis',q.get('note',''))
        ck('original scope/status/qualifier '+label,f['sample_scope'] in provenance and f['status'] in provenance and f['qualifier'] in q.get('qualifier',q.get('note','')))
        if isinstance(v,str):ck('categorical source value '+label,q['value']==v and 'unit' not in q)
        else:
            ck('approximation preserved '+label,q['approximate']==f['approximate'])
            if key=='water-ratio':ck('500:1 stays basis-unknown ratio '+label,v==[500,1] and q['value']==500 and 'One relative Sn2+ part' in q['basis'] and 'molar, mass and volume bases are all unreported' in q['basis'])
            elif key in bounds:
                side,unit,exclusive=bounds[key];ck('observation/bound meaning '+label,q['value'] is None and q[side]==v and q['unit']==unit and q.get(side+'_exclusive')==exclusive and q['minimum' if side=='maximum' else 'maximum'] is None)
            elif isinstance(v,list) and idx is None:ck('reported range '+label,q['value'] is None and [q['minimum'],q['maximum']]==v and q['unit']==(f['unit'] or 'pH'))
            else:ck('scalar and unit '+label,q['value']==(v[idx] if idx is not None else v) and q['unit']==(f['unit'] or 'pH') and q['minimum'] is None and q['maximum'] is None)
        ck('original evidence page retained '+label,all(any('Main PDF p. '+str(e['pdf_page'])+' ' in x['locator'] and x['source_id']=='ribeiro2004' for x in q['evidence']) for e in f['evidence']))
U={u['id']:u for u in IX['units']}
ck('101 unit identities all mapped',len(U)==101 and len(C['source_units'])==101 and {x['source_unit_id'] for x in C['source_units']}==set(U))
ck('index binds actual frozen inventory',IX['source_inventory_sha256']==sha(B/'source-inventory.json'))
for u in U.values():
    src=resolve(I,u['source_inventory_pointer'])
    if u['id']=='identity':src={k:src[k] for k in u['source_payload']}
    elif u['kind']=='protocol':src={k:v for k,v in src.items() if k!='steps'}
    ck('unit index actual source payload '+u['id'],src==u['source_payload'])
for row in C['source_units']:
    u=U[row['source_unit_id']];ck('unit has bindings '+u['id'],bool(row['canonical_bindings']))
    for link in row['canonical_bindings']:
        q=resolve(R[link['record_id']],link['pointer']);lab=u['id']+' '+link['record_id']+link['pointer']
        if u['kind']=='material':ck('material source identity '+lab,q['id']==u['source_payload']['id'] and q['name']==u['source_payload']['name'])
        elif u['kind']=='operation':ck('source procedure retained '+lab,q['description']==u['source_payload']['description'])
        else:ck('entire source context retained '+lab,q['value']==u['claim'] and q['evidence']==u['evidence'])
def r(k):return R['ribeiro-2004-'+k]
def o(k,oid):return next(x for x in r(k)['operations'] if x['id']==oid)
def m(k,mid):return next(x for x in r(k)['measurements'] if x['id']==mid)
ck('one route, five procedures and five contexts',Counter(x['record_type'] for x in R.values())=={'literature_protocol':1,'procedure':5,'observation':5})
groups=build_groups(list(R.values()));ck('all records one split group',len(set(groups.values()))==1)
ck('hydrolysis not a timed two-hour hold',o('hydrolysis','hydrolysis-hydrolyze')['parameters']['duration']['value'] is None and m('uv-visible','monitor-low-low-concentration-monitor')['value']['maximum']==2)
ck('stock is initial ethanolic concentration, not final colloid',r('hydrolysis')['stocks'][0]['concentrations']['initial_tin_concentration']['minimum']==0.0025 and 'not one stock' in r('hydrolysis')['stocks'][0]['scope'])
ck('acid-set treatment range and post-base pH distinct',o('ph-treatment','ph-treatment-acidify')['parameters']['treatment_pH_range']['minimum']==1.5 and o('ph-treatment','ph-treatment-redisperse')['parameters']['measurement_pH_after_base']['value'] is None)
ck('24h aging then TBAOH then 2min probe',o('ph-treatment','ph-treatment-age')['parameters']['duration']['value']==24 and o('ph-treatment','ph-treatment-redisperse')['depends_on']==['ph-treatment-age'] and o('ph-treatment','ph-treatment-sonicate')['parameters']['duration']['value']==2 and o('ph-treatment','ph-treatment-sonicate')['depends_on']==['ph-treatment-redisperse'])
ck('acid/base product states distinct',r('ph-treatment')['products'][0]['material_state_id']=='aged-treatment-series' and r('ph-treatment')['products'][1]['material_state_id']=='sonicated-optical-series')
ck('no base treatment borrowed by zeta or TEM',all(x['id']!='tbaoh-aqueous' for k in ['zeta-potential','microscopy'] for x in r(k)['materials']))
ck('IEP remains electrokinetic result',m('zeta-potential','isoelectric-zeta-series')['value']['value']==3.1 and m('zeta-potential','isoelectric-zeta-series')['value']['approximate'])
ck('200 particles lower bound not 200 replicates',o('microscopy','tem-acquisition')['parameters']['particle_count_lower_bound']['minimum']==200 and o('microscopy','tem-acquisition')['parameters']['particle_count_lower_bound']['value'] is None)
ck('grid drying does not isolate bulk powder',len(r('hydrolysis')['operations'])==3 and 'bulk-powder' in o('microscopy','tem-preparation-air-dry')['description'])
ck('SnOH4 only proposed context',not r('growth-model')['operations'] and r('growth-model')['materials'][0]['role']=='proposed_intermediate')
ck('no XRD or SAED acquisition invented',not any('xrd' in x['id'].lower() or 'saed' in x['id'].lower() for rec in R.values() for x in rec['operations']))
ck('prose cassiterite qualification retained','no original XRD trace' in r('hydrolysis')['products'][0]['phase']['note'])
ck('Equation4 uncertainty coefficient values exact',m('growth-model','number-fit-intercept-uncertainty')['value']['value']==0.14e18 and m('growth-model','number-fit-slope-uncertainty')['value']['value']==0.07e20)
ck('Equation4 uncertainty status and scope',all(m('growth-model',k)['value']['status']=='author_derived' and 'below 0.04' in m('growth-model',k)['conditions'] for k in ['number-fit-intercept-uncertainty','number-fit-slope-uncertainty']))
ck('source nucleation assumption chain retained','concentration-independent' in m('growth-model','supersaturation-assumptions-nucleus-model')['value']['value'] and m('growth-model','supersaturation-assumptions-nucleus-model')['value']['status']=='author_derived')
ck('prior 2-6nm reference range remains separate',m('source-context','prior-range-references')['sample_id']=='references' and 'cited_prior_work' in m('source-context','prior-range-references')['value']['basis'])
ck('no raw measured radii or coordinates manufactured',all(x['value']['status']!='measured' for rec in R.values() for x in rec['measurements']))
for n in [2,3,4,5]:bind(B/f'main-{n}.png');bind(B/f'main-{n:02d}.txt')
bind(B/'main-06.txt')
ck('frozen bound files remain unchanged',all(sha(p)==h for p,h in bound.items()))
counts={'records':len(R),'operations':sum(len(x['operations']) for x in R.values()),'measurement_and_context_entries':sum(len(x['measurements']) for x in R.values()),'material_slots':sum(len(x['materials']) for x in R.values()),'stock_contexts':sum(len(x['stocks']) for x in R.values()),'sample_and_context_ids':sum(len(x['products']) for x in R.values()),'source_facts':len(F),'fact_bindings':sum(len(x['canonical_bindings']) for x in C['facts']),'source_inventory_units':len(U),'unit_bindings':sum(len(x['canonical_bindings']) for x in C['source_units']),'original_assets':len(I['assets']),'checks':len(checks),'bound_files':len(bound)}
report={'schema':'mattersyn.independent-canonical-scientific-audit.v1','status':'passed_with_preserved_source_limits','source_id':'ribeiro2004','auditor':'/root/backlog_eta','audited_at':datetime.now(timezone.utc).isoformat(),'scope':'All 11 private canonical records, all operations and scientific facts/context mappings checked against the independently audited six-page main-source package. Targeted original main pages 2–5 visually reread, page6 conclusion reread. No SI or external cited articles inspected; no repeated full-source extraction claimed.','counts':counts,'checks':checks,'bound_files':bound,'record_hashes':{rid:sha(B/'canonical-drafts'/(rid+'.json')) for rid in R},'source_split_groups':groups,'findings':[],'corrections_required':[],'preserved_conflicts':[x['id'] for x in I['evidence_conflicts']],'remaining_limits':['Main-only scope; SI existence and matching remain unverified. Fuller cited procedures are not inspected.','Water/Sn ratio basis, doses and synthesis duration remain unknown; observation times are not recipe holds.','Acid-set treatment pH is distinct from unknown pH after TBAOH addition; optical redispersion is not borrowed by TEM/zeta methods.','Radii, scale bars, reference constants and optical/particle-number models retain distinct meanings; no new raw-curve digitization or experimental replicate counts.','Cassiterite is a source-reported XRD prose assignment. No XRD trace, SAED, lattice constants, atomic coordinates or CIF imported.','This canonical audit does not grant training eligibility, visual/reader approval, Site integration or publication.'],'training_eligible':False,'site_modified':False,'ledger_modified':False,'source_files_modified':False,'published':False}
report['canonical_author']='/root/peng1998_reader_assets'
(B/'canonical-records-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'canonical-records-audit.md').write_text('Ribeiro canonical scientific audit passed with source limits preserved. No author correction required.\n\nAll 11 drafts (one route, five procedures, five observations), 13 operations and 147 measurement/context entries were inspected. All 63 source facts map through 73 bindings; the separate inventory index retains 101 units through 114 bindings. These identifiers and contexts do not imply independent experiments.\n\nWater/Sn ratio basis, initial versus final concentration, acid-set versus post-base pH, observation-time versus reaction-hold meaning, radii versus diameter, source model assumptions and caption/prose conflicts remain explicit. The six-page main-source review is inherited from its independent audit; targeted pages 2–5 and the conclusion were reread here. SI remains unverified. No XRD/SAED/atomic coordinates or training admission is created.\n\nSchema/semantic validation passed; all records share one source split group. Exact hashes and '+str(len(checks))+' checks are in canonical-records-audit.json. Visual presentation, Site integration and publication remain separate gates.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'counts':counts,'audit_sha256':sha(B/'canonical-records-audit.json'),'markdown_sha256':sha(B/'canonical-records-audit.md')}))
