from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
B=Path(__file__).resolve().parent;V=B/'visuals'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
entries=read(V/'registry-additions.json')['entries'];by={e['id']:e for e in entries};C=[]
def ck(n,v,d=''):C.append({'check':n,'passed':bool(v),'detail':d})
spec=['nanocrystal-specimen','unannealed-specimen']+[f'anneal-{t}-specimen' for t in [600,700,800,900,1000]]+['bulk-specimen','ground-bulk-specimen','erbium-series-specimens']
forms={'lanthanum-oxide':'La2O3','ytterbium-oxide':'Yb2O3','erbium-oxide':'Er2O3','molybdenum-trioxide':'MoO3','ammonium-molybdate':'(NH4)2MoO4','nitric-acid':'HNO3','stock-a':None,'stock-b':None,**{s:'La2(MoO4)3:Yb,Er' for s in spec}}
counts={'lanthanum-oxide':{'La':2,'O':3},'ytterbium-oxide':{'Yb':2,'O':3},'erbium-oxide':{'Er':2,'O':3},'molybdenum-trioxide':{'Mo':1,'O':3},'ammonium-molybdate':{'N':2,'H':8,'Mo':1,'O':4},'nitric-acid':{'H':1,'N':1,'O':3}}
ck('Exactly18 source references',len(entries)==18 and set(by)=={'identity-yi-'+k for k in forms});assets={};texts={}
for k,f in forms.items():
 e=by['identity-yi-'+k];p=e['provenance'];path=V/e['svgPath'];assets[e['svgPath']]=sha(path);xml=ET.fromstring(path.read_text(encoding='utf8'));texts[k]=' '.join(xml.itertext())
 ck(k+'/formula or unknown stock composition',e['formula']==f);ck(k+'/source identity',p['sourceDoi']=='10.1021/cm0115416' and p['sourceSha256']=='6438ee53b3fffb86f5e36508f265041d9235b8ee9f3e20dd99d46aae91c68a57')
 ck(k+'/no measured geometry or training',p['measuredCoordinates'] is False and p['eligible_training'] is False);ck(k+'/no unperformed database lookup',e['pubchemCid'] is None)
 ck(k+'/SVG exact hash',assets[e['svgPath']]==e['assetHashes']['svgPath']);ck(k+'/no atomic models',e['model2dPath'] is None and e['model3dPath'] is None);ck(k+'/no invented functional groups',e['functionalGroups']==[])
 if k in counts:
  ck(k+'/formula-unit count',p['atomCountIllustration']==counts[k])
  for atom,n in counts[k].items():ck(k+'/'+atom+'/actual atom glyph count',sum(t.text==atom for t in xml.iter() if t.tag.endswith('text'))==n)
  ck(k+'/no bond illustration',not any(t.tag.endswith('line') or t.tag.endswith('path') for t in xml.iter()))
  if k.endswith('oxide') or k=='molybdenum-trioxide':ck(k+'/oxide molecule not assigned','not a discrete oxide molecule' in e['caption'])
for k in spec:
 e=by['identity-yi-'+k];ck(k+'/nominal not atomic model','nominal' in e['caption'] and 'not a TEM reconstruction' in e['caption'] and 'not generalized to every specimen' in e['caption'])
