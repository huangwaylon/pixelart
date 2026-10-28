# round-6 ZOOM-IN expression generator. base6.compose(ox,oy,by) + per-expression blocks
# ('_' = keep base): brows (1px lines on clear skin), eyes (PMD construction), nose, mouth, FX.
# anchors are head-relative (move with ox,oy); see A below.
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from base6 import compose
D='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face/portrait/'
PAL={'b':'; pal b #b0e0f8 water light (sweat/tears)\n','p':'; pal p #f0a0a0 blush, tongue\n',
     'm':'; pal m #7a3040 interior lines (mouth, lower lids)\n'}
A={'nb':(9,11),'fb':(22,11),'ne':(9,14),'fe':(22,14),'no':(22,24),'mo':(15,26)}
def put(g,x0,y0,block):
    for j,row in enumerate(block.strip('\n').split('\n')):
        for i,c in enumerate(row):
            if c!='_' and 0<=y0+j<40 and 0<=x0+i<40: g[y0+j][x0+i]=c
from blocks6 import X
def build(k):
    e=X[k]; ox,oy,by=e.get('ox',0),e.get('oy',0),e.get('by',0)
    g=compose(ox,oy,by)
    fx,fy=ox+e.get('fdx',0),oy+e.get('fdy',0); t=e.get('tilt',0)
    for part in ('nb','fb','ne','fe','no','mo'):
        if part in e:
            ax,ay=A[part]; dy=t if part in ('fb','fe') else 0
            put(g,ax+fx+e.get(part+'dx',0),ay+fy+dy+e.get(part+'dy',0),e[part])
    for f in e.get('fx',[]): f(g,ox,oy,fx,fy)
    pal=''.join(v for c,v in PAL.items() if any(c in r for r in g))
    return pal+'\n'.join(''.join(r) for r in g)+'\n'
if __name__=='__main__':
    ks=sys.argv[1:] or list(X)
    for k in ks: open(D+f'P_{k}.txt','w').write(build(k))
