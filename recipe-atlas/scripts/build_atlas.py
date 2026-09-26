"""Aggregate source-level reader hubs; never promote indexed papers to training records."""
import json,re,hashlib
from pathlib import Path
from review_scope import source_review_scope
ROOT=Path(__file__).resolve().parents[1]
SYMBOLS=set('H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og'.split())
NAMES={'CdSe/ZnS':'Cadmium selenide / zinc sulfide core/shell','ZnS':'Zinc sulfide · shell-component context','CdSe/ZnSe':'Cadmium selenide / zinc selenide · coated dots and composite films','Si/SiOx':'Surface-oxidized silicon nanocrystal colloids','Si':'Silicon · cores and substrates','Ge/Si':'Germanium quantum dots on silicon','Ge':'Germanium in supported quantum-dot arrays','SiOx':'Silicon oxide surface layer · stoichiometry unresolved','CdSe':'Cadmium selenide','CdS':'Cadmium sulfide','CoFe2O4':'Cobalt ferrite','CoO':'Cobalt(II) oxide','CoO/CoFe2O4':'Cobalt oxide / cobalt ferrite core–shell','ZnO':'Zinc oxide','InP':'Indium phosphide','CsPbBr3':'Caesium lead bromide','PbS':'Lead sulfide','CdSe/CdS':'Cadmium selenide / cadmium sulfide core/shell','Ir':'Iridium','Fe–O':'Iron oxide · phase and stoichiometry unresolved','Fe3O4':'Magnetite','Fe2O3':'Iron(III) oxide'}
NAMES['InAs']='Indium arsenide'
NAMES['Ag/Si']='Silver nanocrystals on silicon'
NAMES['Ag']='Silver nanocrystals'
NAMES['Pt']='Platinum nanocrystals'
NAMES['PbSe']='Lead selenide nanocrystals and assemblies'
NAMES['FePt/CdS']='Iron–platinum / cadmium sulfide heterodimers'
NAMES['FePt']='Iron–platinum · heterodimer-component context'
NAMES['In66Si100Al92O384']='Indium nanoclusters in zeolite X · nominal In66-X'
NAMES['In']='Indium · zeolite-hosted nanocluster component'
NAMES['SnO2']='Tin dioxide colloids'
NAMES['Mn:ZnO']='Manganese-doped zinc oxide nanocrystals and films'
NAMES['ZnO:Co']='Cobalt-doped zinc oxide quantum dots'
NAMES['ZnO:Ni']='Nickel-doped zinc oxide quantum dots'
NAMES['CdTe/MWNT']='Cadmium telluride quantum dots on multiwalled carbon nanotubes'
NAMES['CdTe']='Cadmium telluride · heterostructure-component context'
NAMES['MWNT']='Multiwalled carbon nanotubes · host-component context'
# Source-reviewed acronym: a carbon nanotube host, not an elemental formula.
COMPONENT_ELEMENTS={'MWNT':['C'],'FAPbI3':['C','H','N','Pb','I'],'SiOx':['Si','O']}
NAMES['FAPbI3']='Formamidinium lead iodide quantum dots'
NAMES['La2(MoO4)3:Yb,Er']='Ytterbium/erbium-codoped lanthanum molybdate'
NAMES['PbS/glass']='PbS quantum dots in multicomponent oxide glass'
NAMES['CdS/SiO2']='CdS nanocrystals in mesoporous silica'
NAMES['SiO2']='Mesoporous silica films'
NAMES['CdS/HgS/CdS']='CdS/HgS quantum-dot quantum wells'
NAMES['HgS']='Mercury sulfide · quantum-well component'
NAMES['CdSe/ZnS/siloxane']='Siloxane-coated CdSe/ZnS quantum dots'
NAMES['CdS/polymer']='Cadmium sulfide nanocrystals in chelate polymer microparticles'
NAMES['CoNi2S4']='Cobalt–nickel thiospinel nanocrystals'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
def slug(f):return re.sub('[^a-z0-9]+','-',f.lower()).strip('-')+'-'+hashlib.sha256(f.encode()).hexdigest()[:6]
def synthesis_route(r):
    role=r.get('reader_role')
    return (r['collection']=='reviewed_literature' and r['record_type'] in {'literature_protocol','protocol_variant','experiment'}
            and r['quality']['review_status']=='source_reviewed'
            and (role=='synthesis_route' or (role is None and 'precursor_selection' in r['quality']['requested_tasks']))
            and any(o['stage']=='synthesis' for o in r['operations']))

