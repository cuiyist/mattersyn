from pathlib import Path
S=Path(__file__).resolve().parents[4]/'recipe-atlas'
p=S/'dist/chemical-viewer.mjs';t=p.read_text(encoding='utf-8')
old='viewer.addModel().addAtoms(atoms(model));viewer.setStyle'
new="viewer.addModel().addAtoms(atoms(model));for(const atom of model.atoms.filter(a=>a.isotope)){const symbol=atom.element??atom.elem;viewer.addLabel((atom.isotope===2&&symbol==='H'?'²H':String(atom.isotope)+symbol),{position:{x:atom.x,y:atom.y,z:atom.z},fontSize:14,fontColor:'#174563',backgroundOpacity:0,inFront:true});}viewer.setStyle"
if old in t:t=t.replace(old,new,1)
assert 'model.atoms.filter(a=>a.isotope)'in t
p.write_text(t,encoding='utf-8')
print('Isotope labels preserved in rotatable molecular references.')
