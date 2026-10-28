// Akane Pixel Override Editor -- paints sparse, palette-locked override layers on top of the
// snapshotted base frames (pixel/base/<anim>/<DIR>/fNN.png).  Ported from the Snowpeak editor
// (/Users/waylonhuang/Documents/other/pixelart/editor), same JSON format as tools/pixel/px.py.
'use strict';
const QS = new URLSearchParams(location.search);
let ANIM = QS.get('anim') || 'idle';
const COMPASS = ['NW', 'N', 'NE', 'W', null, 'E', 'SW', 'S', 'SE'];

const S = {
  pal: [], palRGB: [], W: 128, H: 128, dirs: [], frames: {}, n: 0, pivot: [64, 104], crop: null,
  base: {}, src: {}, ov: {}, meta: {}, lint: null, ms: [],
  dir: 'S', frame: 0, tool: 'pencil', color: 0,
  dirty: new Set(), undo: {}, redo: {},
  playing: false, playT: 0, playFrame: 0, lastTs: 0, painting: false, stroke: null, feedback: [],
};
const $ = (id) => document.getElementById(id);
const key = (d, f) => `${d}/${f}`;
const status = (msg) => { $('status').textContent = msg; };
const pad2 = (k) => String(k).padStart(2, '0');

// ---------------------------------------------------------------- loading
async function loadImage(url) {
  const img = new Image();
  img.src = url + '?t=' + Date.now();
  try { await img.decode(); } catch (e) { return null; }
  return img;
}

async function loadIdx(url) {
  const img = await loadImage(url);
  const c = document.createElement('canvas');
  c.width = img.width; c.height = img.height;
  const g = c.getContext('2d');
  g.drawImage(img, 0, 0);
  const d = g.getImageData(0, 0, img.width, img.height).data;
  const lut = new Map(S.palRGB.map((c, i) => [(c[0] << 16) | (c[1] << 8) | c[2], i]));
  const idx = new Int16Array(img.width * img.height);
  for (let i = 0; i < idx.length; i++) {
    idx[i] = d[i * 4 + 3] === 0 ? -1 : (lut.get((d[i * 4] << 16) | (d[i * 4 + 1] << 8) | d[i * 4 + 2]) ?? -2);
  }
  return idx;
}

async function load() {
  status('loading...');
  const st = await (await fetch(`/api/state?anim=${ANIM}`)).json();
  const sel = $('anim-select');
  sel.innerHTML = st.anims.map((a) => `<option ${a === ANIM ? 'selected' : ''}>${a}</option>`).join('');
  sel.onchange = () => { location.search = `?anim=${sel.value}`; };
  if (!st.dirs.length) { status(`no base frames for ${ANIM} -- run tools/pixel/snapshot.py`); return; }
  S.W = st.W; S.H = st.H; S.pivot = st.pivot; S.dirs = st.dirs; S.frames = st.frames; S.ms = st.ms;
  S.pal = st.palette;
  S.palRGB = S.pal.map((c) => [1, 3, 5].map((i) => parseInt(c.hex.slice(i, i + 2), 16)));
  S.feedback = st.feedback; S.lint = st.lint; S.meta = st.overrides;
  if (!S.dirs.includes(S.dir)) S.dir = S.dirs[0];
  S.n = S.frames[S.dir].length;
  S.base = {}; S.ov = {}; S.src = {};
  const nameIdx = new Map(S.pal.map((c, i) => [c.name, i]));
  const jobs = [];
  for (const d of S.dirs) {
    S.base[d] = []; S.ov[d] = []; S.src[d] = [];
    S.frames[d].forEach((k, f) => {
      jobs.push(loadIdx(`/pixel/base/${ANIM}/${d}/f${pad2(k)}.png`).then((idx) => { S.base[d][f] = idx; }));
      jobs.push(loadImage(`/pixel/source/${ANIM}/${d}/f${pad2(k)}.png`).then((im) => { S.src[d][f] = im; }));
      const o = st.overrides[key(d, k)] || [];
      S.ov[d][f] = new Map(o.map((e) => [e.y * S.W + e.x, e.color === 'clear' ? -1 : nameIdx.get(e.color)]));
    });
  }
  await Promise.all(jobs);
  // stable crop: union bbox of all base frames (+ pad), so the pivot does not move between views
  let x0 = S.W, y0 = S.H, x1 = 0, y1 = 0;
  for (const d of S.dirs) for (const b of S.base[d]) for (let i = 0; i < b.length; i++) if (b[i] !== -1) {
    const x = i % S.W, y = (i / S.W) | 0;
    x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y);
  }
  y1 = Math.max(y1, S.pivot[1]);
  S.crop = { x0: Math.max(0, x0 - 4), y0: Math.max(0, y0 - 4) };
  S.crop.w = Math.min(S.W, x1 + 5) - S.crop.x0; S.crop.h = Math.min(S.H, y1 + 5) - S.crop.y0;
  S.dirty.clear();
  const sn = st.snapshot || {};
  $('buildinfo').textContent = `${ANIM} · round ${sn.round ?? '?'} · ${S.W}x${S.H} cell · ${S.n} frames · ${S.ms[0]}ms`;
  renderQA();
  buildUI();
  status('ready');
}

