import sys,numpy as np
sys.path.insert(0,'tools'); import ds
from PIL import Image
V=['front','left','back','right','iso_S','iso_SE','iso_E','iso_NE','iso_N']
out=[]
for v in V:
    x=np.array(Image.open(ds.S+v+'.png').convert('RGB')).astype(float)[::3,::3]
    m=(x.min(-1)<215)|(x.max(-1)-x.min(-1)>30)
    idx,L=ds.snapmap(x,m)
    # residual: mean colour distance per material
    s=[]
    for mat,al in [('hair','hHgL'),('red','ReE'),('skin','sSm'),('obi','oOQ'),('boot','hHgL')]:
        sel=L==mat; ii=idx[sel]; ks=[ds.KEYS[i] for i in ii]
        res=np.sqrt(((x[sel]-ds.rgb[ii])**2).sum(-1)).mean()
        s.append(f"{mat}:"+'/'.join(f"{c}{ks.count(c)*100//max(1,len(ks))}" for c in al)+f" d{res:.0f}")
    out.append(f"{v:7} "+'  '.join(s))
print('\n'.join(out)); open('work/palcheck.txt','w').write('\n'.join(out)+'\n')
