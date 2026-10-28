import numpy as np,sys
sys.path.insert(0,'tools'); from seg import load,seg
from scipy.cluster.vq import kmeans2
from PIL import Image
h=lambda c:'#%02x%02x%02x'%tuple(np.clip(c,0,255).astype(int))
for v in ['front','iso_S','iso_SE']:
    x,m,y0,y1=load(v); L=seg(x,m,y0,y1)
    # face box: skin rows in top 35% ; bbox of skin there
    H=y1-y0; sk=(L=='skin'); sk[int(y0+0.33*H):]=False
    ys,xs=np.where(sk); fy0,fy1,fx0,fx1=ys.min(),ys.max(),xs.min(),xs.max()
    # eye band: middle of face
    by0=int(fy0+0.25*(fy1-fy0)); by1=int(fy0+0.65*(fy1-fy0))
    crop=x[by0:by1,fx0:fx1]; lc=L[by0:by1,fx0:fx1]
    if v=='front': Image.fromarray(crop.astype(np.uint8)).resize(((fx1-fx0)*2,(by1-by0)*2)).save('work/eyes_front.png')
    p=crop[(lc!='skin')].reshape(-1,3)
    c,l=kmeans2(p,8,minit='++',seed=2); o=np.argsort(c.sum(1))
    print(v,(fx0,by0,fx1,by1),' '.join(f'{h(c[i])}:{(l==i).mean()*100:.0f}' for i in o))
    # red in mouth region / blush in lower face
    lo=x[int(fy0+0.6*(fy1-fy0)):fy1,fx0:fx1]; ll=L[int(fy0+0.6*(fy1-fy0)):fy1,fx0:fx1]
    q=lo[ll=='skin']; c2,l2=kmeans2(q,5,minit='++',seed=2); o=np.argsort(c2.sum(1))
    print('  lowerface skin',' '.join(f'{h(c2[i])}:{(l2==i).mean()*100:.0f}' for i in o))
