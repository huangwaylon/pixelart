// Snowpeak Sprite Editor — paints sparse, palette-locked override layers on top of generated base frames.
'use strict';
const QS = new URLSearchParams(location.search);
const ANIM = QS.get('anim') || 'jump';
const VARIANT = QS.get('variant') || '';
const VQ = VARIANT ? `&variant=${VARIANT}` : '';
const COMPASS = ['NW', 'N', 'NE', 'W', null, 'E', 'SW', 'S', 'SE'];
const HEADROOM = 24;

const S = {
  sheet: null, pal: [], palRGB: [], W: 64, H: 64, dirs: [], n: 0,
  base: {}, ov: {}, shadow: [],
  dir: 'S', frame: 0, tool: 'pencil', color: 0,
  dirty: new Set(), undo: {}, redo: {},
  playing: false, playT: 0, playFrame: 0, lastTs: 0, painting: false, stroke: null,
  feedback: [],
};
const $ = (id) => document.getElementById(id);
const key = (d, f) => `${d}/${f}`;
const status = (msg) => { $('status').textContent = msg; };

// ---------------------------------------------------------------- loading
async function loadImageIdx(url) {
  const img = new Image();
  img.src = url + '?t=' + Date.now();
  await img.decode();
  const c = document.createElement('canvas');
  c.width = img.width; c.height = img.height;
  const g = c.getContext('2d');
  g.drawImage(img, 0, 0);
  const d = g.getImageData(0, 0, img.width, img.height).data;
  const lut = new Map(S.palRGB.map((c, i) => [(c[0] << 16) | (c[1] << 8) | c[2], i]));
  const idx = new Int16Array(img.width * img.height);
  for (let i = 0; i < idx.length; i++) {
    idx[i] = d[i * 4 + 3] === 0 ? -1 : (lut.get((d[i * 4] << 16) | (d[i * 4 + 1] << 8) | d[i * 4 + 2]) ?? -1);
  }
  return { idx, w: img.width, h: img.height };
}

function cut(sheet, col, row) {
  const out = new Int16Array(S.W * S.H);
  for (let y = 0; y < S.H; y++)
    for (let x = 0; x < S.W; x++)
      out[y * S.W + x] = sheet.idx[(row * S.H + y) * sheet.w + col * S.W + x];
  return out;
}

