"""run_jobs.py (F round 7): run jobs.tsv through `tools/gemini.py image` (gemini-3-pro-image), 4 in parallel, skipping existing outputs."""
import os, subprocess
from concurrent.futures import ThreadPoolExecutor
D = os.path.dirname(os.path.abspath(__file__)); SW = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
jobs = [l.rstrip('\n').split('\t') for l in open(os.path.join(D, 'jobs.tsv')) if l.strip()]
def run(j):
    v, e, p = j; out = f'{D}/raw/{v}_{e}.png'
    if os.path.exists(out): return f'skip {v} {e}'
    r = subprocess.run([f'{SW}/.venv/bin/python', 'tools/gemini.py', 'image', p, out, f'{D}/src/{v}_head.png'], cwd=SW, capture_output=True, text=True)
    open(f'{D}/raw/{v}_{e}.log', 'w').write(r.stdout + r.stderr); return f'done {v} {e} {os.path.exists(out)}'
with ThreadPoolExecutor(4) as ex:
    for m in ex.map(run, jobs): print(m, flush=True)
print('JOBS_DONE', flush=True)
