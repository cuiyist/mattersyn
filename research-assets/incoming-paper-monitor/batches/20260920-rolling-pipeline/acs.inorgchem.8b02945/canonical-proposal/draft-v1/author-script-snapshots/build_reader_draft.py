"""Private Friedfeld reader and exact fixture; no Site writes or approval."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib,re,shutil,sys
sys.dont_write_bytecode=True
C=Path(__file__).resolve().parent;F=C.parent;DRAFT=C/'draft-v1';O=DRAFT/'reader';O.mkdir(exist_ok=True)
assert not(DRAFT/'package-freeze.json').exists(),'Preserve frozen versions.'
S=Path('[local path redacted]');sys.path.insert(0,str(S/'scripts'))
import build_paper_reviews as consumer
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return re.sub('[^a-z0-9]+','-',str(x).lower()).strip('-')
def esc(x):return str(x).replace('~','~0').replace('/','~1')
def resolve(x,p):
    for z in p.strip('/').split('/')if p else[]:
        z=z.replace('~1','/').replace('~0','~');x=x[int(z)]if isinstance(x,list)else x[z]
    return x
def uniq(a):return list({json.dumps(x,sort_keys=True,ensure_ascii=False):x for x in a}.values())
def prose(x):
    x=str(x).replace('degC','°C').replace('→',' → ')
    fixes={'ChargeODE':'Charge ODE','underN2':'under N2','togl ovebox':'to glovebox','togl ove':'to glove','togl':'to gl','Table1':'Table 1','Figure1':'Figure 1','Figure2':'Figure 2','Figure3':'Figure 3','Figure4':'Figure 4','Figure5':'Figure 5','Scheme1':'Scheme 1','Scheme2':'Scheme 2','Graphicalabstract':'Graphical abstract','Labeledacid':'Labeled acid','13C NMR':'13C NMR','Gaussianfitboxes':'Gaussian fit boxes','completeanalytical':'complete analytical','citedMSC':'cited MSC','andtitle':'and title','andcompletefootnote':'and complete footnote','numericcells':'numeric cells','andTEM':'and TEM','newcoordinates':'new coordinates','citedcluster':'cited cluster','1Hfrequency':'1H frequency'}
    for a,b in fixes.items():x=x.replace(a,b)
    x=re.sub(r'\b(Variable-temperature|Full labeled MSC|Extended|within|at|after|for|above|below|from|to|near|over|return|interval|between|rate|toluene-d8|NMR|S|SI|main|initial|concentration|versus|and)(?=\d)',r'\1 ',x)
    x=re.sub(r'(?<=\d)(°C|nm|MHz|Hz|mM|mL|min|h|equiv)(?=\b)',r' \1',x)
    x=re.sub(r'\b(Scheme|Table|Figure)\s*(\d+)',r'\1 \2',x);x=re.sub(r',(?=\S)',', ',x);x=x.replace('..','.').replace('Missing details: .','Additional numerical details are not supplied.')
    return re.sub(' +',' ',x).strip()
D=read(F/'source-facts.json');I=read(F/'source-inventory.json');T=read(F/'source-tables.json');A=read(F/'original-assets-manifest.json');PC=read(F/'page-coverage.json')
CM=read(DRAFT/'record-manifest.json');CV=read(DRAFT/'source-to-field-coverage.json');OWN=read(DRAFT/'source-owner-map.json')
R={x['record_id']:read(x['path'])for x in CM['records']};SID=D['source_id'];PRE='friedfeld-2019-'
SECTIONS=[{'id':i,'title':t,'items':[]}for i,t in [('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and limitations')]]
ITEM={};OBJ={};PTR={};FIELD={};OPS={};MATS={};STOCKS={};PRODS={};UNITS={};PUBLIC=[]
def sec(rid):return OWN['section_by_record'][rid]
def evidence(es):
    out=[]
    for e in es:
        if'document_role'in e:out.append({k:e[k]for k in['source_id','document_role','pdf_page','printed_page','locator']if k in e});continue
        m=re.search(r'(MAIN|SI) PDF p\. (\d+) \(printed ([^)]+)\)',e['locator']);out.append({'source_id':SID,'document_role':m[1].lower()if m else'main','pdf_page':int(m[2])if m else None,'printed_page':m[3]if m else None,'locator':e['locator']})
    return out
def add(section,id,title,text,es=(),scope='Source context'):
    assert id not in ITEM
    x={'id':id,'title':prose(title),'text':prose(text),'source_audit_unit_ids':[],'source_fact_ids':[],'evidence':evidence(es),'facts':[],'canonical_links':[],
       'sample_scope':{'label':scope,'canonical_sample_links':[],'same_batch_verified':False},'original_assets':[],'notes':[],'reviewed':False,'training_eligible':False}
    ITEM[id]=x;next(s for s in SECTIONS if s['id']==section)['items'].append(x);return x
OVERVIEW={
 'precursors':('Cluster precursors, additives and isotope-labeled ligands','Preformed InP magic-size clusters are the conversion precursors. Myristate, phenylacetate and carbonyl-13C phenylacetate contexts remain separate. The article supplies a full labeled-phenylacetic-acid preparation, while cluster, labeled indium-carboxylate and phosphorus-precursor preparations are cited or incomplete. Stock concentrations, isotope enrichment and reaction transfers retain their own source scopes.'),
 'protocol':('Thermal cluster conversion and separate preparative procedures','The representative conversion uses a four-neck flask and in situ optical monitoring. A 20.0 mg cluster charge in 1 mL ODE is injected into 19 mL of preheated solution. This charge is not copied into changed-concentration experiments. Acid-additive, indium-additive and concentration variants retain only source-paired alternatives. The carbonyl-13C acid synthesis, ligand-exchange experiments and low-temperature pretreatment remain separate procedures.'),
 'structures':('Local structure, diffraction and domain-size analysis','TEM, local Fourier transforms and powder diffraction support source phase and morphology assignments. The 250 °C TEM specimen is described as spherical particles with a 2.6 ± 0.5 nm mean diameter from 315 particles. InP and In2O3 assignments and separated fractions do not establish pure whole-product composition. Source-calculated Scherrer domains, including conflicting fit-box and prose values, are distinct from microscopy diameters. No current QD atomic coordinates are supplied.'),
 'properties':('Optical, magnetic-resonance and thermal observations','Temperature, concentration and carboxylate perturbations are followed through optical spectra, NMR and thermal analysis. The 500 nm response and its fitted slope are optical proxies, not calibrated isolated yields. Published Gaussian maxima, kinetic regressions and thermal annotations remain literal source evidence with their original units and conflicts. Separate contexts do not establish the same physical aliquot across techniques.'),
 'intuition':('Proposed ligand exchange and cluster dissolution','The authors discuss ligand rearrangement, carboxylate-promoted dissolution and competing productive and nonproductive channels. These mechanisms and the Scheme 1 stoichiometric relation are interpretations. Cited earlier cluster structures and theoretical calculations remain attributed context; no new elementary-reaction product counts, DFT model or molecular coordinates are inferred.'),
 'sources':('Supplied documents and unresolved source statements','The frozen extraction author reviewed eight main and 25 matched SI pages and retained all 44 numbered figures, two schemes, 56 references and 51 selected original crops. Its independent source audit is still pending at this draft stage. Source numbering, pretreatment duration, ligand labels, NMR frequency, DSC rate and fit discrepancies remain explicit. This reader and its canonical records are private and unapproved.')}
for section,(title,text)in OVERVIEW.items():add(section,'overview-'+section,title,text)
for rid,r in R.items():
    it=add(sec(rid),'record-'+rid,r['title'].split(' · ',1)[-1],r['method']+'. '+('Inherited conversion variants are explicitly separated from the representative procedure.'if r['record_type']=='protocol_variant'else'Its source-defined procedure or observation scope is retained independently.'),scope=rid)
    it['canonical_links']=[{'record_id':rid,'json_pointer':'','relation':'Private canonical draft; no scientific or publication approval.'}]
    it['notes']=[prose(x)for x in r['quality']['conflicts']]

def owner(category,obj):
    oid=obj.get('id')
    if category=='facts':return PRE+OWN['fact_owner'][oid]
    if category=='materials':return PRE+'source-materials'
    if category=='stocks':return next(b['record_id']for b in CV['source_objects']if b['category']=='stock'and b['source_id']==oid)
    if category=='protocols':return PRE+('conversion-representative'if oid=='conversion-family'else oid)
    if category=='sample_contexts':return PRE+OWN['sample_owner'][oid]
    if category=='figures':return PRE+OWN['figure_owner'][oid][0]
    if category=='equations':return PRE+OWN['equation_owner'][oid]
    if category=='schemes':return PRE+'mechanistic-context'
    return PRE+'source-context'
for category in['facts','materials','stocks','protocols','sample_contexts','figures','schemes','equations','conflicts','missingness','references']:
    for j,obj in enumerate(D[category]):
        oid=obj.get('id',str(j));rid=owner(category,obj);section=sec(rid);title=obj.get('title',obj.get('name',obj.get('label',oid)));scope=obj.get('sample_scope',obj.get('label',oid));es=obj.get('evidence',[])
        if category=='facts':text=obj['claim']
        elif category=='materials':text=obj['name']+'. '+obj['scope_note'];section='precursors'
        elif category=='stocks':text=obj['name']+'. '+obj['preparation']+' '+obj['scope_note'];section='precursors'
        elif category=='protocols':text=obj['title']+'. Operations, material fractions and comparison levels remain source-scoped; missing conditions are not inferred.'
        elif category=='sample_contexts':text=obj['label']+'. '+obj['physical_batch_join']
        elif category=='figures':text=obj['title']+'. Source panel assignments: '+json.dumps(obj.get('panels',{}),ensure_ascii=False)+'. No raw curve data have been digitized.'
        elif category=='schemes':text=obj.get('description',obj.get('interpretation',obj.get('title',oid)))+'. This is the source mechanistic proposal, not a measured atomic model.'
        elif category=='equations':text=obj['raw_expression']+'. '+obj.get('interpretation','Original source fit function or mechanistic relation; no numerical recalculation.')
        elif category=='references':text=obj.get('raw_citation',obj.get('citation',json.dumps(obj,ensure_ascii=False)))+' The cited full paper is not claimed to have been supplied or newly reviewed.';section='sources'
        else:text=obj['description'];section='sources'
        it=add(section,'source-'+category+'-'+norm(oid),title,text,es,scope);OBJ[(category,oid)]=it
        if category=='facts':it['source_fact_ids']=[oid];it['claim_type']=obj['claim_class'];it['notes']=[prose(x['description'])for x in D['conflicts']if x['id']in obj['conflict_ids']]
        if category=='figures':it['source_sample_context_ids']=obj['sample_context_ids']
for p in D['protocols']:
    rid=PRE+('conversion-representative'if p['id']=='conversion-family'else p['id'])
    for op in p['operations']:
        notes=[x for x in CV['operations']if x['source_operation_id']==op['id']]
        text=op['action']+'. '+(' '.join(notes[0]['notes'])if notes else'')+' Unreported details: '+', '.join(op['missing_fields'])+'.'
        it=add(sec(rid),'operation-'+op['id'],op['action'],text,op['evidence'],p['id']);OBJ[('operation',op['id'])]=it
for t in T['tables']:
    rid=PRE+OWN['table_owner'][t['id']];es=t.get('evidence')or t['rows'][0]['cells'][0]['evidence']
    it=add(sec(rid),'table-'+t['id'],t['title'],'Every printed numeric cell, original row/column heading and source qualifier is retained. Fits and source calculations remain distinct from measured conditions.',es,t['id']);OBJ[('table',t['id'])]=it
for b in CV['source_objects']:
    category=b['category'];oid=b['source_id'];lookup=(category,oid)
    if lookup not in OBJ:
        lookup=({'material':'materials','stock':'stocks','sample_context':'sample_contexts'}.get(category,category),oid)
    it=OBJ.get(lookup,ITEM['record-'+b['record_id']]);PTR[(b['record_id'],b['pointer'])]=it
    it['canonical_links'].append({'record_id':b['record_id'],'json_pointer':b['pointer'],'relation':'Exact canonical source object or operational field.'})
for f in CV['facts']:
    it=OBJ[('facts',f['source_fact_id'])]
    for b in f['canonical_bindings']:PTR[(b['record_id'],b['pointer'])]=it
for b in CV['table_cells']:PTR[(b['record_id'],b['pointer'])]=OBJ[('table',b['table_id'])]
for u in CV['source_units']:
    original=next(x for x in I['units']if x['id']==u['source_unit_id']);its=[]
    for b in u['canonical_bindings']:
        it=PTR.get((b['record_id'],b['pointer']))
        if it is None:
            it=add('intuition'if original['kind']=='conceptual_figure'else'sources','unit-'+original['id'],original['title'],original['summary'],original['evidence']);PTR[(b['record_id'],b['pointer'])]=it
        it['source_audit_unit_ids'].append(u['source_unit_id']);its.append(it['id'])
    UNITS[u['source_unit_id']]=list(dict.fromkeys(its))
def nearest(rid,ptr):
    p=ptr
    while p:
        if(rid,p)in PTR:return PTR[(rid,p)]
        p=p.rsplit('/',1)[0]
    return ITEM['record-'+rid]
def displayed(v):
    if v['value']is not None:return v['value']
    lo,hi=v.get('minimum'),v.get('maximum')
    if lo is not None and hi is not None:return str(lo)+'–'+str(hi)
    if lo is not None:return('> 'if v.get('minimum_exclusive')else'≥ ')+str(lo)
    if hi is not None:return('< 'if v.get('maximum_exclusive')else'≤ ')+str(hi)
    return 'Not reported'
def walk(v,ptr,rid):
    if isinstance(v,dict):
        if{'value','status','evidence'}<=v.keys():
            it=nearest(rid,ptr);label=ptr.rsplit('/',1)[-1].replace('_',' ');sid=None
            if ptr.startswith('/measurements/'):
                m=resolve(R[rid],'/'.join(ptr.split('/')[:3]));label=m['property'].replace('_',' ');sid=m['sample_id']
            q={'id':rid+'::'+ptr,'label':prose(label.capitalize()),'value':displayed(v),'unit':v.get('unit'),'status':v['status'],'approximate':v.get('approximate',False),
               'qualifier':prose(' '.join(v.get(k,'')for k in['basis','qualifier','note'])),'basis':'exact_canonical_field','evidence':evidence(v['evidence']),
               'canonical_record_id':rid,'json_pointer':ptr,'canonical_quantity':deepcopy(v),'presentation_kind':'exact_quantity','training_eligible':False}
            if sid:q['sample_id']=sid
            if isinstance(v['value'],str)and v['value'].startswith('{'):
                try:q['value']=json.loads(v['value']);q['presentation_kind']='curated_source_inventory';q['basis']='exact_canonical_structured_source_payload'
                except ValueError:pass
            elif isinstance(v['value'],str):q['value']=prose(v['value']);q['basis']='exact_canonical_text_with_declared_spacing_only_display'
            it['facts'].append(q);FIELD[(rid,ptr)]=(it['id'],q);return
        for k,x in v.items():walk(x,ptr+'/'+esc(k),rid)
    elif isinstance(v,list):
        for j,x in enumerate(v):walk(x,ptr+'/'+str(j),rid)
for rid,r in R.items():
    for j,m in enumerate(r['materials']):
        it=OBJ[('materials',m['id'])];it.setdefault('material_contexts',[]).append({'record_id':rid,'json_pointer':f'/materials/{j}',**deepcopy(m),'exact_molecular_asset_binding_approved':False});PTR[(rid,f'/materials/{j}')]=it;MATS[rid+'::'+m['id']]=it['id']
    for j,st in enumerate(r['stocks']):
        it=OBJ[('stocks','msc-injection'if st['id']=='msc-injection-varied'else st['id'])];it.setdefault('stock_contexts',[]).append({'record_id':rid,'json_pointer':f'/stocks/{j}',**deepcopy(st),'molecular_bindings_approved':False});PTR[(rid,f'/stocks/{j}')]=it;STOCKS[rid+'::'+st['id']]=it['id']
    for j,op in enumerate(r['operations']):
        it=OBJ[('operation',op['id'])];it.setdefault('operation_contexts',[]).append({'record_id':rid,'json_pointer':f'/operations/{j}',**deepcopy(op),'apparatus_binding_approved':False});PTR[(rid,f'/operations/{j}')]=it;OPS[rid+'::'+op['id']]=it['id']
    for j,p in enumerate(r['products']):
        it=OBJ.get(('sample_contexts',p['sample_id']),ITEM['record-'+rid]);it.setdefault('product_contexts',[]).append({'record_id':rid,'json_pointer':f'/products/{j}',**deepcopy(p),'atomic_asset_binding_approved':False});PTR[(rid,f'/products/{j}')]=it;PRODS[rid+'::'+p['sample_id']]=it['id']
    walk(r,'',rid)
FACTS=[]
for f in CV['facts']:
    bs=[]
    for b in f['canonical_bindings']:
        iid,q=FIELD[(b['record_id'],b['pointer'])];q.setdefault('source_fact_ids',[]).append(f['source_fact_id']);bs.append({**b,'reader_item_id':iid,'reader_fact_id':q['id']})
    FACTS.append({'source_fact_id':f['source_fact_id'],'bindings':bs})
for it in ITEM.values():
    it['canonical_links']=uniq(it['canonical_links']);it['source_audit_unit_ids']=list(dict.fromkeys(it['source_audit_unit_ids']))
    for q in it['facts']:
        if q.get('sample_id'):
            j=next(j for j,p in enumerate(R[q['canonical_record_id']]['products'])if p['sample_id']==q['sample_id']);it['sample_scope']['canonical_sample_links'].append({'record_id':q['canonical_record_id'],'json_pointer':f'/products/{j}','sample_id':q['sample_id'],'relation':'Source-scoped context, not a new batch association.'})
    it['sample_scope']['canonical_sample_links']=uniq(it['sample_scope']['canonical_sample_links'])
for fig in D['figures']:
    it=OBJ[('figures',fig['id'])]
    for sid in fig['sample_context_ids']:
        rid=PRE+OWN['sample_owner'][sid];j=next(j for j,p in enumerate(R[rid]['products'])if p['sample_id']==sid)
        it['sample_scope']['canonical_sample_links'].append({'record_id':rid,'json_pointer':f'/products/{j}','sample_id':sid,'relation':'Original source panel scope; no extra physical-aliquot join.'})
GROUP={k:[]for k in['figures','tables','equations','schemes','source_notes']}
for a in A['assets']:
    assert not a['contains_complete_source_page']and sha(a['path'])==a['sha256']
    oid=a['object_id']
    if oid.startswith('figure-'):it=OBJ[('figures',oid)];group='figures'
    elif oid.startswith('scheme-'):it=OBJ[('schemes',oid)];group='schemes'
    elif oid=='table-1':it=OBJ[('table','table-1')];group='tables'
    elif oid=='acid-preparation':it=OBJ[('protocols','labeled-acid-synthesis')];group='source_notes'
    elif oid in['s38-fit-boxes','s39-fit-boxes']:it=OBJ[('table','gaussian-boxes')];group='equations'
    elif oid=='graphical-abstract':it=next(x for x in ITEM.values()if 'friedfeld2019-unit-graphical-abstract'in x['source_audit_unit_ids']);group='source_notes'
    else:raise AssertionError(oid)
    public='assets/figures/'+SID+'/'+Path(a['path']).name;samplelinks=[]
    for sid in a['sample_context_ids']:
        rid=PRE+OWN['sample_owner'][sid];j=next(j for j,p in enumerate(R[rid]['products'])if p['sample_id']==sid);samplelinks.append({'record_id':rid,'json_pointer':f'/products/{j}','sample_id':sid})
    out={'id':a['id'],'label':prose(a['title']),'caption_paraphrase':it['text'],'document_role':a['document_role'],'page':a['pdf_page'],'printed_page':a['printed_page'],
         'sample_scope':{'label':' / '.join(a['sample_context_ids']),'canonical_sample_links':samplelinks,'same_batch_verified':False},'sample_links':sorted({x['record_id']for x in samplelinks}),
         'sample_linkage':'Original source-assigned context only; no exact sample-to-recipe or coordinate claim.',
         'public_asset':public,'public_asset_sha256':a['sha256'],'asset_provenance':{'source_sha256':a['source_sha256'],'source_pdf_page':a['pdf_page'],'crop_normalized':a['crop_box_normalized'],'source_render_dpi':a['render_dpi'],'renderer':a['renderer'],'pixel_dimensions':a['pixel_dimensions'],'transformation':'Selected original crop, no full source page or scientific reconstruction.'},
         'source_locators':[e['locator']for e in a['evidence']],'notes':it['notes'],'reader_render_verified':False,'reviewed':False,'training_eligible':False}
    if oid=='table-1':out['source_rows']=deepcopy(next(t['rows']for t in T['tables']if t['id']=='table-1'))
    GROUP[group].append(out);it['original_assets'].append({'id':a['id'],'label':'Open original '+prose(a['title']),'public_asset':public,'public_asset_sha256':a['sha256']})
    PUBLIC.append({'id':a['id'],'private_path':a['path'],'public_asset':public,'sha256':a['sha256'],'selected_original_only':True,'publication_approved':False})
docs=[]
for role in['main','si']:
    pp=[p for p in PC['pages']if p['document_role']==role]
    docs.append({'role':role,'filename':'10.1021_acs.inorgchem.8b02945'+('_si_1'if role=='si'else'')+'.pdf',
        'sha256':next(a['source_sha256']for a in A['assets']if a['document_role']==role),'page_count':len(pp),
        'pages':[{'page':p['pdf_page'],'printed_page':802+p['pdf_page']if role=='main'else p['pdf_page'],'text_read':p['text_read'],'visual_review':p['visual_review'],'review_basis':'Frozen extraction author page coverage; distinct source audit pending.','sections':[p['actual_reading_scope']]}for p in pp]})
routes={rid:[r for r in R if r!=rid and R[r]['record_type']=='observation']for rid in R if R[rid]['record_type']in['literature_protocol','protocol_variant']}
counts={'reader_items':len(ITEM),'typed_reader_fields':len(FIELD),'canonical_records':len(R),'source_units':len(UNITS),'source_facts':len(FACTS),'table_numeric_cells':len(CV['table_cells']),
    'operation_instances':len(OPS),'source_operations':34,'material_slots':len(MATS),'stock_slots':len(STOCKS),'sample_context_slots':len(PRODS),'measurements':sum(len(r['measurements'])for r in R.values()),'selected_original_assets':len(PUBLIC),'main_pages':8,'si_pages':25,'full_page_public_assets':0,'training_tasks':0}
rv={'schema_version':'1.0','paper_id':SID,'doi':D['doi'],'title':D['title'],'paper':{'authors':D['authors'],'year':D['year'],'journal':'Inorganic Chemistry','volume':58,'pages':'803–810'},'source_group':SID,
    'review_scope':'supplied_main_and_matched_si','documents':docs,'supporting_information':{'status':'matched_local_author_reading_complete_independent_audit_pending','matched_local_si_count':1,'pdf_pages':25,'scope':'All supplied SI figures through S39 and source numerical listings; no current QD coordinates or raw curve files.'},
    'coverage_status':'private_author_reader_draft','independent_audit':'Pending separate source and canonical/reader review.','publication_status':'Private unapproved draft','source_review_promoted':False,'training_eligible':False,
    'recipe_inventory':[{'id':rid,'label':r['title'],'record_ids':[rid],'record_type':r['record_type'],'status':'private_author_draft_pending_independent_review','scope':'One coherent procedure, variant or context; not an independently identified physical batch.','gaps':r['quality']['missing_fields']}for rid,r in R.items()],
    'characterization_inventory':{'reader_item_ids':[i['id']for s in SECTIONS if s['id']in['structures','properties']for i in s['items']]},'chemical_intuition':{'reader_item_ids':[i['id']for s in SECTIONS if s['id']=='intuition'for i in s['items']]},
    'reader_contract':{'version':'1.0','section_ids':[s['id']for s in SECTIONS]},'reader_sections':SECTIONS,**GROUP,
    'remaining_gaps':[prose(g['description'])for g in D['missingness']],'evidence_conflicts':deepcopy(D['conflicts']),'route_evidence_contexts':routes,
    'route_evidence_scope_notes':{'all':'Linked records provide separate comparative context, not exact observations for every route.','concentration':'Representative injection quantities are excluded from changed-concentration stock amounts.','structure':'No current QD atomic coordinates or measured exact recipe pair.','pretreatment':'The 30/72 h and ligand-label discrepancies prevent automatic physical sample joins.'},
    'presentation_gates':{'molecules':False,'apparatus':False,'products':False,'browser_render':False,'publication':False},'counts':counts}
save(SID+'.json',rv)
save('reader-bindings-proposal.json',{'status':'private_unapproved_draft','source_id':SID,'reader_sha256':sha(O/(SID+'.json')),'original_assets':PUBLIC,'operation_to_reader_item':OPS,'material_to_reader_item':MATS,'stock_to_reader_item':STOCKS,'product_to_reader_item':PRODS,'binding_approved':False})
save('source-item-coverage.json',{'source_units':UNITS,'source_facts':FACTS,'table_cells':[{**b,'reader_item_id':FIELD[(b['record_id'],b['pointer'])][0],'reader_fact_id':FIELD[(b['record_id'],b['pointer'])][1]['id']}for b in CV['table_cells']],
    'canonical_field_map':[{'record_id':rid,'json_pointer':ptr,'reader_item_id':iid,'reader_fact_id':q['id']}for(rid,ptr),(iid,q)in FIELD.items()]})
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
for(rid,ptr),(iid,q)in FIELD.items():ck(rid+ptr+' exact canonical field',resolve(R[rid],ptr)==q['canonical_quantity'])
for it in ITEM.values():
    for b in it['canonical_links']:ck(it['id']+' canonical link',resolve(R[b['record_id']],b['json_pointer'])is not None)
    for b in it['sample_scope']['canonical_sample_links']:ck(it['id']+' sample link',resolve(R[b['record_id']],b['json_pointer'])['sample_id']==b['sample_id'])
for rid,links in routes.items():ck(rid+' route context IDs',isinstance(links,list)and all(isinstance(i,str)and i in R for i in links))
ck('all 51 selected assets',len(PUBLIC)==51)
ck('all source units mapped',set(UNITS)=={u['id']for u in I['units']})
fixture=DRAFT/'isolated-reader-fixture';(fixture/'data/records').mkdir(parents=True,exist_ok=True);(fixture/'dist').mkdir(exist_ok=True)
for r in CM['records']:shutil.copyfile(r['path'],fixture/'data/records'/Path(r['path']).name)
for a in PUBLIC:
    dest=fixture/'dist'/a['public_asset'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a['private_path'],dest);ck(a['id']+' exact crop copy',sha(dest)==a['sha256'])
old=consumer.ROOT
try:consumer.ROOT=fixture;errors=consumer.validate(rv)
finally:consumer.ROOT=old
ck('actual current reader consumer fixture',not errors)
save('reader-author-validation.json',{'status':'passed_author_transport_checks_only','checks':checks,'count':len(checks),'actual_reader_consumer_errors':errors,'fixture':str(fixture),
    'scientific_audit':False,'actual_browser':False,'publication_approved':False,'counts':counts,'consumer_sha256':sha(S/'scripts/build_paper_reviews.py')})
print(json.dumps({'status':'reader_draft_valid','items':len(ITEM),'fields':len(FIELD),'assets':len(PUBLIC),'checks':len(checks),'reader_sha256':sha(O/(SID+'.json'))}))
