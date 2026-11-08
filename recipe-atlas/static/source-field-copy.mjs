// Reader display copy only. Stored status, evidence and facts are never changed.
export const READER_COPY=Object.freeze({
  conditions:'Conditions and source', sourceLink:'Source details →',
  toolbar:'Synthesis and evidence', sourceFigureScope:'record',
  interpretation:'Further interpretation is available in the original source.',
});
const missing=/^(?:not reported|not recorded in this field|not specified|unspecified|source empirical formula not reported)$/i;
export function conditionFieldText(value,record){return typeof value==='string'&&missing.test(value.trim())?'Not reported':value;}
export function conditionDisclosureText(record){return READER_COPY.conditions;}
export function productFactLabel(label,record){return ['Crystal phase','Phase'].includes(label)?'Phase or crystallinity':label;}
export function formulaFieldText(value){const display=conditionFieldText(value);return display==null||typeof display==='string'&&!display.trim()?'Not reported':display;}