async function load() {
  status('loading…');
  const st = await (await fetch(`/api/state?anim=${ANIM}${VQ}`)).json();
  if (!st.sheet) { status('no build yet — click Rebuild'); return; }
  S.sheet = st.sheet;
  [S.W, S.H] = st.sheet.frameSize;
  S.dirs = st.sheet.directions;
  S.n = st.sheet.frames.length;
  S.pal = st.palette.colors;
  S.palRGB = S.pal.map((c) => [1, 3, 5].map((i) => parseInt(c.hex.slice(i, i + 2), 16)));
  S.feedback = st.feedback;
  const sheet = await loadImageIdx(st.baseSheet);
  const sh = await loadImageIdx(st.shadowStrip);
  S.base = {}; S.ov = {};
  S.dirs.forEach((d, r) => {
    S.base[d] = []; S.ov[d] = [];
    for (let f = 0; f < S.n; f++) {
      S.base[d].push(cut(sheet, f, r));
      const o = st.overrides[key(d, f)];
      S.ov[d].push(new Map(o ? o.px.map(([x, y, v]) => [y * S.W + x, v]) : []));
    }
  });
  S.shadow = [];
  for (let f = 0; f < S.n; f++) S.shadow.push(cut(sh, f, 0));
  S.dirty.clear();
  $('buildinfo').textContent = `${VARIANT || 'classic'} · ${ANIM} · build ${st.sheet.buildId} · ${S.W}x${S.H} · ${S.n} frames · ${st.sheet.totalMs}ms`;
  renderQA(st.qa, st.overrides);
  const sel = $('variant-select');
  sel.innerHTML = ['<option value="">classic</option>', ...st.variants.map((v) => `<option ${v === VARIANT ? 'selected' : ''}>${v}</option>`)].join('');
  sel.onchange = () => { location.search = `?anim=${ANIM}` + (sel.value ? `&variant=${sel.value}` : ''); };
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
  if (v === undefined || v === S.base[S.dir][S.frame][i]) ov.delete(i);   // revert / no-op override
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
function drawIdx(g, idx, ox, oy, scale, alpha = 1) {
  g.globalAlpha = alpha;
  for (let y = 0; y < S.H; y++)
    for (let x = 0; x < S.W; x++) {
      const v = idx[y * S.W + x];
      if (v < 0) continue;
      g.fillStyle = S.pal[v].hex;
      g.fillRect(ox + x * scale, oy + y * scale, scale, scale);
    }
  g.globalAlpha = 1;
}

function redraw() {
  const z = +$('opt-zoom').value;
  const c = $('edit');
  c.width = S.W * z; c.height = S.H * z;
  const g = c.getContext('2d');
  // checker background
  for (let y = 0; y < S.H; y++)
    for (let x = 0; x < S.W; x++) {
      g.fillStyle = (x + y) % 2 ? '#e9eff7' : '#dfe7f1';
      g.fillRect(x * z, y * z, z, z);
    }
  // pivot marker
  const [px, py] = S.sheet.pivot;
  g.fillStyle = 'rgba(238,122,94,.35)';
  g.fillRect(0, py * z, c.width, 1); g.fillRect(px * z, 0, 1, c.height);
  if ($('opt-onion').checked) {
    if (S.frame > 0) drawIdx(g, composite(S.dir, S.frame - 1), 0, 0, z, 0.22);
    if (S.frame < S.n - 1) drawIdx(g, composite(S.dir, S.frame + 1), 0, 0, z, 0.12);
  }
  drawIdx(g, composite(S.dir, S.frame, $('opt-base').checked), 0, 0, z);
  if ($('opt-ovl').checked && !$('opt-base').checked) {
    g.strokeStyle = '#ff2fd0'; g.lineWidth = 1;
    for (const [i, v] of S.ov[S.dir][S.frame]) {
      const x = i % S.W, y = (i / S.W) | 0;
      g.strokeRect(x * z + 1.5, y * z + 1.5, z - 3, z - 3);
      if (v === -1) { g.beginPath(); g.moveTo(x * z + 2, y * z + 2); g.lineTo(x * z + z - 2, y * z + z - 2); g.stroke(); }
    }
  }
  if ($('opt-grid').checked && z >= 6) {
    g.strokeStyle = 'rgba(36,22,40,.12)'; g.lineWidth = 1;
    for (let x = 0; x <= S.W; x++) { g.beginPath(); g.moveTo(x * z + .5, 0); g.lineTo(x * z + .5, c.height); g.stroke(); }
    for (let y = 0; y <= S.H; y++) { g.beginPath(); g.moveTo(0, y * z + .5); g.lineTo(c.width, y * z + .5); g.stroke(); }
  }
  const inf = S.sheet.frames[S.frame];
  const dirty = S.dirty.has(key(S.dir, S.frame)) ? ' • unsaved' : '';
  $('frame-title').textContent = `${S.dir} · frame ${S.frame + 1}/${S.n} “${inf.name}” · ${inf.duration_ms}ms · z ${inf.z_px}px · ${S.ov[S.dir][S.frame].size} override px${dirty}`;
  $('frame-info').textContent = JSON.stringify(inf, null, 1);
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
    c.width = S.W * 2; c.height = S.H * 2;
    drawIdx(c.getContext('2d'), composite(S.dir, f), 0, 0, 2);
    div.appendChild(c);
    div.insertAdjacentHTML('beforeend', `<span>${f + 1}</span>` + (S.ov[S.dir][f].size ? '<b class="ov">●</b>' : ''));
    div.onclick = () => { S.frame = f; redraw(); };
    wrap.appendChild(div);
  }
}

