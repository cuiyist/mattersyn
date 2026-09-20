"""Source-verified private draft corrections authorized by parent; no Site writes."""
from pathlib import Path
import json, hashlib
B=Path(__file__).resolve().parent
P=B/'build_records.py'
text=P.read_text(encoding='utf-8')
changes=[]
initial=[{'record_id':p.stem,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((B/'canonical-drafts').glob('*.json'))]
def replace(old,new,finding):
 global text
 assert text.count(old)==1,(finding,text.count(old),old[:90])
 text=text.replace(old,new)
 changes.append({'finding_id':finding,'before':old,'after':new})
replace("description='Recover by methanol precipitation; final size-selective precipitation is intended to reduce separate small ZnS particles. Solvent volume, cycle count and collection settings not supplied.',retained=True)","description=('Recover by methanol precipitation; final size-selective precipitation is intended to reduce separate small ZnS particles. Solvent volume, cycle count and collection settings not supplied.' if iszn else 'Methanol recovery is inherited through the same-basic-procedure statement; CdS-specific workup is not independently detailed. The rationale of reducing separate ZnS nuclei belongs only to the ZnS route and is not assigned to this CdS product.'),retained=True)",'D01')
replace("description='Transfer hexane seed dispersion by syringe; approximate particle amount 0.1–0.4 umol. Hexane volume unreported.')", "description='Transfer hexane seed dispersion by syringe; approximate particle amount 0.1–0.4 umol. Hexane volume unreported.')\n if not iszn:r['operations'][-1]['parameters']['input_core_diameter']=Q(u='angstrom',e=CDS,minimum=33.5,maximum=35,basis='Input CdSe seed diameter explicitly stated in the CdS comparison; not final composite size')",'D02')
replace("V(r,'bare-se-cd','bare','se_to_cd_atomic_ratio',Q(.87,'',e=e,approximate=True),'XPS with finite-particle escape-depth correction',e,'Bare particle analysis; association to a unique original synthesis run is unresolved.')", "P(r,'xps-bare-context','General bare CdSe XPS composition context','CdSe',e=e,notes=['XPS examines multiple approximately33 and40angstrom core samples. No exact physical identity with the Table1 bare aliquot is established. The same source baseline also appears in the air-exposure observation record; it is not an independent replicate.'])\nV(r,'bare-se-cd','xps-bare-context','se_to_cd_atomic_ratio',Q(.87,'',e=e,approximate=True),'XPS with finite-particle escape-depth correction',e,'General bare particle analysis; exact core size and identity with Table1 aliquot unresolved.')\nfor xid,cov in [('xps-065-context',.65),('xps-13-context',1.3),('xps-26-context',2.6)]:P(r,xid,f'XPS context with {cov}monolayers ZnS',e=e,notes=['Source-reported coverage designation in the XPS study of multiple approximately33 and40angstrom cores. Not asserted to be the physical Table1/TEM/optical aliquot of equal nominal coverage.'])",'D03')
replace("for lab in ['ml-13','ml-26']:V(r,lab+'-zn-auger',lab,'zinc_auger_parameter'", "for lab,xid in [('ml-13','xps-13-context'),('ml-26','xps-26-context')]:V(r,lab+'-zn-auger',xid,'zinc_auger_parameter'",'D03')
replace("for lab,ratio in [('ml-065',1.28),('ml-26',1.60)]:V(r,lab+'-xps-auger-ratio',lab,'xps_auger_intensity_ratio'", "for lab,xid,ratio in [('ml-065','xps-065-context',1.28),('ml-26','xps-26-context',1.60)]:V(r,lab+'-xps-auger-ratio',xid,'xps_auger_intensity_ratio'",'D03')
replace("p=P(r,'bare-'+lab,'BareCdSe '+lab+' exposure state','CdSe',e=e,notes=['Same source bare-dot oxidation comparison; initial state includes ordinary brief specimen handling, not proven pristine inert transfer.']);", "p=P(r,'bare-'+lab,'BareCdSe '+lab+' exposure state','CdSe',e=e,notes=[('General initial bare-XPS baseline with ordinary brief handling; exact physical identity with the later16/80h film is not established. Same source baseline as coverage-series xps-bare-context, not an independent replicate.' if lab=='initial' else 'The source describes the16h and80h results as the same bare-dot sample at successive exposure states; no unique original synthesis run is assigned.')]);",'D04')
replace("parameters={'accelerating_voltage':Q(60,'kV',e=e),'tube_current':Q(300,'mA',e=e)},description='SameRigaku300RotaflexCuKa setup as polymerSAXS, including described slits.", "parameters={'accelerating_voltage':Q(60,'kV',e=e),'tube_current':Q(300,'mA',e=e),'scatter_slit':Q(1/6,'degree',e=E(3,'SAXS in Polymer Films continuation'),raw_text='1/6 degree',basis='WAXS explicitly uses the same setup as polymer SAXS'),'diffraction_slit':Q(1/6,'degree',e=E(3,'SAXS in Polymer Films continuation'),raw_text='1/6 degree',basis='WAXS explicitly uses the same setup as polymer SAXS'),'collection_slit':Q(.3,'mm',e=E(3,'SAXS in Polymer Films continuation'),basis='WAXS explicitly uses the same setup as polymer SAXS')},description='SameRigaku300RotaflexCuKa setup as polymerSAXS, including described slits.",'D05')
insert="""
# Independent source audit: field-specific locators for claims beyond acquisition paragraphs.
for r in records:
 for o in r['operations']:
  extra=[]
  if r['record_id'].endswith(('zns-overgrowth','cds-overgrowth')) and o['id']=='heat-seeds':extra+=E(3,'III.A temperature and crystallinity discussion')
  if r['record_id'].endswith('wds-preparation') and o['id']=='wds':extra+=E(5,'WDS Results: uncertainty')
  if r['record_id'].endswith('xps-preparation') and o['id']=='exchange':extra+=E(5,'XPS Results: residual phosphorus')
  if r['record_id'].endswith(('saxs-pvb-film','saxs-diblock-film')) and o['id'] in ['cast','saxs']:extra+=E(7,'Polymer SAXS aggregation and data treatment')
  if r['record_id'].endswith('waxs-film') and o['id']=='waxs':extra+=E(3,'SAXS in Polymer Films continuation')+E(10,'WAXS structural model')
  o['evidence']+=extra
 for m in r['measurements']:
  extra=[]
  if m['property']=='photoluminescence_quantum_yield':extra+=OPT
  if r['record_id'].endswith('coverage-series'):
   if m['property'] in ['major_axis_length','relative_major_axis_distribution','aspect_ratio']:extra+=E(6,'TEM statistics')+E(7,'Figure9 caption')
   if m['property']=='tem_derived_shell_coverage':extra+=E(3,'Monolayer definition')+E(7,'TEM-derived shell coverage')
   if m['property'].startswith('saxs_model'):extra+=E(7,'Polymer SAXS model and fit limitations')
   if m['property']=='waxs_model_zn_to_cd_ratio':extra+=E(10,'WAXS fitted compositions')
   if m['property']=='zn_to_cd_atomic_ratio':extra+=E(5,'WDS Results')
  m['evidence']+=extra
 # Values retain original table/figure locators; added method evidence does not recast them as raw data.
"""
replace("records=json.loads(json.dumps(records))\nOUT=", "records=json.loads(json.dumps(records))\n"+insert+"\nOUT=",'D06')
P.write_text(text,encoding='utf-8')
(B/'canonical-audit-change-log.json').write_text(json.dumps({'scope':'Parent-authorized independent source corrections to private builder only','initial_record_hashes':initial,'changes':changes},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'changes':len(changes),'finding_groups':sorted({x['finding_id'] for x in changes})}))