// ---------------------------------------------------------------- model
function composite(d, f, baseOnly = false) {
  const out = S.base[d][f].slice();
  if (!baseOnly) for (const [i, v] of S.ov[d][f]) out[i] = v;
  return out;
}
function pushUndo() {
  const k = key(S.dir, S.frame);
  (S.undo[k] ||= []).push(new Map(S.ov[S.dir][S.frame]));
  S.redo[k] = [];
}
function undoRedo(redo) {
  const k = key(S.dir, S.frame);
  const from = redo ? S.redo[k] : S.undo[k];
  if (!from || !from.length) return;
  (redo ? (S.undo[k] ||= []) : (S.redo[k] ||= [])).push(new Map(S.ov[S.dir][S.frame]));
  S.ov[S.dir][S.frame] = from.pop();
  S.dirty.add(k);
  redraw();
}
function setPixel(x, y, v) {
  if (x < 0 || y < 0 || x >= S.W || y >= S.H) return;
  const i = y * S.W + x;
  const ov = S.ov[S.dir][S.frame];
  if (v === undefined || v === S.base[S.dir][S.frame][i]) ov.delete(i);
  else ov.set(i, v);
  S.dirty.add(key(S.dir, S.frame));
}
function floodFill(x, y, v) {
  const img = composite(S.dir, S.frame);
  const target = img[y * S.W + x];
  if (target === v) return;
  const stack = [[x, y]];
  const seen = new Uint8Array(S.W * S.H);
  while (stack.length) {
    const [cx, cy] = stack.pop();
    if (cx < 0 || cy < 0 || cx >= S.W || cy >= S.H) continue;
    const i = cy * S.W + cx;
    if (seen[i] || img[i] !== target) continue;
    seen[i] = 1;
    setPixel(cx, cy, v);
    stack.push([cx + 1, cy], [cx - 1, cy], [cx, cy + 1], [cx, cy - 1]);
  }
}

// ---------------------------------------------------------------- drawing
function drawIdx(g, idx, ox, oy, scale, alpha = 1, crop = S.crop) {
  g.globalAlpha = alpha;
  for (let y = 0; y < crop.h; y++)
    for (let x = 0; x < crop.w; x++) {
      const v = idx[(y + crop.y0) * S.W + x + crop.x0];
      if (v === -1) continue;
      g.fillStyle = v === -2 ? '#ff00ff' : S.pal[v].hex;
      g.fillRect(ox + x * scale, oy + y * scale, scale, scale);
    }
  g.globalAlpha = 1;
}

function frameFlags() {
  if (!S.lint || !S.lint.dirs[S.dir]) return [];
  const fr = S.lint.dirs[S.dir].frames[`f${pad2(S.frames[S.dir][S.frame])}`];
  return fr ? fr.flags : [];
}

