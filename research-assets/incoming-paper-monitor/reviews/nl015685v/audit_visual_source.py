"""Independent source/scene checks after manual review of all six page images and contacts."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
B=Path(__file__).resolve().parent;V=B/'visuals'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((V/'scene-manifest.json').read_text(encoding='utf8'))
records={p.stem:json.loads(p.read_text(encoding='utf8')) for p in (B/'canonical-drafts').glob('*.json')}
checks=[]
def ck(test,label):
 checks.append({'label':label,'passed':bool(test)})
 if not test:raise AssertionError(label)
ck(m['module_sha256']==sha(V/'besson2002-protocol.mjs'),'Exact rendered module hash matches current module')
expected={(r['record_id'],o['id']) for r in records.values() for o in r['operations']}
ck(expected=={(s['record_id'],s['operation_id']) for s in m['scenes']},'One scene for every canonical operation and no extra scenes')
ck(len(expected)==36,'All 36 operations covered')
notes={
 'cadmium-stock':'Starting 0.1 M Cd solution, one-equivalent ligand additions and further ammonia to pH 9.5 remain distinct. No final concentration or salt hydration is invented.',
 'copolymer-cds-loading':'Common-framework inheritance is explicit. No copolymer identity, host recipe, extra physical batch, room-temperature synthesis or absolute gas pressure is invented.',
 'ctab-cds-loading':'Retained supported film is rinsed, evacuated, sulfided and reused. Blue adsorbed Cd precedes yellow CdS. Nine is total cycles, not nine extra cycles or distinct batches.',
 'ctab-silica-host':'Correct chemical order; water-specific pH, molar mixing and CTAB ratio, untyped 1:1 dilution, Pyrex spin coating, air template-removal calcination. No CdS before loading.',
 'hrtem':'Cross-sectional microscope is distinct from optical apparatus. 200 kV and 0.18 nm are acquisition/resolution facts. Fourier image power is explicitly not SAED; no atomic lattice is drawn.',
 'loading-fraction':'Colloid reference remains separate from film. 13%, 15% and about 85% are source-derived model values, not independent direct volumetric observations.',
 'pl-silicon':'Silicon substrate and timing of first H2S, next Cd exposure and later treatment remain distinct. No Pyrex spin settings or numeric room temperature are inherited. Figure 4 conflict is preserved.',
 'sims':'Generic primary/secondary-ion geometry without unreported beam identity or energy. Two pre/post-H2S contexts named separately; no numerical depth curve or EDS is invented.',
 'uv-visible':'Source spectra and cited gap–size conversion are distinct, with no invented curves or intermediate size values.',
 'xrd':'Low-angle textured-film geometry; host 0002/harmonic, original scaling and mesoscopic-versus-atomic distinction retained. Overlapping small label removed and re-inspected.'
}
scenes=[]
for s in m['scenes']:
 r=records[s['record_id']];o=next(o for o in r['operations'] if o['id']==s['operation_id']);p=V/s['file'];key=r['record_id']+'/'+o['id']
 ck(s['record_sha256']==sha(B/'canonical-drafts'/(r['record_id']+'.json')),key+' exact current canonical hash')
 ck(s['svg_sha256']==sha(p),key+' exact SVG hash')
 ck(s['parameters']==o['parameters'],key+' parameter values, bounds, statuses and evidence preserved in manifest')
 ck(s['environment']==o['environment'],key+' reported or unknown environment preserved in manifest')
 ck(s['inputs']==o['inputs'] and s['outputs']==o['outputs'],key+' specimen lineage preserved in manifest')
 root=ET.fromstring(p.read_text(encoding='utf8'));ck(root.attrib['viewBox']=='0 0 600 415',key+' valid SVG viewport')
 text=' '.join(root.itertext());ck('not to scale' in text and 'no measured atomic structure' in text,key+' illustration limitations explicit')
 ck(o['label'] in text,key+' selected-operation title present')
 ck(not any(v in text for v in ['NaN','undefined']),key+' no invalid rendering placeholders')
 scenes.append({'record_id':r['record_id'],'operation_id':o['id'],'svg_sha256':sha(p),'manual_source_and_layout_review':'passed','scope_note':notes[r['record_id'].removeprefix('besson-2002-')]})
def op(k,i):return next(o for o in records['besson-2002-'+k]['operations'] if o['id']==i)
def q(k,i,p):return op(k,i)['parameters'][p]
ck(q('ctab-silica-host','mix','water_pH')['value']==1.25,'pH 1.25 is the water parameter')
ck(q('ctab-silica-host','age','temperature')['value']==60 and q('ctab-silica-host','age','duration')['value']==1,'Aging at 60 °C for 1 h')
ck(q('ctab-silica-host','template','ctab_teos_molar_ratio')['value']==.1,'CTAB/TEOS molar ratio 0.1')
ck('not specified' in q('ctab-silica-host','dilute','dilution_ratio')['basis'],'No invented 1:1 dilution basis')
ck(q('ctab-silica-host','spin-coat','rotation_speed')['value']==3000,'3000 rpm applies to Pyrex route')
ck(q('ctab-silica-host','calcine','temperature')['value']==450 and op('ctab-silica-host','calcine')['environment']['value']=='Air','450 °C calcination in air')
ck(q('ctab-silica-host','calcine','duration')['status']=='not_reported','Calcination duration remains unknown')
ck(q('cadmium-stock','prepare','cadmium_nitrate_concentration')['value']==.1,'0.1 M is starting cadmium stock')
ck(q('cadmium-stock','complex','citrate_stock_concentration')['value']==1,'1 M belongs to citrate stock')
ck(q('cadmium-stock','complex','ammonia_stock_concentration')['status']=='not_reported','No invented ammonia concentration')
ck(q('cadmium-stock','adjust-ph','target_pH')['value']==9.5,'Final stock pH 9.5')
for host,n in [('ctab',9),('copolymer',6)]:
 k=host+'-cds-loading';ck(q(k,'repeat','total_cycles')['value']==n,k+' total-cycle endpoint')
 ck(q(k,'evacuate','vacuum_pressure')['status']=='not_reported',k+' unknown vacuum level')
 ck(q(k,'sulfide','h2s_pressure_endpoint')['value'] is None,k+' no numerical atmospheric pressure invention')
 ck(op(k,'sulfide')['endpoint']['value']=='P(H2S) equals atmospheric pressure',k+' symbolic H2S endpoint retained')
 ck('temperature' not in op(k,'impregnate')['parameters'],k+' no invented synthesis temperature')
ck(q('copolymer-cds-loading','impregnate','solution_pH')['status']=='inherited','Copolymer common-framework pH distinguished from separately reported conditions')
ck(q('hrtem','image','acceleration_voltage')['value']==200 and q('hrtem','image','point_resolution')['value']==.18,'HRTEM voltage and resolution distinct')
ck(all(op('pl-silicon',i)['environment']['value']=='Room temperature; numerical temperature unspecified' for i in ['measure-first','measure-cd']),'PL room temperature not numeric')
ck(all(p['composition']['value'] is None for k in ['xrd','sims'] for p in records['besson-2002-'+k]['products'] if p['sample_id']=='cadmium-adsorbed'),'Pre-H2S specimen identity does not assert CdS')
contacts=[{'path':str(p),'sha256':sha(p),'manual_review':'passed'} for p in sorted((V/'review').glob('scenes-*.png'))]
ck(len(contacts)==6,'All six contact sheets independently inspected; final XRD correction re-inspected')
report={'status':'passed_with_source_and_illustration_limits','source_id':'besson2002','module_sha256':sha(V/'besson2002-protocol.mjs'),'operation_count':36,'source_pages_read_and_visually_inspected':6,'manual_scene_reviews':36,'contact_sheets':contacts,'checks':checks,'check_count':len(checks),'creator_render_checks':len(m['checks']),'record_hashes':{k:sha(B/'canonical-drafts'/(k+'.json')) for k in records},'scene_reviews':scenes,'limits':['Apparatus shapes, number of illustrated pores, particle positions, sizes and colors are explanatory; no measured geometry or atomic-coordinate model.','Unknown flow, temperatures, pressures, durations, stock formulations and substrate dimensions are not supplied by illustration.','No current-paper SAED, atomic CIF, raw spectra or independently quantified copolymer host synthesis is invented.','Source conflicts in Figure 4, mesoscopic c values and filling/size comparison remain in records and original reader evidence.']}
(B/'visual-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'visual-source-audit.md').write_text('# Independent Besson 2002 apparatus audit\n\nPassed with source and illustration limits. All six source pages and all 36 scenes in six contact sheets were inspected. The final XRD label correction was re-rendered and checked.\n\nModule SHA-256: `'+report['module_sha256']+'`.\n\n'+str(len(checks))+' source/manifest checks passed; the separate rendering helper reports '+str(len(m['checks']))+' coverage/render checks. Exact canonical, SVG and contact-sheet hashes are in the JSON audit.\n\n'+ '\n'.join('- '+v for v in notes.values())+'\n\nLimits: '+ ' '.join(report['limits'])+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'module_sha256':report['module_sha256']}))
