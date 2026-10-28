# featureless round-3 base: big 3/4 head (turned screen-right), bow cropped at top
# writes base_head.txt (head layer, shifts with expression), base_bow.txt, base_bust.txt (static)
D='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face/portrait/tools/'
W=H=40
g=[['.']*W for _ in range(H)]
def span(y,a,b,c):
    for x in range(a,b+1):
        if 0<=x<W and 0<=y<H: g[y][x]=c
# hair silhouette (y: xl,xr): rounded crown, bob bulges out mid-height and tucks in at the
# ends; back of head shows more on the near (left) side, far (right) side is narrow
HAIR={1:(8,31),2:(5,34),3:(4,35),4:(3,36),5:(2,37),6:(2,37),7:(1,37)}
for y in range(8,30): HAIR[y]=(0 if 14<=y<=27 else 1, 37 if y<20 else 36)
HAIR.update({30:(1,36),31:(1,36),32:(2,35),33:(3,35),34:(5,34),35:(8,33)})
for y,(a,b) in HAIR.items(): span(y,a,b,'H')
# face skin (near cheek left, far cheek right, chin shifted right)
FACE={y:(10,31) for y in range(13,28)}
FACE.update({28:(10,31),29:(11,31),30:(11,30),31:(12,30),32:(13,29),33:(14,29),34:(16,28),35:(18,27),36:(20,26)})
for y,(a,b) in FACE.items(): span(y,a,b,'s')
# bangs: clumps with sharp tips, swept toward screen-right; BANG[x-10] = lowest hair row
BANG=[19,18,17,15,14,14,15,14,14,13,14,15,15,14,13,14,14,14,15,16,18,20]
for i,yb in enumerate(BANG):
    for y in range(13,yb+1): g[y][10+i]='H'
out=[r[:] for r in g]
inb=lambda a,b:0<=a<W and 0<=b<H
for y in range(H):
    for x in range(W):
        c=g[y][x]
        if c=='.': continue
        nb=[(x+1,y),(x-1,y),(x,y+1),(x,y-1)]
        if any(inb(a,b) and g[b][a]=='.' for a,b in nb): out[y][x]='K'
        elif c=='s' and any(inb(a,b) and g[b][a]=='H' for a,b in nb): out[y][x]='K'
g=out
def setc(pts,c,only='H'):
    for x,y in pts:
        if inb(x,y) and g[y][x] in only: g[y][x]=c
# sheen band (L) following the crown arc, broken into strands
SHEEN={6:[(4,6),(31,34)],7:[(3,4),(7,11),(26,30),(33,34)],8:[(2,3),(12,15),(17,20),(22,25),(35,35)],
       9:[(2,2),(9,10),(16,16),(21,21)],10:[(2,2)],11:[(1,2)],12:[(1,1)],13:[(1,1)],15:[(1,1)],16:[(1,1)]}
setc([(x,y) for y,s in SHEEN.items() for a,b in s for x in range(a,b+1)],'L')
# strand partings down into the bang clumps
for x,y0,y1 in [(14,11,15),(19,11,15),(24,12,13)]:
    setc([(x,y) for y in range(y0,y1+1)],'h')
# shadow along the bangs' lower edge
for i,yb in enumerate(BANG):
    setc([(10+i,yb),(10+i,yb-1)] if i in (0,1,20,21) else [(10+i,yb)],'h')
# far side of the head in shadow
for y in range(6,36):
    for x in range(33,W):
        if g[y][x]=='H' and x>=37-(y-6)//7: g[y][x]='h'
    if y>20: setc([(32,y)],'h')
# near lock: inner layer next to the cheek is shadow, outer edge keeps a sheen strand
for y in range(18,35):
    setc([(x,y) for x in range(5 if y>28 else 7,10)],'h')
setc([(3,y) for y in range(20,29)]+[(4,29),(4,30),(5,31)],'L')
setc([(5,y) for y in range(14,22)]+[(6,22),(6,23)],'h')
# skin form shadow: far jaw + under the bangs
for y in range(13,36):
    xs=[x for x in range(W) if g[y][x]=='s']
    if xs and y>=24: g[y][xs[-1]]='S'
for i,yb in enumerate(BANG):
    if inb(10+i,yb+2) and g[yb+2][10+i]=='s' and i>=17: g[yb+2][10+i]='S'
open(D+'base_head.txt','w').write('\n'.join(''.join(r) for r in g)+'\n')
BOW='''
.....KReeeeeEEERRK..KRRK..KRREEEeeeeeRK.
....KReeeeEEEEERRRKKrRRrKKRRREEEEEeeeRK.
....KReeEEEEEERRRrrKrRRrKrrRRREEEEEeeRK.
.....KRREEERRRRrrKKKrrrrKKKrrRRRREEERK..
......KKRRRRrrKKK...KKKK...KKKrrRRRKK...
........KKKKKK...............KKKKKK.....'''.strip('\n').split('\n')
open(D+'base_bow.txt','w').write('\n'.join(BOW)+'\n')
# bust (static): neck in shadow under the chin, red kimono collar crossing into a V
BUST='''
...KKKKKKKKKKKKKKKKKKSssSKKKKKKKKKKKK...
.KKeeeeeEEEEEEEERRRKrSssSrKRRREEEEEeeKK.
KeeeeeEEEEEEEEEERRRRKrSSrKRRRREEEEEEeeeK'''.strip('\n').split('\n')
open(D+'base_bust.txt','w').write('\n'.join(BUST)+'\n')
NECK='''
...................KSSSSSK..............
...................KSSSSsK..............
...................KSSSssK..............'''.strip('\n').split('\n')
open(D+'base_neck.txt','w').write('\n'.join(NECK)+'\n')
