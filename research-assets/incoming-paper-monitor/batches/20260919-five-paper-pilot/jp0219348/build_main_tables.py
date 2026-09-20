"""Private, source-faithful transcription of Heo's five main-paper tables.

No source PDF, parent extraction, canonical record, or Site file is modified.
"""
from pathlib import Path
import hashlib
import json
import re
from decimal import Decimal
from datetime import datetime, timezone
import pypdfium2 as pdfium

B = Path(__file__).resolve().parent
SOURCE = Path(r'[local path redacted]')
EXPECTED_SHA = '03e6f3be5375a0e2023a6850c1c6931904be8e3c85c37e0c30effdf6ecf73c01'
ASSETS = B / 'reader-assets'
ASSETS.mkdir(exist_ok=True)
DPI = 400
CROPS = [
    (1, 4, [52, 337, 296, 657], 'Summary of Experimental and Crystallographic Data'),
    (2, 5, [52, 45, 560, 214], 'Positional, Thermal, and Occupancy Parameters of In66–X'),
    (3, 5, [52, 220, 296, 411], 'Selected Interatomic Distances (Å) and Angles (deg)'),
    (4, 6, [316, 45, 560, 155], 'Deviations of Guest Ions and Atoms (Å) from (111) Planes of Six Rings'),
    (5, 6, [316, 163, 560, 410], 'Radii (Å) of Indium Ions in Fully Indium-Exchanged Zeolites'),
]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

assert sha(SOURCE) == EXPECTED_SHA, 'Main PDF has changed.'
doc = pdfium.PdfDocument(SOURCE)
assert len(doc) == 9
manifest = []
for number, page_num, box, title in CROPS:
    page = doc[page_num - 1]
    im = page.render(scale=DPI / 72).to_pil()
    pixel_box = tuple(round(v * DPI / 72) for v in box)
    crop = im.crop(pixel_box)
    target = ASSETS / f'main-table-{number}.png'
    crop.save(target)
    manifest.append({
        'asset_id': f'heo2003-main-table-{number}', 'kind': 'original_table_crop',
        'table_number': number, 'title': title, 'path': str(target),
        'relative_path': f'reader-assets/main-table-{number}.png',
        'source_role': 'main', 'source_path': str(SOURCE), 'source_sha256': EXPECTED_SHA,
        'pdf_page': page_num, 'printed_page': 1119 + page_num,
        'coordinate_system': 'PDF points, origin at upper left; x0,y0,x1,y1',
        'source_crop_box_points': box, 'source_page_size_points': [612, 792],
        'render_dpi': DPI, 'renderer': 'pypdfium2 / PDFium',
        'crop_pixel_box': pixel_box, 'width': crop.width, 'height': crop.height,
        'sha256': sha(target), 'caption_and_footnotes_included': True,
        'content_transform': 'Original PDF rendered and cropped; no redrawing, relabeling, or data repair.',
        'author_visual_inspection': 'passed: actual original crop viewed with complete title, header, cells and footnotes',
        'independent_scientific_audit': 'pending',
    })
    page.close()
doc.close()
write(B / 'main-table-assets.json', {
    'schema': 'mattersyn.main_table_assets.v1', 'doi': '10.1021/jp0219348',
    'status': 'authored_pending_independent_scientific_audit',
    'generated_at': datetime.now(timezone.utc).isoformat(), 'assets': manifest,
})
print(json.dumps({'original_crops': len(manifest), 'source_sha256': EXPECTED_SHA}))

def locator(page, detail):
    return {'source_role': 'main', 'pdf_page': page, 'printed_page': 1119 + page,
            'locator': detail, 'source_sha256': EXPECTED_SHA}

def quantity(raw, unit, multiplier=1, footnotes=None, status='reported', basis=None):
    """Parse printed scalar/ESD without silently filling source blanks or units."""
    if raw is None:
        return {'raw': None, 'value': None, 'unit': unit, 'status': 'not_reported',
                'reason': 'Blank source cell; neither zero nor not applicable is inferred.'}
    clean = raw.replace('−', '-').replace(' ', '')
    match = re.fullmatch(r'([-+]?\d+(?:\.\d+)?)(?:\((\d+)\))?', clean)
    if not match:
        raise ValueError(f'Cannot parse source scalar: {raw}')
    number = Decimal(match[1])
    value = float(number * Decimal(str(multiplier)))
    out = {'raw': raw, 'printed_value': float(number), 'value': value, 'unit': unit,
           'status': status, 'source_to_value_multiplier': multiplier,
           'uncertainty': None, 'footnote_markers': footnotes or []}
    if match[2]:
        decimal_places = len(match[1].split('.')[1]) if '.' in match[1] else 0
        esd = Decimal(match[2]) * Decimal(10) ** (-decimal_places)
        out['uncertainty'] = {'kind': 'estimated_standard_deviation',
                              'raw_digits': match[2], 'printed_scale_value': float(esd),
                              'value': float(esd * Decimal(str(multiplier))), 'unit': unit,
                              'basis': 'Parentheses give uncertainty in the least significant quoted figures.'}
    if basis:
        out['basis'] = basis
    if multiplier != 1:
        out['normalization_status'] = 'curator_unit_scaling_only; printed cell is retained'
    return out

