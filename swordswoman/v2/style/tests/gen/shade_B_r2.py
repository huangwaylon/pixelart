import numpy as np, sys
M=np.load('/tmp/B_r2_mat.npy',allow_pickle=True); H,W=M.shape
O=np.full((H,W),'.',dtype='<U1')
def blur(a,s):
    r=int(3*s); k=np.exp(-np.arange(-r,r+1)**2/(2*s*s)); k/=k.sum()
    a=np.pad(a,r,mode='constant')
    a=np.apply_along_axis(lambda v:np.convolve(v,k,'same'),0,a)
    a=np.apply_along_axis(lambda v:np.convolve(v,k,'same'),1,a)
    return a[r:-r,r:-r]
def light(mask,s,lx=1.0,ly=0.8):
    b=blur(mask.astype(float),s); gy,gx=np.gradient(b)
    t=gx*lx+gy*ly; m=np.abs(t[mask]).max() if mask.any() else 1
    return t/m
# tones: (light,base,shadow,deep), thresholds (light>a, shadow<-b, deep<-c), sigma
T={'hair':('d','H','h','h',9,.30,9,2.6),'bun':('L','H','h','h',.55,.25,9,1.8),
   'face':('s','s','S','S',9,.55,9,2.2),'neck':('S','S','S','S',9,9,9,1),'handN':('s','s','S','S',9,.45,9,1.4),'handF':('s','s','S','S',9,.45,9,1.4),
   'legN':('s','s','S','S',9,.40,9,1.5),'legF':('s','s','S','S',9,.30,9,1.5),
   'dress':('e','E','R','r',.55,.22,.75,3.2),'sleeveN':('e','E','R','r',.45,.25,.8,2.4),'sleeveF':('e','E','R','r',.5,.2,.7,2.2),
   'bow':('e','E','R','r',.35,.3,.8,2.0),'knot':('E','E','R','r',.4,.3,.8,1.2),
   'obi':('d','d','h','h',9,.3,9,2.0),'bootN':('d','d','h','h',9,.3,9,1.6),'bootF':('d','d','h','h',9,.25,9,1.6),
   'blade':('W','n','n','n',.2,9,9,0.8),'guard':('k','k','k','k',9,9,9,1),'hilt':('h','h','h','h',9,9,9,1)}
for m,(lt,b,sh,dp,a,bb,c,s) in T.items():
    k=M==m
    if not k.any(): continue
    t=light(np.isin(M,['dress','obi']) if m in('dress','obi') else k,s); O[k]=b
    O[k&(t>a)]=lt; O[k&(t<-bb)]=sh; O[k&(t<-c)]=dp
def nb(y,x,d):
    yy,xx=y+d[0],x+d[1]
    return M[yy,xx] if 0<=yy<H and 0<=xx<W else ''
RED={'dress','sleeveN','sleeveF','bow','knot'}
N4=[(-1,0),(1,0),(0,-1),(0,1)]
P=O.copy()
for y in range(H):
    for x in range(W):
        m=M[y,x]
        if not m: continue
        ns=[nb(y,x,d) for d in N4]
        up=ns[0]
        # inner lines (R1/O2)
        if m in('hair','bun') and any(n in('face','neck') for n in ns): P[y,x]='h'
        if m in('sleeveN','sleeveF') and any(n=='dress' or n=='obi' for n in ns): P[y,x]='r'
        if m=='dress' and any(n=='obi' for n in ns): P[y,x]='r'
        if m=='bow' and any(n in('knot','hair','bun') for n in ns): P[y,x]='r'
        if m in('sleeveN',) and any(n=='handN' for n in ns): P[y,x]='r'
        if m in('sleeveF',) and any(n=='handF' for n in ns): P[y,x]='r'
        if m=='dress' and any(n in('legN','legF') for n in ns): P[y,x]='r'
        if m in('hair','bun') and up in('bow','knot'): P[y,x]='h'
        # cast shadows (R2)
        if m=='face' and (up=='hair' or nb(y,x,(-2,0))=='hair' and False): P[y,x]='S'
        if m in('legN','legF') and (up=='dress' or nb(y,x,(-2,0))=='dress'): P[y,x]='S'
        if m=='dress' and (up in('hair','neck','sleeveN') ) and P[y,x] not in('r',): P[y,x]='R'
        if m=='dress' and nb(y,x,(-1,0))=='obi': P[y,x]='r'
        if m=='dress' and nb(y,x,(-2,0))=='obi' and P[y,x] in('E','e'): P[y,x]='R'
        if m=='face' and nb(y,x,(0,-1))=='hair' : P[y,x]='S'
O=P
# outer outline
filled=M!=''
K=np.zeros_like(filled)
for dy,dx in N4:
    K|=np.roll(np.roll(filled,dy,0),dx,1)
K&=~filled
O[K]='K'
open(sys.argv[1],'w').write('\n'.join(''.join(r) for r in O)+'\n')