function drawCell(g, d, f, ox, oy, sc) {
  const useZ = $('opt-z').checked;
  drawIdx(g, S.shadow[f], ox, oy + HEADROOM * sc, sc);
  const z = useZ ? S.sheet.frames[f].z_px : 0;
  drawIdx(g, composite(d, f), ox, oy + (HEADROOM - z) * sc, sc);
}

function drawPreview(f) {
  const c = $('preview');
  const all = $('opt-all').checked;
  const sc = all ? 1 : 4;
  const cw = S.W * sc, ch = (S.H + HEADROOM) * sc;
  c.width = all ? cw * 3 : cw; c.height = all ? ch * 3 : ch;
  const g = c.getContext('2d');
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, c.width, c.height);
  if (all) COMPASS.forEach((d, k) => { if (d) drawCell(g, d, f, (k % 3) * cw, ((k / 3) | 0) * ch, sc); });
  else drawCell(g, S.dir, f, 0, 0, sc);
  c.style.width = (all ? c.width * 1.6 : c.width * 0.75) + 'px';
}

function tick(ts) {
  if (!S.playing) return;
  const dt = (ts - (S.lastTs || ts)) * +$('opt-speed').value;
  S.lastTs = ts;
  S.playT += dt;
  while (S.playT >= S.sheet.frames[S.playFrame].duration_ms) {
    S.playT -= S.sheet.frames[S.playFrame].duration_ms;
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
    d.title = `${i} ${c.name} ${c.hex}`;
    d.onclick = () => selectColor(i);
    pal.appendChild(d);
  });
  selectColor(S.color);
  const cp = $('compass');
  cp.innerHTML = '';
  COMPASS.forEach((d) => {
    const b = document.createElement('button');
    if (d) { b.textContent = d; b.dataset.dir = d; b.onclick = () => { S.dir = d; redraw(); }; }
    else { b.disabled = true; b.textContent = '·'; }
    cp.appendChild(b);
  });
  redraw();
}

function selectColor(i) {
  S.color = i;
  document.querySelectorAll('#palette div').forEach((d, k) => d.classList.toggle('on', k === i));
  $('cur-color').textContent = `${i} · ${S.pal[i].name} · ${S.pal[i].hex}`;
}

function setTool(t) {
  S.tool = t;
  document.querySelectorAll('#tools button').forEach((b) => b.classList.toggle('on', b.dataset.tool === t));
}

