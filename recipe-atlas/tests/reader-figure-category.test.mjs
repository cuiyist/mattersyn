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

test('reviewed plural structure categories work in singular and array fields',()=>{
 assert.equal(figureMatchesCategory({category:'structures'},'structure'),true);
 assert.equal(figureMatchesCategory({categories:['structures']},'structure'),true);
 assert.equal(figureMatchesCategory({category:'structure'},'structures'),true);
 assert.equal(figureMatchesCategory({category:'structures',categories:['structure']},'structure'),true);
});
test('plural structure labels do not imply property or unrecognized categories',()=>{
 assert.equal(figureMatchesCategory({category:'structures'},'property'),false);
 assert.equal(figureMatchesCategory({categories:['structures']},'properties'),false);
 assert.equal(figureMatchesCategory({category:'structure'},'structural'),false);
 assert.equal(figureMatchesCategory({categories:['unknown','structure-ish','Structure']},'structure'),false);
 assert.equal(figureMatchesCategory({categories:'structures'},'structure'),false);
});
test('plural structure and explicit property co-classification preserves both galleries',()=>{
 const fig={category:'structures',categories:['optical','unknown']};
 const original=structuredClone(fig);
 assert.equal(figureMatchesCategory(fig,'structure'),true);
 assert.equal(figureMatchesCategory(fig,'property'),true);
 assert.deepEqual(fig,original);
 assert.equal(figureMatchesCategory({},'structure'),false);
 assert.equal(figureMatchesCategory({category:'unknown'},'structure'),false);
});
