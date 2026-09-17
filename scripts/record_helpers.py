"""Authoring helpers; all supplied scientific values must have source evidence."""
from copy import deepcopy
def ev(source,locator):return [{'source_id':source,'locator':locator}]
def fact(value=None,evidence=None,status=None,note=''):
    return {'value':value,'status':status or ('reported' if value is not None else 'not_reported'),'evidence':evidence or [],'note':note}
def qty(value=None,unit='',evidence=None,status=None,minimum=None,maximum=None,approximate=False,qualifier='',basis='',raw_text='',derivation=None):
    known=value is not None or minimum is not None
    return dict(value=value,minimum=minimum,maximum=maximum,unit=unit,status=status or ('reported' if known else 'not_reported'),approximate=approximate,qualifier=qualifier,basis=basis,raw_text=raw_text,evidence=evidence or [],derivation=derivation)
def source(id,doi,title,authors,year,si='Not located or verified'):
    return dict(id=id,doi=doi,title=title,authors=authors,year=year,url='https://doi.org/'+doi,main_status='Relevant original text reviewed',si_status=si,reuse_status='Bibliographic and factual extraction; original article/figure rights remain separate')
def record(id,title,formula,family,method,src,loc,kind='literature_protocol'):
    e=ev(src['id'],loc)
    return dict(schema_version='1.0.0',record_id=id,revision=1,record_type=kind,title=title,material={'formula':formula,'family':family},method=method,sources=[src],lineage={'source_group':src['id'],'recipe_family':src['id']+'-'+formula.lower(),'parent_record_id':None,'batch_id':None,'duplicate_of':None},intended_target={'composition':fact(formula,e),'phase':fact(evidence=e),'size':qty(unit='nm',evidence=e),'morphology':fact(evidence=e)},materials=[],stocks=[],material_states=[],operations=[],condition_options=[],products=[],measurements=[],structure_assets=[],quality={'review_status':'source_reviewed','review_scope':'Source extraction reviewed for this named literature protocol; not an independent laboratory reproduction. IDs identify records, not author-assigned physical batches.','missing_fields':[],'conflicts':[],'requested_tasks':['precursor_selection','partial_protocol','size_conditioned_recipe','exact_structure_recipe'],'experimental_outcome':'not_established'},context_links=[])
def material(id,name,formula,role,stage,evidence,quantities=None,notes=None,cid=None,smiles=None):
    return dict(id=id,name=name,formula=formula,role=role,stage=stage,identity={'pubchem_cid':cid,'smiles':smiles},quantities=quantities or {},notes=notes or [],evidence=evidence)
def operation(id,action,label,evidence,inputs,outputs,depends=None,parameters=None,stage='synthesis',branch='main',optional=False,description='',environment=None,endpoint=None,retained_fraction=None):
    return dict(id=id,action=action,label=label,stage=stage,branch=branch,optional=optional,depends_on=depends or [],inputs=inputs,outputs=outputs,parameters=parameters or {},environment=environment or fact(evidence=evidence),endpoint=endpoint or fact(evidence=evidence),retained_fraction=retained_fraction,description=description,evidence=evidence)
def product(id,formula,evidence,link='unresolved',state=None,phase=None,surface=None,notes=None):
    return dict(sample_id=id,source_sample_label=None,batch_id=None,material_state_id=state,parent_sample_id=None,composition=fact(formula,evidence),phase=fact(phase,evidence),morphology=fact(evidence=evidence),surface=fact(surface,evidence),recipe_link=link,link_evidence=evidence if link=='explicit' else [],notes=notes or [])
def state(id,name,parents=None,kind='mixture'):return {'id':id,'name':name,'kind':kind,'parent_ids':parents or []}
def measurement(id,sample,prop,value,technique,evidence,conditions='',derives=None):
    return dict(id=id,sample_id=sample,property=prop,technique=technique,value=value,conditions=conditions,derives_from=derives or [],evidence=evidence)
