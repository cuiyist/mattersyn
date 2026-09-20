from pathlib import Path
p=Path(__file__).with_name('gerion2001-protocol.mjs')
s=p.read_text(encoding='utf8')
changes={
"cy=\"174\"":"cy=\"195\"",
"text(477,238,layer===1?'Primed surface':'Growing siloxane layer'":"text(477,259,layer===1?'Primed surface':'Siloxane-coated particle'",
"labeled(260,254,'Collected fraction')":"`<g transform=\"translate(260 239) scale(.78)\">${vial(0,0)}</g>`+text(260,307,'Collected fraction',14)",
"labeled(110,248,'Retain filtrate')":"`<g transform=\"translate(110 255) scale(.7)\">${vial(0,0)}</g>`+text(110,315,'Retain filtrate',14)",
"text(134,131,label,16)":"text(134,131,label,label.length>20?14:16)",
"heading='Quench-mixture preparation';art=addition(['Methanol + TMSCl','TMAH pentahydrate'])":"heading='Quench-mixture preparation';art=stockPreparation(['Methanol + TMSCl','TMAH pentahydrate'])",
"heading='DMAP stock preparation';art=addition(['DMAP solute','DMF solvent'])":"heading='DMAP stock preparation';art=stockPreparation(['DMAP solute','DMF solvent'])",
"id==='dry'?grid(rid==='eels-acquisition')+text(500,92,rid==='tem-acquisition'?'Air dry':'Dry overnight',15)":"id==='dry'?dryGrid(rid==='eels-acquisition')",
"Normalize to each specimen’s initial signal. Source sampling descriptions differ; do not fabricate daily replicate measurements.":"Normalize to each specimen’s day-1 signal. Storage monitoring is distinct from continuous laser irradiation.",
"art=optical(id==='prepare'?'Dilute specimens':'Integrated emission')":"art=id==='prepare'?stockPreparation(['Nanocrystal aliquot','Phosphate buffer']):optical('Integrated emission')",
"art=rotor()+arrow(273,161)+labeled(423,181,'Concentrated dispersion');notes='Vacufuge":"art=rotor().replace('Centrifugation','Centrifugal evaporation')+arrow(273,161)+labeled(423,181,'Concentrated dispersion');notes='Vacufuge",
}
for a,b in changes.items():
 assert a in s,a
 s=s.replace(a,b)
helpers="""
function stockPreparation(rows){return panel(49,104,247,rows)+arrow(336,180)+labeled(465,186,'Prepared mixture');}
function dryGrid(eels){return `<circle cx="300" cy="203" r="65" fill="${C.pale}" stroke="${C.line}" stroke-width="3"/>`+[-40,-20,0,20,40].map(x=>path(`M${300+x} 150V256M247 ${203+x}H353`)).join('')+text(300,110,eels?'Dry overnight':'Dry in air',20)+text(300,305,eels?'Carbon-coated grid':'Ultrathin carbon support',16);}
"""
s=s.replace('function scene(o,r){',helpers+'\nfunction scene(o,r){')
p.write_text(s,encoding='utf8')