def table_shell(number, page, title, scope):
    return {'table_id': f'heo2003-main-table-{number}', 'table_number': number,
            'title': title, 'source': locator(page, f'Table {number}, title through all footnotes'),
            'original_asset_id': f'heo2003-main-table-{number}', 'scope': scope,
            'independent_scientific_audit': 'pending'}

tables = []
t1 = table_shell(1, 4, 'Summary of Experimental and Crystallographic Data',
    'Source summary of the treatment and diffraction/refinement of the In66–X single crystal. '
    'Experimental prose in main page 2 disagrees with three treatment rows; both versions remain separate. '
    'The two refinement columns concern alternative space-group models of the same diffraction study, not two recipes or independent crystals.')
t1['raw_column_headers'] = ['parameter', 'shared value / Fd3̄m model', 'Fd3̄ model']
t1['shared_rows'] = [
    {'row_id':'crystal-cross-section','raw_cells':['cryst cross-section (mm)','0.15',None],
     'quantities':{'cross_section':quantity('0.15','mm')}},
    {'row_id':'tl-ion-exchange','raw_cells':['ion exchange for Tl+ (days/mL/K)','4/10.0/298',None],
     'quantities':{'duration':quantity('4','day'),'volume':quantity('10.0','mL'),'temperature':quantity('298','K')}},
    {'row_id':'tl-dehydration','raw_cells':['dehydration of Tl–X (days/K)','3/673',None],
     'quantities':{'duration':quantity('3','day'),'temperature':quantity('673','K')}, 'conflict_ids':['tl-dehydration-table-prose']},
    {'row_id':'in-redox','raw_cells':['reaction of Tl–X with In (days/K)','5/623',None],
     'quantities':{'duration':quantity('5','day'),'temperature':quantity('623','K')},'conflict_ids':['in-reaction-duration-table-prose']},
    {'row_id':'water-wash','raw_cells':['washing of In–X with DI water (days/mL)','1/10.0',None],
     'quantities':{'duration':quantity('1','day'),'volume':quantity('10.0','mL')}},
    {'row_id':'in-redehydration','raw_cells':['redehydration of In–X (days/K)','3/673',None],
     'quantities':{'duration':quantity('3','day'),'temperature':quantity('673','K')},'conflict_ids':['in-redehydration-table-prose']},
    {'row_id':'h2s-exposure','raw_cells':['exposure to H2S (atm/h/K)','0.5/12/673',None],
     'quantities':{'pressure':quantity('0.5','atm'),'duration':quantity('12','h'),'temperature':quantity('673','K')}},
    {'row_id':'evacuation','raw_cells':['evacuation (min/K)','10.0/673',None],
     'quantities':{'duration':quantity('10.0','min'),'temperature':quantity('673','K')}},
    {'row_id':'data-temperature','raw_cells':['temp for data collection (K)','294',None],
     'quantities':{'temperature':quantity('294','K')}},
    {'row_id':'mo-wavelengths','raw_cells':['X-radiation (Mo Kα) λ1/λ2 (Å)','0.70930/0.71359',None],
     'quantities':{'lambda1':quantity('0.70930','Å'),'lambda2':quantity('0.71359','Å')}},
    {'row_id':'lattice-a','raw_cells':['unit cell constant, a0 (Å)','24.942(4)',None],
     'quantities':{'a0':quantity('24.942(4)','Å')}},
    {'row_id':'lattice-reflection-count','raw_cells':['no. of reflections for a0','25',None],
     'quantities':{'reflection_count':quantity('25','count')}},
    {'row_id':'scan-technique','raw_cells':['scan technique','ω–2θ',None],
     'value':'ω–2θ'},
    {'row_id':'scan-speed','raw_cells':['scan speed (deg 2θ/min)','0.5',None],
     'quantities':{'scan_speed':quantity('0.5','degree 2θ/min')}},
    {'row_id':'scan-width','raw_cells':['scan width (deg)','0.51 + 0.61*tanθ',None],
     'expression':{'raw':'0.51 + 0.61*tanθ','unit':'degree', 'status':'reported_acquisition_expression'}},
    {'row_id':'lattice-angle-range','raw_cells':['2θ range for a0 (deg)','10–20',None],
     'range':{'min':10,'max':20,'unit':'degree 2θ','status':'reported','raw':'10–20'}},
    {'row_id':'collection-angle-range','raw_cells':['2θ range in data collection (deg)','2–70',None],
     'range':{'min':2,'max':70,'unit':'degree 2θ','status':'reported','raw':'2–70'}},
]
model_specs = [
    ('space-group','space group/no.','Fd3̄m/227','Fd3̄/203',None),
    ('measured-reflections','no. of reflections measured','2335','2335','count'),
    ('unique-reflections','no. of unique reflections, m','1209','2032','count'),
    ('strong-reflections','no. of reflections (Fo > 4σ(Fo))','754','1207','count'),
    ('parameters','no. of parameters, s','44','66','count'),
    ('data-parameter-ratio','data/parameter ratio, m/s','17.1','18.3','dimensionless'),
    ('weights','weighting parameters, a/b','0.0789/296.55','0.0677/620.90',None),
    ('r1','R1 (Fo > 4σ(Fo))^a','0.0583','0.0691','dimensionless'),
    ('wr2','wR2 (all unique data)^b','0.183','0.187','dimensionless'),
    ('goodness-of-fit','goodness of fit^c','1.112','1.080','dimensionless'),
]
t1['model_rows'] = []
for rid, label, selected, other, unit in model_specs:
    row = {'row_id':rid,'raw_cells':[label,selected,other]}
    if unit:
        row['model_values'] = {'Fd3̄m':quantity(selected,unit),'Fd3̄':quantity(other,unit)}
    if rid == 'weights':
        row['model_values'] = {sg:{k:quantity(v,None,basis='Weighting parameter; the source table supplies no unit.')
                                   for k,v in zip(['a','b'],raw.split('/'))}
                               for sg,raw in [('Fd3̄m',selected),('Fd3̄',other)]}
    if rid == 'data-parameter-ratio':
        row['conflict_ids'] = ['ratio-count-definition']
    t1['model_rows'].append(row)
