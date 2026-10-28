"""fc.py: face compositor. Stamps are lists of strings; '.'=keep base. Base '.' inside face = filled by stamp or skin."""
import sys, json
sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/style/tools')
import pk
from PIL import Image
def load(p): return [list(l.rstrip('\n')) for l in open(p) if l.strip() and not l.startswith(';')]
def put(g, st, x0, y0, mirror=False):
    for dy,row in enumerate(st):
        r=row[::-1] if mirror else row
        for dx,c in enumerate(r):
            if c=='.' : continue
            y,x=y0+dy,x0+dx
            if 0<=y<len(g) and 0<=x<len(g[0]): g[y][x]='.' if c=='_' else c
    return g
def fill(g, ch='s'):
    # fill interior transparent holes (not connected to border) with ch
    h,w=len(g),len(g[0]); seen=set(); st=[(y,x) for y in range(h) for x in (0,w-1)]+[(y,x) for x in range(w) for y in (0,h-1)]
    while st:
        y,x=st.pop()
        if (y,x) in seen or not(0<=y<h and 0<=x<w) or g[y][x]!='.': continue
        seen.add((y,x)); st+= [(y+1,x),(y-1,x),(y,x+1),(y,x-1)]
    for y in range(h):
        for x in range(w):
            if g[y][x]=='.' and (y,x) not in seen: g[y][x]=ch
    return g
def save(g, out, scales=(1,8)):
    s=[''.join(r) for r in g]; pk.write(out+'.txt', s)
    for k in scales: pk.to_img(s,k,bg=(k>1)).save(f'{out}_{k}x.png')
    return s
