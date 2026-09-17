import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { scan, readJSON, exportHTML } from './storage.mjs';

export async function serve(root, { port = 4731, interval = 1500, keep = 30 } = {}) {
  let current = scan(root, { keep });
  let status = { state: 'ready', checkedAt: new Date().toISOString(), error: null };
  const mime = { 'index.html': 'text/html', 'app.js': 'text/javascript', 'style.css': 'text/css' };
  const server = http.createServer((req, res) => {
    const host = req.headers.host;
    if (host !== '127.0.0.1:' + server.address().port && host !== 'localhost:' + server.address().port) { res.writeHead(403); res.end(); return; }
    if (req.headers.origin && !['http://127.0.0.1:' + server.address().port, 'http://localhost:' + server.address().port].includes(req.headers.origin)) { res.writeHead(403); res.end(); return; }
    if (req.method !== 'GET') { res.writeHead(405); res.end(); return; }
    const url = new URL(req.url, 'http://' + host);
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    const json = value => { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(value)); };
    try {
      if (url.pathname === '/api/graph') return json(current.graph);
      if (url.pathname === '/api/status') return json(status);
      if (url.pathname === '/api/history') return json(readJSON(path.join(current.base, 'data', 'history.json'), []));
      const match = url.pathname.match(/^\/api\/snapshots\/([1-9]\d*)$/);
      if (match) {
        const graph = readJSON(path.join(current.base, 'tmp', 'snapshots', match[1].padStart(6, '0') + '.json'));
        if (graph) return json(graph);
        res.writeHead(404); return res.end('Snapshot expired');
      }
      if (url.pathname === '/export.html') {
        const version = url.searchParams.get('version');
        if (version !== null && !/^[1-9]\d*$/.test(version)) { res.writeHead(400); return res.end('Invalid version'); }
        const graph = version ? readJSON(path.join(current.base, 'tmp', 'snapshots', version.padStart(6,'0') + '.json')) : current.graph;
        if (!graph) { res.writeHead(404); return res.end('Snapshot expired'); }
        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        res.setHeader('Content-Disposition', 'attachment; filename="overview-project.html"');
        return res.end(exportHTML(graph));
      }
      const file = url.pathname === '/' ? 'index.html' : url.pathname.slice(1);
      if (!Object.hasOwn(mime, file)) { res.writeHead(404); return res.end('Not found'); }
      res.setHeader('Content-Type', mime[file] + '; charset=utf-8');
      res.end(fs.readFileSync(path.join(current.base, 'viewer', file)));
    } catch (e) { res.statusCode = 500; json({ error: e.message }); }
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(port, '127.0.0.1', resolve); });
  const timer = setInterval(() => {
    status.state = 'analyzing';
    try {
      const next = scan(root, { keep });
      current = next;
      status = { state: 'ready', checkedAt: new Date().toISOString(), error: null };
      if (next.changed) console.log('Updated v' + next.graph.version + ' · ' + next.graph.nodes.length + ' nodes');
    } catch (e) { status = { state: 'error', checkedAt: new Date().toISOString(), error: e.message }; }
  }, interval);
  server.on('close', () => clearInterval(timer));
  return server;
}
