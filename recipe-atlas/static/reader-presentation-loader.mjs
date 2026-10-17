// One shared promise cache for current monolith and fixed verified public parts.
const BASE='reader-presentation.json';
const PART='reader-presentation.part2.json';
const MARKER='_reader_registry_split';
const TABLES=['records','materials','figures_by_source'];
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
function tables(value){if(!object(value)||TABLES.some(k=>!object(value[k])))throw Error('Invalid Reader tables');}
export function createReaderPresentationLoader({fetcher=(...a)=>globalThis.fetch(...a),crypto=globalThis.crypto}={}){
 const cache=new Map();
 async function bytes(url){const response=await fetcher(url,{cache:'no-store'});if(!response.ok)throw Error('Unavailable '+url);return new Uint8Array(await response.arrayBuffer());}
 const parse=raw=>JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw));
 async function read(url){
  const base=parse(await bytes(url));tables(base);
  if(!own(base,MARKER))return base;
  const marker=base[MARKER];
  if(!object(marker)||Object.keys(marker).sort().join(',')!=='part,schema,sha256'||marker.schema!=='reader-presentation-two-part/1'||marker.part!==PART||!(/^[0-9a-f]{64}$/).test(marker.sha256))throw Error('Invalid public Reader split marker');
  if(!crypto?.subtle)throw Error('Reader checksum verification unavailable');
  const raw=await bytes(new URL(PART,url).href);
  const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)),b=>b.toString(16).padStart(2,'0')).join('');
  if(digest!==marker.sha256)throw Error('Reader part checksum differs');
  const part=parse(raw);tables(part);
  if(Object.keys(part).sort().join(',')!==[...TABLES].sort().join(','))throw Error('Unexpected Reader part fields');
  const result={...base};delete result[MARKER];
  for(const table of TABLES){
   if(Object.keys(part[table]).some(key=>own(base[table],key)))throw Error('Duplicate Reader keys across parts');
   result[table]={...base[table],...part[table]};
  }
  return result;
 }
 return function load(url){
  const key=new URL(String(url),import.meta.url);
  if(!key.pathname.endsWith('/'+BASE))return Promise.reject(Error('Use the fixed public Reader path'));
  if(!cache.has(key.href))cache.set(key.href,read(key.href));
  return cache.get(key.href);
 };
}
export const loadReaderPresentations=createReaderPresentationLoader();