function redraw() {
  const z = +$('opt-zoom').value;
  const C = S.crop;
  const c = $('edit');
  c.width = C.w * z; c.height = C.h * z;
  const g = c.getContext('2d');
  g.imageSmoothingEnabled = true;
  for (let y = 0; y < C.h; y++)
    for (let x = 0; x < C.w; x++) {
      g.fillStyle = (x + y) % 2 ? '#c8cacf' : '#bdc0c6';
      g.fillRect(x * z, y * z, z, z);
    }
  const src = S.src[S.dir][S.frame];
  if ($('opt-src').checked && src) {
    const f = src.width / S.W;
    g.globalAlpha = 0.45;
    g.drawImage(src, C.x0 * f, C.y0 * f, C.w * f, C.h * f, 0, 0, c.width, c.height);
    g.globalAlpha = 1;
  }
  const [px, py] = S.pivot;
  if ($('opt-onion').checked) {
    if (S.frame > 0) drawIdx(g, composite(S.dir, S.frame - 1), 0, 0, z, 0.22);
    if (S.frame < S.n - 1) drawIdx(g, composite(S.dir, S.frame + 1), 0, 0, z, 0.12);
  }
  drawIdx(g, composite(S.dir, S.frame, $('opt-base').checked), 0, 0, z, $('opt-src').checked ? 0.75 : 1);
  g.fillStyle = 'rgba(238,60,60,.5)';
  g.fillRect(0, (py - C.y0) * z + z / 2, c.width, 1); g.fillRect((px - C.x0) * z + z / 2, 0, 1, c.height);
  if ($('opt-ovl').checked && !$('opt-base').checked) {
    g.strokeStyle = '#ff2fd0'; g.lineWidth = 1;
    for (const [i, v] of S.ov[S.dir][S.frame]) {
      const x = i % S.W - C.x0, y = ((i / S.W) | 0) - C.y0;
      g.strokeRect(x * z + 1.5, y * z + 1.5, z - 3, z - 3);
      if (v === -1) { g.beginPath(); g.moveTo(x * z + 2, y * z + 2); g.lineTo(x * z + z - 2, y * z + z - 2); g.stroke(); }
    }
  }
  if ($('opt-flags').checked) {
    g.lineWidth = 2;
    for (const f of frameFlags()) {
      if (f.sev === 'info') continue;
      g.strokeStyle = { orphan: '#ffe600', outline_gap: '#00e6ff', notch: '#008cff', spur: '#aa5aff', double: '#ff50c8',
        jaggy: '#ff9696', banding: '#78ff78', inner_break: '#00ffbe', flicker: '#ffffff' }[f.type] || '#ff0000';
      g.strokeRect((f.x - C.x0) * z + 1, (f.y - C.y0) * z + 1, z - 2, z - 2);
    }
  }
  if ($('opt-grid').checked && z >= 6) {
    for (let x = 0; x <= C.w; x++) {
      g.strokeStyle = (x + C.x0) % 4 === 0 ? 'rgba(0,0,0,.35)' : 'rgba(0,0,0,.10)'; g.lineWidth = 1;
      g.beginPath(); g.moveTo(x * z + .5, 0); g.lineTo(x * z + .5, c.height); g.stroke();
    }
    for (let y = 0; y <= C.h; y++) {
      g.strokeStyle = (y + C.y0) % 4 === 0 ? 'rgba(0,0,0,.35)' : 'rgba(0,0,0,.10)'; g.lineWidth = 1;
      g.beginPath(); g.moveTo(0, y * z + .5); g.lineTo(c.width, y * z + .5); g.stroke();
    }
  }
  const k = S.frames[S.dir][S.frame];
  const dirty = S.dirty.has(key(S.dir, S.frame)) ? ' · unsaved' : '';
  const stale = (S.meta[key(S.dir, k)] || []).some((e) => e._stale) ? ' · STALE (base changed)' : '';
  $('frame-title').textContent = `${S.dir} · f${pad2(k)} (${S.frame + 1}/${S.n}) · ${S.ms[S.frame] ?? '?'}ms · ${S.ov[S.dir][S.frame].size} override px${dirty}${stale}`;
  const saved = S.meta[key(S.dir, k)] || [];
  $('frame-info').textContent = saved.length ? saved.map((e) => `(${e.x},${e.y}) ${e.base_color}->${e.color}  ${e.author}: ${e.reason}`).join('\n') : 'none saved';
  document.querySelectorAll('#compass button').forEach((b) => b.classList.toggle('on', b.dataset.dir === S.dir));
  drawThumbs();
  renderFeedback();
  if (!S.playing) drawPreview(S.frame);
}

