"""W/NW/SW heads: mirror of E/NE/SE (the head design is symmetric by the lock decision: bow centred on
the bun's front base), then RE-LIGHT by hand rules so the camera-locked lighting stays correct:
key light top-left (hair_2 sheen crescent upper-left); no rim in stamps."""
import sys; sys.path.insert(0,'/tmp'); from stamplib import *
def load(p): 
    L=open(p).read().split('grid:\n')[1].strip('\n').split('\n'); return L
for src,dst,desc in [('head_E.pix','head_W.pix','facing W profile'),('head_NE.pix','head_NW.pix','facing NW back three-quarter'),('head_SE.pix','head_SW.pix','facing SW three-quarter')]:
    rows=[r[::-1] for r in load(src)]
    W=len(rows[0])
    rows=[''.join(('H' if ch=='J' else ch) for ch in r) for r in rows]
    # remove mirrored rim (now on the left edge)
    rows=[''.join(('h' if (ch=='p' and x<5) else ch) for x,ch in enumerate(r)) for r in rows]
    # hair sheen crescent, upper-left of the skull (rows 9-12) and of the bun (rows 1-3)
    def hairrun(y):
        r=rows[y]; xs=[x for x,ch in enumerate(r) if ch in 'hH']; return xs
    for y,(a,b) in {9:(3,6),10:(1,3),11:(1,2)}.items():
        xs=hairrun(y)
        if xs:
            x0=xs[0]; r=list(rows[y])
            for x in range(x0+a,x0+b+1):
                if r[x] in 'hH': r[x]='J'
            rows[y]=''.join(r)
    for y in (1,2):
        xs=hairrun(y)
        if xs:
            r=list(rows[y]); x0=xs[0]
            for x in (x0+1,x0+2):
                if r[x] in 'hH': r[x]='J'
            rows[y]=''.join(r)
    # rim light is NOT baked into head stamps (applied on the whole silhouette at sprite level)
    save(dst,rows,desc+' (mirror of the E-side stamp + hand re-light)')
