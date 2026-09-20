"""Independent supplied-main source-to-eleven-record audit; private output only."""
from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
keys=['resin-conditioning','cadmium-loading','sample-a','sample-b','timepoint-workup','absorption','optical-microscopy','xrd','tem','other-electrolytes','characterization']
records={k:read(B/'canonical-drafts'/('yao-1998-'+k+'.json')) for k in keys}
checks=[]
def check(n,b,detail=''):checks.append({'name':n,'passed':bool(b),'detail':detail})
def op(k,i):return next(o for o in records[k]['operations'] if o['id']==i)
def mat(k,i):return next(m for m in records[k]['materials'] if m['id']==i)
def st(k,i):return next(s for s in records[k]['stocks'] if s['id']==i)
def evidence(j):return ' '.join(e.get('locator','')for e in j.get('evidence',[]))
def val(k,i,p,v):check(k+'/'+i+'/'+p,op(k,i)['parameters'][p].get('value')==v)
def evhas(j,p):return f'PDF p. {p},'in evidence(j)
for k,r in records.items():
 check(k+' source and year',r['sources'][0]['doi']=='10.1021/la970480g'and r['sources'][0]['year']==1998)
 check(k+' unreviewed and no training',r['quality']['review_status']=='imported_unreviewed'and r['quality']['requested_tasks']==[])
 check(k+' all operation evidence',all(o.get('evidence')for o in r['operations']))
 check(k+' no unsupported recovery equipment',not any(o['action'] in ['centrifugation','filtration','decantation']for o in r['operations']))
 for p in r['products']:check(k+'/'+p['sample_id']+' batch not invented',p.get('batch_id')is None)
for i,v in [('hcl-wash',2),('naoh-wash',2)]:check(i+' wash concentration',next(iter(st('resin-conditioning',i)['concentrations'].values()))['value']==v)
check('Resin wash order',[o['id']for o in records['resin-conditioning']['operations']]==['soak','wash-methanol','wash-hcl','wash-naoh','wash-water','ethanol','dry','store'])
val('resin-conditioning','wash-water','eluent_ph',10)
check('pH belongs to eluent',op('resin-conditioning','wash-water')['parameters']['eluent_ph']['approximate']is True)
check('Dry host mass0.107g',mat('cadmium-loading','resin')['quantities']['dry_mass']['value']==0.107)
check('Cdstock8.4mM5mL',st('cadmium-loading','cadmium-stock')['concentrations']['molarity']['value']==8.4e-3 and st('cadmium-loading','cadmium-stock')['concentrations']['solution_volume']['value']==5)
check('Cadmium acetate is dihydrate','2H2O'in mat('cadmium-loading','cd-acetate')['formula'])
val('cadmium-loading','load','duration',10);val('cadmium-loading','equilibrate','duration',2)
check('Cdsonication no temperature invented','temperature'not in op('cadmium-loading','load')['parameters'])
check('Diagnostic counterion unknown',mat('cadmium-loading','diagnostic-hs')['formula']=='HS−'and 'Counterion'in' '.join(mat('cadmium-loading','diagnostic-hs')['notes']))
for k in ['sample-a','sample-b']:
 s=st(k,'sulfide-stock')['concentrations'];check(k+' sulfide stock38e-5M100mL',s['molarity']['value']==3.8e-4 and s['solution_volume']['value']==100)
 check(k+' Na2S nonahydrate','9H2O'in mat(k,'na2s')['formula'])
 val(k,'precondition','duration',10);val(k,'stir','duration',2);val(k,'stand','duration',2)
 check(k+' stirred temperature unknown','temperature'not in op(k,'stir')['parameters'])
 check(k+' standingroomtemperature qualifier',op(k,'stand')['parameters']['temperature']['value']is None and op(k,'stand')['parameters']['temperature']['qualifier']=='room temperature')
 check(k+' clockconflictretained',any('48 h'in c and'2 h'in c for c in records[k]['quality']['conflicts']))
 check(k+' productembedded','polymer'in records[k]['products'][0]['composition']['value'].lower())
 check(k+' washes water thenethanol',[o['id']for o in records[k]['operations'] if o['id'].startswith('wash-')]==['wash-water','wash-ethanol'])
 check(k+' no drying time/temperature inserted',not any(z in op(k,'dry')['parameters']for z in ['temperature','duration']))
