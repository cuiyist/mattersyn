// Display scope only: recorded fields do not assert what the full paper omits.
const extracted=r=>r?.quality?.review_status==='source_extracted';
export function conditionFieldText(value,record){return extracted(record)&&value==='Not reported'?'Not recorded in this field':value;}
export function conditionDisclosureText(record){return extracted(record)?'Conditions and source':'All reported conditions and source';}
export function productFactLabel(label,record){return extracted(record)&&['Crystal phase','Phase'].includes(label)?'Phase or crystallinity':label;}
