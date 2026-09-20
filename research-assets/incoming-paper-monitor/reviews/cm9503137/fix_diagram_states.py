from pathlib import Path
B=Path(__file__).resolve().parent;p=B/'danek-protocol.mjs';s=p.read_text(encoding='utf-8')
s=s.replace('function vessel(x,y,{pellet=false,coated=false}={})','function vessel(x,y,{pellet=false,coated=false,particles=true}={})').replace("${[-17,1,19].map((a,i)=>","${(particles?[-17,1,19]:[]).map((a,i)=>")
s=s.replace('function stack(x,y,w,{composite=false,cap=false}={})','function stack(x,y,w,{composite=false,cap=false,coated=false}={})').replace('stroke="${C.blue}" stroke-width="3"','stroke="${coated?C.blue:C.gold}" stroke-width="${coated?3:0}"')
marker="function purification(o){"
s=s.replace(marker,"function hasShell(o,r){return /overcoated-dot-film|annealing-control/.test(r.record_id)||(r.record_id==='danek-1996-znse-overgrowth'&&['isolate','exchange','store','cool','quench'].includes(o.id));}\nfunction purification(o,r){")
s=s.replace("+vessel(117,189)+arrow(205,189)","+vessel(117,189,{coated:hasShell(o,r)})+arrow(205,189)").replace("vessel(481,189,{pellet:true,coated:true})","vessel(481,189,{pellet:true,coated:hasShell(o,r)})")
s=s.replace('function filtering(o){','function filtering(o,r){').replace('vessel(93,174,{coated:true})','vessel(93,174,{coated:hasShell(o,r)})').replace('vessel(511,174,{coated:true})','vessel(511,174,{coated:hasShell(o,r)})')
s=s.replace('function redispersion(o){','function redispersion(o,r){').replace('vessel(98,183,{pellet:true,coated:true})',"vessel(98,183,{pellet:o.action==='redispersion',coated:hasShell(o,r)})").replace('vessel(512,183,{coated:true})','vessel(512,183,{coated:hasShell(o,r)})')
s=s.replace('vessel(103,154)','vessel(103,154,{particles:false})').replace('vessel(360,181)','vessel(360,181,{particles:false})')
s=s.replace('function layer(o){','function layer(o,r){').replace('{composite:cap,cap})','{composite:cap,cap,coated:hasShell(o,r)})').replace('function electrospray(o){','function electrospray(o,r){').replace('stack(315,236,224,{composite:true})','stack(315,236,224,{composite:true,coated:hasShell(o,r)})')
p.write_text(s,encoding='utf-8')
print('Corrected particle-shell and input physical-state semantics in private diagram module.')
