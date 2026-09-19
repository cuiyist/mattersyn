"""Single definition of the exported MatterSyn record schema (Draft 2020-12)."""
def obj(properties, required=None):
    return {'type':'object','properties':properties,'required':required or list(properties),'additionalProperties':False}
def arr(item): return {'type':'array','items':item}
def ref(name): return {'$ref':'#/$defs/'+name}
string={'type':'string'}
nullable_string={'type':['string','null']}
number={'type':['number','null']}
strings=arr(string)
statuses=['reported','author_derived','calculated','inherited','inferred','not_reported','not_applicable']
evidence=obj({'source_id':string,'locator':string})
fact=obj({'value':{'type':['string','number','boolean','null']},'status':{'enum':statuses},'evidence':arr(evidence),'note':string})
quantity=obj({'value':number,'minimum':number,'maximum':number,'unit':string,'status':{'enum':statuses},'approximate':{'type':'boolean'},'qualifier':string,'basis':string,'raw_text':string,'evidence':arr(evidence),'derivation':nullable_string})
source=obj({'id':string,'doi':nullable_string,'title':string,'authors':string,'year':{'type':['integer','null']},'url':string,'main_status':string,'si_status':string,'reuse_status':string})
material=obj({'id':string,'name':string,'formula':nullable_string,'role':string,'stage':string,'identity':obj({'pubchem_cid':{'type':['integer','null']},'smiles':nullable_string}), 'quantities':{'type':'object','additionalProperties':ref('quantity')},'notes':strings,'evidence':arr(evidence)})
component=obj({'material_id':string,'quantities':{'type':'object','additionalProperties':ref('quantity')}})
stock=obj({'id':string,'name':string,'components':arr(component),'concentrations':{'type':'object','additionalProperties':ref('quantity')},'preparation_operation_ids':strings,'scope':string,'evidence':arr(evidence)})
state=obj({'id':string,'name':string,'kind':{'enum':['stock','mixture','reaction_batch','aliquot','fraction','product','waste']},'parent_ids':strings})
operation=obj({'id':string,'action':string,'label':string,'stage':{'enum':['precursor_preparation','storage','synthesis','workup','fractionation','surface_exchange','characterization']},'branch':string,'optional':{'type':'boolean'},'depends_on':strings,'inputs':strings,'outputs':strings,'parameters':{'type':'object','additionalProperties':ref('quantity')},'environment':ref('fact'),'endpoint':ref('fact'),'retained_fraction':nullable_string,'description':string,'evidence':arr(evidence)})
operation['properties']['optional_inputs']=strings
product=obj({'sample_id':string,'source_sample_label':nullable_string,'batch_id':nullable_string,'material_state_id':nullable_string,'parent_sample_id':nullable_string,'composition':ref('fact'),'phase':ref('fact'),'morphology':ref('fact'),'surface':ref('fact'),'recipe_link':{'enum':['explicit','general_context','unresolved']},'link_evidence':arr(evidence),'notes':strings})
measurement=obj({'id':string,'sample_id':string,'property':string,'technique':string,'value':{'oneOf':[ref('quantity'),ref('fact')]},'conditions':string,'derives_from':strings,'evidence':arr(evidence)})
structure=obj({'id':string,'role':{'enum':['measured_sample','external_reference','computed_reference','illustrative']},'sample_id':nullable_string,'url':string,'description':string,'eligible_as_measured_label':{'type':'boolean'}})
quality=obj({'review_status':{'enum':['source_reviewed','structured_data_verified','metadata_only','imported_unreviewed']},'review_scope':string,'missing_fields':strings,'conflicts':strings,'requested_tasks':strings,'experimental_outcome':{'enum':['reported_product','reported_failure','reported_partial','not_established']}})
record=obj({'schema_version':{'const':'1.0.0'},'record_id':{'type':'string','pattern':'^[a-z0-9][a-z0-9-]+$'},'revision':{'type':'integer','minimum':1},'record_type':{'enum':['literature_protocol','protocol_variant','procedure','experiment','observation']},'title':string,'material':obj({'formula':string,'family':string}),'method':string,'sources':arr(source),'lineage':obj({'source_group':string,'recipe_family':string,'parent_record_id':nullable_string,'batch_id':nullable_string,'duplicate_of':nullable_string}),'intended_target':obj({'composition':ref('fact'),'phase':ref('fact'),'size':ref('quantity'),'morphology':ref('fact')}),'materials':arr(material),'stocks':arr(stock),'material_states':arr(state),'operations':arr(operation),'condition_options':arr(obj({'id':string,'label':string,'parameters':{'type':'object','additionalProperties':ref('quantity')},'evidence':arr(evidence)})),'products':arr(product),'measurements':arr(measurement),'structure_assets':arr(structure),'quality':ref('quality'),'context_links':arr(obj({'label':string,'url':string,'relation':string}))})
record['properties']['schema_version']={'enum':['1.0.0','1.1.0']}
record['properties']['intended_target']['properties']['surface']=ref('fact')
record['properties']['collection']={'enum':['reviewed_literature','published_benchmark']}
record['properties']['material']['properties']['elements']=strings
record['properties']['material']['properties']['components']=strings
record['properties']['material']['properties']['architecture']={'enum':['single_material','core_shell','heterostructure','alloy','composite','unresolved']}
SCHEMA={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'https://mattersyn-recipe-atlas.cuiy781513.chatgpt.site/data/record.schema.json','title':'MatterSyn source-linked synthesis record',**record,'$defs':{'quantity':quantity,'fact':fact,'quality':quality}}
