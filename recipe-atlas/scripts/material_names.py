"""Common names for material pages whose name is not set by hand.

`common_name(formula)` returns the standard common name from a fixed table, or the
formula itself when the formula has no standard common name (composites, doped,
non-stoichiometric and non-formula entries). Hand-set names in build_atlas.NAMES
always take precedence.
"""

ELEMENTS = dict(pair.split(':') for pair in (
    'H:Hydrogen He:Helium Li:Lithium Be:Beryllium B:Boron C:Carbon N:Nitrogen O:Oxygen F:Fluorine Ne:Neon '
    'Na:Sodium Mg:Magnesium Al:Aluminum Si:Silicon P:Phosphorus S:Sulfur Cl:Chlorine Ar:Argon K:Potassium '
    'Ca:Calcium Sc:Scandium Ti:Titanium V:Vanadium Cr:Chromium Mn:Manganese Fe:Iron Co:Cobalt Ni:Nickel '
    'Cu:Copper Zn:Zinc Ga:Gallium Ge:Germanium As:Arsenic Se:Selenium Br:Bromine Kr:Krypton Rb:Rubidium '
    'Sr:Strontium Y:Yttrium Zr:Zirconium Nb:Niobium Mo:Molybdenum Tc:Technetium Ru:Ruthenium Rh:Rhodium '
    'Pd:Palladium Ag:Silver Cd:Cadmium In:Indium Sn:Tin Sb:Antimony Te:Tellurium I:Iodine Xe:Xenon '
    'Cs:Cesium Ba:Barium La:Lanthanum Ce:Cerium Pr:Praseodymium Nd:Neodymium Pm:Promethium Sm:Samarium '
    'Eu:Europium Gd:Gadolinium Tb:Terbium Dy:Dysprosium Ho:Holmium Er:Erbium Tm:Thulium Yb:Ytterbium '
    'Lu:Lutetium Hf:Hafnium Ta:Tantalum W:Tungsten Re:Rhenium Os:Osmium Ir:Iridium Pt:Platinum Au:Gold '
    'Hg:Mercury Tl:Thallium Pb:Lead Bi:Bismuth Po:Polonium At:Astatine Rn:Radon Fr:Francium Ra:Radium '
    'Ac:Actinium Th:Thorium Pa:Protactinium U:Uranium Np:Neptunium Pu:Plutonium Am:Americium Cm:Curium '
    'Bk:Berkelium Cf:Californium Es:Einsteinium Fm:Fermium Md:Mendelevium No:Nobelium Lr:Lawrencium '
    'Rf:Rutherfordium Db:Dubnium Sg:Seaborgium Bh:Bohrium Hs:Hassium Mt:Meitnerium Ds:Darmstadtium '
    'Rg:Roentgenium Cn:Copernicium Nh:Nihonium Fl:Flerovium Mc:Moscovium Lv:Livermorium Ts:Tennessine '
    'Og:Oganesson').split())

