import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import build
F={}
# f0 anticipation: coil back-left, squash 1, blade raised up-left behind, bow lags right
F[0]=[
 ('body',{
 30:(22,"ss"),
 31:(22,"SSeeerrSSSSrrR"),
 32:(21,"eEEEreerSrrERRRR"),
 33:(21,"eEEErEEEEEERRRRR"),
 34:(21,"EEERrdddddhrRRRR"),
 35:(21,"ERRrrhhhhhhrRRrr"),
 36:(22,"rr.EERRRRRRRRRR"),
 37:(24,"EEEEEERRRRRRR"),
 38:(24,"EEEEEERRRRRRRR"),
 39:(23,"EEEEEEERRRRRRRR"),
 40:(23,"EEEEERRRRRRRRRR"),
 41:[(26,"SS"),(35,"SS")],
 }),
 ('head',-1,1,1),
 ('body',{
 25:(16,"n"),26:(17,"n"),27:(18,"W"),28:(19,"n"),29:(20,"n.k"),30:(21,"k"),
 42:[(26,"dd"),(35,"ddd")],43:[(26,"ddd"),(35,"hhhh")],44:(26,"hhh"),
 }),
]
# f1 wind-up/launch: stretch 1, step forward, blade raised high beside head, bow lags left
F[1]=[
 ('body',{
 21:(21,"sss"),
 22:(21,"SSS"),
 23:(21,"eEE"),
 24:(20,"eEER"),
 25:(20,"EEER"),
 26:(20,"EEERr"),
 27:(20,"EERRrr"),
 28:(21,"ERRrr"),
 29:(21,"EERrrEEErrSSSSrrR"),
 30:[(21,"rrr"),(25,"EeeEEErSrrERRRR")],
 31:(25,"EeEEEEEEEERRRRR"),
 32:(26,"ErddddddhrRRRR"),
 33:(26,"ErhhhhhhhrRRRR"),
 34:(26,"EERRRRRRRRRRRR"),
 35:(25,"EEEEEERRRRRRRRR"),
 36:(25,"EEEEEEERRRRRRRRR"),
 37:(24,"EEEEEEEERRRRRRRRR"),
 38:(24,"EEEEEERRRRRRRRRRR"),
 39:[(28,"SS"),(35,"SS")],
 40:[(28,"ss"),(36,"ss")],
 41:(28,"ss"),
 }),
 ('head',1,-1,-1),
 ('body',{
 14:(20,"n"),15:(20,"n"),16:(21,"W"),17:(21,"n"),18:(22,"n"),19:(22,"n"),20:(21,"kkk"),
 41:(37,"dd"),42:[(28,"dd"),(37,"ddd")],43:[(28,"ddd"),(37,"hhhh")],44:(28,"hhh"),
 }),
]
import math
def arc(cx,cy,r1,r2,sx,sy,a0,a1,edge=1.0):
    """crescent: inside circle (cx,cy,r1), outside circle (cx+sx,cy+sy,r2), angles a0..a1 deg (0=right, +=down)"""
    rows={}
    for y in range(48):
        for x in range(64):
            d1=math.hypot(x-cx,y-cy); d2=math.hypot(x-cx-sx,y-cy-sy)
            a=math.degrees(math.atan2(y-cy,x-cx))
            if d1<=r1 and d2>r2 and a0<=a<=a1:
                c='n' if d1>r1-edge or d2<r2+0.7 else 'W'
                rows.setdefault(y,[]).append((x,c))
    return {y:[(x,c) for x,c in v] for y,v in rows.items()}
