import test from 'node:test';
import assert from 'node:assert/strict';
import {figureCaptionTexts,appendFigureCaptions} from '../static/figure-captions.mjs';

test('long registered captions remain complete, with no sentence or length truncation',()=>{
 const caption='Synthetic full caption. '+('Long caption detail. '.repeat(100));
 assert.deepEqual(figureCaptionTexts({title:'Figure 1',caption}),[caption.trim()]);
});
test('an explicitly public caption takes precedence and raw quote payloads are not displayed',()=>{
 assert.deepEqual(figureCaptionTexts({public_caption:'Public paraphrase',caption:'Old citation',summary:'Scope',scope:'Scope',quote:'PRIVATE',raw_text:'PRIVATE'}),['Public paraphrase']);
});
test('legacy registered summary captions remain available without inventing a caption',()=>{
 assert.deepEqual(figureCaptionTexts({title:'Figure 2',summary:'Registered source caption'}),['Registered source caption']);
 assert.deepEqual(figureCaptionTexts({title:'Figure 2'}),[]);
});
test('caption and summary duplicates appear once while distinct qualifications remain',()=>{
 assert.deepEqual(figureCaptionTexts({caption:'Caption',summary:'Caption'}),['Caption']);
 assert.deepEqual(figureCaptionTexts({caption:'Caption',summary:'Qualification'}),['Caption','Qualification']);
});
test('cards and enlarged views use the same safe text append interface',()=>{
 const outputs=[];const host={append:node=>outputs.push(node)};
 appendFigureCaptions(host,{caption:'<img onerror=bad>'},(tag,text,cls)=>({tag,text,cls}));
 assert.deepEqual(outputs,[{tag:'p',text:'<img onerror=bad>',cls:'reader-caption-text'}]);
});
