"""Bounded source-verified edits by independent audit; not a chemistry inference engine."""
from pathlib import Path
P=Path(__file__).with_name('build_review.py')
s=P.read_text(encoding='utf-8')
backup=P.with_name('build_review.pre-independent-audit.py')
if not backup.exists():backup.write_text(s,encoding='utf-8')
def replace(old,new):
    global s
    assert old in s,old
    s=s.replace(old,new)
replace('from pathlib import Path\n','from pathlib import Path\nsys.dont_write_bytecode=True\n')
replace('Fig.3a','Fig.3 upper S1 spectrum')
replace('Fig.3b','Fig.3 lower S2 spectrum')
replace('def variant(label,title):', '''def mark_preparation_inherited(obj,label):
    """Only preparation facts shared by the explicit same-recipe clause are inherited."""
    if isinstance(obj,list):
        for item in obj:mark_preparation_inherited(item,label)
    elif isinstance(obj,dict):
        if obj.get('status')=='reported' and 'value' in obj:
            obj['status']='inherited'
            key='qualifier' if 'unit' in obj else 'note'
            obj[key]=(obj.get(key,'')+' Inherited from S1 under the explicit same-conditions statement for '+label+'.').strip()
            obj['evidence']+=E('Main p.16030, Sample Preparation, final two sentences defining S2–S4')
        elif obj.get('status')=='calculated':
            obj['basis']=(obj.get('basis','')+' Uses unchanged preparation inputs inherited from S1 for '+label+'.').strip()
        for value in obj.values():mark_preparation_inherited(value,label)

def variant(label,title):''')
replace("    old='fu2007-s1';new='fu2007-'+label.lower()", """    for key in ['materials','stocks','operations']:mark_preparation_inherited(r[key],label)
    r['intended_target']['size']['qualifier']='No prespecified numerical size target is reported for this variant.'
    r['intended_target']['phase']['note']='No prespecified target phase is given; any observed phase must be linked to this variant separately.'
    r['intended_target']['morphology']['note']='Part of the paper’s ZnO quantum-dot study; no prespecified shape dimensions are supplied for this variant.'
    old='fu2007-s1';new='fu2007-'+label.lower()""")
replace("for key in ['oleic_acid_amount','nominal_OA_to_Zn_ratio']:comb['parameters'].pop(key)","""comb['description']='Combine the two aqueous stocks without oleic acid, as specified for S2. Unchanged stock charges are inherited from S1. The calculated 100 mL water-charge sum is not a measured final volume; order and addition rates are unspecified.'
for st in s2['stocks']:st['scope']='Unchanged aqueous stock preparation inherited from S1; combine the DEA and zinc stocks without OA. Stock charges in operations repeat these same charges, not additional inputs.'
for key in ['oleic_acid_amount','nominal_OA_to_Zn_ratio']:comb['parameters'].pop(key)""")
replace("s3['operations'][2]['label']='Combine ammonia input, zinc stock and OA'", """s3['operations'][2]['label']='Combine ammonia input, zinc stock and OA'
s3['operations'][2]['description']='Combine the ammonia replacement input, zinc stock and OA under the same-recipe statement for S3. OA and zinc-stock charges are inherited; ammonia charge, concentration, formulation and carrier volume remain unknown, so no total water or mixture volume is calculated.'
s3['stocks'][1]['scope']='Unchanged zinc-stock preparation inherited from S1; combine with the ammonia replacement input and OA. Starting stock molarity is not reaction molarity.'
s3['material_states'][0]['name']='Ammonia input, aqueous zinc stock and OA combined'
for m in s3['materials']:
    if m['id']=='water':m['notes']=[x for x in m['notes'] if 'two stocks' not in x]+['Distilled water for the zinc stock is inherited from S1. The ammonia formulation and carrier volume are unknown. Water is the final dispersion medium; its final volume is unspecified.']""")