t1['model_context'] = {'selected':{'space_group':'Fd3̄m','international_number':227},
    'alternative':{'space_group':'Fd3̄','international_number':203},
    'reason_for_selected_model':'Main page 3: hkl/khl intensity equality, nearly equal Si–O and Al–O distances in the Fd3̄ trial, and lower error indices.',
    'refinement':'Full-matrix least-squares on F² using all reflections without an nσ cutoff; the strong-reflection R1 subset is not the full fitting data.',
    'evidence':[locator(3,'X-ray Data Collection and Structure Determination'),locator(6,'Space Group Considerations')]}
t1['footnotes'] = [
    {'marker':'a','raw':'R1 = Σ(|Fo − |Fc||)/ΣFo.','equation_id':'table1-r1',
     'transcription_note':'Absolute-value marks and grouping retained as printed; the original crop is authoritative.'},
    {'marker':'b','raw':'wR2 = [Σ{w(Fo² − Fc²)²}/Σw(Fo²)²]^(1/2).','equation_id':'table1-wr2'},
    {'marker':'c','raw':'[Σ{w(Fo² − Fc²)²}/(m − s)]^(1/2), where m and s are the numbers of unique reflections and parameters, respectively.',
     'equation_id':'table1-goodness-of-fit'},
]
t1['related_weight_definition'] = {'raw':'w = 1/[σ²(Fo²) + (aP)² + bP]; P = [max(Fo²,0) + 2Fc²]/3',
    'source':locator(3,'Structure Determination, final weights paragraph'),
    'scope':'Definition of Table 1 refined weighting parameters; not a synthesis equation.'}
tables.append(t1)

t2 = table_shell(2, 5, 'Positional, Thermal, and Occupancy Parameters^a of In66–X',
    'Final Fd3̄m refinement of the product single crystal. Printed occupancies are atoms/ions per unit cell, not fractional site occupation. '
    'The fixed and varied columns are different refinement states of the same structure. The averaged (Si,Al) site does not resolve Si and Al coordinates independently.')
t2['raw_column_headers'] = ['atom','Wyckoff position','x','y','z','U11','U22','U33','U12','U13','U23','occupancy: fixed','occupancy: varied']
t2['column_units'] = {'x':'fractional coordinate ×10^5','y':'fractional coordinate ×10^5','z':'fractional coordinate ×10^5',
    'U11':'U ×10^4','U22':'U ×10^4','U33':'U ×10^4','U12':'U ×10^4','U13':'U ×10^4','U23':'U ×10^4',
    'occupancy: fixed':'atoms or ions per unit cell','occupancy: varied':'atoms or ions per unit cell'}
