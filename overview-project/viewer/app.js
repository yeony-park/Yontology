(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const snapshot = $('snapshot-data');
  const offline = !!snapshot;
  let graph, index = new Map(), selected = null, mode = 'files', focused = false;
  let historical = false, latestVersion = 0, query = '', relation = 'all';
  let activeCluster = null;
  let anchor = null, explored = new Set();
  const codeOpened = new Set();
  const BLOCK_WIDTH=320, BLOCK_HEIGHT=400, COLUMN=370, ROW=450;
  let inspectorOpen=false;
  let nodeType='all';
  let expansionNotice='';
  const functionKinds=new Set(['function','method','component','test']);
  const sharingCache=new WeakMap();
  function moduleVariable(n){return n.kind==='variable' && n.moduleLevel!==false && index.get(n.parent)?.kind==='file';}
  function sharedVariables(){
    if(sharingCache.has(graph))return sharingCache.get(graph);
    const shared=new Map();
    for(const e of graph.edges){
      if(!['reads','writes'].includes(e.kind)||!moduleVariable(index.get(e.target)||{})||!functionKinds.has(index.get(e.source)?.kind))continue;
      if(!shared.has(e.target))shared.set(e.target,new Map());
      const users=shared.get(e.target);if(!users.has(e.source))users.set(e.source,new Set());users.get(e.source).add(e.kind);
    }
    const result=new Map([...shared].filter(([,users])=>users.size>=2));sharingCache.set(graph,result);return result;
  }
  function typeMatches(n){
    if(nodeType==='classes')return n.kind==='class';
    if(nodeType==='functions')return functionKinds.has(n.kind);
    if(nodeType==='globals')return moduleVariable(n);
    if(nodeType==='shared')return sharedVariables().has(n.id);
    return true;
  }
  let transform = { x: 35, y: 35, scale: 1 }, positions = new Map(), drag = null;
  const SVG = 'http://www.w3.org/2000/svg';
  const color = kind => ({ file:'#628cac', directory:'#628cac', test:'#886caf', component:'#408e7b', function:'#408e7b', method:'#408e7b', variable:'#c59b57', class:'#537da7', utility:'#bd8868', style:'#bd8868', element:'#a37a97' }[kind] || '#84958d');
  function el(tag, text, cls) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; }
  function svg(tag, attrs, text) { const n = document.createElementNS(SVG, tag); for (const [k,v] of Object.entries(attrs)) n.setAttribute(k,v); if (text !== undefined) n.textContent = text; return n; }
  async function get(url) { const r = await fetch(url); if (!r.ok) throw new Error('Request failed: ' + r.status); return r.json(); }
  function setGraph(next) {
    graph = next; index = new Map(graph.nodes.map(n => [n.id, n]));
    if (selected && !index.has(selected)) selected = null;
    explored = new Set([...explored].filter(id=>index.has(id)));
    $('project').textContent = graph.project;
    if (!offline) $('export').href = '/export.html?version=' + graph.version;
    $('metrics').replaceChildren(...[['FILES',graph.files.length],['SYMBOLS',graph.nodes.filter(n => !['file','directory','utility'].includes(n.kind)).length],['CONNECTIONS',graph.edges.filter(e => e.kind !== 'contains').length]].map(([label,value]) => {
      const n = el('div',undefined,'metric'); n.append(el('b',String(value)),el('span',label)); return n;
    }));
    $('file-count').textContent = graph.files.length;
    const d = graph.diff;
    $('changes').textContent = `v${graph.version} · ${new Date(graph.generatedAt).toLocaleString()}  |  +${d.added.length} added · −${d.removed.length} removed · ${d.changed.length} changed · 연결 +${d.edgesAdded}/−${d.edgesRemoved}`;
    $('diagnostic-title').textContent = `분석 범위 및 알림 · ${graph.diagnostics.length}개 알림 · 미해결/외부 참조 ${graph.unresolved}개`;
    const info = el('ul');
    for (const message of graph.limitations) info.append(el('li',message));
    for (const diagnostic of graph.diagnostics) info.append(el('li',diagnostic.file + ': ' + diagnostic.message));
    if (d.removed.length) info.append(el('li','삭제된 노드: ' + d.removed.map(n => n.file + ' / ' + n.name).join(', ')));
    $('diagnostic-body').replaceChildren(info);
    renderTree(); render(); details();
  }
  function choose(id, reveal = false) {
    const entering = reveal && !focused;
    selected = id;
    if (entering) {
      const n = index.get(id);
      if (n) mode = n.kind === 'file' ? 'files' : n.kind === 'test' ? 'tests' : ['style','utility','element'].includes(n.kind) ? 'styles' : 'symbols';
      focused = true; query = ''; $('search').value = ''; relation = 'all'; $('relation').value = 'all';
      anchor=id; explored=new Set(); positions=new Map([[id,{x:20,y:65}]]);
      codeOpened.add(id);inspectorOpen=false;
      expandConnections(id);
    }
    if (focused) explored.add(id);
    if (reveal) activeCluster = null;
    renderTree(); render(); details();
    if (entering) fit();
  }
  function expansionTargets(id) {
    const targets=new Set([id]);
    for (const e of graph.edges) if ((e.kind!=='contains' || ['file','class'].includes(index.get(id)?.kind)) && (e.source===id || e.target===id)) {
      if(index.has(e.source))targets.add(e.source);if(index.has(e.target))targets.add(e.target);
    }
    return targets;
  }
  function expansionCount(id){return [...expansionTargets(id)].filter(target=>!explored.has(target)).length;}
  function expandConnections(id) {
    const count=expansionCount(id);
    for(const target of expansionTargets(id))explored.add(target);
    expansionNotice=`${index.get(id)?.name || '선택 노드'} · ${count?count+'개 노드 추가됨':'이미 모든 연결이 펼쳐져 있습니다'}${nodeType!=='all'?' · 표시 대상 필터 적용 중':''}`;
  }
  function expansionButton(id,label='+ 연결'){
    const count=expansionCount(id),button=el('button',count?`${label} ${count}개 펼치기`:'✓ 연결 펼쳐짐');
    button.disabled=!count;button.classList.toggle('expanded',!count);
    button.title=count?'기존 노드와 위치를 유지하면서 연결된 노드를 추가합니다.':'추가로 펼칠 노드가 없습니다. 현재 필터에서 일부 노드는 숨겨질 수 있습니다.';
    button.onclick=()=>{selected=id;expandConnections(id);render();details();};return button;
  }
  function placeNodes(candidates, edges) {
    const lanes=new Map();
    for(const [id,p] of positions){const file=index.get(id)?.file||'공유 스타일';if(!lanes.has(file))lanes.set(file,p.x);}
    for(const n of candidates) {
      if(positions.has(n.id))continue;
      const file=n.file||'공유 스타일';
      if(!lanes.has(file))lanes.set(file,lanes.size?Math.max(...lanes.values())+COLUMN+30:20);
      const x=lanes.get(file),same=[...positions.values()].filter(p=>p.x===x);
      const y=same.length?Math.max(...same.map(p=>p.y))+ROW:65;
      positions.set(n.id,{x,y});
    }
  }
  function renderTree() {
    const container = $('tree'), open = new Set([...container.querySelectorAll('details[open]')].map(n => n.dataset.path));
    const initialized = container.childNodes.length > 0;
    const root = { children: new Map(), files: [] };
    for (const n of graph.nodes.filter(n => n.kind === 'file' && (!query || n.file.toLowerCase().includes(query) || graph.nodes.some(s => s.file === n.file && s.name.toLowerCase().includes(query))))) {
      const parts = n.file.split('/'); parts.pop(); let branch = root;
      for (const part of parts) { if (!branch.children.has(part)) branch.children.set(part,{ children: new Map(), files: [] }); branch = branch.children.get(part); }
      branch.files.push(n);
    }
    function build(branch, parent = '') {
      const frag = document.createDocumentFragment();
      for (const [name, child] of branch.children) {
        const p = parent + '/' + name, d = el('details'); d.dataset.path = p; d.open = !initialized || open.has(p) || !!query;
        d.append(el('summary', name),build(child,p)); frag.append(d);
      }
      for (const n of branch.files) { const b = el('button',(n.test ? '◇ ' : '▤ ') + n.name,selected === n.id ? 'selected' : ''); b.title = n.file; b.onclick = () => { activeCluster = clusterKey(n); focused = false; selected = n.id; render(); details(); }; frag.append(b); }
      return frag;
    }
    container.replaceChildren(build(root));
  }
  function clusterKey(n) {
    if (!n.file) return '공유 스타일';
    const parts = n.file.split('/'); parts.pop();
    return parts.join('/') || '프로젝트 루트';
  }
  function clusters() {
    const groups = new Map(), membership = new Map();
    // Preserve folder ownership; attach test files to the production module they actually reference.
    const assignments = new Map();
    for (const file of graph.nodes.filter(n => n.kind === 'file' && n.test)) {
      const votes = new Map();
      for (const e of graph.edges) {
        const a = index.get(e.source), b = index.get(e.target);
        if (a?.file === file.file && b?.file && !b.test && e.kind !== 'contains') {
          const key = clusterKey(b); votes.set(key, (votes.get(key) || 0) + 1);
        }
      }
      const winner = [...votes].sort((a,b) => b[1]-a[1] || a[0].localeCompare(b[0]))[0];
      if (winner) assignments.set(file.file, winner[0]);
    }
    for (const n of graph.nodes.filter(n => n.kind !== 'directory')) {
      const key = assignments.get(n.file) || clusterKey(n);
      if (!groups.has(key)) groups.set(key, { key, nodes: [], links: new Map() });
      groups.get(key).nodes.push(n); membership.set(n.id,key);
    }
    for (const e of graph.edges.filter(e => e.kind !== 'contains')) {
      const a = membership.get(e.source), b = membership.get(e.target);
      if (a && b && a !== b) {
        const links = groups.get(a).links;
        if (!links.has(b)) links.set(b,new Set());
        links.get(b).add([e.source,e.target,e.kind].join('|'));
      }
    }
    // Put strongly connected modules next to each other, keeping ordering deterministic.
    const remaining=new Map([...groups].sort((a,b)=>a[0].localeCompare(b[0]))), ordered=[];
    const weight=g=>[...g.links.values()].reduce((sum,edges)=>sum+edges.size,0);
    while(remaining.size){
      const seed=[...remaining.values()].sort((a,b)=>weight(b)-weight(a)||a.key.localeCompare(b.key))[0];
      const queue=[seed.key];
      while(queue.length){const key=queue.shift(),g=remaining.get(key);if(!g)continue;remaining.delete(key);ordered.push(g);
        const neighbors=[...remaining.values()].map(other=>({key:other.key,weight:(g.links.get(other.key)?.size||0)+(other.links.get(key)?.size||0)})).filter(n=>n.weight).sort((a,b)=>b.weight-a.weight||a.key.localeCompare(b.key));
        queue.push(...neighbors.map(n=>n.key));
      }
    }
    return ordered;
  }
  function renderClusters() {
    const host = $('cluster-board'); host.replaceChildren();
    const all = clusters();
    const matches = n => typeMatches(n) && (!query || (n.name+' '+n.file).toLowerCase().includes(query)) &&
      (mode === 'files' && !!n.file || mode === 'symbols' && !['file','style','utility','element'].includes(n.kind) || mode === 'tests' && n.test || mode === 'styles' && ['style','utility','element','component'].includes(n.kind)) &&
      (relation === 'all' || graph.edges.some(e=>e.kind===relation && (e.source===n.id || e.target===n.id)));
    const shown = all.filter(g => (!activeCluster || g.key === activeCluster) && g.nodes.some(matches));
    $('graph-count').textContent = `${shown.length}개 그룹 · 폴더 기준 / 테스트는 참조 대상에 연결`;
    const intro = el('div',undefined,'board-intro');
    intro.append(el('h2',activeCluster || '어디서 무엇을 하는지, 먼저 큰 그림부터'),el('p',activeCluster ? '파일별 정의를 펼치고 함수를 선택해 연결을 따라가세요.' : '폴더별로 코드를 묶었습니다. 그룹을 열면 파일과 함수가, 연결 배지를 누르면 의존 대상이 보입니다.'));
    host.append(intro);
    if (!shown.length) host.append(el('p','검색 결과가 없습니다. 전체 보기로 돌아가거나 검색어를 바꿔보세요.'));
    for (const group of shown) {
      const card = el('article',undefined,'cluster-card'+(activeCluster?' expanded-cluster':''));
      const title = el('button',group.key,'cluster-title'); title.onclick = () => { activeCluster = activeCluster ? null : group.key; render(); details(); };
      const files = new Set(group.nodes.filter(n=>n.file).map(n=>n.file));
      card.append(title,el('p',`${files.size} 파일 · ${group.nodes.filter(n=>!['file','utility'].includes(n.kind)).length} 정의 · ${group.nodes.filter(n=>n.kind==='test').length} 테스트`,'cluster-meta'));
      const fileGroups = new Map();
      for (const n of group.nodes.filter(matches)) { const key=n.file || '공유 스타일'; if(!fileGroups.has(key))fileGroups.set(key,[]);fileGroups.get(key).push(n); }
      const entries = [...fileGroups];
      for (const [file,nodes] of (activeCluster || query ? entries : entries.slice(0,4))) {
        const row = el('details',undefined,'file-group'); row.open=!!activeCluster || !!query || nodeType!=='all';
        row.append(el('summary',`${nodes.some(n=>n.test)?'◇ ':''}${file.split('/').pop()} · ${group.nodes.filter(n=>n.file===file&&n.kind!=='file').length}`));
        row.append(el('small',file,'file-path'));
        const members = nodes.filter(n=>n.kind!=='file');
        const definitions = members.length ? members : group.nodes.filter(n=>n.file===file && n.kind!=='file' && typeMatches(n));
        const classContainers=new Map();
        for (const n of definitions) {
          let parent=index.get(n.parent),owner=null;
          while(parent&&parent.kind!=='file'){if(parent.kind==='class')owner=parent;parent=index.get(parent.parent);}
          let container=row;
          if(owner&&nodeType!=='classes'){
            if(!classContainers.has(owner.id)){const section=el('details',undefined,'class-container');section.open=true;section.append(el('summary','class '+owner.name));row.append(section);classContainers.set(owner.id,section);}
            container=classContainers.get(owner.id);
          }
          const b=el('button',undefined,'symbol-row'); b.append(el('span',n.name),el('small',n.kind)); b.onclick=()=>choose(n.id,true);container.append(b);
          if(moduleVariable(n)){
            const users=sharedVariables().get(n.id);
            if(users){const hint=el('p',`${users.size}개 함수가 공유 · `+[...users].map(([id,kinds])=>index.get(id).name+' ('+[...kinds].map(k=>k==='reads'?'읽기':'쓰기').join('/')+')').join(', '),'shared-hint');container.append(hint);}
          }
        }
        if (!definitions.length) { const f=group.nodes.find(n=>n.file===file&&n.kind==='file'); if(f){const b=el('button','파일 연결 보기','symbol-row');b.onclick=()=>choose(f.id,true);row.append(b);} }
        card.append(row);
      }
      if(!activeCluster && !query && entries.length>4){const more=el('button',`+ ${entries.length-4}개 파일 더 보기`,'more-files');more.onclick=()=>{activeCluster=group.key;render();};card.append(more);}
      const deps=el('div',undefined,'cluster-deps'); deps.append(el('small','이 그룹이 참조하는 곳'));
      for(const [target,edges] of group.links){const b=el('button',`→ ${target} · ${edges.size}`);b.title='정적 분석으로 찾은 그룹 간 연결 수';b.onclick=()=>{activeCluster=target;query='';$('search').value='';mode='files';relation='all';$('relation').value='all';render();};deps.append(b);}
      if(!group.links.size)deps.append(el('span','감지된 외부 그룹 연결 없음'));
      card.append(deps);host.append(card);
    }
  }
  function visible() {
    let candidates = graph.nodes.filter(n => mode === 'files' ? n.kind === 'file' : mode === 'symbols' ? !['file','directory','utility','style','element'].includes(n.kind) : mode === 'styles' ? ['component','element','style','utility','file'].includes(n.kind) : n.test);
    if (mode === 'tests') {
      const ids = new Set(candidates.map(n=>n.id));
      for (const e of graph.edges) if (e.kind === 'tests' && ids.has(e.source)) ids.add(e.target);
      candidates = graph.nodes.filter(n=>ids.has(n.id));
    }
    if (focused) {
      candidates = graph.nodes.filter(n=>explored.has(n.id));
    }
    if(nodeType==='shared' && focused){
      const shared=sharedVariables(),ids=new Set();
      for(const n of candidates)if(shared.has(n.id)){ids.add(n.id);for(const id of shared.get(n.id).keys())ids.add(id);}
      candidates=graph.nodes.filter(n=>ids.has(n.id));
    }else candidates=candidates.filter(typeMatches);
    candidates = candidates.filter(n => !query || (n.name + ' ' + n.file).toLowerCase().includes(query));
    if (relation !== 'all') {
      const ids = new Set(graph.edges.filter(e=>e.kind===relation).flatMap(e=>[e.source,e.target]));
      candidates = candidates.filter(n=>ids.has(n.id));
    }
    candidates.sort((a,b)=>(a.file || '').localeCompare(b.file || '') || (a.line || 0)-(b.line || 0));
    const total = candidates.length; if(!focused)candidates = candidates.slice(0,100);
    const ids = new Set(candidates.map(n=>n.id));
    const edges = graph.edges.filter(e => ids.has(e.source) && ids.has(e.target) && (relation === 'all' ? e.kind !== 'contains' || focused && index.get(anchor)?.kind==='file' : e.kind === relation));
    return { candidates, edges, total };
  }
  function render() {
    if (!$('cluster-board')) { const board=el('div',undefined,'cluster-board');board.id='cluster-board';$('canvas').append(board); }
    document.querySelector('main').classList.toggle('has-selection',!!selected || focused);
    document.querySelector('main').classList.toggle('has-inspector',inspectorOpen);
    document.body.classList.toggle('block-map-open',focused);
    $('canvas').classList.toggle('overview-mode',!focused);
    for (const b of document.querySelectorAll('[data-mode]')) b.classList.toggle('active',b.dataset.mode===mode);
    const remaining=selected?expansionCount(selected):0;
    $('focus').textContent = focused ? remaining?`+ 연결 ${remaining}개 펼치기`:'✓ 연결 펼쳐짐' : '선택 노드 연결 보기';
    $('focus').disabled = !selected || focused&&!remaining;
    $('focus').classList.toggle('expanded',focused&&!!selected&&!remaining);
    $('expansion-status').textContent=focused?expansionNotice:'';
    if (!focused) { renderClusters(); return; }
    const { candidates, edges, total } = visible();
    $('graph-count').textContent = candidates.length + ' nodes · ' + edges.length + ' links · 클릭: 상세 선택 / 펼치기: 연결 추가';
    $('empty').hidden = candidates.length > 0;
    const scene = $('scene'); scene.replaceChildren();
    placeNodes(candidates,edges);
    const files=new Map();
    for(const n of candidates){const file=n.file||'공유 스타일';if(!files.has(file))files.set(file,[]);files.get(file).push(positions.get(n.id));}
    for(const [file,points] of files){
      const x=points[0].x,y=35,bottom=Math.max(...points.map(p=>p.y))+BLOCK_HEIGHT+16;
      scene.append(svg('rect',{x:x-12,y:y-28,width:BLOCK_WIDTH+24,height:bottom-y+28,rx:12,class:'file-boundary'}));
      const label=svg('text',{x,y:28,class:'file-heading'},short(file,46));label.append(svg('title',{},file));scene.append(label);
    }
    const uniqueEdges = new Map();
    for (const e of edges) uniqueEdges.set([e.source,e.target,e.kind].join('|'),e);
    for (const e of uniqueEdges.values()) {
      const a = positions.get(e.source), b = positions.get(e.target);
      const sameCol = a.x===b.x;
      const x1 = a.x+BLOCK_WIDTH, y1=a.y+60, x2=sameCol ? b.x+BLOCK_WIDTH : b.x, y2=b.y+60;
      const bend = sameCol ? 45 : Math.max(30,Math.abs(x2-x1)/2);
      const d = `M${x1},${y1} C${x1+bend},${y1} ${sameCol?x2+bend:x2-bend},${y2} ${x2},${y2}`;
      const p = svg('path',{ d, class:'edge '+(e.confidence==='inferred'?'inferred ':'')+([e.source,e.target].includes(selected)?'highlight':''), 'marker-end':'url(#arrow)' });
      p.append(svg('title',{},`${e.kind} · ${e.confidence} · L${e.line}${e.call?' · '+e.call.expression:''}`)); scene.append(p);
      if (edges.length < 20) scene.append(svg('text',{x:sameCol?x1+35:(x1+x2)/2,y:(y1+y2)/2-5,class:'edge-label'},e.kind));
    }
    const added = new Set(graph.diff.added), changed = new Set(graph.diff.changed);
    for (const n of candidates) {
      const p = positions.get(n.id);
      const g = svg('g',{transform:`translate(${p.x},${p.y})`,class:'node '+(n.id===selected?'selected ':'')+(changed.has(n.id)?'changed':added.has(n.id)?'added':''), tabindex:'0',role:'button','aria-label':n.kind+' '+n.name});
      const body=svg('foreignObject',{width:BLOCK_WIDTH,height:BLOCK_HEIGHT});
      body.append(functionBlock(n));g.append(body);
      g.append(svg('title',{},n.file+' / '+n.name));
      g.addEventListener('click',e=>{if(!e.target.closest('button,details,pre,summary'))choose(n.id,true);});
      g.addEventListener('keydown',e=>{if(e.target===g&&(e.key==='Enter'||e.key===' ')){e.preventDefault();choose(n.id,true);}});
      scene.append(g);
    }
    applyTransform();
  }
  function short(value,max=110){return value.length>max?value.slice(0,max)+'…':value;}
  function parameterText(p){return (p.rest?'…':'')+p.name+(p.optional?'?':'')+(p.type?': '+p.type:'')+(p.default!==null&&p.default!==undefined?' = '+p.default:'');}
  function responsibility(n) {
    if(n.contract?.documentation)return {label:'역할 · 소스 문서',text:n.contract.documentation};
    const calls=[...new Set(n.contract?.calls?.map(c=>c.name)||graph.edges.filter(e=>e.source===n.id&&e.kind==='calls').map(e=>index.get(e.target)?.name).filter(Boolean))];
    return {label:'관찰된 동작 · 의도 설명 아님',text:calls.length?'호출: '+calls.join(', '):n.contract?.returns.length?'반환: '+n.contract.returns.map(r=>r.expression).join(' / '):'역할 설명 없음. 코드나 문서로 확인이 필요합니다.'};
  }
  function functionBlock(n) {
    const card=el('article',undefined,'function-block');
    const head=el('div',undefined,'block-head');head.append(el('span',(n.contract?.asyncFunction?'async ':'')+n.kind,'badge'),el('strong',n.name),el('small',n.file+':'+(n.line||1)));card.append(head);
    const parent=index.get(n.parent);if(parent&&parent.kind!=='file')head.append(el('small','소속: '+parent.kind+' '+parent.name));
    if(moduleVariable(n)){const users=sharedVariables().get(n.id);if(users)head.append(el('small',`${users.size}개 함수가 공유하는 모듈 변수`));}
    const summary=responsibility(n),role=el('div',undefined,'block-purpose');role.append(el('small',summary.label),el('p',short(summary.text,95)));card.append(role);
    if(n.contract){
      const io=el('div',undefined,'block-io');
      for(const [label,values] of [['INPUT · 파라미터',n.contract.parameters.map(parameterText)],['OUTPUT · 반환식',n.contract.returns.map(r=>(r.kind==='yield'?'yield ':'')+r.expression)]]){
        const cell=el('div');cell.append(el('small',label));
        cell.append(el('p',values.length?values.slice(0,3).map(v=>short(v,90)).join('\n')+(values.length>3?`\n+${values.length-3}개 · 상세에서 확인`:''):label.startsWith('INPUT')?'명시적 파라미터 없음':'명시적 return 없음 (실행 결과 미확인)'));io.append(cell);
      }card.append(io);
    }else card.append(el('p','함수 외 노드 · 입출력 계약 없음','block-note'));
    const code=el('details',undefined,'block-code');code.open=codeOpened.has(n.id);
    code.append(el('summary','실제 코드 펼치기'),el('pre',n.code||n.snippet||'소스 정보 없음'));
    code.ontoggle=()=>{if(code.open)codeOpened.add(n.id);else codeOpened.delete(n.id);};card.append(code);
    const actions=el('div',undefined,'block-actions');const inspect=el('button','입출력·호출 상세');inspect.onclick=()=>{inspectorOpen=true;choose(n.id,true);};
    const expand=expansionButton(n.id);actions.append(inspect,expand);card.append(actions);
    return card;
  }
  function details() {
    const box = $('details'), n = index.get(selected);
    if (!n) { box.replaceChildren(el('div','함수를 선택하면 연결과 코드가 표시됩니다.','placeholder')); return; }
    box.replaceChildren(el('span',n.kind,'badge'),el('h2',n.name),el('p',n.file+(n.line?':'+n.line:''),'location'));
    const copy = el('button','위치 복사'); copy.onclick = async () => {
      try { await navigator.clipboard.writeText(n.file+(n.line?':'+n.line:'')); copy.textContent='복사됨'; }
      catch { copy.textContent='위 텍스트를 선택해 복사하세요'; }
    }; box.append(copy);
    const dismiss=el('button','상세 닫기');dismiss.onclick=()=>{inspectorOpen=false;render();};box.append(dismiss);
    const expand=focused?expansionButton(n.id):el('button','연결 보기');if(!focused)expand.onclick=()=>choose(n.id,true);box.append(expand);
    const purpose=responsibility(n);box.append(el('h3',purpose.label),el('p',purpose.text,'contract-description'));
    if(n.contract){
      box.append(el('h3','INPUT · 선언된 파라미터'));
      for(const p of n.contract.parameters)box.append(el('pre',parameterText(p)));
      if(!n.contract.parameters.length)box.append(el('p','명시적 파라미터 없음'));
      box.append(el('h3','OUTPUT · 반환 타입 / 반환식'),el('p',n.contract.returnType||'반환 타입 선언 없음 · 실행값은 분석하지 않음'));
      for(const r of n.contract.returns)box.append(el('pre',`L${r.line} ${r.kind||'return'} ${r.expression}`));
      if(!n.contract.returns.length)box.append(el('p','명시적 return 없음. 정상 종료·예외·실행값은 이 분석만으로 보장하지 않습니다.'));
    }
    const uniqueLinks=[...new Map(graph.edges.filter(e=>e.kind!=='contains').map(e=>[[e.source,e.target,e.kind].join('|'),e])).values()];
    const inbound=uniqueLinks.filter(e=>e.target===n.id),outbound=uniqueLinks.filter(e=>e.source===n.id);
    box.append(el('p',`${inbound.length}개 연결이 들어오고 ${outbound.length}개 연결이 나갑니다. 점선은 정적 분석에서 추정한 관계입니다. 캔버스를 드래그하면 아래쪽 연결도 볼 수 있습니다.`,'connection-summary'));
    for (const [label,predicate,target] of [['이 코드를 사용하는 곳',e=>e.target===n.id,e=>e.source],['이 코드가 사용하는 것',e=>e.source===n.id,e=>e.target]]) {
      const links = uniqueLinks.filter(predicate);
      box.append(el('h3',label+' · '+links.length));
      for(const e of links.slice(0,50)) {
        const other=index.get(target(e)); if(!other)continue;
        const b=el('button',undefined,'connection'); b.append(el('span',other.name),el('br'),el('small',e.kind+' · '+other.file+':'+(e.line||other.line||1)));
        b.onclick=()=>choose(other.id,true);box.append(b);
        const sites=graph.edges.filter(site=>site.source===e.source&&site.target===e.target&&site.kind===e.kind&&site.call);
        for(const site of sites.slice(0,12)){
          const call=el('details',undefined,'call-site');call.append(el('summary',`L${site.line} 호출 인수 보기`),el('pre',site.call.expression));
          const params=index.get(site.target)?.contract?.parameters||[];
          for(const [i,arg] of site.call.arguments.entries())call.append(el('p',`인수 ${i+1}: ${arg}`));
          if(params.length)call.append(el('small','대상 선언: '+params.map(parameterText).join(', ')+' · 바인딩/실행값 미확인'));
          box.append(call);
        }
      }
      if(links.length>50)box.append(el('p','앞의 50개 연결만 표시합니다.'));
    }
    if(n.code||n.snippet) {const code=el('details');code.append(el('summary','소스 코드 보기'),el('pre',n.code||n.snippet));if(n.codeTruncated)code.append(el('p','24,000자 이후 생략 · 원본 파일에서 확인'));box.append(code);}
  }
  function applyTransform(){ $('scene').setAttribute('transform',`translate(${transform.x},${transform.y}) scale(${transform.scale})`); }
  const typeLabel=el('label','표시 대상 '),typeSelect=el('select');typeSelect.id='node-type';typeSelect.setAttribute('aria-label','표시 대상');
  for(const [value,label] of [['all','전체'],['classes','클래스만'],['functions','함수·메서드만'],['globals','모듈 전역변수'],['shared','공유 전역변수']])typeSelect.append(new Option(label,value));
  typeLabel.append(typeSelect);document.querySelector('.subtoolbar').prepend(typeLabel);
  const expansionStatus=el('div',undefined,'expansion-status');expansionStatus.id='expansion-status';expansionStatus.setAttribute('role','status');expansionStatus.setAttribute('aria-live','polite');document.querySelector('.subtoolbar').after(expansionStatus);
  typeSelect.onchange=e=>{nodeType=e.target.value;if(nodeType==='shared'||nodeType==='globals'){mode='symbols';focused=false;selected=null;activeCluster=null;inspectorOpen=false;}render();details();};
  function fit(){ if(!focused)return;transform={x:25,y:5,scale:1};applyTransform(); }
  for(const b of document.querySelectorAll('[data-mode]'))b.onclick=()=>{mode=b.dataset.mode;focused=false;selected=null;activeCluster=null;render();details();};
  $('search').oninput=e=>{query=e.target.value.toLowerCase().trim();renderTree();render();fit();};
  $('relation').onchange=e=>{relation=e.target.value;render();fit();};
  $('focus').onclick=()=>{if(!selected)return;if(!focused)choose(selected,true);else{expandConnections(selected);render();details();}};
  $('reset').onclick=()=>{focused=false;selected=null;activeCluster=null;query='';relation='all';$('search').value='';$('relation').value='all';renderTree();render();details();};
  $('fit').onclick=fit;
  $('zoom-in').onclick=()=>{transform.scale=Math.min(3,transform.scale*1.2);applyTransform();};
  $('zoom-out').onclick=()=>{transform.scale=Math.max(.1,transform.scale/1.2);applyTransform();};
  $('graph').addEventListener('wheel',e=>{if(e.target.closest('.function-block'))return;e.preventDefault();const r=$('graph').getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top,old=transform.scale;transform.scale=Math.max(.1,Math.min(3,old*(e.deltaY>0?.9:1.1)));transform.x=x-(x-transform.x)*transform.scale/old;transform.y=y-(y-transform.y)*transform.scale/old;applyTransform();},{passive:false});
  $('graph').onpointerdown=e=>{if(e.target.closest('.node'))return;drag={x:e.clientX,y:e.clientY,tx:transform.x,ty:transform.y};$('graph').setPointerCapture(e.pointerId);};
  $('graph').onpointermove=e=>{if(drag){transform.x=drag.tx+e.clientX-drag.x;transform.y=drag.ty+e.clientY-drag.y;applyTransform();}};
  $('graph').onpointerup=()=>{drag=null;};
  $('graph').onpointercancel=()=>{drag=null;};
  async function history(){const rows=await get('/api/history'),value=$('history').value;$('history').replaceChildren(new Option('현재 버전 · Live','live'),...rows.slice().reverse().map(h=>new Option(`v${h.version} · ${new Date(h.generatedAt).toLocaleTimeString()}`,String(h.version))));if(value!=='live'&&![...$('history').options].some(o=>o.value===value))$('history').append(new Option(`v${value} · 보관 만료 (현재 화면 유지)`,value));$('history').value=value;}
  $('history').onchange=async e=>{historical=e.target.value!=='live';try{setGraph(await get(historical?'/api/snapshots/'+e.target.value:'/api/graph'));$('status').textContent=historical?'◷ 과거 스냅샷 · v'+graph.version:'● Live · v'+graph.version;}catch(err){$('status').textContent=err.message;}};
  async function refresh(){
    try{
      const status=await get('/api/status'),next=await get('/api/graph');
      if(next.version!==latestVersion){latestVersion=next.version;await history();if(!historical)setGraph(next);}
      $('status').classList.toggle('error',status.state==='error');
      $('status').textContent=status.error || (historical?`◷ 과거 v${graph.version} · 최신 v${latestVersion}`:`● Live · v${next.version} · ${new Date(status.checkedAt).toLocaleTimeString()}`);
    }catch(e){$('status').classList.add('error');$('status').textContent='연결 끊김 · 마지막 결과 표시 중';}
  }
  async function start(){
    if(offline){setGraph(JSON.parse(snapshot.textContent));$('status').textContent='◷ Offline snapshot · v'+graph.version;$('history').hidden=true;$('export').hidden=true;fit();}
    else{await refresh();if(graph)fit();setInterval(refresh,2000);}
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
