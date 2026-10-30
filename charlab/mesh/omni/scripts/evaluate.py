"""Evaluate meshes: render (Blender) + metrics + turntable strip, char inferred from the name prefix.

Usage: venv/bin/python -I evaluate.py [--side] PATH.glb ...
Ref mask = refs/<id>/ front (if R2's refs exist and REF=r2) else work/inputs/<id>_front_mask.png.
Metrics rows go to work/metrics.jsonl, renders to work/rend/, strips to out/turntables/.
"""
import sys, os, subprocess, glob
O = '/Users/waylonhuang/Documents/other/pixelart/charlab/mesh/omni'
PY = '/Users/waylonhuang/Documents/other/pixelart/.models/hy_omni/venv/bin/python'
B = '/Applications/Blender.app/Contents/MacOS/Blender'
paths = [p for p in sys.argv[1:] if p.endswith('.glb')]
subprocess.run([B, '-b', '--factory-startup', '-P', f'{O}/scripts/render.py', '--', f'{O}/work/rend'] + paths,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
by = {}
for p in paths:
    cid = os.path.basename(p).split('_')[0]
    by.setdefault(cid, []).append(p)
for cid, ps in by.items():
    front = os.environ.get(f'REF_{cid}', f'{O}/work/inputs/{cid}_front_mask.png')
    cmd = [PY, '-I', f'{O}/scripts/metrics.py', f'{O}/work/rend', f'{O}/work/metrics.jsonl', front]
    side = f'{O}/work/inputs/{cid}_side_mask.png'
    if os.path.exists(side):
        cmd += ['--side', side]
    subprocess.run(cmd + ps, check=True)
subprocess.run([PY, '-I', f'{O}/scripts/board.py', 'strip', f'{O}/work/rend', f'{O}/out/turntables'] +
               [os.path.splitext(os.path.basename(p))[0] for p in paths], check=True)
