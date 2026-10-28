import sys; sys.path.insert(0,'/tmp'); from stamplib import *
W,H=20,40
g=[['.']*W for _ in range(H)]
def put(x,y,c,only=None):
    if 0<=x<W and 0<=y<H and (only is None or g[y][x] in only): g[y][x]=c
gx,gy=7,10
for k in range(1,9):
    y=gy-k; x=gx-(k+1)//2
    pat=('dR' if k%2 else 'Rd')
    put(x-1,y,'K'); put(x,y,pat[0]); put(x+1,y,pat[1]); put(x+2,y,'K')
y=gy-9; x=gx-5; put(x,y,'K'); put(x+1,y,'T'); put(x+2,y,'T'); put(x+3,y,'K'); put(x+1,y-1,'K'); put(x+2,y-1,'K')
bar=[(gx-4,gy+2),(gx-3,gy+2),(gx-2,gy+1),(gx-1,gy+1),(gx,gy),(gx+1,gy),(gx+2,gy-1),(gx+3,gy-1)]
for (x,y) in bar: put(x,y,'T')
# kagi: crescent at the bar's upper-right end; horns go up-left and down-right, gap open to the upper-right
hook=[(gx+4,gy-2),(gx+5,gy-3),(gx+5,gy-1)]
for (x,y) in hook: put(x,y,'T')
for (x,y) in bar+hook:
    for dx,dy in ((0,-1),(0,1),(-1,0),(1,0)):
        put(x+dx,y+dy,'K',only='.')
put(gx-5,gy+2,'K')
for k in range(1,29):
    y=gy+k; x=gx+(k)//2
    if k<=2: put(x,y,'T'); put(x+1,y,'T')
    elif k<27: put(x,y,'w'); put(x+1,y,'t')
    else: put(x+1,y,'w')
rows=[''.join(r) for r in g]
for i,r in enumerate(rows): assert len(r)==W
open('katana_idle_2to1.pix','w').write("# canonical sprite-scale katana at the idle angle: blade down-right at 2:1 (~27 deg off vertical), hilt up-left (hand-placed pixels). Mirror for the other hand side.\nsize: %d %d\ngrid:\n"%(W,H)+"\n".join(rows)+"\n")
