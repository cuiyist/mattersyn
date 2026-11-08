// Reader layout only. Native geometry is illustrative; facts/records stay untouched.
export const PROTOCOL_SCENE_CAPTION='Schematic: vessel shapes and colors are illustrative.';
export function protocolPresentationPolicy(_record,{protectedPerPaper=false,protectedCaption='',hasDrawing=true}={}){
  return {caption:protectedPerPaper&&protectedCaption?protectedCaption:PROTOCOL_SCENE_CAPTION,enlarge:Boolean(hasDrawing)};
}
const finite=value=>typeof value==='number'&&Number.isFinite(value)&&value>=0;
export const protocolArtHeight=width=>width<=700?320:400;
export function compactDrawingFacts(original,spec,conditions=[],options={}){
  const facts={...original,added:original.added.map(x=>({...x})),sources:original.sources.map(x=>({...x,lines:[...x.lines]})),durations:[...original.durations],flowHeaterTemperatures:[...original.flowHeaterTemperatures],substrateLabels:[...original.substrateLabels]},fullFacts=[];
  if(!options.fallback)return {facts,fullFacts};
  const full=(label,value,callout)=>{if(!value)return;const marker=callout||label+' ↗',existing=fullFacts.find(x=>x.label===label&&x.value===value);if(existing){if(!existing.callouts.includes(marker))existing.callouts.push(marker);return;}fullFacts.push({label,value,callout:marker,callouts:[marker]});};
  for(const c of conditions)if(c.drawingValue&&c.drawingValue!==c.value)full(c.key.replaceAll('_',' '),c.value,c.drawingValue+' ↗');
  facts.added=facts.added.map((item,index)=>{if(item.label.length<=24&&!options.minimalLabels)return item;const formula=spec.addedFormulas?.[item.index??index];if(formula&&formula.length<=24&&!options.minimalLabels)return {...item,label:formula};const label='Input '+(index+1);full(label,spec.added[item.index??index]||item.label);return {...item,label:label+' ↗'};});
  if(facts.atmosphere.length>32){full('Atmosphere',facts.atmosphere);facts.atmosphere='Atmosphere ↗';}
  facts.sources=facts.sources.map((source,index)=>{
    const short=source.label.length<=14&&facts.sources.length<8;
    const shortName=short&&!options.minimalLabels;
    const label=shortName?source.label:'S'+(index+1)+' ↗';
    if(!shortName)full('Source '+(index+1),source.label,label);
    if(source.lines.length>1||source.lines.some(line=>line.length>18)){const marker='Source '+(index+1)+' details ↗';full(label,source.lines.join('; '),marker);return {...source,label,lines:[marker]};}
    return {...source,label};
  });
  if(facts.durations.length>2||facts.durations.reduce((n,c)=>n+c.value.length,0)>32){for(const c of facts.durations)full(c.key.replaceAll('_',' '),c.value,'Full duration cards ↗');facts.durations=[{key:'duration',value:'Full duration cards ↗'}];}
  if(facts.flowHeaterTemperatures.length){for(const c of facts.flowHeaterTemperatures)full(c.key.replaceAll('_',' '),c.value,'Full temperature cards ↗');facts.flowHeaterTemperatures=[{key:'temperature',value:'Full temperature cards ↗'}];}
  if(facts.substrateLabels.join('; ').length>32){for(const value of facts.substrateLabels)full('Substrate',value);facts.substrateLabels=['Substrate ↗'];}
  return {facts,fullFacts};
}

export function wireDrawingCallouts(host,facts,prefix){
  const safe=String(prefix||'step').replace(/[^A-Za-z0-9_-]/g,'-');
  facts.forEach((fact,index)=>{fact.id='protocol-fact-'+safe+'-'+index;});
  if(typeof host.querySelectorAll!=='function')return;
  for(const leaf of host.querySelectorAll('span,strong,dd,p')){
    if(leaf.children.length||!leaf.textContent.includes('↗'))continue;
    const value=leaf.textContent,matches=facts.flatMap(f=>(f.callouts||[f.callout]).filter(Boolean).map(callout=>({...f,callout}))).filter(f=>value.includes(f.callout));if(!matches.length)continue;
    const targets=[...new Map(matches.map(f=>[f.callout,f])).values()].sort((a,b)=>value.indexOf(a.callout)-value.indexOf(b.callout));
    leaf.replaceChildren();let cursor=0;
    for(const fact of targets){const index=value.indexOf(fact.callout,cursor);if(index<0)continue;if(index>cursor)leaf.append(document.createTextNode(value.slice(cursor,index)));const link=document.createElement('a');link.href='#'+fact.id;link.textContent=fact.callout;link.style.font='inherit';link.style.lineHeight='inherit';leaf.append(link);cursor=index+fact.callout.length;}
    if(cursor<value.length)leaf.append(document.createTextNode(value.slice(cursor)));
  }
}

