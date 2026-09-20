from pathlib import Path
B=Path(__file__).resolve().parent
t=(B.parent/'ja036811v/build_molecular_assets.py').read_text(encoding='utf8')
t=t.replace("DOI='10.1021/ja036811v';SH='48bb96493905290ae44c58f2346c6313677041e68ec5a9d50bdc428011c2be9f'","DOI='10.1021/nl0345116';SH='72684e3bf22a2ef173ea1d6d6e31648a1222b2b15bc069bb8fe6cef8d1876a33'")
start=t.index('definitions=[');end=t.index('\n\nfor id,name,smi',start)
t=t[:start]+'''definitions=[('trimethylsilane','Trimethylsilane, literal source name','C[SiH](C)C','C3H10Si','C3H10Si',True,'Connectivity of the compound literally named trimethylsilane in the source. The surface diagram shows a bound trimethylsilyl motif but does not identify a different chlorosilane reagent. This free-molecule reference does not verify the reported surface treatment or its reaction mechanism.')]
'''+t[end:]
t=t.replace("patterns=[('Thiol'","patterns=[('Si–H bond','[Si]-[H]',(.87,.67,.18)),('Thiol'")
cards=[
('identity-sashchiuk-lead-chxbu','Lead-cyclohexanebutirate, as printed',None,'unresolved-identity',['Pb-cHxBu precursor','Source spelling retained','Formula and exact connectivity unresolved'],'The local article supplies a precursor name and abbreviation but no structural drawing, formula, CAS or preparation. Exact carboxylate identity and coordination are unresolved; no guessed molecule is drawn.'),
('identity-sashchiuk-topo-reagent','TOPO reagent: 90% or 99% purity',None,'mixture',['TOPO mother solution','Aldrich 90% or 99% purity','Impurity composition not quantified'],'The source lists 90% or 99% TOPO and discusses phosphonic-acid impurities in the 90% material. A pure TOPO molecule is separately shown as a named component; no complete mixture composition or exact purity assignment for every sample is known.'),
('identity-sashchiuk-pbse-individual','Individual PbSe nanocrystals','PbSe','specimen',['Individual PbSe nanocrystals','Rock-salt phase reported','Dimensions remain specimen-specific'],'PbSe composition and rock-salt phase are source assignments. Cubic individual particles are described and imaged; spherical wording also appears in the source. This schematic is not a measured particle geometry or surface-ligand reconstruction.'),
('identity-sashchiuk-pbse-spheres','Spherical PbSe nanocrystal assemblies','PbSe','specimen',['Spherical polycrystalline assemblies','Randomly oriented PbSe building blocks','Assembly size is not crystallite size'],'The spheres comprise multiple PbSe nanocrystals. Their assembly dimensions, constituent particle sizes and diffraction evidence have separate source scopes. Relative packing and ligand positions are illustrative.'),
('identity-sashchiuk-pbse-wires','Wire-like PbSe nanocrystal assemblies','PbSe','specimen',['Ordered wire-like assemblies','PbSe nanocrystal building blocks','Junctions and gradual orientation changes'],'Source microscopy and SAED support ordered assemblies of PbSe nanocrystals. A straight chain sketch does not establish atomic fusion, measured interface coordinates or a continuous bulk single-crystal wire.'),
('identity-sashchiuk-formvar-grid','Formvar/carbon-coated copper TEM grid',None,'support',['Copper grid · 300 mesh','Amorphous Formvar + evaporated carbon','Microscopy preparation support'],'Source-specific microscopy support. Formvar composition, film thickness and support geometry are not fully specified; no unique molecular formula or measured grid structure is assigned.'),
('identity-sashchiuk-silicon-substrate','p-Doped silicon substrate','Si','support',['p-Doped silicon substrate','Device support and back gate','Dopant identity and concentration unknown'],'Silicon electrical-device support with unspecified p-type dopant and orientation. This is not a PbSe synthesis precursor or an independently synthesized silicon material.'),
('identity-sashchiuk-silica-layer','Silicon oxide layer','SiO2','support',['200 nm oxide layer on silicon','Source labels the stack Si/SiO2','Growth method unreported'],'The paper reports a 200 nm oxide layer and depicts SiO2 on silicon. Its growth process, defect chemistry and atomic coordinates are not supplied.'),
('identity-sashchiuk-pmma','Poly(methyl methacrylate) resist',None,'polymer',['PMMA lithography resist','Spin coating followed by annealing','Molecular weight and formulation unknown'],'Named PMMA resist used in device fabrication. Molecular weight, tacticity, solvent and film thickness are not reported; no unique molecule or chain conformer is claimed.'),
('identity-sashchiuk-titanium','Titanium contact component','Ti','element',['Ti contact component','Evaporated with Au contact leads','Layer thickness and sequence unknown'],'Elemental component of the Ti/Au electrical contacts, not a molecular titanium reagent or PbSe synthesis ingredient. Evaporation thicknesses and detailed layer sequence are unreported.'),
('identity-sashchiuk-gold','Gold contact component','Au','element',['Au contact component','Ti/Au leads shown in device','Contact dimensions unreported'],'Elemental component of the electrical leads. A metal identity illustration is not a molecular gas, exact contact structure or separate gold synthesis.')]
start=t.index('cards=[');end=t.index('\n\nfor id,name,formula',start)
t=t[:start]+'cards='+repr(cards)+t[end:]
# Draw schematic assemblies in their identity cards; leave chemical uncertainty explicit.
start=t.index(" for y,row,size in zip([120,199,263]")
end=t.index("\n svg+='</svg>'",start)
t=t[:start]+''' if 'pbse-' in id:
  if id.endswith('individual'):
   svg+='<rect x="406" y="53" width="88" height="88" rx="5" fill="#739caf" stroke="#2c5268" stroke-width="3"/><path d="M406 53l20-14h88l-20 14M494 53l20-14v88l-20 14" fill="none" stroke="#2c5268" stroke-width="3"/>'
  elif id.endswith('spheres'):
   svg+='<circle cx="450" cy="97" r="66" fill="#dce9ed" stroke="#739caf"/>'
   for x,y,a in [(415,68,16),(449,54,-24),(475,74,12),(398,99,28),(433,96,-17),(469,108,31),(427,132,9),(461,141,-20),(489,131,6)]:svg+=f'<rect x="{x}" y="{y}" width="20" height="20" fill="#739caf" stroke="#2c5268" transform="rotate({a},{x+10},{y+10})"/>'
  else:
   for k in range(9):
    x=278+k*39;y=76+5*math.sin(k/2);svg+=f'<rect x="{x}" y="{y:.2f}" width="34" height="34" fill="#739caf" stroke="#2c5268" stroke-width="2" transform="rotate({k-4},{x+17},{y+17})"/>'
  ys=[199,245,290];sizes=[27,20,18]
 else:ys=[115,193,257];sizes=[28,21,18]
 for y,row,size in zip(ys,rows,sizes):svg+=f'<text x="450" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{size}" fill="#294451">{html.escape(row)}</text>'
'''+t[end:]
(B/'build_molecular_assets.py').write_text(t,encoding='utf8')
print('Prepared source-specific molecular/identity builder.')
