import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';
import postcss from 'postcss';
import { parse } from 'parse5';
import ignore from 'ignore';

export const ENGINE = '0.2.2';
const here = path.dirname(fileURLToPath(import.meta.url));
const extensions = new Set(['.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.html', '.css']);
const excluded = new Set(['.git', '.overview-project', 'node_modules', '.venv', 'venv', '__pycache__', 'dist', 'build', 'coverage']);
const slash = p => p.split(path.sep).join('/');
export const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const isTest = p => /(^|\/)(__tests__|tests?|specs?)(\/|$)|(^|\/)(test_|.*[.](test|spec)[.])|_test\.py$/.test(p.split(/(?:^|\/)fixtures\//).at(-1));

export function inventory(root) {
  const files = [], diagnostics = [];
  function walk(dir, rules = []) {
    const gitignore = path.join(dir, '.gitignore');
    if (fs.existsSync(gitignore) && !fs.lstatSync(gitignore).isSymbolicLink()) {
      rules = [...rules, { base: dir, matcher: ignore().add(fs.readFileSync(gitignore, 'utf8')) }];
    }
    for (const entry of fs.readdirSync(dir, { withFileTypes: true }).sort((a,b) => a.name.localeCompare(b.name))) {
      if (entry.isSymbolicLink() || excluded.has(entry.name) || entry.name.startsWith('.env')) continue;
      const absolute = path.join(dir, entry.name), relative = slash(path.relative(root, absolute));
      if (rules.some(r => r.matcher.ignores(slash(path.relative(r.base, absolute)) + (entry.isDirectory() ? '/' : '')))) continue;
      if (entry.isDirectory()) { walk(absolute, rules); continue; }
      if (!entry.isFile() || !extensions.has(path.extname(entry.name))) continue;
      if (fs.statSync(absolute).size > 2 * 1024 * 1024) {
        diagnostics.push({ file: relative, message: 'Skipped: exceeds 2 MiB source limit' }); continue;
      }
      const source = fs.readFileSync(absolute, 'utf8');
      files.push({ path: relative, source, hash: hash(source) });
    }
  }
  walk(root);
  return { files, diagnostics };
}

function analyzeWeb(file) {
  const nodes = [], refs = [], imports = [], styles = [];
  const fid = 'file:' + file.path;
  const ext = path.extname(file.path);
  const addStyle = (token, source, line) => styles.push({ token, source, line });
  if (ext === '.css') {
    const css = postcss.parse(file.source, { from: file.path });
    css.walkRules(rule => {
      const id = file.path + '::selector:' + rule.selector;
      if (!nodes.some(n => n.id === id)) nodes.push({ id, name: rule.selector, kind: 'style', file: file.path, parent: fid, line: rule.source.start.line, endLine: rule.source.end.line, language: 'css' });
      for (const m of rule.selector.matchAll(/\.((?:\\.|[\w-])+)/g)) refs.push({ source: id, kind: 'selector', name: m[1].replace(/\\(.)/g, '$1'), line: rule.source.start.line });
    });
    return { nodes, refs, imports, styles };
  }
  if (ext === '.html') {
    const doc = parse(file.source, { sourceCodeLocationInfo: true });
    function walk(n, parent) {
      let owner = parent;
      if (n.tagName && n.sourceCodeLocation) {
        const line = n.sourceCodeLocation.startLine;
        owner = file.path + '::element:' + n.sourceCodeLocation.startOffset;
        const attrs = Object.fromEntries((n.attrs || []).map(a => [a.name, a.value]));
        nodes.push({ id: owner, name: n.tagName + (attrs.id ? '#' + attrs.id : ''), kind: 'element', file: file.path, parent, line, endLine: n.sourceCodeLocation.endLine, language: 'html' });
        for (const token of (attrs.class || '').split(/\s+/).filter(Boolean)) addStyle(token, owner, line);
        const module = n.tagName === 'script' ? attrs.src : n.tagName === 'link' ? attrs.href : null;
        if (module) imports.push({ module, line });
      }
      for (const c of n.childNodes || []) walk(c, owner);
      if (n.content) walk(n.content, owner);
    }
    walk(doc, fid);
    return { nodes, refs, imports, styles };
  }
  const sf = ts.createSourceFile(file.path, file.source, ts.ScriptTarget.Latest, true,
    ext === '.tsx' || ext === '.jsx' ? ts.ScriptKind.TSX : ext === '.js' || ext === '.mjs' || ext === '.cjs' ? ts.ScriptKind.JS : ts.ScriptKind.TS);
  const scopes = [fid], names = [];
  const lineOf = n => sf.getLineAndCharacterOfPosition(n.getStart(sf)).line + 1;
  const locals=new WeakMap();
  function boundNames(name,set){if(ts.isIdentifier(name))set.add(name.text);else if(ts.isObjectBindingPattern(name)||ts.isArrayBindingPattern(name))for(const e of name.elements)if(ts.isBindingElement(e))boundNames(e.name,set);}
  function shadowed(identifier){
    for(let p=identifier.parent;p;p=p.parent){
      if(!ts.isFunctionLike(p)&&!ts.isBlock(p)&&!ts.isForStatement(p)&&!ts.isForOfStatement(p)&&!ts.isForInStatement(p))continue;
      if(!locals.has(p)){
        const names=new Set();for(const param of p.parameters||[])boundNames(param.name,names);
        function collect(c){if(ts.isFunctionLike(c)){if(c.name&&ts.isIdentifier(c.name))names.add(c.name.text);return;}if(ts.isVariableDeclaration(c))boundNames(c.name,names);ts.forEachChild(c,collect);}
        ts.forEachChild(p,collect);locals.set(p,names);
      }
      if(locals.get(p).has(identifier.text))return true;
    }return false;
  }
  function moduleLevel(n){for(let p=n.parent;p&&!ts.isSourceFile(p);p=p.parent)if(ts.isFunctionLike(p)||ts.isBlock(p)||ts.isForStatement(p)||ts.isForOfStatement(p)||ts.isForInStatement(p))return false;return true;}
  function contract(n) {
    let fn = n;
    if (ts.isVariableDeclaration(n)) fn=n.initializer;
    if (ts.isCallExpression(n)) fn=n.arguments.find(a=>ts.isArrowFunction(a)||ts.isFunctionExpression(a));
    if (!fn?.parameters || !fn.body) return undefined;
    const returns=[],calls=[];
    function walk(child) {
      if (ts.isFunctionLike(child) || ts.isClassDeclaration(child)) return;
      if (ts.isReturnStatement(child)) returns.push({expression:child.expression?.getText(sf)||'undefined',line:lineOf(child)});
      if (ts.isYieldExpression(child)) returns.push({expression:child.expression?.getText(sf)||'undefined',line:lineOf(child),kind:'yield'});
      if (ts.isCallExpression(child)||ts.isNewExpression(child)) calls.push({name:child.expression.getText(sf),line:lineOf(child)});
      ts.forEachChild(child,walk);
    }
    if(ts.isBlock(fn.body))ts.forEachChild(fn.body,walk);
    else {returns.push({expression:fn.body.getText(sf),line:lineOf(fn.body)});walk(fn.body);}
    const docs=n.jsDoc || n.parent?.parent?.jsDoc || [];
    return {parameters:fn.parameters.map(p=>({name:p.name.getText(sf),type:p.type?.getText(sf)||null,default:p.initializer?.getText(sf)||null,optional:!!p.questionToken,rest:!!p.dotDotDotToken})),
      returns,calls,returnType:fn.type?.getText(sf)||null,documentation:docs.map(d=>typeof d.comment==='string'?d.comment:'').filter(Boolean).join('\n'),
      asyncFunction:!!fn.modifiers?.some(m=>m.kind===ts.SyntaxKind.AsyncKeyword)};
  }
  function visit(n) {
    let definition = null;
    if (ts.isImportDeclaration(n) || ts.isExportDeclaration(n)) {
      if (n.moduleSpecifier && ts.isStringLiteral(n.moduleSpecifier)) {
        const module = n.moduleSpecifier.text;
        const base = { module, line: lineOf(n) };
        imports.push(base);
        const clause = n.importClause;
        if (clause?.name) imports.push({ ...base, local: clause.name.text, imported: 'default' });
        if (clause?.namedBindings) {
          if (ts.isNamespaceImport(clause.namedBindings)) imports.push({ ...base, local: clause.namedBindings.name.text, imported: '*' });
          else for (const e of clause.namedBindings.elements) imports.push({ ...base, local: e.name.text, imported: (e.propertyName || e.name).text });
        }
      }
    }
    let name = n.name?.getText(sf), kind;
    if (ts.isFunctionDeclaration(n)) { name ||= 'default'; kind = /^[A-Z]/.test(name) ? 'component' : 'function'; }
    else if (ts.isClassDeclaration(n)) { name ||= 'default'; kind = 'class'; }
    else if (ts.isMethodDeclaration(n) || ts.isConstructorDeclaration(n)) { name ||= 'constructor'; kind = 'method'; }
    else if (ts.isVariableDeclaration(n) && ts.isIdentifier(n.name)) {
      const init = n.initializer;
      if (init && (ts.isArrowFunction(init) || ts.isFunctionExpression(init))) kind = /^[A-Z]/.test(name) ? 'component' : 'function';
      else if (scopes.length === 1) kind = 'variable';
    }
    if (ts.isCallExpression(n) && /^(test|it)(\.(only|skip|todo))?$/.test(n.expression.getText(sf)) && n.arguments[0] && ts.isStringLiteral(n.arguments[0])) {
      name = n.arguments[0].text; kind = 'test';
    }
    if (kind && name) {
      const qualified = [...names, name].join('.');
      definition = file.path + '::' + qualified;
      if (nodes.some(x => x.id === definition)) definition += ':' + n.getStart(sf);
      nodes.push({ id: definition, name, qualified, kind, file: file.path, line: lineOf(n),
        endLine: sf.getLineAndCharacterOfPosition(n.end).line + 1, parent: scopes.at(-1), language: 'typescript',
        exported: n.modifiers?.some(m => m.kind === ts.SyntaxKind.ExportKeyword) || false,
        defaultExport: n.modifiers?.some(m => m.kind === ts.SyntaxKind.DefaultKeyword) || false,
        contract:contract(n), ...(kind==='variable'?{moduleLevel:moduleLevel(n)}:{}) });
      if (ts.isClassDeclaration(n)) for (const h of n.heritageClauses || []) for (const t of h.types) refs.push({ source: definition, name: t.expression.getText(sf), kind: 'inherits', line: lineOf(t) });
      scopes.push(definition); names.push(name);
    }
    const owner = scopes.at(-1);
    if (ts.isCallExpression(n) || ts.isNewExpression(n)) {
      refs.push({ source: owner, name: n.expression.getText(sf), kind: 'calls', line: lineOf(n),
        call:{expression:n.getText(sf),arguments:[...(n.arguments||[])].map(a=>a.getText(sf))} });
      if (n.expression.getText(sf) === 'require' && n.arguments?.[0] && ts.isStringLiteral(n.arguments[0])) imports.push({ module: n.arguments[0].text, line: lineOf(n) });
    }
    if (ts.isJsxOpeningElement(n) || ts.isJsxSelfClosingElement(n)) {
      const name = n.tagName.getText(sf);
      if (/^[A-Z]/.test(name)) refs.push({ source: owner, name, kind: 'renders', line: lineOf(n) });
      for (const a of n.attributes.properties) if (ts.isJsxAttribute(a) && ['className', 'class'].includes(a.name.getText(sf)) && a.initializer) {
        let value = ts.isStringLiteral(a.initializer) ? a.initializer.text : null;
        if (ts.isJsxExpression(a.initializer) && a.initializer.expression && ts.isStringLiteralLike(a.initializer.expression)) value = a.initializer.expression.text;
        for (const token of (value || '').split(/\s+/).filter(Boolean)) addStyle(token, owner, lineOf(a));
      }
    }
    if (ts.isIdentifier(n) && n.parent && n !== n.parent.name && !ts.isImportSpecifier(n.parent)) {
      const p = n.parent;
      const writes = ts.isBinaryExpression(p) && p.left === n && p.operatorToken.kind >= ts.SyntaxKind.FirstAssignment && p.operatorToken.kind <= ts.SyntaxKind.LastAssignment;
      refs.push({ source: owner, name: n.text, kind: writes ? 'writes' : 'reads', line: lineOf(n),shadowed:shadowed(n) });
    }
    ts.forEachChild(n, visit);
    if (definition) { scopes.pop(); names.pop(); }
  }
  visit(sf);
  const error = sf.parseDiagnostics.map(d => ts.flattenDiagnosticMessageText(d.messageText, '\n')).join('; ');
  return { nodes, refs, imports, styles, ...(error ? { error } : {}) };
}

export function analyze(root, input, previousCache = {}) {
  const { files, diagnostics } = input;
  const cache = {}, parsed = {}, changedPython = [];
  for (const f of files) {
    const hit = previousCache[f.path];
    if (hit?.hash === f.hash && hit.engine === ENGINE) parsed[f.path] = hit.result;
    else if (f.path.endsWith('.py')) changedPython.push(f);
    else {
      try { parsed[f.path] = analyzeWeb(f); }
      catch (e) { parsed[f.path] = { nodes: [], refs: [], imports: [], error: e.message }; }
    }
  }
  if (changedPython.length) {
    const run = spawnSync(process.env.OVERVIEW_PYTHON || 'python3', [path.join(here, 'python_ast.py')], { input: JSON.stringify(changedPython), encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
    if (run.status === 0) Object.assign(parsed, JSON.parse(run.stdout));
    else for (const f of changedPython) parsed[f.path] = { nodes: [], refs: [], imports: [], error: 'Python analysis unavailable: ' + (run.error?.message || run.stderr.trim()) };
  }
  const nodes = [], edges = [], edgeIds = new Set(), directories = new Set();
  function edge(source, target, kind, line = 1, confidence = 'resolved', call) {
    if (!source || !target || source === target && ['reads', 'writes'].includes(kind)) return;
    const id = hash([source, target, kind, line, call?.expression || ''].join('|')).slice(0, 20);
    if (!edgeIds.has(id)) { edgeIds.add(id); edges.push({ id, source, target, kind, line, confidence, ...(call?{call}:{}) }); }
  }
  for (const f of files) {
    let dir = path.posix.dirname(f.path);
    while (dir !== '.') { directories.add(dir); dir = path.posix.dirname(dir); }
  }
  for (const dir of [...directories].sort()) {
    const parent = path.posix.dirname(dir);
    nodes.push({ id: 'dir:' + dir, name: path.posix.basename(dir), kind: 'directory', file: dir, parent: parent === '.' ? null : 'dir:' + parent });
  }
  for (const f of files) {
    const result = parsed[f.path];
    cache[f.path] = { hash: f.hash, engine: ENGINE, result };
    const dir = path.posix.dirname(f.path);
    nodes.push({ id: 'file:' + f.path, name: path.posix.basename(f.path), kind: 'file', file: f.path, line: 1, parent: dir === '.' ? null : 'dir:' + dir, test: isTest(f.path), hash: f.hash });
    nodes.push(...result.nodes.map(n => ({ ...n, test: n.kind === 'test' || isTest(f.path) })));
    if (result.error) diagnostics.push({ file: f.path, message: result.error });
  }
  const byId = new Map(nodes.map(n => [n.id, n]));
  for (const n of nodes) if (n.parent) edge(n.parent, n.id, 'contains');
  const filePaths = new Set(files.map(f => f.path));
  function moduleFile(file, imp) {
    if (file.endsWith('.py')) {
      const parts = path.posix.dirname(file).split('/').filter(p => p !== '.');
      if (imp.level) parts.splice(Math.max(0, parts.length - imp.level + 1));
      const module = imp.module.replaceAll('.', '/');
      const bases = imp.level ? [path.posix.join(...parts, module)] : [module, 'src/' + module];
      for (const base of bases) for (const c of [base + '.py', base + '/__init__.py']) if (filePaths.has(c)) return c;
      return null;
    }
    if (!imp.module.startsWith('.') && !file.endsWith('.html')) return null;
    const base = path.posix.normalize(path.posix.join(path.posix.dirname(file), imp.module));
    for (const c of [base, ...['.ts','.tsx','.js','.jsx','.mjs','.css'].map(e => base + e), ...['.ts','.tsx','.js','.jsx'].map(e => base + '/index' + e)]) if (filePaths.has(c)) return c;
    if (base.endsWith('.js') && filePaths.has(base.slice(0,-3)+'.ts')) return base.slice(0,-3)+'.ts';
    return null;
  }
  function resolve(file, ref, bindings) {
    let scope = byId.get(ref.source);
    while (scope) {
      const prefix = scope.kind === 'file' ? '' : (scope.qualified || '') + '.';
      const n = byId.get(file + '::' + prefix + ref.name);
      if (n) return n;
      scope = byId.get(scope.parent);
    }
    const n = byId.get(file + '::' + ref.name);
    if (n) return n;
    const [first, ...rest] = ref.name.split('.');
    const binding = bindings.get(first);
    if (!binding) return null;
    const { target, imported } = binding;
    if (imported === 'default') return nodes.find(n => n.file === target && n.defaultExport) || byId.get(target + '::default') || null;
    return byId.get(target + '::' + (imported === '*' ? rest.join('.') : [imported, ...rest].join('.')));
  }
  let unresolved = 0;
  for (const f of files) {
    const r = parsed[f.path], bindings = new Map();
    for (const imp of r.imports) {
      const target = moduleFile(f.path, imp);
      if (target) {
        edge('file:' + f.path, 'file:' + target, 'imports', imp.line);
        if (isTest(f.path)) edge('file:' + f.path, 'file:' + target, 'tests', imp.line, 'inferred');
        if (imp.local) bindings.set(imp.local, { target, imported: imp.imported });
      } else if (imp.module.startsWith('.') || f.path.endsWith('.py')) unresolved++;
    }
    for (const ref of r.refs) {
      if (ref.kind === 'selector') continue;
      if(ref.shadowed && ['reads','writes'].includes(ref.kind))continue;
      const n = resolve(f.path, ref, bindings);
      if (n && (!['reads','writes'].includes(ref.kind) || n.kind === 'variable')) {
        edge(ref.source, n.id, ref.kind, ref.line, 'inferred', ref.call);
        if (byId.get(ref.source)?.test && ['calls','renders'].includes(ref.kind) && !n.test) edge(ref.source, n.id, 'tests', ref.line, 'inferred');
      } else if (['calls','renders','inherits'].includes(ref.kind)) unresolved++;
    }
  }
  const selectors = new Map();
  for (const r of Object.values(parsed)) for (const ref of r.refs) if (ref.kind === 'selector') selectors.set(ref.name, [...(selectors.get(ref.name) || []), ref.source]);
  for (const r of Object.values(parsed)) for (const s of r.styles || []) {
    const targets = selectors.get(s.token);
    if (targets) for (const target of targets) edge(s.source, target, 'styles', s.line, 'inferred');
    else {
      const id = 'utility:' + s.token;
      if (!byId.has(id)) { const n = { id, name: s.token, kind: 'utility', file: '', language: 'css' }; nodes.push(n); byId.set(id, n); }
      edge(s.source, id, 'styles', s.line, 'inferred');
    }
  }
  return { cache, graph: { schemaVersion: 1, engineVersion: ENGINE, project: path.basename(root), nodes, edges, diagnostics, unresolved,
    files: files.map(f => ({ path: f.path, hash: f.hash })),
    limitations: ['Static relationships, not runtime execution or test coverage.', 'Python name resolution and test/style links are inferred; dynamic dispatch, aliases/re-exports and computed classes may be unresolved.', 'Utility nodes represent literal class usage; Tailwind configuration is not executed.', 'JavaScript/TypeScript: relative imports and direct lexical names; tsconfig paths, props/state dataflow and full type analysis are not supported yet.'] } };
}
