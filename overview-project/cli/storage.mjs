import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { analyze, inventory, hash, ENGINE } from '../analyzer/index.mjs';

const viewer = fileURLToPath(new URL('../viewer/', import.meta.url));
export const readJSON = (p, fallback = null) => {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); }
  catch (e) { if (e.code === 'ENOENT' || e instanceof SyntaxError) return fallback; throw e; }
};
export function atomic(p, value) {
  const tmp = p + '.' + process.pid + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(value));
  fs.renameSync(tmp, p);
}
export function initialize(root) {
  const base = path.join(root, '.overview-project');
  for (const rel of ['', 'viewer', 'data', 'tmp', 'tmp/cache', 'tmp/snapshots', 'exports']) {
    const p = path.join(base, rel);
    if (fs.existsSync(p) && fs.lstatSync(p).isSymbolicLink()) throw new Error('Output directory cannot be a symlink: ' + p);
    fs.mkdirSync(p, { recursive: true });
  }
  fs.writeFileSync(path.join(base, '.gitignore'), '*\n');
  for (const name of ['index.html', 'app.js', 'style.css']) {
    const target = path.join(base, 'viewer', name);
    if (fs.existsSync(target) && fs.lstatSync(target).isSymbolicLink()) throw new Error('Output file cannot be a symlink');
    fs.copyFileSync(path.join(viewer, name), target);
  }
  return base;
}
export function diffGraph(previous, next) {
  const before = new Map((previous?.nodes || []).map(n => [n.id, n]));
  const after = new Map(next.nodes.map(n => [n.id, n]));
  const oldEdges = new Set((previous?.edges || []).map(e => [e.source, e.target, e.kind].join('|')));
  const newEdges = new Set(next.edges.map(e => [e.source, e.target, e.kind].join('|')));
  return {
    added: [...after.keys()].filter(id => !before.has(id)),
    removed: [...before.values()].filter(n => !after.has(n.id)).map(n => ({ id: n.id, name: n.name, file: n.file })),
    changed: [...after.keys()].filter(id => before.has(id) && (after.get(id).hash !== before.get(id).hash || after.get(id).snippet !== before.get(id).snippet)),
    edgesAdded: [...newEdges].filter(id => !oldEdges.has(id)).length,
    edgesRemoved: [...oldEdges].filter(id => !newEdges.has(id)).length
  };
}
export function scan(root, { keep = 30 } = {}) {
  if (!Number.isInteger(keep) || keep < 1) throw new Error('--keep must be a positive integer');
  const base = initialize(root), lock = path.join(base, 'tmp', 'scan.lock');
  try { fs.mkdirSync(lock); }
  catch (e) { if (e.code === 'EEXIST') throw new Error('Another scan is running (tmp/scan.lock). After an interrupted process, remove the empty lock directory before retrying.'); throw e; }
  try {
    const input = inventory(root);
    const fingerprint = hash(JSON.stringify([ENGINE, input.files.map(f => [f.path, f.hash]), input.diagnostics]));
    const previous = readJSON(path.join(base, 'data', 'graph.json'));
    if (previous?.fingerprint === fingerprint && !previous.diagnostics.length) return { graph: previous, changed: false, base };
    const cachePath = path.join(base, 'tmp', 'cache', 'files.json');
    const result = analyze(root, input, readJSON(cachePath, {}));
    const sources = new Map(input.files.map(f => [f.path, f.source.split('\n')]));
    for (const n of result.graph.nodes) if (n.line && sources.has(n.file)) {
      n.snippet = sources.get(n.file).slice(n.line - 1, Math.min(n.endLine || n.line + 12, n.line + 39)).join('\n');
      if (n.contract) {
        const code=sources.get(n.file).slice(n.line-1,n.endLine||n.line).join('\n');
        n.code=code.slice(0,24000); n.codeTruncated=code.length>24000;
      }
      if (n.kind !== 'file') n.hash = hash(sources.get(n.file).slice(n.line - 1, n.endLine || n.line).join('\n'));
    }
    const history = readJSON(path.join(base, 'data', 'history.json'), []);
    const version = Math.max(previous?.version || 0, ...history.map(h => h.version), 0) + 1;
    const graph = { ...result.graph, version, fingerprint, generatedAt: new Date().toISOString() };
    graph.diff = diffGraph(previous, graph);
    // Avoid duplicate snapshots when unchanged parser errors are reported again.
    if (previous?.fingerprint === fingerprint && JSON.stringify(previous.diagnostics) === JSON.stringify(graph.diagnostics)) return { graph: previous, changed: false, base };
    atomic(cachePath, result.cache);
    const snapshot = path.join(base, 'tmp', 'snapshots', String(version).padStart(6,'0') + '.json');
    atomic(snapshot, graph);
    atomic(path.join(base, 'data', 'graph.json'), graph);
    history.push({ version, generatedAt: graph.generatedAt, nodes: graph.nodes.length, edges: graph.edges.length, diagnostics: graph.diagnostics.length });
    const removed = history.splice(0, Math.max(0, history.length - keep));
    atomic(path.join(base, 'data', 'history.json'), history);
    for (const item of removed) if (Number.isInteger(item.version) && item.version > 0) {
      const p = path.join(base, 'tmp', 'snapshots', String(item.version).padStart(6,'0') + '.json');
      if (fs.existsSync(p)) fs.unlinkSync(p);
    }
    return { graph, changed: true, base };
  } finally { fs.rmdirSync(lock); }
}
export function exportHTML(graph) {
  const template = fs.readFileSync(path.join(viewer, 'index.html'), 'utf8');
  const css = fs.readFileSync(path.join(viewer, 'style.css'), 'utf8');
  const js = fs.readFileSync(path.join(viewer, 'app.js'), 'utf8');
  const payload = JSON.stringify(graph).replaceAll('<', '\\u003c').replaceAll('>', '\\u003e').replaceAll('&', '\\u0026');
  return template.replace('<link rel="stylesheet" href="/style.css">', () => '<style>' + css + '</style>')
    .replace('<script src="/app.js" defer></script>', () => '<script id="snapshot-data" type="application/json">' + payload + '</script><script>' + js + '</script>');
}
