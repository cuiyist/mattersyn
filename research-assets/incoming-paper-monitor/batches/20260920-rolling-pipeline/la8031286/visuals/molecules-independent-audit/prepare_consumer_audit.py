from pathlib import Path
A=Path(__file__).resolve().parent;V=A.parent/'molecules';N=A.parents[1];M=N.parents[4]
s=(V/'check_consumer.mjs').read_text('utf8')
s=s.replace("const O=path.dirname(fileURLToPath(import.meta.url)),A=O,P=path.join(A,'../..');", "const O=path.dirname(fileURLToPath(import.meta.url)),A=path.join(O,'../molecules'),P=path.join(A,'../..');\n// Independently executed adapted harness; initial minimal-DOM scaffolding came from the author.\n// Current Site consumer and extra keyboard/fallback/close/immutability tests are auditor-selected.")
s=s.replace("canonical-proposal/v1/record-manifest.json", "canonical-proposal/v2/record-manifest.json")
s=s.replace("const modulePath=path.join(A,'reference-snapshots/chemical-viewer.mjs');", "const snapshotPath=path.join(A,'reference-snapshots/chemical-viewer.mjs');\nconst modulePath="+repr(str(M/'recipe-atlas/dist/chemical-viewer.mjs').replace('[local path redacted] current viewer exactly equals frozen consumer');")
s=s.replace("'Author test source context for '","'Independent audit source context for '")
s=s.replace("ck(currentViewer.calls.some(x=>Array.isArray(x)&&x[0]==='zoom'&&x[1]===1.2),'Zoom dispatch');", """ck(currentViewer.calls.some(x=>Array.isArray(x)&&x[0]==='zoom'&&x[1]===1.2),'Zoom dispatch');
  const host=walk(dialog).find(x=>x.className==='molecule-model');
  for(const [key,expected]of Object.entries({ArrowLeft:[-12,'y'],ArrowRight:[12,'y'],ArrowUp:[-12,'x'],ArrowDown:[12,'x']})){
   let prevented=false;const offset=currentViewer.calls.length;host.onkeydown({key,preventDefault(){prevented=true;}});
   ck(prevented&&currentViewer.calls.slice(offset).some(x=>eq(x,['rotate',...expected])),'Keyboard rotation '+e.id+'/'+key);
  }
  let prevented=false;host.onkeydown({key:'Home',preventDefault(){prevented=true;}});ck(prevented,'Keyboard fit '+e.id);
  const n=currentViewer.calls.length;host.onkeydown({key:'a',preventDefault(){throw Error('Other key intercepted');}});ck(currentViewer.calls.length===n,'Unrelated key ignored');""")
s=s.replace("dialogs++;", "dialogs++;")
s=s.replace("\nfunction examineSelector", "\n// Reopen a symbolic item after the 3D sequence, ensuring no retained atom scene.\ncurrentViewer=null;const symbolic=[...entries.values()].find(e=>!e.model2dPath&&!e.model3dPath);await api.openChemical(symbolic);ck(currentViewer===null,'Symbolic view after molecular sequence creates no atomic model');\nconst lastDialog=document.body.children[0];walk(lastDialog).find(x=>x.tagName==='button'&&x.textContent==='Close ×').onclick();ck(lastDialog.open===false,'Close handler works');\nfunction examineSelector")
s=s.replace("schema:'mattersyn-author-molecule-consumer-checks/1',independent_approval:false,author:'/root/peng1998_reader_assets'", "schema:'mattersyn-independent-molecule-consumer-checks/1',independent_approval:false,auditor:'/root/norberg2004_extract',scaffolding:'Adapted author minimal-DOM fixture; independently executed against current Site consumer with added keyboard, close, post-3D symbolic fallback, exact-current-consumer and v2-record checks.'")
s=s.replace("path.join(O,'consumer-checks.json')", "path.join(O,'consumer-checks-v1.json')")
(A/'check_consumer_independent.mjs').write_text(s,'utf8')
print('Prepared independent consumer audit helper only.')