check('Samplea10mLwater',op('sample-a','precondition')['parameters']['water_volume']['value']==10)
check('Sampleb10mL0.5Msaltstock',st('sample-b','nacl-stock')['concentrations']['solution_volume']['value']==10 and st('sample-b','nacl-stock')['concentrations']['molarity']['value']==0.5)
check('Samplebfinalsaltunresolved',any('post-mixing'in c.lower()and'0.5 M'in c for c in records['sample-b']['quality']['conflicts']))
check('Timepoint aliquot severalmLnotnumeric',op('timepoint-workup','sample')['parameters']['aliquot_volume']['value']is None and'several'in op('timepoint-workup','sample')['parameters']['aliquot_volume']['qualifier'])
check('Absorptionwetbead100–110um',op('absorption','acquire')['parameters']['wet_host_diameter']['minimum']==100 and op('absorption','acquire')['parameters']['wet_host_diameter']['maximum']==110)
val('absorption','time-readout','monitor_wavelength',450)
val('optical-microscopy','measure-layer','precision_limit',4)
check('XRD range20–60',op('xrd','acquire')['parameters']['two_theta_range']['minimum']==20 and op('xrd','acquire')['parameters']['two_theta_range']['maximum']==60)
val('xrd','acquire','xray_wavelength',0.154);val('xrd','fit','fitted_two_theta',26.5)
check('TEMlowandhighremainseparate',op('tem','low')['depends_on']==['section']and op('tem','high')['depends_on']==['section'])
check('TEMfit0.4unitundefined','unit unspecified'in op('tem','distribution')['description'])
alt=records['other-electrolytes']
check('Alternative salts are observation not operative recipe',alt['record_type']=='observation' and not alt['operations'] and not alt['stocks'] and not alt['material_states'])
check('Three alternative specimens and six qualitative comparisons',len(alt['products'])==3 and len(alt['measurements'])==6)
for salt,formula in [('licl','LiCl'),('kcl','KCl'),('tmacl','C4H12NCl')]:
 m=mat('other-electrolytes',salt);q=m['quantities']['nominal_source_concentration']
 check(salt+' identity, nominal0.5M and unknown concentration stage',m['formula']==formula and q['value']==0.5 and q['unit']=='mol/L' and 'stock versus final mixture is not stated'in q['basis'])
 p=next(p for p in alt['products'] if p['sample_id']=='electrolyte-'+salt)
 check(salt+' separate unresolved specimen context',p['recipe_link']=='general_context' and p['phase']['value']is None and 'not one combined mixture'in ' '.join(p['notes']))
 ms=[m for m in alt['measurements'] if m['sample_id']==p['sample_id']]
 check(salt+' absorption and L only',len(ms)==2 and {m['property']for m in ms}=={'visible_absorption_comparison','cds_layer_width_comparison'})
 for m in ms:
  check(m['id']+' qualitative source note25 join',isinstance(m['value']['value'],str) and 'quite similar to the nominal 0.5 M NaCl sample'in m['value']['value'] and evhas(m,4) and 'Note 25'in evidence(m) and 'no numeric difference'in m['conditions'])
c=records['characterization'];ms={m['id']:m for m in c['measurements']}
check('Characterization 53 source rows once only',len(ms)==53 and len(c['measurements'])==53 and not c['operations'])
# Expected numeric transcriptions and source-region joins established from the independently read seven pages.
# Scalar: (value, unit, sample); range: (lower, upper, unit, sample).
expected={
'host-wet-diameter':(100,110,'um','a-and-b-context'),
'spectrum-reproducibility':(5,'%','a-and-b-context'),
'lamp-power':(150,'W','a-and-b-context'),
'monitor-wavelength':(450,'nm','a-and-b-context'),
'xrd-scan':(20,60,'degree','a-and-b-context'),
'xrd-radiation':(.154,'nm','a-and-b-context'),
'xrd-111':(26.5,'degree','a-and-b-context'),
'xrd-220':(44,'degree','a-and-b-context'),
'xrd-311':(52,'degree','a-and-b-context'),
'sample-a-xrd-mean':(3.8,'nm','sample-a'),
'sample-b-xrd-mean':(3.1,'nm','sample-b'),
'sample-b-plateau':(2,'h','sample-b'),
'sample-a-continuation':(48,'h','sample-a'),
'sample-a-sqrt-time-slope':(.0046,'s^(-1/2)','sample-a'),
'sample-b-sqrt-time-slope':(.0089,'s^(-1/2)','sample-b'),
'a-depth4um-depth':(4,5,'um','a-depth4um'),
'a-depth8um-depth':(8,9,'um','a-depth8um'),
'b-depth9um-depth':(9,10,'um','b-depth9um'),
'b-depth15um-depth':(15,16,'um','b-depth15um'),
'a-layer-end':(8,10,'um','sample-a'),
'a-inner-crystals':(4,7,'nm','a-depth4um'),
'a-surface-hist-mean':(2.7,'nm','a-surface'),
'a-surface-hist-sd':(.4,'','a-surface'),
'a-inner-hist-depth':(4,'um','a-depth4um'),
'a-inner-hist-mean':(4.6,'nm','a-depth4um'),
'a-inner-hist-sd':(1.8,'nm','a-depth4um'),
'a-surface-qual-size':(3,'nm','a-surface'),
'a-inner-qual-size':(5,'nm','a-depth4um'),
'a-ring-depth':(8,'um','sample-a'),
'l-resolution':(4,'um','a-and-b-context'),
'sample-a-effective-HS-diffusion':(2.5e-10,'cm^2 s^-1','sample-a'),
'sample-b-effective-HS-diffusion':(1.1e-9,'cm^2 s^-1','sample-b'),
'donnan-no-salt':(-390,'mV','donnan-model-no-salt'),
'donnan-salt':(-10,'mV','donnan-model-salt'),
'donnan-swelling':(-26,'meV','donnan-model-one-third-swelling'),
'donnan-fixed-charge':(.4,'equiv/L','donnan-model-context'),
'na-diffusion':(1.2e-7,'cm^2 s^-1','pretreatment-context'),
'selectivity':(1e7,'','donnan-model-context')}
for k,x in expected.items():
 m=ms['char-'+k];q=m['value'];isrange=len(x)==4
 ok=(q.get('value')is None and q.get('minimum')==x[0]and q.get('maximum')==x[1])if isrange else q.get('value')==x[0]
 check('char-'+k+' source value, unit and scope',ok and q.get('unit')==x[-2]and m['sample_id']==x[-1]and bool(m['evidence']))