t2['normalization_note'] = 'Scaled numeric values are simple curator conversions of printed cells: xyz ×10^−5, Uij ×10^−4. '
t2['normalization_note'] += 'Fractional coordinates follow the crystallographic x,y,z context. Å² for Uij follows dimensional reading of the stated temperature factor with a in Å; the footnote itself prints only the ×10^4 scale. '
t2['normalization_note'] += 'No CIF, DFT input, symmetry completion, tensor permutation, coordinate repair, or training admission is implied.'
atom_rows = [
 ['(Si,Al)','192(i)','−5168(8)','12 413(8)','3640(7)','108(9)','68(8)','90(9)','−23(7)','−11(6)','−1(7)','192^c',None],
 ['O(1)','96(h)','−10 116(20)','0^d','10 116(20)','210(24)','184(39)','210(24)','−71(21)','31(29)','−71(21)','96',None],
 ['O(2)','96(g)','26(24)','26(24)','14 727(29)','193(22)','193(22)','189(39)','6(22)','6(22)','56(31)','96',None],
 ['O(3)','96(g)','−2337(28)','7097(19)','7097(19)','122(34)','143(21)','143(21)','−3(25)','27(18)','27(18)','96',None],
 ['O(4)','96(g)','7826(22)','7826(22)','31 976(29)','197(24)','197(24)','154(39)','40(20)','40(20)','50(28)','96',None],
 ['In(U)','8(a)','12 500^d','12 500^d','12 500^d','146(5)','146(5)','146(5)','0','0','0','8','7.9(1)'],
 ['In(I′)','32(e)','6289(3)','6289(3)','6289(3)','159(3)','159(3)','159(3)','−18(3)','−18(3)','−18(3)','32','31.7(3)'],
 ['In(II)','32(e)','25 149(5)','25 149(5)','25 149(5)','271(5)','271(5)','271(5)','−23(6)','−23(6)','−23(6)','25','25.0(4)'],
 ['In(IIa)','32(e)','23 480(194)','23 480(194)','23 480(194)','295(137)','295(137)','295(137)','229(178)','229(178)','229(178)','1','0.8(2)'],
]
t2['rows'] = []
for index, cells in enumerate(atom_rows,1):
    typed = {}
    for col, raw in zip(t2['raw_column_headers'][2:], cells[2:]):
        marks = raw.split('^')[1:] if raw and '^' in raw else []
        clean = raw.split('^')[0] if raw else None
        if col in ['x','y','z']:
            q = quantity(clean,'fractional_coordinate',1e-5,marks,
                         status='fixed_by_symmetry' if 'd' in marks else 'refined',
                         basis='Table 2 footnote a scale; footnote d only on explicitly marked source cells.')
        elif col.startswith('U'):
            q = quantity(clean,'Å²',1e-4,marks,status='reported_refinement_parameter',
                         basis='Table 2 footnote a scale; dimensional unit follows the printed anisotropic temperature factor.')
        else:
            q = quantity(clean,'atoms_or_ions_per_unit_cell',footnotes=marks,
                         status='fixed_final_refinement' if col.endswith('fixed') else 'varied_refinement',
                         basis='Table 2 footnote b; these values are not fractional occupancies.')
        q['raw_cell'] = raw
        typed[col] = q
    t2['rows'].append({'row_id':f'atom-{index:02}', 'atom_label':cells[0], 'raw_cells':cells,
        'wyckoff':{'raw':cells[1],'multiplicity':int(re.match(r'\d+',cells[1])[0]),
                   'letter':re.search(r'\((.)\)',cells[1])[1]},
        'quantities':typed, 'source':locator(5,f'Table 2, {cells[0]} row, all columns')})
t2['footnotes'] = [
 {'marker':'a','raw':'Positional parameters are given ×10^5; thermal parameters are given ×10^4. Numbers in parentheses are the estimated standard deviations in the units of the least significant figure given for the corresponding parameter. The anisotropic temperature factor is exp[−2π²a^−2(U11h² + U22k² + U33l² + 2U12hk + 2U13hl + 2U23kl)].',
  'equation_id':'table2-anisotropic-temperature-factor'},
 {'marker':'b','raw':'Occupancy factors are given as the number of atoms or ions per unit cell.'},
 {'marker':'c','raw':'Occupancy for (Si) = 96 and (Al) = 96.'},
 {'marker':'d','raw':'Fixed by symmetry.'},
]
t2['related_prose'] = [
 {'source':locator(3,'Structure Determination, last two model additions and final refinement'),
  'note':'Main text gives freely refined In(II)/In(U)/In(I′)/In(IIa) occupancies 25.0(4)/7.9(1)/31.7(3)/0.8(2), followed by final anisotropic cycles fixed at 25/8/32/1. The Table 2 columns must remain distinct.'},
 {'source':locator(3,'Structure Determination, scattering factors paragraph'),
  'note':'Indium charge assignments and the (Si,Al)^1.75+ mean scattering factor are model assumptions. They are not independently resolved site-specific oxidation states.'},
 {'source':locator(6,'Space Group Considerations'),
  'note':'The source explains loss of long-range Si/Al ordering and selects Fd3̄m. This does not resolve the table-footnote 96/96 versus nominal 100/92 elemental tally.'},
]
t2['conflict_ids'] = ['nominal-versus-averaged-framework']
t2['source_literal_caution'] = 'O(2), O(3) and O(4) U12/U13/U23 remain in the exact printed header order. No tensor entries have been swapped to impose presumed symmetry.'
tables.append(t2)

t3 = table_shell(3,5,'Selected Interatomic Distances (Å) and Angles (deg)^a',
    'Selected geometry of the final In66–X structural model; framework atoms are averaged (Si,Al) sites. '
    'Most entries carry source ESDs; the central tetrahedral angle is imposed by symmetry, rather than an independently measured angle.')
