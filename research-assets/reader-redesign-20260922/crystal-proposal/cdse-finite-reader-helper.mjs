export function finiteReferencesForRecord(refs,r){
 return refs.filter(ref=>ref.finiteModelPath&&(!Array.isArray(ref.finiteRecordIds)||ref.finiteRecordIds.includes(r.record_id))).map(ref=>({
  ...ref,
  name:ref.finiteName||ref.name,
  sourceType:ref.finiteSourceType||ref.sourceType,
  referenceType:ref.finiteReferenceType||ref.referenceType,
  phaseScope:ref.finiteScope||ref.phaseScope,
  scope:ref.finiteScope||ref.scope,
  sample_context_note:ref.finiteContextNote||ref.sample_context_note,
  displayPolicy:ref.finiteDisplayPolicy||ref.displayPolicy,
  cifPath:ref.finiteCifPath||ref.cifPath,
  cifSha256:ref.finiteCifSha256||ref.cifSha256,
  sourceUrl:ref.finiteSourceUrl||ref.sourceUrl,
  additionalDownloads:ref.finiteAdditionalDownloads||ref.additionalDownloads
 }));
}
