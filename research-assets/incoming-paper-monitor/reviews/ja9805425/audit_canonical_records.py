"""Independent source oracle for the Peng 1998 draft records; no Site mutation."""
import json,hashlib,datetime
from pathlib import Path
B=Path(__file__).parent
files=sorted((B/'canonical-drafts').glob('*.json'))
rs={p.stem:json.loads(p.read_text(encoding='utf-8')) for p in files}
checks=[]
def check(id,ok,detail):checks.append({'id':id,'passed':bool(ok),'detail':detail})
def r(key):return rs['peng-1998-'+key]
def op(key,id):return next(o for o in r(key)['operations'] if o['id']==id)
def m(key,id):return next(o for o in r(key)['measurements'] if o['id']==id)
def checkq(id,q,v,u,status='reported'):
    check(id,q.get('value')==v and q.get('unit')==u and q.get('status')==status,f'Source oracle: {v!r} {u}, status={status}; actual {q.get("value")!r} {q.get("unit")}, status={q.get("status")}.')
expected_kinds={'cdse-focusing':'literature_protocol','inas-focusing':'literature_protocol','incl3-top-stock':'procedure','cdse-aliquot-analysis':'procedure','inas-aliquot-analysis':'procedure','pl-size-analysis':'procedure','cdse-kinetics':'observation','inas-kinetics':'observation','cdse-tem':'observation','cdse-calibration':'observation','inas-calibration':'observation','growth-model':'observation'}
check('record_inventory',set(rs)=={'peng-1998-'+k for k in expected_kinds},'Twelve records: two synthesis routes, four supporting procedures and six observation contexts. Reinjections are not extra routes.')
for key,kind in expected_kinds.items():
    x=r(key); check(key+'-type',x['record_type']==kind,'Expected '+kind)
    check(key+'-identity',all(s['id']=='peng1998' and s['doi']=='10.1021/ja9805425' and s['year']==1998 for s in x['sources']),'Correct source ID/DOI/year.')
    check(key+'-intended-target',x['intended_target']['composition']['value'] in (['CdSe','InAs'] if kind=='literature_protocol' else [None]),'Only two named synthesis routes have an intended material target.')
    check(key+'-no-size-target',x['intended_target']['size']['value'] is None,'No exact requested synthesis size invented.')
    check(key+'-no-phase-target',x['intended_target']['phase']['value'] is None,'No experimental crystal phase reported in the supplied sources.')
    check(key+'-training-task-scope',x['quality']['requested_tasks']==(['precursor_selection','partial_protocol'] if kind=='literature_protocol' else []),'No new exact-size, exact-structure, success or unrelated task labels.')
    check(key+'-no-batch-ids',x['lineage']['batch_id'] is None and all(p['batch_id'] is None for p in x['products']),'Curator IDs are not author-assigned batch identifiers.')
    check(key+'-no-structure-assets',not x['structure_assets'],'No invented CIF, SAED, XRD or atomic coordinates.')
    mids={p['sample_id'] for p in x['products']}
    check(key+'-sample-links',all(mm['sample_id'] in mids for mm in x['measurements']),'All measurements have existing context/product sample IDs.')
    for pp in x['products']:
        check(key+'-phase-'+pp['sample_id'],pp['phase']['value'] is None,'No phase assigned to '+pp['sample_id'])
    for oo in x['operations']:
        check(key+'-operation-evidence-'+oo['id'],bool(oo['evidence']) and all(e['source_id']=='peng1998' for e in oo['evidence']),'Every operation has this source’s locator.')
    for mm in x['measurements']:
        check(key+'-measurement-evidence-'+mm['id'],bool(mm['evidence']) and bool(mm['value'].get('evidence')) and all(e['source_id']=='peng1998' for e in mm['evidence']),'Each numeric/text measurement preserves source evidence.')
    def walk(v,path=''):
        if isinstance(v,dict):
            if 'value'in v and 'status'in v:
                check(key+'-fact-evidence-'+path,bool(v.get('evidence')),'Source-bearing fact retains evidence at '+path)
                if v['value'] is None and v.get('minimum') is None and v.get('maximum') is None:
                    check(key+'-null-status-'+path,v['status'] in ['not_reported','unresolved','not_applicable','unknown'],'Null quantity/fact remains missing rather than reported zero.')
            for k,z in v.items():walk(z,path+'/'+k)
        elif isinstance(v,list):
            for n,z in enumerate(v):walk(z,path+'/'+str(n))
    walk(x)