export function nativeArtMetric(rect,boxes=[]){
  let left=rect.left,top=rect.top,right=rect.right,bottom=rect.bottom;
  for(const box of boxes)if(box.width&&box.height){left=Math.min(left,box.left);top=Math.min(top,box.top);right=Math.max(right,box.right);bottom=Math.max(bottom,box.bottom);}
  return {width:Math.max(1,right-left),height:Math.max(1,bottom-top),baseWidth:rect.width,originX:rect.left-left,originY:rect.top-top};
}
export function fitRecordGeometry(metrics,{width,maxHeight}){
  if(!finite(width)||width<=0||!finite(maxHeight)||maxHeight<=0)throw new TypeError('Positive drawing frame dimensions required');
  let scale=Infinity;
  for(const metric of metrics){
    if(!finite(metric.width)||metric.width<=0||!finite(metric.height)||metric.height<=0||!finite(metric.overhead||0))throw new TypeError('Finite native geometry/annotation metrics required');
    const overhead=metric.overhead||0;
    if(overhead>=maxHeight)throw new RangeError('Annotation overhead leaves no drawing space');
    // The common frame also contains fixed-width padding around the apparatus.
    // Reserve its measured width; scaling SVG geometry never scales labels.
    const horizontal=metric.horizontalOverhead??0;
    if(!finite(horizontal)||horizontal>=width)throw new RangeError('Horizontal annotation/padding overhead leaves no drawing space');
    scale=Math.min(scale,(width-horizontal)/metric.width,(maxHeight-overhead)/metric.height);
  }
  if(!metrics.length)scale=1;
  // A tiny fixed reserve absorbs subpixel rounding, never a font transform.
  scale=Math.max(0,Math.min(scale,1.5))*0.995;
  return {scale,width,maxHeight,metrics:metrics.map(m=>({...m,renderedHeight:(m.overhead||0)+m.height*scale}))};
}

export function createProtocolArtFrame(art,fit={}){
  const frame=document.createElement('div');frame.className='protocol-art-frame';frame.dataset.protocolArtFrame='true';
  Object.assign(frame.style,{position:'relative',width:'100%',minWidth:'0',boxSizing:'border-box',margin:'0 auto',overflow:'clip'});
  if(art?.dataset.renderer==='reported-fields'){
    frame.dataset.scaleKind='shared-svg';frame.append(art);
    if(finite(fit.scale)&&fit.scale>0){frame.dataset.recordGeometryScale=String(fit.scale);frame.style.maxHeight=fit.maxHeight+'px';}
    return frame;
  }
  const native=document.createElement('div');native.dataset.protocolNativeArt='true';native.append(art);
  frame.append(native);frame.dataset.scaleKind='native-art';
  const metric=fit.metric;
  if(metric&&finite(fit.scale)&&fit.scale>0){
    frame.dataset.recordGeometryScale=String(fit.scale);frame.dataset.nativeArtWidth=String(metric.width);frame.dataset.nativeArtHeight=String(metric.height);
    Object.assign(frame.style,{height:metric.height*fit.scale+'px',maxHeight:fit.maxHeight+'px'});
    Object.assign(native.style,{position:'absolute',left:Math.max(0,(fit.width-metric.width*fit.scale)/2)+'px',top:'0',width:metric.width+'px',height:metric.height+'px',transform:`scale(${fit.scale})`,transformOrigin:'0 0'});
    if(art?.style){art.style.width=(metric.baseWidth||metric.width)+'px';art.style.maxWidth='none';art.style.margin='0';art.style.position='relative';art.style.left=(metric.originX||0)+'px';art.style.top=(metric.originY||0)+'px';}
  }
  return frame;
}