def material_elements(r):
    formula=r['material']['formula']
    elements=r['material'].get('elements') or COMPONENT_ELEMENTS.get(formula,re.findall('[A-Z][a-z]?',formula))
    if synthesis_route(r) and (not elements or not set(elements)<=SYMBOLS):
        raise ValueError(f"Reviewed synthesis route {r['record_id']} needs an explicit valid element list for material {formula!r}; it must not disappear from the atlas.")
    return elements

def component_contribution_role(architecture):
    if architecture=='phase_mixture':return 'component_of_phase_mixture'
    if architecture in ('core_shell','heterostructure'):return 'component_of_heterostructure'
    return 'component_of_product_system'

def component_scope_note(architectures):
    architectures=set(architectures or [])
    if 'phase_mixture' in architectures:
        if architectures=={'phase_mixture'}:
            return 'This material is a source-reported phase component in source-defined phase mixtures below. The phase-mixture association does not establish a within-particle heterostructure; these are not standalone pure-material syntheses.'
        return 'This material is a component of source-reviewed product systems below. Phase-mixture links identify co-reported phases and do not establish a within-particle heterostructure; these are not standalone pure-material syntheses.'
    if architectures and architectures <= {'core_shell','heterostructure'}:
        return 'This material is a component of the explicitly named heterostructures below; these are not standalone pure-material syntheses.'
    return 'This material is a component of the source-defined product systems below; these are not standalone pure-material syntheses. Component membership alone does not establish a within-particle arrangement.'
