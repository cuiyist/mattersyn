from pathlib import Path
B=Path(__file__).resolve().parent
old=(B.parent/'jp0105488/build_molecular_assets.py').read_text(encoding='utf-8')
header=old[:old.index('definitions=[')]
header=header.replace('10.1021/jp0105488','10.1021/jp010002l').replace('98a21f9489eda29e1e1f5f40b336661ceb1b27d9468095a9b44ad342a780400b','00ac817e60651f0e7f9faabe85ba18372ac37fea1f0f5d174779c982064b4184')
definitions="""definitions=[('hydrogen-sulfide','Hydrogen sulfide','S','H2S','H2S',True,'Free H2S molecular reference. Gas injection and aqueous delivery are distinct recipe states; solution ionization is not represented by a unique hydrated structure.')]
"""
loop=old[old.index('for id,name,smi,formula,display,conformer,specific in definitions:'):old.index('\ncards=[')]
loop=loop.replace('m=Chem.MolFromSmiles(smi);assert m is not None','m=Chem.AddHs(Chem.MolFromSmiles(smi));assert m is not None').replace('op.bondLineWidth=2','op.bondLineWidth=2;op.updateAtomPalette({16:(.61,.45,.08)})')
tail=old[old.index("write(O/'registry-additions.json'"):]
middle='''
cards=[
 ('identity-cadmium-ii-aqueous','Cadmium(II) ions in water','Cd2+','ionic_components',['Cd²⁺ (aq)','Aqueous cadmium source','Counterion / hydration unspecified'],'Source names aqueous Cd²⁺, not a specific salt. The displayed ion identity does not establish coordination number, counterion, hydrate or solution complex.'),
 ('identity-mercury-ii-aqueous','Mercury(II) ions in water','Hg2+','ionic_components',['Hg²⁺ (aq)','Aqueous mercury source','Counterion / hydration unspecified'],'Source names aqueous Hg²⁺, not a specific salt. The displayed ion identity does not establish coordination number, counterion, hydrate or solution complex.'),
 ('identity-hexametaphosphate-unresolved','Hexametaphosphate stabilizer',None,'unresolved-identity',['Hexametaphosphate','Colloid stabilizer','Salt form / dose unspecified'],'The paper names hexametaphosphate but gives no counterion, concentration, chain-length characterization or confirmed discrete ring structure. No formula or unique molecular geometry is assigned.'),
 ('identity-braun-h2s-water','Hydrogen sulfide in water',None,'mixture',['H₂S + water','Dropwise sulfide feed','Concentration / total volume unreported'],'Source-named aqueous H2S feed. Molecular H2S and water are separate references; no exact solution speciation, concentration or delivered dose is assigned.'),
 ('identity-braun-sapphire','Sapphire continuum-generation plate','Al2O3','support',['Sapphire plate','White-light continuum generation','Optical hardware; not product'],'Source-named sapphire plate. Al2O3 is a chemical identity reference, not a measured nanocrystal phase, unit cell or a synthesis ingredient.'),
 ('identity-braun-glass-cell','Glass optical cell',None,'support',['Glass sample cell','Rotated optical specimen','Glass composition unreported'],'Reported glass cell is optical hardware. Do not infer its glass formulation or transfer its dimensions to the synthesized particles.'),
 ('identity-braun-qdqw-specimens','CdS/HgS quantum-dot quantum-well specimens',None,'specimen',['CdS / HgS / CdS','Systems I, II and III','Separate architectures / specimens'],'Shared acquisition context for separately measured quantum-dot quantum-well systems. This is not a physical mixture or a uniquely identified experimental batch.'),
 ('identity-braun-cds-core','CdS core dispersion','CdS','specimen',['CdS nanocrystal cores','Aqueous colloid','Source core-size discrepancy retained'],'Composition reference for the CdS core dispersion. The general preparation states 3.5 nm while the system description and Figure1 state 3.2 nm; no measured atomic coordinates, phase or exact particle geometry are assigned.')]
for id,name,formula,kind,rows,caption in cards:
 e=base(id,name,formula,kind,caption)
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="900" height="360" viewBox="0 0 900 360"><title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc><rect x="18" y="20" width="864" height="320" rx="20" fill="#f1f6f9" stroke="#cbdce6"/>'
 for y,row,size in zip([120,199,263],rows,[30,22,19]):svg+=f'<text x="450" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{size}" fill="#294451">{html.escape(row)}</text>'
 svg+='</svg>'; (O/e['svgPath']).write_text(svg,encoding='utf-8');e['assetHashes']={'svgPath':sha(O/e['svgPath'])};entries.append(e)
for system,layers,rows in [
 ('i',['CdS','HgS','CdS'],['CdS core: 3.2 nm as assigned','One HgS well: 0.4 nm','CdS cap: 0.4 nm']),
 ('ii',['CdS','HgS','HgS','CdS'],['CdS core: 3.2 nm as assigned','Double-layer HgS well: 0.8 nm','CdS cap: 0.4 nm']),
 ('iii',['CdS','HgS','CdS','CdS','HgS','CdS'],['CdS core: 3.2 nm as assigned','Two HgS wells: 0.4 nm each','CdS barrier: 0.8 nm; cap: 0.4 nm'])]:
 id='identity-braun-system-'+system;name='System '+system.upper()+' quantum-dot quantum-well architecture';cap='Composition-layer schematic following the paper. Rings communicate sequence only, not particle shape, scale or measured geometry. The source cites tetrahedral CdS; its core-size 3.5 nm/3.2 nm discrepancy remains unresolved. No atomistic interface, phase or exact crystal structure is assigned.'
 e=base(id,name,'CdS/HgS/CdS','specimen',cap)
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420" viewBox="0 0 900 420"><title>'+html.escape(name)+'</title><desc>'+html.escape(cap)+'</desc><rect x="10" y="12" width="880" height="396" rx="24" fill="#f5f9fb"/>'
 for i in reversed(range(len(layers))):
  col='#c65b55' if layers[i]=='HgS' else '#56a397';radius=59+i*14
  svg+=f'<circle cx="212" cy="191" r="{radius}" fill="{col}" stroke="#ffffff" stroke-width="2"/>'
 for y,row in zip([120,181,242],rows):svg+=f'<text x="394" y="{y}" font-family="Arial,sans-serif" font-size="22" fill="#294451">{html.escape(row)}</text>'
 svg+='<text x="450" y="342" text-anchor="middle" font-family="Arial,sans-serif" font-size="18" fill="#617580">Layer-sequence illustration · not to scale · no measured atomic model</text></svg>'
 (O/e['svgPath']).write_text(svg,encoding='utf-8');e['assetHashes']={'svgPath':sha(O/e['svgPath'])};entries.append(e)
'''
(B/'build_molecular_assets.py').write_text(header+definitions+loop+middle+tail,encoding='utf-8')
print('Prepared source-specific molecular asset builder')