function drawThumbs() {
  const wrap = $('frames');
  wrap.innerHTML = '';
  for (let f = 0; f < S.n; f++) {
    const div = document.createElement('div');
    div.className = 'f' + (f === S.frame ? ' on' : '');
    const c = document.createElement('canvas');
    c.width = S.crop.w * 2; c.height = S.crop.h * 2;
    drawIdx(c.getContext('2d'), composite(S.dir, f), 0, 0, 2);
    div.appendChild(c);
    div.insertAdjacentHTML('beforeend', `<span>f${pad2(S.frames[S.dir][f])}</span>` + (S.ov[S.dir][f].size ? '<b class="ov">●</b>' : ''));
    div.onclick = () => { S.frame = f; redraw(); };
    wrap.appendChild(div);
  }
}

function drawPreview(f) {
  const c = $('preview');
  const all = $('opt-all').checked;
  const sc = all ? 1 : 3;
  const cw = S.crop.w * sc, ch = S.crop.h * sc;
  c.width = all ? cw * 3 : cw; c.height = all ? ch * 3 : ch;
  const g = c.getContext('2d');
  g.fillStyle = '#808080'; g.fillRect(0, 0, c.width, c.height);
  if (all) COMPASS.forEach((d, k) => { if (d && S.base[d]) drawIdx(g, composite(d, f), (k % 3) * cw, ((k / 3) | 0) * ch, sc); });
  else drawIdx(g, composite(S.dir, f), 0, 0, sc);
  c.style.width = (all ? c.width * 2 : c.width) + 'px';
}

function tick(ts) {
  if (!S.playing) return;
  const dt = (ts - (S.lastTs || ts)) * +$('opt-speed').value;
  S.lastTs = ts;
  S.playT += dt;
  while (S.playT >= (S.ms[S.playFrame] || 100)) {
    S.playT -= S.ms[S.playFrame] || 100;
    S.playFrame = (S.playFrame + 1) % S.n;
  }
  drawPreview(S.playFrame);
  requestAnimationFrame(tick);
}

