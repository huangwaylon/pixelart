# round-6 ZOOM-IN base: face (brow..chin) spans ~24 rows, bob cropped by the frame on top + both
# sides, bow only partly visible, collar on the bottom edge. Drawn procedurally on an oversized
# canvas so the head (ox,oy) and the bust (by) can move independently without gaps.
M=8                      # canvas margin
CW=40+2*M
def canvas(): return [['.']*CW for _ in range(CW)]
def crop(g): return [r[M:M+40] for r in g[M:M+40]]
# fringe: lowest hair row per x (x=7..31), clumps with sharp tips swept toward screen-right
BANG=[17,15,12,6,7,7,8,6,6,7,7,8,5,6,7,7,8,5,6,7,8,9,12,15,17]
# face skin rows (y: xl,xr) incl. the outline pixel; 3/4 view turned screen-right, chin at x~22
FACE={y:(8,30) for y in range(3,14)}
FACE.update({y:(7,31) for y in range(14,26)})
FACE.update({26:(8,31),27:(8,30),28:(9,30),29:(10,29),30:(11,29),31:(13,28),32:(15,27),33:(19,24)})
def head(ox,oy):
    g=canvas()
    def P(x,y,c):
        X,Y=x+ox+M,y+oy+M
        if 0<=X<CW and 0<=Y<CW: g[Y][X]=c
    def G(x,y):
        X,Y=x+ox+M,y+oy+M
        return g[Y][X] if 0<=X<CW and 0<=Y<CW else '.'
    # hair mass: round crown (ellipse) + bob locks running off both sides of the frame
    for y in range(-M-4,40):
        for x in range(-M-4,48):
            cr=((x-19.5)/24)**2+((y-14)/20)**2<=1
            lockL= y<=31 or (y==32 and x<=8) or (y==33 and 1<=x<=6)
            lockR= y<=30 or (y==31 and x>=31) or (y==32 and x>=33)
            if (cr and y<14) or (y>=14 and (x<20 and lockL or x>=20 and lockR)): P(x,y,'H')
    for y,(a,b) in FACE.items():
        for x in range(a,b+1): P(x,y,'s')
    for i,yb in enumerate(BANG):
        for y in range(-2,yb+1): P(7+i,y,'H')
    # bow on top of the crown, only its lower half inside the frame
    BOW=['__KRREEEeeeeeRK_KRRK_KReeeeeEEERRK__',
         '_KRREEEEeeeEERRKrRRrKRREEeeeEEEERRK_',
         '_KRRRREEEEERRRrKrrrrKrRRREEEEERRRRK_',
         '__KKRRRRRRRrrKKKKKKKKKrrRRRRRRRKK___',
         '____KKKKKKKKK___________KKKKKKKK____']
    for j,row in enumerate(BOW):
        for i,c in enumerate(row):
            if c!='_': P(2+i,-2+j,c)
    # neck behind the chin
    for y in range(30,42):
        for x in range(18,26):
            if G(x,y)=='.': P(x,y,'n')
    # outline: silhouette vs background, skin vs hair (on the skin side)
    src=[r[:] for r in g]
    for Y in range(1,CW-1):
        for X in range(1,CW-1):
            c=src[Y][X]
            if c=='.': continue
            nb=[src[Y][X+1],src[Y][X-1],src[Y+1][X],src[Y-1][X]]
            if '.' in nb and c!='n': g[Y][X]='K'
            elif c=='s' and ('H' in nb or 'n' in nb): g[Y][X]='K'
            elif c=='n' and ('.' in nb[:2] or 'H' in nb[:2]): g[Y][X]='k'
    # neck: shadow under the chin (2 rows) and on the near side, light below
    for y in range(30,42):
        for x in range(18,26):
            if G(x,y)=='n': P(x,y,'Q' if (G(x,y-2) in 'sSK' or x<=19) else 'q')
    # hair shading: sheen arc on the crown broken into strands, far side in shadow
    SHEEN={0:[(4,7),(30,34)],1:[(2,3),(8,12),(26,29),(35,36)],2:[(1,1),(13,16),(18,21),(23,25),(37,37)],
           3:[(0,0),(9,11),(17,17),(22,22),(38,38)]}
    for y,ss in SHEEN.items():
        for a,b in ss:
            for x in range(a,b+1):
                if G(x,y)=='H': P(x,y,'L')
    for x,y0,y1 in [(14,3,6),(19,4,5),(24,3,5),(10,4,6)]:   # partings into the clumps
        for y in range(y0,y1+1):
            if G(x,y) in 'HL': P(x,y,'h')
    for x,y in [(11,4),(12,4),(12,5),(16,3),(17,3),(17,4),(21,3),(22,3),(22,4),(26,4),(27,5)]:  # sheen on the clumps
        if G(x,y)=='H': P(x,y,'L')
    for i,yb in enumerate(BANG):                                      # shadow along the fringe edge
        for y in ([yb,yb-1] if i in (0,1,2,22,23,24) else [yb]):
            if G(7+i,y)=='H': P(7+i,y,'h')
    for y in range(-4,34):                                            # far side of the head
        for x in range(32,48):
            if G(x,y) in 'HL' and x>=36-(y+2)//8: P(x,y,'h')
        if 8<y<31 and G(32,y)=='H': P(32,y,'h')
    for y in range(10,33):                                            # near lock: inner shadow + sheen strand
        for x in range(4,7):
            if G(x,y)=='H': P(x,y,'h')
        if 9<y<21 and G(1,y)=='H': P(1,y,'L')
        if 20<y<29 and G(2,y)=='H': P(2,y,'L')
        if 10<y<30 and G(35,y)=='h': P(35,y,'H')
    for y in range(4,12):
        if G(3,y)=='H': P(3,y,'h')
    # skin form shadow: far cheek edge, under the fringe on the far side, jaw
    for y in range(4,35):
        xs=[x for x in range(-M,40+M) if G(x,y)=='s']
        if xs and y>=12: P(xs[-1],y,'S')
    for i,yb in enumerate(BANG):
        if i>=19 and G(7+i,yb+2)=='s': P(7+i,yb+2,'S')
    return g
