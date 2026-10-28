"""portrait.py: PMD-style 40x40 portrait, option-E hair placeholder. Base built from geometry, then stamps:
eye 9 cols (c0 = outer wing margin, c1-7 = 7-wide eye, c8 = inner margin) x 9 rows at rows 18-26 (left eye x0=9, right eye mirrored x0=30);
brows 9 x 3 at rows 15-17 (same x); mouth 8 x 4 at x 16, rows 28-31; blush hatch at rows 26-27."""
import sys; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face2/tools'); import kit, pal
W=H=40
HL={2:12,3:9,4:7,5:6,6:5,7:4,8:4,9:3,10:3}      # hair silhouette left edge per row (right = 39-L)
FL={25:9,26:9,27:10,28:11,29:12,30:15,31:17,32:18,33:19}  # face left edge below row 24 (rows 12-24: 9): taper 1,1,1,2,2,2 -> soft point
LOCKS=[(10,17),(14,16),(19,17),(25,16),(30,18)]  # bang locks (centre x, tip row): edge rises 1 px per px from each tip
def fl(y): return 9 if 12<=y<=24 else FL.get(y)
def bang_bottom(x): return max(t-abs(x-c) for c,t in LOCKS)
BUN=["..KKKK..",".KHLLHK.","KHHLHHhK","KHHHHhhK",".KhhhhK."]
BOWP=["KKKK..KKKK","KeeEKKeEEK","KeEEErEEEK","KEEERRERRK","KRRRKKRRRK",".KKKrrKKK.","...KRRK...","...KREK...","..KRK.KRK.","..KK...KK."]
def base():
    g=[['.']*W for _ in range(H)]
    def put(x,y,c):
        if 0<=x<W and 0<=y<H: g[y][x]=c
    for y in range(2,40):                                   # hair mass (back hair to the bottom)
        L=HL.get(y,3) if y<36 else 4
        for x in range(L,40-L): put(x,y,'H')
    for y in range(30,40):                                  # neck
        for x in range(16,24): put(x,y,'s')
    for y in range(35,40):                                  # kimono collar, V opening
        op=max(1.5,6-(y-35)*1.2)
        for x in range(4,36):
            if abs(x+0.5-20)>op: put(x,y,'E')
    for y in range(12,34):                                  # face
        L=fl(y)
        for x in range(L,40-L): put(x,y,'s')
    for x in range(8,32):                                   # bangs as 5 pointed locks
        for y in range(8,bang_bottom(x)+1): put(x,y,'H')
    for y in range(12,38):                                  # tapered sidelocks framing the face
        w=5 if y<30 else max(1,5-(y-29)//2)
        for k in range(w):
            put(5+k+(5-w)//1*0+((y-29)//3 if y>29 else 0),y,'H'); put(34-k-((y-29)//3 if y>29 else 0),y,'H')
    # shading
    for y in range(1,H):
        for x in range(W):
            c=g[y][x]
            if c=='s' and g[y-1][x]=='H': g[y][x]='S'                           # bang shadow
            if c=='s' and 30<=y<=33 and (fl(y) is None or x<fl(y) or x>=40-fl(y)): g[y][x]='S'   # neck under chin
            if c=='s' and 18<=y<=30 and fl(y) and x==39-fl(y)-1 and g[y][x+1] in 'H.': g[y][x]='S'  # right cheek shade
    for y in range(3,8):                                    # broken angel ring (dashes)
        for x in range(8,32):
            if g[y][x]=='H' and abs(((x+0.5-18)/10.5)**2+((y-10.5)/6)**2-1)<0.16 and (x%5)!=2: g[y][x]='L'
    for y in range(H):
        for x in range(W):
            if g[y][x]=='H':
                nb=[g[y+dy][x+dx] if 0<=y+dy<H and 0<=x+dx<W else '.' for dx,dy in ((1,0),(-1,0),(0,1))]
                if 's' in nb or 'S' in nb: g[y][x]='h'
            if g[y][x]=='E' and (x<=9 or x>=30): g[y][x]='R'
    for c,t in LOCKS[:-1]:                                   # lock separations: h line up from each valley
        pass
    for x in range(9,31):
        bb=bang_bottom(x)
        if bang_bottom(x-1)>bb<bang_bottom(x+1) or (bang_bottom(x-1)>bb and bang_bottom(x+1)==bb):
            for y in range(bb-2,bb+1):
                if g[y][x]=='H': g[y][x]='h'
    for y in range(12,36):                                   # right-side hair shadow column
        for x in range(30,37):
            if g[y][x]=='H' and (x==36-((y-29)//3 if y>29 else 0) or g[y][x+1]=='.'): g[y][x]='h'
    def spr(sp,x0,y0):
        for dy,r in enumerate(sp):
            for dx,c in enumerate(r):
                if c!='.': put(x0+dx,y0+dy,c)
    spr(BUN,25,0); spr(BOWP,29,1)                            # E FINAL: knot + bow on her left side-back (picture right)
    o=[r[:] for r in g]
    for y in range(H):
        for x in range(W):
            if g[y][x]!='.':
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    X,Y=x+dx,y+dy
                    if 0<=X<W and 0<=Y<H and g[Y][X]=='.': o[y][x]='K'
            if g[y][x] in 'ER' and y>0 and g[y-1][x] in 'sSHh': o[y][x]='K'
            if g[y][x] in 'ER' and x>0 and g[y][x-1] in 'sS': o[y][x]='K'
            if g[y][x] in 'ER' and x<W-1 and g[y][x+1] in 'sS': o[y][x]='K'
    for y in range(26,34):                                   # jaw/chin line
        L=fl(y); Ln=fl(y+1)
        for x in range(L,40-L):
            if (Ln is None or x<Ln or x>=40-Ln) and o[y][x] in 'sS': o[y][x]='K'
    for y in range(36,40):                                   # collar fold + shadow wedge under the chin
        for x in (12,27):
            if o[y][x] in 'ER': o[y][x]='R'
    o[27][20]='S'                                           # nose: 1 px shadow
    return [''.join(r) for r in o]
N0=["..KKKKK..","KKKKKKKK.",".KWWiiiK.",".iWWiiiW.",".iiiKKiW.",".iIiKKIW.",".IIIIIW..","..nnnn...","........."]
EYE={
 'neutral':     N0,
 'cheerful':    N0[:6]+[".........",".........","........."],
 'determined':  [".........","KKKK.....",".KKKKKK..",".iWWKKKK.",".iWWiiiW.",".iiiKKiW.",".IIIKKIW.","..nnnnW..","........."],
 'shout':       [".........","KKK......",".KKKKK...",".WWWKKKK.",".WWiiiWW.",".WiKKiW..",".WIKKIW..","..WnnW...","........."],
 'effort':      [".........","KK.......",".KKKK....",".KKKKKKK.",".iWWiiKK.",".iiiKKiW.","..IIIIW..",".........","........."],
 'joy':         [".........",".........","..KKKKK..",".KK...KK.","KK.......",".........",".........",".........","........."],
 'surprised':   [".KKKKKK..","KKKKKKKK.",".WWWWWWK.",".WWiiiWW.",".WiKKiWW.",".WiKKiWW.",".WWiIWW..","..WWWW...","........."],
 'pain':        [".........",".KK......","...KKK...",".....KK..","...KKK...",".KK......",".........","nn.......","n........"],
 'blink_half':  [".........",".........",".........",".........","KKKKKKKK.",".iiiKKiK.",".IIIIIW..","..nnnn...","........."],
 'blink_closed':[".........",".........",".........",".........","KK.......",".KK....K.","..KKKKK..",".........","........."],
 'embarrassed': [".........",".........","KKKKKKKK.",".KWWiiiK.",".iWWiKKW.",".IIIiKKW.","..nnnn...",".........","W........"],
}
BROW={
 'neutral':     [".........",".hhhhh...","........."],
 'cheerful':    ["..hhhh...",".h.......","........."],
 'determined':  ["hh.......","..hhh....",".....hh.."],
 'shout':       ["hhh......","...hhh...","......hh."],
 'effort':      ["hh.......","..hhh....",".....hhh."],
 'joy':         ["..hhhh...",".h....h..","........."],
 'surprised':   ["..hhhh...",".h....h..","........."],
 'pain':        [".....hh..","..hhh....","hh......."],
 'blink_half':  [".........",".hhhhh...","........."],
 'blink_closed':[".........",".hhhhh...","........."],
 'embarrassed': [".....hh..","..hhh....","........."],
}
MOUTH={
 'neutral':     ["........","...rr...","........","........"],
 'cheerful':    ["........","..rrrr..","..reer..","...rr..."],
 'determined':  ["........","........","..rrrr..","........"],
 'shout':       ["........","..rrrr..",".rKKKKr.","..reer.."],
 'effort':      ["........",".rrrrrr.",".rWWWWr.","..rrrr.."],
 'joy':         ["........",".rrrrrr.","..KKKK..","...ee..."],
 'surprised':   ["...rr...","..rKKr..","...rr...","........"],
 'pain':        ["........","..rrrr..",".rKKKKr.","........"],
 'blink_half':  ["........","...rr...","........","........"],
 'blink_closed':["........","...rr...","........","........"],
 'embarrassed': ["........","...r.r..","..r.r...","........"],
}
BL={1:["....","kkkk"],2:["kkkk","kkkk"],3:["ekek","keke"]}
FX={'pain':[(4,8,["..W.",".WnW","WnnK",".KK."])],'shout':[(3,6,[".E.E.","EE.EE",".....","EE.EE",".E.E."])],
    'embarrassed':[(4,8,["..W.",".WnW","WnnK",".KK."])],'surprised':[(5,8,["W.","W.","..","W."])]}
EXPR=kit.EXPR
def build(expr):
    g=[list(r) for r in base()]
    st=EYE[expr]; br=BROW[expr]
    for x,m in ((10,False),(29,True)):
        for dy,r in enumerate(br):                      # brows only on skin (bangs hide them)
            for dx,c in enumerate(r):
                X=x-dx if m else x+dx; Y=15+dy
                if c!='.' and g[Y][X] in 'sS': g[Y][X]=c
        kit.stamp(g,st,x,18,m)
    kit.stamp(g,MOUTH[expr],16,28)
    n=kit.BLUSH.get(expr,0)
    if n: kit.stamp(g,BL[n],10,26); kit.stamp(g,BL[n],29,26,True)
    for x,y,stp in FX.get(expr,[]): kit.stamp(g,stp,x,y)
    return [''.join(r) for r in g]
if __name__=='__main__':
    from PIL import Image, ImageDraw
    Z=int(sys.argv[1]) if len(sys.argv)>1 else 4; C=4; ims=[]
    for e in EXPR:
        rows=build(e); open(f'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face2/portrait/P_{e}.txt','w').write('\n'.join(rows)+'\n')
        ims.append((e,rows))
    w=40*Z+44; h=40*Z+14; S=Image.new('RGBA',(C*w,((len(ims)+C-1)//C)*h),(255,255,255,255)); d=ImageDraw.Draw(S)
    for i,(e,rows) in enumerate(ims):
        x,y=(i%C)*w,(i//C)*h; a=pal.to_img(rows,Z,(150,190,220,255)); b=pal.to_img(rows,1,(150,190,220,255))
        S.paste(a,(x,y+12)); S.paste(b,(x+40*Z+2,y+12)); d.text((x,y),e,fill='black')
    S.save(sys.argv[2] if len(sys.argv)>2 else '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face2/work/p2.png'); print(S.size)
