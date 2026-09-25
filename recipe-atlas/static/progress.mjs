const $=id=>document.getElementById(id);

const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);if(cls)n.className=cls;return n;};

const number=v=>new Intl.NumberFormat().format(v);

const date=v=>{const d=new Date(v);if(!v||Number.isNaN(d.getTime()))return 'Timestamp not recorded';return new Intl.DateTimeFormat(undefined,/^\d{4}-\d{2}-\d{2}$/.test(v)?{dateStyle:'medium',timeZone:'UTC'}:{dateStyle:'medium',timeStyle:'short'}).format(d);};

const statusNames={complete:'Complete within stated scope',in_progress:'In progress',pending:'Pending',paused:'Paused'};

function safeLink(label,path){const a=el('a',label);const url=new URL(path,import.meta.url);if(url.origin!==location.origin||!url.pathname.startsWith(new URL('.',import.meta.url).pathname))throw Error('Unexpected progress link');a.href=url.href;return a;}

function metrics(host,items){host.replaceChildren(...items.map(([value,label])=>{const n=el('div',undefined,'progress-metric');n.append(el('strong',number(value)),el('span',label));return n;}));}

function render(data){

 const paused=['paused_for_joint_review','trial_finished_awaiting_user_review'].includes(data.estimate?.status);
 if($('review-progress-brief')){$('review-progress-brief').textContent=paused?'Curation is paused for review. Completed contributions are published; unfinished work is retained.':data.current_work.length?`${data.current_work[0].short_label}: ${data.current_work[0].stage.replace(/\.+$/,'')}.`:'No paper is currently under review.';$('review-progress-time').textContent=`Snapshot generated ${date(data.updated_at)} · checked for updates every minute`;}
 if(!$('published-metrics'))return;

 $('progress-updated').textContent=`Snapshot generated ${date(data.updated_at)} · automatic update check every minute`;
 const overall=data.whole_corpus_progress;
 if($('stage-progress')){
  const host=$('stage-progress');host.replaceChildren();
  if(overall){
   $('stage-denominator').textContent=`Entire fixed existing collection: ${number(overall.denominator)} distinct main-article/SI document contents, from ${number(overall.original_file_copies)} file copies. New arrivals are separate. Exact duplicates count once. Percentages below use this same collection-wide denominator.`;
   for(const stage of overall.stages){
    const card=el('article',undefined,'stage-card');
    card.append(el('h3',stage.label),el('strong',`${stage.count_is_lower_bound?'At least ':''}${stage.percent.toFixed(2)}%`,'stage-percent'),el('p',`${number(stage.completed)} / ${number(stage.total)} documents`));
    const bar=el('progress');bar.max=stage.total;bar.value=stage.completed;bar.setAttribute('aria-label',stage.label+' across the fixed collection');card.append(bar,el('p',stage.definition,'progress-note'));
    const elapsed=stage.elapsed_active_hours===null?'Not recorded for earlier work':`${stage.elapsed_active_hours.toFixed(2)} hours in latest measured window`;
    const remaining=stage.remaining_active_hours===null?'Not yet calibrated':`About ${Math.round(stage.remaining_active_hours)} active hours (provisional)`;
    const timing=el('dl',undefined,'stage-timing');timing.append(el('dt','Measured elapsed'),el('dd',elapsed),el('dt','Estimated remaining'),el('dd',remaining));card.append(timing);
    if(stage.latest_window)card.append(el('p',stage.latest_window,'progress-note'));
    host.append(card);
   }
   $('stage-time-note').textContent=overall.count_basis+' '+overall.time_note;
   $('stage-remaining-note').textContent=overall.remaining_note;
  }else host.append(el('p','Whole-collection counts are being reconciled.'));
 }
 const p=data.published;metrics($('published-metrics'),[[p.record_count,'Structured records'],[p.synthesis_route_count,'Synthesis routes / variants'],[p.material_hub_count,'Material / component collections'],[p.formal_source_reader_count,'Formal source readers']]);
 $('published-detail').textContent=`Dataset ${p.dataset_version} · ${p.direct_material_hub_count} direct material systems and ${p.component_material_hub_count} component collections. Records include procedures, observations and benchmark rows; they are not independent experiments. Exact structure–recipe pairs: ${p.exact_structure_recipe_count}.`;
 const t=data.daily_throughput;if(t){metrics($('throughput-metrics'),[[t.target_papers_per_day,'Paper contributions required per day'],[t.completed_papers_today,'Fully verified contributions today'],[t.deployed_pending_closeout,'Deployed; closeout still pending']]);$('throughput-detail').textContent=t.counting_rule;$('throughput-evidence').textContent=`Measured publication window: ${t.observed_pipeline.papers} completed papers over ${t.observed_pipeline.elapsed_hours.toFixed(2)} elapsed hours (${t.observed_pipeline.papers_per_hour.toFixed(2)}/hour; about ${t.observed_pipeline.arithmetic_per_24h.toFixed(1)}/day by arithmetic only). ${t.observed_pipeline.scope_note||'This selected observation is not a forecast.'} The 500/day target is ${t.observed_pipeline.target_gap_factor.toFixed(1)}× higher than that measured cadence. ${t.capacity_note} ${t.machine_stage_note}`;}
 $('batch-count').textContent=`${data.batch.published} / ${data.batch.total} papers published`;

 $('batch-list').replaceChildren(...data.batch.papers.map(paper=>{const n=el('article',undefined,'batch-card '+(paper.published?'complete':'pending'));n.append(el('span',paper.published?'Published':'In preparation','state-label'));n.append(paper.href?safeLink(paper.label,paper.href):el('strong',paper.label));n.append(el('small',paper.scope));return n;}));

 $('current-work').replaceChildren(...data.current_work.map(work=>{const n=el('article',undefined,'work-card');n.append(el('span',work.short_label,'eyebrow'),el('h3',work.title),el('p',work.stage,'work-current'),el('p',work.summary));const stages=el('ol',undefined,'work-stages');for(const stage of work.stages||[]){const item=el('li',undefined,stage.status);item.append(el('strong',stage.label),el('small',statusNames[stage.status]||stage.status),el('small',stage.detail));stages.append(item);}n.append(stages);if(work.gaps?.length){const details=el('details',undefined,'source-gaps');details.append(el('summary','Unresolved source details retained in the record'));const list=el('ul');work.gaps.forEach(g=>list.append(el('li',g)));details.append(list);n.append(details);}return n;}));

 if(paused&&!data.current_work.length)$('current-work').append(el('p','Curation is paused until you ask to resume. Completed and unfinished work retain separate status.','work-current'));
 const c=data.corpus;metrics($('queue-metrics'),[[c.present_files,'Document copies in both local collections'],[c.canonical_review_units,'Provisional review scopes'],[c.waiting_review_scopes,'Waiting review scopes'],[c.active_review_claims,'Active paper claims']]);
 if($('workflow-summary')){const w=data.workflow,host=$('workflow-summary');host.replaceChildren();if(w){host.append(el('p',w.summary),el('p',w.screening_scope,'progress-note'));const list=el('ol');for(const step of w.steps)list.append(el('li',step));host.append(list,el('p',w.capacity,'progress-note'),el('p',w.paid_processing,'progress-note'));}else{host.append(el('p','Workflow snapshot pending.'));}}
 $('corpus-note').textContent=`Last corpus scan: ${date(data.corpus_scanned_at)}. ${data.count_note} Incoming collection: ${number(c.source_document_copies.incoming)} copies; original collection: ${number(c.source_document_copies.legacy)} copies.`;

 $('queue-policy').textContent=`Priority: ${data.priority} Papers without synthesis content can be excluded after an evidenced independent screening check.`;

 const estimate=$('completion-estimate');estimate.replaceChildren(el('p',data.estimate.summary));if(data.estimate.current_batch)estimate.append(el('p',data.estimate.current_batch));

 if(data.estimate.scenarios?.length){const wrap=el('div',undefined,'estimate-table-wrap'),table=el('table'),head=el('thead'),tr=el('tr');for(const h of ['Scenario','Completed review scopes / day','Frozen backlog duration'])tr.append(el('th',h));head.append(tr);table.append(head);const body=el('tbody');for(const row of data.estimate.scenarios){const r=el('tr');r.append(el('td',row.label),el('td',row.reviews_per_day),el('td',row.duration));body.append(r);}table.append(body);wrap.append(table);estimate.append(wrap);}

 for(const note of data.estimate.notes||[])estimate.append(el('p',note,'progress-note'));

 $('milestone-list').replaceChildren(...data.recent_milestones.map(m=>{const li=el('li'),time=el('time',date(m.at||m.date));if(m.at||m.date)time.dateTime=m.at||m.date;li.append(time,el('p',m.text));return li;}));$('update-policy').textContent=data.update_policy;

}

let last='',running=false;

async function refresh(){if(running||document.hidden)return;running=true;try{const url=new URL('data/review-progress.json',import.meta.url);url.searchParams.set('snapshot',String(Math.floor(Date.now()/60000)));const response=await fetch(url,{cache:'no-store'});if(!response.ok)throw Error('Progress request failed');const data=await response.json();if(data.updated_at!==last||$('review-progress-time')?.dataset.snapshotLabel){render(data);last=data.updated_at;}if($('progress-error'))$('progress-error').textContent='';if($('review-progress-time'))delete $('review-progress-time').dataset.snapshotLabel;}catch{const warning='Latest update unavailable; showing the dated published snapshot. Retrying automatically.';if($('progress-error'))$('progress-error').textContent=warning;if($('review-progress-time')){const node=$('review-progress-time');node.dataset.snapshotLabel ||= node.textContent.replace(/ · Latest update unavailable.*$/, '');node.textContent=node.dataset.snapshotLabel+' · '+warning;}}finally{running=false;}}

refresh();setInterval(refresh,60000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});

