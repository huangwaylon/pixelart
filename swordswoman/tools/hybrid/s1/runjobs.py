"""run gen.py jobs, 4 concurrent. jobs file lines: name|extra-args(shell-quoted)|out"""
import shlex, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
def run(line):
    n, x, o = line.split('|')
    cmd = [R + '/.venv/bin/python', R + '/tools/hybrid/s1/gen.py', n, 'clay', o] + shlex.split(x)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=R)
    return (r.stdout + r.stderr).strip()[-200:]
lines = [l for l in open(sys.argv[1]).read().splitlines() if l.strip()]
with ThreadPoolExecutor(4) as ex:
    for res in ex.map(run, lines): print(res)