// Called only inside a mounted Reader. The same plan is reused by all buttons.
// All-step measurement is a small DOM layout pass, not another site build/read.
export function createRecordFitController({host,operations,createArt,onChange}){
  let plan=null,key='',dead=false,observer=null;
  const watchedImages=new WeakSet();
  const observeImageDimensions=root=>{for(const image of root.querySelectorAll?.('img')||[]){if(image.complete||watchedImages.has(image))continue;watchedImages.add(image);const loaded=()=>{if(dead||!host.isConnected)return;key='';const frame=host.querySelector('.protocol-art-frame');if(frame&&controller.refresh(frame))onChange?.();};image.addEventListener('load',loaded,{once:true});image.addEventListener('error',loaded,{once:true});}};
  const metricsByID=new Map(),modesByID=new Map();
  const controller={
    options(id){return plan?{...plan,metric:metricsByID.get(id),compact:true,...modesByID.get(id)}:{compact:true};},
    refresh(frame){
      if(dead||typeof frame?.getBoundingClientRect!=='function'||typeof host?.append!=='function')return false;
      const width=frame.getBoundingClientRect().width;
      if(!(width>0))return false;
      observeImageDimensions(frame);
      const cap=protocolArtHeight(globalThis.innerWidth||width),nextKey=width.toFixed(2)+'|'+cap;
      if(key===nextKey)return false;
      const scratch=document.createElement('div');scratch.dataset.protocolMeasure='true';
      Object.assign(scratch.style,{position:'fixed',left:'-100000px',top:'0',width:width+'px',visibility:'hidden',pointerEvents:'none',contain:'layout style',boxSizing:'border-box'});
      host.append(scratch);const metrics=[];
      try{
        for(const operation of operations){
          let mode={compact:true,measureOnly:true},art=createArt(operation,mode);if(!art)continue;
          scratch.replaceChildren(art);
          observeImageDimensions(art);
          for(const fallback of [{fallback:true},{fallback:true,minimalLabels:true}]){
            // Fixed-font facts need a real share of the frame. Compact only
            // after measurement shows the full labels consume that share.
            const readableGeometry=art.recordGeometry?Math.min(150,art.recordGeometry.height*0.45):0;
            if(!art.recordGeometry||art.getBoundingClientRect().height+(art.recordGeometry.extraOverhead||0)<cap-readableGeometry)break;
            mode={...mode,...fallback};art=createArt(operation,mode);scratch.replaceChildren(art);
          }
          modesByID.set(operation.id,{fallback:Boolean(mode.fallback),minimalLabels:Boolean(mode.minimalLabels)});
          let metric;
          if(art.recordGeometry){
            const view=art.recordGeometry;
            const panel=art.querySelector?.('.reported-scene-geometry');
            const panelWidth=panel?.getBoundingClientRect().width;
            const horizontalOverhead=Number.isFinite(panelWidth)?Math.max(0,width-panelWidth):0;
            metric={id:operation.id,kind:'shared-svg',width:view.width,height:view.height,horizontalOverhead,overhead:Math.max(0,art.getBoundingClientRect().height)+(view.extraOverhead||0)+2};
          }else{
            const rect=art.getBoundingClientRect(),boxes=[...(art.querySelectorAll?.('*')||[])].map(child=>child.getBoundingClientRect());
            metric={id:operation.id,kind:'native-art',...nativeArtMetric(rect,boxes),overhead:0};
          }
          metrics.push(metric);metricsByID.set(operation.id,metric);
        }
        plan=fitRecordGeometry(metrics,{width,maxHeight:cap});key=nextKey;return true;
      }finally{scratch.remove();}
    },
    disconnect(){dead=true;observer?.disconnect();},
  };
  if(typeof ResizeObserver==='function'&&host?.getBoundingClientRect){
    observer=new ResizeObserver(()=>{if(!dead&&host.isConnected){const frame=host.querySelector('.protocol-art-frame');if(frame&&controller.refresh(frame))onChange?.();}});observer.observe(host);
  }
  if(document.fonts?.ready)document.fonts.ready.then(()=>{if(!dead&&host.isConnected){key='';const frame=host.querySelector('.protocol-art-frame');if(frame&&controller.refresh(frame))onChange?.();}});
  return controller;
}