def bust(by):
    # red kimono: shoulders run off both sides, lapels crossing into a V at the neck
    g=canvas()
    def P(x,y,c):
        X,Y=x+M,y+by+M
        if 0<=X<CW and 0<=Y<CW: g[Y][X]=c
    T=lambda x: 35 if 14<=x<=29 else (36 if 7<=x<=34 else 37)
    for x in range(-M,40+M):
        for y in range(T(x),48): P(x,y,'E' if x<30 else 'R')
        P(x,T(x),'K')
        if x<14 or 30<x: P(x,T(x)+1,'e' if x<14 else 'E')
    for y in range(35,48):
        d=y-35; a,b=18+d,25-d//2                     # V opening (left lapel crosses over)
        for x in range(a,b+1): P(x,y,'n')
        if a<=b: P(a-1,y,'K'); P(b+1,y,'K')
        P(a-2,y,'e'); P(a-3,y,'e'); P(a-4,y,'K'); P(b+2,y,'E'); P(b+3,y,'R'); P(b+4,y,'K')
    return g
def compose(ox=0,oy=0,by=0):
    # head over bust, except the neck/background of the head layer, which the bust covers
    # (the bust's V opening shows the neck, or plain skin shadow if the neck is too short)
    h=head(ox,oy); b=bust(by); out=[r[:] for r in h]
    for Y in range(CW):
        for X in range(CW):
            c=b[Y][X]; hc=h[Y][X]
            if c=='.' or hc not in '.qQk': continue
            out[Y][X]=(hc if hc!='.' else 'S') if c=='n' else c
    T={'q':'s','Q':'S','k':'K','n':'S'}
    return crop([[T.get(c,c) for c in r] for r in out])
if __name__=='__main__':
    import sys
    a=[int(v) for v in sys.argv[2:5]] if len(sys.argv)>2 else []
    open(sys.argv[1],'w').write('\n'.join(''.join(r) for r in compose(*a))+'\n')
