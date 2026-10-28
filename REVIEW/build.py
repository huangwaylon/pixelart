#!/usr/bin/env python3
"""Build REVIEW/index.html: the main review hub for every attempt and test in this repo.

Each result is one JSON file in REVIEW/entries/ (schema below). Assets for new experiments go in
REVIEW/exp/<id>/. Run `python3 REVIEW/build.py` after adding or editing an entry. It uses only the stdlib.

Entry schema (only id, date, project, status and title are required):
{
  "id": "2026-10-28_hires_sw",           # unique; also the asset folder name under exp/
  "date": "2026-10-28",
  "project": "swordswoman" | "snowpeak" | "both",
  "kind": "experiment" | "result" | "release" | "review",
  "status": "winner" | "approved" | "promising" | "needs-review" | "running" | "inconclusive" | "rejected",
  "pinned": true,                         # optional: also show in "Current best"
  "title": "...",
  "question": "what are we testing",
  "method": "how (commands / scripts)",
  "result": "what happened (numbers)",
  "verdict": "team verdict + why",
  "scores": {"Opus": "6/10", "Argon": "7/10", "ssim_b": ".95"},
  "media": [{"src": "exp/<id>/board.png", "caption": "...", "wide": true}],   # paths relative to REVIEW/
  "links": [{"href": "../docs/x.md", "label": "notes"}],
  "next": "follow-up"
}
"""
import html, json, os, glob

HERE = os.path.dirname(os.path.abspath(__file__))
STATUS = {  # colour, sort order
    'winner': ('#3fb950', 0), 'approved': ('#3fb950', 1), 'promising': ('#58a6ff', 2), 'needs-review': ('#d29922', 3),
    'running': ('#a371f7', 4), 'inconclusive': ('#8b949e', 5), 'rejected': ('#f85149', 6)}

CSS = """
body{background:#1e1f22;color:#ddd;font:14px/1.45 -apple-system,system-ui,sans-serif;margin:0}
header{position:sticky;top:0;background:#16171a;padding:10px 18px;border-bottom:1px solid #333;z-index:5}
h1{margin:0 0 6px;font-size:19px;color:#fff} h2{color:#ffd;margin:26px 18px 8px;font-size:17px}
.filters button{background:#2b2d31;color:#ccc;border:1px solid #444;border-radius:12px;padding:2px 10px;margin:2px;cursor:pointer}
.filters button.on{background:#ffd;color:#111}
main{padding:0 18px 40px}
.card{background:#26282c;border:1px solid #393b40;border-radius:8px;margin:12px 0;padding:12px 14px}
.card h3{margin:0 0 4px;font-size:16px;color:#fff}
.meta{font-size:12px;color:#999;margin-bottom:6px}
.badge{display:inline-block;border-radius:10px;padding:0 8px;font-size:12px;color:#111;font-weight:600;margin-right:6px}
.proj{background:#444;color:#ddd}
dl{display:grid;grid-template-columns:90px 1fr;gap:2px 10px;margin:6px 0} dt{color:#aaa} dd{margin:0}
.scores span{display:inline-block;background:#33363b;border-radius:4px;padding:0 6px;margin:0 4px 4px 0;font-size:12px}
.media{display:flex;flex-wrap:wrap;gap:10px;margin-top:8px}
figure{margin:0;background:#4a4a4a;padding:6px;border-radius:4px;max-width:100%}
figure.wide{flex-basis:100%}
figure img{image-rendering:pixelated;max-width:100%;max-height:520px;display:block;cursor:zoom-in}
figure.wide img{max-height:none}
figcaption{font-size:12px;color:#ddd;margin-top:4px}
a{color:#79c0ff}
#zoom{display:none;position:fixed;inset:0;background:rgba(0,0,0,.92);z-index:9;overflow:auto;cursor:zoom-out}
#zoom img{image-rendering:pixelated;display:block;margin:20px auto;max-width:none}
.pinned{border-color:#3fb950}
"""

JS = """
const st={project:'all',status:'all'};
function apply(){document.querySelectorAll('.card').forEach(c=>{
 const ok=(st.project==='all'||c.dataset.project===st.project||c.dataset.project==='both')&&(st.status==='all'||c.dataset.status===st.status);
 c.style.display=ok?'':'none';});}
document.querySelectorAll('.filters button').forEach(b=>b.onclick=()=>{
 const k=b.dataset.k; st[k]=b.dataset.v; document.querySelectorAll('.filters button[data-k='+k+']').forEach(x=>x.classList.toggle('on',x===b)); apply();});
const z=document.getElementById('zoom'),zi=z.querySelector('img');
document.querySelectorAll('figure img').forEach(i=>i.onclick=()=>{zi.src=i.src;zi.style.width=(i.naturalWidth*Math.max(1,Math.floor(1600/Math.max(i.naturalWidth,1))))+'px';z.style.display='block';});
z.onclick=()=>z.style.display='none';
"""


