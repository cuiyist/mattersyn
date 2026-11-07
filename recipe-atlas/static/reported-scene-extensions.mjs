// Conservative reader-only extensions for otherwise unmatched operation images.
// No paper/model reads or record writes; own current-step facts only.
const words=v=>typeof v==='string'?v.toLowerCase().replaceAll('_',' ').replace(/[-\u2013\u2014]/g,' ').replace(/\s+/g,' ').trim():'';
const positive=(v,re)=>words(v).split(/[.;]/).some(c=>re.test(c)&&!/\b(?:avoid|prevent|without|no|not|omit|exclude|rather than)\b[^,;]*$/.test(c.slice(0,c.search(re))));
const liquid=/\b(?:aqueous|solutions?|solvents?|slurr(?:y|ies)|suspensions?|dispersions?|sols?|gels?|water|ethanol|methanol|propanol|isopropanol|butanol|toluene|hexane|heptane|chloroform|chlorobenzene|acetonitrile|acetone|oleylamine|octadecene|ode|toa|top|dodecane|hexadecane)\b/;
const solids=/\b(?:powders?|wafer|substrates?|dry solids?|mortar|pestle|pellets?|foils?|films?|ribbons?|substrate)\b/;
const vessel=/\b(?:vial|tube|beaker|flask|bottle)\b/;
const technique=/\bmbe\b|molecular beam epitax|\bmocvd\b|\bmovpe\b|\bcvd\b|chemical vapou?r deposition|sputter|vacuum deposition|thermal evaporation|epitax|(?:growth|deposition|vacuum|evaporation) chamber/;
export function extendedReportedScene(o,r,{descriptor,readReactorLineNote}={}){
 const action=words(o?.action),label=words(o?.label),detail=words(o?.description),own=[action,label,detail].join(' ');
 if(!action||/^(?:do not|never|avoid|omit|without)\b/.test(action))return {reason:'missing_or_negated_action'};
 if(/\b(?:optionally|if necessary|may|might|could|would|will)\b/.test(own)||/^(?:do not|never|avoid|omit|without)\b/.test(detail))return {reason:'conditional_or_negated_own_instruction'};
 if(/\b(?:for later|prior to|subsequent|before|afterwards|next stage)\b/.test(own))return {reason:'temporally_ambiguous_own_context'};
 if(/\b(?:measur\w*|character\w*|acquire\w*|spectr\w*|imag\w*|scan\w*|monitor\w*|record\w*|observ\w*|analy\w*|absorption|photoluminescence|pl|xrd|tem)\b/.test(action))return {reason:'characterization_or_observation'};
 const materialById=new Map((r.materials||[]).map(m=>[m.id,m]));
 const directSolvent=(o.inputs||[]).some(id=>materialById.get(id)?.role==='solvent');
 const liquidOwn=(positive(own,liquid)&&!positive(own,/\b(?:water|solvent) vapou?r\b/))||directSolvent;
 const solidOwn=positive(own,solids)&&!liquidOwn;
 const surfaceWords=/\b(?:substrates?|wafers?|foils?|films?|ribbons?)\b/;
 const surfaceInput=(o.inputs||[]).some(id=>{const m=materialById.get(id);return m?.role==='substrate'||positive(m?.name,surfaceWords);});
 const surfaceContext=surfaceInput||positive(own,surfaceWords);
 const explicitDissolveOrDisperse=/\b(?:dissolv\w*|redissolv\w*|dispers\w*|redisper\w*)\b/.test(action)||/^(?:dissolv\w*|redissolv\w*|dispers\w*|redisper\w*)\b/.test(label);
 const genericLiquidBlocked=surfaceContext&&!explicitDissolveOrDisperse;
 const hook={readReactorLine:readReactorLineNote};
 const ownVessel=typeof descriptor==='function'?descriptor({...o,action:'wash'},r,hook)?.vessel:null;
 const ownReportedVessel=ownVessel?.scope==='step'&&vessel.test(words(ownVessel.value));
 const reportedEnv=o.environment?.status==='reported'?words(o.environment.value):'';
 const yes=(kind,rule)=>({kind,rule,reason:'new_conservative_match',liquid_own:liquidOwn,direct_solvent_input:directSolvent,reported_step_vessel:Boolean(ownReportedVessel),vessel_scope:'step_only',heating:'no_borrowed_heat',added_names:'existing_explicit_addition_rules_only'});
 // Accept only a current, anchored own-label action for bookkeeping action keys.
 const ownLabel=/^(?:(?:then|slowly|rapidly|carefully)\s+)*(centrifug(?:e|ed|ing|ation)|filter(?:ed|ing)?|filtration|wash(?:ed|ing)?|rins(?:e|ed|ing)|precipitat(?:e|ed|ing|ion)|redisper(?:se|sed|sing|sion)|resuspend(?:ed|ing)?|dr(?:y|ied|ying)|dissolv(?:e|ed|ing)|redissolv(?:e|ed|ing)|prepar(?:e|ed|ing|ation)|mix(?:ed|ing)?|combin(?:e|ed|ing|ation)|add(?:ed|ing|ition)?|stir(?:red|ring)?|inject(?:ed|ing|ion)?|heat(?:ed|ing)?|preheat(?:ed|ing)?|degas(?:sed|sing)?|purg(?:e|ed|ing)|cool(?:ed|ing)?|quench(?:ed|ing)?|reflux(?:ed|ing)?)\b/.exec(label);
 if(ownLabel&&typeof descriptor==='function'&&!solidOwn){
  const verb=ownLabel[1],workup=/^(?:centrifug|filter|filtrat|wash|rins|precipitat|redisper|resuspend|dry)/.test(verb);
  if(!genericLiquidBlocked&&(workup||liquidOwn||ownReportedVessel)){
   const aliases=[[/^centrifug/,'centrifuge'],[/^(?:filter|filtrat)/,'filter'],[/^wash/,'wash'],[/^rins/,'rinse'],[/^precipitat/,'precipitate'],[/^redisper/,'redisperse'],[/^resuspend/,'resuspend'],[/^dry/,'dry'],[/^(?:dissolv|redissolv)/,'dissolve'],[/^prepar/,'prepare'],[/^mix/,'mix'],[/^combin/,'combine'],[/^add/,'add'],[/^stir/,'stir'],[/^inject/,'inject'],[/^(?:heat|preheat)/,'heat'],[/^degas/,'degas'],[/^purge/,'purge'],[/^cool/,'cool'],[/^quench/,'quench'],[/^reflux/,'reflux']];
   const selected=aliases.find(([re])=>re.test(verb))?.[1];
   const scoped={...r,method:'Other',products:(r.products||[]).map(p=>({...p,notes:(p.notes||[]).filter(n=>!/^Reactor:/.test(n))}))};
   const candidate=selected?descriptor({...o,action:selected},scoped,hook):null;
   if(candidate)return {...yes(candidate.kind,'anchored_current_own_label_supported_action'),selector_action:selected};
  }
 }
 // A broad bookkeeping verb may specify a concrete current operation in its label.
 const workupVerb=/\b(?:purif\w*|recover\w*|collect\w*|isolat\w*|separat\w*|extract\w*)\b/.test(action);
 if(workupVerb){
  if(positive(label,/\bcentrifug\w*\b/))return yes('centrifuge','explicit_own_label_centrifugation');
  if(positive(label,/\bfiltrat\w*|\bfilter\w*/))return yes('filter','explicit_own_label_filtration');
  if(positive(label,/\b(?:wash\w*|rins\w*|precipitat\w*|floccul\w*|redisper\w*|resuspend\w*)\b/))return yes('workup-tube','explicit_own_label_wet_workup');
  if(!genericLiquidBlocked&&(liquidOwn||positive(label,/\b(?:organic|aqueous) phase\b|\bsupernatant\b/)))return yes('workup-tube','generic_workup_with_own_liquid_or_phase');
  return {reason:'workup_technique_or_liquid_not_explicit'};
 }
 if(/\b(?:evaporat\w*|concentrat\w*|remove (?:solvent|volatiles)\w*)\b/.test(action)&&liquidOwn&&!solidOwn&&!genericLiquidBlocked)return yes('dry-tube','own_liquid_evaporation_or_concentration');
 if(/\bredissolv\w*\b/.test(action)&&!solidOwn)return yes('solution','explicit_redissolution_alias');
 if(/\bpreheat\w*\b/.test(action)&&(liquidOwn||ownReportedVessel)&&!solidOwn&&!genericLiquidBlocked)return yes('solution','preheat_with_own_liquid_or_reported_vessel');
 if(/\b(?:clean\w*)\b/.test(action)&&liquidOwn&&!solidOwn&&!genericLiquidBlocked)return yes('workup-tube','own_liquid_cleaning');
 if(/\b(?:dispers\w*|dilut\w*|formulat\w*|sonicat\w*|ultrasonicat\w*|charg\w*|load\w*|dispens\w*|fill\w*|transfer\w*|age|aging|incubat\w*|exchange\w*|recrystalliz\w*)\b/.test(action)){
  if(liquidOwn&&!solidOwn&&!genericLiquidBlocked)return yes('solution','own_liquid_supported_action');
  return {reason:'liquid_context_not_explicit'};
 }
 if(/\bstore\w*\b/.test(action)){
  if(ownReportedVessel&&liquidOwn&&!solidOwn&&!genericLiquidBlocked)return yes('workup-tube','storage_with_reported_own_container');
  return {reason:'storage_vessel_or_liquid_not_explicit'};
 }
 if(/\b(?:grow\w*|deposit\w*|cap\w*|supply\w*)\b/.test(action)){
  if(positive(reportedEnv,technique)||positive(label+' '+detail,technique))return yes('chamber','explicit_own_step_deposition_system');
  if(/\bgrow\w*\b/.test(action)&&liquidOwn&&!solidOwn&&!genericLiquidBlocked)return yes('solution','growth_with_explicit_own_liquid');
  return {reason:'growth_or_deposition_system_not_explicit'};
 }
 if(/\b(?:anneal\w*|heat\w*)\b/.test(action)&&positive(label+' '+detail,/\bfurnace\b/))return yes('furnace','explicit_own_step_furnace');
 if(/\b(?:evacuat\w*|vacuum)\b/.test(action)&&liquidOwn&&!solidOwn&&!genericLiquidBlocked)return yes('degas','evacuation_with_own_liquid');
 if(positive(own,/\bmortar\b/)&&positive(own,/\bpestle\b/)&&/\b(?:grind\w*|mix\w*)\b/.test(action))return yes('mortar-pestle','explicit_own_mortar_and_pestle');
 if(genericLiquidBlocked)return {reason:'explicit_surface_or_substrate_not_a_generic_liquid_sample'};
 if(solidOwn)return {reason:'unsupported_solid_handling_or_apparatus'};
 if(/\b(?:anneal\w*|calcin\w*|sinter\w*|oxidiz\w*|reduc\w*|melt\w*)\b/.test(action))return {reason:'thermal_or_reaction_apparatus_not_explicit'};
 return {reason:'unsupported_or_insufficient_own_step_evidence'};
}
