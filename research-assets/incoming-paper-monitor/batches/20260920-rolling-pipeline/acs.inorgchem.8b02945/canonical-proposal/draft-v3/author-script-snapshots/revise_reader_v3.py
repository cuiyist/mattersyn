"""Preserved, display-only Friedfeld reader correction; never writes Site or v2."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
import hashlib, json, re, shutil, sys
sys.dont_write_bytecode = True
C = Path(__file__).resolve().parent
F = C.parent
V2 = C / 'draft-v2'
O = C / 'draft-v3'
S = Path('[local path redacted]')
sys.path.insert(0, str(S / 'scripts'))
import build_paper_reviews as consumer
from dataset_lib import validate_record, eligibility, build_groups

def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, x): Path(p).write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def resolve(x, p):
    for k in p.strip('/').split('/') if p else []:
        k = k.replace('~1', '/').replace('~0', '~')
        x = x[int(k)] if isinstance(x, list) else x[k]
    return x

checks = []
def ck(label, passed):
    checks.append({'check': label, 'passed': bool(passed)})
    assert passed, label

assert not O.exists(), 'A version directory is immutable once created; choose another version.'
base_freeze = read(V2 / 'package-freeze.json')
ck('Exact independent-review input freeze', sha(V2 / 'package-freeze.json') == 'ff8767ef6a51f4184825de335dfe9906fab80e53b97e641fa534f6344f25a112')
for p, h in base_freeze['bound_files'].items(): ck('Preserved v2 file ' + p, sha(V2 / p) == h)
for p, h in base_freeze['external_bound_inputs'].items(): ck('Preserved source input ' + p, sha(p) == h)
# Retain the complete predecessor at its original path; do not copy its freeze as a new one.
shutil.copytree(V2, O, ignore=shutil.ignore_patterns('package-freeze.json'))
historic = O / 'inherited-v2-validation'
historic.mkdir()
for rel in ['author-validation.json', 'reader/reader-author-validation.json']:
    target = historic / Path(rel).name
    shutil.copyfile(O / rel, target)

old = read(V2 / 'reader/friedfeld2019.json')
r = deepcopy(old)
old_items = {i['id']: i for sec in old['reader_sections'] for i in sec['items']}
items = {i['id']: i for sec in r['reader_sections'] for i in sec['items']}

# These replacements apply ONLY to the reader's explicitly named display fields.
# Literal source JSON, operation_contexts, quantitative facts and evidence are untouched.
REPLACEMENTS = {
    'Purchased1M in2-Me-THF': 'Purchased as a 1 M solution in 2-Me-THF',
    '99%13C': '99% 13C', 'cites43/45': 'cites references 43 and 45',
    'cited43/45': 'cited references 43 and 45',
    'explicitly1-ODE': 'explicitly identifies 1-ODE',
    'BathCO2': 'Bath CO2', 'aqueousHCl': 'aqueous HCl',
    'Aqueous1M': 'Aqueous 1 M', 'Three20': 'Three 20',
    'in2-Me-THF': 'in 2-Me-THF', 'inODE': 'in ODE',
    'inject;20': 'inject; 20', 'reachpH2': 'reach pH 2',
    'LabeledMSC': 'Labeled MSC', 'UnlabeledMSC': 'Unlabeled MSC',
    'Labeledindium': 'Labeled indium', 'Low-temperatureMSC': 'Low-temperature MSC',
    'PowderXRD': 'Powder XRD', 'acidNMR': 'acid NMR',
    'myristateMSC': 'myristate MSC', 'initialMSC': 'initial MSC ',
    'extended-timeTEM': 'extended-time TEM', 'exactimageages': 'exact image ages',
    'by250': 'by 250', 'describingMSC': 'describing MSC',
    'ontemperature': 'on temperature', 'R²0.987': 'R² = 0.987',
    'At250': 'At 250', 'factor-of10': 'factor-of-10',
    'onset130': 'onset 130', 'with20[InP]': 'with 20[InP]',
    'plus17In': 'plus 17In', 'path1': 'path 1', 'path2': 'path 2',
    'path3': 'path 3', 'addsP(SiMe3)3': 'adds P(SiMe3)3',
    'FiguresS1': 'Figures S1', 'dx2.7324': 'dx 2.7324',
    'versus2.7325': 'versus 2.7325', 'says49°': 'says 49°', 'is51.2843': 'is 51.2843',
}
def clean(s):
    for a, b in REPLACEMENTS.items(): s = s.replace(a, b)
    s = re.sub(r'\b(130|150|200|250|300)C(?=\b|\d)', r'\1 °C ', s)
    s = re.sub(r'\bS (\d+)', r'S\1', s)
    s = re.sub(r'(?<=\d)°C', ' °C', s)
    s = re.sub(r'°C(?=\d)', '°C ', s)
    return re.sub(r' +', ' ', s).strip()

conflicts = {
 'C1': 'The main text gives −35 °C for the low-temperature NMR experiment, whereas Figure 1 labels −30 °C. Both values are retained.',
 'C2': 'The main prose gives a 25 °C lower endpoint for optical heating, whereas the Figure 1B caption and Figure S3 legend give 20 °C.',
 'C3': 'The materials section describes a purchased 1 L break-seal vessel; the preparation describes a 1.90 L bulb containing 40.9 mmol. The two container volumes are not reconciled.',
 'C4': 'The general 31P NMR description names a 700 MHz instrument, whereas Figure 4 literally prints 202 Hz. The nucleus, instrument and caption frequency remain separately scoped.',
 'C5': 'Figure 4A and Figure S13 describe pretreatment at 130 °C for 30 h; main page 5 and Figures S14–S16 describe 72 h. Figure 4B refers to these samples, but the exact cross-panel specimen match is unresolved.',
 'C6': 'The blue comparison trace in Figure S14 is labeled oleate MSC, whereas the main experiment is described as myristate MSC. The control ligand identity is not inferred.',
 'C7': 'Figure S19 describes the subsequent ramp with the printed phrase “at a rate of 1800 °C.” No time denominator is supplied, so the expression is not converted to a normalized heating rate.',
 'C8': 'The Figure S22 table, axis and caption use eV for values from 0.2965 to 0.2102. The magnitude and unit remain as printed, without rescaling or an imposed photon-energy correction.',
 'C9': 'The kinetic plots use different minute/second axes, concentration rounding and coefficient precision. The Figure S36 low-concentration slope of −3.64052 is retained despite an apparent mismatch with the plotted slope. The indium-fit intercepts in Figures S30 and S31 remain distinct: 2.25e-4 and 2.26e-4.',
 'C10': 'Near 26° in Figure S38, the fit box gives 60.7828/26.5841/1.67, whereas the prose gives 38.2411/26.4049/1.4908. Other S38 widths differ in precision. Near 44° in Figure S39, the width is 2.7324 in the box and 2.7325 in the prose; the final heading says 49° although the fitted center is 51.2843. Each source statement is retained separately.',
 'C11': 'The main supporting-information declaration ends at Figure S28, but the supplied SI captions continue through Figure S39. The contents list repeats S21/S30 and shifts some captions. Figure mappings follow the actual page and printed caption identifiers.',
 'C12': 'Reference 56 prints “200870” without a separator between the year and volume. Its literal citation is retained without an external correction.',
}
def normalize_note(x):
    explicit = re.match(r'^(C\d+):\s*', x)
    if explicit: return explicit[1] + ': ' + conflicts[explicit[1]]
    for c in old['evidence_conflicts']:
        # The v2 builder added spaces to S labels and figure names in display notes.
        if re.sub(r'\s+', '', x) == re.sub(r'\s+', '', c['description']): return conflicts[c['id']]
    return clean(x)

for it in items.values():
    # Equation text and references are literal scientific/citation displays.
    if not it['id'].startswith(('source-equations-', 'source-references-')):
        for k in ['title', 'text']: it[k] = clean(it[k])
    it['notes'] = [normalize_note(x) for x in it['notes']]
for c in r['evidence_conflicts']:
    c['description'] = conflicts[c['id']]
    if c['id'] == 'C12': c['title'] = 'Reference 56 typography'
    it = items['source-conflicts-' + c['id'].lower()]
    it['title'] = c['title']; it['text'] = c['description']
r['remaining_gaps'] = [clean(x) for x in r['remaining_gaps']]
for x in r['recipe_inventory']: x['label'] = clean(x['label'])

OPS = {
 'dry-flask': ('Dry the apparatus', 'Oven-dry and Schlenk-dry the apparatus before charging the reaction. This preparation has no chemical material output. The Schlenk drying pressure and duration are not reported.'),
 'charge-ode': ('Charge ODE and the selected additive solution', 'Charge ODE with the selected additive solution. The zero-equivalent control contains no additive; acid and indium-additive alternatives remain separate. The additive stock concentration is not reported.'),
 'heat-baseline': ('Heat under nitrogen and collect the optical baseline', 'Heat under nitrogen, calibrate the dip probe and collect the pre-injection baseline. The heating ramp, stirring speed and calibration standard are not reported.'),
 'sonicate-msc': ('Prepare the MSC injection solution', 'Prepare the MSC solution in ODE by sonication. The representative charge and the changed-concentration variants retain their separate canonical quantities. Sonication duration and power are not reported.'),
 'inject-msc': ('Inject the MSC solution and homogenize', 'Rapidly inject the MSC solution and homogenize the reaction. The numerical injection rate and mixing duration are not reported.'),
 'monitor-growth': ('Acquire time-resolved absorption spectra', 'Monitor the reaction by time-resolved absorption. A condition-specific endpoint is not supplied by this general operation; separately reported figure contexts retain their own endpoints.'),
 'distill-solvent': ('Distill the reaction solvent', 'Distill the solvent after the reaction, retaining the reaction residue for purification. Distillation temperature and pressure are not reported.'),
 'transfer-purify': ('Transfer the residue and purify in the glovebox', 'Transfer the residue to the glovebox and purify it. GPC-separated InP and In2O3 fractions remain distinct; the output represents a set of fractions rather than a single pure mixture. Column details, eluent, collection windows and recoveries are not supplied.'),
 'acid-charge': ('Charge the Grignard reagent and THF; attach the CO2 bulb', 'Charge the Grignard reagent and THF, then attach the labeled CO2 bulb. The bulb is attached at this stage; its contents enter during the following condensation. Stirring speed is not reported.'),
 'acid-condense': ('Cool, evacuate and condense labeled CO2', 'Cool with liquid nitrogen, evacuate the apparatus and condense labeled CO2 into the reaction vessel. Liquid nitrogen is an external coolant. Vacuum pressure and cooling duration are not reported.'),
 'acid-cold-hold': ('Warm in a dry-ice/acetone bath and hold', 'Warm the reaction in a dry-ice/acetone bath and hold under the reported conditions. Dry ice and acetone are external bath components, not reagents charged to the reaction.'),
 'acid-ambient-hold': ('Warm to room temperature and hold', 'Warm the reaction to room temperature and hold for the reported duration. A numerical room temperature is not supplied.'),
 'acid-quench': ('Cool in an ice-water bath and add methanol dropwise', 'Cool the reaction in an ice-water bath and add methanol dropwise. Bath water remains external to the reaction charge. Methanol volume and addition rate are not reported.'),
 'acid-acidify': ('Acidify with aqueous 1 M HCl to pH 2', 'Add aqueous 1 M HCl until pH 2 is reached. The volume of HCl solution is not reported.'),
 'acid-extract': ('Extract three times with diethyl ether', 'Extract the product three times with diethyl ether using the reported portions. Retain the organic extracts for the next workup stage.'),
 'acid-wash-dry': ('Combine the organic extracts, wash and dry', 'Combine the organic extracts, wash with brine and dry over Na2SO4. The brine and drying-agent amounts are not reported.'),
 'acid-filter-evaporate': ('Filter and remove solvent by rotary evaporation', 'Retain the organic filtrate, then remove solvent by rotary evaporation to retain the nonvolatile crude acid. Neither the aqueous fraction nor the drying agent is retained as product. Evaporation settings are not reported.'),
 'acid-layer': ('Dissolve in minimal dichloromethane and layer pentane', 'Dissolve the crude acid in minimal dichloromethane and layer pentane above it. The solvent volumes are not quantified.'),
 'acid-crystallize': ('Crystallize under the reported cold-storage conditions', 'Allow the layered solution to stand cold for the reported crystallization duration.'),
 'acid-isolate': ('Collect and dry the white crystals', 'Collect the white crystals and dry them. Drying settings are not reported.'),
 'substitute-labeled-acid': ('Substitute labeled acid in the cited MSC preparation', 'Replace the natural-abundance acid with the labeled acid in the cited MSC preparation. The supplied paper does not reproduce the upstream reagent amounts, reaction conditions or isolation settings.'),
 'add-labeled-acid': ('Add labeled acid to natural-abundance MSCs', 'Compare additions of 1, 10 or 30 equivalents of labeled acid per MSC as separate titration levels. Aliquot volumes and equilibration times are not reported.'),
 'add-labeled-indium': ('Add labeled indium carboxylate to natural-abundance MSCs', 'Compare additions of 1, 5, 10 or 20 equivalents of labeled indium salt per MSC as separate titration levels. Aliquot volumes and equilibration times are not reported.'),
 'pretreat-msc': ('Pretreat MSCs at 130 °C', 'Keep the reported 30 h and 72 h pretreatment contexts separate. Their exact cross-panel specimen relationship is unresolved; subsequent conversion measurements remain linked context rather than a verified match to one pretreatment batch.'),
 'tem-analyze': ('Acquire TEM images', 'Analyze the source-defined TEM specimens separately. Inputs represent distinct specimens or data contexts and are not pooled. Acquisition and quantitative limitations remain recorded in source gap G5 and the linked methods evidence.'),
 'xrd-analyze': ('Acquire powder XRD patterns', 'Acquire powder diffraction data for the separate source-defined specimens and references. These inputs are not pooled. Acquisition and quantitative limitations remain recorded in source gap G5 and the linked methods evidence.'),
 'scherrer-analysis-analyze': ('Retain the source Gaussian and Scherrer analysis', 'Keep the source Gaussian fits and Scherrer calculations in their separate specimen contexts. Inputs are not pooled. The incomplete Scherrer implementation and other quantitative limits remain recorded in source gap G5.'),
 'nmr-analyze': ('Acquire NMR spectra', 'Keep the NMR specimens and reference spectra separate. The literal 202 Hz caption in Figure 4 is retained as source evidence rather than a universal instrument setting. Inputs are not pooled; source gap G5 and the linked methods evidence retain the remaining limitations.'),
 'uvvis-analyze': ('Acquire absorption spectra', 'Acquire absorption data for the separate source-defined specimens. Inputs are not pooled. Source gap G5 and the linked methods evidence retain the acquisition and quantitative limitations.'),
 'tga-analyze': ('Perform thermogravimetric analysis', 'Keep the source thermal specimen context separate. The general nitrogen reaction rule does not establish the analysis atmosphere. Inputs are not pooled; source gap G5 and the linked methods evidence retain the remaining limitations.'),
 'dsc-analyze': ('Perform differential scanning calorimetry', 'Keep the source calorimetry contexts separate. The general nitrogen reaction rule does not establish the analysis atmosphere. Inputs are not pooled; source gap G5 and the linked methods evidence retain the remaining limitations.'),
 'optical-analysis-analyze': ('Smooth spectra and subtract the baseline', 'Process each source optical dataset with the reported smoothing and baseline-subtraction procedure. Separate datasets are not pooled. Source gap G5 retains the raw-data and quantitative limitations.'),
 'kinetic-analysis-analyze': ('Retain the source kinetic transformations and fits', 'Keep the published optical transformations and fits in their separate source contexts. Inputs are not pooled and no independent refit is implied. Source gap G5 retains the raw-data and quantitative limitations.'),
 'acid-nmr-analyze': ('Characterize the labeled acid by NMR', 'Retain the labeled-acid NMR observations in their stated solvent and acquisition contexts. Separate spectra are not pooled. Source gap G5 and the linked methods evidence retain the remaining limitations.'),
}
ck('All 34 source operation cards have explicit prose', set(OPS) == {x.removeprefix('operation-') for x in items if x.startswith('operation-')})
for oid, (title, text) in OPS.items():
    items['operation-' + oid]['title'] = title
    items['operation-' + oid]['text'] = text

PANELS = {
 'figure-1': 'Panel A shows 13C NMR in toluene-d8 at 176 MHz, with labels −30, 25 and 80 °C and return to 25 °C. Panel B shows absorption from 20 to 110 °C in 10 °C steps; its caption identifies phenylacetate MSCs in toluene. Conflicting prose temperature endpoints remain explicit elsewhere.',
 'figure-2': 'Panel A compares natural-abundance MSCs with 1, 10 or 30 equivalents of 13C-labeled acid, alongside authentic labeled MSC and free-acid references. Panel B compares 1, 5, 10 or 20 equivalents of labeled indium salt and an authentic labeled-MSC reference; the caption specifies toluene-d8 and 176 MHz.',
 'figure-3': 'Panel A shows spectra at 250 °C after 0, 10, 20, 30, 40, 50 and 60 min, with an inset at 500, 600 and 700 nm. Panel B compares the 500 nm response at 150, 200, 250 and 300 °C; panel C compares final absorption at those temperatures. Panel D compares 150 and 250 °C XRD patterns with InP and In2O3 references. Panel E shows 150 °C agglomerates and panel F shows 250 °C spherical particles; both TEM panels have 20 nm scale bars. Panel F reports 2.6 ± 0.5 nm from 315 particles; the definition of the ± uncertainty is not specified.',
 'figure-4': 'Panel A shows 31P NMR in C6D6 after pretreatment at 130 °C for 30 h and literally prints 202 Hz. Panel B follows conversion at 250 °C through the 500 nm response. The 30 h/72 h pretreatment descriptions do not establish an exact cross-panel specimen match.',
 'figure-5': 'The main panel compares initial MSC concentrations of 0.182, 0.061 and 0.030 mM at 250 °C using the 500 nm response. The inset rate axis is labeled ×10^4 ΔAbs/s; its caption gives the fit 0.00564x − 0.00012 with R² = 0.9904. These literal source values are not independently refitted.',
}
for iid, it in items.items():
    if iid.startswith('source-figures-'):
        fid = iid.removeprefix('source-figures-')
        it['text'] = it['title'] + '. ' + PANELS.get(fid, 'The selected original figure and its source-assigned specimen contexts are retained. Original curves have not been digitized or refitted.')
    elif iid.startswith('source-sample_contexts-'):
        it['text'] = it['title'] + '. This is a named source context. Equal composition or conditions do not establish an exact physical-aliquot match.'
    elif iid == 'unit-friedfeld2019-unit-graphical-abstract':
        it['text'] = 'The graphical abstract is the authors’ illustration and summary. It does not provide newly qualified atomic coordinates.'
    elif iid in ['unit-friedfeld2019-unit-si-contents-1', 'unit-friedfeld2019-unit-si-contents-2']:
        it['text'] = 'The SI contents list is retained privately with its numbering conflicts. Figure mappings follow the actual printed captions.'

# The reviewer supplied exact existing canonical pointers; no new specimen association is added.
omissions_path = F / 'canonical-independent-audit/sample-link-omissions.json'
omissions = read(omissions_path)
ck('Exactly 62 bounded sample-link omissions', len(omissions) == 62 and len({x['item_id'] for x in omissions}) == 62)
cm = read(V2 / 'record-manifest.json')
records = {x['record_id']: read(x['path']) for x in cm['records']}
for x in omissions:
    it = items[x['item_id']]
    ck(x['item_id'] + ' reviewer exact prior links', it['sample_scope']['canonical_sample_links'] == x['existing_links'])
    ck(x['item_id'] + ' target already exists', resolve(records[x['record_id']], x['pointer'])['sample_id'] == x['sample_id'])
    ck(x['item_id'] + ' source context matches identity', x['item_id'] == 'source-sample_contexts-' + x['sample_id'])
    it['sample_scope']['canonical_sample_links'].append({'record_id': x['record_id'], 'json_pointer': x['pointer'], 'sample_id': x['sample_id'], 'relation': 'Existing named source context; no new physical-aliquot association.'})

# Update prose mirrors used by original-asset galleries, without changing provenance or payloads.
asset_to_item = {a['id']: it for it in items.values() for a in it['original_assets']}
for group in ['figures', 'tables', 'equations', 'schemes', 'source_notes']:
    for a in r[group]:
        it = asset_to_item[a['id']]
        a['label'] = clean(a['label'])
        a['caption_paraphrase'] = it['text']
        a['notes'] = [normalize_note(x) for x in a['notes']]
for it in items.values():
    for a in it['original_assets']: a['label'] = clean(a['label'])

def differences(a, b, ptr=''):
    if type(a) != type(b): return [{'pointer': ptr, 'before': a, 'after': b}]
    if isinstance(a, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            p = ptr + '/' + k.replace('~', '~0').replace('/', '~1')
            if k not in a: out.append({'pointer': p, 'before_missing': True, 'after': b[k]})
            elif k not in b: out.append({'pointer': p, 'before': a[k], 'after_missing': True})
            else: out.extend(differences(a[k], b[k], p))
        return out
    if isinstance(a, list):
        if len(a) != len(b): return [{'pointer': ptr, 'before': a, 'after': b}]
        return [z for j, (x, y) in enumerate(zip(a, b)) for z in differences(x, y, ptr + '/' + str(j))]
    return [] if a == b else [{'pointer': ptr, 'before': a, 'after': b}]

delta = differences(old, r)
display_patterns = [
 r'/reader_sections/\d+/items/\d+/(title|text)$',
 r'/reader_sections/\d+/items/\d+/notes/\d+$',
 r'/reader_sections/\d+/items/\d+/original_assets/\d+/label$',
 r'/reader_sections/\d+/items/\d+/sample_scope/canonical_sample_links$',
 r'/(figures|tables|equations|schemes|source_notes)/\d+/(label|caption_paraphrase)$',
 r'/(figures|tables|equations|schemes|source_notes)/\d+/notes/\d+$',
 r'/remaining_gaps/\d+$', r'/evidence_conflicts/\d+/(title|description)$',
 r'/recipe_inventory/\d+/label$',
]
for d in delta: ck('Permitted reader-only delta ' + d['pointer'], any(re.fullmatch(p, d['pointer']) for p in display_patterns))
link_delta = [d for d in delta if d['pointer'].endswith('/sample_scope/canonical_sample_links')]
ck('Exactly 62 added existing named links', len(link_delta) == 62 and all(len(d['after']) == len(d['before']) + 1 and d['after'][:-1] == d['before'] for d in link_delta))
for iid, it in items.items():
    before = old_items[iid]
    for field in ['facts', 'operation_contexts', 'material_contexts', 'stock_contexts', 'product_contexts', 'evidence', 'canonical_links', 'source_audit_unit_ids', 'source_fact_ids']:
        ck(iid + ' unchanged ' + field, before.get(field) == it.get(field))
    if iid.startswith(('source-equations-', 'source-references-')): ck(iid + ' literal equation/citation text unchanged', it['text'] == before['text'])
    ck(iid + ' no empty missingness prose', 'Unreported details: .' not in it['text'])
    ck(iid + ' no raw panel JSON prose', 'Source panel assignments:' not in it['text'])
ck('All counts and gate states preserved', r['counts'] == old['counts'] and r['presentation_gates'] == old['presentation_gates'])
ck('2,131 typed fields unchanged', sum(len(x['facts']) for x in items.values()) == 2131)
ck('750 canonical measurements unchanged', sum(len(x['measurements']) for x in records.values()) == 750)

save(O / 'reader/friedfeld2019.json', r)
bindings = read(O / 'reader/reader-bindings-proposal.json')
bindings['reader_sha256'] = sha(O / 'reader/friedfeld2019.json')
save(O / 'reader/reader-bindings-proposal.json', bindings)
record_receipt = []
for x in cm['records']:
    previous = Path(x['path']); current = O / 'records' / previous.name
    ck(x['record_id'] + ' canonical byte identity', sha(previous) == sha(current) == x['sha256'])
    ck(x['record_id'] + ' current schema', not validate_record(records[x['record_id']]))
    ck(x['record_id'] + ' no eligible training task', not any(v['eligible'] for v in eligibility(records[x['record_id']]).values()))
    record_receipt.append({'record_id': x['record_id'], 'prior_path': str(previous), 'current_path': str(current), 'sha256': x['sha256'], 'byte_identical': True})
    x['path'] = str(current)
save(O / 'record-manifest.json', cm)
ck('One source split', len(set(build_groups(list(records.values())).values())) == 1)
coverage = read(O / 'reader/source-item-coverage.json')
for b in coverage['canonical_field_map']:
    q = next(q for q in items[b['reader_item_id']]['facts'] if q['id'] == b['reader_fact_id'])
    ck(b['record_id'] + b['json_pointer'] + ' exact canonical field', resolve(records[b['record_id']], b['json_pointer']) == q['canonical_quantity'])
for it in items.values():
    for b in it['sample_scope']['canonical_sample_links']:
        ck(it['id'] + ' exact source sample link ' + b['sample_id'], resolve(records[b['record_id']], b['json_pointer'])['sample_id'] == b['sample_id'])
ck('Source and typed field maps unchanged', sha(O / 'source-to-field-coverage.json') == sha(V2 / 'source-to-field-coverage.json') and sha(O / 'reader/source-item-coverage.json') == sha(V2 / 'reader/source-item-coverage.json'))
for a in bindings['original_assets']:
    ck(a['id'] + ' selected crop immutable', sha(a['private_path']) == sha(O / 'isolated-reader-fixture/dist' / a['public_asset']) == a['sha256'])
for x in cm['records']:
    ck(x['record_id'] + ' isolated fixture exact bytes', sha(O / 'isolated-reader-fixture/data/records' / Path(x['path']).name) == x['sha256'])
old_root = consumer.ROOT
try:
    consumer.ROOT = O / 'isolated-reader-fixture'
    errors = consumer.validate(r)
finally:
    consumer.ROOT = old_root
ck('Actual current reader consumer in private fixture', errors == [])
for p, h in base_freeze['bound_files'].items(): ck('Final v2 immutability ' + p, sha(V2 / p) == h)

save(O / 'reader-revision3-delta.json', {
 'status': 'bounded_author_correction_pending_distinct_recheck', 'findings': ['Readable reader display prose', '62 existing named sample-context links'],
 'prior_freeze': str(V2 / 'package-freeze.json'), 'prior_freeze_sha256': sha(V2 / 'package-freeze.json'),
 'prior_reader_sha256': sha(V2 / 'reader/friedfeld2019.json'), 'current_reader_sha256': sha(O / 'reader/friedfeld2019.json'),
 'reader_delta': delta, 'reader_delta_count': len(delta), 'added_named_sample_links': 62,
 'source_payloads_unchanged': True, 'typed_reader_fields_unchanged': 2131, 'canonical_measurements_unchanged': 750,
 'original_selected_crops_unchanged': 51, 'all_30_records_byte_identical': True,
 'reviewer_omissions_path': str(omissions_path), 'reviewer_omissions_sha256': sha(omissions_path),
 'retained_predecessor': 'Every v2 frozen file remains at its original path; no overwritten author/source bytes.'})
save(O / 'unchanged-record-receipt.json', {'status': 'exact_hash_verification', 'records': record_receipt,
 'scope': 'Reader-only v3 does not change any canonical record. Separately frozen apparatus and molecular packages may reference this receipt without being silently rewritten.',
 'source_freeze_sha256': cm['source_freeze_sha256'], 'source_independent_audit_sha256': cm['source_audit_sha256']})
validation = {'status': 'passed_author_checks_pending_distinct_reader_v3_recheck', 'created_at': datetime.now(timezone.utc).isoformat(),
 'checks': checks, 'check_count': len(checks), 'reader_delta_count': len(delta), 'actual_reader_consumer_errors': errors,
 'consumer_path': str(S / 'scripts/build_paper_reviews.py'), 'consumer_sha256': sha(S / 'scripts/build_paper_reviews.py'),
 'fixture': str(O / 'isolated-reader-fixture'), 'canonical_independent_v3_approval': False, 'actual_browser': False, 'publication_approved': False}
save(O / 'author-validation.json', validation)
save(O / 'reader/reader-author-validation.json', validation)
(O / 'PROPOSAL_NOTES.md').write_text('''# Friedfeld reader revision 3

This revision resolves the two independent v2 reader findings: readable display prose and direct links from all 62 source-context cards to their existing named canonical samples. It preserves all 30 canonical files byte for byte, 2,131 typed reader fields, 750 measurements, literal source payloads, references and equation text, scientific pointers, and 51 selected original crops. Generic source-payload context links remain alongside the newly added existing sample links; these do not certify a physical aliquot match.

The prior v2 freeze remains immutable. reader-revision3-delta.json enumerates every allowed display/link change; unchanged-record-receipt.json records all 30 old/new paths and equal hashes. No source facts, units, values, operations, material flow, conditions, molecular/apparatus assets or training eligibility changed. Current reader-consumer validation ran against a private fixture with real canonical records and selected crop bytes. Root consumer code and Site were not edited.

The effective source revision 2 already passed distinct source review. The v2 reviewer found no canonical correction; the v3 reader still needs its bounded distinct recheck. This author freeze grants no browser, installed binding, training or publication approval. Historical v2 author validations are retained in inherited-v2-validation. The original apparatus package remains frozen separately and can use this unchanged-record receipt as an external addendum.
''', encoding='utf-8')
shutil.copyfile(Path(__file__), O / 'author-script-snapshots/revise_reader_v3.py')
# A readable proof document is private; it includes display prose only, no source-page cache.
display = []
for section in r['reader_sections']:
    display.append('## ' + section['title'])
    for it in section['items']:
        display.append('\n### ' + it['id'] + ' — ' + it['title'] + '\n\n' + it['text'])
        if it['notes']: display.append('\n' + '\n'.join('- ' + n for n in it['notes']))
(O / 'reader/display-proof.md').write_text('\n'.join(display) + '\n', encoding='utf-8')
print(json.dumps({'status': 'prepared_and_validated_not_yet_frozen', 'checks': len(checks), 'reader_deltas': len(delta), 'reader_sha256': sha(O / 'reader/friedfeld2019.json'), 'manifest_sha256': sha(O / 'record-manifest.json')}))