function canvasXY(e) {
  const r = $('edit').getBoundingClientRect();
  const z = +$('opt-zoom').value;
  return [Math.floor((e.clientX - r.left) / z), Math.floor((e.clientY - r.top) / z)];
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

function line(x0, y0, x1, y1, fn) {   // Bresenham so fast strokes stay connected (pixel-perfect)
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
window.addEventListener('mousemove', (e) => {
  if (!S.painting) return;
  const [x, y] = canvasXY(e);
  if (S.stroke[0] === x && S.stroke[1] === y) return;
  const tool = S.tool;
  line(S.stroke[0], S.stroke[1], x, y, (px, py) =>
    setPixel(px, py, tool === 'pencil' ? S.color : tool === 'erase' ? -1 : undefined));
  S.stroke = [x, y];
  redraw();
});
window.addEventListener('mouseup', () => { S.painting = false; });

async function save() {
  const todo = [...S.dirty];
  for (const k of todo) {
    const [d, f] = k.split('/');
    const px = [...S.ov[d][+f]].map(([i, v]) => [i % S.W, (i / S.W) | 0, v]);
    const r = await fetch(`/api/override?anim=${ANIM}${VQ}&dir=${d}&frame=${f}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ px }),
    });
    if (!r.ok) { status(`save failed for ${k}`); return; }
    S.dirty.delete(k);
  }
  status(`saved ${todo.length} frame override(s) — Rebuild to bake into deliverables`);
  redraw();
}

async function rebuild() {
  if (S.dirty.size) await save();
  status('building…');
  const r = await (await fetch(`/api/build?anim=${ANIM}${VQ}`, { method: 'POST' })).json();
  console.log(r.log);
  await load();
  status(`build ${r.code === 0 ? 'OK' : 'finished with QA errors'} in ${r.seconds}s`);
}

function renderQA(qa, overrides) {
  if (!qa) { $('qa').textContent = 'no report'; return; }
  const h = [`<div class="${qa.pass ? 'ok' : 'err'}">${qa.pass ? 'PASS' : 'FAIL'}</div>`];
  qa.errors.forEach((e) => h.push(`<div class="err">✖ ${e}</div>`));
  qa.warnings.forEach((e) => h.push(`<div class="warn">▲ ${e}</div>`));
  const m = qa.metrics;
  h.push(`<pre>foot slide ${m.foot_slide_px}px · height Δ ${m.max_height_delta_px}px · orphans ${m.orphan_pixels_total} · colours ${m.colours_used}</pre>`);
  $('qa').innerHTML = h.join('');
}

function renderFeedback() {
  const list = S.feedback.filter((f) => f.dir === S.dir && f.frame === S.frame);
  $('fb-list').innerHTML = list.map((f) => `<div><small>${f.time} · ${f.author} · ${f.status}</small><br>${f.note.replace(/</g, '&lt;')}</div>`).join('') || '<p class="hint">No notes on this frame.</p>';
}

$('btn-fb').onclick = async () => {
  const note = $('fb-note').value.trim();
  if (!note) return;
  const entry = { anim: ANIM, variant: VARIANT, dir: S.dir, frame: S.frame, author: $('fb-author').value, note };
  await fetch('/api/feedback', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(entry) });
  S.feedback.push({ ...entry, time: 'just now', status: 'open' });
  $('fb-note').value = '';
  renderFeedback();
};
$('btn-save').onclick = save;
$('btn-build').onclick = rebuild;
$('btn-play').onclick = () => {
  S.playing = !S.playing;
  $('btn-play').textContent = S.playing ? '❚❚ Pause' : '▶ Play';
  S.lastTs = 0; S.playT = 0; S.playFrame = S.frame;
  if (S.playing) requestAnimationFrame(tick); else drawPreview(S.frame);
};
document.querySelectorAll('#tools button').forEach((b) => (b.onclick = () => setTool(b.dataset.tool)));
['opt-grid', 'opt-onion', 'opt-ovl', 'opt-base', 'opt-zoom', 'opt-all', 'opt-z'].forEach((id) => ($(id).oninput = redraw));

window.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT' && e.target.type !== 'checkbox' && e.target.type !== 'range') return;
  const k = e.key.toLowerCase();
  if ((e.ctrlKey || e.metaKey) && k === 's') { e.preventDefault(); save(); return; }
  if ((e.ctrlKey || e.metaKey) && k === 'z') { e.preventDefault(); undoRedo(e.shiftKey); return; }
  const tools = { b: 'pencil', e: 'erase', g: 'fill', i: 'pick', r: 'revert' };
  if (tools[k]) setTool(tools[k]);
  else if (k === 'o') { $('opt-onion').checked = !$('opt-onion').checked; redraw(); }
  else if (k === 'h') { $('opt-base').checked = !$('opt-base').checked; redraw(); }
  else if (k === ' ') { e.preventDefault(); $('btn-play').click(); }
  else if (e.key === 'ArrowRight') { S.frame = (S.frame + 1) % S.n; redraw(); }
  else if (e.key === 'ArrowLeft') { S.frame = (S.frame + S.n - 1) % S.n; redraw(); }
  else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    const i = S.dirs.indexOf(S.dir);
    S.dir = S.dirs[(i + (e.key === 'ArrowDown' ? 1 : S.dirs.length - 1)) % S.dirs.length];
    redraw();
  }
});

load();
