"""Independent, read-only source-to-canonical audit. Writes only this package's audit outputs."""
import sys,json,hashlib,re,collections
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent
S=Path(r'[local path redacted]')
sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record,eligibility,build_groups
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pointer(v,p):
    if not p:return v
    for k in p.lstrip('/').split('/'):
        k=k.replace('~1','/').replace('~0','~')
        v=v[int(k)] if isinstance(v,list) else v[k]
    return v
def packed(v):return json.dumps(v,ensure_ascii=False,separators=(',',':'))
checks=[];findings=[];bound={}
def check(label,ok,detail=None):
    checks.append({'check':label,'passed':bool(ok)})
    if not ok:findings.append({'check':label,'detail':detail})
def bind(p,expected=None):
    p=Path(p);p=p if p.is_absolute() else B/p
    h=sha(p);bound[str(p)]=h
    if expected:check('Unchanged bytes: '+str(p),h==expected,{'expected':expected,'actual':h})
    return h
M=read(B/'canonical-record-manifest.json');C=read(B/'canonical-source-coverage.json')
I=read(B/'source-inventory.json');F0=read(B/'source-facts.json');A=read(B/'source-scientific-audit.json')
F={x['id']:x for x in F0['facts']}
bind('canonical-record-manifest.json','185ae1359ba2aab1e2091e877cc2b72f929cfb14128fc7ae56ddffe067a0d609')
for n,k in [('source-facts.json','source_facts_sha256'),('source-inventory.json','source_inventory_sha256'),('source-scientific-audit.json','source_extraction_audit_sha256'),('page-coverage.json','page_coverage_sha256')]:bind(n,M[k])
for n,h in A['audited_artifacts'].items():bind(n,h)
for x in M['original_sources']:bind(x['path'],x['sha256'])
for x in A['reviewed_assets']:bind(x['path'],x['sha256'])
for n in ['canonical-source-coverage.json','canonical-draft-validation.json','canonical-draft-notes.md','build_canonical_drafts.py']:bind(n)
for n in ['dataset_lib.py','schema_definition.py','record_helpers.py']:bind(S/'scripts'/n)
check('Prior independent full supplied-source audit passed',A['status']=='passed' and A['independent'] is True)
R={}
for x in M['records']:
    bind(x['path'],x['sha256']);r=read(x['path']);R[r['record_id']]=r
    check('Record ID '+x['record_id'],r['record_id']==x['record_id'])
    check('Schema and semantic validation '+r['record_id'],not (e:=validate_record(r)),e)
    check('Private review status '+r['record_id'],r['quality']['review_status']=='imported_unreviewed')
    check('No requested training tasks '+r['record_id'],r['quality']['requested_tasks']==[])
    check('No current eligibility '+r['record_id'],all(not z['eligible'] for z in eligibility(r).values()))
    check('Manifest operation IDs '+r['record_id'],[o['id'] for o in r['operations']]==x['operations'])
    check('Manifest sample IDs '+r['record_id'],[p['sample_id'] for p in r['products']]==x['samples'])
    check('Single source DOI and year '+r['record_id'],all(s['doi']=='10.1021/ja048427j' and s['year']==2004 for s in r['sources']))
    check('Shared source split '+r['record_id'],r['lineage']['source_group']=='norberg2004')
    check('No invented structure assets '+r['record_id'],not r.get('structure_assets'))
check('All 19 frozen canonical files covered',set(R)=={p.stem for p in (B/'canonical-drafts').glob('*.json')} and len(R)==19)
check('Every source fact exactly once in coverage',len(C['facts'])==201 and {x['source_fact_id'] for x in C['facts']}==set(F))
fact_rows=[]
for x in C['facts']:
    f=F[x['source_fact_id']]; fid=f['id']; check('Coverage original exact '+fid,x['source_fact']==f)
    check('Nonempty canonical binding '+fid,bool(x['canonical_bindings']))
    for z in x['canonical_bindings']:
        rid=z['record_id'];q=pointer(R[rid],z['pointer']);v=pointer(f['value'],z['source_value_pointer']);label=fid+' '+rid+z['pointer']
        check('Typed field '+label,isinstance(q,dict) and 'status' in q and 'value' in q)
        # Lists without member pointers are explicit intervals, never an inferred mean.
        if isinstance(v,list):same=q.get('value') is None and [q.get('minimum'),q.get('maximum')]==v
        elif q.get('value') is not None:same=q['value']==v
        elif isinstance(v,(int,float)):same=(q.get('minimum')==v) != (q.get('maximum')==v)
        else:same=q.get('value')==v
        check('Exact source numeric/text value '+label,same,{'source':v,'canonical':q})
        text=q.get('basis','')+' '+q.get('note','')+' '+q.get('qualifier','')
        check('Original sample scope preserved '+label,f['sample_scope'] in text,{'scope':f['sample_scope'],'field':q})
        check('Source-native status retained '+label,f['status'] in text,{'status':f['status'],'field':q})
        check('Source qualifier retained '+label,not f['qualifier'] or f['qualifier'] in text)
        if f['uncertainty'] is not None:check('Uncertainty exact and un-reclassified '+label,packed(f['uncertainty']) in text and 'not reclassified' in text)
        if 'approximate' in q:check('Approximation flag '+label,q['approximate']==f['approximate'])
        if f['raw_text'] and 'raw_text' in q:check('Raw reported text '+label,q['raw_text']==f['raw_text'])
        # All scalar-unit fields except object rows retain the original fact unit.
        if 'unit' in q and not isinstance(f['value'],dict):check('Exact source unit '+label,q['unit']==(f['unit'] or ''),{'source':f['unit'],'canonical':q['unit']})
        ev=q.get('evidence',[])
        for se in f['evidence']:
            role='Main' if se['source_role']=='main' else 'SI'
            check('Exact source page and locator '+label+str(se['pdf_page']),any(e['source_id']=='norberg2004' and role in e['locator'] and f"p. {se['pdf_page']} " in e['locator'] and se['locator'] in e['locator'] for e in ev),{'source':se,'field':q})
        fact_rows.append({'source_fact_id':fid,'record_id':rid,'pointer':z['pointer'],'source_value_pointer':z['source_value_pointer']})
