const fs=require('fs'),path=require('path'),crypto=require('crypto');
const sharp=require('[local path redacted]');
const P=__dirname;
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const manifest=JSON.parse(fs.readFileSync(path.join(P,'container-manifest.json')));
const map={schema_version:'1.0',scope:'Compact card depictions only; full original SVG and molecular viewer remain authoritative.',registry_sha256:manifest.registry_sha256,entries:{}};
const converted=[];let checks=0;
async function main(){
 for(const e of manifest.entries){
  const result={original_svg:e.original_svg,original_sha256:e.original_sha256,thumbnail_path:e.thumbnail_path,status:e.status,reason:e.reason};
  if(e.status==='candidate_compact'){
   const source=path.join(P,e.container_path),xml=fs.readFileSync(source,'utf8');
   const start=xml.match(/<svg\b[^>]*>/)[0],vb=start.match(/viewBox="([^"]+)"/);
   if(!vb){result.status='original_retained';result.reason='No explicit source viewBox.';map.entries[e.id]=result;continue;}
   const box=vb[1].split(/[ ,]+/).map(Number);
   const {data,info}=await sharp(source,{density:96}).resize({width:1400}).flatten({background:'#ffffff'}).removeAlpha().raw().toBuffer({resolveWithObject:true});
   let minX=info.width,minY=info.height,maxX=-1,maxY=-1;
   for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++){
    const i=(y*info.width+x)*info.channels;
    if(Math.min(data[i],data[i+1],data[i+2])<253){minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);}
   }
   if(maxX<0){result.status='original_retained';result.reason='No visible chemical ink.';map.entries[e.id]=result;continue;}
   const x=box[0]+minX/info.width*box[2],y=box[1]+minY/info.height*box[3];
   const w=(maxX-minX+1)/info.width*box[2],h=(maxY-minY+1)/info.height*box[3];
   const pad=Math.max(14,Math.min(w,h)*.075);
   const crop=[x-pad,y-pad,w+2*pad,h+2*pad].map(v=>Number(v.toFixed(4)));
   let root=start.replace(/viewBox="[^"]+"/,`viewBox="${crop.join(' ')}"`)
      .replace(/\bwidth="[^"]+"/,`width="${crop[2]}"`).replace(/\bheight="[^"]+"/,`height="${crop[3]}"`);
   const newxml=xml.replace(start,root);const local='svg/'+e.id+'.svg',out=path.join(P,local);
   fs.writeFileSync(out,newxml);
   // The body of the entire isolated chemical drawing is byte-identical; only root
   // viewport attributes changed. No chemical node is reconstructed or edited.
   if(newxml.replace(root,'')!==xml.replace(start,''))throw Error('Chemical body mutation '+e.id);checks++;
   const preview='previews/'+e.id+'.png';
   await sharp(out,{density:144}).resize(300,180,{fit:'contain',background:'#ffffff'}).flatten({background:'#ffffff'}).png().toFile(path.join(P,preview));
   Object.assign(result,{status:'compact',reason:'Original molecular drawing preserved; outer plate prose omitted and viewBox padded around visible drawing.',
    thumbnail_path:'assets/chemical-thumbnails/'+e.id+'.svg',proposal_path:local,thumbnail_sha256:hash(out),
    source_container_path:e.container_path,source_container_sha256:e.container_sha256,selection:e.selection,
    source_viewbox:box,thumbnail_viewbox:crop,chemical_signature_sha256:e.chemical_signature_sha256,
    chemical_element_count:e.chemical_element_count,chemical_body_byte_identical:true,
    original_to_compact_area_ratio:Number((box[2]*box[3]/(crop[2]*crop[3])).toFixed(3)),
    preview_path:preview,preview_sha256:hash(path.join(P,preview))});
   converted.push({id:e.id,...result});
  }
  map.entries[e.id]=result;
 }
 const contacts=[];
 for(let page=0;page<Math.ceil(converted.length/40);page++){
  const items=converted.slice(page*40,(page+1)*40),layers=[];
  for(let i=0;i<items.length;i++){
   const x=(i%4)*300,y=Math.floor(i/4)*210;
   layers.push({input:path.join(P,items[i].preview_path),left:x,top:y});
   layers.push({input:Buffer.from(`<svg width="300" height="30" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="30" fill="#edf3f7"/><text x="5" y="18" font-family="Arial" font-size="10" fill="#18374c">${escape(items[i].id)}</text></svg>`),left:x,top:y+180});
  }
  const file=`contacts/contact-${page+1}.png`;
  await sharp({create:{width:1200,height:Math.ceil(items.length/4)*210,channels:3,background:'#ffffff'}}).composite(layers).png().toFile(path.join(P,file));
  contacts.push({path:file,sha256:hash(path.join(P,file)),entry_ids:items.map(x=>x.id)});
 }
 map.counts={registry_entries:manifest.entries.length,compact:converted.length,original_retained:manifest.entries.length-converted.length};
 fs.writeFileSync(path.join(P,'thumbnail-map.json'),JSON.stringify(map,null,2)+'\n');
 fs.writeFileSync(path.join(P,'render-validation.json'),JSON.stringify({status:'passed',checks,counts:map.counts,
  renderer:'Installed Sharp/libvips SVG renderer; visible-ink bounds at 1400 px width, at least 14 source-unit padding.',
  chemical_transformation:'None: exact drawing-container body retained; only SVG root viewport/size changes.',
  contacts,manual_visual_review:'pending'},null,2)+'\n');
 console.log(JSON.stringify(map.counts));console.log('map sha256',hash(path.join(P,'thumbnail-map.json')));
}
main().catch(e=>{console.error(e);process.exit(1)});
