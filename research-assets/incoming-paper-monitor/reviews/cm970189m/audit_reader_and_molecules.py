from pathlib import Path
from collections import Counter
import json,hashlib,re,math
B=Path(__file__).resolve().parent;P=B/'public-review-proposal';A=B/'molecular-assets';S=B.parents[3]/'recipe-atlas/dist/assets/chemical-registry'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def at(j,p):
 for k in p.strip('/').split('/') if p else []:j=j[int(k)] if isinstance(j,list) else j[k.replace('~1','/').replace('~0','~')]
 return j
source=read(B/'source-audit.json');ledger=read(P/'veinot1997.json');mapping=read(P/'source-item-coverage.json')['source_audit_unit_map'];items={i['id']:i for s in ledger['reader_sections'] for i in s['items']}
checks=[]
def check(name,ok,detail=''):checks.append(dict(name=name,passed=bool(ok),detail=detail))
check('141 distinct source units mapped',len(mapping)==141 and {x['source_audit_id'] for x in mapping}=={x['id'] for x in source['units']})
for m in mapping:
 try: targets=[at(ledger,p) for p in m['public_targets']];okay=bool(targets) and all(t is not None for t in targets)
 except (KeyError,IndexError,TypeError):okay=False
 check(m['source_audit_id']+' source/target pointer',at(source,m['source_audit_pointer'])['id']==m['source_audit_id'] and okay)