expected_ops={'cdse-focusing':['prepare-stock','heat','injection','grow','refeed'],'inas-focusing':['prepare-feed','heat','injection','recover','grow','refeed1','continue','refeed2'],'incl3-top-stock':['heat','cool','store'],'cdse-aliquot-analysis':['withdraw','precipitate','purify','redissolve','adjust-od','measure'],'inas-aliquot-analysis':['withdraw','dilute','measure'],'pl-size-analysis':['calibrate','convert','moments']}
for key,ids in expected_ops.items():check(key+'-operation-sequence',[o['id'] for o in r(key)['operations']]==ids,'Source-scoped operation order: '+', '.join(ids))
for key,oids in [('cdse-focusing',['injection']),('inas-focusing',['injection'])]:
    q=op(key,'injection')['parameters']['injection_duration_upper_bound']
    check(key+'-strict-duration-bound',q.get('value') is None and q.get('maximum')==.1 and q.get('maximum_exclusive') is True and q.get('status')=='reported' and '<0.1' in q.get('raw_text','') and q['unit']=='s','Initial injection is <0.1 s, not an exact duration. Typed exclusive maximum and original strict-bound wording preserved.')
source_q=[
('cdse-focusing','heat','temperature',360,'degC'),('cdse-focusing','heat','topo_mass',4,'g'),('cdse-focusing','injection','injection_volume',2.4,'mL'),('cdse-focusing','injection','post_injection_temperature',300,'degC'),('cdse-focusing','grow','elapsed_time_before_reinjection',190,'min'),('cdse-focusing','refeed','injection_volume',.8,'mL'),('cdse-focusing','refeed','elapsed_time_from_first_injection',190,'min'),
('inas-focusing','heat','temperature',300,'degC'),('inas-focusing','heat','top_mass',2,'g'),('inas-focusing','injection','injection_volume',1,'mL'),('inas-focusing','injection','initial_post_injection_temperature',250,'degC'),('inas-focusing','recover','temperature',260,'degC'),('inas-focusing','grow','elapsed_time_to_next_injection',23,'min'),('inas-focusing','refeed1','injection_volume',.5,'mL'),('inas-focusing','refeed1','elapsed_time_from_first_injection',23,'min'),('inas-focusing','continue','temperature',260,'degC'),('inas-focusing','continue','next_injection_elapsed_time',158,'min'),('inas-focusing','refeed2','injection_volume',.8,'mL'),('inas-focusing','refeed2','elapsed_time_from_first_injection',158,'min'),
('incl3-top-stock','heat','temperature',260,'degC'),('incl3-top-stock','heat','incl3_per_top_volume',.33,'g/mL'),('cdse-aliquot-analysis','withdraw','aliquot_volume',.2,'mL'),('cdse-aliquot-analysis','precipitate','methanol_volume',2,'mL'),('cdse-aliquot-analysis','adjust-od','optical_density',.09,'dimensionless'),('cdse-aliquot-analysis','adjust-od','optical_density_tolerance',.02,'dimensionless')]
for key,oid,p,v,u in source_q:checkq(key+'-'+oid+'-'+p,op(key,oid)['parameters'][p],v,u)
checkq('cdse-nominal-growth-temperature',op('cdse-focusing','grow')['parameters']['growth_temperature'],300,'degC','inferred')
check('cdse-growth-temperature-scope','maintain' in json.dumps(op('cdse-focusing','grow')).lower() or 'inferred' in json.dumps(op('cdse-focusing','grow')).lower(),'300 °C is a contextual nominal growth condition, not a separately measured continuous hold.')
check('cdse-slow-dose-rate-missing',op('cdse-focusing','refeed')['parameters']['injection_rate']['value'] is None,'Slow feed has no numerical rate.')
check('inas-aliquot-volume-missing',op('inas-aliquot-analysis','withdraw')['parameters']['aliquot_volume']['value'] is None,'Do not import the CdSe aliquot volume.')
check('stock-concentration-basis','solvent' in op('incl3-top-stock','heat')['parameters']['incl3_per_top_volume']['basis'].lower(),'0.33 g per mL TOP, not measured final-solution concentration.')
check('stock-storage-temperature-missing',not any('temperature' in k for k in op('incl3-top-stock','store')['parameters']),'Do not import storage −35 °C.')
check('stock-storage-drybox','drybox' in op('incl3-top-stock','store')['environment']['value'].lower(),'Drybox storage preserved.')
check('stock-argon','argon' in op('incl3-top-stock','heat')['environment']['value'].lower(),'Argon used for upstream preparation.')
check('inas-growth-atmosphere-not-inherited',op('inas-focusing','heat')['environment']['value'] is None,'No separate InAs growth atmosphere asserted from upstream argon.')
check('cdse-argon-flow','flowing ar' in op('cdse-focusing','heat')['environment']['value'].lower(),'Flowing argon is explicit for hot TOPO.')
stock_expect={'cdse-focusing':[('se',2),('cdme2',5),('tbp',100)],'inas-focusing':[('tms3as',1),('incl3',1.1),('top',2.8)]}
for key,parts in stock_expect.items():
    st=r(key)['stocks'][0]
    check(key+'-stock-components',[(z['material_id'],z['quantities']['mass_parts']['value']) for z in st['components']]==parts,'Exact source mass parts and precursor identities.')
    for z in st['components']:checkq(key+'-stock-'+z['material_id'],z['quantities']['mass_parts'],dict(parts)[z['material_id']],'mass part')
    check(key+'-stock-not-molarity',not st['concentrations'],'No stock density, molarity or component charges fabricated.')
