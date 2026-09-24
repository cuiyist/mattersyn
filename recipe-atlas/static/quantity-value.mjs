// Shared scalar/range/bound display. A reported upper bound is never an exact value.
export function quantityValue(q){
 if(!q)return null;
 if(q.value!==null&&q.value!==undefined)return q.value;
 const lo=q.minimum,hi=q.maximum,hasLo=lo!==null&&lo!==undefined,hasHi=hi!==null&&hi!==undefined;
 if(hasLo&&hasHi)return q.minimum_exclusive||q.maximum_exclusive?`${q.minimum_exclusive?'(':'['}${lo}, ${hi}${q.maximum_exclusive?')':']'}`:`${lo}–${hi}`;
 if(hasLo)return `${q.minimum_exclusive?'>':'≥'}${lo}`;
 if(hasHi)return `${q.maximum_exclusive?'<':'≤'}${hi}`;
 return null;
}