check('All 366 source fact bindings traversed',len(fact_rows)==366)
# Whole inventory objects remain retrievable as exact JSON payloads in addition to semantic fields.
payload_objects=set();semantic=0
for x in C['source_objects']:
    src=pointer(I,x['source_pointer']);out=pointer(R[x['record_id']],x['pointer']);label=x['record_id']+x['pointer']
    if 'id' in src:check('Inventory original ID '+label,src['id']==x['source_object_id'])
    if x['mode']=='lossless_inventory_context_payload':
        check('Lossless inventory object '+label,json.loads(out['value'])==src)
        check('Context payload not a new measurement '+label,'not a measured target' in out['note'])
        payload_objects.add(x['source_pointer'])
    else:
        semantic+=1;check('Semantic source field resolves '+label,isinstance(out,(dict,list,str)) and bool(out))
expected_objects={f'/{category}/{j}' for category in ['materials','stocks','protocols','samples','figures_tables_schemes','equations','tables','chemical_intuition','references','gaps','other_source_content'] for j,_ in enumerate(I[category])}
check('All 174 inventory objects independently compared',payload_objects==expected_objects and len(expected_objects)==174,{'missing':sorted(expected_objects-payload_objects)})
for x in C['source_units']:
    for z in x['canonical_bindings']:
        q=pointer(R[z['record_id']],z['pointer']);check('Source unit binding '+x['source_unit_id']+' '+z['record_id']+z['pointer'],bool(q))
check('Audited source unit IDs all represented',set(A['reviewed_source_unit_ids'])<=set(x['source_unit_id'] for x in C['source_units']))
source_ops=[]
for x in C['source_operations']:
    so=pointer(I,x['source_pointer']);o=pointer(R[x['record_id']],x['pointer']);source_ops.append(so['id'])
    check('Source operation identity '+so['id'],so['id']==x['source_operation_id'])
    check('Mapped operation retains source action '+so['id'],so['action']==o['action'])
    check('Mapped operation retains source conditions '+so['id'],so.get('conditions','') in o['description'])
    check('Mapped operation retains input lineage '+so['id'],[i.removesuffix('-state') for i in o['inputs']]==so['inputs'])
    check('Mapped operation evidence '+so['id'],bool(o.get('evidence')))
check('All 26 inventory operations mapped exactly once',len(source_ops)==len(set(source_ops))==26 and set(source_ops)=={o['id'] for p in I['protocols'] for o in p['operations']})
# Independent scoped transformations, checked against the original page contexts.
derived={'author_estimation_from_literature','author_model','author_estimated','author_fit','author_model_bound','author_derived_from_XRD','author_derived','author_tentative_interpretation'}
for x in C['facts']:
    f=x['source_fact']
    for z in x['canonical_bindings']:
        q=pointer(R[z['record_id']],z['pointer'])
        expected='author_derived' if f['status'] in derived else 'reported'
        if f['status']=='author_model_and_cited_comparison':expected='reported' if 'cited_experimental' in z['source_value_pointer'] else 'author_derived'
        check('Correct source versus model status '+f['id']+z['pointer'],q['status']==expected)
        if z['pointer'].startswith('/measurements/'):
            m=pointer(R[z['record_id']],z['pointer'].rsplit('/',1)[0]);scope=f['sample_scope']; sid=m['sample_id']
            if scope=='Films A–C collectively / individual film not specified':expected_sid='films-a-b-c-collective'
            elif scope=='table-s4':expected_sid='film-'+f['value']['film'].lower()
            elif scope=='Literature or model context, not a measured outcome of this paper':expected_sid=f['id'].removeprefix('norberg2004-')
            else:expected_sid=scope
            check('Actual sample association '+f['id']+z['pointer'],sid==expected_sid,{'actual':sid,'expected':expected_sid})
        if isinstance(f['value'],dict) and 'unit' in q:
            member=z['source_value_pointer']; expected_unit=''
            for key,unit in [('frequency_GHz','GHz'),('path_length_cm','cm'),('temperature_K','K'),('field_T_range','T'),('cuvette_cm','cm'),('cm-1','cm−1'),('accelerating_voltage_kV','kV'),('instrument_temperature_ceiling_K','K'),('mass_ug','µg'),('Ms_emu_g','emu/g'),('Ms_muB_per_Mn2+','µB/Mn2+')]:
                if key in member:expected_unit=unit
            check('Object member unit '+f['id']+member,q['unit']==expected_unit)
