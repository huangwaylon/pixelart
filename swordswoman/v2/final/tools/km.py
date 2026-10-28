import numpy as np, glob
from PIL import Image
from scipy.cluster.vq import kmeans2
S='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/hair/turnE_final/'
V=['front','left','back','right','iso_S','iso_SE','iso_E','iso_NE','iso_N']
def fig(v):
    x=np.array(Image.open(S+v+'.png').convert('RGB')).astype(float)
    m=(x.min(-1)<215)|(x.max(-1)-x.min(-1)>30)
    return x,m
allp=[];per={}
for v in V:
    x,m=fig(v);p=x[m];per[v]=p;allp.append(p[::7])
allp=np.concatenate(allp)
c,_=kmeans2(allp,28,minit="++",seed=0)
import scipy.spatial as sp
class K:
    def predict(s,p): return sp.distance.cdist(p,c).argmin(1)
km=K()

o=np.argsort(c.sum(1))
print('id hex  '+' '.join(f'{v[-5:]:>6}' for v in V))
for i in o:
    row=[]
    for v in V:
        l=km.predict(per[v][::5]);row.append(f'{(l==i).mean()*100:6.1f}')
    print(i,'#%02x%02x%02x'%tuple(c[i].astype(int)),' '.join(row))
np.save('work/km.npy',c)