t3['raw_layout'] = 'Two side-by-side label/value lists; preserved as separate left and right blocks to avoid inventing pairwise associations between horizontal neighbors.'
left_geometry = [
 ('(Si,Al)–O(1)','1.636(3)','Å'),('(Si,Al)–O(2)','1.681(4)','Å'),
 ('(Si,Al)–O(3)','1.732(4)','Å'),('(Si,Al)–O(4)','1.644(3)','Å'),
 ('mean of (Si,Al)–O','1.673(4)','Å'),('In(I′)–O(3)','2.170(7)','Å'),
 ('In(II)–O(2)','2.600(7)','Å'),('In(IIa)–O(2)','2.246(32)','Å'),
 ('(Si,Al)–O(1)–(Si,Al)','146.8(5)','degree'),('(Si,Al)–O(2)–(Si,Al)','135.2(5)','degree'),
 ('(Si,Al)–O(3)–(Si,Al)','126.6(4)','degree'),('(Si,Al)–O(4)–(Si,Al)','147.4(5)','degree'),
]
right_geometry = [
 ('O(1)–(Si,Al)–O(2)','113.9(3)','degree'),('O(1)–(Si,Al)–O(3)','108.4(3)','degree'),
 ('O(1)–(Si,Al)–O(4)','113.5(4)','degree'),('O(2)–(Si,Al)–O(3)','102.5(3)','degree'),
 ('O(2)–(Si,Al)–O(4)','107.8(4)','degree'),('O(3)–(Si,Al)–O(4)','110.5(4)','degree'),
 ('In(U)–In(I′)','2.6831(13)','Å'),('In(I′)–In(U)–In(I′)','109.47^b','degree'),
 ('O(2)–In(II)–O(2)','88.1(3)','degree'),('O(2)–In(IIa)–O(2)','111.7(20)','degree'),
 ('O(3)–In(I′)–O(3)','100.10 (23)','degree'),
]
t3['blocks'] = []
for name, entries in [('left',left_geometry),('right',right_geometry)]:
    rows = []
    for index,(label,raw,unit) in enumerate(entries,1):
        marks = ['b'] if '^b' in raw else []
        q = quantity(raw.split('^')[0],unit,footnotes=marks,
                     status='fixed_by_symmetry' if marks else 'reported_refined_geometry')
        if marks:
            q['basis'] = 'Source says exactly the tetrahedral angle by symmetry; 109.47 is its printed decimal representation, not a measured two-decimal exact value.'
        rows.append({'row_id':f'{name}-{index:02}','raw_cells':[label,raw],
                     'quantity':q,'source':locator(5,f'Table 3, {name} block, {label}')})
    t3['blocks'].append({'block_id':name,'raw_columns':['atom sequence','value'],'rows':rows})
t3['footnotes'] = [
 {'marker':'a','raw':'Numbers in parentheses are the estimated standard deviations in the units of the least significant digit given for the corresponding parameter.'},
 {'marker':'b','raw':'Exactly the tetrahedral angle by symmetry.'},
]
t3['related_prose'] = {'source':locator(7,'Subsection (c), Dipositive Indium Ions at Sites I′ (more likely 1.75+) and II′, including later In(IIa) paragraph'),
    'note':'Rounded prose forms 100.1(2)°, 112(2)° and 2.25(3) Å remain compatible rounded presentations of the table values 100.10(23)°, 111.7(20)° and 2.246(32) Å. They do not establish separate specimens.'}
tables.append(t3)

t4 = table_shell(4,6,'Deviations of Guest Ions and Atoms (Å) from (111) Planes of Six Rings',
    'Geometric offsets relative to two different oxygen-defined ring planes in the final In66–X model. '
    'Signs have the table-specific directions stated in its footnotes; the listed charge assignments are tentative author interpretations.')
t4['blocks'] = []
for name, header, entries in [
    ('O2-S6R','At O(2)s of S6Rs^a',[['In(II)','II','1+','1.55'],['In(IIa)','II','2+','0.83']]),
    ('O3-D6R','At O(3)s of D6Rs^b',[['In(I′)','I′','ca. 2+','1.01'],['In(U)^c','U','0','3.69']]),
]:
    rows=[]
    for index,cells in enumerate(entries,1):
        rows.append({'row_id':f'{name}-{index:02}','raw_cells':cells,
            'deviation':quantity(cells[3],'Å',status='reported_model_geometry'),
            'charge':{'raw':cells[2],'status':'author_tentative_assignment',
                'qualifier':'approximately' if cells[2].startswith('ca.') else None},
            'source':locator(6,f'Table 4, {header}, {cells[0]} row')})
    t4['blocks'].append({'block_id':name,'raw_header':header,
        'raw_columns':['ions or atoms','site','charge','deviation'],'rows':rows})
t4['footnotes'] = [
 {'marker':'a','raw':'A positive deviation indicates that the ion lies in the supercage.'},
 {'marker':'b','raw':'A positive deviation indicates that the ion or atom lies in the sodalite unit.'},
 {'marker':'c','raw':'At the very center of the sodalite unit.'},
]
t4['missingness'] = ['The table supplies no ESDs for these four offsets.',
    'Site-specific charges are not directly resolved by the XPS spectrum. The source discusses In(I′) as approximately 2+ or 1.75+ when choosing a 7+ indium cluster model.']
