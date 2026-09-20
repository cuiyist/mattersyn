"""Exact source/record bindings for independently qualified molecular assets."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib,html
O=Path(__file__).resolve().parent;F=O.parents[1];C=F/'canonical-proposal/draft-v2';V=O.parent/'molecules';D=O.parent/'molecules-correction-v2'
assert not (O/'package-freeze.json').exists()
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(rel,x):p=O/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n','utf8')
def ptr(x,p):
 for k in p.strip('/').split('/'):x=x[int(k)] if isinstance(x,list) else x[k.replace('~1','/').replace('~0','~')]
 return x
ck=[]
def check(n,v):ck.append({'check':n,'passed':bool(v)});assert v,n
check('Frozen canonical version',sha(C/'package-freeze.json')=='ff8767ef6a51f4184825de335dfe9906fab80e53b97e641fa534f6344f25a112')
check('Independent molecular correction passed',sha(F/'molecular-independent-audit/independent-audit.json')=='d4822a38a3c605feab64d59763f5f0b8e267e6ae0a5f7fe1827615e1f15a4a52' and read(F/'molecular-independent-audit/independent-audit.json')['status']=='passed')
entries={e['provenance']['sourceMaterialId']:e for e in read(D/'registry-additions.json')['entries']}
source=read(F/'source-extraction-revision-2/source-facts.json');sm={m['id']:m for m in source['materials']};ss={s['id']:s for s in source['stocks']}
records={p.stem:read(p) for p in (C/'records').glob('*.json')}
def fmt(q):
 if q.get('status')=='not_reported':return 'Not reported'+(' ('+q['unit']+')' if q.get('unit') else '')
 value=q.get('raw_text') or str(q.get('value'));return value+(' '+q['unit'] if q.get('unit') else '')+' ['+q['status']+']'
bindings={'schemaVersion':'1.0','source_id':'friedfeld2019','recordBindings':{},'bindingNotes':{},'binding_approved':False,'status':'private_author_proposal','published':False,'eligible_training':False};slots=[];stocks=[];contexts=[]
for rid,r in records.items():
 if r['materials']:bindings['recordBindings'][rid]={};bindings['bindingNotes'][rid]={}
 for mi,m in enumerate(r['materials']):
  mid=m['id'];e=entries[mid];check(rid+'/'+mid+' literal source identity',m['name']==sm[mid]['name'] and m['formula']==sm[mid]['source_formula_or_abbreviation'])
  note={'record_id':rid,'material_id':mid,'json_pointer':f'/materials/{mi}','canonical_record_sha256':sha(C/'records'/(rid+'.json')),'registry_id':e['id'],'canonical_identity':deepcopy(m),'source_material':deepcopy(sm[mid]),'viewOverrides':{'name':m['name'],'caption':e['caption']+' Role in this record: '+m['role']+'.','limitations':deepcopy(e['limitations'])},'reference_formula':e['formula'],'literal_source_formula':m['formula'],'binding_approved':False,'quantity_links':[{'record_id':rid,'json_pointer':f'/materials/{mi}/quantities/{k}','quantity':q,'display_value':fmt(q)} for k,q in m['quantities'].items()]}
  bindings['recordBindings'][rid][mid]=e['id'];bindings['bindingNotes'][rid][mid]=note;slots.append(note)
 for si,s in enumerate(r['stocks']):
  sid=s['id'];sourceid='msc-injection' if sid=='msc-injection-varied' else sid;src=ss[sourceid];components=[]
  for ci,c in enumerate(s['components']):
   mid=c['material_id'];sc=next(x for x in src['components'] if x['material_id']==mid);e=entries[mid]
   check(rid+'/'+sid+'/'+mid+' material slot exists',mid in bindings['recordBindings'][rid])
   links=[{'record_id':rid,'json_pointer':f'/stocks/{si}/components/{ci}/quantities/{key}','quantity':deepcopy(q),'display_value':fmt(q)} for key,q in c['quantities'].items()]
   components.append({'material_id':mid,'registry_id':e['id'],'role':sc['role'],'json_pointer':f'/stocks/{si}/components/{ci}','source_quantities':deepcopy(c['quantities']),'quantity_links':links,'binding_approved':False})
  concentrations=[{'record_id':rid,'json_pointer':f'/stocks/{si}/concentrations/{key}','quantity':deepcopy(q),'display_value':fmt(q)} for key,q in s['concentrations'].items()]
  summary=sm[components[0]['material_id']]['name']+' in '+sm[components[1]['material_id']]['name']+'. '
  summary+='; '.join(k.replace('_',' ')+': '+fmt(q) for k,q in s['concentrations'].items()) if s['concentrations'] else 'Stock concentration is not reported.'
  quantities=[link['display_value'] for c in components for link in c['quantity_links']]
  if quantities:summary+=' Component quantities: '+', '.join(quantities)+'.'
  limit='Separate component structures are references, not a measured solution complex. '+s['scope']
  if sid=='msc-injection-varied':
   check('Varied mass remains unknown',components[0]['source_quantities']['condition_specific_mass']['value'] is None)
   check('Varied stock excludes representative solute amount',all(q.get('value') not in [20,.00121] for q in components[0]['source_quantities'].values()))
   limit+=' Do not use the representative stock illustration: its 20 mg charge does not apply to this concentration series.'
  stocks.append({'record_id':rid,'stock_id':sid,'canonical_pointer':f'/stocks/{si}','canonical_stock':deepcopy(s),'source_definition_id':sourceid,'source_definition_inherited':sid!=sourceid,'components':components,'concentration_links':concentrations,'display_summary':summary,'display_limit':limit,'binding_approved':False})
  contexts.append({'record_id':rid,'id':'friedfeld2019-'+sid,'label':s['name'],'scope':summary+' '+limit,'components':[{'material_id':c['material_id'],'registry_id':c['registry_id'],'role':c['role'],'label':sm[c['material_id']]['name'],'viewOverrides':{'caption':entries[c['material_id']]['caption']+' '+summary+' '+limit,'limitations':[limit]+entries[c['material_id']]['limitations']}} for c in components],'binding_approved':False})
check('77 material slots and 8 stock instances',len(slots)==77 and len(stocks)==8)
for slot in slots:
 for link in slot['quantity_links']:check('Exact material quantity pointer',ptr(records[slot['record_id']],link['json_pointer'])==link['quantity'])
for stock in stocks:
 for link in stock['concentration_links']+[q for c in stock['components'] for q in c['quantity_links']]:check('Exact stock quantity pointer',ptr(records[stock['record_id']],link['json_pointer'])==link['quantity'])
save('bindings-proposal.json',bindings);save('material-slot-map.json',{'slots':slots,'count':len(slots),'independent_approval':False});save('stock-component-map.json',{'stocks':stocks,'count':len(stocks),'independent_approval':False});save('solution-components-proposal.json',{'schemaVersion':'1.0','contexts':contexts,'binding_approved':False})
# Separate diagram for the concentration variant. Reuse only the identity/solvent
# graphics, replacing all representative quantitative prose before publication.
old=(V/'stock-svg/friedfeld2019-msc-injection.svg').read_text('utf8');prefix=old.split('<text x="45" y="478"')[0]
check('Representative quantity region found',len(prefix)<len(old))
prefix=prefix.replace('Representative myristate-MSC injection in ODE','Condition-specific myristate-MSC injection in ODE')
lines=['MSC mass and amount: not reported for the changed-concentration conditions.','ODE component: 1 mL inherited common solvent volume; not separately reported for each run.','Initial MSC reaction concentrations are condition options, not stock concentrations.','The representative 20 mg / 0.00121 mmol charge is excluded from this stock.','No measured cluster coordinates or dissolved complex are supplied.']
svg=prefix+''.join(f'<text x="45" y="{480+i*45}" font-family="Arial,sans-serif" font-size="20" fill="#294658">{html.escape(line)}</text>' for i,line in enumerate(lines))+'</svg>'
p=O/'stock-svg/friedfeld2019-msc-injection-varied.svg';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(svg,'utf8')
stockfigs=[]
for s in stocks:
 sid=s['stock_id'];path=p if sid=='msc-injection-varied' else next((D/x['svg_path'] if (D/x['svg_path']).exists() else V/x['svg_path']) for x in read(D/'source-stock-reference-proposal.json')['stocks'] if x['stock_id']==sid)
 stockfigs.append({'record_id':s['record_id'],'stock_id':sid,'path':str(path),'sha256':sha(path),'scope':s['display_limit'],'binding_approved':False})
save('stock-figure-bindings.json',{'stocks':stockfigs,'new_varied_stock_requires_visual_review':True})
save('author-checks.json',{'checks':ck,'check_count':len(ck),'status':'passed_author_checks','independent_approval':False})
save('input-bindings.json',{'canonical_freeze':{'path':str(C/'package-freeze.json'),'sha256':sha(C/'package-freeze.json')},'molecular_correction_audit':{'path':str(F/'molecular-independent-audit/independent-audit.json'),'sha256':sha(F/'molecular-independent-audit/independent-audit.json')},'canonical_record_files':{str(C/'records'/(rid+'.json')):sha(C/'records'/(rid+'.json')) for rid in records}})
print(json.dumps({'material_slots':len(slots),'stock_instances':len(stocks),'components':sum(len(x['components']) for x in stocks),'author_checks':len(ck),'independent_approval':False,'freeze':'pending visual and consumer checks'}))
