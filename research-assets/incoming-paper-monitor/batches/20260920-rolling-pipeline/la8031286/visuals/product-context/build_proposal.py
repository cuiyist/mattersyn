"""Private Pati symbolic contexts; source/canonical inputs are read-only."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib,html,textwrap,shutil
O=Path(__file__).resolve().parent; P=O.parents[1]
C=P/'canonical-proposal/v1'; S=Path('[local path redacted]')
assert not (O/'package-freeze.json').exists(), 'Preserve the frozen proposal.'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
checks=[]
def ck(k,v):checks.append({'check':k,'passed':bool(v)});assert v,k
for d in ['svg','previews','consumer-snapshot']:(O/d).mkdir(parents=True,exist_ok=True)
manifest=read(C/'record-manifest.json');records={};paths={}
for x in manifest['records']:
 p=Path(x['path']);ck('canonical hash '+x['record_id'],sha(p)==x['sha256']);records[x['record_id']]=read(p);paths[x['record_id']]=p
sf=read(P/'source-facts.json');facts={f['id']:f for f in sf['facts']}
audit=P/'source-independent-audit/independent-audit.json'
ck('current passed source',read(audit)['status']=='passed' and read(audit)['source_package_freeze_sha256']==sha(P/'package-freeze.json'))

# Formula is populated only for explicitly qualified CeO2 phase references.
cards={
 'as-ethanol':('Ethanol-derived as-prepared powder','','Unresolved whole composition','Local CeO2 evidence does not establish a pure powder.','powder'),
 'as-propanol':('1-Propanol-derived as-prepared powder','','Unresolved whole composition','Local CeO2 evidence does not establish a pure powder.','powder'),
 'as-butanol':('1-Butanol-derived as-prepared powder','','Unresolved whole composition','Local CeO2 evidence does not establish a pure powder.','powder'),
 'calcined':('Calcined powder · source phase assignment','CeO2','Cubic phase assigned by the source','A reported diffraction assignment; no atomic model or new elemental assay.','phase'),
 'local-ceo2':('Local CeO2 microscopy evidence','CeO2','HRTEM / selected-area diffraction','Local crystalline regions are not a whole-powder purity measurement.','local'),
 'unresolved':('Powder measurement context','','Whole composition remains unresolved','Sample history and technique are specified in the selected context.','powder'),
 'dispersion':('Solvent-specific DLS context','','Dispersed particle / aggregate measurement','Reported radii versus conclusion diameters remain an unresolved source conflict.','dispersion'),
 'xps-as-short':('As-prepared surface · short X-ray exposure','','81% Ce(III) / 19% Ce(IV)','Main: less than 15 min. SI: approximately 15 min / 15 min.','xps'),
 'xps-calcined-short':('Calcined surface · short X-ray exposure','','33% Ce(III) / 67% Ce(IV)','Main: less than 15 min. SI: approximately 15 min / 15 min.','xps'),
 'xps-as-long':('As-prepared surface · long X-ray exposure','','No Ce(IV) evidence in the spectrum','More than 5 h exposure; absence of evidence is not an exact zero fraction.','xps'),
 'xps-calcined-long':('Calcined surface · long X-ray exposure','','Approximately 45% Ce(III)','More than 5 h exposure; an unreported complementary fraction is not inserted.','xps'),
}
def tx(x,y,s,size=22,color='#244756',anchor='start'):
 return f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" fill="{color}" text-anchor="{anchor}">{html.escape(s)}</text>'
def wrap(s,x,y,width=80,size=21):return ''.join(tx(x,y+30*i,t,size) for i,t in enumerate(textwrap.wrap(s,width)))
entries=[]
for key,(title,formula,headline,detail,kind) in cards.items():
 eid='pati2009-'+key+'-product-symbol'
 note='Symbolic specimen context only. No atomic positions, particle envelope, phase fraction or ligand coverage is depicted.'
 if kind=='xps':note='These are source-reported surface-fit results under X-ray exposure, not a bulk formula, oxygen stoichiometry or independent synthesis outcome.'
 if kind=='local':note='The CeO2 label refers to the local diffraction/fringe assignment. The whole as-prepared specimen remains unresolved and may contain other components.'
 body=tx(46,62,title,29)+tx(46,111,'Pati et al. · Langmuir 2009 · symbolic source context',21,'#687f8b')
 body+='<rect x="47" y="156" width="1006" height="310" rx="18" fill="#f1f6f8" stroke="#b5cdd7"/>'
 if formula:body+=tx(550,260,formula,65,anchor='middle')+tx(550,323,headline,28,anchor='middle')
 else:body+=wrap(headline,90,258,57,32)
 body+=wrap(detail,90,385,78,21)
 body+=wrap(note,52,528,83,21)+tx(52,637,'No coordinate model · no exact structure–recipe or training admission',20,'#687f8b')
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="680" viewBox="0 0 1100 680"><title>'+html.escape(title)+'</title><desc>'+html.escape(note)+'</desc><rect x="1" y="1" width="1098" height="678" rx="20" fill="white" stroke="#b9ced8"/>'+body+'</svg>'
 rel='svg/'+eid+'.svg';(O/rel).write_text(svg,encoding='utf8')
 entries.append({'id':eid,'name':title,'formula':formula,'displayFormula':formula or 'Whole composition unassigned','depictionKind':'symbolic_context','svgPath':rel,'model2dPath':None,'model3dPath':None,'functionalGroups':[],'caption':note,'limitations':['Source-scoped symbolic reference; no measured atomic model or pure-product inference beyond the explicit source phase claim.','XPS oxidation fractions are surface-fit observations, not a new bulk formula.'],'sourceUrls':['https://doi.org/10.1021/la8031286'],'assetHashes':{'svgPath':sha(O/rel)},'binding_approved':False,'published':False,'eligible_training':False})
ek={k:entries[i] for i,k in enumerate(cards)}
maps={}
def add(rec,sid,key,label,note,fids,phase=None,parent=None):
 maps.setdefault('pati-2009-'+rec,[]).append({'sid':sid,'key':key,'label':label,'note':note,'fids':fids.split(),'phase':phase,'parent':parent})
for solvent,label in [('ethanol','Ethanol'),('propanol','1-Propanol'),('butanol','1-Butanol')]:
 add(solvent+'-route',solvent+'-as-prepared','as-'+solvent,label+' · as-prepared powder','This is the separately prepared '+label.lower()+' route. Its complete as-prepared composition is unresolved. The source proposes a mixture of cerium–TEA nitrate, Ce(OH)4 and hydrated ceria without measured phase fractions; these are not isolated, solved compounds. Local CeO2 HRTEM/SAED does not establish bulk purity.','asprep-xrd tem-size saed',None,solvent+'-as-prepared')
 add('calcination',solvent+'-calcined','calcined',label+' · calcined powder','The source assigns pure cubic CeO2 after 200 °C for 3 h for the calcined material. This named solvent preparation is kept separate from the other two alternatives. The phase claim is not a measured full elemental assay, occupancy refinement or proof of identical aliquots across methods.','calcination calcined-xrd bet-results','cubic CeO2 (source diffraction assignment)',solvent+'-calcined')
 add('dls',solvent+'-solution-dls','dispersion',label+' · DLS dispersion','The source reports a '+label.lower()+' solution-particle context. Dispersion preparation and reconstitution are not specified. Results call the size a hydrodynamic radius and the conclusion calls the same value a diameter; no factor-of-two correction, phase assignment or TEM-size equivalence is made.','dls-values conclusion-dls dls-acquisition',None,solvent+'-solution-dls')

asnote='The as-prepared bulk pattern does not match a known cerium compound in the source database. The suggested heterogeneous composition remains a hypothesis; local CeO2 evidence is not a bulk-purity result.'
calcnote='Figure 2b is assigned cubic CeO2 after 200 °C for 3 h, with approximately 5 nm Scherrer size. The solvent and exact physical batch for this diffraction specimen are not explicitly identified; no link to a specific TEM aliquot is asserted.'
for rec,sid in [('xrd','xrd-as-prepared'),('xrd','source-unit-pati2009-figure-2-a'),('structure-results','as-prepared-xrd-specimen-solvent-unspecified')]:add(rec,sid,'unresolved','As-prepared · bulk diffraction',asnote,'asprep-xrd',None)
for rec,sid in [('xrd','xrd-calcined'),('xrd','source-unit-pati2009-figure-2-b'),('structure-results','calcined-xrd-specimen-solvent-not-explicit')]:add(rec,sid,'calcined','Calcined · bulk diffraction',calcnote,'calcined-xrd','cubic CeO2 (source diffraction assignment)')
for panel,solvent,label in [('a','ethanol','Ethanol'),('b','propanol','1-Propanol'),('c','butanol','1-Butanol')]:
 add('structure-results','source-unit-pati2009-figure-1-'+panel,'local-ceo2',label+' · local microscopy (Figure 1'+panel+')','The source identifies this panel as the '+label.lower()+' as-prepared sample. The {200}, {220} and {311} assignments and 0.267 nm observed fringe spacing support a local CeO2 interpretation; 0.271 nm is a cited reference spacing. They do not supply a refined lattice, whole-composition identity or pure CeO2 powder label.','saed tem-size figure1-bars asprep-xrd','local cubic CeO2 assignment; whole specimen unresolved',solvent+'-as-prepared')
for sid in ['butanol-calcined-microscopy','source-unit-pati2009-figure-1-d']:
 add('structure-results',sid,'calcined','1-Butanol · calcined microscopy (Figure 1d)','This panel is explicitly the 1-butanol preparation after 200 °C for 3 h. HRTEM and SAED are assigned cubic CeO2; the additional {111} label is preserved. The image is not an atomic-coordinate reconstruction.','calcined-tem figure1-bars','cubic CeO2 (source microscopy assignment)','butanol-calcined')
for rec,sid in [('bet','calcined-powders-for-reported-areas'),('property-results','three-calcined-solvent-powders')]:
 add(rec,sid,'calcined','Calcined powders · three separate solvent variants','This is a comparison of separately prepared ethanol, 1-propanol and 1-butanol calcined powders, not a pooled specimen. BET areas are 78, 80 and 84 m²/g, respectively. The reported 10, 9.8 and 9.3 nm diameters are derived using a spherical-particle assumption and are distinct from TEM crystallite sizes and DLS radii/diameters.','bet-results bet-diameters calcined-xrd','cubic CeO2 (source calcined-material assignment)')
for rec,sid in [('tga','butanol-tga'),('property-results','butanol-as-prepared-tga'),('property-results','source-unit-pati2009-figure-3-a')]:
 add(rec,sid,'as-butanol','1-Butanol · as-prepared TGA specimen','This is the as-prepared 1-butanol powder during TGA in air. The mass-loss intervals and the source interpretation after 600 °C are thermal-analysis observations; they do not redefine the 200 °C calcination product. No unique initial mixture fractions are solved from the proposed conversion losses.','tga-steps tga-calculation tga-acquisition',None,'butanol-tga')
for rec,sid,state in [('dsc','butanol-dsc','as-prepared'),('dsc','dsc-calcined','calcined'),('property-results','source-unit-pati2009-figure-3-b','as-prepared'),('property-results','source-unit-pati2009-figure-3-c','calcined')]:
 add(rec,sid,'unresolved',state.capitalize()+' · DSC specimen','The '+state+' DSC comparison retains its own thermal-analysis scope. The source reports a 173 °C endotherm for the as-prepared sample and no such peak in the calcined comparison. The inferred 150–180 °C transition is an author interpretation, not a new preparation or measured atomic model. Exact cross-technique aliquot identity is unknown.','dsc-results dsc-acquisition',None,'butanol-dsc' if state=='as-prepared' else 'dsc-calcined')
add('packing','packing-powder','unresolved','Dried powder · packing-density context','The room-temperature-dried porous powder has a rough packing-density estimate. The cited bulk CeO2 density is a reference, not this powder’s measured crystal density. Solvent and whole composition are not newly assigned.','packing-result packing-acquisition')
xps={
 'xps-as-short':('As-prepared · short-exposure XPS','The main reports less than 15 min of X-ray exposure; SI uses approximately 15 min or 15 min. The reported 81% Ce(III) and 19% Ce(IV) are surface-fit fractions, not a bulk formula.','xps-short-main si-short-results si-exposure xps-elements'),
 'xps-calcined-short':('Calcined · short-exposure XPS','The main reports less than 15 min of X-ray exposure; SI uses approximately 15 min or 15 min. The reported 33% Ce(III) and 67% Ce(IV) are surface-fit fractions, not Ce/O stoichiometry.','xps-short-main si-short-results si-exposure xps-elements'),
 'xps-as-long':('As-prepared · long-exposure XPS','After more than 5 h of X-ray exposure the source finds no evidence of Ce(IV) in the spectrum. This is not a measured exact zero bulk fraction or a new pure Ce(III) product.','si-long-results si-fit-four si-exposure'),
 'xps-calcined-long':('Calcined · long-exposure XPS','After more than 5 h of X-ray exposure the source reports approximately 45% Ce(III). No unreported 55% complement or oxygen-deficient formula is inserted.','si-long-results si-exposure'),
}
for sid,(label,note,fids) in xps.items():add('xps',sid,sid,label,note+' The solvent and exact physical batch remain unspecified; beam exposure is analytical history, not a synthesis step.',fids,None,sid)
for panel,sid in [('a','xps-as-long'),('b','xps-as-short'),('c','xps-calcined-long'),('d','xps-calcined-short')]:
 label,note,fids=xps[sid];add('xps-fit','source-unit-pati2009-figure-s1-'+panel,sid,label+' (Figure S1'+panel+')',note+' The source figure/fit label discrepancies are retained; this is the supported panel context, not a newly joined batch.',fids,None,sid)
add('xps-fit','as-prepared-long-exposure-surface','xps-as-long',xps['xps-as-long'][0],xps['xps-as-long'][1],xps['xps-as-long'][2],None,'xps-as-long')

contexts={};bindings=[];exclusions=[]
for rid,r in records.items():
 requested=maps.get(rid,[])
 ck(rid+' distinct requested sample IDs',len({x['sid'] for x in requested})==len(requested))
 for spec in requested:
  matches=[(i,p) for i,p in enumerate(r['products']) if p['sample_id']==spec['sid']];ck(rid+'/'+spec['sid']+' unique product',len(matches)==1);i,prod=matches[0]
  fs=[facts['pati2009-'+s] for s in spec['fids']];links=[];measurements=[]
  for f in fs:
   found=[]
   for crid,cr in records.items():
    for j,m in enumerate(cr['measurements']):
     if m['id']==f['id']+'-claim' or m['id'].startswith(f['id']+'-q'):
      item={'record_id':crid,'record_sha256':sha(paths[crid]),'json_pointer':f'/measurements/{j}','measurement_id':m['id'],'canonical_measurement':deepcopy(m)}
      measurements.append(item)
      if m['id']==f['id']+'-claim':ck(f['id']+' exact claim transport',m['value']['value']==f['claim']);found.append(item)
   ck(rid+'/'+spec['sid']+'/'+f['id']+' canonical claim',bool(found));links+=found
  # Use canonical rendered locators in the public consumer, preserving original locators separately.
  evidence=list({json.dumps(ev,sort_keys=True):ev for x in links for ev in x['canonical_measurement']['evidence']}.values())
  entry=ek[spec['key']];caption=spec['note']+' The illustration is symbolic; no atomic coordinates, particle shape, surface coverage or exact training pair is supplied.'
  row={'sample_id':spec['sid'],'label':spec['label'],'registry_id':entry['id'],'caption':caption,'phase':{'value':spec['phase'],'status':'reported_context' if spec['phase'] else 'not_assigned','evidence':evidence,'note':'This display does not overwrite canonical composition or phase fields. Technique-local assignments and analytical states remain scoped.'},'canonical_product_pointer':f'/products/{i}','canonical_product_snapshot':deepcopy(prod),'morphology':deepcopy(prod['morphology']),'composition_evidence':evidence,'source_fact_ids':[f['id'] for f in fs],'source_fact_links':[{'path':str(P/'source-facts.json'),'json_pointer':'/facts/'+str(sf['facts'].index(f)),'sha256':jsha(f)} for f in fs],'canonical_claim_links':links,'canonical_measurement_links':measurements,'conflict_ids':sorted({v for f in fs for v in f.get('conflict_ids',[])}),'reported_parent_context':spec['parent'],'same_physical_batch_asserted':False,'projection_kind':'source_scoped_symbolic_context','training_eligible':False,'atomic_model':False,'binding_approved':False}
  contexts.setdefault(rid,[]).append(row)
  bindings.append({'record_id':rid,'sample_id':spec['sid'],'registry_id':entry['id'],'canonical_record_path':str(paths[rid]),'canonical_record_sha256':sha(paths[rid]),'product_pointer':f'/products/{i}','product_sha256':jsha(prod),'entry_sha256':jsha(entry),'source_fact_ids':row['source_fact_ids']})
 for i,prod in enumerate(r['products']):
  if any(s['sid']==prod['sample_id'] for s in requested):continue
  reason='Combined acquisition, workup, figure, or generic comparison context is not assigned a single product identity; separately supported specimens have explicit mappings.'
  if rid.endswith(('source-context','source-materials')):reason='Bibliographic, source/conflict/gap or precursor/stock context is not a measured final product.'
  if rid.endswith('mechanistic-context') or 'model' in prod['sample_id']:reason='Cited or author-interpreted mechanism/model context is not a separately synthesized, composition-verified specimen.'
  if rid.endswith('filtrate-diagnostic'):reason='Separate filtrate diagnostic aliquot; no identified isolated solid or reported whole-composition outcome.'
  if rid.endswith('-route'):reason='Generic reaction/workup trajectory or retained/discarded fractions; the final named solvent-specific powder receives the product mapping.'
  exclusions.append({'record_id':rid,'sample_id':prod['sample_id'],'canonical_product_pointer':f'/products/{i}','canonical_product_snapshot':deepcopy(prod),'reason':reason})
ck('all maps reference records',set(maps)<=set(records))
total=sum(len(r['products']) for r in records.values());ck('complete included/excluded accounting',len(bindings)+len(exclusions)==total==156)
ck('atomic paths absent',all(e['model2dPath'] is None and e['model3dPath'] is None for e in entries))
ck('XPS and unresolved entries have no formula',all(not e['formula'] for k,e in ek.items() if k not in ['calcined','local-ceo2']))
ck('all three routes mapped separately',all(len(contexts['pati-2009-'+s+'-route'])==1 for s in ['ethanol','propanol','butanol']))
notice='As-prepared whole composition remains unresolved despite local CeO2 microscopy. The source assigns cubic CeO2 to calcined material; named solvent variants, bulk diffraction, local microscopy, DLS dispersions and XPS exposure states retain separate scopes. Surface Ce(III)/Ce(IV) fits do not define bulk stoichiometry. No atomic model, identical-aliquot cross-technique join or exact training pair is provided.'
save('registry-additions.json',{'schemaVersion':'1.0','source_id':'pati2009','entries':entries,'binding_approved':False})
save('product-contexts-additions.json',{'recordContexts':contexts,'sourceNotices':{'pati2009':notice}})
public_contexts={rid:[{k:deepcopy(row[k]) for k in ['sample_id','label','registry_id','caption','phase','morphology','conflict_ids','reported_parent_context','same_physical_batch_asserted','projection_kind','training_eligible','atomic_model','binding_approved']} for row in rows] for rid,rows in contexts.items()}
save('public-product-contexts-proposal.json',{'recordContexts':public_contexts,'sourceNotices':{'pati2009':notice}})
save('bindings.json',{'schema':'mattersyn-symbolic-product-context-proposal/1','author':'/root/backlog_eta','status':'author_draft_pending_distinct_audit','canonical_manifest':{'path':str(C/'record-manifest.json'),'sha256':sha(C/'record-manifest.json')},'canonical_package':{'path':str(C/'package-manifest.json'),'sha256':sha(C/'package-manifest.json')},'source_freeze':{'path':str(P/'package-freeze.json'),'sha256':sha(P/'package-freeze.json')},'source_audit':{'path':str(audit),'sha256':sha(audit)},'source_facts_sha256':sha(P/'source-facts.json'),'bindings':bindings,'excluded_contexts':exclusions,'exact_dispatch':maps,'scientific_records_unchanged':True,'independent_approval':False})
save('public-asset-proposal.json',{'status':'unapproved_public_candidates','assets':[{'path':str(O/e['svgPath']),'sha256':e['assetHashes']['svgPath'],'public_path':'assets/chemical-registry/pati2009-products/'+Path(e['svgPath']).name,'entry_id':e['id']} for e in entries],'excluded':'Original PDFs/SI, full-page scans, raw text, snapshots, scripts, private paths, bindings and checks are not public image assets.'})
save('author-validation.json',{'author':'/root/backlog_eta','status':'passed_author_mapping_checks_visuals_pending','checks':checks,'check_count':len(checks),'counts':{'canonical_records':len(records),'canonical_product_context_slots':total,'contexts':len(bindings),'records_with_mappings':len(contexts),'excluded_contexts':len(exclusions),'symbols':len(entries),'atomic_models':0},'independent_audit':False,'browser_approval':False})
consumer=S/'dist/crystal-viewer.mjs';shutil.copyfile(consumer,O/'consumer-snapshot/crystal-viewer.mjs')
save('consumer-snapshot/provenance.json',{'path':str(consumer),'sha256':sha(consumer),'snapshot':'crystal-viewer.mjs','purpose':'Reproducible actual consumer function checks; not browser approval.'})
(O/'README.md').write_text('''# Pati 2009 symbolic product-context proposal

Private author proposal using the current `recordContexts` / `sourceNotices` contract in `crystal-viewer.mjs`. Copy only exact SVG candidates from `public-asset-proposal.json` after independent approval. During integration, map each entry svgPath to its allowlisted public path; strip private author provenance paths from public data. No atomic assets are supplied.

All 156 record/sample slots are either explicitly mapped or excluded with a reason. A context is not an independent physical sample. The three solvent preparations stay separate; local CeO2 assignments do not overwrite unresolved whole compositions. Calcined phase assignments cite the source, not a new elemental assay. XPS surface fractions are not bulk formulas or oxygen stoichiometry. Grouped and bibliographic/model contexts are not fabricated products.

Canonical v1 remains frozen. Its pending independent review and the known reader review_scope enum correction are separate gates; a later metadata-only canonical package revision can use a narrow unchanged-record receipt. Any scientific record change requires revalidation. Function checks use a retained exact current consumer snapshot; no mounted-browser, integration, publication or independent scientific approval is claimed.
''',encoding='utf8')
print(json.dumps({'counts':read(O/'author-validation.json')['counts'],'checks':len(checks)}))
