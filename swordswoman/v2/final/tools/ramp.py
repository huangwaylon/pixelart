import numpy as np
from scipy.cluster.vq import kmeans2
P=np.load('work/seg_pooled.npy',allow_pickle=True).item(); per=np.load('work/seg_per.npy',allow_pickle=True).item()
V=['front','left','back','right','iso_S','iso_SE','iso_E','iso_NE','iso_N']
h=lambda c:'#%02x%02x%02x'%tuple(np.clip(c,0,255).astype(int))
for k,n in [('red',4),('skin',4),('obi',3),('hair',5),('boot',3)]:
    c,_=kmeans2(P[k],n,minit='++',seed=1); c=c[np.argsort(c.sum(1))]
    print(k,'pooled:',' '.join(h(x) for x in c))
    for v in V:
        p=per[(v,k)]; l=((p[:,None]-c[None])**2).sum(-1).argmin(1)
        fr=[(l==i).mean() for i in range(n)]
        print(f'  {v:7} med {h(np.median(p,0))} share '+' '.join(f'{f*100:4.0f}' for f in fr))
