"""Presentation-only mapping from the independently audited reader; retain every field."""
from pathlib import Path
import hashlib,json,shutil
E=Path(__file__).resolve().parent;S=E.parents[4]/'recipe-atlas';O=E/'site-integration-proposal'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
reader=read(S/'data/paper-reviews/evans2010.json');rr={p.stem:read(p) for p in (O/'v2/records').glob('*.json')}
ids={rid:set() for rid in rr}
for sec in reader['reader_sections']:
 if sec['id']=='properties':
  for item in sec['items']:
   for link in item.get('canonical_links',[]):
    bits=link['json_pointer'].strip('/').split('/')
    if bits[0]=='measurements':ids[link['record_id']].add(rr[link['record_id']]['measurements'][int(bits[1])]['id'])
display=read(S/'data/measurement-display.json');display['record_property_measurement_ids']={k:sorted(v) for k,v in ids.items()}
assert all(not (set(display['record_structural_measurement_ids'][k])&v) for k,v in ids.items())
save(S/'data/measurement-display.json',display)
changes=[]
def edit(rel,old,new,count=1):
 p=S/rel;t=p.read_text(encoding='utf8');assert t.count(old)==count,(rel,old[:80],t.count(old))
 dest=O/'before-reader-refinement'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 p.write_text(t.replace(old,new),encoding='utf8');changes.append({'path':rel,'old':old,'new':new,'count':count})
rel='scripts/build_dataset.py'
edit(rel,"def dump(path,value):",'''def is_property(m,record_id=None):
    scoped=DISPLAY.get('record_property_measurement_ids',{})
    return m['id'] in scoped[record_id] if record_id in scoped else not is_structural(m,record_id)

def stock_scope(stock,record_id):
    raw=stock['scope']
    if not record_id.startswith('evans-2010-'):return '<p>'+esc(raw)+'</p>'
    try: fields,end=json.JSONDecoder().raw_decode(raw)
    except (ValueError,TypeError):return '<p>'+esc(raw)+'</p>'
    if not isinstance(fields,dict):return '<p>'+esc(raw)+'</p>'
    def value(v):
        if v is None:return 'Not explicitly reported'
        if isinstance(v,(list,dict)):return json.dumps(v,ensure_ascii=False)
        return str(v).replace('_',' ') if isinstance(v,str) else str(v)
    rows=''.join('<div><dt>'+esc(k.replace('_',' '))+'</dt><dd>'+esc(value(v))+'</dd></div>' for k,v in fields.items() if k not in {'id','source_unit_id'})
    provenance='; '.join(k+': '+str(v) for k,v in fields.items() if k in {'id','source_unit_id'})
    return '<dl class="fact-list">'+rows+'</dl><p>'+esc(raw[end:].strip())+'</p><details><summary>Stock provenance identifiers</summary><p>'+esc(provenance)+'</p></details>'

def dump(path,value):''')
edit(rel,"+esc(stock['scope'])+'</p>'","+esc(stock['scope'])+'</p>'",1) # Verify the scoped replacement target before changing it.
p=S/rel;t=p.read_text(encoding='utf8');old="+'<p>'+esc(stock['scope'])+'</p>'" # The actual title suffix includes </h4>.
old="+'</h4><p>'+esc(stock['scope'])+'</p>'";new="+'</h4>'+stock_scope(stock,rid)";assert t.count(old)==1;p.write_text(t.replace(old,new),encoding='utf8');changes.append({'path':rel,'old':old,'new':new})
edit(rel,"if not is_structural(m,r['record_id'])]","if is_property(m,r['record_id'])]")
edit(rel,"    body+='<details class=\"record-audit\">",'''    contextual=[m for m in r['measurements'] if not is_structural(m,rid) and not is_property(m,rid)]
    if contextual:body+='<h3>Additional source observations and preparation data</h3><p>Retained source fields outside the structural and property sections. Recipe conditions, reagent specifications and author interpretations are not product-property labels.</p>'+measurement_table(contextual)
    body+='<details class="record-audit">''')
edit(rel,"+'dataset.html\">Synthesis dataset</a></nav>","+'dataset.html\">Synthesis dataset</a><a href=\"'+prefix+'progress.html\">Review progress</a></nav>")
rel='scripts/build_reader_views.py';edit(rel,'<a href="dataset.html">Synthesis dataset</a></nav>','<a href="dataset.html">Synthesis dataset</a><a href="progress.html">Review progress</a></nav>')
rel='dist/material-hub.mjs';edit(rel," const data=", " const data=",1) if False else None
p=S/rel;t=p.read_text(encoding='utf8');anchor=" const displayCategories="
old='structural(m,r)===isStructure';new="(isStructure?structural(m,r):(Object.hasOwn(displayCategories.record_property_measurement_ids||{},r.record_id)?displayCategories.record_property_measurement_ids[r.record_id].includes(m.id):!structural(m,r)))";edit(rel,old,new)
# One reusable DOM renderer keeps material-hub and record stock descriptions readable.
module='''const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
export function stockScope(stock,record){
 const host=el('div'),raw=stock.scope;
 if(record.lineage?.source_group!=='evans2010'){host.append(el('p',raw));return host;}
 let fields,end=-1;
 for(let i=0;i<raw.length;i++){if(raw[i]!=='}')continue;try{fields=JSON.parse(raw.slice(0,i+1));end=i+1;break;}catch{}}
 if(!fields||typeof fields!=='object'||Array.isArray(fields)){host.append(el('p',raw));return host;}
 const list=el('dl');list.className='fact-list';const identifiers=[];
 for(const [key,v] of Object.entries(fields)){
  if(['id','source_unit_id'].includes(key)){identifiers.push(key+': '+v);continue;}
  const row=el('div'),value=v===null?'Not explicitly reported':typeof v==='object'?JSON.stringify(v):String(v).replaceAll('_',' ');
  row.append(el('dt',key.replaceAll('_',' ')),el('dd',value));list.append(row);
 }
 host.append(list,el('p',raw.slice(end).trim()));const provenance=el('details');provenance.append(el('summary','Stock provenance identifiers'),el('p',identifiers.join('; ')));host.append(provenance);return host;
}
'''
(S/'dist/stock-scope.mjs').write_text(module,encoding='utf8')
rel='dist/material-guide.mjs';edit(rel,"import {quantityValue}","import {stockScope} from './stock-scope.mjs';\nimport {quantityValue}")
edit(rel,"el('summary',s.name),el('p',s.scope)","el('summary',s.name),stockScope(s,r)")
save(O/'reader-refinement-delta.json',{'scope':'Presentation only; scientific records and reader values unchanged','property_measurements':sum(map(len,ids.values())),'all_other_measurements_retained':'Additional source observations and preparation data in record Evidence section; downloadable canonical data unchanged.','changes':changes,'file_hashes':{rel:sha(S/rel) for rel in sorted({c['path'] for c in changes}|{'data/measurement-display.json','dist/stock-scope.mjs'})}})
print(json.dumps({'property_measurements':sum(map(len,ids.values())),'presentation_changes':len(changes)}))
