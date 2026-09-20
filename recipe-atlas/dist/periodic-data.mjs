const rows=[
 'H He', 'Li Be B C N O F Ne', 'Na Mg Al Si P S Cl Ar',
 'K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr',
 'Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe',
 'Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn',
 'Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og'
];
const names={Cd:'Cadmium',Se:'Selenium',In:'Indium',P:'Phosphorus',Pb:'Lead',S:'Sulfur',Cs:'Caesium',Br:'Bromine',Zn:'Zinc',O:'Oxygen',C:'Carbon',Si:'Silicon',Te:'Tellurium',Cl:'Chlorine',N:'Nitrogen',Au:'Gold',Ag:'Silver',Cu:'Copper',Fe:'Iron'};
Object.assign(names,{H:'Hydrogen',He:'Helium',Li:'Lithium',Be:'Beryllium',B:'Boron',F:'Fluorine',Ne:'Neon',Na:'Sodium',Mg:'Magnesium',Al:'Aluminium',Ar:'Argon',K:'Potassium',Ca:'Calcium',Sc:'Scandium',Ti:'Titanium',V:'Vanadium',Cr:'Chromium',Mn:'Manganese',Co:'Cobalt',Ni:'Nickel',Ir:'Iridium',Pt:'Platinum',Ga:'Gallium',Ge:'Germanium',As:'Arsenic',Kr:'Krypton'});
Object.assign(names,{Rb:'Rubidium',Sr:'Strontium',Y:'Yttrium',Zr:'Zirconium',Nb:'Niobium',Mo:'Molybdenum',Tc:'Technetium',Ru:'Ruthenium',Rh:'Rhodium',Pd:'Palladium',Sn:'Tin',Sb:'Antimony',I:'Iodine',Xe:'Xenon',Ba:'Barium',La:'Lanthanum',Ce:'Cerium',Pr:'Praseodymium',Nd:'Neodymium',Pm:'Promethium',Sm:'Samarium',Eu:'Europium',Gd:'Gadolinium',Tb:'Terbium',Dy:'Dysprosium',Ho:'Holmium',Er:'Erbium',Tm:'Thulium',Yb:'Ytterbium',Lu:'Lutetium'});
Object.assign(names,{Hf:'Hafnium',Ta:'Tantalum',W:'Tungsten',Re:'Rhenium',Os:'Osmium',Hg:'Mercury',Tl:'Thallium',Bi:'Bismuth',Po:'Polonium',At:'Astatine',Rn:'Radon',Fr:'Francium',Ra:'Radium',Ac:'Actinium',Th:'Thorium',Pa:'Protactinium',U:'Uranium',Np:'Neptunium',Pu:'Plutonium',Am:'Americium',Cm:'Curium',Bk:'Berkelium',Cf:'Californium',Es:'Einsteinium',Fm:'Fermium',Md:'Mendelevium',No:'Nobelium',Lr:'Lawrencium'});
Object.assign(names,{Rf:'Rutherfordium',Db:'Dubnium',Sg:'Seaborgium',Bh:'Bohrium',Hs:'Hassium',Mt:'Meitnerium',Ds:'Darmstadtium',Rg:'Roentgenium',Cn:'Copernicium',Nh:'Nihonium',Fl:'Flerovium',Mc:'Moscovium',Lv:'Livermorium',Ts:'Tennessine',Og:'Oganesson'});
let atomicNumber=0;
export const elements=rows.flatMap((line,index)=>line.split(' ').map((symbol,i)=>{
 const z=++atomicNumber,period=index+1;
 let row=period,column=i+1;
 if(period===1&&i===1)column=18;
 if((period===2||period===3)&&i>=2)column=i+11;
 if(period>=6){if(i>=2&&i<=16){row=period+3;column=i+1;}else if(i>=17)column=i-13;}
 return {symbol,number:z,name:names[symbol]||symbol,row,column};
}));
