from pathlib import Path
import json,hashlib
O=Path(__file__).resolve().parent;F=O.parent;B=F/'visuals/molecular-bindings';C=F/'canonical-proposal/draft-v2';A=B/'consumer-fixture';D=F/'visuals/molecules-correction-v2';V=F/'visuals/molecules'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ptr(x,p):
 for k in p.strip('/').split('/'):x=x[int(k)] if isinstance(x,list) else x[k.replace('~1','/').replace('~0','~')]
 return x
checks=[];bound={}
def ck(n,b):checks.append({'check':n,'passed':bool(b)})
def bind(p):bound[str(p)]=sha(p)
f=read(B/'package-freeze.json');ck('Exact original package freeze',sha(B/'package-freeze.json')=='1c35c9e37ae21dda72c3c4d22148b29ca46487684f69c7d396ab0f22a3bd35b3');bind(B/'package-freeze.json')
for p,h in f['bound_files'].items():
 p=B/p;ck(str(p)+' exact author file',sha(p)==h);bind(p)
for k in ['canonical_freeze','molecular_audit']:
 p=Path(f[k]['path']);ck(k+' exact dependency',sha(p)==f[k]['sha256']);bind(p)
ma=read(f['molecular_audit']['path']);ck('Distinct chemistry audit passed',ma['status']=='passed')
reg=read(D/'registry-additions.json');entries={x['id']:x for x in reg['entries']};ck('Fixture registry exact corrected registry',read(A/'registry-additions.json')==reg);bind(D/'registry-additions.json')
for e in entries.values():
 for key in ['model2dPath','model3dPath']:
  if not e.get(key):continue
  rel=e[key];p=D/rel if (D/rel).exists() else V/rel
  ck(e['id']+'/'+key+' qualified model exact',sha(A/rel)==sha(p)==e['assetHashes'][key]);bind(p)
b=read(B/'bindings-proposal.json');slots=read(B/'material-slot-map.json')['slots'];stocks=read(B/'stock-component-map.json')['stocks'];sol=read(B/'solution-components-proposal.json')['contexts'];figs=read(B/'stock-figure-bindings.json')['stocks'];sf=read(F/'source-extraction-revision-2/source-facts.json');sm={x['id']:x for x in sf['materials']};ss={x['id']:x for x in sf['stocks']}
manifest=read(C/'record-manifest.json');records={x['record_id']:read(x['path']) for x in manifest['records']};rh={x['record_id']:x['sha256'] for x in manifest['records']}
for row in manifest['records']:ck(row['record_id']+' canonical exact',sha(row['path'])==row['sha256']);bind(Path(row['path']))
expected={(rid,m['id']) for rid,r in records.items() for m in r['materials']};seen=set()
for s in slots:
 rid,mid=s['record_id'],s['material_id'];key=(rid,mid);seen.add(key);m=ptr(records[rid],s['json_pointer']);e=entries[s['registry_id']]
 ck(str(key)+' exact snapshot/hash',m==s['canonical_identity'] and s['canonical_record_sha256']==rh[rid]);ck(str(key)+' exact source identity',s['source_material']==sm[mid]);ck(str(key)+' exact reference identity',e['provenance']['sourceMaterialId']==mid)
 ck(str(key)+' bindings map exact',b['recordBindings'][rid][mid]==s['registry_id'] and b['bindingNotes'][rid][mid]==s)
 ck(str(key)+' scoped identity and limitations',s['viewOverrides']['name']==m['name'] and s['viewOverrides']['limitations']==e['limitations'] and s['viewOverrides']['caption']==e['caption']+' Role in this record: '+m['role']+'.')
 ck(str(key)+' no model override',set(s['viewOverrides'])=={'name','caption','limitations'})
 ck(str(key)+' private approval',s['binding_approved'] is False)
 ck(str(key)+' exact quantity coverage',len(s['quantity_links'])==len(m['quantities']))
 for q in s['quantity_links']:ck(q['json_pointer']+' exact material quantity',ptr(records[rid],q['json_pointer'])==q['quantity'])
ck('All and only 77 material slots',seen==expected and len(slots)==len(seen)==77)
seen=set();component_count=0
for s in stocks:
 rid,sid=s['record_id'],s['stock_id'];seen.add((rid,sid));r=records[rid];stock=ptr(r,s['canonical_pointer']);src=ss[s['source_definition_id']]
 ck(rid+'/'+sid+' exact stock snapshot',stock==s['canonical_stock']);ck(rid+'/'+sid+' components exact count',len(s['components'])==len(stock['components']))
 context=next(x for x in sol if x['record_id']==rid and x['id']=='friedfeld2019-'+sid)
 ck(rid+'/'+sid+' readable source summary',context['label']==stock['name'] and context['scope']==s['display_summary']+' '+s['display_limit'])
 for component,sc in zip(s['components'],stock['components']):
  component_count+=1;mid=component['material_id'];sourcecomponent=next(x for x in src['components'] if x['material_id']==mid)
  ck(rid+'/'+sid+'/'+mid+' exact component',ptr(r,component['json_pointer'])==sc and component['source_quantities']==sc['quantities'])
  ck(rid+'/'+sid+'/'+mid+' exact identity role',component['registry_id']==b['recordBindings'][rid][mid] and component['role']==sourcecomponent['role'])
  ck(rid+'/'+sid+'/'+mid+' quantity coverage',len(component['quantity_links'])==len(sc['quantities']))
  for q in component['quantity_links']:ck(q['json_pointer']+' exact component quantity',ptr(r,q['json_pointer'])==q['quantity'])
 for q in s['concentration_links']:ck(q['json_pointer']+' exact concentration',ptr(r,q['json_pointer'])==q['quantity'])
 ck(rid+'/'+sid+' no missing concentration',len(s['concentration_links'])==len(stock['concentrations']))
ck('All eight stocks / sixteen components',seen=={(rid,s['id']) for rid,r in records.items() for s in r['stocks']} and len(stocks)==8 and component_count==16)
for f in figs:ck(f['stock_id']+' stock figure exact',sha(f['path'])==f['sha256']);bind(Path(f['path']))
varied=next(s for s in stocks if s['stock_id']=='msc-injection-varied');ck('Varied source inheritance explicit',varied['source_definition_id']=='msc-injection' and varied['source_definition_inherited'] is True)
ck('No representative solute charge in varied stock',list(varied['components'][0]['source_quantities'])==['condition_specific_mass'] and varied['components'][0]['source_quantities']['condition_specific_mass']['value'] is None)
ck('Varied solvent inherited',varied['components'][1]['source_quantities']['msc_injection_solvent']['status']=='inherited')
ck('Eight distinct record/stock context keys',len(sol)==len({(x['record_id'],x['id']) for x in sol})==8)
ck('No public/training promotion',b['published'] is False and b['eligible_training'] is False and b['binding_approved'] is False)
result={'status':'passed' if all(x['passed'] for x in checks) else 'findings','check_count':len(checks),'failures':[x for x in checks if not x['passed']],'checks':checks,'bound_files':bound}
(O/'binding-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k not in ['checks','bound_files']}))
