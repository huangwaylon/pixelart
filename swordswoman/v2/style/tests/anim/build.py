# compose 64x48 slash frames: hand-drawn body rows + A_r4 head stamp + auto K outline
import sys, os
D=os.path.dirname(os.path.abspath(__file__))
M=[l.rstrip('\n') for l in open(os.path.join(D,'..','A_r4.txt')) if l.strip()]
STAMP=[M[r][11:29] for r in range(6,22)]   # bow..chin, 18x16
W,H=64,48
def head(g,dx,dy,bow=0):
    ox,oy=23+dx,14+dy
    for r,row in enumerate(STAMP):
        sh=bow if r<=3 else 0
        for c,ch in enumerate(row):
            if ch=='.': continue
            if r==3 and c>=13: sh=0          # hair-top outline right of bow stays
            x,y=ox+c+sh,oy+r
            if ch=='K' and g[y][x]!='.': continue
            g[y][x]=ch
def put(g,rows):
    for y,(x0,s) in rows:
        for i,c in enumerate(s):
            if c!='.': g[y][x0+i]=c
def outline(g):
    add=[]
    for y in range(H):
        for x in range(W):
            if g[y][x]!='.': continue
            for dx,dy in((1,0),(-1,0),(0,1),(0,-1)):
                X,Y=x+dx,y+dy
                if 0<=X<W and 0<=Y<H and g[Y][X] not in '.K': add.append((x,y)); break
    for x,y in add: g[y][x]='K'
def build(layers):
    g=[['.']*W for _ in range(H)]
    for L in layers:
        if L[0]=='head': head(g,*L[1:])
        else: put(g,L[1])
    outline(g)
    for L in layers:
        if L[0]=='post': put(g,L[1])
    return [''.join(r) for r in g]
