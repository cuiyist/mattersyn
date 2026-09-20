from build_corpus import material_mentions,component_systems
def formulas(s):return {m['formula'] for m in material_mentions(s)}
cases=[
('Evaluation of AgNCs@PEI and AIE-active AuNCs',{'Ag','Au'}),
('ZnONPs and CuInS2QDs nanocrystals',{'ZnO','CuInS2'}),
('Ag3PO4/NP-CQDs composite',{'Ag3PO4'}),
('CDs NCs CNTs PNIPAm RhB IN BY ON OFF PHYSICS CNN',set()),
('Group II-VI and IV-VI materials; Cr(VI) reduction',set()),
('CdTe0.5Se0.5 and CdSe1−xSx and InP1–xAsx',set()),
('Cs2Na0.5Ag0.5InCl6 and NiS1.03 compositions',set()),
('CdSe/CdS, InP/ZnSe/ZnS and CsPbBr3',{'CdSe','CdS','InP','ZnSe','ZnS','CsPbBr3'}),
('MnO2nanosheets',set()),
('BN, BCN, SiC, CoP and H2O2',{'BN','BCN','SiC','CoP','H2O2'}),
('CrO42− and Cs8PbBr64+ and PbBr64– clusters',set()),
('Kitasatospora sp. SeTe27 strain',set()),
('Properties of (Cu2Sn)xZn3(1−x)S3 nanocrystals',set()),
('${\\rm CsPbBr}_{3}$ perovskites',set()),
]
for title,expected in cases:
    actual=formulas(title);assert actual==expected,(title,actual,expected)
assert component_systems('Ag3PO4/NP-CQDs composite')==[]
assert component_systems('CdSe/CdS quantum dots')[0]['components']==['CdSe','CdS']
print(f'Passed {len(cases)} adversarial/positive formula cases and 2 component-system checks.')