facts={
'phase':('a-and-b-context','cubic'),
'30min-optical':('a-and-b-context','lower absorbance below 500'),
'48h-optical':('a-and-b-context','blue-shifted'),
'first2h-optical':('a-and-b-context','first 2 h'),
'early-shape':('a-and-b-context','nearly the same'),
'a-center':('sample-a','No crystals were observed'),
'a-surface-flocculation':('a-surface','No CdS flocculation'),
'a-inner-aggregates':('a-depth4um','several tens of nanometers'),
'l-definition':('a-and-b-context','surface to the optically visible ring'),
'sample-b-surface':('b-surface','No flocculation'),
'sample-b-middle':('b-depth9um','Slight flocculation'),
'sample-b-deep':('b-depth15um','isolated small nanocrystals'),
'b-larger-L':('a-and-b-context','wider'),
'a-L-correlation':('a-and-b-context','linear relation'),
'earliest-optical-limit':('a-and-b-context','cannot be treated')}
for k,(sid,fragment)in facts.items():
 m=ms['char-'+k];check('char-'+k+' source qualitative observation and scope',m['sample_id']==sid and fragment in m['value']['value']and bool(m['evidence']))
check('All characterization units explicitly reviewed',len(expected)+len(facts)==53 and set(ms)=={'char-'+x for x in [*expected,*facts]})
for p in c['products']:
 if 'model'in p['sample_id']or p['sample_id']=='pretreatment-context':check(p['sample_id']+' is not physical experiment',p['composition']['value']is None and p['phase']['value']is None and 'not a physical product'in' '.join(p['notes']))
