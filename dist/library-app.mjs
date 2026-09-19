const $=id=>document.getElementById(id);let papers=[],page=0;const pageSize=20;
function node(tag,text,cls){const x=document.createElement(tag);if(text)x.textContent=text;if(cls)x.className=cls;return x;}
function render(){
 const query=$('paper-search').value.trim().toLowerCase(),status=$('paper-status').value;
 const matches=papers.filter(p=>(!query||[p.title,p.doi,...p.materials,...p.candidateMaterialMentions||[]].join(' ').toLowerCase().includes(query))&&(!status||p.reviewStatus===status));
 page=Math.min(page,Math.max(0,Math.ceil(matches.length/pageSize)-1));$('paper-count').textContent=matches.length.toLocaleString()+' matching paper groups';const host=$('paper-results');host.replaceChildren();
 for(const p of matches.slice(page*pageSize,(page+1)*pageSize)){
  const card=node('article','', 'paper-contribution');card.append(node('span',p.fullDocumentReview?.label|| (p.reviewStatus==='main_only_reviewed'?'Full main reviewed · SI unverified':p.reviewStatus==='full_documents_reviewed'?'Full main + matched SI reviewed':p.reviewStatus==='selected_recipes_reviewed'?'Selected recipes reviewed':p.reviewStatus==='published_benchmark'?'Published numerical benchmark':'Indexed · detailed review pending'),'atlas-status'));
  const h=node('h3');const a=node('a',p.title||'Title awaiting verification');a.href='paper.html?id='+p.id;h.append(a);card.append(h);
  card.append(node('p',`${p.doi} · ${p.coverage.localDocumentCount??'—'} local document(s) · Main candidate: ${p.coverage.mainDocumentAvailable?'present':'not linked'} · SI candidate: ${p.coverage.supportingDocumentAvailable?'present':'not linked'}`));
  if(p.materials.length)card.append(node('p','Verified synthesis contributions: '+p.materials.join(' · ')));
  else if(p.candidateMaterialMentions?.length)card.append(node('p','Unreviewed title mentions: '+p.candidateMaterialMentions.join(' · ')));
  const links=node('div','','paper-links');const detail=node('a','Inspect source coverage →');detail.href=a.href;const doi=node('a','Publisher source ↗');doi.href=p.doiUrl;links.append(detail,doi);card.append(links);host.append(card);
 }
 if(!matches.length)host.append(node('p','No papers match this search.','atlas-empty'));
 $('paper-page').textContent=`Page ${page+1} of ${Math.max(1,Math.ceil(matches.length/pageSize))}`;$('paper-prev').disabled=page===0;$('paper-next').disabled=(page+1)*pageSize>=matches.length;
}
try{
 const response=await fetch('data/library-index.json',{cache:'no-store'});if(!response.ok)throw Error('Source index is unavailable');const data=await response.json();papers=data.papers;
 const s=data.summary;$('document-total').textContent=(s.sourceDocumentCount||0).toLocaleString();$('paper-total').textContent=data.local_paper_groups.toLocaleString();$('extracted-total').textContent=(s.extractionStatusCounts?.extracted||0).toLocaleString();$('reviewed-total').textContent=papers.filter(p=>p.reviewedRecordIds?.length).length;
 const fully=papers.filter(p=>p.fullDocumentReview),matched=fully.filter(p=>p.fullDocumentReview.scope==='supplied_main_and_matched_si'),mainOnly=fully.filter(p=>p.fullDocumentReview.scope==='supplied_main_only_si_unverified');$('full-review-state').textContent=matched.length+' papers have complete supplied main + matched SI review ('+matched.reduce((n,p)=>n+p.fullDocumentReview.pages,0)+' pages). '+mainOnly.length+' have complete supplied-main review with SI unverified ('+mainOnly.reduce((n,p)=>n+p.fullDocumentReview.pages,0)+' pages). Remaining papers still require full-document review; source omissions and unresolved links remain visible.';
 const states=Object.entries(s.extractionStatusCounts||{}).map(([k,v])=>k.replaceAll('_',' ')+': '+v.toLocaleString()).join(' · ');
 $('corpus-state').textContent=(s.pipelineComplete?'The full-folder indexing pass is complete. ':'The full-folder indexing pass is in progress. ')+states+'. Full text and page-linked evidence candidates are retained locally. Documents requiring conversion or OCR remain listed for follow-up.';
 const params=new URLSearchParams(location.search);$('paper-search').value=params.get('q')||'';render();
 for(const id of ['paper-search','paper-status'])$(id).addEventListener(id==='paper-search'?'input':'change',()=>{page=0;render();});$('paper-prev').addEventListener('click',()=>{page--;render();});$('paper-next').addEventListener('click',()=>{page++;render();});
}catch(e){$('paper-count').textContent=e.message;console.error(e);}
