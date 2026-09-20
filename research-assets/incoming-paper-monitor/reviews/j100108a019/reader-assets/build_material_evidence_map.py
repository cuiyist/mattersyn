"""Private, manually scoped record-to-material evidence map. No Site writes."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SITE=HERE.parents[4]/'recipe-atlas'
PREFIX='littau-1993-si-'

CURATED={
    PREFIX+'aerosol-1p0':('synthesis_route',['synthesis_protocol','final_structures'],
        'Current-apparatus 1.0 stock-mixture-flow formulation; Table I entries have formulation-level linkage only. Crystallinity is not directly established. Missing TEM/core/XRD values remain missing; HPLC equivalent diameter is not a crystalline-core diameter.'),
    PREFIX+'aerosol-2p0':('synthesis_route',['synthesis_protocol','final_structures'],
        'Current-apparatus 2.0 stock-mixture-flow formulation. Overall TEM diameter, dark-field core size, XRD coherence and HPLC-equivalent size are different observables. Do not assume the same physical batch, collector fraction or acquisition specimen across techniques.'),
    PREFIX+'aerosol-6p0':('synthesis_route',['synthesis_protocol','final_structures'],
        'Current-apparatus 6.0 stock-mixture-flow formulation. Overall TEM diameter, dark-field core size, XRD coherence and HPLC-equivalent size are different observables. Retain Table I/prose disagreements and unresolved specimen linkage.'),
    PREFIX+'colloid-concentration':('supporting_procedure',['supporting_protocols'],
        'Shared vacuum-concentration workup with no exact formulation, starting/final volume, vacuum level or time assignment. Not an additional synthesis or a quantified yield.'),
    PREFIX+'powder-preparation':('supporting_procedure',['supporting_protocols','final_structures'],
        'Dry-powder preparation context for characterization; typical recovered mass is not a run-resolved synthesis yield. Preserve the washed-powder versus source unwashed-powder caveat; no exact batch/technique join is created.'),
    PREFIX+'hplc-fractionation':('supporting_procedure',['supporting_protocols','final_structures','properties'],
        'Size-exclusion calibration, fractionation, activated-fraction quenching and reactivation are distinct contexts. Polymer-calibrated HPLC size includes hydrodynamic/aggregation effects and is not a direct crystalline-core measurement. Do not attach an exact fraction or reactivation treatment to an unspecified formulation.'),
    PREFIX+'tem-characterization':('supporting_procedure',['final_structures'],
        'Contains different aerosol, evaporated-colloid and HPLC-fraction grid-preparation branches plus 6.0/2.0 structural contexts. Total diameter, core diameter, shell thickness and core/total ratio retain their definitions. Preparation branch is not uniquely assigned to each micrograph. SAED is discussed in prose; no original SAED image is supplied.'),
    PREFIX+'xrd-characterization':('supporting_procedure',['final_structures'],
        '6.0 and 2.0 powder lattice comparisons are separate from the source-stated bulk-Si lattice reference. The reference is not a measured nanocrystal CIF. Alternative mounting contexts and unresolved exact specimens remain explicit.'),
    PREFIX+'ir-characterization':('supporting_procedure',['final_structures','properties'],
        'IR bands belong to the 6.0 dry-powder/KBr-pellet context and include surface-oxide/hydroxyl/impurity interpretation. They are not bulk or isolated-Si vibrational properties and are not evidence that Raman data were acquired.'),
    PREFIX+'acid-activation':('supporting_procedure',['supporting_protocols','properties'],
        'Separate as-made and acid-activated 6.0, 2.0 and 1.0 contexts. Three activated PL peaks are distinct from the shared approximate QY cohort; do not assign the QY independently to every formulation or its as-made state. The added-water pH is not the final mixture pH; the 5% basis is unresolved.'),
    PREFIX+'optical-characterization':('supporting_procedure',['properties'],
        'As-made 6.0 emission and the low-temperature bulk-Si comparison are separate specimens. Do not transfer the bulk-Si reference peak to colloids, replace activated-state PL with as-made values, or imply that a bulk-Si control has a reconstructed synthesis recipe.'),
    PREFIX+'time-resolved-pl':('supporting_procedure',['properties'],
        'The two fitted decay components refer to activated 1.0 colloid; they are not two samples, an average lifetime, a run duration, or a proven crystalline-Si core lifetime. Preserve missing amplitudes, fit details and exact batch linkage.'),
    'littau-1993-aks41-context':('contextual_observation',['final_structures'],
        'Earlier-apparatus AKS41 observation without a reconstructed synthesis. Separate the population distribution, one Figure 3 particle and three HPLC fractions. Parent-context phase/shell evidence is not a separate measurement on every fraction. Keep ASK41 as a printed alias, not a second sample; do not assign 1.0/2.0/6.0 stock flows.'),
}


def main():
    records={}
    hashes={}
    for rid in CURATED:
        path=SITE/'data/records'/f'{rid}.json'
        raw=path.read_bytes()
        records[rid]=json.loads(raw)
        hashes[rid]=hashlib.sha256(raw).hexdigest()
    shared=(
        'Seven supplied main pages were reviewed; matching SI is not located or verified. '
        'These are source-level evidence records. Shared formulation names do not establish identical '
        'physical batches, collector fractions, treatment states or characterization specimens. '
        'Keep routes, supporting procedures and AKS41 context separate. '
        'The map controls reader visibility only; it does not alter canonical lineage, route counts or training eligibility.'
    )
    component=(
        'Component context: these records describe surface-oxidized Si/SiOx colloids and their named specimens, '
        'not a standalone bare-Si synthesis or intrinsic isolated-Si properties. '
        'Surface/interface, activated-colloid and whole-particle measurements retain their Si/SiOx attribution. '
        'Bulk-Si references remain separate comparison specimens. '
        'The 1.0 formulation does not establish a crystalline Si core.'
    )
    ids=list(CURATED)
    details={}
    for rid,(role,sections,note) in CURATED.items():
        r=records[rid]
        details[rid]={
            'record_type':r['record_type'],'display_role':role,'sections':sections,
            'record_material_formula':r['material']['formula'],
            'sample_scope_caveat':note,
            'sample_ids':[p['sample_id'] for p in r['products']],
            'measurement_ids':[m['id'] for m in r['measurements']],
            'measurement_sample_links':{m['id']:m['sample_id'] for m in r['measurements']},
            'component_si_attribution':'Surface-oxidized Si/SiOx system context; never relabel the whole record as intrinsic Si.',
            'source_evidence_locators':sorted({ev['locator'] for field in ['operations','measurements'] for obj in r[field] for ev in obj.get('evidence',[]) if ev['source_id']=='littau1993'}),
        }
    output={
        'schema':'mattersyn-material-evidence-map-proposal-1',
        'source_group':'littau1993','doi':'10.1021/j100108a019',
        'review_scope':'supplied_main_only_si_unverified',
        'material_evidence_records':{'Si/SiOx':ids,'Si':ids},
        'material_evidence_scope':{
            'Si/SiOx':{'contribution_role':'direct_material_evidence','caveat':shared},
            'Si':{'contribution_role':'component_system_evidence','caveat':component+' '+shared,
                  'render_requirement':'Show the component caveat above evidence and preserve each record material formula and sample labels. If the renderer cannot show these qualifications, link to the Si/SiOx evidence section instead of rendering unqualified Si properties.'},
        },
        'record_display_groups':{
            'synthesis_routes':[rid for rid in ids if CURATED[rid][0]=='synthesis_route'],
            'supporting_procedures':[rid for rid in ids if CURATED[rid][0]=='supporting_procedure'],
            'contextual_observations':[rid for rid in ids if CURATED[rid][0]=='contextual_observation'],
        },
        'supporting_evidence_record_ids':[rid for rid in ids if CURATED[rid][0]!='synthesis_route'],
        'record_scope':details,
        'count_policy':{
            'unique_source_records':13,'synthesis_routes':3,'supporting_procedures':9,
            'contextual_observations':1,'measurement_entries':48,
            'direct_route_counts_by_material':{'Si/SiOx':3,'Si':0},
            'shared_component_route_contributions':{'Si':3},
            'additional_routes_created':0,
            'warning':'The same 13 IDs appear on two material pages. Count them once; do not append the ten supporting/context records to the synthesis-route registry or selectors.'},
        'integration_policy':[
            'Attach this map to the Littau source-review metadata. Keep it separate from hub record_ids/direct_record_ids and synthesis-route counting.',
            'Use a distinct source-evidence panel with record categories. Do not append all procedures and observations to the selected route product/measurement arrays.',
            'Scope original figures with existing record/sample/formulation metadata. A source-wide map is not a license to assign every figure to every route.',
            'Keep bulk-Si references, as-made/activated samples, AKS41 population/particle/fractions, and HPLC/TEM/XRD observables separate.',
            'No separate SiOx page or bare-Si route is proposed.',
        ],
        'canonical_record_sha256':hashes,'site_changed':False,'published':False,
    }
    checks=[]
    def check(label,condition):checks.append({'check':label,'passed':bool(condition)})
    check('All actual Littau records covered exactly once per material',set(records)=={p.stem for p in (SITE/'data/records').glob('littau-*.json')} and all(len(v)==len(set(v))==13 for v in output['material_evidence_records'].values()))
    check('Shared source and Si/SiOx formula verified',all(r['lineage']['source_group']=='littau1993' and r['material']['formula']=='Si/SiOx' and 'Si' in r['material']['components'] for r in records.values()))
    check('Exactly 3 routes, 9 procedures, 1 observation',tuple(len(v) for v in output['record_display_groups'].values())==(3,9,1))
    check('Procedures and observations cannot become routes',all(records[rid]['record_type']=='procedure' and not records[rid]['quality']['requested_tasks'] for rid in output['record_display_groups']['supporting_procedures']) and all(records[rid]['record_type']=='observation' and not records[rid]['operations'] and not records[rid]['quality']['requested_tasks'] for rid in output['record_display_groups']['contextual_observations']))
    check('Three established route IDs only',all(records[rid]['record_type']=='protocol_variant' and 'precursor_selection' in records[rid]['quality']['requested_tasks'] for rid in output['record_display_groups']['synthesis_routes']))
    check('48 measurement entries preserved with original sample assignments',sum(len(x['measurement_ids']) for x in details.values())==48 and all(set(x['measurement_sample_links'].values())<=set(x['sample_ids']) for x in details.values()))
    check('No physical recipe linkage inferred',all(p['recipe_link']=='general_context' for r in records.values() for p in r['products']))
    check('Input bytes unchanged during map preparation',all(hashlib.sha256((SITE/'data/records'/f'{rid}.json').read_bytes()).hexdigest()==h for rid,h in hashes.items()))
    errors=[x['check'] for x in checks if not x['passed']]
    validation={'status':'passed' if not errors else 'failed','checks':checks,'errors':errors,'scope':'Curated reader-visibility/category/sample-scope map only; no new scientific review or publication.'}
    assert not errors,errors
    (HERE/'material-evidence-map.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (HERE/'material-evidence-map-validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Littau material evidence map','','All 13 records may be shown under **Si/SiOx**. The **Si** component page may link/show the same records only as evidence for surface-oxidized Si/SiOx, with its component caveat visible. It must not label the optical, surface, oxide or whole-particle measurements as intrinsic/bare-Si properties. If the UI cannot preserve these qualifications, link to the Si/SiOx evidence panel instead.','','The flat map is `material-evidence-map.json:material_evidence_records`; categories, exact specimen/measurement IDs, source locators and record hashes are supplied alongside it. There are only **three routes**, plus **nine procedures** and **one AKS41 observation**. The ten non-route records belong in a separate source-evidence panel, not the route selector.','','## Exact record IDs and scope','']
    for rid,(role,sections,note) in CURATED.items():
        lines+=['- `'+rid+'` — '+role.replace('_',' ')+'. '+note]
    lines+=['','## Required caveats','',shared,'',component,'','Every figure and measurement retains its own acquisition/sample scope. The bulk-Si lattice reference and optical control remain reference specimens; AKS41 is not a fourth current-apparatus recipe. No extra route, physical-batch identity or training eligibility is created. Eight map-validation checks passed.','','No Site files were changed.']
    (HERE/'material-evidence-map.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'status':'passed','checks':len(checks),'material_keys':list(output['material_evidence_records']),'unique_records':13,'routes':3,'procedures':9,'observations':1,'measurement_entries':48}))


if __name__=='__main__':main()