tables.append(t4)

t5 = table_shell(5,6,'Radii^a (Å) of Indium Ions in Fully Indium-Exchanged Zeolites',
    'Author-derived effective indium ionic radii, obtained by subtracting 1.320 Å for O− from the nearest framework-oxygen approach distance. '
    'These are not nanocluster/particle sizes. Prior In–A and In87/88–X rows are cited comparisons; the final In66–X block compares two space-group refinements of the current product, not independent syntheses.')
t5['raw_spanning_header'] = 'oxidation no. and sites (zeolites A/X)'
t5['columns'] = [
 {'column_id':'crystal','raw_header':'crystal'},
 {'column_id':'one-plus-ring-large','raw_charge_header':'1+','raw_site_header':'I′^b/II^c',
  'zeolite_A_site':'I′','zeolite_X_site':'II','footnote_markers':['b','c'],'unit':'Å'},
 {'column_id':'one-plus-sodalite','raw_charge_header':'1+','raw_site_header':'I′^d/I′^d',
  'zeolite_A_site':'I′','zeolite_X_site':'I′','footnote_markers':['d'],'unit':'Å'},
 {'column_id':'one-plus-other','raw_charge_header':'1+','raw_site_header':'II^e,f/III′^f,g',
  'zeolite_A_site':'II','zeolite_X_site':'III′','footnote_markers':['e','f','g'],'unit':'Å'},
 {'column_id':'higher-charge-sodalite','raw_charge_header':'1.75+ or 2+','raw_site_header':'I′^d/I′^d',
  'zeolite_A_site':'I′','zeolite_X_site':'I′','footnote_markers':['d'],'unit':'Å'},
]
radii_rows = [
 ('in-a','In–A^h',['1.253','1.341','1.290','1.039'],'cited_comparison',32,None),
 ('in-a-s2','In–A(S2)^i',['1.258','1.19','1.29','1.046'],'cited_comparison',33,None),
 ('in-a-h2s','In–A(H2S)^j',['1.255','1.367','1.29','1.032'],'cited_comparison',35,None),
 ('in-a-average','average',['1.255','1.30','1.29','1.039'],'author_average_of_cited_comparisons',None,None),
 ('in88-x','In88–X^k,l',['1.254','1.206','1.20','0.933'],'cited_comparison',34,'Fd3̄'),
 ('in87-x','In87–X^k,m',['1.290','1.188','1.31','0.908'],'cited_comparison',34,'Fd3̄m'),
 ('prior-in-x-average','average',['1.272','1.197','1.26','0.921'],'author_average_of_cited_comparisons',None,None),
 ('in66-x-fd3bar','In66–X^l',['1.281',None,None,'0.852'],'current_product_alternative_refinement',None,'Fd3̄'),
 ('in66-x-fd3barm','In66–X^m',['1.280',None,None,'0.850'],'current_product_selected_refinement',None,'Fd3̄m'),
 ('in66-x-average','average',['1.281',None,None,'0.851'],'author_average_of_current_refinements',None,None),
]
t5['rows'] = []
for rid,label,vals,scope,ref,sg in radii_rows:
    t5['rows'].append({'row_id':rid,'raw_cells':[label,*vals],'source_scope':scope,
        'cited_reference_number':ref,'space_group':sg,
        'values':{col['column_id']:quantity(raw,'Å',status='author_derived',
                   basis='Table 5 footnote a; printed author value retained, not recalculated or interpreted as a particle radius.')
                  for col,raw in zip(t5['columns'][1:],vals)},
        'source':locator(6,f'Table 5, {rid} row')})
t5['row_groups'] = [
    {'group_id':'cited-zeolite-a','rows':['in-a','in-a-s2','in-a-h2s','in-a-average']},
    {'group_id':'cited-zeolite-x','rows':['in88-x','in87-x','prior-in-x-average']},
    {'group_id':'current-in66-x-refinements','rows':['in66-x-fd3bar','in66-x-fd3barm','in66-x-average']},
]
t5['footnotes'] = [
 {'marker':'a','raw':'The radius was calculated by subtracting that of O− (1.320 Å) from its approach distance to the nearest framework oxygen.'},
 {'marker':'b','raw':'Opposite six ring in the large cavity.'},
 {'marker':'c','raw':'Opposite six ring in the supercage.'},
 {'marker':'d','raw':'Opposite six ring in the sodalite unit.'},
 {'marker':'e','raw':'Near the eight ring in the large cavity.'},
 {'marker':'f','raw':'Averaged when more than one position is present at this site.'},
 {'marker':'g','raw':'Opposite four rings in the supercage.'},
 {'marker':'h','raw':'Data from ref 32.','reference_number':32,'external_reference_inspection':'not performed in this table-authoring task'},
 {'marker':'i','raw':'Data from ref 33.','reference_number':33,'external_reference_inspection':'not performed in this table-authoring task'},
 {'marker':'j','raw':'Data from ref 35.','reference_number':35,'external_reference_inspection':'not performed in this table-authoring task'},
 {'marker':'k','raw':'Data from ref 34.','reference_number':34,'external_reference_inspection':'not performed in this table-authoring task'},
 {'marker':'l','raw':'Refined in the space group Fd3̄.'},
 {'marker':'m','raw':'Refined in the space group Fd3̄m.'},
]
t5['derivation'] = {'expression':'r(In) = nearest In–framework-O approach distance − 1.320 Å',
    'oxygen_reference':quantity('1.320','Å',status='author_assumed_reference_radius'),
    'oxygen_charge_as_printed':'O−','uncertainty_propagation':'No radius ESDs or propagation are supplied in Table 5.',
    'source':locator(6,'Table 5 footnote a'),
    'blank_cells':'Six cells in the current In66–X block are blank. They remain null, not zero and not an inferred absence of indium.'}
