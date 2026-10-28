"""eyes3/pxvar.py NAME 'x,y,c;x,y,c' : copy eyes3/F masters to eyes3/v_NAME with S pixel edits (ssim experiments)"""
import shutil, sys, os
B = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/'; n, ed = sys.argv[1], sys.argv[2]; o = B + 'eyes3/v_' + n; os.makedirs(o, exist_ok=True)
src = sys.argv[3] if len(sys.argv) > 3 else B + 'eyes3/F'
for v in ['S', 'SE', 'E']:
    for ext in ['json', 'png', 'txt']: shutil.copy(f'{src}/EC0_{v}_96.{ext}', f'{o}/EC0_{v}_96.{ext}')
p = f"{o}/EC0_{os.environ.get('VW', 'S')}_96.txt"; g = [list(l.rstrip('\n')) for l in open(p) if l.strip()]
for t in filter(None, ed.split(';')):
    x, y, c = t.split(','); g[int(y)][int(x)] = c
open(p, 'w').write('\n'.join(''.join(r) for r in g) + '\n')
