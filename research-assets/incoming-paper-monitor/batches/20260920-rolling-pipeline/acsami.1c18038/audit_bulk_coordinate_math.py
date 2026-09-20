"""Independent root comparison of source-table coordinates, geometry and partial CIFs.

This checker uses direct trigonometry and raw printed-number parsing, not the
author's Gemmi builder. It is a numerical checkpoint, not yet viewer approval.
"""
from pathlib import Path
from decimal import Decimal
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,math,re
L=Path(__file__).resolve().parent;V=L/'visuals/bulk-structure-proposal';O=L/'visuals/bulk-structure-independent-audit';O.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tables={t['id']:t for t in read(L/'source-tables.json')['tables']}
checks=[]
def check(name,condition):
 checks.append(name)
 if not condition:raise AssertionError(name)
def number(raw,scale=1):
 m=re.fullmatch(r'(-?\d+(?:\.\d+)?)(?:\((\d+)\))?',raw);assert m,raw
 v=Decimal(m[1]);su=Decimal(m[2])*Decimal(10)**v.as_tuple().exponent if m[2] else None
 return float(v*Decimal(str(scale))),float(su*Decimal(str(scale))) if su is not None else None
def close(a,b,tol=1e-9):return abs(a-b)<=tol
def transform(f,v):return [sum(f[j]*v[j][i] for j in range(3)) for i in range(3)]
def distance(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def cif_loop(lines,header):
 i=lines.index(header);start=i
 while start>0 and lines[start-1].startswith('_'):start-=1
 end=i+1
 while end<len(lines) and lines[end].startswith('_'):end+=1
 headers=lines[start:end];rows=[]
 for line in lines[end:]:
  if not line or line.startswith(('#','loop_','_','data_')):break
  parts=line.split();assert len(parts)==len(headers);rows.append(dict(zip(headers,parts)))
 return rows
results=[]
for phase,coord,adp,bonds,angles,expected in [('A','table-s6','table-s8','table-s2','table-s4',64),('B','table-s7','table-s9','table-s3','table-s5',144)]:
 mp=V/f'lian2021-bulk-{phase.lower()}-non-h.json';cp=V/f'lian2021-bulk-{phase.lower()}-non-h-partial.cif';m=read(mp)
 col=0 if phase=='A' else 1;meta={r['row_label']:r['cells'][col] for r in tables['table-s1']['rows']}
 for key in ['a','b','c','alpha','beta','gamma']:
  check(phase+' cell '+key,close(m['cell'][key],number(meta[key]['raw_text'])[0]))
 a,b,c=[m['cell'][k] for k in ['a','b','c']];al,be,ga=[math.radians(m['cell'][k]) for k in ['alpha','beta','gamma']]
 cx=c*math.cos(be);cy=c*(math.cos(al)-math.cos(be)*math.cos(ga))/math.sin(ga)
 vectors=[[a,0,0],[b*math.cos(ga),b*math.sin(ga),0],[cx,cy,math.sqrt(c*c-cx*cx-cy*cy)]]
 volume=a*b*math.sin(ga)*vectors[2][2]
 check(phase+' cell volume',abs(volume-meta['volume']['value'])<3*meta['volume']['uncertainty'])
 for i in range(3):
  for j in range(3):check(phase+f' Cartesian basis {i},{j}',close(m['cell_cartesian_matrix'][i][j],vectors[j][i]))
 source={r['row_label']:r for r in tables[coord]['rows']};anis={r['row_label']:r for r in tables[adp]['rows']};sites={s['id']:s for s in m['asymmetric_unit_sites']}
 check(phase+' complete source labels',set(source)==set(sites)==set(anis))
 xyz={}
 for label,row in source.items():
  site=sites[label];f=[];su=[]
  check(phase+label+' exact coordinate row',site['source_coordinate_row']==row)
  check(phase+label+' exact ADP row',site['source_adp_row']==anis[label])
  for x in row['cells'][:3]:
   value,uncertainty=number(x['raw_text'],.0001);f.append(value);su.append(uncertainty)
  xyz[label]=transform(f,vectors)
  check(phase+label+' fractional/SU',all(close(x,y) for x,y in zip(site['fractional'],f)) and all(close(x,y) for x,y in zip(site['fractional_su'],su)))
  check(phase+label+' independent Cartesian',all(close(x,y) for x,y in zip(site['cartesian'],xyz[label])))
  check(phase+label+' no occupancy or H invention',site['occupancy'] is None and site['element']!='H')
 ops=[lambda x,y,z:[x,y,z],lambda x,y,z:[-x,-y,-z]] if phase=='A' else [lambda x,y,z:[x,y,z],lambda x,y,z:[-x,y+.5,-z+.5],lambda x,y,z:[-x,-y,-z],lambda x,y,z:[x,-y+.5,z+.5]]
 expected_positions={}
 for label,site in sites.items():
  for op in ops:
   f=op(*site['fractional']);wrapped=[x-math.floor(x) for x in f]
   expected_positions[(label,*[round(x,10) for x in wrapped])]=site['element']
 actual={}
 for pos in m['geometric_cell_positions']:
  key=(pos['source_label'],*[round(x,10) for x in pos['fractional']]);actual[key]=pos['element']
  check(phase+pos['id']+' geometric position',pos['occupancy'] is None and all(0<=x<1 for x in pos['fractional']) and all(close(x,y) for x,y in zip(pos['cartesian'],transform(pos['fractional'],vectors))))
  check(phase+pos['id']+' wrapping provenance',all(close(u+t,f) for u,t,f in zip(pos['unwrapped_fractional'],pos['wrapping_translation'],pos['fractional'])))
 check(phase+' independent symmetry orbit',actual==expected_positions and len(actual)==expected and len(actual)==len(m['geometric_cell_positions']))
 coords=[p['fractional'] for p in m['geometric_cell_positions']]
 check(phase+' no cross-label duplicate coordinates',len({tuple(round(x,10) for x in f) for f in coords})==len(coords))
 bond_diffs=[];angle_diffs=[]
 for row in tables[bonds]['rows']:
  val=row['cells'][0];got=distance(*[xyz[x] for x in row['atoms']]);delta=abs(got-val['value']);bond_diffs.append(delta)
  check(phase+' source bond '+row['row_label'],delta<=3*val['uncertainty']+.0001)
 for row in tables[angles]['rows']:
  x,y,z=[xyz[k] for k in row['atoms']];u=[a-b for a,b in zip(x,y)];v=[a-b for a,b in zip(z,y)];cosine=sum(a*b for a,b in zip(u,v))/math.sqrt(sum(a*a for a in u)*sum(b*b for b in v));got=math.degrees(math.acos(max(-1,min(1,cosine))));val=row['cells'][0];delta=abs(got-val['value']);angle_diffs.append(delta)
  check(phase+' source angle '+row['row_label'],delta<=3*val['uncertainty']+.01)
 lines=cp.read_text(encoding='utf8').splitlines();cifsites=cif_loop(lines,'_atom_site_label');cifadps=cif_loop(lines,'_atom_site_aniso_label')
 check(phase+' CIF source labels',{x['_atom_site_label'] for x in cifsites}==set(source))
 for row in cifsites:
  label=row['_atom_site_label'];check(phase+label+' CIF unknown occupancy',row['_atom_site_occupancy']=='?')
  for i,key in enumerate(['_atom_site_fract_x','_atom_site_fract_y','_atom_site_fract_z','_atom_site_U_iso_or_equiv']):
   got=number(row[key]);want=number(source[label]['cells'][i]['raw_text'],.0001 if i<3 else .001)
   check(phase+label+' CIF '+key,all(close(x,y) for x,y in zip(got,want)))
 check(phase+' CIF ADP rows',{x['_atom_site_aniso_label'] for x in cifadps}==set(anis))
 for row in cifadps:
  label=row['_atom_site_aniso_label']
  for cell in anis[label]['cells']:
   key='_atom_site_aniso_U_'+cell['column'][-2:]
   got=number(row[key]);want=number(cell['raw_text'],.001)
   check(phase+label+' CIF '+key,all(close(x,y) for x,y in zip(got,want)))
 check(phase+' no automatic training admission',not any(m['eligibility'].values()))
 results.append({'phase':phase,'listed_sites':len(sites),'geometric_positions':len(actual),'coordinate_element_counts':dict(Counter(p['element'] for p in m['geometric_cell_positions'])),'independent_volume_A3':volume,'maximum_bond_difference_A':max(bond_diffs),'maximum_angle_difference_deg':max(angle_diffs),'model_sha256':sha(mp),'partial_cif_sha256':sha(cp)})
out={'schema':'mattersyn.independent_bulk_coordinate_math/1','auditor':'/root','author':'/root/peng1998_reader_assets','at':datetime.now(timezone.utc).isoformat(),'status':'passed','scope':'Source tables to scaled coordinates, independent trigonometric Cartesian conversion and manually stated standard P-1/P21-c symmetry orbits; all published bond/angle values; partial CIF values and uncertainties. Viewer binding and actual browser checks remain pending.','source_pages_visually_reopened':['main-06','si-13','si-18','si-19','si-20','si-21','si-22'],'source_tables_sha256':sha(L/'source-tables.json'),'script_sha256':sha(Path(__file__)),'check_count':len(checks),'models':results,'final_viewer_approval':False}
(O/'coordinate-math-audit.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))