t5['related_prose'] = [
 {'source':locator(6,'Assignment of Tentative Oxidation States, cluster-charge discussion'),
  'note':'The source cannot distinguish In^1.75+–O from In^2+–O by these bond lengths. The higher-charge header retains both assignments.'},
 {'source':locator(7,'Continuation of subsection (b) and subsection (c), ionic-radius comparisons'),
  'note':'The discussion compares current radii around 1.28 and 0.85 Å with prior zeolites and with tabulated ionic radii; the derived table values are not direct ionic-radius measurements.'},
]
tables.append(t5)

conflicts = [
 {'conflict_id':'tl-dehydration-table-prose','status':'unresolved_source_conflict',
  'table_version':{'duration':quantity('3','day'),'temperature':quantity('673','K'),'source':locator(4,'Table 1, dehydration of Tl–X')},
  'prose_version':{'duration':quantity('48','h'),'temperature':quantity('623','K'),'pressure':quantity('1','Torr',1e-6,basis='Source prints 1 ×10^−6 Torr.'),
                   'source':locator(2,'Experimental Section, several crystals of colorless Tl–X were completely dehydrated')},
  'disposition':'Retain both versions; no preferred temperature or duration selected from this table extraction.'},
 {'conflict_id':'in-reaction-duration-table-prose','status':'unresolved_source_conflict',
  'table_version':{'duration':quantity('5','day'),'temperature':quantity('623','K'),'source':locator(4,'Table 1, reaction of Tl–X with In')},
  'prose_version':{'duration':quantity('96','h'),'temperature':quantity('623','K'),'source':locator(2,'Experimental Section, brought into contact with In0')},
  'disposition':'Five days and 96 h are different reported reaction durations. Do not merge them into a single exact protocol.'},
 {'conflict_id':'in-redehydration-table-prose','status':'unresolved_source_conflict',
  'table_version':{'duration':quantity('3','day'),'temperature':quantity('673','K'),'source':locator(4,'Table 1, redehydration of In–X')},
  'prose_version':{'duration':quantity('48','h'),'temperature':quantity('623','K'),'pressure':quantity('1','Torr',1e-6,basis='Source prints 1 ×10^−6 Torr.'),
                  'source':locator(2,'Experimental Section, washed crystal lodged in a fine Pyrex capillary and then dehydrated')},
  'disposition':'Retain both versions, including their different temperatures and durations.'},
 {'conflict_id':'nominal-versus-averaged-framework','status':'unresolved_source_composition_difference',
  'table_version':{'Si_atoms_per_cell':96,'Al_atoms_per_cell':96,'source':locator(5,'Table 2, (Si,Al) row and footnote c')},
  'prose_version':{'Si_atoms_per_cell':100,'Al_atoms_per_cell':92,'O_atoms_per_cell':384,
      'raw_formula':'Na92Si100Al92O384','source':locator(2,'Experimental Section, starting sodium zeolite X unit-cell stoichiometry')},
  'related_sources':[locator(6,'Space Group Considerations and Assignment of Tentative Oxidation States')],
  'disposition':'Keep nominal chemical framework and averaged refinement occupancy distinct. Loss of ordering is discussed, but no equivalence or corrected chemical formula is established. No CIF or charge-balanced atomistic training example is admitted.'},
 {'conflict_id':'ratio-count-definition','status':'curator_arithmetic_identified_source_inconsistency',
  'source':locator(4,'Table 1, unique-reflection m, strong-reflection counts, parameter s, m/s ratio; footnote c'),
  'printed_ratios':{'Fd3̄m':'17.1','Fd3̄':'18.3'},
  'source_defined_m':{'Fd3̄m':1209,'Fd3̄':2032},'source_defined_s':{'Fd3̄m':44,'Fd3̄':66},
  'curator_check':{'unique_div_parameters':{'Fd3̄m':1209/44,'Fd3̄':2032/66},
                   'strong_div_parameters':{'Fd3̄m':754/44,'Fd3̄':1207/66}},
  'interpretation':'Printed 17.1 and 18.3 follow the strong-reflection counts divided by the parameters, whereas the row m and footnote c define m as unique reflections. This is a curator arithmetic observation, not an author correction.',
  'disposition':'Retain all original counts and ratios. Do not silently change m, the fitting set, the table ratios, or the goodness-of-fit definition.'},
 {'conflict_id':'subsection-site-label','status':'unresolved_source_label_inconsistency',
  'heading_version':{'raw':'(c) Dipositive Indium Ions at Sites I′ (more likely 1.75+) and II′.',
                     'source':locator(7,'Subsection (c) heading, left column')},
  'body_and_table_version':{'raw':'another site II, at In(IIa)',
      'sources':[locator(7,'Subsection (c), Finally, one In2+ ion per unit cell'),
                 locator(5,'Table 2, In(IIa) row'),locator(6,'Table 4, In(IIa) site II row')]},
  'disposition':'The subsection heading prints II′; its body and Table 4 use site II for In(IIa). Preserve the discrepancy without creating an additional measured II′ indium position.'},
]

