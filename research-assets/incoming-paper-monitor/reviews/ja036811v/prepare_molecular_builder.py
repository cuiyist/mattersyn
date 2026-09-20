from pathlib import Path
B=Path(__file__).resolve().parent
t=(B.parent/'jp010002l/build_molecular_assets.py').read_text(encoding='utf8')
t=t.replace("DOI='10.1021/jp010002l';SH='00ac817e60651f0e7f9faabe85ba18372ac37fea1f0f5d174779c982064b4184'","DOI='10.1021/ja036811v';SH='48bb96493905290ae44c58f2346c6313677041e68ec5a9d50bdc428011c2be9f'")
a=t.index('definitions=');b=t.index('\nfor id,name,smi',a)
t=t[:a]+'''definitions=[
('zinc-acetate-dihydrate','Zinc acetate dihydrate','[Zn+2].CC(=O)[O-].CC(=O)[O-].O.O','C4H10O6Zn','Zn(OAc)2·2H2O',False,'Reported hydrate represented as disconnected formula components. No Zn–acetate coordination, crystal packing or DMSO solution complex is assigned.'),
('cobalt-acetate-tetrahydrate','Cobalt(II) acetate tetrahydrate','[Co+2].CC(=O)[O-].CC(=O)[O-].O.O.O.O','C4H14CoO8','Co(OAc)2·4H2O',False,'Reported hydrate represented as disconnected formula components. No cobalt coordination, hydration shell or DMSO speciation is assigned.'),
('nickel-perchlorate-hexahydrate','Nickel(II) perchlorate hexahydrate','[Ni+2].[O-]Cl(=O)(=O)=O.[O-]Cl(=O)(=O)=O.O.O.O.O.O.O','H12Cl2NiO14','Ni(ClO4)2·6H2O',False,'Reported hydrate formula components. Perchlorate connectivity is a resonance representation, not a measured nickel complex or hydrated crystal.'),
('dodecylamine','Dodecylamine','CCCCCCCCCCCCN','C12H27N','C12H27N',True,'Free dodecylamine connectivity and computed conformer. Surface binding, protonation and ligand density on ZnO are not reconstructed.')]
''' +t[b:]
t=t.replace("('Carboxyl group','C(=O)[O;H1]'","('Carboxylate group','C(=O)[O-]'")
a=t.index('\ncards=');b=t.index('\nfor id,name,formula,kind,rows,caption in cards:',a)
t=t[:a]+'''\ncards=[
('identity-schwartz-zinc-acetate-additive','Zinc acetate clarity additive',None,'unresolved-identity',['Zn(OAc)2 · hydration unspecified','Approximately 10 mg','Only for a cloudy suspension'],'The source writes approximately10mg Zn(OAc)2 for optical-clarity restoration without specifying hydration. The separate main starting salt is dihydrate; that hydration is not silently transferred here.'),
('identity-schwartz-topo-technical','Technical-grade TOPO',None,'mixture',['TOPO-containing technical reagent','Phosphonic-acid impurities reported','Mixture composition unspecified'],'Footnote16 specifies technical-grade TOPO and unidentified phosphonic-acid impurities. The linked pure TOPO structure describes only the named component, not the full reagent or actual surface ligand distribution.'),
('identity-schwartz-zno-specimen','ZnO nanocrystals','ZnO','specimen',['Wurtzite ZnO nanocrystals','Pure-host route','Particle dimensions remain sample-specific'],'Source reports ZnO phase and TEM/electron-diffraction evidence. This identity card is not a measured particle lattice; the separate independent bulk CIF does not reconstruct the synthesized sample.'),
('identity-schwartz-co-specimen','Co-doped ZnO nanocrystals','ZnO:Co','specimen',['Co2+-doped wurtzite ZnO','Dopant loading varies by sample','Feed and incorporated content kept separate'],'Source-assigned substituted Co2+ in ZnO. No exact universal stoichiometry, site occupancy, radial dopant profile or measured atomic coordinates are supplied.'),
('identity-schwartz-ni-specimen','Ni-doped ZnO nanocrystals','ZnO:Ni','specimen',['Ni2+-doped wurtzite ZnO','Dopant loading varies by sample','Feed and incorporated content kept separate'],'Source-assigned substituted Ni2+ in ZnO. No exact universal stoichiometry, site occupancy, radial dopant profile or measured atomic coordinates are supplied.'),
('identity-schwartz-surface-co-specimen','Surface-bound Co on ZnO control',None,'specimen',['Co intentionally bound to ZnO surface','SI Figure S2 cleaning control','Surface-loading preparation incomplete'],'This control has intentionally surface-bound Co and is separate from substitutionally doped ZnO. No exact loading, binding geometry or missing preparation recipe is inferred.'),
('identity-schwartz-co-aggregate-specimen','Co-doped ZnO aggregate powder','ZnO:Co','specimen',['3.6% Co:ZnO aggregate specimen','Slow evaporation from ethanol','Magnetic measurement population'],'Macroscopic aggregates of doped nanocrystals are distinct from isolated colloids. The source prints4.9 and5.0nm precursor sizes in different places. No measured interparticle atomic reconstruction is supplied.'),
('identity-schwartz-quartz','Quartz optical support','SiO2','support',['Quartz disk','Spin-coated optical film support','Thickness and spin settings unreported'],'Source-named optical support, not a synthesis ingredient or a refined quartz crystal. SiO2 identifies the material; no measured substrate structure or thickness is assigned.')]
''' +t[b:]
a=t.index('\nfor system,layers,rows in [');b=t.index("\nwrite(O/'registry-additions.json'",a);t=t[:a]+t[b:]
(B/'build_molecular_assets.py').write_text(t,encoding='utf8')
print('Prepared source-specific molecular builder.')