// ---------------------------------------------------------------- UI
function buildUI() {
  const pal = $('palette');
  pal.innerHTML = '';
  S.pal.forEach((c, i) => {
    const d = document.createElement('div');
    d.style.background = c.hex;
    d.title = `${c.name} ${c.hex}`;
    d.onclick = () => selectColor(i);
    pal.appendChild(d);
  });
  selectColor(S.color);
  const cp = $('compass');
  cp.innerHTML = '';
  COMPASS.forEach((d) => {
    const b = document.createElement('button');
    if (d && S.dirs.includes(d)) { b.textContent = d; b.dataset.dir = d; b.onclick = () => { S.dir = d; S.n = S.frames[d].length; S.frame = Math.min(S.frame, S.n - 1); redraw(); }; }
    else { b.disabled = true; b.textContent = d || '·'; }
    cp.appendChild(b);
  });
  redraw();
}
function selectColor(i) {
  S.color = i;
  document.querySelectorAll('#palette div').forEach((d, k) => d.classList.toggle('on', k === i));
  $('cur-color').textContent = `${S.pal[i].name} · ${S.pal[i].hex}`;
}
function setTool(t) {
  S.tool = t;
  document.querySelectorAll('#tools button').forEach((b) => b.classList.toggle('on', b.dataset.tool === t));
}
function canvasXY(e) {
  const r = $('edit').getBoundingClientRect();
  const z = +$('opt-zoom').value;
  return [Math.floor((e.clientX - r.left) / z) + S.crop.x0, Math.floor((e.clientY - r.top) / z) + S.crop.y0];
}
function applyTool(x, y, e) {
  const tool = e.altKey ? 'pick' : S.tool;
  if (tool === 'pick') {
    const v = composite(S.dir, S.frame)[y * S.W + x];
    if (v >= 0) selectColor(v);
    return;
  }
  if (tool === 'pencil') setPixel(x, y, S.color);
  else if (tool === 'erase') setPixel(x, y, -1);
  else if (tool === 'revert') setPixel(x, y, undefined);
  else if (tool === 'fill') floodFill(x, y, S.color);
  redraw();
}
function line(x0, y0, x1, y1, fn) {
  const dx = Math.abs(x1 - x0), dy = -Math.abs(y1 - y0), sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
  let err = dx + dy;
  for (;;) {
    fn(x0, y0);
    if (x0 === x1 && y0 === y1) break;
    const e2 = 2 * err;
    if (e2 >= dy) { err += dy; x0 += sx; }
    if (e2 <= dx) { err += dx; y0 += sy; }
  }
}
$('edit').addEventListener('mousedown', (e) => {
  const [x, y] = canvasXY(e);
  if (!e.altKey && S.tool !== 'pick') pushUndo();
  S.painting = S.tool !== 'fill' && S.tool !== 'pick' && !e.altKey;
  S.stroke = [x, y];
  applyTool(x, y, e);
});
$('edit').addEventListener('mousemove', (e) => {
  const [x, y] = canvasXY(e);
  const v = composite(S.dir, S.frame)[y * S.W + x];
  const b = S.base[S.dir][S.frame][y * S.W + x];
  const nm = (q) => (q === -1 ? 'clear' : q === -2 ? 'OFF-PALETTE' : S.pal[q].name);
  const fl = frameFlags().filter((f) => f.x === x && f.y === y).map((f) => f.type + (f.detail ? `: ${f.detail}` : '')).join('; ');
  $('cursor').textContent = `(${x},${y})  ${nm(v)}${v !== b ? `  [base ${nm(b)}]` : ''}${fl ? '  flags: ' + fl : ''}`;
});
window.addEventListener('mousemove', (e) => {
  if (!S.painting) return;
  const [x, y] = canvasXY(e);
  if (S.stroke[0] === x && S.stroke[1] === y) return;
  const tool = S.tool;
  line(S.stroke[0], S.stroke[1], x, y, (px, py) => setPixel(px, py, tool === 'pencil' ? S.color : tool === 'erase' ? -1 : undefined));
  S.stroke = [x, y];
  redraw();
});
window.addEventListener('mouseup', () => { S.painting = false; });

