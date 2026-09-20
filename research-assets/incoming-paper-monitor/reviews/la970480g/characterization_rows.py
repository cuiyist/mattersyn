"""Map the independent source-row draft into explicitly scoped canonical observations."""
from pathlib import Path
import json
B=Path(__file__).resolve().parent

def build_characterization(base,P,Q,F,E,measurement):
 d=json.loads((B/'characterization-draft.json').read_text(encoding='utf-8'))
 r=base('characterization','Regional structure, optical properties and author models','observation','Source-scoped characterization')
 common='a-and-b-context'
 def evidence(row):return [item for x in row['evidence'] for item in E(x['pdf_page'],x['locator'])]
 product_sources={}
 for row in d['measurement_rows']:
  if row['id']=='char-other-electrolytes':continue
  sid=common if isinstance(row['sample_id'],list)else row['sample_id']
  product_sources.setdefault(sid,[]).extend(evidence(row))
 for sid,ev in product_sources.items():
  ev=[dict(t)for t in sorted({tuple(sorted(x.items()))for x in ev})]
  model='model' in sid or sid=='pretreatment-context'
  p=P(r,sid,'Shared sample-a/sample-b source context'if sid==common else sid,e=ev,composition=None if model else 'CdS nanocrystals in Chelex 100 polymer',notes=['Context identifier, not a physical product or experiment. Values are author-model calculations or cited inputs, not measured CdS properties.']if model else['Source formulation or regional context, not a unique physical batch or verified cross-instrument specimen. Regional depth identifiers preserve location without inventing a separate synthesis.'])
  p['source_sample_label']='sample a'if sid=='sample-a'or sid.startswith('a-')and sid!=common else'sample b'if sid=='sample-b'or sid.startswith('b-')else None
  p['notes'].append('Curator context identifier: '+sid+'. This identifier is not an author-assigned specimen code.')
  if sid in [common,'sample-a','sample-b']:p['phase']=F('Zinc blende (cubic) CdS component',E(3,'XRD assignment'),status='author_derived',note='Authors assign the CdS component from three reflections; no refinement, phase fraction, lattice parameters or coordinates supplied. Composite host is not a single crystal.')
 for row in d['measurement_rows']:
  if row['id']=='char-other-electrolytes':continue
  e=evidence(row);sid=common if isinstance(row['sample_id'],list)else row['sample_id'];basis=row['basis']
  status='author_derived'if basis in {'fitted','author_calculated','author_calculated_model','author_assignment','author_interpretation'}else'reported'
  note='; '.join(x for x in [row.get('source_condition'),row.get('caveat'),'Evidence class: '+basis,'Scope: '+row['scope_type']]if x)
  prop=row['property']
  if row['id']=='char-lamp-power':
   prop='lamp_power_rating';note+='; Lamp hardware rating, not sample irradiance or delivered optical dose.'
  if 'quantity'in row:
   q=row['quantity'];raw=q.get('raw_text','');qual=''
   if row['id']=='char-sample-b-plateau':prop='optical_formation_plateau_time_upper_bound';qual='Finished within 2 h: an upper-time bound, not exact equality.'
   if row['id']=='char-spectrum-reproducibility':qual='Reported reproducibility within ±5%; statistic and replicate count not specified.'
   if row['id']=='char-sample-a-continuation':qual='Observed continuation up to 48 h, not a known completion time.'
   if q.get('unit')is None:qual+=((' 'if qual else'')+'Unit not stated; no unit assigned.')
   value=Q(q.get('value'),q.get('unit')or'',e=e,minimum=q.get('lower_bound'),maximum=q.get('upper_bound'),approximate=q.get('approximate',False),status=status,raw_text=raw,basis=basis,qualifier=qual)
  else:value=F(row['fact'],e,status=status,note='Evidence class: '+basis)
  r['measurements'].append(measurement(row['id'],sid,prop,value,row.get('method')or('Author model or cited input'if row['scope_type']in['model_context','cited_context']else'Source-reported observation'),e,note))
 r['quality']['conflicts']=[x['text']+' '+x['resolution']for x in d['conflicts_and_limitations']]
 r['quality']['missing_fields']+=['No raw particle list, digitized curve, complete statistical uncertainty, refined structure, or exact specimen linkage supplied.','Figure 1 panel a/b labels are time panels, independent of preparation sample a/b labels.','Cited model inputs reproduce the current paper only; the cited references have not all been independently read.']
 for key,label in [('sample-a','No-added-NaCl synthesis'),('sample-b','NaCl-pretreated synthesis'),('tem','TEM specimen procedure'),('absorption','Optical specimen procedure'),('xrd','XRD procedure'),('other-electrolytes','Other monovalent electrolyte comparisons')]:r['context_links'].append({'label':label,'url':'../records/yao-1998-'+key+'.html','relation':'Source-cohort and method context; no physical batch equality inferred.'})
 return r