def measurements(suffix):return {m['id']:m for m in R['norberg-2004-'+suffix]['measurements']}
def factq(fid):
    x=next(x for x in C['facts'] if x['source_fact_id']==fid);return [pointer(R[z['record_id']],z['pointer']) for z in x['canonical_bindings']]
dom=measurements('magnetism')['norberg2004-domain-spin-bound']
check('S>800 is a collective domain estimate, not Film A or atomic spin',dom['sample_id']=='films-a-b-c-collective' and dom['value'].get('minimum')==800 and dom['value'].get('minimum_exclusive') is True and dom['value']['status']=='author_derived')
check('No D–F invented preparation operations',R['norberg-2004-films-d-f']['operations']==[])
check('Only one common hydrolysis route',collections.Counter(r['record_type'] for r in R.values())=={'literature_protocol':1,'procedure':11,'observation':7})
for k in ['norberg2004-zn-magnetic-impurities','norberg2004-cool-limit']:
    check('Strict upper bound '+k,all(q.get('maximum_exclusive') is True and q['value'] is None for q in factq(k)))
for m in R['norberg-2004-films-d-f']['measurements']:
    if m['sample_id'] in ['film-d','film-f'] and 'source' not in m['id'] and not str(m['value'].get('value','')).startswith('{'):
        check('D/F conflict attached to actual result '+m['id'],'g-si-curve-table' in packed(m) or 'D/F' in packed(m),m)
check('D/F conflict remains in both manuscript representations','g-si-curve-table' in packed(R['norberg-2004-films-d-f']) and 'D > E > F' in packed(R['norberg-2004-films-d-f']) and '0.038' in packed(R['norberg-2004-films-d-f']) and '0.076' in packed(R['norberg-2004-films-d-f']))
check('Surface-control avoids 180 C stripping',not any(q.get('value')==180 for o in R['norberg-2004-surface-control']['operations'] for q in o['parameters'].values()))
check('TOPO treatment does not borrow quantitative amine-cleaning conditions',all(not isinstance(q.get('value'),(int,float)) for o in R['norberg-2004-topo']['operations'][:1] for q in o['parameters'].values()))
check('Dodecylamine melting point is reagent property',measurements('reagent-properties')['norberg2004-dda-mp']['sample_id']=='dodecylamine' and all(o['parameters'].get('temperature',{}).get('value')!=30 for r in R.values() for o in r['operations']))
check('Theory carrier concentration separate from film measurements',measurements('source-context')['norberg2004-theory-carriers']['sample_id']=='theory-context')
check('Dopant means retained as model-derived outcomes',all(m['value']['status']=='author_derived' for m in R['norberg-2004-dopant-statistics']['measurements'] if 'model-mn-count' in m['id']))
check('SI notation ambiguity remains explicit','g-poisson' in packed(R['norberg-2004-dopant-statistics']))
check('Same-paper records remain together for eventual dataset split',len(set(build_groups(list(R.values())).values()))==1)
counts={'records':len(R),'operations':sum(len(r['operations']) for r in R.values()),'measurements_and_context_entries':sum(len(r['measurements']) for r in R.values()),'source_facts':len(F),'source_fact_bindings':len(fact_rows),'source_units':len(C['source_units']),'source_unit_bindings':sum(len(x['canonical_bindings']) for x in C['source_units']),'original_inventory_objects':len(expected_objects),'source_object_bindings':len(C['source_objects']),'source_operations':len(source_ops)}
check('Counts match frozen manifest',all(v==M['counts'].get(k,v) for k,v in counts.items()))
for x in M['records']:bind(x['path'],x['sha256'])
bind(__file__)
result={'schema':'mattersyn-independent-canonical-audit/1','source_id':'norberg2004','doi':'10.1021/ja048427j','reviewer':'/root/peng1998_reader_assets','author':'/root/norberg2004_extract','independent':True,'at':datetime.now(timezone.utc).isoformat(),'status':'passed' if not findings else 'findings','counts':counts,'checks':checks,'check_count':len(checks),'findings':findings,'record_hashes':{x['record_id']:x['sha256'] for x in M['records']},'bound_files':bound,'fact_bindings_checked':fact_rows}
(B/'canonical-audit-working-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'findings':len(findings),'first_findings':findings[:14]},ensure_ascii=False,indent=2))