check('cdse-tbp-distinct-top','tbp'in {x['id'] for x in r('cdse-focusing')['materials']} and 'top'not in {x['id'] for x in r('cdse-focusing')['materials']},'CdSe uses tributylphosphine in this paper, not TOP.')
check('inas-tms3as-identity',next(x for x in r('inas-focusing')['materials'] if x['id']=='tms3as')['formula']=='C9H27AsSi3','Tris(trimethylsilyl)arsine molecular formula; no tris-selenium substitution.')
opts=r('cdse-focusing')['condition_options'];check('cdse-four-context-variants',len(opts)==4,'Reduced first dose, Cd-rich, low-Cd, and low-Cd with concentration rescue remain separate contexts.')
for ix,k,v,u in [(0,'initial_feed_reduction',15,'%'),(1,'cadmium_to_selenium_molar_ratio',1.9,'mol/mol'),(2,'cadmium_to_selenium_molar_ratio',1.1,'mol/mol'),(3,'cadmium_to_selenium_molar_ratio',1.1,'mol/mol')]:checkq('variant-'+str(ix)+'-'+k,opts[ix]['parameters'][k],v,u)
check('reduced-dose-approximate',opts[0]['parameters']['initial_feed_reduction']['approximate'],'About 15%, not exactly 15%.')
check('almost-double-approximate',opts[3]['parameters']['cd_and_se_concentration_multiplier']['approximate'] and 'almost' in opts[3]['parameters']['cd_and_se_concentration_multiplier']['qualifier'],'Almost doubled remains qualified, not an exact concentration multiplier.')
cdse_expected=[('initial-size','cdse-trajectory',2.1,'nm'),('initial-spread','cdse-trajectory',20,'%'),('focused-time','cdse-trajectory',22,'min'),('focused-size','cdse-trajectory',3.3,'nm'),('focused-spread','cdse-trajectory',7.7,'%'),('defocused-size','cdse-trajectory',3.9,'nm'),('defocused-spread','cdse-trajectory',10.6,'%'),('refocused-spread','cdse-trajectory',8.7,'%'),('reduced-focusing-time','reduced-feed',11,'min'),('reduced-focused-size','reduced-feed',2.7,'nm'),('baseline-ratio','cdse-trajectory',1.4,'mol/mol'),('rich-ratio','cd-rich',1.9,'mol/mol'),('lean-ratio','near-equimolar',1.1,'mol/mol')]
for mid,sid,v,u in cdse_expected:
    mm=m('cdse-kinetics',mid);checkq('cdse-measurement-'+mid,mm['value'],v,u);check('cdse-measurement-scope-'+mid,mm['sample_id']==sid,'Correct trajectory or comparison context.')
