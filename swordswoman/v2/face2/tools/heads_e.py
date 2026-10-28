"""heads_e.py (r2): placeholder heads in HAIR option-E style (half-up + red bow, side-swept bangs, sidelocks, long back hair).
Crown row 4 (bow rows 0-3 excluded) .. chin row 18 = 15 px crown-chin. Tile 19 x 22. Eye boxes: S 3x5 (cols 5-7 / 10-12, rows 10-14),
SE near 3x5 (8-10) + far 2x5 (13-14), E profile wedge (cols 11-14), brow row 9. Faces have no K inside the hair; K only on the silhouette/chin."""
BOW=[
"...KKK......KKK...",
"..KeeEK.KK.KeEEK..",
"..KeEEEKeEKEEERK..",
"..KEERRKERKRRRRK..",
]
S=["".ljust(16,'.')]*4+[
"....KKKKKKKK....",
"..KKHHHHHLLHKK..",
".KHHHHHLLHHHLHK.",
"KHHHHsHHHHHHHHhK",
"KHHhssHHHHHHHHhK",
"KHsssssshssssshK",
"KHsssssssssssshK",
"KHsssssssssssshK",
"KHsssssssssssshK",
"KHsssssssssssshK",
"KHsssssssssssshK",
"KHsssssssssssshK",
"KHhsssssssssShK.",
"KHHHHhSssShHHHK.",
"KHHHHhhKKhhHHHHK",
"KHHHHHKSSKHHHHhK",
".KHHHhKSsKhHHhK.",
".KhHK.K..K.KHhK.",
]
SE=["".ljust(16,'.')]*4+[
"....KKKKKKKK....",
"..KKHHHHHLLHKK..",
".KHHHHHHLLHHLHK.",
"KHHHHHHHHHHHHHhK",
"KHHHHHHHHsHHHHhK",
"KHHHHhsssshhsssK",
"KHHHHssssssssssK",
"KHHHHssssssssssK",
"KHHHHssssssssssK",
"KHHHHssssssssssK",
"KHHHHsssssssssssK",
"KHHHHsssssssssssK",
"KHHHHhssssssssK.",
"KHHHHHhKssssSK..",
"KHHHHHHhhKKK....",
"KHHHHHHhKSSK....",
".KHHHHhhKSsK....",
".KhHHhK.K..K....",
]
E=[
"..KKK.............",
".KeeEK.KK.........",
".KeEEEKeEK........",
".KEERRKERK........",
"..KKKHHHHKKKK.....",
"..KHHHHHHHLLHKK...",
".KHHHHHHLHHLLHHK..",
".KHHHHHHHHHHHHHhK.",
"KHHHHHHHHHHHHHhhK.",
"KHHHHHHHHHHssssK..",
"KHHHHHHHHHhsssssK.",
"KHHHHHHHHHhsssssK.",
"KHHHHHHHHKssssssK.",
"KHHHHHHHKsSsssssK.",
"KHHHHHHHKsSssssssK",
"KHHHHHHHHKssssssK.",
"KHHHHHHHHhKssssK..",
"KHHHHHHHHHhKssssK.",
"KHHHHHHHHHHhKKKK..",
"KHHHHHHHHHhKSSK...",
".KHHHHHHHhKSSsK...",
".KhHHhHHhK.KSsK...",
]
NE=[
"....KKK......KKK..",
"...KEEEK.KK.KEEEK.",
"...KERRRKRRKRRRRK.",
"....KKKKKRRKKKKK..",
"....KKHHHERHHKK...",
"..KKHHHHHERHHHHKK.",
".KHHHLLHHERHHLHHK.",
".KHHHHHHHERHHHHhK.",
"KHHHHHHHHKKHHHHhhK",
"KHHHHHHHHHHHHHHhhK",
"KHHHHHHHHHHHHHHHhK",
"KHHHHHHHHHHHHHHhsK",
"KHHHHHHHHHHHHHhSsK",
"KHHHHHHHHHHHHHhSsK",
"KHHHHHHHHHHHHHHhsK",
"KHHHHHHHHHHHHHHhK.",
"KHHHHHHHHHHHHHhK..",
"KHHHHHHHHHHHHhKSK.",
"KHHHHHHHHHHHhKSSK.",
"KHHHhHHHhHHHhKSSK.",
".KHHhHHhHHHhK.KK..",
"..KhK.KhK.KK......",
]
N=[
"...KKK......KKK...",
"..KEEEK.KK.KEEEK..",
"..KERRRKRRKRRRRK..",
"...KKKKKRRKKKKK...",
"...KKKHHERHHKKK...",
"..KKHHHHERHHHHKK..",
".KHHLLHHERHHLLHHK.",
".KHHHHHHERHHHHHhK.",
"KHHHHHHHKKHHHHHhhK",
"KHHHHHHHHHHHHHHhhK",
"KHHHHHHHHHHHHHHhhK",
"KHHHHHHHHHHHHHHhhK",
"KHHHHHHHHHHHHHHhhK",
"KHHHHHHHHHHHHHHhhK",
"KHHHHHHHHHHHHHHhhK",
"KHHHHHHHHHHHHHHhhK",
"KHHHHHHHHHHHHHHhhK",
"KhHHHhHHHHHHhHHhhK",
"KhHHHhHHKKHHhHHhhK",
"KhHHhHHKSSKHHhHhhK",
".KhHhHhKSSKhHhHhK.",
"..KhK.KhK.KhK.KK..",
]
E=["".ljust(18,".")]*4+[r[:4]+r[6:] for r in E[4:]]
NE=["".ljust(18,".")]*4+NE[4:]
N=["".ljust(18,".")]*4+N[4:]
NE=[r[:2]+r[4:] for r in NE]
N=[r[:2]+r[3:16]+r[17:] for r in N]
BUN=[".KKK.","KHLHK","KHHhK",".KKK."]
BOWF=["KKK.KKK","KeEKeEK","KEErERK","KRRKRRK",".KKRKK.","..KRK..","..K.K.."]
def over(rows,spr,x0,y0,behind=False):
    g=[list(r.ljust(19,'.')) for r in rows]
    for dy,r in enumerate(spr):
        for dx,c in enumerate(r):
            if c=='.': continue
            X,Y=x0+dx,y0+dy
            if 0<=Y<len(g) and 0<=X<19 and (not behind or g[Y][X]=='.'): g[Y][X]=c
    return [''.join(r) for r in g]
SE[15]=SE[15][:13]+'S'+SE[15][14:]                     # 3/4 nose: 1 px skin shadow toward the far cheek
E[8:19]=["KHHHHHHHHHHHhK","KHHHHHHHHsssssK","KHHHHHHHhsssssK","KHHHHHHHhssssK","KHHHHHHKsssssK","KHHHHHKsSssssK",
          "KHHHHHKsSsssssK","KHHHHHHKsssssK","KHHHHHHhKSssK","KHHHHHHHhKSssK","KHHHHHHHHhKKK"]   # r5 profile rhythm: brow out, eye in, nose out, mouth in, chin out
E[19]="KHHHHHHHhKSSK"; E[20]=".KHHHHHhKSSK"; E[21]=".KhHHHhK.KSK"
for _n,(bx,by,wx,wy,beh) in {'S':(9,1,11,1,False),'SE':(10,1,11,0,True),'E':(2,1,0,0,True),'NE':(5,1,1,2,False),'N':(5,1,0,2,False)}.items():
    globals()[_n]=over(over(globals()[_n],BUN,bx,by,True),BOWF,wx,wy,beh)
for _n in ('S','SE','E','NE','N'):
    globals()[_n]=[r.ljust(19,'.') for r in globals()[_n]]
