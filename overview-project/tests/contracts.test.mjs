import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {scan,exportHTML} from '../cli/storage.mjs';

test('local shadowing is not reported as shared module state',t=>{
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'overview-scopes-'));
  t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  fs.writeFileSync(path.join(root,'state.py'),'STATE = 1\ndef read():\n    return STATE\ndef local(STATE):\n    return STATE\ndef write():\n    global STATE\n    STATE = 2\n');
  fs.writeFileSync(path.join(root,'state.ts'),'const STATE = 1; function read(){return STATE;} function local(STATE:number){return STATE;} function write(){STATE = 2;} (()=>{const HIDDEN=1;})();');
  const {graph}=scan(root);
  for(const file of ['state.py','state.ts']){
    assert.ok(graph.edges.some(e=>e.source===file+'::read'&&e.target===file+'::STATE'&&e.kind==='reads'));
    assert.ok(graph.edges.some(e=>e.source===file+'::write'&&e.target===file+'::STATE'&&e.kind==='writes'));
    assert.ok(!graph.edges.some(e=>e.source===file+'::local'&&e.target===file+'::STATE'));
  }
  assert.equal(graph.nodes.find(n=>n.id==='state.ts::HIDDEN').moduleLevel,false);
});

test('function blocks include declared inputs, own returns, docs, code and call arguments',t=>{
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'overview-contracts-'));
  t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  fs.writeFileSync(path.join(root,'calc.py'),`def normalize(value: str, limit: int = 8) -> str:
    """Trim a name to the requested length."""
    def nested():
        return 'NOT_OUTER'
    return value.strip()[:limit]

def register(raw):
    return normalize(raw, limit=4)
`);
  fs.writeFileSync(path.join(root,'calc.ts'),`/** Trim a name. */
export function normalize(value: string, limit = 8): string {
  function nested(){ return 'NOT_OUTER'; }
  return value.trim().slice(0, limit);
}
export const register = (raw: string) => normalize(raw, 4);
`);
  const {graph}=scan(root);
  assert.equal(graph.diagnostics.length,0);
  for(const file of ['calc.py','calc.ts']){
    const fn=graph.nodes.find(n=>n.id===file+'::normalize');
    assert.equal(fn.contract.parameters[0].name,'value');
    assert.equal(fn.contract.parameters[1].default,'8');
    assert.equal(fn.contract.returns.length,1);
    assert.ok(!fn.contract.returns[0].expression.includes('NOT_OUTER'));
    assert.ok(fn.contract.documentation.includes('Trim a name'));
    assert.ok(fn.code.includes('NOT_OUTER'));
    assert.equal(fn.codeTruncated,false);
    const call=graph.edges.find(e=>e.source===file+'::register'&&e.target===fn.id&&e.kind==='calls');
    assert.equal(call.call.arguments[0],'raw');
    assert.ok(call.call.expression.includes('normalize'));
  }
  assert.equal(graph.nodes.find(n=>n.id==='calc.ts::register').contract.returns[0].expression,'normalize(raw, 4)');
  assert.ok(exportHTML(graph).includes('function-block'));
});
