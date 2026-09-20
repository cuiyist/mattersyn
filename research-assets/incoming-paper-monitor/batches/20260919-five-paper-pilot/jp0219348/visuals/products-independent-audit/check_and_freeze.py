"""Independent product/typed-SI projection review, without editing author files."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,csv,re,copy,collections,xml.etree.ElementTree as ET
A=Path(__file__).resolve().parent;H=A.parents[1];P=H/'visuals/products';R=H/'si-reader-proposal';C=H/'canonical-proposal/v2'
bound={};groups=collections.Counter();failed=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p).resolve();bound[str(p)]=sha(p);return p
def read(p):return json.loads(bind(p).read_bytes())
def ck(group,label,ok):
    groups[group]+=1
    if not ok:failed.append({'group':group,'check':label})
def walk(x,p=''):
    yield p,x
    if isinstance(x,dict):
        for k,v in x.items():yield from walk(v,p+'/'+k)
    elif isinstance(x,list):
        for i,v in enumerate(x):yield from walk(v,p+'/'+str(i))
pm=read(P/'package-manifest.json');rm=read(R/'package-manifest.json')
ck('freeze','product manifest identity',sha(P/'package-manifest.json')=='6cb1bc1d721a79ed6eca98b0fac1436d138222f2367ecdacaac3fa5ce5eec2f9')
ck('freeze','SI manifest identity',sha(R/'package-manifest.json')=='79ddcb9f78a008702a6b42f337837367d502e6f1fe894aef960a41d8b918c2e3')
for group in ['public_assets','private_files','bound_source_files']:
    for name,digest in pm[group].items():ck('freeze',group+' '+name,sha(bind(H/name))==digest)
for name,digest in rm['files'].items():ck('freeze','SI '+name,sha(bind(H/name))==digest)
model=read(P/'heo2003-average-view.json');base=read(H/'structure-candidate/average-model.json');proposal=read(P/'product-viewer-proposal.json');registry=read(P/'registry-entry-proposal.json')
ck('model','Exact audited CIF bytes',(P/'heo2003-average-position-occupancy.cif').read_bytes()==(H/'structure-candidate/heo2003-average-position-occupancy.cif').read_bytes())
for key in ['fractionalSites','asymmetric_sites','spaceGroup','spaceGroupNumber','origin_choice','coordinate_scope']:
    ck('model','Unchanged audited model '+key,model[key]==base[key])
ck('model','Cell side/ESD scope retained',model['cell']=={'a':24.942,'b':24.942,'c':24.942,'alpha':90,'beta':90,'gamma':90,'length_unit':'angstrom','a_raw':'24.942(4)'})
ck('model','680 distinct positions /872 components',len(model['fractionalSites'])==680 and sum(len(x['components']) for x in model['fractionalSites'])==872)
counts=collections.defaultdict(float)
for site in model['fractionalSites']:
    ck('model-sites',site['id']+' Cartesian conversion',all(abs(c-f*24.942)<1e-10 for c,f in zip(site['cartesian'],site['fractional'])))
    ck('model-sites',site['id']+' occupancy sum',site['occupancy_sum']==sum(c['occupancy'] for c in site['components']))
    for c in site['components']:counts[c['element']]+=c['occupancy']
ck('model','Independent weighted composition642',dict(counts)=={'Si':96,'Al':96,'O':384,'In':66} and sum(counts.values())==642 and model['weighted_counts']==dict(counts))
for g in model['groups']:
    subset=[s for s in model['fractionalSites'] if s['source_label']==g['label']]
    ck('model-groups',g['label']+' exact count/components',len(subset)==g['positions_per_cell'] and all(s['components']==g['components'] and s['occupancy_sum']==g['occupancy_sum'] for s in subset))
ck('model','Mixed sites remain statistical',all(s['components']==[{'element':'Si','occupancy':0.5,'source_label':'(Si,Al)'},{'element':'Al','occupancy':0.5,'source_label':'(Si,Al)'}] for s in model['fractionalSites'] if s['mixed']) and sum(s['mixed'] for s in model['fractionalSites'])==192)
for label,occupancy in [('In(II)',25/32),('In(IIa)',1/32)]:ck('model',label+' split occupancy unchanged',all(s['occupancy_sum']==occupancy for s in model['fractionalSites'] if s['source_label']==label))
for k in ['unique_ordered_microstate','exact_structure_recipe_eligible','dft_input_eligible','training_approved']:ck('model','No unsupported eligibility '+k,model[k] is False)
ck('model','No finite particle/ligand shell',model['finite_particle'] is None and model['surface_ligands'] is None)
limits=' '.join(model['limitations'])
for text in ['not an author-supplied CIF','ADPs','107.1602','111.7(20)','2.27','three-ESD','No sulfur']:
    ck('model','Visible source limitation '+text,text in limits if text!='ADPs' else 'displacement parameters are omitted' in limits)
expected={'heo-2003-in66-route':'final','heo-2003-single-crystal-acquisition':'final','heo-2003-average-structure':'average-model'}
ck('bindings','Only three qualified record/sample pairs',{b['record_id']:b['sample_id'] for b in proposal['bindings']}==expected)
for b in proposal['bindings']:
    p=C/'canonical-drafts'/(b['record_id']+'.json');r=read(p)
    ck('bindings',b['record_id']+' source record hash',sha(p)==b['canonical_record_sha256'])
    ck('bindings',b['record_id']+' exact existing product object',b['canonical_json_pointer']=='/products/0' and b['canonical_sample']==r['products'][0] and b['sample_id']==r['products'][0]['sample_id'])
    ck('bindings',b['record_id']+' no exact-label approval',b['exact_structure_recipe_eligible'] is False and b['binding_approved'] is False)
allids={p.stem for p in (C/'canonical-drafts').glob('*.json')}
ck('bindings','Other seven contexts explicitly excluded',set(proposal['excluded_record_ids'])==allids-set(expected))
ck('bindings','Scoped custom adapter required',registry['requiresSourceSpecificAdapter'] and registry['viewerKind']=='source_average_occupancy' and registry['finiteModelPath'] is None)
svg=ET.fromstring((P/'heo2003-average-cell.svg').read_bytes());circles=svg.findall('{http://www.w3.org/2000/svg}circle')
ck('fallback SVG','Exactly680 average marker circles',len(circles)==680)
for c,s in zip(circles,sorted(model['fractionalSites'],key=lambda s:sum(s['cartesian']))):
    x,y,z=s['cartesian'];px=330+(x-y)*.707*9;py=400+(x+y)*.35*9-z*.85*9
    ck('fallback SVG',s['id']+' exact view-only projection/color',abs(float(c.attrib['cx'])-px)<=.00051 and abs(float(c.attrib['cy'])-py)<=.00051 and c.attrib['fill']==model['colors'][s['source_label']])
source=read(H/'si-complete-candidate/all-reflections.json');data=read(R/'heo2003-reflections.json');mapping=read(R/'private-projection-map.json')
def public_cell(c):
    x=copy.deepcopy(c)
    x['evidence'].pop('source_path',None);x['evidence'].pop('original_crop_path',None)
    x.get('effective_audit_reference',{}).pop('path',None)
    return x
def public_row(r):
    x={k:copy.deepcopy(v) for k,v in r.items() if k not in ['author_transcription','effective_independent_audit']}
    x['cells']=[public_cell(c) for c in r['cells']]
    return x
ck('SI projection','Exact all-row source order/coverage',len(data['rows'])==1209 and [r['row_id'] for r in data['rows']]==[r['row_id'] for r in source['rows']])
ck('SI projection','Counts match distinct passed aggregate',data['counts']==source['counts'])
for i,(src,row,mp) in enumerate(zip(source['rows'],data['rows'],mapping['rows'])):
    ck('SI rows',row['row_id']+' exact scientific payload after documented private metadata deletion',public_row(src)==row)
    ck('SI rows',row['row_id']+' trace mapping',mp=={'row_id':row['row_id'],'source_json_pointer':f'/rows/{i}','public_json_pointer':f'/rows/{i}','cell_ids':[c['cell_id'] for c in row['cells']]})
    for c,sc in zip(row['cells'],src['cells']):
        ck('SI cells',c['cell_id']+' exact signed/raw/unit/uncertainty/source scope',c==public_cell(sc))
expected_unresolved=copy.deepcopy(source['unresolved_cells'])
for x in expected_unresolved:x['cell']=public_cell(x['cell'])
ck('SI projection','Both unresolved-cell objects exactly retained',data['unresolved_cells']==expected_unresolved)
cells=[c for r in data['rows'] for c in r['cells'] if c['evidence']['column_key']!='marker']
ck('SI projection','7254 numericpositions/7252 resolved/two sign nulls',len(cells)==7254 and sum(c['numeric_value'] is not None for c in cells)==7252 and {c['cell_id'] for c in cells if c['numeric_value'] is None}=={'si-p11-R-r035-Fobs2','si-p12-L-r012-Fcal2'})
ck('SI projection','137 negative observations and one zero',sum(c['evidence']['column_key']=='Fobs2' and c['numeric_value'] is not None and c['numeric_value']<0 for c in cells)==137 and sum(c['evidence']['column_key']=='Fobs2' and c['numeric_value']==0 for c in cells)==1)
ck('SI projection','Scientific limits exclude coordinate recalculation and new samples',any('does not recompute' in x for x in data['scientific_limits']) and any('not a new synthesis sample' in x for x in data['scientific_limits']))
tsv=list(csv.DictReader(bind(R/'heo2003-reflections.tsv').read_text(encoding='utf-8').splitlines(),delimiter='\t'))
ck('SI TSV','All1209 rows',len(tsv)==1209)
for t,r in zip(tsv,data['rows']):
    cs={c['evidence']['column_key']:c for c in r['cells']};e=r['cells'][0]['evidence']
    ck('SI TSV',r['row_id']+' row/source locator',t['row_id']==r['row_id'] and int(t['pdf_page'])==e['pdf_page'] and t['block']==e['column_block'] and int(t['row_in_block'])==e['row_in_block'])
    for k in ['h','k','l']:ck('SI TSV',r['row_id']+' index '+k,int(t[k])==cs[k]['numeric_value'])
    for k in ['Fcal2','Fobs2','sigma_Fobs2']:
        ck('SI TSV',r['row_id']+' raw '+k,t[k+'_raw']==cs[k]['raw_text'])
        ck('SI TSV',r['row_id']+' signed '+k,t[k+'_numeric']=='' if cs[k]['numeric_value'] is None else float(t[k+'_numeric'])==cs[k]['numeric_value'])
    ck('SI TSV',r['row_id']+' literal uninterpreted marker',t['marker_raw']==cs['marker']['raw_text'])
    for k in ['Fcal2','Fobs2']:ck('SI TSV',r['row_id']+' sign status '+k,t[k+'_sign_status']==cs[k].get('sign_status','resolved'))
for name in pm['public_assets']:
    p=H/name;text=p.read_text(encoding='utf-8');ck('public path hygiene',name+' no absolute local path',not re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]',text))
for p,x in walk(data):
    if isinstance(x,str):ck('public SI metadata',p+' no source path/image delivery',not re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]',x) and not x.endswith(('.pdf','.png','.jpg')))
runtime=read(A/'runtime-checks.json');ck('runtime','7939 independent exported-function checks passed',runtime['checks']==7939 and not runtime['failed'])
for p in (P/'author-preview').glob('*.png'):bind(p)
for p in [Path(__file__),A/'runtime-checks.mjs']:bind(p)
report={'schema':'mattersyn.heo_product_si_projection_independent_audit/1','at':datetime.now(timezone.utc).isoformat(),'author':'/root/peng1998_reader_assets','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','status':'passed_scientific_projection_and_function_scope' if not failed else 'findings','product_manifest_sha256':sha(P/'package-manifest.json'),'si_manifest_sha256':sha(R/'package-manifest.json'),'checks':dict(groups),'check_count':sum(groups.values()),'runtime_check_count':7939,'findings':failed,'counts':pm['counts'],'actual_scope':'Read both adapter modules, both integration contracts and all scientific limitations; independently compared complete arrays/CIF, three product bindings, all1209 SI row/cell projections and all TSV fields. Reused the passed geometry/addendum and aggregate SI audits; no new source-cell or crystallographic refinement audit. Actually viewed seven retained author screenshots (desktop/mobile unit cell, repeated model, occupancy/caveats, unresolved signs, mobile table, SVG fallback). Screenshots are author-captured evidence, not independent live interaction. Actual exported functions and scope guards were executed separately.','manual_scientific_findings':['The three allowed final-product/diffraction/average-model contexts are justified; EPXMA exposure, XPS sputtering, earlier refinement, topology and theoretical contexts do not receive coordinates.','One marker represents a mixed average position. Si0.5/Al0.5, 25/32 and1/32 In split occupancies,680positions/872components/642weightedatoms remain explicit; no ordered microstate, ligand shell or finite particle is selected.','The byte-identical curator-derived CIF remains distinct from an author-supplied or DFT-ready file. ADPs are omitted and the unresolved107.1602 versus111.7(20) degree tension remains visible.','The reflection table preserves all raw digits, signed values, negative observations,zero,uncertainties,uninterpreted markers and two null signs. Calculated factors are source-reported, not recomputed from this limited model.','Local-path/private-wrapper removal is separate from scientific data preservation. Source/audit hashes and locators remain; no whole source image is delivered by this package.'],'limits':['Final integrated DOM/WebGL/browser behavior and promotion remain separate gates.','Custom average-occupancy adapter must precede generic crystal rendering.','All source ambiguities remain; no exact training pair or new SI-cell reading is certified.'],'mutations':'Only products-independent-audit private files written. All product/SI/canonical/source/Site files untouched.','bound_files':bound}
report['checker_development_note']='checker-draft-1.json is retained. Its three path findings were checker false positives on http(s) URL substrings, corrected by requiring a drive-letter boundary. No author asset changes were needed.'
(A/'product-si-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=['# Heo product and SI viewer independent audit','',f"**Result: {report['status']}.**",'',f"Author: `/root/peng1998_reader_assets`; independent auditor: `/root/backlog_eta`. {sum(groups.values()):,} data/binding checks and7,939 actual function checks; {len(failed)} findings.",'','The exact audited CIF and all680 average positions/872species components are retained. Three qualified final-product/diffraction/average-model bindings preserve all sample boundaries; mixed Si/Al and partial split In sites are presented as an average model, without ordered/DFT/exact-pair approval. The ADP omission and2.27ESD angle discrepancy remain explicit.','','All1,209 SI rows,7,254numeric positions,7,252resolved values,two null signs,137negative observations and one zero are preserved in JSON/TSV. Only local-path/private-wrapper fields are removed; source precision, uncertainty, markers, source/audit hashes and locators remain. Source-order filters and every exact hkl/row-ID search were executed independently.','','All seven retained author screenshots were actually viewed. They support presentation review but are not independent live browser interaction. Final integrated DOM/WebGL/browser QA remains a separate gate. No source-cell reread, geometry recomputation or publication approval is implied.','','Both author manifests, previous passed source audits, scientific inputs, all package files and independent checker files are SHA256-bound in the JSON report. Only private audit files were written.','']
text='\n'.join(md)
for old,new in [('checks and7,939','checks and 7,939'),('all680','all 680'),('872species','872 species'),('and2.27ESD','and 2.27 ESD'),('All1,209','All 1,209'),('rows,7,254numeric','rows, 7,254 numeric'),('positions,7,252resolved','positions, 7,252 resolved'),('values,two','values, two'),('signs,137negative','signs, 137 negative')]:text=text.replace(old,new)
(A/'product-si-source-audit.md').write_text(text,encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':report['check_count'],'findings':failed[:20],'finding_count':len(failed),'sha256':sha(A/'product-si-source-audit.json')},ensure_ascii=False))
