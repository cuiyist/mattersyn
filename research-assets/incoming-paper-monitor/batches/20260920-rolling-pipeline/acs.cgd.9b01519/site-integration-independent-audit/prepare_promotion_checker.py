"""Adapt the previously exercised independent transport checker to Sommer's exact boundary."""
from pathlib import Path
A=Path(__file__).resolve().parent
old=A.parent.parent/'ja212032q/site-integration-independent-audit/check_promotion.py'
s=old.read_text(encoding='utf8')
changes=[
 ('import copy, hashlib, json, re, shutil, sys','import copy, hashlib, json, re, shutil, sys, argparse'),
 ("f=bind(P/'package-freeze.json')\nsame(sha(P/'package-freeze.json'),'a5290e674534c727c012e34e331f27095dfc73ad4c397b30974072ae674a2712','exact promotion freeze')","ap=argparse.ArgumentParser();ap.add_argument('--expected-freeze',required=True);args=ap.parse_args()\nf=bind(P/'package-freeze.json')\nsame(sha(P/'package-freeze.json'),args.expected_freeze,'exact promotion freeze')"),
 ("removed=['All supplied main/SI extraction passed distinct source audit of revision 2. Canonical/reader review remains pending; this is an unapproved private draft. Historical pending flags in the frozen source payload describe its author freeze, before the separate audit.']","removed=['The complete supplied 11-page main extraction passed distinct source audit. Declared SI remains locally unlocated/unverified. Canonical/reader independent review remains pending; this is an unapproved private author draft. Historical pending flags in immutable source payloads refer to their author-freeze time.']"),
 ("old_gap='The source extraction audit passed; independent canonical and reader approval is pending. Molecular, product, apparatus, browser and publication gates remain separate.'","old_gaps={'The distinct supplied-main source audit passed; canonical and reader independent approval remain pending.','Molecular, apparatus, product-context, browser and publication gates remain separate.'}"),
 ("if x!=old_gap","if x not in old_gaps"),
 ('metadata-correction-v3','canonical-v2-rebind'),
 ('whole_source_page','contains_complete_source_page'),
 ('ghosh2012','sommer2020'),('Ghosh','Sommer'),
 ("same(len(records),21,'21 records')","same(len(records),19,'19 records')"),
 ("Counter({'synthesis_route':5,'supporting_procedure':10,'contextual_observation':6}),'roles 5/10/6'","Counter({'synthesis_route':3,'supporting_procedure':9,'contextual_observation':7}),'roles 3/9/7'"),
 ("),33,'33 operations'","),31,'31 operations'"),
 ("),585,'585 measurements'","),532,'532 measurements'"),
 ("same(len(reg['entries']),25,'25 molecular entries')","same(len(reg['entries']),28,'28 molecular entries')"),
 ("same(len(sol['contexts']),3,'three stocks')","same(len(sol['contexts']),7,'seven stocks')"),
 ("),8,'eight components'","),23,'23 components'"),
 ("same(len(assets),85,'85 public files')","same(len(assets),57,'57 public files')"),
 ("Counter({'selected_original_scientific_crop':36,'reviewed_chemical_reference':48,'independently_audited_apparatus':1}),'36 crops48 chemicals1module'","Counter({'selected_original_scientific_crop':20,'reviewed_chemical_reference':36,'independently_audited_apparatus':1}),'20 crops36 chemicals1module'"),
 ("'records':21,'routes_variants':5,'procedures':10,'observations':6,'operations':33,'measurements':585","'records':19,'routes_variants':3,'procedures':9,'observations':7,'operations':31,'measurements':532"),
 ("'entries':25,'material_slots':88,'stocks':3,'stock_components':8,'public_files':85","'entries':28,'material_slots':62,'stocks':7,'stock_components':23,'public_files':57"),
 ('ALL 88 assignments','ALL 62 assignments'),('all 88 material slots and three stock contexts/eight components','all 62 material slots and seven stock contexts/23 components'),
 ('Exact 85-file allowlist','Exact 57-file allowlist'),('The 85 public files are exactly 36 selected crops, 48 chemical assets','The 57 public files are exactly 20 selected crops, 36 chemical assets'),
 ('21 records, 33 operations and 585 measurement/context entries','19 records, 31 operations and 532 measurement/context entries'),
 ('Five route/variant, ten procedure and six observation roles','Three route, nine procedure and seven observation roles'),
 ('Effective molecular v3','Effective molecular v2 rebind'),('effective v3 input','effective overlay input'),('effective chemical v3 bytes','effective chemical overlay bytes'),
 ('all identities, 88 slot assignments','all identities, 62 slot assignments'),
]
for old,new in changes:
 assert old in s,old
 s=s.replace(old,new)
needle="audit=bind(G/rel);same(sha(G/rel),digest,'audit hash '+rel);same(audit['status'],'passed','prior audit passed '+rel)"
replacement=needle+"\n for path,h in audit.get('bound_files',{}).items():\n  fp=Path(path) if Path(path).is_absolute() else G/path\n  bind(fp);same(sha(fp),h,'audit dependency unchanged '+str(path))"
assert needle in s;s=s.replace(needle,replacement)
# The upstream table/model tests are already independently passed. This check compares
# exact preserved assets and uses the actual current canonical/reader validators only.
(A/'check_promotion.py').write_text(s,encoding='utf8')
print('Prepared Sommer checker. Requires exact --expected-freeze before it can run.')
