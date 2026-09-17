#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { scan, exportHTML, readJSON } from './storage.mjs';
import { serve } from './server.mjs';

const args = process.argv.slice(2);
const command = args.shift() || 'help';
const rootArg = args[0] && !args[0].startsWith('--') ? args.shift() : '.';
function option(name, fallback) {
  const index = args.indexOf('--' + name);
  if (index < 0) return fallback;
  if (!args[index + 1] || args[index + 1].startsWith('--')) throw new Error('Missing value for --' + name);
  const value = args[index + 1]; args.splice(index, 2); return value;
}
try {
  const port = Number(option('port', '4731'));
  const keep = Number(option('keep', '30'));
  const output = option('output', null);
  if (args.length) throw new Error('Unknown arguments: ' + args.join(' '));
  if (!['scan','serve','watch','export','history'].includes(command)) {
    console.log('overview-project <scan|serve|watch|export|history> [project-directory]\n  --port 4731    Local web port (serve/watch)\n  --keep 30      Per-project snapshot retention\n  --output PATH Export HTML destination (must not exist)\n\nRequires Node 20+ and Python 3.9+ for Python analysis.');
    if (!['help','--help','-h'].includes(command)) process.exitCode = 1;
  } else {
    const root = fs.realpathSync(path.resolve(rootArg));
    if (!fs.statSync(root).isDirectory()) throw new Error('Target must be a directory');
    if (command === 'serve' || command === 'watch') {
      if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('Invalid --port');
      const server = await serve(root, { port, keep });
      console.log('Overview Project · ' + root + '\nhttp://127.0.0.1:' + server.address().port + '\nWatching files. Ctrl+C to stop.');
      for (const signal of ['SIGINT','SIGTERM']) process.on(signal, () => server.close(() => process.exit(0)));
    } else if (command === 'history') {
      console.log(JSON.stringify(readJSON(path.join(root, '.overview-project/data/history.json'), []), null, 2));
    } else {
      const result = scan(root, { keep });
      if (command === 'export') {
        const dest = output ? path.resolve(output) : path.join(result.base, 'exports', 'overview-project-v' + result.graph.version + '.html');
        fs.writeFileSync(dest, exportHTML(result.graph), { flag: 'wx' });
        console.log(dest);
      } else console.log(JSON.stringify({ version: result.graph.version, changed: result.changed, nodes: result.graph.nodes.length, edges: result.graph.edges.length, diagnostics: result.graph.diagnostics, output: path.join(result.base, 'data/graph.json') }, null, 2));
    }
  }
} catch (e) { console.error('overview-project: ' + e.message); process.exitCode = 1; }
