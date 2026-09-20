"""Independent Evans source audit: read original files, never mutate author data."""
from pathlib import Path
import json,hashlib,re,math
from datetime import datetime,timezone

E=Path(__file__).resolve().parents[1]
O=Path(__file__).resolve().parent
def read(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[];bound={};findings=[]
def ck(ok,label):
 checks.append({'check':label,'passed':bool(ok)})
 if not ok: raise AssertionError(label)
def bind(p): bound[str(p)]=sha(p)
freeze=read(E/'source-extraction-freeze.json');bind(E/'source-extraction-freeze.json')
for row in freeze['files']:
 p=Path(row['path']);ck(sha(p)==row['sha256'],'Frozen author file '+row['relative_path']);bind(p)
for role,row in freeze['source_documents'].items():
 p=Path(row['path']);ck(sha(p)==row['sha256'],'Original '+role+' bytes');bind(p)
I=read(E/'source-inventory.json');F=read(E/'source-facts.json')['facts'];C=read(E/'cif-source-inventory.json');A=read(E/'selected-original-assets.json')['assets']
units={u['id']:u for u in I['units']};facts={f['id']:f for f in F};assets={a['id']:a for a in A}
ck(len(units)==len(I['units'])==198,'198 distinct source units')
ck(len(facts)==len(F)==457,'457 distinct facts')
ck(len(assets)==25,'25 selected original assets')
for u in units.values():
 ck(u['source_unit_id']==u['id'],'Stable unit ID '+u['id'])
 role=u['source_role'];ck(u['source_sha256']==freeze['source_documents'][role]['sha256'],'Unit source fingerprint '+u['id'])
 ck(role=='cif' or 1<=u['pdf_page']<=freeze['source_documents'][role]['page_count'],'Unit source page '+u['id'])
 ck(set(u['original_asset_ids'])<=set(assets),'Unit asset links '+u['id'])
for f in F:
 ck(f['source_unit_id'] in units,'Fact source unit '+f['id'])
 ck(f['eligible_training'] is False,'No extraction training promotion '+f['id'])
 ck(f['evidence'] and all(x['source_sha256']==freeze['source_documents'][x['source_role']]['sha256'] for x in f['evidence']),'Fact evidence fingerprints '+f['id'])
 ck(f['minimum'] is None or f['maximum'] is None or f['minimum']<=f['maximum'],'Fact bound order '+f['id'])
 ck(not f['minimum_exclusive'] or f['minimum'] is not None,'Exclusive minimum has bound '+f['id'])
 ck(not f['maximum_exclusive'] or f['maximum'] is not None,'Exclusive maximum has bound '+f['id'])
for group,key in [('materials','source_unit_id'),('stocks','source_unit_id'),('procedures','source_unit_id')]:
 ck(len({x['id'] for x in I[group]})==len(I[group]),'Unique '+group+' IDs')
 for row in I[group]:ck(row[key] in units,group+' unit '+row['id'])
for p in I['procedures']:
 ck(set(p['quantity_fact_ids'])<=set(facts),'Procedure quantities '+p['id'])
 ck(set(p['explicit_inheritance'])<=set(units),'Explicit procedure inheritance '+p['id'])
 ck(p['complete_executable_recipe_asserted'] is False,'No missingness-suppressing execution claim '+p['id'])
samples={x['id']:x for x in I['sample_lineage']}
for s in samples.values():
 ck(set(s['explicit_parent_ids'])<=set(samples),'Existing sample parents '+s['id'])
 ck(set(s['source_unit_ids'])<=set(units),'Sample source units '+s['id'])
 ck(set(s['original_asset_ids'])<=set(assets),'Sample source images '+s['id'])
 ck(s['distinct_physical_replicate_claimed'] is False,'No invented physical replicates '+s['id'])
for a in A:
 p=Path(a['path']);ck(sha(p)==a['sha256'],'Original crop bytes '+a['id']);bind(p)
 ck(a['source_sha256']==freeze['source_documents'][a['source_role']]['sha256'],'Crop parent source '+a['id'])

# A separate lexical reader, not the author's tokenizer or validation code.
# It preserves exact quoted/multiline tokens and line locators from original CIF bytes.
src=Path(C['source_path']);raw=src.read_text(encoding='utf8');lines=raw.splitlines();tok=[];i=0
while i<len(lines):
 line=lines[i]
 if line.startswith(';'):
  start=i;i+=1
  while i<len(lines) and not lines[i].startswith(';'):i+=1
  ck(i<len(lines),'Closed CIF multiline token at '+str(start+1))
  token='\n'.join(lines[start:i+1]);tok.append((token,token[1:token.rfind('\n')+1],start+1,i+1));i+=1;continue
 pos=0
 while pos<len(line):
  if line[pos].isspace():pos+=1;continue
  if line[pos]=='#':break
  start=pos
  if line[pos] in "\"'":
   quote=line[pos];pos+=1
   while pos<len(line) and not (line[pos]==quote and (pos+1==len(line) or line[pos+1].isspace())):pos+=1
   ck(pos<len(line),'Closed CIF quoted token line '+str(i+1));pos+=1;token=line[start:pos];val=token[1:-1]
  else:
   while pos<len(line) and not line[pos].isspace():pos+=1
   token=line[start:pos];val=token
  tok.append((token,val,i+1,i+1))
 i+=1
sc=[];loops=[];i=0;block=None
while i<len(tok):
 t=tok[i]
 if t[0].startswith('data_'):block=t[0][5:];i+=1;continue
 if t[0]=='loop_':
  start=t[2];i+=1;tags=[]
  while i<len(tok) and tok[i][0].startswith('_'):tags.append(tok[i]);i+=1
  vals=[]
  while i<len(tok) and not (tok[i][0].startswith(('_','data_')) or tok[i][0]=='loop_'):vals.append(tok[i]);i+=1
  ck(len(vals)%len(tags)==0,'Complete loop rectangularity '+str(start));loops.append((tags,vals,start,block));continue
 ck(t[0].startswith('_'),'CIF scalar tag at line '+str(t[2]));sc.append((t,tok[i+1],block));i+=2
ck(len(sc)==99 and len(loops)==7,'Independent original CIF99 scalars7 loops')
ck(len(tok)==C['raw_lexical_token_count'],'Independent full CIF lexical token count')
def token_eq(x,a,label):
 ck(x[0]==a['raw_token'],label+' raw token')
 ck(x[1]==a['value'],label+' decoded value')
 ck(x[2]==a['line_start'] and x[3]==a['line_end'],label+' source lines')
for (tag,t,b),a in zip(sc,C['scalars']):
 ck(tag[0]==a['tag'] and tag[2]==a['tag_line'] and b==a['block'],'Scalar tag and block '+a['tag']);token_eq(t,a['token'],a['tag'])
 f=next(f for f in F if f['property']==a['tag'])
 ck(f['raw_text']==t[0],'CIF fact raw scalar '+a['tag'])
 ck(f['sample_scope']=='molecular species9 crystal','CIF scalar molecular scope '+a['tag'])
 v=t[1];m=re.fullmatch(r'([-+]?\d+(?:\.\d*)?)(?:\((\d+)\))?',v)
 if v.strip() in ['?','.']:ck(f['value'] is None,'CIF unknown remains null '+a['tag'])
 elif m:
  ck(float(m[1])==f['value'],'CIF numeric scalar '+a['tag'])
  if m[2]:ck(math.isclose(f['standard_uncertainty'],int(m[2])*10**(-len(m[1].split('.')[1]) if '.' in m[1] else 0)),'CIF uncertainty '+a['tag'])
 else:ck(f['value']==v,'CIF literal scalar '+a['tag'])
total=0
for index,((tags,vals,start,block),a) in enumerate(zip(loops,C['loops'])):
 ck([x[0] for x in tags]==a['tags'],'CIF loop tags '+a['id'])
 ck(start==a['line_start'] and block==a['block'],'CIF loop origin '+a['id'])
 ck(len(vals)==a['row_count']*len(tags),'CIF loop size '+a['id']);total+=len(vals)
 for n,t in enumerate(vals):token_eq(t,a['rows'][n//len(tags)][tags[n%len(tags)][0]],a['id']+' cell '+str(n))
 f=facts['evans2010-'+a['id']+'-complete-source-loop'];ck(f['value']=={'tags':a['tags'],'rows':a['rows']},'CIF complete loop fact '+a['id'])
ck(total==2896,'All2896 molecular CIF loop cells independently matched')
for u in units.values():
 if u['kind'] in ['cif_scalar','cif_loop']:
  p=u['payload'];target=C
  for k in p['cif_inventory_pointer'].strip('/').split('/'):target=target[int(k)] if isinstance(target,list) else target[k]
  ck(target==p['scalar' if u['kind']=='cif_scalar' else 'loop'],'CIF unit exact inventory payload '+u['id'])

# Manually read numerical anchor values asserted independently, source scope kept.
anchors={'object-figure-S16-left-tem-scale-bar':5,'object-figure-S16-right-tem-scale-bar':50,'pbse-qd-optical-example-heating-duration':20,'cdse-qd-optical-example-heating-duration':10,'pbse-qd-oil-bath-temperature':80,'cdse-qd-growth-temperature':200,'object-calculation-S21-yield-initial-limiting-dppse':2.25e-6,'object-calculation-S21-yield-printed-final-denominator':2.25e6,'object-calculation-S21-yield-reported-conversion':93,'species9-crystallization-nominal-dppse-to-pb-ratio':5,'object-figure-S11-anhydride-carbonyl13c-shift':168.93}
for k,v in anchors.items():ck(facts['evans2010-'+k]['value']==v,'Independent source anchor '+k)
f=facts['evans2010-cif-diffrn-measured-fraction-theta-max-diffrn-measured-fraction-theta-max']
if f['unit']=='deg':findings.append({'id':'cif-measured-fraction-unit','severity':'requires_bounded_correction','fact_id':f['id'],'pointer':'/facts/444/unit','observed':'deg','required':'dimensionless or null with exact CIF-tag semantics','source':'Original CIF _diffrn_measured_fraction_theta_max 0.980. This is completeness fraction, not diffraction angle.','source_value_unchanged':True})
result={'schema':'mattersyn-independent-scientific-checks/1','auditor':'/root/peng1998_reader_assets','at':datetime.now(timezone.utc).isoformat(),'status':'bounded_correction_required' if findings else 'passed_mechanical_checks','checks':checks,'check_count':len(checks),'findings':findings,'cif_independent_tokenizer':{'scalars':len(sc),'loops':len(loops),'cells':total,'original_bytes_unchanged':sha(src)==C['source_sha256']},'bound_files':bound}
(O/'mechanical-checks-v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'checks':len(checks),'findings':findings,'sha256':sha(O/'mechanical-checks-v1.json')}))
