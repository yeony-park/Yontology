import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const app=fs.readFileSync(new URL('../viewer/app.js',import.meta.url),'utf8');
test('type filters retain only requested kinds; shared variables require two distinct function users',()=>{
  const graph={nodes:[{id:'file:a',kind:'file',file:'a.py'},{id:'C',kind:'class',file:'a.py',parent:'file:a'},{id:'f',kind:'method',file:'a.py',parent:'C'},{id:'g',kind:'function',file:'b.py'}, {id:'v',kind:'variable',file:'a.py',parent:'file:a'},{id:'local',kind:'variable',parent:'f'},{id:'single',kind:'variable',parent:'file:a'}],edges:[
    {source:'f',target:'v',kind:'reads'},{source:'g',target:'v',kind:'writes'},
    {source:'f',target:'local',kind:'reads'},{source:'g',target:'local',kind:'reads'},
    {source:'f',target:'single',kind:'reads'},{source:'f',target:'single',kind:'writes'}]};
  const context=vm.createContext({graph,index:new Map(graph.nodes.map(n=>[n.id,n]))});
  vm.runInContext(`let nodeType='all';const functionKinds=new Set(['function','method','component','test']),sharingCache=new WeakMap();${app.slice(app.indexOf('  function moduleVariable('),app.indexOf('  let transform'))}`,context);
  const run=code=>JSON.parse(vm.runInContext(`JSON.stringify(${code})`,context));
  assert.deepEqual(run('[...sharedVariables().keys()]'),['v']);
  assert.deepEqual(run("[...sharedVariables().get('v').get('g')]"),['writes']);
  vm.runInContext("nodeType='classes'",context);assert.deepEqual(run('graph.nodes.filter(typeMatches).map(n=>n.id)'),['C']);
  vm.runInContext("nodeType='functions'",context);assert.deepEqual(run('graph.nodes.filter(typeMatches).map(n=>n.id)'),['f','g']);
  vm.runInContext("nodeType='globals'",context);assert.deepEqual(run('graph.nodes.filter(typeMatches).map(n=>n.id)'),['v','single']);
});
test('layout groups nodes by owning file and preserves positions during expansion',()=>{
  const context=vm.createContext({});
  vm.runInContext(`const COLUMN=370,ROW=450;const nodes=[{id:'a',file:'one.py'},{id:'b',file:'two.py'},{id:'c',file:'one.py'}];const index=new Map(nodes.map(n=>[n.id,n]));const positions=new Map();${app.slice(app.indexOf('  function placeNodes('),app.indexOf('  function renderTree('))}placeNodes(nodes,[]);`,context);
  const positions=JSON.parse(vm.runInContext('JSON.stringify([...positions])',context));
  assert.equal(positions[0][1].x,positions[2][1].x);assert.notEqual(positions[0][1].x,positions[1][1].x);
  assert.ok(positions[2][1].y>positions[0][1].y);
});
