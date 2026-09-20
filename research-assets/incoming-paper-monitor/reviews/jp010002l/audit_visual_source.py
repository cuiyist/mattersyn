"""Independent source-semantics checks for the root-authored Braun apparatus module.
Run only after all current contact sheets have been visually inspected.
"""
from pathlib import Path
import json,hashlib,re,xml.etree.ElementTree as ET
B=Path(__file__).resolve().parent;V=B/'visuals';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((V/'scene-manifest.json').read_text(encoding='utf8'))
records={p.stem:json.loads(p.read_text(encoding='utf8')) for p in (B/'canonical-drafts').glob('*.json')}
checks=[]
def ck(v,label):
 checks.append({'check':label,'passed':bool(v)})
 if not v:raise AssertionError(label)
ck(manifest['module_sha256']==sha(V/'braun2001-protocol.mjs'),'Manifest identifies the current module bytes')
ck(len(manifest['scenes'])==45,'All45 source operations are represented')
expected={(r['record_id'],o['id']) for r in records.values() for o in r['operations']}
ck({(s['record_id'],s['operation_id']) for s in manifest['scenes']}==expected,'Exact canonical operation coverage')
svg={}
for s in manifest['scenes']:
 key=(s['record_id'],s['operation_id']);r=records[key[0]];o=next(o for o in r['operations'] if o['id']==key[1]);p=V/s['file'];t=p.read_text(encoding='utf8');tx=' '.join(ET.fromstring(t).itertext());svg[key]=tx
 ck(sha(p)==s['svg_sha256'],'Scene bytes '+str(key))
 ck(sha(B/'canonical-drafts'/(r['record_id']+'.json'))==s['record_sha256'],'Canonical hash '+str(key))
 for name in ['parameters','environment','inputs','outputs','evidence']:ck(s[name]==o[name],name+' correspondence '+str(key))
 ET.fromstring(t);ck('viewBox="0 0 600 415"' in t,'SVG viewport '+str(key))
 ck('no measured atomic structure or experimental signal is simulated' in t,'Illustration label '+str(key))
 ck(not any(x in t.lower() for x in ['heating mantle','hot bath','°c','celsius']),'No invented heating or numeric temperature '+str(key))
 if r['record_type']=='literature_protocol':
  ck(('>Ar</text>' in t or '>Ar flow</text>' in t)==(o['environment']['value']=='Argon'),'Source-selected argon only '+str(key))
  if key[1].endswith('-exchange'):
   ck('Displaced Cd²⁺ stays in solution' in t,'Exchange retains dissolved Cd '+str(key))
   ck('replacement, not an additional deposited layer' in tx,'Exchange distinction '+str(key))
   radii=[]
   for x in [395,535]:
    g=re.search(r'<g transform="translate\('+str(x)+r' 152\) scale\(0?\.75\)">(.*?)</g>',t)
    ck(g is not None,'Layer inset group '+str(key)+' '+str(x))
    radii.append(max(map(float,re.findall(r' r="([0-9.]+)"',g.group(1)))))
   ck(radii[0]==radii[1],'Cation exchange preserves schematic outer radius '+str(key))
  if key[1].endswith('-add-cd'):
   ck(key[0].endswith('-iii') and key[1] in ['c2-add-cd','c3-add-cd'],'Extra Cd only consecutive C stages '+str(key))
   ck('Dose not reported' in t and 'C follows C' in t,'Missing additional Cd dose remains explicit '+str(key))
  if re.match(r'c\d-grow',key[1]):ck('Add one CdS layer' in t and '25 min at pH 7.0' in t,'Source C growth conditions '+str(key))
