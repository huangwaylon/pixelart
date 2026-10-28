# round-3 expression generator: composes base (head shifted by DY) + per-expression face blocks
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from compose import compose
D='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face/portrait/'
PAL='; pal b #b0e0f8 water light (sweat/tears)\n'
PALP='; pal p #f0a0a0 blush\n'
def put(g,x0,y0,block):
    for dy,row in enumerate(block.strip('\n').split('\n')):
        for dx,c in enumerate(row):
            if c!='_' and 0<=y0+dy<40 and 0<=x0+dx<40: g[y0+dy][x0+dx]=c
# anchors (unshifted): near eye block at NE (x12..19, y16..27, 8x12), far eye at FE (x24..30, 7x12),
# mouth block at MO (x19..27, y29..33, 9x5). blocks use '_' = keep base.
NE=(11,16); FE=(24,16); MO=(19,29)
E={}; FX={}; DY={}
from blocks import *
def build(k):
    dy=DY.get(k,0); g=compose(dy)
    ne,fe,m=E[k]
    put(g,NE[0],NE[1]+dy,ne); put(g,FE[0],FE[1]+dy,fe); put(g,MO[0],MO[1]+dy,m)
    put(g,22,26+dy,NOSE)
    if k in FX: FX[k](g,dy)
    pal=PAL if k in ('effort','pain','teary','worried') else ''
    if k in ('joy','inspired'): pal+=PALP
    return pal+'\n'.join(''.join(r) for r in g)+'\n'
if __name__=='__main__':
    ks=sys.argv[1:] or list(E)
    for k in ks: open(D+f'P_{k}.txt','w').write(build(k))
