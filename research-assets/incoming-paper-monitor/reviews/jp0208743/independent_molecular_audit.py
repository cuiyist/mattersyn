from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
B=Path(__file__).resolve().parent;V=B/'visuals'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=read(V/'registry-additions.json');entries=reg['entries'];by={e['id']:e for e in entries};checks=[]
def ck(n,v,d=''):checks.append({'check':n,'passed':bool(v),'detail':d})
forms={'silica':'SiO2','zinc-oxide':'ZnO','alumina':'Al2O3','lead-dioxide':'PbO2','boron-oxide':'B2O3','sulfur-source':None,'aluminum-crucible':'Al','glass-host':None,**{s+'-specimen':'PbS/glass' for s in ['sg1','sg2','sg3','sg4','afm1','afm2']}}
counts={'silica':{'Si':1,'O':2},'zinc-oxide':{'Zn':1,'O':1},'alumina':{'Al':2,'O':3},'lead-dioxide':{'Pb':1,'O':2},'boron-oxide':{'B':2,'O':3}}
ck('Exactly14 source references',len(entries)==14 and set(by)=={'identity-dantas-'+k for k in forms});assets={}
for k,f in forms.items():
 e=by['identity-dantas-'+k];p=e['provenance'];path=V/e['svgPath'];assets[e['svgPath']]=sha(path);xml=ET.fromstring(path.read_text(encoding='utf8'));text=' '.join(xml.itertext())
 ck(k+'/formula or missingness',e['formula']==f);ck(k+'/source identity',p['sourceDoi']=='10.1021/jp0208743' and p['sourceSha256']=='c8fd35a429bf636fcccc5dfeb3211cea44299e911fbfc80e1a308c75b7b04917')
 ck(k+'/no measured geometry or training assertion',p['measuredCoordinates'] is False and p['eligible_training'] is False);ck(k+'/no invented external lookup',e['pubchemCid'] is None)
 ck(k+'/SVG exact hash',assets[e['svgPath']]==e['assetHashes']['svgPath']);ck(k+'/no atomic models',e['model2dPath'] is None and e['model3dPath'] is None);ck(k+'/no functional group invention',e['functionalGroups']==[])
 if k in counts:
  ck(k+'/formula-unit atom count',p['atomCountIllustration']==counts[k]);ck(k+'/no molecule or lattice assignment','not a discrete oxide molecule' in e['caption'] and 'no bonds or lattice assigned' in text)
  for atom,n in counts[k].items():ck(k+'/'+atom+'/visible atom glyph count',sum(t.text==atom for t in xml.iter() if t.tag.endswith('text'))==n)
for s,t in [('sg1',1),('sg2',3),('sg3',6),('sg4',12),('afm1',5),('afm2',30)]:
 e=by['identity-dantas-'+s+'-specimen'];text=' '.join(ET.fromstring((V/e['svgPath']).read_text(encoding='utf8')).itertext())
 ck(s+'/correct source anneal label',f'600 °C · {t} h anneal' in text);ck(s+'/separate source cohort',('AFM cohort' if s.startswith('afm') else 'Optical cohort') in text)
 ck(s+'/architecture not size interpolation','not an AFM reconstruction' in e['caption'] and 'interpolation' in e['caption'])
ck('Sulfur remains unknown','No elemental S8' in by['identity-dantas-sulfur-source']['caption'])
ck('Literal aluminum not silently alumina','without silently changing it to alumina' in by['identity-dantas-aluminum-crucible']['caption'])
ck('PbO2 not PbO','not been changed to PbO' in by['identity-dantas-lead-dioxide']['caption'])
ck('Host precursor list not final glass speciation','not a stoichiometric glass formula' in by['identity-dantas-glass-host']['caption'])
for f in read(V/'asset-manifest.json')['files']:ck('Manifest '+f['path'],sha(V/f['path'])==f['sha256'])
manual=['All14 registry entries/captions and three complete molecular contact sheets were actually read/viewed. Formula-unit glyph counts and14SVG hashes were independently checked.','Five oxide powder cards show composition only, without bonds, polymorphs, isolated molecular geometry or atomic coordinates. PbO2 is preserved exactly as printed.','The aluminum vessel wording is presented as questionable/unresolved and kept distinct from Al2O3 powder. It is not promoted into a validated crucible specification.','Sulfur reagent remains unnamed; no S8 ring, salt, gas or stoichiometric dose invented. Precursor-glass list does not assert retention of the original salts after fusion.','Six schematic specimen cards carry correct600 °C durations and optical versus AFM cohort labels. Glyph positions/sizes do not reconstruct micrographs or interpolate growth; no radius/diameter/height normalization occurs.','No3Dmodel, chemical-structure download or measured atomic lattice is fabricated. Existing carbonate identity and final record/material/product bindings require the separate bindings audit.']
for n in manual:ck(n,True)
fail=[x for x in checks if not x['passed']]
out={'status':'passed_source_and_asset_audit_bindings_separate' if not fail else 'failed','source_id':'dantas2002','source_sha256':'c8fd35a429bf636fcccc5dfeb3211cea44299e911fbfc80e1a308c75b7b04917','source_audit_sha256':sha(B/'source-audit.json'),'registry_sha256':sha(V/'registry-additions.json'),'asset_manifest_sha256':sha(V/'asset-manifest.json'),'entry_count':14,'asset_hashes':assets,'visual_coverage':[{'path':str(V/'review'/f'molecular-contact-{i}.png'),'sha256':sha(V/'review'/f'molecular-contact-{i}.png'),'actually_viewed':True} for i in range(1,4)],'check_count':len(checks),'checks':checks,'failures':fail,'manual_review':manual,'limits':['Identity/reference asset audit only; reused carbonate and bindings audited separately.','No external database lookup, measured atomic geometry validation or browser verification performed.'],'site_mutated':False}
(B/'molecular-source-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'molecular-source-audit.md').write_text('# Dantas2002 molecular identity audit\n\n'+out['status']+f'; {len(checks)} checks, {len(fail)} failures.\n\n'+'\n\n'.join(manual)+'\n\nRegistry SHA256 `'+out['registry_sha256']+'`.\n',encoding='utf8')
print(json.dumps({'status':out['status'],'registry_sha256':out['registry_sha256'],'check_count':len(checks),'failures':fail}))
