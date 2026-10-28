import math, sys
W=H=80
M=[['.']*W for _ in range(H)]
def inpoly(x,y,P):
    c=False; n=len(P)
    for i in range(n):
        x1,y1=P[i]; x2,y2=P[(i+1)%n]
        if (y1>y)!=(y2>y) and x < (x2-x1)*(y-y1)/(y2-y1)+x1: c=not c
    return c
def poly(P,m):
    for y in range(H):
        for x in range(W):
            if inpoly(x+.5,y+.5,P): M[y][x]=m
def sell(cx,cy,rx,ry,m,p=2,cond=lambda x,y:True):
    for y in range(H):
        for x in range(W):
            if abs((x+.5-cx)/rx)**p+abs((y+.5-cy)/ry)**p<=1 and cond(x,y): M[y][x]=m
def rect(x0,y0,x1,y1,m):
    for y in range(y0,y1+1):
        for x in range(x0,x1+1): M[y][x]=m
# legs + boots
rect(35,62,39,72,'leg'); rect(43,62,47,72,'leg')
sell(37.0,75.0,4.0,3.4,'boot',3); 
sell(46.6,75.0,4.2,3.4,'boot',3)
rect(34,72,39,74,'boot'); rect(43,72,48,74,'boot')
# dress
poly([(36,41.5),(50.5,41.5),(53.5,49),(57,63.6),(27.5,63.6),(31,49)],'dress')
for y in range(50,54):
    for x in range(W):
        if M[y][x]=='dress': M[y][x]='obi'
poly([(43.5,40),(48.5,40),(46.4,45.2)],'face')
# katana geometry
hx,hy=25.6,59.0; dx,dy=-0.38,1.0; L=math.hypot(dx,dy); dx/=L; dy/=L
def seg(t0,t1,w,m,tip=None):
    for y in range(H):
        for x in range(W):
            px,py=x+.5-hx,y+.5-hy; t=px*dx+py*dy; d=-px*dy+py*dx
            if t0<=t<=t1 and abs(d)<=w:
                if tip and t>tip[0] and d<-w+ (t1-t)*tip[1]*0+(-(t-tip[0])/(t1-tip[0]))*0+0 and False: continue
                M[y][x]=m
seg(-6.0,0,1.9,'hilt')
# sleeves
poly([(38,41.6),(32,43),(28,47.5),(24.5,52.5),(21.6,57.6),(30.6,57.6),(32,53),(35,47)],'sleeveL')
poly([(48.5,41.6),(52.5,43),(55.5,47.5),(58.5,52.5),(60.6,56.6),(53.2,56.6),(52,52),(50.5,46)],'sleeveR')
BLADE=True
# taper tip: cut the right side near the end
for y in range(H):
    for x in range(W):
        px,py=x+.5-hx,y+.5-hy; t=px*dx+py*dy; d=-px*dy+py*dx
        if M[y][x]=='blade' and t>16.5 and d > 2.05-(t-16.5)*1.0: M[y][x]='.'