for t in [600,700,800,900,1000]:ck(str(t)+'/correct specimen hold',f'{t} °C · 5 h' in texts[f'anneal-{t}-specimen'])
ck('Separate1200 air bulk','1200 °C · 5 h in air' in texts['bulk-specimen'])
ck('Ground bulk has no invented nanodiameter','does not establish a nanoscale size' in by['identity-yi-ground-bulk-specimen']['caption'])
ck('900 aggregation qualifier','aggregation at900 °C' in by['identity-yi-anneal-900-specimen']['caption'] and 'does not supply aggregate dimensions' in by['identity-yi-anneal-900-specimen']['caption'])
ck('Er series markers preserve missing6',all(x in texts['erbium-series-specimens'] for x in ['1%','2%','3%','4%','5%','7%']) and 'no6%' in by['identity-yi-erbium-series-specimens']['caption'])
ck('Ammonium/molybdate groups',by['identity-yi-ammonium-molybdate']['provenance']['groupCounts']=={'NH4':2,'MoO4':1})
ck('Mass amount conflict retained','1.961 g and 9.37 mmol' in texts['ammonium-molybdate'] and 'neither is repaired' in by['identity-yi-ammonium-molybdate']['caption'])
ck('Nitric acid speciation not prescribed','does not prescribe an undissociated molecule' in by['identity-yi-nitric-acid']['caption'])
for k in ['stock-a','stock-b']:ck(k+'/water amount and stir', '30 mL deionized water · stir 1 h' in texts[k] and by['identity-yi-'+k]['formula'] is None)
ck('A residue identity unresolved','nitrate/hydration speciation' in by['identity-yi-stock-a']['caption'])
ck('B molarity unrepaired','neither a corrected mole amount nor a repaired molarity' in by['identity-yi-stock-b']['caption'])
for f in read(V/'asset-manifest.json')['files']:ck('Manifest '+f['path'],sha(V/f['path'])==f['sha256'])
manual=['All18 registry entries/captions and all three complete contact sheets were actually read/viewed. Actual SVG formula glyph counts and hashes independently checked. Four oxide powders, nitric acid and ammonium molybdate retain literal source formula identities, without fabricated lattice or aqueous species.','Ammonium molybdate contains exactly two N, eight H, one Mo and four O glyphs, grouped as two NH4 and one MoO4 composition units. They are explicitly group counts, not a bonded molecular model or measured salt packing. Printed1.961 g and9.37 mmol remain unresolved.','Nitric acid composition is illustrative and does not assert its undissociated fraction. StockA retains acid dissolution/evaporation/redissolution and unknown nitrate hydration; stockB retains salt ambiguity and added water rather than corrected final molarity.','Ten specimen/reference cards distinguish preanneal powder, five temperature endpoints,1200 °C bulk, ground bulk and the Er-concentration series.900 °C aggregation and1000 °C bulk-like outcome are qualitative illustrations with no interpolated size. The same nominal host label does not assign verified dopant occupancies or the800 °C phase to all specimens.','No new molecular conformer or crystalline coordinate model supplied. Existing water and final record/product bindings are audited separately. No Site mutation or browser verification claimed.']
fail=[x for x in C if not x['passed']]
out={'status':'passed_source_and_asset_audit_bindings_separate' if not fail else 'failed','source_id':'yi2002','source_sha256':'6438ee53b3fffb86f5e36508f265041d9235b8ee9f3e20dd99d46aae91c68a57','source_audit_sha256':sha(B/'source-audit.json'),'registry_sha256':sha(V/'registry-additions.json'),'asset_manifest_sha256':sha(V/'asset-manifest.json'),'entry_count':18,'asset_hashes':assets,'visual_coverage':[{'path':str(V/'review'/f'molecular-contact-{i}.png'),'sha256':sha(V/'review'/f'molecular-contact-{i}.png'),'actually_viewed':True} for i in range(1,4)],'check_count':len(C),'checks':C,'failures':fail,'manual_review':manual,'limits':['Formula/identity/schematic audit; reused water and bindings separate.','No external database lookup or source atomic-coordinate model supplied.'],'site_mutated':False}
(B/'molecular-source-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'molecular-source-audit.md').write_text('# Yi2002 molecular identity audit\n\n'+out['status']+f'; {len(C)} checks, {len(fail)} failures.\n\n'+'\n\n'.join(manual)+'\n\nRegistry SHA256 `'+out['registry_sha256']+'`.\n',encoding='utf8')
print(json.dumps({'status':out['status'],'registry_sha256':out['registry_sha256'],'checks':len(C),'failures':fail}))

