import sys, json, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/prop/tools')
from overlay import *
V = json.load(open(R + 'prop/blockout/verify.json'))
refs = [(n,) + REFS[n] for n in REFS]
bl = [('blk ' + v, f'masters/../prop/blockout/{v}.png', V[v]['rows'], V[v]['widths']) for v in ['S', 'SE', 'E', 'NE', 'N']]
out = sys.argv[1] if len(sys.argv) > 1 else R + 'prop/blockout_vs_refs.png'
stack([panel(refs[:2] + bl[:3] + refs[2:], 230), panel(refs[:1] + bl[3:] + refs[3:], 230)], out, 1000)