def main():
    source=ROOT/'data/corpus/library-source.json'
    corpus=read(source) if source.exists() else {'summary':{},'papers':[]}
    records=[read(p) for p in sorted((ROOT/'data/records').glob('*.json'))]
    full_reviews={c['doi'].lower():c for c in [read(p) for p in (ROOT/'data/paper-reviews').glob('*.json')]}
    papers={p['doi'].lower():p for p in corpus['papers'] if p.get('doi') and p['coverage']['localDocumentCount']>0}
    materials={}
    def ensure(formula,elements):
        if not elements or not set(elements)<=SYMBOLS:return None
        if formula not in materials:materials[formula]={'id':slug(formula),'formula':formula,'name':NAMES.get(formula,formula+' literature collection'),'elements':list(dict.fromkeys(elements)),'url':'cdse.html' if formula=='CdSe' else 'material.html?id='+slug(formula),'record_ids':set(),'direct_record_ids':set(),'paper_dois':set(),'mentioned_paper_dois':set(),'architectures':set(),'component_architectures':set()}
        return materials[formula]
    for r in records:
        f=r['material']['formula'];els=material_elements(r)
        primary=next(s for s in r['sources'] if s['id']==r['lineage']['source_group']);doi=primary['doi'].lower()
        if doi not in papers:papers[doi]={'id':'paper-'+hashlib.sha256(doi.encode()).hexdigest()[:20],'doi':doi,'doiUrl':primary['url'],'title':primary['title'],'year':primary['year'],'documentIds':[],'coverage':{'localDocumentCount':None,'mainDocumentAvailable':True,'supportingDocumentAvailable':None,'extractionStatusCounts':{}},'materialTitleMentions':[],'titleComponentSystems':[]}
        papers[doi]['title']=primary['title'];papers[doi]['year']=primary['year'];papers[doi]['titleVerifiedFromSelectedRecord']=True
        papers[doi].setdefault('reviewedRecordIds',[])
        if r['collection']=='reviewed_literature':papers[doi]['reviewedRecordIds'].append(r['record_id'])
        papers[doi].setdefault('benchmarkRecordIds',[])
        if r['collection']=='published_benchmark':papers[doi]['benchmarkRecordIds'].append(r['record_id'])
        if not synthesis_route(r):continue
        m=ensure(f,els)
        if m is None:continue
        m['record_ids'].add(r['record_id']);m['direct_record_ids'].add(r['record_id']);m['architectures'].add(r['material'].get('architecture','single_material'));m['paper_dois'].add(doi)
        for component in r['material'].get('components',[f]):
            c=ensure(component,COMPONENT_ELEMENTS.get(component,re.findall('[A-Z][a-z]?',component)))
            if c:
                c['record_ids'].add(r['record_id']);c['paper_dois'].add(doi)
                if component != f:c['component_architectures'].add(r['material'].get('architecture','single_material'))
    # Title matches remain library search metadata. They cannot create material
    # pages or attach a paper to a synthesis contribution.
    byid={r['record_id']:r for r in records};library=[]
    for doi,p in papers.items():
        p['reviewedRecordIds']=list(dict.fromkeys(p.get('reviewedRecordIds',[])));p['benchmarkRecordIds']=list(dict.fromkeys(p.get('benchmarkRecordIds',[])))
        p['reviewStatus']='selected_recipes_reviewed' if p['reviewedRecordIds'] else 'published_benchmark' if p['benchmarkRecordIds'] else 'indexed_awaiting_review'
        review=full_reviews.get(doi)
        p['fullDocumentReview']=None
        if review:
            scope=source_review_scope(review)
            p['reviewStatus']=scope['review_status']
            p['fullDocumentReview']={'id':review['paper_id'],'url':'paper-review.html?id='+review['paper_id'],'scope':scope['scope'],'label':scope['label'],'si_status':scope['si_status'],'pages':sum(d['page_count'] for d in review['documents']),'figures':len(review['figures']),'independent_audit':review.get('independent_audit','pending')}
        p['materials']=sorted({f for f,m in materials.items() if doi in m['paper_dois']})
        # Preserve the automatic indexing result as historical scope metadata;
        # current review and contribution statuses follow the reviewed records.
        p['indexingStageStatus']={k:p[k] for k in ['recipeCurationStatus','materialContributionStatus'] if k in p}
        p['recipeCurationStatus']='source_reviewed_records' if p['reviewedRecordIds'] else 'published_benchmark' if p['benchmarkRecordIds'] else 'not_curated_by_this_pipeline'
        p['materialContributionStatus']='verified_synthesis_contribution' if p['materials'] and p['reviewedRecordIds'] else 'no_verified_synthesis_contribution'
        p['candidateMaterialMentions']=sorted({x['formula'] for x in p.get('materialTitleMentions',[])})
        write(ROOT/'dist/data/papers'/(p['id']+'.json'),p)
        library.append({k:p.get(k) for k in ['id','doi','doiUrl','title','year','coverage','materials','candidateMaterialMentions','reviewStatus','reviewedRecordIds','benchmarkRecordIds','titleMetadata','fullDocumentReview']})
    index=[]
    for f,m in materials.items():
        def reader_order(rid):
            rec=byid[rid];review=full_reviews.get(rec['sources'][0]['doi'].lower(),{})
            ordered=[x for item in review.get('recipe_inventory',[]) for x in item.get('record_ids',[])]
            return (rid not in m['direct_record_ids'],rec['sources'][0].get('year') or 9999,ordered.index(rid) if rid in ordered else 9999,rid)
        related=[byid[x] for x in sorted(m['record_ids'],key=reader_order)];m['record_ids']=sorted(m['record_ids']);m['direct_record_ids']=sorted(m['direct_record_ids']);m['architectures']=sorted(m['architectures']);m['component_architectures']=sorted(m['component_architectures'])
        m['reviewed_records']=sum(synthesis_route(r) for r in related)
        m['publication_status']='verified_synthesis_contribution'
        m['component_only']=not bool(m['direct_record_ids'])
        m['scope_note']=component_scope_note(m['component_architectures']) if m['component_only'] else 'Each method is supported by a source-reviewed synthesis record. Unreviewed title matches are excluded from this page.'
        if f == 'CoFe2O4' and not m['component_only']:
            m['scope_note']='This page combines direct standalone CoFe2O4 Method-A routes with a separately scoped CoFe2O4 shell contribution in the CoO/CoFe2O4 composite. Shell structure and property observations remain attached to that composite sample and are not relabeled as results for the standalone nanocrystals.'
        m['benchmark_records']=sum(r['collection']=='published_benchmark' for r in related);m['paper_count']=len(m['paper_dois'])
        m['papers']=[]
        for p in library:
            if p['doi'] not in m['paper_dois']:continue
            contribution=dict(p)
            contribution['reviewedRecordIds']=[rid for rid in p['reviewedRecordIds'] if rid in m['record_ids']]
            contribution['benchmarkRecordIds']=[rid for rid in p['benchmarkRecordIds'] if rid in m['record_ids']]
            contribution['reviewStatus']=p['reviewStatus'] if p['fullDocumentReview'] else 'selected_recipes_reviewed' if contribution['reviewedRecordIds'] else 'published_benchmark' if contribution['benchmarkRecordIds'] else 'indexed_awaiting_review'
            m['papers'].append(contribution)
        m['records']=[{'record_id':r['record_id'],'title':r['title'],'formula':r['material']['formula'],'method':r['method'],'record_type':r['record_type'],'is_synthesis_route':synthesis_route(r),'collection':r['collection'],'doi':r['sources'][0]['doi'],'year':r['sources'][0]['year'],'page_url':'records/'+r['record_id']+'.html','architecture':r['material'].get('architecture','single_material'),'contribution_role':'direct_material' if r['record_id'] in m['direct_record_ids'] else component_contribution_role(r['material'].get('architecture','single_material'))} for r in related]
        # Supporting evidence is explicitly curated per material, never inferred
        # from a paper title or promoted into a synthesis route.
        evidence_ids=set(m['record_ids']);m['evidence_scope_notes']=[]
        for doi in sorted(m['paper_dois']):
            review=full_reviews.get(doi,{})
            for rid in review.get('material_evidence_records',{}).get(f,[]):
                assert rid in byid, f'Unknown material evidence record: {rid}'
                record=byid[rid]
                assert record['quality']['review_status']=='source_reviewed'
                assert any(s['doi'].lower()==doi for s in record['sources'])
                evidence_ids.add(rid)
            note=review.get('material_evidence_scope_notes',{}).get(f)
            if note:m['evidence_scope_notes'].append(note)
        m['evidence_records']=[{'record_id':rid,'record_type':byid[rid]['record_type'],'collection':byid[rid]['collection']} for rid in sorted(evidence_ids)]
        m['paper_dois']=sorted(m['paper_dois']);m['mentioned_paper_dois']=sorted(m['mentioned_paper_dois'])
        write(ROOT/'dist/data/materials'/(m['id']+'.json'),m)
        index.append({k:m[k] for k in ['id','formula','name','elements','url','reviewed_records','benchmark_records','paper_count','architectures','component_architectures','publication_status','component_only']})
    summary=corpus['summary'];coverage=f"{len(index)} material pages with verified synthesis contributions. {len(library):,} indexed paper groups remain searchable separately in the Source library; indexing does not create a material page."
    write(ROOT/'dist/data/materials-index.json',{'schema_version':'1.0','materials':index,'coverage':coverage})
    write(ROOT/'dist/data/library-index.json',{'summary':summary,'papers':library,'local_paper_groups':len(library),'scope':'Paper and supplement matching and material mentions are candidates until independently reviewed. Selected reviewed recipes do not imply full-paper curation.'})
    # Remove obsolete generated shards after the complete replacement registry exists.
    for folder,valid in [('materials',{m['id'] for m in index}),('papers',{p['id'] for p in library})]:
        directory=(ROOT/'dist/data'/folder).resolve()
        assert directory.is_relative_to((ROOT/'dist/data').resolve())
        for path in directory.glob('*.json'):
            if path.stem not in valid:path.unlink()
    print(f'Built {len(index)} material hubs and {len(library)} local paper records; training records remain independently gated.')
if __name__=='__main__':main()