check('Common measurements not cloned to a/b',all(ms['char-'+x]['sample_id']=='a-and-b-context'for x in ['host-wet-diameter','lamp-power','xrd-radiation','l-definition']))
check('Plateau remains upper bound','upper_bound'in ms['char-sample-b-plateau']['property']and'upper-time bound'in ms['char-sample-b-plateau']['value']['qualifier'])
check('48h continuation not exact completion','not a known completion time'in ms['char-sample-a-continuation']['value']['qualifier'])
check('Lognormal SD unit unassigned','Unit not stated'in ms['char-a-surface-hist-sd']['value']['qualifier'])
check('Absorbance sqrt-time fit is not rate derivative',all(ms['char-'+k]['property']=='absorbance_vs_sqrt_time_slope'for k in ['sample-a-sqrt-time-slope','sample-b-sqrt-time-slope']))
check('HS diffusion inferred not direct measured',all(ms['char-'+k]['value']['status']=='author_derived'for k in ['sample-a-effective-HS-diffusion','sample-b-effective-HS-diffusion']))
check('Donnan printed meV not silently repaired',ms['char-donnan-swelling']['value']['unit']=='meV'and any('meV'in x for x in c['quality']['conflicts']))
check('No unsupported regional phase transfer',all(p['phase']['value']is None for p in c['products']if p['sample_id']in ['a-depth4um','a-depth8um','b-depth9um','b-depth15um','a-surface','b-surface']))
check('Final 11 records,47operations,61measurements',len(records)==11 and sum(len(r['operations'])for r in records.values())==47 and sum(len(r['measurements'])for r in records.values())==61)
findings=[]
def finding(i,title,resolved,detail):findings.append({'id':i,'title':title,'status':'resolved'if resolved else'open','detail':detail})
finding('F01','Precursor-stage material metadata must match actual composition','Cd'not in records['resin-conditioning']['material']['elements']and'S'not in records['cadmium-loading']['material']['elements'],'ConditionedChelex has no CdS; Cd-loadedChelex has no introduced sulfur. Intendedtarget alone cannot repair misleading materialmetadata.')
test=op('cadmium-loading','supernatant-test');states={s['id']:s for s in records['cadmium-loading']['material_states']}
finding('F02','Diagnostic test must consume a separated supernatant aliquot','loaded-suspension'not in test['inputs']and any(i in states and states[i].get('kind')in ['aliquot','fraction']for i in test['inputs']),'The graph must not imply hydrosulfide was added directly to the loadedbeads; unknown aliquotwithdrawal technique/volume stays unknown.')
lamp=op('absorption','acquire')['parameters'];finding('F03','150W is Xe lamp specification',('lamp_power'not in lamp and any(q.get('value')==150 for q in lamp.values()))or'specification'in op('absorption','acquire')['description'].lower(),'Keep lamp source powerdistinctfrom measured sampleirradiance or actual exposure dose.')
sp=st('sample-b','sulfide-stock')['concentrations'];finding('F04','Sampleb sulfide feed inherits analogous procedure',all(sp[k]['status']=='inherited'for k in ['molarity','solution_volume']),'Sourceb explicitlyinherits sample-a feed, while10mL0.5Mpretreatment,10min,2h,2days are directlyreported for b.')
finding('F05','Do not assert unreported powder specimen preparation','powder'not in op('xrd','acquire')['label'].lower(),'XRDacquisitiongiven but specimengeometry/mountnot reported.')
finding('F06','Specific notes need their actual page locators',all(evhas(mat(k,'na2s'),1)for k in ['sample-a','sample-b'])and evhas(op('absorption','time-readout'),6),'Note15 aqueousspecies p1; Note27 earlytimeexciton caveat p6.')
finding('F07','Cited Na diffusion association must preserve source sentence','Chelex 100'in ms['char-na-diffusion']['conditions']and 'Dowex A-1'in ms['char-na-diffusion']['conditions']and 'another resin'not in ' '.join(c['quality']['conflicts']),'The numeric 1.2e-7 cm2/s appears with Chelex 100; Dowex A-1 is described as similar. It remains a cited Na+ value, not a directly measured HS- coefficient or a new physical sample.')
finding('F08','Characterization lamp basis is hardware specification',ms['char-lamp-power']['value']['basis']=='hardware_specification','150 W identifies the Xe lamp hardware rating, not sample irradiance, dose or an independently measured operating condition.')
out={'status':'passed'if all(c['passed']for c in checks)and not any(f['status']=='open'for f in findings)else'must_fix','source_id':'yao1998','scope':'Independent source-to-eleven-record scientific audit: nine recipe/procedure records, electrolyte comparisons and all 53 characterization rows. Seven supplied main pages read text and visually; no repeated unchanged PDF audit. Reader rendering and publication remain root responsibilities.','source_audit_sha256':sha(B/'source-audit.json'),'characterization_draft_sha256':sha(B/'characterization-draft.json'),'records':[{'record_id':r['record_id'],'basename':r['record_id']+'.json','sha256':sha(B/'canonical-drafts'/(r['record_id']+'.json'))}for r in records.values()],'record_count':len(records),'operation_count':sum(len(r['operations'])for r in records.values()),'measurement_count':sum(len(r['measurements'])for r in records.values()),'check_count':len(checks),'checks':checks,'findings':findings,'open_findings':[f for f in findings if f['status']=='open'],'scope_limits':['All 144 source units independently inventoried. Canonical records intentionally preserve selected recipe/measurement/context facts; models, figures, intuition and reference details also require the public reader crosswalk.','SI not located or verified.','No phase/size in synthesis intended target; molecular host and composite composition remain distinct.','No training, publication or whole-corpus completion claim.']}
(B/'canonical-records-audit.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
(B/'canonical-records-audit.md').write_text('# Independent Yao canonical audit\n\nStatus: **'+out['status']+'**. All 11 records: 47 operations, 61 measurement entries including all 53 characterization rows; '+str(len(checks))+' bounded checks.\n\n'+ '\n'.join('- '+f['id']+' '+f['status']+': '+f['title']+'. '+f['detail']for f in findings)+'\n\nAll seven supplied main pages previously read in text and visually. SI remains unverified. Models, cited values, regional cohorts, broad a/b context, apparatus specifications, fitted sizes and measurement uncertainty are kept distinct. No reader, training or publication promotion. Exact record hashes saved in JSON.\n',encoding='utf8')
print(json.dumps({'status':out['status'],'checks':len(checks),'failed_checks':[c for c in checks if not c['passed']],'open_findings':out['open_findings']},indent=2))