for j in range(15):
    y=63+j; x0=22-((j+1)//2)
    w=4 if j<12 else (3 if j<14 else 2)
    for i in range(w): M[y][x0+i]='blade'

sell(25.6,59.0,2.9,2.7,'hand',2.4)
sell(23.6,62.6,3.6,1.6,'guard',2.2)
sell(56.6,58.4,2.8,2.7,'hand',2.4)
# hair mass, face, side locks
sell(40,26.4,16.6,15.6,'hair',2.7, lambda x,y: not (x>=47 and y>=39))
poly([(38,24.6),(53,24.6),(53,37),(51,39.6),(48.5,41.6),(45,41.6),(42,39.6),(39.6,37.4),(38,34)],'face')
poly([(52.2,22),(56.6,22),(56.4,30),(55.4,36),(53.6,39.6),(52.6,34)],'hair')
# bun + bow
sell(35.8,10.0,4.3,4.2,'bun',2.2)
poly([(43,9.4),(48.5,6.0),(54.0,6.0),(56.0,8.0),(56.0,12.4),(54.4,14.6),(49.5,14.2),(43,13.4)],'bow')
poly([(40,11.0),(34.5,11.6),(29.6,12.8),(26.0,15.0),(25.6,19.6),(28.0,20.6),(31.5,19.6),(36,16.4),(40,14.6)],'bow')
rect(39,9,43,14,'knot')

base={'hair':'H','bun':'H','face':'s','leg':'s','hand':'s','dress':'E','sleeveL':'E','sleeveR':'E','obi':'d','boot':'d','bow':'E','knot':'E','blade':'n','guard':'k','hilt':'h'}
C=[[base.get(m,'.') for m in row] for row in M]
def at(x,y): return M[y][x] if 0<=x<W and 0<=y<H else '.'
KAT=('blade','guard','hilt')
rules={('dress','leg'):'K',('leg','boot'):'K',('sleeveL','dress'):'r',('sleeveR','dress'):'r',('sleeveL','obi'):'r',('sleeveR','obi'):'r',
 ('hand','dress'):'K',('hand','sleeveL'):'K',('hand','sleeveR'):'K',('hand','obi'):'K',
 ('hair','face'):'h',('face','dress'):'K',('hair','dress'):'K',('hair','sleeveL'):'K',('hair','sleeveR'):'K',('hair','obi'):'K',
 ('bow','hair'):'K',('bow','bun'):'K',('knot','hair'):'K',('knot','bun'):'K',('knot','bow'):'r',('bun','hair'):'h',
 ('dress','obi'):'r',('face','obi'):'K',('face','sleeveL'):'K',('face','sleeveR'):'K',
 ('blade','*'):'K',('guard','*'):'K',('hilt','*'):'K',('leg','dress'):None}
LINE=set()
for y in range(H):
    for x in range(W):
        m=M[y][x]
        if m=='.': continue
        for ddx,ddy in((1,0),(-1,0),(0,1),(0,-1)):
            n=at(x+ddx,y+ddy)
            if n=='.': C[y][x]='K'; LINE.add((x,y)); break
            if n==m: continue
            r=rules.get((m,n), rules.get((m,'*')))
            if r: C[y][x]=r; LINE.add((x,y))
def interior(x,y,m): return M[y][x]==m and (x,y) not in LINE
def span(y,mats):
    xs=[x for x in range(W) if M[y][x] in mats]; return (min(xs),max(xs)) if xs else None
# ---- shading
for y in range(H):
    for x in range(W):
        m=M[y][x]
        if (x,y) in LINE: continue
        if m in('hair','bun'):
            # right side / underside shadow
            run=0; xx=x+1
            while xx<W and M[y][xx]==m and (xx,y) not in LINE: run+=1; xx+=1
            below=0; yy=y+1
            while yy<H and M[yy][x]==m and (x,yy) not in LINE: below+=1; yy+=1
            if m=='hair' and (run<=2 and M[y][min(W-1,x+run+1)] in ('.',m) and x>44 or below<=1 and y>34): C[y][x]='h'
            if m=='bun' and run<=1: C[y][x]='h'
            if at(x,y-1) in('bow','knot') or at(x,y-2) in ('bow','knot') and at(x,y-1)!='hair': C[y][x]='h'
            if m=='hair':
                r=math.hypot(x+.5-41.5,(y+.5-28)*1.0); a=math.degrees(math.atan2(y+.5-28,x+.5-41.5))
                if 12.2<=r<=14.3 and -170<=a<=-80: C[y][x]='L'
        elif m=='face':
            if y==25: C[y][x]='S'
            if at(x+1,y)=='hair' or at(x+2,y)=='hair' and y>30: C[y][x]='S'
        elif m in('dress','sleeveL','sleeveR'):
            s=span(y,(m,)); 
            w=s[1]-s[0]+1; rel=(x-s[0])/max(1,w-1)
            if m=='dress':
                if rel>0.68 or y in(54,) : C[y][x]='R'
            if m=='sleeveL':
                if rel>0.62: C[y][x]='R'
                if at(x,y+1)=='hand' or at(x,y+2)=='hand' and C[y][x]!='K': pass
            if m=='sleeveR':
                if rel>0.55: C[y][x]='R'
            if m in('sleeveL','sleeveR') and y>=55: C[y][x]='r'
            if m in('sleeveL','sleeveR') and y<=46 and rel<0.5: C[y][x]='e'
        elif m=='obi':
            s=span(y,('obi',))
            if x>s[1]-6 or y==53: C[y][x]='h'
        elif m=='leg':
            if y==62 or y==63 or at(x+1,y)!='leg' or at(x+2,y)!='leg': C[y][x]='S'
        elif m=='boot':
            if at(x+1,y)!='boot' or at(x+2,y)!='boot' or at(x,y+2)!='boot': C[y][x]='h'
        elif m=='bow' or m=='knot':
            if m=='bow':
                if x>43:
                    if y<=7 or (y==8 and x<50): C[y][x]='e'
                    if y>=12 or (x>=54 and y>=10): C[y][x]='R'
                else:
                    if at(x,y-1)!='bow' and y<=13 or (at(x,y-2)!='bow' and y<=12 and x>30): C[y][x]='e'
                    if y>=17 or (x<=28 and y>=15) or (x>=35 and y>=15): C[y][x]='R'
            else:
                if x==42 or y==13: C[y][x]='R'
                if x==40 and y==10: C[y][x]='e'
        elif m=='blade':
            if (at(x-1,y)!='blade' or (x-1,y) in LINE) : C[y][x]='W'
# ---- face features (absolute coords)
def put(x0,y0,rows):
    for j,r in enumerate(rows):
        for i,c in enumerate(r):
            if c!=' ': C[y0+j][x0+i]=c
put(38,27,[" KKKKK",
           "KKiiWW",
           " iiiWW",
           " iiIII",
           " IIIII",
           " IIIII",
           "  SSS "])
put(48,27,["KKKK ",
           "WWiKK",
           "WWii ",
           "IIii ",
           "IIII ",
           "IIII ",
           " SS  "])
put(46,37,["SS"])
open(sys.argv[1],'w').write('\n'.join(''.join(r) for r in C)+'\n')
