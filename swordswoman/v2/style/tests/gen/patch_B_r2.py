import sys
p=sys.argv[1]; g=[list(l) for l in open(p).read().split()]
def put(x,y,c): g[y][x]=c
def row(x0,y,s):
    for i,c in enumerate(s):
        if c!=' ': g[y][x0+i]=c
# fringe: last hair row per column (3 tapered points + far lock), base H, right third h, bottom edge h
fr={40:32,41:31,42:30,43:29,44:29,45:29,46:30,47:32,48:32,49:31,50:30,51:29,52:29,53:30,54:31,55:32}
for x,yb in fr.items():
    for y in range(25,yb+1):
        g[y][x]='H' if x<51 else 'h'
    g[yb][x]='h'
    for y in range(yb+1,33):
        if g[y][x] in 'Hhd': g[y][x]='s'
    g[yb+1][x]='S'                      # 1 px cast shadow under the fringe
# near-side cheek boundary: 2 px h, rest H
for y in range(29,40):
    if g[y][37]=='h': g[y][37]='H'
# sheen (R3/S3): 3 short broken L dashes on the skull curve, d on their outer (lit) side
import math
cx,cy=40.6,27.6
for a0,a1 in((192,208),(218,236),(246,264)):
    for a in range(a0*4,a1*4+1):
        t=math.radians(a/4)
        for r,c in((12.0,'L'),(11.3,'L'),(10.5,'d')):
            x=round(cx+r*math.cos(t)-.5); y=round(cy+r*math.sin(t)-.5)
            if g[y][x] in 'Hd' and not (c=='d' and g[y][x]=='L'): g[y][x]=c
# bow creases (r) from the knot into each loop
def line(x0,y0,x1,y1,c,ok):
    n=max(abs(x1-x0),abs(y1-y0))
    for i in range(n+1):
        x=round(x0+(x1-x0)*i/n); y=round(y0+(y1-y0)*i/n)
        if g[y][x] in ok: g[y][x]=c
line(45,12,51,10,'r','eER'); line(38,14,26,18,'r','eER'); line(26,18,22,24,'r','eER')
# eyes (R4): heavy K lash, 2 px at outer corner + flick, iris mostly i, I bottom, W glint upper-inner, S lower lid
row(42,31,'KKKKK'); put(41,32,'K')
row(42,32,'KiiWW')
row(42,33,'KiiWW')
row(42,34,'iiiii')
row(42,35,'iIIIi')
row(43,36,'SSS')
# far eye 1 px lower = slight head tilt toward the facing side (R6)
row(50,32,'KKKK'); put(54,33,'K')
row(50,33,'WiiK')
row(50,34,'WiiK')
row(50,35,'iiii')
row(50,36,'IIIi')
row(51,37,'SS')
# mouth, off-centre toward the facing side
row(48,39,'Sr'); row(50,38,'ss'); row(50,39,'s')
# collar V with light trim
row(44,43,'erSSSrE'); row(45,44,'erSrE'); row(46,45,'erE'); row(46,46,'ErR')
# hair strand clusters (h) running down the bob, broken before the outline
for pts in(((29,28),(27,33),(26,37)),((34,27),(33,33),(32,38)),((38,29),(37,34))):
    for (x0,y0),(x1,y1) in zip(pts,pts[1:]): line(x0,y0,x1,y1,'h','H')
# skirt folds: short R creases lit from the upper-left (e on the lit side)
line(39,57,37,62,'R','eE'); line(47,57,47,62,'R','eE')
for y in range(58,63):
    for x in range(30,50):
        if g[y][x]=='R' and g[y][x-1]=='E' and x<45: g[y][x-1]='e'
# R1: no K inside the silhouette except lashes/pupils
H,W=len(g),len(g[0])
def n8(x,y): return [g[y+dy][x+dx] for dy in(-1,0,1) for dx in(-1,0,1) if (dy or dx) and 0<=y+dy<H and 0<=x+dx<W]
for y in range(H):
    for x in range(W):
        if g[y][x]=='K' and '.' not in n8(x,y) and not (41<=x<=54 and 31<=y<=34):
            nb=n8(x,y)
            g[y][x]='r' if any(c in 'eERr' for c in nb) else 'h' if any(c in 'HhLd' for c in nb) else 'S'
# S4: merge orphans outside the face and blade into the dominant neighbour
from collections import Counter
for y in range(H):
    for x in range(W):
        c=g[y][x]
        if c in '.KWnIiL' or (40<=x<=55 and 29<=y<=40): continue
        nb=n8(x,y)
        if c not in nb:
            cand=[d for d in nb if d not in '.K']
            if cand: g[y][x]=Counter(cand).most_common(1)[0][0]
g=[['.']+r[:-1] for r in g]   # centre the bbox (x 10..69)
open(p,'w').write('\n'.join(''.join(r) for r in g)+'\n')