check('Main-only SI-unverified scope',ledger['review_scope']=='supplied_main_only_si_unverified')
check('Private ledger not publication claim',ledger['publication_status']=='private_proposal_not_published' and not ledger['training_eligible'])
check('No displayed sizing equation invented',len(ledger['equations'])==0)
def text(i):return items[i]['text']
check('Acyl stock is5mL solution, not solvent-only charge','5 mL of solution' in text('esterification-stocks') and '170 mg' in text('esterification-stocks'))
check('QDOH weak1870cm-1 overtone preserved','1870' in text('qdoh-ir') and 'weak' in text('qdoh-ir'))
check('Structured NMR multiple-environment interpretation preserved','multiple' in text('qdoh-nmr-exchange') and 'environment' in text('qdoh-nmr-exchange'))
check('NMR solvent scope is compound specific','3a' in text('analytical-materials') and '3e' in text('analytical-materials'))
obs8=next(m for m in mapping if m['source_audit_id']=='observation-08')
check('General C4/C5 assignments remain traceable',any(at(ledger,p).get('id')=='conflict-06' for p in obs8['public_targets']))
check('All eleven molecular/cluster Table1 rows',len(ledger['tables'][0].get('structured_rows',[]))==11,'Original table and full structured rows retained.')
reader=dict(status='passed' if all(c['passed'] for c in checks) else 'must_fix',source_id='veinot1997',scope='Bounded independent source-unit and reader-context audit; no browser/rendering or publication claim.',reader_items=len(items),source_units=len(mapping),ledger_sha256=sha(P/'veinot1997.json'),mapping_sha256=sha(P/'source-item-coverage.json'),check_count=len(checks),checks=checks,open_findings=[c for c in checks if not c['passed']],resolved_findings=['5mL acylating solution distinguished from5mL solvent inQDOHstock.','NMRsolvent claim restricted to compounds supported bysource;3e separately identified.','QDOH1870cm−1 and preparation-summary IRdetails restored in reader context.','Multiple-environment NMR interpretation and source-specific C4/C5assignment conflict included.'],manual_review=['Read all polished precursor/protocol/structure/property/intuition context and all independent observation-unit mappings.','All three source tables and original figures remain available. Surface coverage and prior-system22/25Å² values remain author models or citation-only comparisons, not current measured outcomes.','Noacylchloridefailure becomes quantitativebulkCdSsynthesis; unfunctionalizedcontrol remains no-reaction context; >12h isstrictlowerbound, notexact measuredtiming.','6nmbar/1100Åtext discrepancy,7Åresolution-limitedprecision,295/305/390nmfeatures,20/34mol%capestimates,3b15/30min,absentEq1 and unresolvedSI remain visible.'])
(B/'reader-context-audit.json').write_text(json.dumps(reader,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
(B/'reader-context-audit.md').write_text('# Independent Veinot reader-context audit\n\nStatus: **'+reader['status']+'**. '+str(len(items))+' reader items,141 source units mapped. '+str(len(checks))+' bounded checks; '+str(len(reader['open_findings']))+' open checks.\n\n'+ '\n'.join('- '+x for x in reader['manual_review'])+'\n\nThis audit does not establish browser rendering or publication. Exact ledger and coverage-map hashes are in reader-context-audit.json.\n',encoding='utf8')

checks=[]
reg=read(A/'registry-additions.json');entries={e['id']:e for e in reg['entries']};reuse=read(A/'reused-references.json');existing={e['id']:e for e in read(S/'registry.json')['entries']};bindings=read(A/'bindings-additions.json');canon={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')}
binding_rows=[]
for rid,r in canon.items():
 check(rid+' binding source hash',bindings['sourceRecordSha256'][rid]==sha(B/'canonical-drafts'/(rid+'.json')))
 for m in r['materials']:
  bid=bindings['recordBindings'][rid].get(m['id']);e=entries.get(bid) or existing.get(bid)
  check(rid+'/'+m['id']+' identified binding',bool(e))
  note=bindings.get('bindingNotes',{}).get(rid,{}).get(m['id'],'')
  check(rid+'/'+m['id']+' no inherited other-paper condition',not any(x in note.lower() for x in ['electrospray','pyridine dispersion','silicon ligand','twofold excess']))
  binding_rows.append(dict(record_id=rid,material_id=m['id'],reference_id=bid,canonical_name=m['name'],reference_name=e['name'] if e else None,reference_kind=e.get('depictionKind') if e else None))
check('115 actual materials bound',len(binding_rows)==115)
for e in reg['entries']:
 for key,expected in e.get('assetHashes',{}).items():
  path=e.get(key)
  check(e['id']+'/'+key+' hash',path and sha(A/path)==expected)
 if e['depictionKind']=='molecule':
  m=read(A/e['model3dPath']);atoms=m['atoms'];counts=Counter('D' if a['element']=='H' and a.get('isotope')==2 else a['element'] for a in atoms)
  expected=Counter({el:int(n or 1) for el,n in re.findall(r'([A-Z][a-z]?)(\d*)',e['formula'])})
  check(e['id']+' explicit atom formula/isotopes',counts==expected)
  check(e['id']+' finite illustrative conformer',all(math.isfinite(a[k]) for a in atoms for k in ['x','y','z']) and m.get('eligible_training') is False)
  check(e['id']+' valid bond endpoints',all(0<=b['a']<len(atoms) and 0<=b['b']<len(atoms) for b in m['bonds']))
  check(e['id']+' functional-group index bounds',all(all(0<=i<len(atoms) for i in g.get('atomIndices',[])) and all(0<=i<len(m['bonds']) for i in g.get('bondIndices',[])) for g in e.get('functionalGroups',[])))
 else:
  check(e['id']+' card has no invented atom model',not e.get('model2dPath') and not e.get('model3dPath') and e['provenance'].get('measured_coordinates') is False)
for e in reuse['entries']:
 for k,h in e['assetHashes'].items():check('Reused '+e['id']+'/'+k+' hash',sha(S/e['assetPaths'][k])==h)
check('22 molecular conformers and25identity cards',sum(e['depictionKind']=='molecule' for e in entries.values())==22 and sum(e['depictionKind']!='molecule' for e in entries.values())==25)
check('Generic workup ether not assigned diethyl ether',all(row['reference_id']=='identity-veinot-ether' for row in binding_rows if row['material_id']=='ether'))
check('Thionyl functional group correctly labelled',all(g['label']!='Sulfoxide' for g in entries['thionyl-chloride']['functionalGroups']))
for x,sub in [('a','CH₃'),('b','n-C₃H₇'),('c','pyren-1-yl'),('d','phenyl'),('e','n-C₉H₁₉')]:
 e=entries['identity-veinot-ester-2'+x];svg=(A/e['svgPath']).read_text(encoding='utf8')
 check('Surface2'+x+' correctRgroup',sub in svg)
 check('Surface2'+x+' not measured atomic model','illustrative' in e['caption'].lower() and 'no atomistic phase' in e['caption'].lower() and e['model3dPath'] is None)
contacts=[dict(basename=p.name,sha256=sha(p),independently_visually_inspected=True) for p in sorted((A/'review').glob('*contact*.png'))]
out=dict(status='passed' if all(c['passed'] for c in checks) else 'must_fix',source_id='veinot1997',scope='Independent source identity, bindings, isotope/formula and surface-card audit. All22molecule2Dpanels,22projected3Dconformers and25cards independently visually inspected; not browserQA or a claim of experimental geometry.',checks=checks,check_count=len(checks),open_findings=[c for c in checks if not c['passed']],binding_rows=binding_rows,package_hashes={f:sha(A/f) for f in ['registry-additions.json','bindings-additions.json','asset-manifest.json','product-reference-proposal.json']},visual_contacts=contacts,scientific_limits=['Free4-hydroxythiophenol hasS–H;surfaceQDOHcard correctly hasCdS–S–aryl–OH and noS–H.','All five surface ester motifs areCdS–S–para-aryl–O–C(=O)–R withcorrectacetyl/butanoyl/pyrenecarbonyl/benzoyl/decanoylsubstituents. No measured ligand count,coverage,phase,lattice or complete conversion is implied.','3a–e freeorganicprecursors are distinct from2a–e nanoclusters;pyreneposition andN-acylconnectivity visually matchoriginalScheme1.','DMSO-d6,CDCl3,D2Oretain6/1/2deuteriumlabels. ClassicalRDKitconformersareillustrative andnotDFT,solutionstate,thermodynamic ortrainingdata.','Sodiumsulfidenonahydrate/cadmiumacetatehydration/unspecifiedworkupether/filterpaper/mixedbed/sieve/variableagents remainidentitycards whenstructure/speciationisnotestablished.','No experimentalCdSlattice ornanoclusteratomiccoordinatesaremanufactured;organic3DreferencesarenotcombinedwithCdScoretofakeaninterface.'])
(B/'molecular-source-audit.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
(B/'molecular-source-audit.md').write_text('# Independent Veinot molecular/source audit\n\nStatus: **'+out['status']+'**. '+str(len(binding_rows))+' material bindings;47newreferences(22molecules,25cards);8reusedreferences. '+str(len(checks))+' bounded checks; '+str(len(out['open_findings']))+' open checks.\n\n'+ '\n'.join('- '+x for x in out['scientific_limits'])+'\n\nSee molecular-source-audit.json for exact binding and asset hashes and resolved/open findings. No Site or molecule assets modified.\n',encoding='utf8')
print(json.dumps(dict(reader_status=reader['status'],reader_checks=reader['check_count'],reader_open=reader['open_findings'],molecule_status=out['status'],molecule_checks=out['check_count'],molecule_open=out['open_findings']),indent=2))