check('baseline-ratio-approx',m('cdse-kinetics','baseline-ratio')['value']['approximate'],'About 1.4:1 molar ratio.')
check('refocus-no-exact-time','not stated' in m('cdse-kinetics','refocused-spread')['conditions'],'8.7% endpoint time is unspecified.')
check('kinetics-tem-not-joined',not any(mm['value'].get('value')==8.5 for mm in r('cdse-kinetics')['measurements']),'8.5 nm TEM specimen is not part of the smaller size trajectory.')
for t in [.2,1,12,35,55,190,210,240]:checkq('cdse-trace-time-'+str(t),m('cdse-kinetics','figure1-time-'+str(t).replace('.','p'))['value'],t,'min')
cdse_ids={x[0] for x in cdse_expected}|{'particle-number','monomer-trend','rich-stability','lean-defocusing','lean-concentrated'}|{'figure1-time-'+str(t).replace('.','p') for t in [.2,1,12,35,55,190,210,240]}
check('cdse-exact-measurement-inventory',{x['id'] for x in r('cdse-kinetics')['measurements']}==cdse_ids,'No undocumented curve points or missing source-valued rows.')
for tech,times in [('absorption',[18,28,43,158,176,245]),('pl',[23,28,80,158,176])]:
    for t in times:
        mm=m('inas-kinetics',f'{tech}-time-{t}');checkq(f'inas-{tech}-time-{t}',mm['value'],t,'min');check(f'inas-{tech}-time-scope-{t}','omits time units' in mm['conditions'],'The SI omits units; minutes are contextual from main trajectory.')
checkq('inas-reabsorption-energy',m('inas-kinetics','reabsorption-energy')['value'],1,'eV')
check('inas-reabsorption-approx',m('inas-kinetics','reabsorption-energy')['value']['approximate'],'Approximately 1 eV.')
check('inas-high-energy-only','higher-energy half' in m('inas-kinetics','high-half-only')['value']['value'],'Only high-energy PL half used.')
check('inas-no-transferred-od','optical_density' not in json.dumps(r('inas-aliquot-analysis')),'No CdSe OD parameter transferred to InAs.')
check('inas-no-transferred-precipitation',all(o['action']!='precipitation' for o in r('inas-aliquot-analysis')['operations']),'No source-free methanol precipitation for InAs.')
checkq('tem-diameter',m('cdse-tem','tem-diameter')['value'],8.5,'nm');checkq('tem-scale',m('cdse-tem','tem-scale')['value'],25,'nm')
check('tem-unassigned-recipe',r('cdse-tem')['products'][0]['recipe_link']!='explicit' and 'no full sample-specific recipe' in ' '.join(r('cdse-tem')['products'][0]['notes']),'TEM specimen not joined to exact recipe.')
tables={'cdse':[(484,2.47,2.1),(488,2.46,2.1),(516,2.34,2.4),(526,2.3,2.6),(534,2.27,2.7),(542,2.24,2.9),(550,2.21,3.1),(560,2.17,3.3),(566,2.16,3.4),(570,2.14,3.5),(576,2.09,3.6),(596,2.04,4.3),(600,2.03,4.4),(606,2.02,4.6),(608,2.01,4.7),(610,2,4.8)],'inas':[(838,1.41,2.3),(861,1.38,2.4),(886,1.34,2.6),(905,1.31,2.8),(929,1.28,3),(954,1.24,3.2),(976,1.22,3.4),(1004,1.19,3.6),(1029,1.16,3.8),(1051,1.13,4),(1078,1.1,4.2),(1107,1.08,4.4),(1132,1.05,4.6),(1159,1.03,4.8),(1187,1.01,5),(1216,.98,5.2),(1246,.96,5.4),(1272,.94,5.6),(1305,.92,5.8),(1333,.9,6)]}
for formula,rows in tables.items():
    key=formula+'-calibration';x=r(key)
    check(key+'-row-count',len(x['products'])==len(rows) and len(x['measurements'])==3*len(rows),'All rows manually checked against the source image; no OCR substitutions.')
    for n,(uv,pl,size) in enumerate(rows,1):
        sid=f'calibration-row-{n:02}'
        for prefix,val,unit in [('uv',uv,'nm'),('pl',pl,'eV'),('size',size,'nm')]:
            mm=m(key,f'{prefix}-{n:02}');checkq(key+f'-row{n:02}-{prefix}',mm['value'],val,unit);check(key+f'-row{n:02}-{prefix}-sample',mm['sample_id']==sid,'Within-row calibration join only.')
        pp=x['products'][n-1]
        check(key+f'-row{n:02}-no-recipe',pp['recipe_link']!='explicit' and pp['material_state_id'] is None and 'Not a new synthesis run' in ' '.join(pp['notes']),'Calibration row does not become a current synthesis batch.')
