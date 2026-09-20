from pathlib import Path
N=Path(__file__).resolve().parent
t=(N.parent/'ja212032q/prepare_site_proposal.py').read_text('utf-8').replace('Ghosh','Sommer').replace('ghosh','sommer').replace('2012','2020')
start=t.index("scope='");end=t.index('\nrecords={}',start)
t=t[:start]+'''scope='Complete supplied eleven-page main article read and independently audited. Declared SI remains locally unlocated and unverified. Canonical/reader, molecule and apparatus audits passed. Three laboratory routes, nine supporting procedures and seven observation records remain distinct. Source conflicts, unknown outcomes and unresolved specimen joins are preserved; no atomistic pair or training task is admitted.'
removed_missing=['The complete supplied 11-page main extraction passed distinct source audit. Declared SI remains locally unlocated/unverified. Canonical/reader independent review remains pending; this is an unapproved private author draft. Historical pending flags in immutable source payloads refer to their author-freeze time.']''' +t[end:]
t=t.replace("All ten supplied main pages read, visually inspected and independently audited; source and canonical checks passed.","All eleven supplied main pages read, visually inspected and independently audited; source and canonical checks passed.")
t=t.replace("Matched nine-page SI fully read, visually inspected and independently audited; unresolved specimen and acquisition contexts are retained.","Declared supporting information remains locally unlocated/unverified; no SI content is claimed read.")
t=t.replace('len(records)==21','len(records)==19').replace("values())==33","values())==31")
t=t.replace('supplied_main_and_matched_si_review_complete','supplied_main_review_complete_si_unverified')
t=t.replace('TEM, PXRD and nominal layer accounting do not provide product atomic coordinates, exact cross-technique sample–recipe joins or DFT-ready inputs.','Source diffraction, microscopy and nominal targets do not provide product atomic coordinates, exact cross-technique sample–recipe joins or DFT-ready inputs.')
t=t.replace("x!='The source extraction audit passed; independent canonical and reader approval is pending. Molecular, product, apparatus, browser and publication gates remain separate.'","x not in {'The distinct supplied-main source audit passed; canonical and reader independent approval remain pending.','Molecular, apparatus, product-context, browser and publication gates remain separate.'}")
t=t.replace('len(assets)==36','len(assets)==20')
t=t.replace("V/'metadata-correction-v3/effective-file-map.json'","V/'canonical-v2-rebind/effective-file-map.json'")
start=t.index('def effective_read(name):');end=t.index("registry=effective_read",start)
t=t[:start]+'''def effective_read(name):
 item=effective['replacements'].get(name)
 if item:
  p=Path(item['path']);assert sha(p)==item['sha256'];return read(p)
 p=V/name;assert str(p) in read(V/'package-freeze.json')['bound_files']
 assert sha(p)==read(V/'package-freeze.json')['bound_files'][str(p)];return read(p)
''' +t[end:]
start=t.index("for rel,item in read(V/'metadata-correction-v3/effective-public-assets.json').items():")
end=t.index("asset(L/'visuals/apparatus",start)
t=t[:start]+'''for item in read(V/'canonical-v2-rebind/effective-public-assets.json')['assets']:
 src=Path(item['source_path']);assert sha(src)==item['sha256'];asset(src,'assets/chemical-registry/'+item['path'],'reviewed_chemical_reference')
''' +t[end:]
t=t.replace("'records':21,'routes_and_variants':5,'supporting_procedures':10,'observations':6,'operations':33","'records':19,'routes_and_variants':3,'supporting_procedures':9,'observations':7,'operations':31")
t=t.replace("'selected_source_crops':36,'molecular_entries':25,'material_slots':88,'stock_components':8","'selected_source_crops':20,'molecular_entries':28,'material_slots':62,'stock_components':23")
(N/'prepare_site_proposal.py').write_text(t,'utf-8')
assert 'ghosh' not in t.lower() and 'Matched nine' not in t and 'metadata-correction-v3' not in t
print('Prepared Sommer-specific promotion script; no Site or projection mutation.')
