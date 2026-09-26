// Artwork is admitted by the source/asset release gates; this selector only binds
// an already reviewed illustration to its exact record and operation.
export function selectProtocolArt(binding,record,operation){
 if(!binding||binding.record_id!==record.record_id||!Array.isArray(binding.bindings))return null;
 const matches=binding.bindings.filter(item=>item.operation_id===operation.id);
 if(matches.length!==1)return null;
 const item=matches[0];
 if(!/^assets\/protocol\/[a-zA-Z0-9_-]+\.(svg|png|webp)$/.test(item.asset_path||'')||
    !/^[a-f0-9]{64}$/.test(item.asset_sha256||'')||
    typeof item.caption!=='string'||!item.caption||
    typeof item.source_locator!=='string'||!item.source_locator)return null;
 return item;
}
