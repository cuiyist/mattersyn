import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const sharp=require('[local path redacted]');
const A=path.dirname(fileURLToPath(import.meta.url)),V=path.join(A,'../v1');
const {buildHeo2003Scene}=await import('../v1/heo2003-protocol.mjs');
const records=JSON.parse(fs.readFileSync(path.join(V,'records.json'))),saved=JSON.parse(fs.readFileSync(path.join(V,'scene-output.json')));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const checks=[],renders=[];
const ck=(check,passed)=>checks.push({check,passed:Boolean(passed)});
fs.mkdirSync(path.join(A,'renders'),{recursive:true});
let i=0;
for(const r of records)for(const o of r.operations){
 const s=buildHeo2003Scene(o,r),old=saved[i++],svgPath=path.join(V,'scenes',s.kind+'.svg'),bytes=fs.readFileSync(svgPath);
 ck(s.kind+' exact module SVG reproduces freeze',Buffer.from(s.svg).equals(bytes));
 ck(s.kind+' condition rows exact',JSON.stringify(s.rows)===JSON.stringify(old.rows));
 ck(s.kind+' source description exact',s.description===o.description&&s.description===old.description);
 ck(s.kind+' scope guard rejects foreign source',buildHeo2003Scene(o,{...r,lineage:{source_group:'other'}})===null);
 ck(s.kind+' scope guard rejects unknown operation',buildHeo2003Scene({...o,id:'unknown'},r)===null);
 const png=await sharp(bytes).png().toBuffer();
 const out=path.join(A,'renders',s.kind+'.png');fs.writeFileSync(out,png);
 const m=await sharp(png).metadata();renders.push({kind:s.kind,source_svg:svgPath,source_sha256:hash(bytes),render:out,render_sha256:hash(png),width:m.width,height:m.height});
}
ck('All14 operations independently reproduced',i===14);
ck('59 condition rows retained',saved.reduce((n,s)=>n+s.rows.length,0)===59);
for(let j=0;j<renders.length;j+=2){
 const pair=renders.slice(j,j+2),height=Math.max(...pair.map(x=>x.height));
 const out=path.join(A,'renders',`contact-${String(j/2+1).padStart(2,'0')}.png`);
 await sharp({create:{width:1800,height,channels:4,background:'#e9eff4'}}).composite(pair.map((x,k)=>({input:x.render,left:k*900,top:0}))).png().toFile(out);
}
const result={scope:'Independent exact module execution and deterministic SVG raster viewing derivatives; frozen inputs untouched.',checks,renders,counts:{checks:checks.length,failed:checks.filter(x=>!x.passed).length,scenes:renders.length}};
fs.writeFileSync(path.join(A,'module-checks.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result.counts));
