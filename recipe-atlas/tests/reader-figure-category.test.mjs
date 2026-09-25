import test from 'node:test';
import assert from 'node:assert/strict';
import {figureMatchesCategory} from '../static/reader-utils.mjs';

test('reviewed optical figures remain visible in the property gallery',()=>{
 assert.equal(figureMatchesCategory({category:'optical'},'property'),true);
 assert.equal(figureMatchesCategory({categories:['optical']},'property'),true);
 assert.equal(figureMatchesCategory({category:'properties'},'property'),true);
 assert.equal(figureMatchesCategory({category:'optical'},'structure'),false);
});
test('composition remains a structure figure and multi-category figures retain both views',()=>{
 assert.equal(figureMatchesCategory({category:'composition'},'structure'),true);
 assert.equal(figureMatchesCategory({category:'composition'},'property'),false);
 const both={category:'structure',categories:['property']};
 assert.equal(figureMatchesCategory(both,'structure'),true);
 assert.equal(figureMatchesCategory(both,'property'),true);
});
test('uncategorized and unrelated figures are not promoted',()=>{
 assert.equal(figureMatchesCategory({},'property'),false);
 assert.equal(figureMatchesCategory({category:'precursor'},'property'),false);
 assert.equal(figureMatchesCategory({category:'other'},'structure'),false);
});
