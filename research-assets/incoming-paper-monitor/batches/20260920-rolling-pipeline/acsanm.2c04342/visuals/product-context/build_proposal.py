"""Author source-qualified symbolic product contexts. Only writes this private directory."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib,html,textwrap,argparse
O=Path(__file__).resolve().parent;P=O.parents[1]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
parser=argparse.ArgumentParser();parser.add_argument('--canonical-manifest',type=Path,required=True);args=parser.parse_args()
assert not(O/'package-freeze.json').exists(),'Frozen output must remain unchanged.'
(O/'svg').mkdir(exist_ok=True);(O/'previews').mkdir(exist_ok=True)
sf=read(P/'source-facts.json');facts={f['id']:f for f in sf['facts']};sourcecontexts={s['id']:s for s in sf['sample_contexts']}
manifest=read(args.canonical_manifest);records={};paths={};checks=[]
def ck(k,yes):checks.append({'check':k,'passed':bool(yes)});assert yes,k
for meta in manifest['records']:
 p=Path(meta['path']);ck('Canonical hash '+meta['record_id'],sha(p)==meta['sha256']);records[meta['record_id']]=read(p);paths[meta['record_id']]=p
sourceaudit=P/'source-independent-audit/independent-audit-v2.json'
ck('Passed current source freeze',read(sourceaudit)['status']=='passed' and read(sourceaudit)['source_package_freeze_sha256']==sha(P/'package-freeze.json'))

def tx(x,y,s,size=22,color='#244756',anchor='start'):
 return f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial,sans-serif" font-size="{size}" text-anchor="{anchor}">{html.escape(s)}</text>'
def wrap(s,x,y,n=84,size=21):return ''.join(tx(x,y+i*30,t,size) for i,t in enumerate(textwrap.wrap(s,n)))
cards={
 'cubic':('CsMnCl3','Cubic phase assignment','Reported for the 150@NCs source condition','phase'),
 'rhombohedral':('CsMnCl3','Rhombohedral phase assignment','Reported for the 180 and 200 °C source conditions','phase'),
 'film':('CsMnCl3','Deposited nanocrystal film','A source-specific substrate specimen','film'),
 'dispersion':('CsMnCl3','Nanocrystal dispersion context','The suspension and its measurement state remain distinct','dispersion'),
 'cscl':('CsCl','Aged-sample phase component','Reported in the aged 150@NCs refinement','phase'),
 'cs3mncl5':('Cs3MnCl5','Aged-sample phase component','Reported in the aged 150@NCs refinement','phase'),
 'csmn4cl9':('CsMn4Cl9','Aged-sample phase component','Reported in the aged 150@NCs refinement','phase'),
}
entries=[]
for key,(formula,title,subtitle,kind) in cards.items():
 eid='matuhina2023-'+key+'-product-symbol';note='Symbolic composition and specimen context. Atomic positions, particle shape, surface coverage and phase fractions are not drawn.'
 if kind=='film':
  graphic='<rect x="235" y="345" width="630" height="26" rx="4" fill="#e48dc3"/><rect x="235" y="375" width="630" height="50" rx="5" fill="#dbeaf1" stroke="#789dab"/>'+tx(550,470,'Schematic layers; thickness and morphology are not to scale',20,anchor='middle')
  note='A generic deposited-film symbol. The binding caption specifies the actual substrate and aging or optical context; no polymer encapsulation is implied.'
 elif kind=='dispersion':
  graphic='<rect x="280" y="340" width="540" height="100" rx="12" fill="#f4dfed" stroke="#c4a4b8"/>'+tx(550,385,'Dispersed nanocrystal material',25,anchor='middle')+tx(550,420,'No individual particles or solvent molecules modeled',18,anchor='middle')
 else:
  graphic='<rect x="255" y="338" width="590" height="100" rx="15" fill="#edf4f7" stroke="#aac6d1"/>'+tx(550,379,'Source-reported phase identity',25,anchor='middle')+tx(550,417,'No unit cell or atomic coordinates depicted',20,anchor='middle')
 body=tx(48,59,title,30)+tx(48,107,subtitle,22)+tx(550,258,formula,64,anchor='middle')+graphic+wrap(note,52,548,86,20)
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="680" viewBox="0 0 1100 680"><title>'+html.escape(title)+'</title><desc>'+html.escape(note)+'</desc><rect x="1" y="1" width="1098" height="678" rx="20" fill="#fff" stroke="#b9ced8"/>'+body+'</svg>'
 rel='svg/'+eid+'.svg';(O/rel).write_text(svg,encoding='utf8')
 entries.append({'id':eid,'name':title,'formula':formula,'displayFormula':formula,'depictionKind':'symbolic_context','svgPath':rel,'model2dPath':None,'model3dPath':None,'functionalGroups':[],'caption':note,'limitations':['Identity/phase context only; no atomistic, exact-sample, DFT-input or training approval.','The paper supplies refinement tables; unresolved structural-table issues prevent this proposal from qualifying a CIF or model.'],'sourceUrls':['https://doi.org/10.1021/acsanm.2c04342'],'assetHashes':{'svgPath':sha(O/rel)},'binding_approved':False,'published':False,'eligible_training':False})
ek={k:entries[i] for i,k in enumerate(cards)}
labels={'nc150':'150@NCs','nc180-07':'180@NCs//0.7','nc180-05':'180@NCs//0.5','nc180-035':'180@NCs//0.35','nc200':'200@NCs'}
maps={}
def add(rec,sid,key,label,note,fids,phase=None,parent=None):
 rid='matuhina-2023-'+rec;maps.setdefault(rid,[]).append({'sid':sid,'key':key,'label':label,'note':note,'fids':fids.split(),'phase':phase,'parent':parent})
def sample(rec,sid,parent,kind):
 phase='cubic' if parent=='nc150' else 'rhombohedral';key=phase
 state={'route':'source preparation condition','xrd':'diffraction specimen','tem':'microscopy specimen','icp':'digested analytical specimen','optical':'optical dispersion','ta':'transient-absorption dispersion'}[kind]
 note=labels[parent]+' is the source label for this '+state+'. The '+phase+' phase is the paper’s diffraction assignment for that named preparation condition; this does not assert an identical physical aliquot across techniques.'
 if kind=='icp':note+=' ICP-MS measures the Mn:Cs analytical ratio, not the crystal phase or a complete dissolved formula.'
 if kind in ['optical','ta']:key='dispersion';note+=' The dispersed material identity is shown; its liquid environment, particle geometry and ligand coverage are not reconstructed.'
 if kind=='route':note+=' The source-defined Mn/Cs loading ratio remains a preparation label, distinct from measured Mn:Cs composition. The five conditions do not imply a full factorial design.'
 fids='phase variant-map'
 if kind=='icp':fids+=' icp-result'
 if kind=='tem':fids+=' morphology tem-histograms'
 if kind=='optical':fids+=' optical-summary'
 if kind=='ta':fids+=' ta-ste'
 add(rec,sid,key,labels[parent]+' · '+state,note,fids,phase+' (source assignment for the named preparation)',parent)
for sid in labels:sample('hot-injection-series',sid,sid,'route')
for suffix,kind,rec in [('xrd','xrd','structure-results'),('tem','tem','tem-procedure'),('icp','icp','icp-procedure'),('optical','optical','optical-results')]:
 for sid in labels:sample(rec,sid+'-'+suffix,sid,kind)
sample('structure-results','nc180-05','nc180-05','tem')
sample('optical-procedure','nc180-05','nc180-05','optical')
for sid in ['nc150','nc180-07','nc180-05']:sample('ta-procedure',sid+'-ta',sid,'ta')
sample('ta-procedure','nc150','nc150','ta')
for rec in ['optical-procedure','optical-results']:
 add(rec,'nc180-05-trpl','dispersion','180@NCs//0.5 · TRPL dispersion','The optimized source sample is measured by time-resolved photoluminescence in a dispersion context. The printed lifetime equation, table averages and 330/335 nm excitation discrepancy remain in the reader. No measured state is converted into a DFT configuration.','trpl phase','rhombohedral (source preparation assignment)','nc180-05')
add('optical-results','nc180-05-photo','dispersion','180@NCs//0.5 · photographed dispersion','This symbol identifies the source-labeled NC dispersion in the Figure4 photographic context. It is not a simulated photograph, emission spectrum or scale model.','optical-summary phase','rhombohedral (source assignment)','nc180-05')
for rec in ['ltpl-procedure','optical-results']:
 add(rec,'ltpl-nc180-05','film','180@NCs//0.5 · low-temperature PL film','The optimized sample is deposited on silica for low-temperature PL. It is separate from the solution spectra and the glass-supported LSC device. The film-specific 655/680/673 nm trends remain in their own source context; no thickness, morphology or polymer matrix is inferred.','ltpl-shift ltpl phase','rhombohedral (source preparation assignment)','nc180-05')
add('stability-results','rhombohedral-film','film','Rhombohedral NC film · structural aging','The source follows diffraction of a rhombohedral NC film over storage. Similar patterns through three months do not establish unchanged ligand coverage or solution luminescence. The exact loading variant and physical batch are not newly assigned.','phase-stability','rhombohedral (source film diffraction assignment)')
add('stability-results','cubic-film','film','Initially cubic NC film · aging trajectory','This context starts from the cubic 150@NCs preparation. The source reports phase change after nine weeks; the symbol does not assert that the aged film remains cubic. Its aged-component refinement is available as a separate context.','phase-stability','initially cubic; aged phase changes reported','nc150')
add('stability-results','rhombohedral-dispersion','dispersion','Rhombohedral NC dispersion · optical aging','This is the hexane-dispersion luminescence aging context, separate from film diffraction. Source prose uses PLQY/efficiency while the plot uses normalized integrated PL; the conflicting endpoint is not harmonized. No exact fresh-to-aged whole composition is assigned.','pl-stability','source-labeled rhombohedral material; aged whole phase not resolved')
add('stability-results','aged-rhombohedral','dispersion','Aged rhombohedral NCs · TEM context','Source FigureS9 shows partial aggregation of material described as aged rhombohedral NCs. Exact loading variant and age are not specified. This symbol does not supply particle coordinates, quantitatively resolve aged phases or measure ligand loss.','aged-tem','source-labeled rhombohedral material; no new aged phase refinement')
for key,formula in [('cscl','CsCl'),('cs3mncl5','Cs3MnCl5'),('csmn4cl9','CsMn4Cl9')]:
 add('stability-results','aged-nc150',key,'Aged 150@NCs · '+formula+' component','SI FigureS8 reports '+formula+' as one phase component in the aged 150@NCs refinement. The original fractions and their lack of supplied uncertainties remain in source results. This card is neither the whole-specimen formula nor a new independently synthesized product.','aged-phase-fractions',formula+' (reported component; no new refinement)','nc150')
for rec,sids in [('lsc-procedure',['lsc-film']),('device-results',['lsc-film','lsc-fresh','lsc-aged'])]:
 for sid in sids:
  note='The device uses NC material deposited on glass, explicitly unencapsulated. A loading variant or identical batch shared with spectroscopy is not assigned from the generic film label.'
  if sid=='lsc-aged':note+=' The same device film was measured after eleven weeks; a fresh phase formula is not imposed on the aged specimen.'
  else:note+=' The film’s light collection is distinct from the bare-glass and dark photodiode controls.'
  add(rec,sid,'film','LSC '+('aged film' if sid=='lsc-aged' else 'fresh film' if sid=='lsc-fresh' else 'NC film'),note,'lsc-setup lsc-result','not individually refined for this device context')

# Build strictly by enumerated record/sample pairs. No formula-based fallback.
contexts={};bindings=[];exclusions=[]
for rid,r in records.items():
 requested=maps.get(rid,[])
 for spec in requested:
  matches=[(i,p) for i,p in enumerate(r['products']) if p['sample_id']==spec['sid']]
  ck(rid+'/'+spec['sid']+' exact unique product',len(matches)==1);i,prod=matches[0]
  fs=[facts['matuhina2023-'+s] for s in spec['fids']]
  claimlinks=[]
  for f in fs:
   links=[(crid,j,m) for crid,cr in records.items() for j,m in enumerate(cr['measurements']) if m['id']==f['id']+'-claim']
   ck(rid+'/'+spec['sid']+'/'+f['id']+' canonical claim exists',bool(links))
   for crid,j,m in links:
    ck(f['id']+' exact canonical claim',m['value']['value']==f['claim'])
    claimlinks.append({'record_id':crid,'record_sha256':sha(paths[crid]),'json_pointer':f'/measurements/{j}','measurement_id':m['id'],'canonical_measurement':deepcopy(m)})
  evidence=list({json.dumps(ev,sort_keys=True):ev for f in fs for ev in f['evidence']}.values())
  caption=spec['note']+' This is a symbolic source-context reference, with no qualified unit cell, atomistic nanocrystal, exact surface geometry or training-pair admission.'
  entry=ek[spec['key']]
  row={'sample_id':spec['sid'],'label':spec['label'],'registry_id':entry['id'],'caption':caption,'phase':{'value':spec['phase'],'status':'reported_context','evidence':evidence,'note':'Canonical product fields remain unchanged. Source refinement tables and their conflicts are retained separately; this illustration is not an atomic reconstruction.'},'canonical_product_pointer':f'/products/{i}','canonical_product_snapshot':deepcopy(prod),'morphology':deepcopy(prod['morphology']),'composition_evidence':evidence,'source_fact_ids':[f['id'] for f in fs],'source_fact_links':[{'path':str(P/'source-facts.json'),'json_pointer':'/facts/'+str(sf['facts'].index(f)),'sha256':jsha(f)} for f in fs],'canonical_claim_links':claimlinks,'reported_parent_context':spec['parent'],'same_physical_batch_asserted':False,'projection_kind':'source_scoped_symbolic_context','phase_component_formula':entry['formula'] if spec['key'] in ['cscl','cs3mncl5','csmn4cl9'] else None,'training_eligible':False,'atomic_model':False,'binding_approved':False}
  contexts.setdefault(rid,[]).append(row)
  bindings.append({'record_id':rid,'sample_id':spec['sid'],'registry_id':entry['id'],'canonical_record_path':str(paths[rid]),'canonical_record_sha256':sha(paths[rid]),'product_pointer':f'/products/{i}','product_sha256':jsha(prod),'entry_sha256':jsha(entry),'source_fact_ids':row['source_fact_ids']})
 for i,prod in enumerate(r['products']):
  if not any(x['sid']==prod['sample_id'] for x in requested):
   reason='Combined, generic, control, precursor or model context lacks an explicit specimen mapping in this bounded proposal; no parent-formula fallback.'
   if rid.endswith('dft-procedure') or 'model' in prod['sample_id']:reason='Computational/model context is not a measured specimen. No DFT structure, coordinate array or experimental product identity is supplied by this symbolic proposal.'
   if prod['sample_id'] in ['lsc-bare','lsc-dark']:reason='Bare glass or dark photodiode control contains no asserted NC product identity.'
   if rid.endswith(('purification-trials','unisolated-control')):reason='Control/workup sample outcome does not establish an exact five-variant phase/product identity; preserve source observations without assigning a synthesized phase.'
   exclusions.append({'record_id':rid,'sample_id':prod['sample_id'],'canonical_product_pointer':f'/products/{i}','canonical_product_snapshot':deepcopy(prod),'reason':reason})
ck('all explicit records found',set(maps)<=set(records))
ck('five source route labels',len(contexts['matuhina-2023-hot-injection-series'])==5)
ck('no DFT mapping',not any('dft' in rid for rid in contexts))
ck('no atomic assets',all(e['model2dPath'] is None and e['model3dPath'] is None for e in entries))
ck('aged cubic distinct components', {x['phase_component_formula'] for x in contexts['matuhina-2023-stability-results'] if x['sample_id']=='aged-nc150'}=={'CsCl','Cs3MnCl5','CsMn4Cl9'})
notice='These symbolic cards distinguish the five source-defined preparations, source-scoped measurement specimens, deposited films, dispersions and aged phase components. They do not overwrite canonical composition fields or equate different physical aliquots. Structural Tables S1–S2 are retained, including zero occupancies, inconsistent site settings and the missing 200@ coordinate block; this proposal does not qualify a CIF or atomic model. DFT contexts and unresolved controls receive no experimental product-coordinate binding.'
save('registry-additions.json',{'schemaVersion':'1.0','source_id':'matuhina2023','entries':entries,'binding_approved':False})
save('product-contexts-additions.json',{'recordContexts':contexts,'sourceNotices':{'matuhina2023':notice}})
save('bindings.json',{'schema':'mattersyn-symbolic-product-context-proposal/1','author':'/root/peng1998_reader_assets','status':'author_draft_pending_distinct_audit','canonical_manifest':{'path':str(args.canonical_manifest),'sha256':sha(args.canonical_manifest)},'source_freeze':{'path':str(P/'package-freeze.json'),'sha256':sha(P/'package-freeze.json')},'source_audit':{'path':str(sourceaudit),'sha256':sha(sourceaudit)},'source_facts_sha256':sha(P/'source-facts.json'),'bindings':bindings,'excluded_contexts':exclusions,'exact_dispatch':maps,'scientific_records_unchanged':True,'independent_approval':False})
save('public-asset-proposal.json',{'status':'unapproved_public_candidates','assets':[{'path':str(O/e['svgPath']),'sha256':e['assetHashes']['svgPath'],'public_path':'assets/chemical-registry/matuhina2023-products/'+Path(e['svgPath']).name,'entry_id':e['id']} for e in entries],'excluded':'All source PDFs, full-page images, private text, author scripts, snapshots and audit inputs are excluded from this asset allowlist.'})
save('author-validation.json',{'status':'passed_author_mapping_checks_visuals_pending','checks':checks,'check_count':len(checks),'counts':{'contexts':len(bindings),'records':len(contexts),'mapped_record_samples':len({(b['record_id'],b['sample_id']) for b in bindings}),'excluded_products':len(exclusions),'symbols':len(entries),'atomic_models':0},'targeted_source_pages_actually_read_and_viewed':{'main':[3,4,5,8,9,10],'si':[6,7,13]},'independent_audit':False,'browser_approval':False})
(O/'README.md').write_text('''# Matuhina2023 symbolic product-context proposal

This private proposal uses the existing `recordContexts` / `sourceNotices` contract consumed by `crystal-viewer.mjs`. Merge the seven entries and copy only the exact SVG allowlist after distinct review. Replace each private-relative `svgPath` with its allowlisted public path during integration; keep hashes unchanged. No renderer code change or atomic model is required.

Five preparation labels and supported measurement contexts are explicitly enumerated. Film, dispersion, fresh/aged device and aged-cubic phase-component captions remain separate. Unspecified combined contexts, unisolated/workup controls, bare-glass/dark references and DFT products have explicit exclusions. Phase references on ICP/optical specimens cite the source preparation assignment and do not claim that these methods measured that phase or that aliquots are identical.

SI supplies structural tables, so the limitation is qualification, not absence of printed coordinates. Their occupancy/site-setting inconsistencies remain unresolved. No new CIF, exact nanocrystal, particle shape, ligand coverage, sample coordinate or training admission is introduced. All prior source and canonical files remain unchanged. This authoring packet requires a distinct source/mapping audit and later integration/browser checks.
''',encoding='utf8')
print(json.dumps({'counts':read(O/'author-validation.json')['counts'],'checks':len(checks)}))
