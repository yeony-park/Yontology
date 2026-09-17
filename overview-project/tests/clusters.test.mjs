import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const app=fs.readFileSync(new URL('../viewer/app.js',import.meta.url),'utf8');
const functions=app.slice(app.indexOf('  function clusterKey('),app.indexOf('  function renderClusters('));
function cluster(graph){return vm.runInNewContext(functions+'; clusters();',{graph,index:new Map(graph.nodes.map(n=>[n.id,n]))});}
test('folder ownership, dependency adjacency, and tests attached by real references',()=>{
  const graph={nodes:[
    {id:'f',kind:'file',file:'ui/app.ts'}, {id:'a',kind:'function',file:'ui/app.ts'},
    {id:'b',kind:'function',file:'core/service.ts'},
    {id:'t',kind:'file',file:'tests/app.test.ts',test:true},
    {id:'test',kind:'test',file:'tests/app.test.ts',test:true},
    {id:'u',kind:'function',file:'unrelated/tool.ts'}
  ],edges:[{source:'a',target:'b',kind:'calls'},{source:'test',target:'a',kind:'tests'}]};
  const result=cluster(graph),ui=result.find(g=>g.key==='ui');
  assert.deepEqual(Array.from(ui.nodes,n=>n.id),['f','a','t','test']);
  assert.equal(ui.links.get('core').size,1);
  assert.equal(Math.abs(result.findIndex(g=>g.key==='ui')-result.findIndex(g=>g.key==='core')),1);
  assert.equal(result.flatMap(g=>Array.from(g.nodes)).length,graph.nodes.length);
});
test('unresolved tests keep their folder and duplicate links do not inflate counts',()=>{
  const graph={nodes:[{id:'a',file:'a/app.ts',kind:'function'},{id:'b',file:'b/lib.ts',kind:'function'},{id:'t',file:'tests/unknown.ts',kind:'file',test:true}],edges:[{source:'a',target:'b',kind:'calls'},{source:'a',target:'b',kind:'calls'}]};
  const result=cluster(graph);
  assert.equal(result.find(g=>g.key==='a').links.get('b').size,1);
  assert.ok(result.find(g=>g.key==='tests').nodes.some(n=>n.id==='t'));
  assert.deepEqual(Array.from(result,g=>g.key),Array.from(cluster(graph),g=>g.key));
});
