// A duration mentioning temperature is still a duration, never a temperature.
export function matchProtocolCondition(entries, pattern){
 const matches=new RegExp(pattern,'i');
 return entries.find(([name,q])=>{
  if(!matches.test(name))return false;
  if(pattern==='temperature'){
   if(/duration|time|rate|ramp|interval/i.test(name))return false;
   if(q?.unit&&!['degC','°C','C','K','kelvin','degF','°F'].includes(q.unit))return false;
  }
  if(pattern==='pressure'&&/duration|time|rate|interval/i.test(name))return false;
  return true;
 });
}
