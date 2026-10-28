# round-4 expression generator: base head (shifted by dx,dy, fringe lifted 1px over the brows)
# + per-expression face blocks (near eye, far eye, mouth) with a feature offset/tilt, + FX
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from compose import rd
D='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face/portrait/'
PALB='; pal b #b0e0f8 water light (sweat/tears)\n'
PALP='; pal p #f0a0a0 blush\n'
def put(g,x0,y0,block):
    for dy,row in enumerate(block.strip('\n').split('\n')):
        for dx,c in enumerate(row):
            if c!='_' and 0<=y0+dy<40 and 0<=x0+dx<40: g[y0+dy][x0+dx]=c
# anchors (unshifted): near eye x12..19,y17..27 ; far eye x24..30,y17..27 ; mouth x17..28,y27..34
NE=(12,17); FE=(24,17); MO=(17,27)
def shift(rows,dx,dy):
    out=[['.']*40 for _ in range(40)]
    for y,r in enumerate(rows):
        for x,c in enumerate(r):
            y2,x2=y+dy,x+dx
            if 0<=y2<40 and 0<=x2<40: out[y2][x2]=c
    if dy>0:   # head moved down: extend the cropped crown upward
        for y in range(dy): out[y]=out[dy][:]
    return out
def compose(dx,dy):
    g=shift(rd('base_head.txt'),dx,dy)
    for y,r in enumerate(shift(rd('base_bow.txt'),dx,dy)):
        for x,c in enumerate(r):
            if c!='.': g[y][x]=c
    for y,r in enumerate(rd('base_neck.txt')):
        for x,ch in enumerate(r):
            if ch!='.' and g[34+y][x]=='.': g[34+y][x]=ch
    for y,r in enumerate(rd('base_bust.txt')):
        for x,c in enumerate(r):
            if c!='.': g[37+y][x]=c
    return g
def lift(g,xs,dy,n=1):
    # raise the fringe's lower edge by n px in columns xs (hair->K->skin)
    for _ in range(n):
        for x in xs:
            for y in range(11+dy,21+dy):
                if g[y][x]=='K' and g[y-1][x] in 'Hh' and g[y+1][x] in 'sS':
                    g[y][x]='s'; g[y-1][x]='K'
                    if g[y-2][x]=='H': g[y-2][x]='h'
                    break
    for y in range(11+dy,21+dy):   # re-outline exposed skin beside the clumps
        for x in xs:
            if g[y][x]=='s' and (g[y][x-1] in 'HhL' or g[y][x+1] in 'HhL'): g[y][x]='K'
from blocks import X, NOSE
def build(k):
    e=X[k]; dx,dy=e.get('dx',0),e.get('dy',0); g=compose(dx,dy)
    lift(g,range(13+dx,29+dx),dy,1+e.get('lift',0))
    fx,fy=dx+e.get('fdx',0),dy+e.get('fdy',0); t=e.get('tilt',0)
    put(g,NE[0]+fx,NE[1]+fy,e['ne']); put(g,FE[0]+fx,FE[1]+fy+t,e['fe'])
    if e.get('nose',1): put(g,24+fx,27+fy,NOSE)
    put(g,MO[0]+fx+e.get('mdx',0),MO[1]+fy,e['mo'])
    for f in e.get('fx',[]): f(g,dx,dy,fx,fy)
    pal=''.join(p for p,c in ((PALB,'b'),(PALP,'p')) if any(c in r for r in g))
    return pal+'\n'.join(''.join(r) for r in g)+'\n'
if __name__=='__main__':
    ks=sys.argv[1:] or list(X)
    for k in ks: open(D+f'P_{k}.txt','w').write(build(k))
