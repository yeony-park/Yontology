import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { analyze, inventory } from '../analyzer/index.mjs';
import { scan, exportHTML, readJSON } from '../cli/storage.mjs';
import { serve } from '../cli/server.mjs';
const fixture = fileURLToPath(new URL('./fixtures/sample', import.meta.url));
function sandbox(t) { const root = fs.mkdtempSync(path.join(os.tmpdir(), 'overview-test-')); fs.cpSync(fixture,root,{recursive:true}); t.after(()=>fs.rmSync(root,{recursive:true,force:true})); return root; }

test('Python, TSX, test and style relationships have real node endpoints', t => {
  const root = sandbox(t), { graph } = analyze(root,inventory(root));
  const has = (source,target,kind) => graph.edges.some(e=>e.source===source&&e.target===target&&e.kind===kind);
  assert.equal(graph.diagnostics.length,0);
  assert.ok(has('src/service.py::register','src/service.py::normalize','calls'));
  assert.ok(has('src/service.py::UserService','src/service.py::BaseService','inherits'));
  assert.ok(has('src/service.py::UserService.create','src/service.py::LIMIT','reads'));
  assert.ok(has('tests/test_service.py::test_register','src/service.py::register','tests'));
  assert.ok(has('src/App.tsx::App','src/Button.tsx::Button','renders'));
  assert.ok(has('src/App.tsx::App','src/format.ts::formatName','calls'));
  assert.ok(has('tests/format.test.ts::formats a name','src/format.ts::formatName','tests'));
  assert.ok(has('src/App.tsx::App','utility:flex','styles'));
  assert.ok(has('src/App.tsx::App','src/styles.css::selector:.app','styles'));
  const ids=new Set(graph.nodes.map(n=>n.id));
  assert.equal(ids.size,graph.nodes.length);
  for(const e of graph.edges){assert.ok(ids.has(e.source));assert.ok(ids.has(e.target));}
});

test('local history is independent, deduplicated, tracks edits/deletes and retains newest versions', t => {
  const a=sandbox(t),b=sandbox(t);
  const v1=scan(a,{keep:2});assert.equal(v1.graph.version,1);
  assert.equal(scan(a,{keep:2}).changed,false);
  assert.equal(scan(b).graph.version,1);
  fs.appendFileSync(path.join(a,'src/format.ts'),'\nexport const VALUE = 42;\n');
  const v2=scan(a,{keep:2});assert.equal(v2.graph.version,2);assert.ok(v2.graph.diff.added.includes('src/format.ts::VALUE'));
  fs.unlinkSync(path.join(a,'src/format.ts'));
  const v3=scan(a,{keep:2});assert.equal(v3.graph.version,3);assert.ok(v3.graph.diff.removed.some(n=>n.id==='src/format.ts::VALUE'));
  assert.deepEqual(readJSON(path.join(a,'.overview-project/data/history.json')).map(h=>h.version),[2,3]);
  assert.equal(fs.existsSync(path.join(a,'.overview-project/tmp/snapshots/000001.json')),false);
  assert.equal(scan(b).graph.version,1);
});

test('ignores, symlinks, syntax diagnostics and output recursion', t => {
  const root=sandbox(t);
  fs.writeFileSync(path.join(root,'.gitignore'),'ignored.py\n');
  fs.writeFileSync(path.join(root,'ignored.py'),'secret=1');
  fs.symlinkSync(path.join(root,'src/service.py'),path.join(root,'linked.py'));
  fs.writeFileSync(path.join(root,'broken.py'),'def nope(:');
  const {graph}=scan(root);
  assert.ok(!graph.files.some(f=>/ignored|linked/.test(f.path)));
  assert.ok(graph.diagnostics.some(d=>d.file==='broken.py'));
  assert.ok(inventory(root).files.every(f=>!f.path.startsWith('.overview-project')));
  assert.equal(scan(root).changed,false);
});

test('single HTML embeds a safe payload and no local asset dependencies', t => {
  const root=sandbox(t),{graph}=scan(root);
  graph.project='</script><script>alert(1)</script>';
  const html=exportHTML(graph);
  assert.ok(!html.includes('src="/app.js"'));assert.ok(!html.includes('href="/style.css"'));
  const payload=html.match(/<script id="snapshot-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
  assert.ok(!payload.includes('<'));assert.equal(JSON.parse(payload).project,graph.project);
});

test('live server updates, returns history and denies filesystem traversal and foreign origins', async t => {
  const root=sandbox(t),server=await serve(root,{port:0,interval:100});
  t.after(()=>new Promise(resolve=>server.close(resolve)));
  const url='http://127.0.0.1:'+server.address().port;
  const get=async p=>(await fetch(url+p)).json();
  assert.equal((await get('/api/graph')).version,1);
  fs.appendFileSync(path.join(root,'src/format.ts'),'\nexport function added(){ return 7; }\n');
  let next;
  for(let i=0;i<50;i++){await new Promise(r=>setTimeout(r,100));next=await get('/api/graph');if(next.version===2)break;}
  assert.equal(next.version,2);
  assert.equal((await get('/api/snapshots/1')).version,1);
  assert.equal((await get('/api/history')).length,2);
  assert.equal((await fetch(url+'/../package.json')).status,404);
  assert.equal((await fetch(url+'/api/graph',{headers:{Origin:'https://example.com'}})).status,403);
  assert.equal((await fetch(url+'/api/graph',{method:'POST'})).status,405);
  assert.ok((await (await fetch(url+'/export.html')).text()).includes('snapshot-data'));
  const historical=await (await fetch(url+'/export.html?version=1')).text();
  const payload=historical.match(/<script id="snapshot-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
  assert.equal(JSON.parse(payload).version,1);
  assert.equal((await fetch(url+'/export.html?version=99999')).status,404);
});

test('changes past the source preview still change the symbol hash', t => {
  const root=sandbox(t),file=path.join(root,'long.py');
  const code='def long_function():\n'+Array.from({length:50},(_,i)=>'    x'+i+' = '+i).join('\n')+'\n    return 1\n';
  fs.writeFileSync(file,code);scan(root);
  fs.writeFileSync(file,code.replace('return 1','return 2'));
  const {graph}=scan(root);
  assert.ok(graph.diff.changed.includes('long.py::long_function'));
});