async function save() {
  const reason = $('reason').value.trim();
  const todo = [...S.dirty];
  if (!todo.length) { status('nothing to save'); return; }
  if (!reason) { status('enter a reason first: every pixel must have a purpose'); $('reason').focus(); return; }
  for (const k of todo) {
    const [d, f] = k.split('/');
    const fk = S.frames[d][+f];
    const px = [...S.ov[d][+f]].map(([i, v]) => [i % S.W, (i / S.W) | 0, v === -1 ? 'clear' : S.pal[v].name]);
    const r = await fetch(`/api/override?anim=${ANIM}&dir=${d}&frame=${fk}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ px, reason, author: $('author').value || 'artist' }),
    });
    const j = await r.json();
    if (!r.ok) { status(`save failed for ${k}: ${j.error}`); return; }
    S.meta[key(d, fk)] = j.edits;
    S.dirty.delete(k);
  }
  status(`saved ${todo.length} frame(s) -- "Apply + lint" writes pixel/clean`);
  redraw();
}
async function rebuild() {
  if (S.dirty.size) await save();
  if (S.dirty.size) return;
  status('applying...');
  const r = await (await fetch(`/api/apply?anim=${ANIM}`, { method: 'POST' })).json();
  console.log(r.log);
  const st = await (await fetch(`/api/state?anim=${ANIM}`)).json();
  S.lint = st.lint; S.meta = st.overrides;
  renderQA();
  redraw();
  status(`apply + lint ${r.code === 0 ? 'OK' : 'FAILED'} in ${r.seconds}s`);
}
function renderQA() {
  const L = S.lint;
  if (!L) { $('qa').textContent = 'no lint report yet (Apply + lint)'; return; }
  const h = [`<pre>src: ${L.src}</pre>`];
  for (const [d, r] of Object.entries(L.dirs)) {
    const t = Object.entries(r.totals).filter(([k]) => k !== 'info').map(([k, v]) => `${k} ${v}`).join(', ');
    h.push(`<div class="${d === S.dir ? 'warn' : ''}"><b>${d}</b>: ${t || 'clean'} · y drift ${r.pivot.baseline_drift ?? '-'}</div>`);
  }
  $('qa').innerHTML = h.join('');
}
function renderFeedback() {
  const k = S.frames[S.dir][S.frame];
  const list = S.feedback.filter((f) => f.dir === S.dir && f.frame === k);
  $('fb-list').innerHTML = list.map((f) => `<div><small>${f.time} · ${f.author} · ${f.status}</small><br>${f.note.replace(/</g, '&lt;')}</div>`).join('') || '<p class="hint">No notes on this frame.</p>';
}
$('btn-fb').onclick = async () => {
  const note = $('fb-note').value.trim();
  if (!note) return;
  const entry = { anim: ANIM, dir: S.dir, frame: S.frames[S.dir][S.frame], author: $('fb-author').value, note };
  await fetch('/api/feedback', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(entry) });
  S.feedback.push({ ...entry, time: 'just now', status: 'open' });
  $('fb-note').value = '';
  renderFeedback();
};
$('btn-save').onclick = save;
$('btn-build').onclick = rebuild;
$('btn-play').onclick = () => {
  S.playing = !S.playing;
  $('btn-play').textContent = S.playing ? 'Pause' : 'Play';
  S.lastTs = 0; S.playT = 0; S.playFrame = S.frame;
  if (S.playing) requestAnimationFrame(tick); else drawPreview(S.frame);
};
document.querySelectorAll('#tools button').forEach((b) => (b.onclick = () => setTool(b.dataset.tool)));
['opt-grid', 'opt-onion', 'opt-ovl', 'opt-base', 'opt-zoom', 'opt-all', 'opt-flags', 'opt-src'].forEach((id) => ($(id).oninput = redraw));
window.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'TEXTAREA' || (e.target.tagName === 'INPUT' && e.target.type !== 'checkbox' && e.target.type !== 'range')) return;
  const k = e.key.toLowerCase();
  if ((e.ctrlKey || e.metaKey) && k === 's') { e.preventDefault(); save(); return; }
  if ((e.ctrlKey || e.metaKey) && k === 'z') { e.preventDefault(); undoRedo(e.shiftKey); return; }
  const tools = { b: 'pencil', e: 'erase', g: 'fill', i: 'pick', r: 'revert' };
  const tog = { o: 'opt-onion', h: 'opt-base', l: 'opt-flags', u: 'opt-src' };
  if (tools[k]) setTool(tools[k]);
  else if (tog[k]) { $(tog[k]).checked = !$(tog[k]).checked; redraw(); }
  else if (k === ' ') { e.preventDefault(); $('btn-play').click(); }
  else if (e.key === 'ArrowRight') { S.frame = (S.frame + 1) % S.n; redraw(); }
  else if (e.key === 'ArrowLeft') { S.frame = (S.frame + S.n - 1) % S.n; redraw(); }
  else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    e.preventDefault();
    const i = S.dirs.indexOf(S.dir);
    S.dir = S.dirs[(i + (e.key === 'ArrowDown' ? 1 : S.dirs.length - 1)) % S.dirs.length];
    S.n = S.frames[S.dir].length; S.frame = Math.min(S.frame, S.n - 1);
    redraw();
  }
});
load();
