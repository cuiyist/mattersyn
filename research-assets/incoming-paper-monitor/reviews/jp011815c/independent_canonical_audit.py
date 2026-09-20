"""Independent checks transcribed from the eight inspected Shah source pages.
Private audit only. Does not import the record builder or mutate its outputs.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import json, hashlib, math, re
B=Path(__file__).resolve().parent
def read(p): return json.loads(p.read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d): (B/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
checks=[]
def check(name,actual,expected=True):
 if isinstance(actual,set):actual=sorted(actual)
 if isinstance(expected,set):expected=sorted(expected)
 checks.append({'check':name,'passed':actual==expected,'actual':actual,'expected':expected})
records={p.stem:read(p) for p in sorted((B/'canonical-drafts').glob('*.json'))}
def R(k):return records['shah-2001-'+k]
def ops(k):return {x['id']:x for x in R(k)['operations']}
def ms(k):return {x['id']:x for x in R(k)['measurements']}
def scalar(k,op,name,value,unit):
 q=ops(k)[op]['parameters'][name]
 check(k+'/'+op+'/'+name,(q['value'],q['unit']),(value,unit))
def metric(k,name,value,unit=None):
 q=ms(k)[name]['value'];check(k+'/measurement/'+name,(q['value'],q.get('unit')),(value,unit))
table=[('a',1.8,14.9,60,39,18,46),('b',2.2,10.3,90,26,11,45),('c',2.9,8.2,70,50,23,45),('d',3.4,6.0,80,57,33,57),('e',3.4,5.7,90,55,27,49),('f',3.4,6,100,59,31,52),('g',3.6,5.8,70,56,22,40),('h',3.9,6.4,70,69,34,49),('i',4.9,11,70,107,40,38)]
for label,c,ratio,t,d,sd,pct in table:
 k='ag-'+label
 for op,p,v,u in [('load','precursor_concentration',c,'mM'),('inject','thiol_to_precursor_molar_ratio',ratio,'mol/mol'),('condition','temperature',t,'degC'),('hold','temperature',t,'degC'),('condition','pressure',276,'bar'),('hold','pressure',276,'bar'),('hold','duration',3,'h'),('fill','initial_pressure',138,'bar'),('fill','initial_temperature',20,'degC')]:scalar(k,op,p,v,u)
 for name,v,u in [('diameter',d,'angstrom'),('diameter-standard-deviation',sd,'angstrom'),('relative-standard-deviation',pct,'%')]:metric(k,name,v,u)
 check(k+'/same-table-and-histogram-sample',all(m['sample_id']==k for m in R(k)['measurements']))
 check(k+'/explicit-table-link',R(k)['products'][0]['recipe_link'],'explicit')
 check(k+'/no-typical-dose-transfer',set(ops(k)['inject']['parameters']),{'thiol_to_precursor_molar_ratio'})
 check(k+'/no-assigned-typical-fill-volume',set(ops(k)['fill']['parameters']),{'initial_pressure','initial_temperature'})
 check(k+'/body-table-conflicts-preserved',len(R(k)['quality']['conflicts']),4)
for k,c,ratio in [('ir',3.3,7.6),('pt',3.6,6.6)]:
 for op,p,v,u in [('load','precursor_concentration',c,'mM'),('inject','thiol_to_precursor_molar_ratio',ratio,'mol/mol'),('condition','temperature',80,'degC'),('condition','pressure',276,'bar'),('hold','temperature',80,'degC'),('hold','pressure',276,'bar')]:scalar(k,op,p,v,u)
 for op,p in [('fill','initial_pressure'),('fill','initial_temperature'),('hold','duration')]:check(k+'/'+op+'/'+p+'/inheritance',ops(k)[op]['parameters'][p]['status'],'inferred')
 check(k+'/no-size-label',not any(m['property']=='diameter' for m in R(k)['measurements']))
 check(k+'/partial-task-only',R(k)['quality']['requested_tasks'],['precursor_selection','partial_protocol'])
 metric(k,'tem-scale',10,'nm')
metric('ir','tem-inset-scale',5,'nm')
pt=R('pt')['materials'][0]
check('pt/unresolved-formula',pt['formula'],None)
check('pt/as-printed-name','cyclopentadiene' in pt['name'])
check('ir/identity-formula',R('ir')['materials'][0]['formula'],'C14H19Ir')
k='ag-typical-framework'
for op,n,lo,hi,u in [('load','precursor_mass',5.9,16,'mg'),('fill','co2_fill_volume',14,18,'mL'),('inject','thiol_mass',162,324,'mg'),('condition','temperature',60,100,'degC')]:
 q=ops(k)[op]['parameters'][n];check(k+'/'+n+'/range',(q['value'],q['minimum'],q['maximum'],q['unit']),(None,lo,hi,u))
for op,n,v,u in [('fill','cell_working_volume',27,'mL'),('inject','hydrogen_mass',6.22,'mg'),('inject','thiol_loop_capacity_option_1',100,'uL'),('inject','thiol_loop_capacity_option_2',200,'uL'),('inject','hydrogen_loop_capacity',800,'uL')]:scalar(k,op,n,v,u)
metric(k,'cell-internal-diameter',1.75,'cm');metric(k,'darkest-time',1,'h')
check(k+'/darkening-approximate',ms(k)['darkest-time']['value']['approximate'])
check(k+'/framework-not-run',R(k)['record_type'],'procedure')
check('recovery/order',list(ops('recovery')),['cool','depressurize','vent','collect','precipitate','redisperse'])
check('recovery/retains-precipitate',ops('recovery')['precipitate']['retained_fraction'],'nanocrystal-precipitate')
check('recovery/no-invented-quantities',all(not o['parameters'] for o in R('recovery')['operations']))
for op,n,v,u in [('deposit','grid_mesh',200,'mesh'),('image','accelerating_voltage',200,'kV'),('image','instrument_point_resolution',1.7,'angstrom')]:scalar('tem-eds',op,n,v,u)
q=ops('tem-eds')['size']['parameters']['minimum_particles_per_sample']
check('tem/inclusive-at-least-400',(q['value'],q['minimum'],q.get('minimum_exclusive',False)),(None,400,False))
for name,v in [('fig2-a-scale',50),('fig2-b-scale',40),('fig2-c-scale',5),('fig11-a-scale',5),('fig11-b-scale',5),('fig11-c-scale',5),('fig11-d-scale',6)]:metric('ag-structure',name,v,'nm')
metric('ag-structure','interparticle-separation',20,'angstrom')
metric('optical-comparison','i-peak',400,'nm');metric('optical-comparison','i-diameter-context',59,'angstrom');metric('optical-comparison','ii-diameter-context',55,'angstrom')
check('optical/separate-cohorts',[p['sample_id'] for p in R('optical-comparison')['products']],['spectrum-i','spectrum-ii','spectrum-iii'])
check('optical/no-auto-table-join',all(p['recipe_link']=='general_context' for p in R('optical-comparison')['products']))
metric('solvation','hydrocarbon-spacing',10,'angstrom');metric('solvation','fluorinated-shortening',20,'%')
for name,v,u in [('frequency',3e15,'s^-1'),('silver-vacuum',2.2,'eV'),('silver-co2',1.4,'eV'),('silver-acetone',.93,'eV'),('hamaker-temperature',25,'degC'),('critical-temperature',31,'degC'),('critical-pressure',71,'bar'),('mu1',1.48,'dimensionless'),('mu3',.82,'dimensionless'),('model-sticking',1,'dimensionless'),('global-spread',47,'%'),('stronger-attraction',50,'%')]:metric('growth-model',name,v,u)
for name,bound,v in [('mu1-threshold','minimum',1.25),('mu3-threshold','maximum',.905)]:
 q=ms('growth-model')[name]['value'];check('growth-model/'+name+'/strict-bound',(q['value'],q[bound],q.get(bound+'_exclusive')),(None,v,True))
check('growth/no-extra-runs',R('growth-model')['record_type'],'observation')
check('growth/sphere-assumption','spherical' in ops('growth-analysis')['volume']['description'])
check('growth/source-integral-conflict','printed' in ms('growth-model')['psi2']['value']['value'])
for rid,r in records.items():
 check(rid+'/no-unreported-atomic-structure',r['structure_assets'],[])
 check(rid+'/no-physical-batch-invention',r['lineage']['batch_id'],None)
 check(rid+'/si-unknown','absence' in r['sources'][0]['si_status'])
 for m in r['materials']:
  if m['id'] in ['co2','hydrogen'] and 'supplier_purity' in m['quantities']:
   q=m['quantities']['supplier_purity'];check(rid+'/'+m['id']+'/strict-purity',(q['value'],q['minimum'],q.get('minimum_exclusive')),(None,99.99 if m['id']=='co2' else 99.999,True))
 known={p['sample_id'] for p in r['products']}
 for m in r['measurements']:
  check(rid+'/'+m['id']+'/local-sample-link',m['sample_id'] in known)
  check(rid+'/'+m['id']+'/source-evidence',bool(m['evidence']) and all(x['source_id']=='shah2001' for x in m['evidence']))
check('record-count',len(records),19)
check('operation-count',sum(len(r['operations']) for r in records.values()),74)
check('measurement-count',sum(len(r['measurements']) for r in records.values()),111)
check('material-binding-count',sum(len(r['materials']) for r in records.values()),99)
check('named-source-experiments',sum(r['record_type']=='literature_protocol' for r in records.values()),11)
semantic=[
 'All source-linked scalar and text measurement fields, material identities/roles, apparatus descriptions, operation order and stated missingness were substantively compared with the independently read eight-page source inventory. Automated checks below are supplementary, not a substitute for that reading.',
 'Nine Ag labels A–I are source experiments; Ir and Pt give two additional named conditions. Four procedures and four context observations do not create extra synthesis runs.',
 'A–I values preserve each printed mean, standard deviation and percentage; no forced arithmetic reconciliation. All nine share the common Ag method but lack row-specific absolute masses and final reactor volume.',
 'Ir/Pt common fill/hold parameters are inferred inheritance. Their directly reported concentrations, thiol ratios, 80 °C and 276 bar remain reported. Neither has an invented mean size. Pt precursor identity stays unresolved.',
 'The 27 mL working cell, 14–18 mL fill, two alternative thiol loop capacities and 800 µL hydrogen loop are distinct bases. No per-row dosing is back-calculated. Simultaneous thiol/H2 introduction, 3 h hold and approximate 1 h darkening are distinct.',
 'Acetone collection, heptane precipitation, retained precipitate and acetone redispersion are correct. No centrifugation, drying, isolated yield, solvent quantity or stock synthesis is invented. Alternative redispersants are observations rather than compulsory additions.',
 'Microscope voltage, point resolution, grid mesh and sample-count lower bound are acquisition details, not material dimensions. Image scale bars remain image metadata.',
 'Figures 2/6/11 are unassigned Ag cohorts; {111} fringes and hexagonal particle arrays do not establish a refined unit cell or hcp Ag phase. Figure 8 is linked by the Results text only to its respective metal.',
 'Figure 7 uses three separate synthesis/ligand/measurement-solvent contexts. The current 59 Å optical cohort is not automatically experiment F; the prior 55 Å comparator is not experiment E. Prior comparisons do not become current recipe outcomes.',
 'Negative post-recovery CO2 redispersion and positive in-reactor stabilization are both retained. C10 ligand prior performance, octanethiol/hexanethiol comparisons, ethanol discussion and future suggestions are context rather than current additions.',
 'All three force equations, distribution definitions and moment ratios were read against source. Model 25 °C/phase conflict, 20% chain-shortening claim and printed integral differential mismatch remain explicit; no numerical model is represented as measured atomic or force data.',
 'Growth claims retain author interpretation and assumptions: coagulation is inferred, most observed Ag is single-crystalline, some images are polycrystalline, sticking probability one is theory, and cited 70 Å gold realignment is a personal communication.',
 'Canonical records intentionally do not duplicate all 48 bibliography entries, all figure axis metadata or general introduction statements. Their complete preservation is in the source inventory and pending reader audit; canonical completeness alone does not prove reader completeness.'
]
failures=[c for c in checks if not c['passed']]
report={'schema':'mattersyn-independent-canonical-audit-1','source_id':'shah2001','doi':'10.1021/jp011815c','reviewer':'independent_source_auditor','checked_utc':datetime.now(timezone.utc).isoformat(),'status':'passed_with_source_limits' if not failures else 'failed','source_sha256':'2e6310ab5f5c6102ffa46e91dc3ccc2a180e6a6d17fd6a82ef448867edd79967','source_inventory_sha256':sha(B/'source-audit.json'),'record_hashes':{rid:sha(B/'canonical-drafts'/(rid+'.json')) for rid in records},'record_count':19,'operation_count':74,'measurement_count':111,'material_binding_count':99,'reviewed_main_pages':list(range(1,9)),'semantic_review':semantic,'check_count':len(checks),'failure_count':len(failures),'checks':checks,'failures':failures,'publication_or_integration_verified':False,'limits':['No supplied SI located or verified; absence is not proven.','No external cited paper inspected; reference claims remain attributed.','Reader, molecular binding, browser and published website audits are separate.']}
save('canonical-records-audit.json',report)
(B/'canonical-records-audit.md').write_text('# Independent canonical audit: Shah et al. (2001)\n\nStatus: '+report['status']+'. All 19 records, 74 operations, 111 measurements and 99 material bindings reviewed; '+str(len(checks))+' supplementary checks, '+str(len(failures))+' failures.\n\n'+'\n\n'.join(semantic)+'\n\nExact canonical hashes and checks are in canonical-records-audit.json. This report does not assert integration or publication.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'failures':failures,'audit_sha256':sha(B/'canonical-records-audit.json')}))
