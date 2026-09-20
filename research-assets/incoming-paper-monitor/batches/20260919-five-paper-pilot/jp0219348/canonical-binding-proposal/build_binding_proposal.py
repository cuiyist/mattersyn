"""Author-only external viewer bindings. Never writes source/canonical/Site files."""
from pathlib import Path
import copy, hashlib, json, re, subprocess

OUT = Path(__file__).resolve().parent
H = OUT.parent
V = H / 'canonical-proposal/v1'
M = H / 'visuals/molecules'
S = H.parents[4] / 'recipe-atlas'
EXPECTED_MOLECULE_FREEZE = '19df5b4c42d6ae463ccff131d41f08f05b4b68302cef7997ac61e3795ef5edf3'
EXPECTED_CANONICAL_FREEZE = 'bdf431a74cb75e08e3dfac9a630c90ded580aad0bb9dd0fc2c4e1669a105c948'
checks = []

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def put(name, data):
    (OUT/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def check(ok, label):
    checks.append({'check': label, 'passed': bool(ok)})
    if not ok: raise AssertionError(label)
def pointer(d, ptr):
    for token in ptr.strip('/').split('/') if ptr else []:
        token=token.replace('~1','/').replace('~0','~')
        d=d[int(token)] if isinstance(d,list) else d[token]
    return d
def formula(s):
    if s is None: return None
    tokens=re.findall(r'([A-Z][a-z]?)(\d*)',s)
    check(''.join(a+b for a,b in tokens)==s, 'Formula parser consumed '+s)
    result={}
    for a,b in tokens: result[a]=result.get(a,0)+int(b or 1)
    return result
def file_link(p, ptr='', payload=None):
    result={'file':str(p.relative_to(H)).replace('\\','/'),'sha256':sha(p),'json_pointer':ptr}
    if payload is not None: result['payload']=copy.deepcopy(payload)
    return result

def main():
    if (OUT/'package-manifest.json').exists():
        raise RuntimeError('Frozen proposal exists; preserve it and author a new revision instead.')
    before={str(p.relative_to(H)).replace('\\','/'):sha(p) for root in (V,M) for p in root.rglob('*') if p.is_file()}
    check(sha(M/'package-freeze.json')==EXPECTED_MOLECULE_FREEZE,'Expected molecule freeze')
    check(sha(V/'proposal-package-manifest.json')==EXPECTED_CANONICAL_FREEZE,'Expected canonical v1 freeze')
    mf=read(M/'package-freeze.json')
    for section in ('bound_files','bound_source_and_baseline_inputs'):
        for p,digest in mf[section].items(): check(sha(p)==digest,'Molecular frozen input '+str(p))
    cm=read(V/'canonical-record-manifest.json')
    records={p.stem:read(p) for p in sorted((V/'canonical-drafts').glob('*.json'))}
    for rid,digest in cm['record_hashes'].items(): check(sha(V/'canonical-drafts'/f'{rid}.json')==digest,'Canonical record '+rid)
    inv=read(H/'source-inventory.json'); facts=read(H/'source-facts.json')
    inventory={x['id']:(i,x) for i,x in enumerate(inv['materials'])}
    fact_index={x['id']:(i,x) for i,x in enumerate(facts['facts'])}
    plan=read(M/'molecule-binding-plan.json')
    planned={x['source_material_id']:x for x in plan['slots']}
    registry={}
    for rel,base in [('registry-additions.json',M),('reused-references.json',M/'reference-base')]:
        for i,e in enumerate(read(M/rel)['entries']):
            registry[e['id']]={'entry':e,'source':file_link(M/rel,f'/entries/{i}'),'base':base}
    fact_ids={
      'na-x':['parent-host','host-shape','host-size'], 'tl-acetate':['exchange-reagent'],
      'feed-water':['exchange-reagent','exchange-stock','exchange-ph'],
      'wash-water':['wash','wash-time','wash-volume'], 'in-metal':['indium-metal'],
      'h2s':['h2s-reagent','h2s-pressure','h2s-t','h2s-time'], 'pyrex':['capillary'],
      'final-crystal':['product-formula','seal'], 'parent-reference':['washed-parent'],
      'indium-reference':['in-metal-xps'], 'argon':['sputter-voltage','sputter-rate','sputter-step']}
    source_ids={'na-x':'na-x','tl-acetate':'tl-acetate','feed-water':'water','wash-water':'water',
      'in-metal':'in-metal','h2s':'h2s','pyrex':'pyrex','final-crystal':'in66-x',
      'parent-reference':'in87-x','indium-reference':'in-metal','argon':'ar'}
    maps=[]; rb={}; notes={}; entries_used=set()
    for rid,r in records.items():
      for i,mat in enumerate(r['materials']):
        mid=mat['id']; p=planned[mid]; ref=registry[p['registry_id']]; e=ref['entry']
        check(formula(mat['formula'])==formula(e['formula']),rid+' '+mid+' elemental identity')
        ii,im=inventory['heo2003-'+source_ids[mid]]
        source=[file_link(H/'source-inventory.json',f'/materials/{ii}',im)]
        for short in fact_ids[mid]:
            j,f=fact_index['heo2003-'+short]; source.append(file_link(H/'source-facts.json',f'/facts/{j}',f))
        ov=copy.deepcopy(p['viewOverrides'])
        if mid=='final-crystal':
          if rid.endswith('single-crystal-acquisition'):
            ov['name']='In66-X · sealed diffraction specimen'
            ov['caption']='H2S-treated In66-X crystal sealed for single-crystal diffraction. This symbolic specimen panel supplies no atomic coordinates. Nominal Si100Al92 remains distinct from the Table 2 average Si96Al96 refinement.'
          elif rid.endswith('epxma-acquisition'):
            ov['name']='In66-X · atmosphere-exposed EPXMA specimen'
            ov['caption']='Current treated crystal exposed to the atmosphere after diffraction for EPXMA/EDS. This symbolic panel represents that handling context; it does not transfer the sealed-state geometry or identify a sulfur-containing crystal phase.'
          else:
            ov['name']='In66-X · XPS and sputter-profile context'
            ov['caption']='Current treated-product XPS context. The initial spectrum and successive argon-sputtered states remain separate measurements; this shared symbolic icon does not specify surface composition or coordinates at any depth.'
        elif mid=='parent-reference':
          if rid.endswith('epxma-acquisition'):
            ov['name']='In87-X · EPXMA parent comparison'
            ov['caption']='Parent In87-X EPXMA/EDS comparison. Figure 1B is copied from reference 34; it is not a newly synthesized replicate or the treated In66-X specimen.'
          else:
            ov['name']='In87-X · XPS parent comparison'
            ov['caption']='Parent In87-X XPS comparison in Figure 2C. The parent/control spectrum is distinct from the treated product; this icon does not establish a same-crystal join with the copied Figure 1B EPXMA spectrum.'
        elif mid=='indium-reference':
          ov['name']='Indium metal · XPS reference'
          ov['caption']='Indium-metal XPS reference in Figure 2A, whose displayed intensity is scaled to one twentieth. This analytical reference is separate from the synthesis reagent charge and has no assigned metal-lattice coordinates.'
        elif mid=='feed-water':
          ov['caption']='Water solvent in the 0.1 mol/L thallous-acetate feed at pH 6.4. The feed-water grade is unreported. Neither the explicitly deionized wash-water grade nor the reused registry alias Milli-Q defines this feed.'
        ov['limitations']=list(dict.fromkeys([ov['caption']]+e.get('limitations',[])))
        if mid in ('in-metal','indium-reference'):
          ov['limitations']=[ov['caption'],'Symbolic elemental identity only; no bulk lattice, cluster geometry or isolated-atom measurement is assigned.']
        if mid=='parent-reference':
          ov['limitations']=[ov['caption'],'No parent atomic coordinates are supplied. Shared nominal composition does not prove a physical specimen join.']
        if mid in ('feed-water','wash-water','h2s'):
          ov['limitations'].append('Any displayed free-molecule 3D geometry is a locally computed illustration, not a measured Heo solution or gas structure.')
        assets=[]
        for key in ('svgPath','model2dPath','model3dPath'):
          if e.get(key):
            ap=ref['base']/e[key]
            check(sha(ap)==e['assetHashes'][key],rid+' '+mid+' '+key+' hash')
            assets.append({'kind':key,'file':str(ap.relative_to(H)).replace('\\','/'),'sha256':sha(ap)})
        material_scope='apparatus' if mid=='pyrex' else ('analytical_context' if r['record_id']!='heo-2003-in66-route' else 'route_material')
        item={'binding_id':rid+'::'+mid,'source_id':'heo2003','source_links':source,
          'canonical':file_link(V/'canonical-drafts'/f'{rid}.json',f'/materials/{i}',mat),
          'record_id':rid,'material_id':mid,'canonical_sha256':cm['record_hashes'][rid],
          'registry_id':e['id'],'reference':ref['source'],'reference_assets':assets,
          'scope':material_scope,'viewOverrides':ov,
          'binding_approved':False,'independent_binding_audit':'pending','published':False,
          'eligible_training':False,'exact_structure_or_dft_eligibility':False}
        if mid=='indium-reference': item['source_context_note']='The inventory indium identity is reused only as an elemental identity. The source fact and canonical slot assign the separate Figure 2A analytical role, not the reagent purity or charge.'
        if mid=='feed-water': item['source_context_note']='The inventory combines feed/wash water but explicitly restricts deionized to washing. This binding follows that qualification and the distinct canonical feed-water slot.'
        if mid=='argon': item['source_context_note']='The inventory supplies the explicit argon identity at main p. 5. Sputter-condition facts support only the analytical procedure, never a synthesis atmosphere.'
        maps.append(item); entries_used.add(e['id']); rb.setdefault(rid,{})[mid]=e['id']
        notes.setdefault(rid,{})[mid]={'binding_approved':False,'viewOverrides':ov,'source_id':'heo2003',
          'binding_id':item['binding_id'],'canonical_sha256':item['canonical_sha256'],
          'canonical_json_pointer':item['canonical']['json_pointer'],'independent_scientific_audit':'pending'}
    route=records['heo-2003-in66-route']; stock=route['stocks'][0]
    stock_links=[]
    for j,c in enumerate(stock['components']):
      b=next(x for x in maps if x['record_id']==route['record_id'] and x['material_id']==c['material_id'])
      stock_links.append({'component_id':c['material_id'],
        'canonical_component':file_link(V/'canonical-drafts'/f"{route['record_id']}.json",f'/stocks/0/components/{j}',c),
        'material_binding_id':b['binding_id'],'material_json_pointer':b['canonical']['json_pointer'],
        'registry_id':b['registry_id'],'reference':b['reference'],'viewOverrides':b['viewOverrides'],
        'role':'source-named salt; formal disconnected ionic connectivity' if j==0 else 'aqueous solvent; grade unspecified',
        'binding_approved':False})
    concentrations=[]
    for key,q in stock['concentrations'].items():
      concentrations.append(file_link(V/'canonical-drafts'/f"{route['record_id']}.json",'/stocks/0/concentrations/'+key,q))
    stock_binding={'record_id':route['record_id'],'stock_id':stock['id'],
      'canonical':file_link(V/'canonical-drafts'/f"{route['record_id']}.json",'/stocks/0',stock),
      'source_links':[file_link(H/'source-facts.json',f'/facts/{fact_index[x][0]}',fact_index[x][1]) for x in ['heo2003-exchange-stock','heo2003-exchange-ph','heo2003-exchange-volume']],
      'components':stock_links,'canonical_concentrations':concentrations,
      'label':stock['name'],'scope':read(M/'component-view-proposal.json')['scope'],
      'renderer_strategy':'Use existing mountStockComponents from the two canonical stock.components and approved per-material bindings. Do not add a duplicate solution-components context.',
      'solution_model':None,'preparation_operation_ids':stock['preparation_operation_ids'],
      'binding_approved':False,'independent_binding_audit':'pending','published':False}
    all_slots={(rid,i) for rid,r in records.items() for i in range(len(r['materials']))}
    check(len(maps)==14 and len(all_slots)==14,'All 14 material slots represented')
    check({(x['record_id'],int(x['canonical']['json_pointer'].split('/')[-1])) for x in maps}==all_slots,'Exact one-to-one slot coverage')
    check(len(stock_links)==2 and len(concentrations)==2,'Two stock components and two exact stock conditions')
    check(len(entries_used)==9,'Nine reference identities used for fourteen slots')
    for x in maps:
      check(pointer(records[x['record_id']],x['canonical']['json_pointer'])==x['canonical']['payload'],'Exact canonical payload '+x['binding_id'])
      check(set(x['viewOverrides'])=={'name','caption','limitations'},'Whitelisted scoped metadata '+x['binding_id'])
      for link in x['source_links']:
        check(pointer(read(H/link['file']),link['json_pointer'])==link['payload'],'Exact source payload '+x['binding_id']+' '+link['json_pointer'])
    check(registry['heo2003-thallous-acetate']['entry']['model3dPath'] is None,'No salt 3D assigned')
    for eid in entries_used:
      if eid.startswith('identity-'): check(registry[eid]['entry']['model2dPath'] is None and registry[eid]['entry']['model3dPath'] is None,'Symbolic representation only '+eid)
    flags={'author':'/root/peng1998_reader_assets','source_id':'heo2003','status':'private_author_proposal_pending_independent_binding_audit','published':False,'binding_approved':False,'eligible_training':False}
    put('material-slot-map.json',{'schema':'mattersyn-private-material-slot-bindings/1',**flags,'counts':{'canonical_records':10,'records_with_materials':4,'material_slots':14,'used_registry_identities':9},'bindings':maps})
    put('bindings-proposal.json',{'schemaVersion':'1.0.0',**flags,'recordBindings':rb,'bindingNotes':notes})
    put('stock-component-map.json',{'schema':'mattersyn-private-stock-component-bindings/1',**flags,'stocks':[stock_binding]})
    put('canonical-patch-proposal.json',{'schema':'mattersyn-private-canonical-patch-proposal/1',**flags,'base_manifest_sha256':EXPECTED_CANONICAL_FREEZE,'record_hashes':cm['record_hashes'],'patches':[],
      'reason':'No canonical mutation is necessary. The fourteen material slots, stock components, quantities and source roles already exist. Current viewer bindings are external to the strict canonical record schema.',
      'prohibited_changes':['Do not add viewer IDs to canonical material.identity.','Do not promote quality flags or requested_tasks.','Do not merge analytical samples or turn symbolic references into atomic structure_assets.']})
    deferred=[{'registry_id':'identity-heo2003-tl-x','source_material_id':'heo2003-tl-x','disposition':'not a canonical material or stock slot; retain as an optional future state depiction','canonical_contexts':[{'record_id':route['record_id'],'json_pointer':f'/material_states/{i}','state_id':x['id']} for i,x in enumerate(route['material_states']) if x['id'] in ('tl-x','dehydrated-tl-x')],'binding_created':False},
      {'registry_id':'identity-heo2003-surface-residue','source_material_id':'heo2003-surface-powder','disposition':'observed residue context, not an identified reagent/product phase; no new material slot or confirmed sulfide binding created','source_fact_id':'heo2003-surface-powder','binding_created':False}]
    put('unbound-context-dispositions.json',{'schema':'mattersyn-private-binding-dispositions/1',**flags,'contexts':deferred,'average_atomic_model_binding':'outside this material/stock proposal; no structure_assets or CIF binding created'})
    runtime=OUT/'runtime-contract-check.mjs'
    runtime.write_text("import fs from 'node:fs';\nimport assert from 'node:assert/strict';\nimport {pathToFileURL} from 'node:url';\nconst p="+json.dumps(str(OUT))+";\nconst read=n=>JSON.parse(fs.readFileSync(p+'/'+n,'utf8'));\nconst {chemicalEntry}=await import(pathToFileURL("+json.dumps(str(S/'dist/chemical-viewer.mjs'))+").href);\nconst bindings=read('bindings-proposal.json');\nconst maps=read('material-slot-map.json').bindings;\nconst entries=new Map();\nfor(const x of maps){const file="+json.dumps(str(H))+"+'/'+x.reference.file;const all=JSON.parse(fs.readFileSync(file,'utf8'));entries.set(x.registry_id,all.entries[Number(x.reference.json_pointer.split('/').at(-1))]);}\nlet checks=0;\nfor(const x of maps){const base=entries.get(x.registry_id);assert.equal(chemicalEntry({entries,bindings},x.record_id,x.material_id),base);checks++;}\n// Approval below exists only in a transient test fixture. The authored files stay false.\nconst fixture=structuredClone(bindings);\nfor(const x of maps){const note=fixture.bindingNotes[x.record_id][x.material_id];note.binding_approved=true;note.viewOverrides.formula='PROHIBITED_TEST_OVERRIDE';const scoped=chemicalEntry({entries,bindings:fixture},x.record_id,x.material_id);assert.equal(scoped.name,x.viewOverrides.name);assert.equal(scoped.caption,x.viewOverrides.caption);assert.equal(scoped.sourceBindingCaption,x.viewOverrides.caption);assert.deepEqual(scoped.limitations,x.viewOverrides.limitations);assert.equal(scoped.formula,entries.get(x.registry_id).formula);assert.equal(scoped.model3dPath,entries.get(x.registry_id).model3dPath);checks+=6;}\nconst feed=chemicalEntry({entries,bindings:fixture},'heo-2003-in66-route','feed-water');const wash=chemicalEntry({entries,bindings:fixture},'heo-2003-in66-route','wash-water');assert.notEqual(feed.caption,wash.caption);assert.ok(feed.caption.includes('grade is unreported'));assert.ok(wash.caption.includes('deionized'));checks+=3;\nconsole.log(JSON.stringify({status:'passed',checks,scope:'Actual chemicalEntry function; pending and hypothetical approved in-memory fixtures only. No DOM, browser, asset science or public integration audit.'}));\n",encoding='utf-8')
    node=Path(r'[local path redacted]')
    run=subprocess.run([str(node),str(runtime)],capture_output=True,text=True,encoding='utf-8')
    check(run.returncode==0,'Actual chemicalEntry contract check: '+run.stderr)
    runtime_result=json.loads(run.stdout); runtime_result['module']=file_link(S/'dist/chemical-viewer.mjs') if S.is_relative_to(H) else {'file':str(S/'dist/chemical-viewer.mjs'),'sha256':sha(S/'dist/chemical-viewer.mjs')}
    put('runtime-contract-result.json',runtime_result)
    after={str(p.relative_to(H)).replace('\\','/'):sha(p) for root in (V,M) for p in root.rglob('*') if p.is_file()}
    check(before==after,'All frozen canonical v1 and molecular files unchanged')
    put('input-integrity.json',{'schema':'mattersyn-private-binding-input-integrity/1','status':'passed','unchanged':True,'file_count':len(before),'before':before,'after':after})
    put('author-validation.json',{'schema':'mattersyn-private-binding-author-validation/1',**flags,'validation_status':'passed','check_count':len(checks),'runtime_contract_checks':runtime_result['checks'],'checks':checks,
      'scope':'Author pointer, identity-formula, exact payload, asset-hash, source-scope and actual pure viewer-function checks; not an independent scientific, browser or publication audit.',
      'pending':['Independent molecule and binding audit','Approved binding promotion and reference import by site owner','Actual stock selector and dialog browser QA','Separate product/atomic-model review and integration']})
    (OUT/'README.md').write_text('''# Heo material and stock binding proposal

This private author proposal binds all 14 material slots in four of the ten frozen canonical v1 records to nine molecular or symbolic references. One aqueous stock contains two independently selectable components. The source inventory and fact pointers, canonical payloads and file hashes, reference-entry pointers and asset hashes are retained in the maps.

No canonical patch is required. `canonical-patch-proposal.json` deliberately contains an empty patch list. The current viewer uses external `recordBindings` and approved, whitelisted `bindingNotes.viewOverrides`. All authored approval/publication/training flags remain false. Importing these pending bindings without later audited promotion would omit their scoped captions; the Site owner must complete the independent review gate first.

Thallous acetate remains disconnected formal Tl+ and acetate, with no salt 3D, hydrate, Tl–O coordination or unique aqueous speciation. Water and H2S free-molecule models are illustrative computed references. Feed-water grade is unreported; wash water is deionized. The existing water alias Milli-Q does not identify the source grade. The stock's 0.1 mol/L and pH 6.4 values are exact canonical objects; the Table 1 10 mL basis remains unresolved. No stock preparation, salt:water count or solution model was created.

Na-X, In66-X, In87-X, indium metal and Pyrex remain symbolic identity panels. Pyrex is apparatus. Reagent indium and the scaled XPS metal reference have distinct captions. The diffraction, atmosphere-exposed EPXMA and XPS/sputter specimens have separate slot mappings; shared icons do not establish new physical specimen joins. Parent EPXMA Figure 1B and XPS Figure 2C remain separately scoped.

Tl-X and the unknown residue have no material/stock slot in v1; their candidate assets remain unbound with explicit dispositions. No extra recipe, sulfide phase, atomic coordinates, CIF, DFT eligibility or training admission was introduced. The separately developed average-structure candidate is outside this package.

Author checks verify every pointer and source/canonical snapshot, equivalent elemental formulas despite formula-order differences, all used asset hashes and unchanged input packages. The pure `chemicalEntry` function was tested from the actual current module with pending bindings and a temporary hypothetical approved fixture; no approval was written. This is not browser QA or independent molecular science review. The distinct reviewer will audit this package and the source molecule package before integration.
''',encoding='utf-8')
    files={str(p.relative_to(OUT)).replace('\\','/'):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()}
    put('package-manifest.json',{'schema':'mattersyn-private-canonical-binding-package/1',**flags,'status':'frozen_author_proposal_pending_independent_binding_audit','version':1,
      'counts':{'canonical_records_bound_as_inputs':10,'records_with_material_slots':4,'material_slots':14,'registry_identities_used':9,'stocks':1,'stock_components':2,'stock_conditions':2,'deferred_context_assets':2,'canonical_patches':0},
      'canonical_v1_manifest_sha256':EXPECTED_CANONICAL_FREEZE,'molecule_freeze_sha256':EXPECTED_MOLECULE_FREEZE,'files':files,
      'input_hashes':{'source-inventory.json':sha(H/'source-inventory.json'),'source-facts.json':sha(H/'source-facts.json'),'canonical-proposal/v1/proposal-package-manifest.json':sha(V/'proposal-package-manifest.json'),'visuals/molecules/package-freeze.json':sha(M/'package-freeze.json'),'current-viewer-module':sha(S/'dist/chemical-viewer.mjs')},
      'record_hashes':cm['record_hashes'],'author_validation_sha256':sha(OUT/'author-validation.json')})
    print(json.dumps({'status':'author_frozen','manifest_sha256':sha(OUT/'package-manifest.json'),'checks':len(checks),'runtime_checks':runtime_result['checks'],'counts':read(OUT/'package-manifest.json')['counts']},indent=2))

if __name__=='__main__': main()
