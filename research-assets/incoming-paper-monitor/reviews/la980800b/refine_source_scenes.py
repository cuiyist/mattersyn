from pathlib import Path
import json
R=Path(__file__).resolve().parent;P=R/'stiger-protocol.mjs';s=P.read_text(encoding='utf8')
s=s.replace("function rinse(o){const product=o.id==='rinse-product',first=o.id==='rinse1';", "function rinse(o,r){const product=o.id==='rinse-product',control=o.id==='rinse-control',first=o.id==='rinse1';")
s=s.replace("title(product?'Rinse the deposited surface with pure acetonitrile':first?", "title(control?'Rinse the open-circuit control with acetonitrile':product?'Rinse the deposited surface with pure acetonitrile':first?")
s=s.replace("product?'Pure acetonitrile':first?'Nanopure water':'Water'", "product||control?'Pure acetonitrile':first?'Nanopure water':'Water'")
s=s.replace("product?'Retain deposited silver':first?'Oxidized silicon':'H-terminated surface'", "control?'Control surface':product?'Retain deposited silver':first?'Oxidized silicon':'H-terminated surface'")
s=s.replace("rinse:(o)=>rinse({...o,id:'rinse-product'})", "rinse:(o,r)=>rinse({...o,id:'rinse-control'},r)")
s=s.replace("'current-transients':{prepare:mix", "'current-transients':{prepare:cell")
s=s.replace("[['beam_energy','Source beam']]", "[['source_accelerating_voltage_label','Source label']]")
s=s.replace("'Graphite is a calibration specimen, not a silver-synthesis product or a new graphite recipe.'", "'Independent instrument calibration; its timing relative to Ag imaging and diffraction is unreported.'")
# Keep explicitly measured settings within the scene while the full source conditions remain adjacent.
s=s.replace("const noAg=silverFree(r),cv=recordType(r)==='cyclic-voltammetry';return", "const noAg=silverFree(r),cv=recordType(r)==='cyclic-voltammetry';const e=q(o,'applied_potential'),rate=q(o,'scan_rate');const label=scan&&rate?'Scan rate: '+rate:pulse&&e?'Applied potential: '+e+(o.parameters?.applied_potential?.value!=null?' versus Ag':''):'';return")
s=s.replace("'Mount the coupon in the three-electrode cell')+box", "'Mount the coupon in the three-electrode cell')+(label?txt(300,78,label,16):'')+box")
# AFM source has both reference H-Si and deposited specimens; no universal Ag markers.
start=s.index('function afm(o,r)');end=s.index('\nfunction flatten()',start)
s=s[:start]+'''function afm(o,r){const control=isControl(r);return title(control?'Check the control surface by noncontact AFM':'Acquire source-scoped noncontact AFM topography')+(control?wafer(296,276,347,{h:true}):wafer(157,280,222,{h:true})+wafer(442,280,222,{h:true,ag:true})+txt(158,324,'Etched Si reference',17)+txt(442,324,'Deposited Ag specimen',16)+txt(300,274,'OR',16))+line('M178 117H354V139H178Z',C.line,3)+`<path d="M326 141L345 193L363 141Z" fill="#b4c9d4" stroke="${C.line}"/>`+line('M345 201V228',C.green,1.5)+txt(127,206,control?'Control surface':'Keep specimens separate',16)+txt(480,172,'AFM probe',18)+txt(480,208,'Not to scale',16)+note(control?'Control images were not printed. Background-particle identity and possible roughening remain unresolved.':'Contact-mode comparison can remove particles. Height and tip-convolved lateral width are distinct.');}''' +s[end:]
P.write_text(s,encoding='utf8')
p=R/'chemical-reference-proposal.json';d=json.loads(p.read_text(encoding='utf8'))
for x in d['proposed_cards_or_ionic_references']:
 if x['name']=='Ultralever AFM probes':x['limits']='Source gives Ultralever dimensions of 0.6 µm and 2 µm without naming the dimension type, plus an NC resonance range. Tip material and radius are not specified.'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Updated control, comparison, calibration and measurement scene scopes.')