COMPOUNDS = {
    # III-V and II-VI semiconductors and their common alloys
    'GaAs': 'Gallium arsenide', 'GaN': 'Gallium nitride', 'GaP': 'Gallium phosphide', 'GaSb': 'Gallium antimonide',
    'InAs': 'Indium arsenide', 'InP': 'Indium phosphide', 'InSb': 'Indium antimonide', 'InN': 'Indium nitride',
    'AlN': 'Aluminum nitride', 'AlAs': 'Aluminum arsenide', 'AlSb': 'Aluminum antimonide', 'AlP': 'Aluminum phosphide',
    'BN': 'Boron nitride', 'InGaAs': 'Indium gallium arsenide', 'InGaN': 'Indium gallium nitride',
    'InGaP': 'Indium gallium phosphide', 'AlGaAs': 'Aluminum gallium arsenide', 'AlGaN': 'Aluminum gallium nitride',
    'GaAsSb': 'Gallium arsenide antimonide', 'ZnSe': 'Zinc selenide', 'ZnTe': 'Zinc telluride', 'ZnO': 'Zinc oxide',
    'ZnS': 'Zinc sulfide', 'CdS': 'Cadmium sulfide', 'CdSe': 'Cadmium selenide', 'CdTe': 'Cadmium telluride',
    'HgS': 'Mercury sulfide', 'HgSe': 'Mercury selenide', 'HgTe': 'Mercury telluride', 'CdSeS': 'Cadmium selenide sulfide',
    'CdZnS': 'Cadmium zinc sulfide', 'ZnCdS': 'Zinc cadmium sulfide', 'CdZnSe': 'Cadmium zinc selenide',
    'ZnCdSe': 'Zinc cadmium selenide', 'ZnSeS': 'Zinc selenide sulfide', 'ZnSeTe': 'Zinc selenide telluride',
    'CdTeSe': 'Cadmium telluride selenide', 'Cd3As2': 'Cadmium arsenide', 'Cd3P2': 'Cadmium phosphide',
    'Zn3P2': 'Zinc phosphide', 'SiC': 'Silicon carbide', 'Si3N4': 'Silicon nitride', 'SiGe': 'Silicon germanium',
    # IV-VI, V-VI and other chalcogenides
    'PbS': 'Lead sulfide', 'PbSe': 'Lead selenide', 'PbTe': 'Lead telluride', 'SnS': 'Tin(II) sulfide',
    'SnSe': 'Tin(II) selenide', 'SnTe': 'Tin telluride', 'SnS2': 'Tin(IV) sulfide', 'Bi2S3': 'Bismuth sulfide',
    'Bi2Se3': 'Bismuth selenide', 'Bi2Te3': 'Bismuth telluride', 'Sb2S3': 'Antimony sulfide', 'Sb2Se3': 'Antimony selenide',
    'Sb2Te3': 'Antimony telluride', 'MoS2': 'Molybdenum disulfide', 'MoSe2': 'Molybdenum diselenide',
    'WS2': 'Tungsten disulfide', 'WSe2': 'Tungsten diselenide', 'Cu2S': 'Copper(I) sulfide', 'CuS': 'Copper(II) sulfide',
    'Cu2Se': 'Copper(I) selenide', 'CuSe': 'Copper(II) selenide', 'Ag2S': 'Silver sulfide', 'Ag2Se': 'Silver selenide',
    'Ag2Te': 'Silver telluride', 'FeS2': 'Iron disulfide', 'CoS2': 'Cobalt disulfide', 'NiS2': 'Nickel disulfide',
    'MnS': 'Manganese(II) sulfide', 'CuInS2': 'Copper indium sulfide', 'CuInSe2': 'Copper indium selenide',
    'CuGaS2': 'Copper gallium sulfide', 'AgInS2': 'Silver indium sulfide', 'AgInTe2': 'Silver indium telluride',
    'AgGaS2': 'Silver gallium sulfide', 'AgBiS2': 'Silver bismuth sulfide', 'CuSbS2': 'Copper antimony sulfide',
    'Cu2SnS3': 'Copper tin sulfide', 'Cu2ZnSnS4': 'Copper zinc tin sulfide',
    # oxides
    'TiO2': 'Titanium dioxide', 'SiO2': 'Silicon dioxide', 'ZrO2': 'Zirconium dioxide', 'HfO2': 'Hafnium dioxide',
    'CeO2': 'Cerium dioxide', 'GeO2': 'Germanium dioxide', 'SnO2': 'Tin dioxide', 'MnO2': 'Manganese dioxide',
    'MoO2': 'Molybdenum dioxide', 'MoO3': 'Molybdenum trioxide', 'WO3': 'Tungsten trioxide', 'V2O5': 'Vanadium pentoxide',
    'Al2O3': 'Aluminum oxide', 'MgO': 'Magnesium oxide', 'CaO': 'Calcium oxide', 'NiO': 'Nickel(II) oxide',
    'CoO': 'Cobalt(II) oxide', 'FeO': 'Iron(II) oxide', 'CuO': 'Copper(II) oxide', 'Cu2O': 'Copper(I) oxide',
    'Ag2O': 'Silver oxide', 'In2O3': 'Indium oxide', 'Ga2O3': 'Gallium oxide', 'Y2O3': 'Yttrium oxide',
    'Nd2O3': 'Neodymium oxide', 'Yb2O3': 'Ytterbium oxide', 'Gd2O3': 'Gadolinium oxide', 'Eu2O3': 'Europium oxide',
    'La2O3': 'Lanthanum oxide', 'Bi2O3': 'Bismuth oxide', 'Fe2O3': 'Iron(III) oxide', 'Fe3O4': 'Magnetite',
    'γ-Fe2O3': 'Maghemite', 'Co3O4': 'Cobalt(II,III) oxide', 'Mn3O4': 'Manganese(II,III) oxide',
    'BaTiO3': 'Barium titanate', 'SrTiO3': 'Strontium titanate', 'PbTiO3': 'Lead titanate', 'LiNbO3': 'Lithium niobate',
    'NiFe2O4': 'Nickel ferrite', 'ZnFe2O4': 'Zinc ferrite', 'CoFe2O4': 'Cobalt ferrite', 'MnFe2O4': 'Manganese ferrite',
    'ZnAl2O4': 'Zinc aluminate', 'MgAl2O4': 'Magnesium aluminate', 'ZnGa2O4': 'Zinc gallate', 'Zn2SnO4': 'Zinc stannate',
    'LiMn2O4': 'Lithium manganese oxide', 'Y3Al5O12': 'Yttrium aluminum garnet', 'GdFeO3': 'Gadolinium orthoferrite',
    'Bi2WO6': 'Bismuth tungstate', 'CaWO4': 'Calcium tungstate', 'PbMoO4': 'Lead molybdate',
    'Pb(Zr0.52Ti0.48)O3': 'Lead zirconate titanate', '(Sc2O3)0.08(ZrO2)0.92': 'Scandia-stabilized zirconia',
    # halides, perovskites, carbonates, phosphates, nitrides, carbides
    'CsPbBr3': 'Cesium lead bromide', 'CsPbI3': 'Cesium lead iodide', 'CsPbCl3': 'Cesium lead chloride',
    'CH3NH3PbBr3': 'Methylammonium lead bromide', 'CH3NH3PbI3': 'Methylammonium lead iodide',
    'FAPbBr3': 'Formamidinium lead bromide', 'FAPbI3': 'Formamidinium lead iodide', 'LiYF4': 'Lithium yttrium fluoride',
    'NaYF4': 'Sodium yttrium fluoride', 'CaCO3': 'Calcium carbonate', 'KTiOPO4': 'Potassium titanyl phosphate',
    'Ca10(PO4)6(OH)2': 'Hydroxyapatite', 'TiN': 'Titanium nitride', 'C3N4': 'Carbon nitride', 'CoSi2': 'Cobalt disilicide',
    'CuAlO2': 'Copper aluminum oxide',
}


def common_name(formula):
    """Standard common name for a formula, or the formula alone."""
    text = formula.strip() if isinstance(formula, str) else ''
    return ELEMENTS.get(text) or COMPOUNDS.get(text) or text