out = {'schema':'mattersyn.main_tables.v1','source_id':'heo2003','doi':'10.1021/jp0219348',
    'authoring_scope':'Complete transcription of all five main-paper tables with relevant surrounding method, refinement and radius-interpretation text. Not a complete main+SI extraction and not an independent scientific audit.',
    'status':'authored_pending_independent_scientific_audit','author':'/root/peng1998_reader_assets',
    'created_at':datetime.now(timezone.utc).isoformat(),
    'source':{'role':'main','path':str(SOURCE),'sha256':EXPECTED_SHA,'page_count':9,'hash_reverified':True},
    'coverage':{'text_pages_read':[2,3,4,5,6,7],'full_page_images_visually_inspected':[4,5,6,7],
        'original_crops_individually_inspected':[a['asset_id'] for a in manifest],
        'si_scope':'SI table comparison is outside this bounded main-table authoring task; no SI transcription or independent audit is claimed.'},
    'transcription_conventions':[
        'All scientific cells and all footnotes are retained. Superscript footnote markers use ^letter in raw text; subscripts may be represented by adjacent digits. Original PDF crops preserve exact typography.',
        'Space-group overbars use the Unicode combining overbar on 3. A prime is distinct from the letter I, and site labels remain source-specific.',
        'Raw decimal precision, spaces within large integers, parenthetical ESD digits, signed values, and source blanks are retained. Numeric normalizations are separately identified.',
        'Raw rows do not infer missing cells, sample identities, reference-paper inspection, tensor corrections, or experimental conditions beyond their source scope.',
    ],
    'tables':tables,'conflicts':conflicts,
    'admission':{'canonical_record_created':False,'cif_created':False,'dft_input_created':False,
                 'training_admission':'not evaluated; unresolved source conflicts and scientific audit remain'},
}
counts = {'tables':len(tables),'table1_shared_rows':len(t1['shared_rows']),
    'table1_model_rows':len(t1['model_rows']),'table2_atom_rows':len(t2['rows']),
    'table2_numeric_cells':sum(1 for r in t2['rows'] for q in r['quantities'].values() if q['value'] is not None),
    'table3_geometry_entries':sum(len(b['rows']) for b in t3['blocks']),
    'table4_offsets':sum(len(b['rows']) for b in t4['blocks']),
    'table5_rows':len(t5['rows']),'table5_numeric_radius_cells':sum(q['value'] is not None for r in t5['rows'] for q in r['values'].values()),
    'table5_blank_radius_cells':sum(q['value'] is None for r in t5['rows'] for q in r['values'].values()),
    'footnotes':sum(len(t['footnotes']) for t in tables),'source_conflicts_or_differences':len(conflicts),
    'original_assets':len(manifest)}
out['counts'] = counts
write(B/'main-tables.json',out)
assert counts['tables']==5 and counts['table2_atom_rows']==9
assert counts['table3_geometry_entries']==23 and counts['table4_offsets']==4
assert counts['table5_rows']==10 and counts['table5_blank_radius_cells']==6
assert t2['rows'][7]['quantities']['occupancy: fixed']['value']==25
assert t2['rows'][7]['quantities']['occupancy: varied']['uncertainty']['value']==0.4
assert t2['rows'][2]['quantities']['U23']['raw']=='56(31)'
assert t3['blocks'][1]['rows'][6]['quantity']['uncertainty']['value']==0.0013
assert t3['blocks'][1]['rows'][-1]['quantity']['uncertainty']['value']==0.23
assert all(sha(Path(a['path']))==a['sha256'] for a in manifest)
write(B/'main-tables-author-check.json',{'status':'passed_author_integrity_checks_not_independent_audit',
    'created_at':datetime.now(timezone.utc).isoformat(),'counts':counts,
    'main_tables_sha256':sha(B/'main-tables.json'),'asset_manifest_sha256':sha(B/'main-table-assets.json'),
    'checks':['Source PDF hash and nine-page count unchanged.',
              'All five tables have original crops, footnotes, and locators.',
              'Expected row counts and source blanks preserved.',
              'Representative uncertainty scales and literal U23 cell checked.',
              'All five actual crop file hashes match the asset manifest.'],
    'independent_scientific_audit':'pending'})
print(json.dumps(counts))