# f2 SMEAR: lunge forward, arms smeared forward, blade = crescent arc, hair/bow trail left
F[2]=[
 ('body',{
 30:(31,"rrSSSSrr"),
 31:(28,"eeEEEEEEEEEEEEEEss"),
 32:(28,"EEEEEEEEEEERRRRRSS"),
 33:(28,"EErddddddhrRRrrr"),
 34:(28,"EErhhhhhhhrRrr"),
 35:(27,"EERRRRRRRRRRR"),
 36:(26,"EEEEEERRRRRRRR"),
 37:(25,"EEEEEEEERRRRRRR"),
 38:(24,"EEEEEEEEERRRRRRR"),
 39:(24,"EEEEEERRRRRRRRRR"),
 40:[(28,"SS"),(37,"SS")],
 41:[(27,"ss"),(38,"dd")],
 42:[(26,"dd"),(38,"ddd")],
 43:[(26,"ddd"),(38,"hhhh")],
 44:(27,"hh"),
 }),
 ('head',3,0,-1),
 ('body',{24:(25,"HH"),25:(25,"HH"),26:(25,"hH"),27:(26,"hh"),28:(27,"hh"),29:(28,"hh")}),
 ('arc',(37,31,19,16.5,-3,0,-80,4)),
 ('body',{31:(46,"k"),32:(46,"knnWnnn"),33:(46,"k")}),
]
# f3 IMPACT hold: committed lunge, blade forward-low, skirt flared, back leg extended
F[3]=[
 ('body',{
 31:(30,"EErrSSSSrr"),
 32:(29,"eeEEEEEEEEEERRR"),
 33:(29,"eEEEEEEEEEERRRRRR"),
 34:(29,"EErddddddhrRRRRss"),
 35:(29,"EErhhhhhhhrRrrrSS"),
 36:(28,"EERRRRRRRRRRrr"),
 37:(27,"EEEEEEERRRRRR"),
 38:(26,"EEEEEEEERRRRRR"),
 39:(24,"EEEEEEEEEERRRRRR"),
 40:(23,"EEEEEEERRRRRRRRR"),
 41:[(26,"SS"),(36,"SS")],
 42:[(24,"SS"),(36,"dd")],
 43:[(23,"ddd"),(36,"ddd")],
 44:[(22,"hhh"),(36,"hhhh")],
 }),
 ('head',4,1,-1),
 ('body',{25:(26,"HH"),26:(26,"hH"),27:(27,"hh"),28:(28,"hh"),29:(29,"hh")}),
 ('body',{35:(47,"k"),36:(46,"k"),37:(47,"n"),38:(48,"n"),39:(49,"W"),40:(50,"n"),41:(51,"n")}),
]
# f4 FOLLOW-THROUGH: overshoot past impact, blade rotates to near-vertical, skirt/hair/bow swing forward
F[4]=[
 ('body',{
 31:(33,"rrSSSSrr"),
 32:(30,"eeEEEEEEEEERRR"),
 33:(30,"eEEEEEEEEERRRRR"),
 34:(30,"EErddddddhrRRRR"),
 35:(30,"EErhhhhhhhrRRRRR"),
 36:(30,"EERRRRRRRRRRrrss"),
 37:[(29,"EEEEEEERRRRRrr"),(44,"SS")],
 38:(28,"EEEEEEEERRRRRRR"),
 39:(27,"EEEEEEEEERRRRRRRR"),
 40:(27,"EEEEEEERRRRRRRRRR"),
 41:[(28,"SS"),(38,"SS")],
 42:[(26,"SS"),(38,"dd")],
 43:[(24,"ddd"),(38,"ddd")],
 44:[(23,"hhh"),(38,"hhhh")],
 }),
 ('head',5,1,1),
 ('body',{25:(45,"h"),26:(45,"hh"),27:(44,"hhh")}),
 ('body',{38:(44,"kk"),39:(45,"n"),40:(46,"n"),41:(46,"W"),42:(47,"n"),43:(47,"n")}),
]
# f5 RECOVER: rise back toward the master pose, blade hangs straight down in front
F[5]=[
 ('body',{
 30:(29,"rrSSSSrr"),
 31:(27,"eeEEEEEEEERRR"),
 32:(26,"eEEEEEEEEEERRRR"),
 33:(26,"EErddddddhrRRRR"),
 34:(26,"EErhhhhhhhrRRRR"),
 35:(26,"EERRRRRRRRRrrss"),
 36:[(25,"EEEEEEERRRRRrr"),(39,"SS")],
 37:(25,"EEEEEEEERRRRRR"),
 38:(24,"EEEEEEEERRRRRRR"),
 39:(24,"EEEEERRRRRRRRRR"),
 40:[(28,"SS"),(34,"SS")],
 41:[(28,"ss"),(34,"dd")],
 42:[(28,"dd"),(34,"ddd")],
 43:[(28,"ddd"),(34,"hhhh")],
 44:(28,"hhh"),
 }),
 ('head',1,0,0),
 ('body',{37:(39,"kk"),38:(40,"n"),39:(40,"n"),40:(40,"W"),41:(40,"n"),42:(40,"n")}),
]
def norm(L):
    out=[]
    for k,v in L:
        if k=='head': out.append((k,)+tuple(v) if isinstance(v,tuple) else (k,v)); continue
        rows=[]
        for y,item in v.items():
            for x0,s in (item if isinstance(item,list) else [item]): rows.append((y,(x0,s)))
        out.append((k,rows))
    return out
def fix(L):
    o=[]
    for t in L:
        if t[0]=='head': o.append(t)
        elif t[0]=='arc':
            A=arc(*t[1]); o.append(('body',[(y,(x,c)) for y,v in A.items() for x,c in v]))
        else:
            rows=[]
            for y,item in t[1].items():
                for x0,s in (item if isinstance(item,list) else [item]): rows.append((y,(x0,s)))
            o.append((t[0],rows))
    return o
if __name__=='__main__':
    which=[int(a) for a in sys.argv[1:]] or sorted(F)
    for i in which:
        g=build(fix(F[i]))
        open(os.path.join(os.path.dirname(os.path.abspath(__file__)),f'A_slash_f{i}.txt'),'w').write('\n'.join(g)+'\n')