check('pl-method-delta-equal','delta-function' in op('pl-size-analysis','convert')['description'] and 'equal emission efficiency' in op('pl-size-analysis','convert')['description'],'Both PL conversion assumptions preserved.')
check('pl-method-width-limitation','overestimate distribution widths' in op('pl-size-analysis','convert')['description'],'Authors’ systematic width-overestimate limitation preserved.')
check('pl-method-no-third-moment','third moment/asymmetry is not determined' in op('pl-size-analysis','moments')['description'],'No reconstructed asymmetry.')
check('analysis-not-physical',r('pl-size-analysis')['products'][0]['composition']['value'] is None,'PL analysis context has no physical sample composition.')
check('model-not-physical',r('growth-model')['products'][0]['composition']['value'] is None,'Theory context has no physical sample composition.')
check('growth-eq1','exp(2σVm/(rRT))' in m('growth-model','gibbs-thomson')['value']['value'],'Gibbs–Thomson expression retained.')
check('growth-eq2','K(1/r + 1/δ)(1/r* − 1/r)' in m('growth-model','growth-rate')['value']['value'] and '≪ 1' in m('growth-model','growth-rate')['value']['value'],'Growth expression and much-less-than approximation retained.')
check('model-infinite-diffusion','infinite diffusion-layer thickness' in m('growth-model','figure4-limit')['value']['value'],'Source Figure 4 model limit retained.')
check('outlook-not-real-controller','does not report an implemented' in m('growth-model','automation')['value']['value'],'Future continuous control is distinguished from an implemented experiment.')
findings=[c for c in checks if not c['passed']]
report={'schema':'mattersyn-independent-canonical-audit-1','source_id':'peng1998','doi':'10.1021/ja9805425','reviewer':'independent_peng1998_source_audit','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed' if not findings else 'corrections_required','review_scope':'All twelve draft files read and compared with the independently text/visually reviewed two main and four SI PDF pages. All 108 calibration quantities and remaining recipe/measurement values checked against source; source-only administrative/bibliographic/figure metadata are delegated to reader coverage.','record_count':len(rs),'operation_count':sum(len(x['operations']) for x in rs.values()),'measurement_count':sum(len(x['measurements']) for x in rs.values()),'check_count':len(checks),'source_audit_sha256':hashlib.sha256((B/'source-audit.json').read_bytes()).hexdigest(),'records':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files],'checks':checks,'findings':findings,'limitations':['This audit does not verify rendered browser controls or Site publication.','References 1–20 remain bibliographic context; no external paper was read or downloaded.','Calibrated sizes are not exact recipe-conditioned training labels.','Public reader must retain all 160 source units, including figures, limitations, references and administrative disposition.']}
(B/'canonical-records-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Independent canonical audit — Peng 1998','',f"Status: {report['status']}. {len(rs)} records; {report['operation_count']} operations; {report['measurement_count']} measurements; {len(checks)} checks.",'',report['review_scope'],'','## Findings','']
lines += [f"- {f['id']}: {f['detail']}" for f in findings] or ['No unresolved scientific value, unit, recipe-boundary or sample-join findings.']
lines+=['','## Evidence boundaries','','The supplied main and matching SI were independently read and visually inspected in full. The CdSe/InAs calibration tables were manually transcribed and compared row by row because OCR is corrupted. The 8.5 nm TEM specimen remains unassigned to an exact synthesis trajectory; sequential precursor injections stay within their respective growth routes. No atomic phase, XRD, SAED, CIF, numerical yield or unreported workup is invented.','', 'Exact reviewed draft hashes are recorded in canonical-records-audit.json.']
(B/'canonical-records-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(checks),'findings':findings},ensure_ascii=False))
