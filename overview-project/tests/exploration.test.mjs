import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const app=fs.readFileSync(new URL('../viewer/app.js',import.meta.url),'utf8');
test('selecting json retains serve callers, coordinates and viewport; expansion only adds nodes',()=>{
  const context=vm.createContext({});
  vm.runInContext(`
    const graph={nodes:['server','test','serve','json','encode'].map(id=>({id,name:id,kind:'function',file:'server.js'})),edges:[
      {source:'server',target:'serve',kind:'calls'}, {source:'test',target:'serve',kind:'tests'},
      {source:'serve',target:'json',kind:'calls'}, {source:'json',target:'encode',kind:'calls'}]};
    const index=new Map(graph.nodes.map(n=>[n.id,n]));
    let selected=null,focused=false,mode='symbols',query='',relation='all',activeCluster=null,anchor=null;
    let explored=new Set(),positions=new Map(),transform={x:12,y:34,scale:1.4},fitCalls=0;
    const COLUMN=370,ROW=450,codeOpened=new Set();let inspectorOpen=false;
    let nodeType='all',expansionNotice='';const functionKinds=new Set(['function','method','component','test']),sharingCache=new WeakMap();
    ${app.slice(app.indexOf('  function moduleVariable('),app.indexOf('  let transform'))}
    const $=()=>({value:''}); const renderTree=()=>{},render=()=>{},details=()=>{},fit=()=>{fitCalls++};
    ${app.slice(app.indexOf('  function choose('),app.indexOf('  function renderTree('))}
    ${app.slice(app.indexOf('  function visible('),app.indexOf('  function render()'))}
    choose('serve',true);let first=visible();placeNodes(first.candidates,first.edges);
    const before=JSON.stringify([...positions]);const viewport=JSON.stringify(transform);
    choose('json',true);let after=visible();placeNodes(after.candidates,after.edges);
    const selectionResult={ids:after.candidates.map(n=>n.id),samePositions:before===JSON.stringify([...positions]),sameViewport:viewport===JSON.stringify(transform),fitCalls,anchor};
    expandConnections('json');let expanded=visible();placeNodes(expanded.candidates,expanded.edges);
    const expansionResult={ids:expanded.candidates.map(n=>n.id),oldPositions:JSON.stringify([...positions].filter(([id])=>id!=='encode'))===before,edges:expanded.edges.length};
    expansionResult.remaining=expansionCount('json');expansionResult.notice=expansionNotice;
  `,context);
  const result=JSON.parse(vm.runInContext('JSON.stringify({selectionResult,expansionResult})',context));
  assert.deepEqual(result.selectionResult.ids,['server','test','serve','json']);
  assert.equal(result.selectionResult.samePositions,true);
  assert.equal(result.selectionResult.sameViewport,true);
  assert.equal(result.selectionResult.fitCalls,1);
  assert.equal(result.selectionResult.anchor,'serve');
  assert.deepEqual(result.expansionResult.ids,['server','test','serve','json','encode']);
  assert.equal(result.expansionResult.oldPositions,true);
  assert.equal(result.expansionResult.edges,4);
  assert.equal(result.expansionResult.remaining,0);
  assert.match(result.expansionResult.notice,/1개 노드 추가됨/);
});
