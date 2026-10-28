"""landmarks.py V... : measured landmarks (master coords, float) from the illustration: eyes (dark blobs inside the face skin), mouth, bow/red blobs in the head, figure parts rows"""
import sys; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/final/tools'); import ds, numpy as np
from scipy import ndimage as nd
from seg import seg
def lm(v):
    x,m=ds.illus(v); H,W=m.shape; h=48; sc=h/H; w=round(W*sc); ox=(64-w)//2; top=14
    M=lambda yy,xx:(round(xx*sc+ox,1),round(yy*sc+top,1))
    L=seg(x,m,0,H-1); out=[]
    head=int(H*0.36)
    skin=(L=='skin'); skin[head:]=False
    # face hull: fill holes in skin region (eyes are holes)
    filled=nd.binary_fill_holes(nd.binary_closing(skin,iterations=6))
    lum=x.mean(-1); dark=filled&~skin&(lum<140)
    lab,n=nd.label(dark); 
    for i,sl in enumerate(nd.find_objects(lab)):
        a=(lab[sl]==i+1).sum()
        if a<0.00004*H*W: continue
        y0,y1,x0,x1=sl[0].start,sl[0].stop,sl[1].start,sl[1].stop
        c=x[sl][lab[sl]==i+1]
        out.append(f"dark blob in face: x {M(0,x0)[0]}-{M(0,x1)[0]} y {M(y0,0)[1]}-{M(y1,0)[1]} (area {a*sc*sc:.1f}px, mean #{''.join('%02x'%int(t) for t in c.mean(0))})")
    red=(L=='red'); red[head:]=False; lab,n=nd.label(nd.binary_opening(red,iterations=2))
    for i,sl in enumerate(nd.find_objects(lab)):
        a=(lab[sl]==i+1).sum()
        if a*sc*sc<1.5: continue
        out.append(f"red blob (bow/tails) in head: x {M(0,sl[1].start)[0]}-{M(0,sl[1].stop)[0]} y {M(sl[0].start,0)[1]}-{M(sl[0].stop,0)[1]} area {a*sc*sc:.1f}px")
    ys,xs=np.where(skin); 
    if len(ys): out.append(f"face/neck skin bbox: x {M(0,xs.min())[0]}-{M(0,xs.max())[0]} y {M(ys.min(),0)[1]}-{M(ys.max(),0)[1]}")
    hair=(L=='hair'); hair[head:]=False; ys,xs=np.where(hair); out.append(f"hair bbox (top 36%): x {M(0,xs.min())[0]}-{M(0,xs.max())[0]} y {M(ys.min(),0)[1]}-{M(ys.max(),0)[1]}")
    for mat in ['obi','boot']:
        ys,xs=np.where(L==mat); out.append(f"{mat} bbox: x {M(0,xs.min())[0]}-{M(0,xs.max())[0]} y {M(ys.min(),0)[1]}-{M(ys.max(),0)[1]}")
    return out
for v in sys.argv[1:]:
    t=lm(v); open(ds.F+f'work/lm_{v}.txt','w').write(f'MEASURED LANDMARKS {v} (master pixel coords x=col y=row, from the illustration):\n'+'\n'.join(t)+'\n'); print(v); print('\n'.join(t))