def g(r,i):return svg[('braun-2001-'+r,i)]
ck('400 nm pump' in g('transient-absorption-acquisition','pump'),'TA pump wavelength')
ck('Femtosecond pulse' in g('transient-absorption-acquisition','pump'),'TA fs pulse distinct from PL pump')
ck('800 nm source' in g('transient-absorption-acquisition','probe') and '450–1050 nm' in g('transient-absorption-acquisition','probe'),'White-light source and range')
ck('Sapphire' in g('transient-absorption-acquisition','probe'),'Sapphire confined to optical probe apparatus')
ck('5 ns · 10 Hz' in g('photoluminescence-acquisition','excite') and 'Third harmonic' in g('photoluminescence-acquisition','excite'),'PL Nd:YAG pump conditions')
ck('440 nm OPO' in g('photoluminescence-acquisition','excite'),'PL excitation wavelength')
ck('90° collection' in g('photoluminescence-acquisition','record'),'PL collection geometry')
ck('not a measured nanocrystal Raman spectrum' in g('photoluminescence-acquisition','subtract'),'Water correction not a material Raman measurement')
ck('Separate water' in g('photoluminescence-acquisition','water-reference'),'Water reference is separate')
ck('not establish one physical batch or a mixture' in g('absorption-acquisition','select-stage'),'Stage/system specimens not mixed')
ck('Second derivative' in g('absorption-acquisition','second-derivative'),'Derivative analysis distinguished from acquisition')
ck('straight lines are visual aids' in g('transient-absorption-acquisition','analyze'),'No mechanistic kinetic-fit assertion')
contacts=[{'path':str(p.relative_to(B)),'sha256':sha(p),'visually_inspected':True} for p in sorted((V/'review').glob('scenes-*.png'))]
report={'status':'passed_with_source_limits','scope':'Independent source and visual audit of the root-authored apparatus module against all four original main pages and the canonical operations. No module edits performed by this reviewer.','source_id':'braun2001','module_path':str(V/'braun2001-protocol.mjs'),'module_sha256':sha(V/'braun2001-protocol.mjs'),'scene_manifest_sha256':sha(V/'scene-manifest.json'),'operation_count':45,'checks':checks,'check_count':len(checks),'contacts':contacts,'scene_hashes':{s['record_id']+'/'+s['operation_id']:s['svg_sha256'] for s in manifest['scenes']},'findings_resolved':['First B schematic originally enlarged the outer radius; root corrected it to show a CdS surface skin replaced by HgS at equal illustrative radius.'],'scientific_limits':['Ring geometry encodes layer sequence only; it is not measured particle morphology, a unit cell, radius calibration or actual atomic structure.','Apparatus geometry is explanatory; no unreported heater, numeric synthesis temperature, counterion, stabilizer dose, gas pressure, gas flow or new separation is asserted.','Canonical adjacent panels retain exact values, approximations and lower bounds; in particular A purge20min differs from each C purge>=20min.','Optical apparatus distinguishes steady-state absorption, PL440nm with Nd:YAG/OPO excitation, and TA400nm/800nm-white-light pump–probe acquisition. No measured signal is synthesized.','No current-source micrograph, measured crystallography or matched SI is supplied.']}
(B/'visual-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(B/'visual-source-audit.md').write_text(f"# Braun 2001 independent apparatus audit\n\nPassed with source limits: {len(checks)} checks, all45 operations and all8 contact sheets reviewed.\n\nModule SHA-256: `{report['module_sha256']}`\n\nThe first-B transition was corrected to show replacement at the same schematic outer radius. Later B preserves outer radius; each C adds one CdS layer, and only the two consecutive-C steps in System III receive unquantified additional Cd2+. Argon appears only in the selected reported atmosphere/purge stages. Optical scenes retain separate PL and transient methods, separate water reference, derivative analysis and source-fit limits.\n\nRings, vessel dimensions and beam geometry are explanatory. No actual atomic structure, measured microscopic image or simulated source spectrum is presented. Canonical conditions, including the ≥20min C purge bound, remain beside the art. Declared-source scope is four supplied main pages; SI availability is unresolved.\n",encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'module_sha256':report['module_sha256']}))