replace("for k,v in [('nominal_DEA_to_Zn_ratio',1.25)", "s4['operations'][1]['description']='Prepare 4.0 mM aqueous zinc nitrate for S4. The 50 mL distilled-water charge is inherited from the unchanged common framework; the S4 salt mass and measured final stock volume are not reported.'\nfor k,v in [('nominal_DEA_to_Zn_ratio',1.25)")
replace("loc='Main p.16033, Fig.6'+('b' if parent=='S2' else 'c')", "loc='Main p.16033 treatment discussion; Fig.6'+('b' if parent=='S2' else 'c')+' on p.16032'")
replace("'source_locators':[EXP] if r['record_type']!='procedure' else ['Main p.16033 Fig.6b/c']", "'source_locators':[EXP] if r['record_type']!='procedure' else ['Main p.16033 treatment discussion; Fig.6b/c on p.16032']")
replace("'S1 PL/PLE; luminescence photograph; photostability monitored at 440 nm under 350 nm UV, 130 µW/cm². Plot extends to 48 h.',['S1']", "'a: PL/PLE of S1 and aqueous S2, with both S2 traces scaled by ten; b: photographs of S1/S2 under 350 nm UV; c: S1 photostability at 440 nm under 350 nm UV, 130 µW/cm², over 48 h.',['S1','S2']")
replace(" ('fig7','main',5", " ('surface-reaction-scheme','main',3,[114,604,560,683],'Unnumbered proposed surface reaction of OA with ZnO hydroxyl groups at 80 °C; x/y are schematic occupancies, not measured surface composition.',['S1'],'author_model'),\n ('fig7','main',5")
replace("'ZnO slope113.8,R².998; quinine sulfate slope82.6,R².995.", "'ZnO slope 113.8, R² .998; quinine sulfate slope 82.6, R² .995.") if "'ZnO slope113.8" in s else None
replace('ZnO slope113.8,R².998; quinine sulfate slope82.6,R².995.', 'ZnO slope 113.8, R² .998; quinine sulfate slope 82.6, R² .995.')
replace('size4.2 nm','size 4.2 nm')
replace("['Results: FTIR/PL/photostability','Confinement model'],['Results: absorption, dry-powder PL','Comparison controls']", "['Results: FTIR/PL/photostability','Proposed surface-reaction scheme','Absorption-onset extrapolation'],['Quantum-confinement model','Results: absorption, dry-powder PL','Comparison controls']")
replace("['Main pp.16030–16032 Fig.5a']", "['Main pp.16030–16032 Fig.5a–b; Eq.1 on p.16032']")
replace("coverage['referenced_methods']=[", "coverage['referenced_methods']=[{'reference':'13: Qu and Peng, Journal of the American Chemical Society 2002, 124, 2049','purpose':'Relative quantum-yield calibration reference; the supplied SI gives the adopted method','status':'Cited full paper not reviewed in this batch.'},{'reference':'18: Monticone et al., Journal of Physical Chemistry B 1998, 102, 2854','purpose':'Direct-gap absorption relation used for onset extrapolation','status':'Cited full paper not reviewed in this batch.'},{'reference':'20: Yang et al., Journal of Applied Physics 2001, 90, 4489','purpose':'Prior 0.39 eV redshift comparison, not a measurement of these samples','status':'Cited full paper not reviewed in this batch.'},")
# Narrative typography corrections preserve all scientific values.
for old,new in [('JCPDS89','JCPDS 89'),('Nicolet470','Nicolet 470'),('free-OA1700','free-OA 1700'),('bare-ZnO450','bare-ZnO 450'),('reference15','reference 15'),('Philips3000','Philips 3000'),('gives3.94/3.67','gives 3.94/3.67'),('Model3.92/3.68','Model 3.92/3.68'),('Excitation350','Excitation 350'),('detection432','detection 432'),('the440','the 440'),('in0.5','in 0.5'),('yield.55','yield .55'),('absorbance<.1 at350','absorbance <.1 at 350'),('indices1.33','indices 1.33'),('quartz1.00','quartz 1.00'),('cell;2.5','cell; 2.5'),('Slopes113.8/82.6, R².998/.995','Slopes 113.8/82.6, R² .998/.995'),('UV130','UV 130'),('monitored440','monitored 440'),('.9.4%','. 9.4%'),('first6','first 6'),('spans48','spans 48'),('Kayanuma1988','Kayanuma 1988'),('B1988,38','B 1988, 38'),('Nanotechnology2003,14','Nanotechnology 2003, 14'),(';450','; 450')]:
    s=s.replace(old,new)
replace("coverage['remaining_gaps']=", """coverage['model_and_context_inventory']=[
 {'id':'confinement-equation','evidence_kind':'author_model','source_locators':['Main p.16032, Eq.1 and adjacent paragraph'],'formula_as_printed':'Egap,dot = Egap,bulk + h^2/(8 R^2) (1/me* + 1/mh*) - 0.248 ERyd*','parameters':[{'name':'bulk ZnO gap','value':3.37,'unit':'eV','source_locator':'Main p.16031, absorption discussion'},{'name':'bulk exciton binding energy','value':60,'unit':'meV'},{'name':'electron effective mass','value':0.24,'unit':'m0'},{'name':'hole effective mass as printed','value':1.8,'unit':'mh','caveat':'Self-referential printed expression; not silently normalized to m0.'}],'notes':['R is particle radius, although TEM values 3.8 and 5.0 nm are diameters. h is Planck’s constant. Model outputs 3.92/3.68 eV are distinct from optical extrapolations 3.94/3.67 eV.']},
 {'id':'energy-differences','evidence_kind':'author_comparison','source_locators':['Main p.16032'],'facts':[{'name':'S1 absorption-emission separation','value':1.12,'unit':'eV','status':'author_derived','basis':'3.94 eV absorption onset minus 2.82 eV emission'},{'name':'prior-work highest redshift cited','value':0.39,'unit':'eV','status':'contextual_prior_work','basis':'Reference 20; not a new measurement in this paper.'}]},
 {'id':'proposed-oa-surface-reaction','evidence_kind':'author_model','source_locators':['Main p.16031, unnumbered chemical scheme'],'temperature_C':80,'notes':['Symbolic x/y do not specify measured ligand stoichiometry. The mechanism is an author proposal, not atomically resolved structure.']}
]
coverage['remaining_gaps']=""")
replace('All5 main pages and4 matching SI pages', 'All 5 main pages and 4 matching SI pages')
replace('All7 main figures and3 SI figures are inventoried.', 'All 7 main figures, 3 SI figures and the unnumbered proposed surface-reaction scheme are inventoried.')
replace('Early60 C/20 min is not a20 min', 'Early 60 C/20 min is not a 20 min')
# Reuse unchanged original crops and their hashes when regeneration does not request rendering.
replace("(OUT/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'[local path redacted] "for f in coverage['figures']:\n    crop_path=OUT/f['crop']['path']\n    if crop_path.exists():f['crop']['sha256']=hashlib.sha256(crop_path.read_bytes()).hexdigest()\n(OUT/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'[local path redacted]
P.write_text(s,encoding='utf-8')
print('Applied independent source-review corrections to generator.')