def esc(s):
    return html.escape(str(s))


def card(e, pinned=False):
    col = STATUS.get(e['status'], ('#888', 9))[0]
    out = [f'<div class="card{" pinned" if pinned else ""}" data-project="{esc(e["project"])}" data-status="{esc(e["status"])}" id="{esc(e["id"])}">',
           f'<h3>{esc(e["title"])}</h3>',
           f'<div class="meta"><span class="badge" style="background:{col}">{esc(e["status"])}</span>'
           f'<span class="badge proj">{esc(e["project"])}</span>{esc(e.get("kind", ""))} · {esc(e["date"])} · <a href="#{esc(e["id"])}">#</a></div>']
    rows = [(k, e.get(k)) for k in ('question', 'method', 'result', 'verdict', 'next') if e.get(k)]
    if rows:
        out.append('<dl>' + ''.join(f'<dt>{k}</dt><dd>{esc(v)}</dd>' for k, v in rows) + '</dl>')
    if e.get('scores'):
        out.append('<div class="scores">' + ''.join(f'<span>{esc(k)}: <b>{esc(v)}</b></span>' for k, v in e['scores'].items()) + '</div>')
    if e.get('media'):
        out.append('<div class="media">')
        for m in e['media']:
            missing = not os.path.exists(os.path.join(HERE, m['src']))
            cap = esc(m.get('caption', '')) + (' <b style="color:#f85149">[missing file]</b>' if missing else '')
            out.append(f'<figure class="{"wide" if m.get("wide") else ""}"><img loading="lazy" src="{esc(m["src"])}"><figcaption>{cap}</figcaption></figure>')
        out.append('</div>')
    if e.get('links'):
        out.append('<p>' + ' · '.join(f'<a href="{esc(l["href"])}">{esc(l["label"])}</a>' for l in e['links']) + '</p>')
    out.append('</div>')
    return '\n'.join(out)


def main():
    entries = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(HERE, 'entries', '*.json')))]
    entries.sort(key=lambda e: (e['date'], e['id']), reverse=True)
    projects = sorted({e['project'] for e in entries} - {'both'})
    statuses = [s for s in STATUS if any(e['status'] == s for e in entries)]
    btn = lambda k, v, on=False: f'<button data-k="{k}" data-v="{v}" class="{"on" if on else ""}">{v}</button>'
    legacy = sorted(os.path.basename(p) for p in glob.glob(os.path.join(HERE, 'legacy', '*.html')))
    parts = [f'<!doctype html><meta charset="utf-8"><title>pixelart review hub</title><style>{CSS}</style>',
             '<header><h1>pixelart review hub: every attempt and test</h1><div class="filters">',
             'project: ' + btn('project', 'all', True) + ''.join(btn('project', p) for p in projects),
             ' &nbsp; status: ' + btn('status', 'all', True) + ''.join(btn('status', s) for s in statuses),
             '</div></header><main>',
             '<p>Newest first. Click any image to zoom (nearest-neighbour). Rebuild with <code>python3 REVIEW/build.py</code>. '
             'Team summary: <a href="../docs/team_review/2026-10-28/00_SUMMARY.md">docs/team_review/2026-10-28/00_SUMMARY.md</a>.</p>',
             '<h2>Current best</h2>']
    parts += [card(e, True) for e in entries if e.get('pinned')]
    parts.append('<h2>All attempts and tests (newest first)</h2>')
    parts += [card(e) for e in entries]
    parts.append('<h2>Earlier history</h2><ul>' + ''.join(f'<li><a href="legacy/{esc(l)}">{esc(l)}</a></li>' for l in legacy) + '</ul>')
    parts.append(f'</main><div id="zoom"><img></div><script>{JS}</script>')
    open(os.path.join(HERE, 'index.html'), 'w').write('\n'.join(parts))
    print(f'wrote REVIEW/index.html: {len(entries)} entries, {sum(1 for e in entries if e.get("pinned"))} pinned')


if __name__ == '__main__':
    main()
