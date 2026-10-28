import numpy as np, colorsys
from PIL import Image
from scipy.cluster.vq import kmeans2
S='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/hair/turnE_final/'
V=['front','left','back','right','iso_S','iso_SE','iso_E','iso_NE','iso_N']
def load(v):
    x=np.array(Image.open(S+v+'.png').convert('RGB')).astype(float)
    m=(x.min(-1)<215)|(x.max(-1)-x.min(-1)>30)
    ys,xs=np.where(m); return x,m,ys.min(),ys.max()
def seg(x,m,y0,y1):
    r,g,b=x[...,0],x[...,1],x[...,2]; mx=x.max(-1); mn=x.min(-1); sat=(mx-mn)/np.maximum(mx,1)
    yy=(np.arange(x.shape[0])[:,None]-y0)/(y1-y0)*np.ones(x.shape[:2])
    L=np.full(x.shape[:2],'',dtype='<U4')
    L[m]='?'
    K=m&(mx<45); L[K]='K'
    red=m&~K&(r>g*1.6)&(r>90)&(sat>0.55)&(mx<235)
    L[red]='red'
    skin=m&~K&~red&(r>150)&(r>g)&(g>b*0.95)&(sat<0.5)&(sat>0.15)
    L[skin]='skin'
    obi=m&~K&~red&~skin&(b>=r*0.95)&(mx>80)&(mx<235)
    L[obi]='obi'
    brown=m&~K&~red&~skin&~obi&(mx<150)
    L[brown&(yy>0.86)]='boot'; L[brown&(yy<=0.86)]='hair'
    return L
if __name__=='__main__':
    import sys
    pooled={};per={}
    for v in V:
        x,m,y0,y1=load(v);L=seg(x,m,y0,y1)
        print(v,{k:round((L==k).sum()/m.sum()*100,1) for k in ['K','red','skin','obi','hair','boot','?']})
        for k in ['red','skin','obi','hair','boot']:
            per[(v,k)]=x[L==k]; pooled.setdefault(k,[]).append(x[L==k][::5])
        if v=='iso_SE':
            cm={'K':(255,0,255),'red':(255,0,0),'skin':(255,220,180),'obi':(120,120,255),'hair':(90,60,40),'boot':(0,160,0),'?':(255,255,0),'':(255,255,255)}
            im=np.array([[cm[c] for c in row] for row in L[::2,::2]],np.uint8); Image.fromarray(im).save('work/seg_SE.png')
    np.save('work/seg_pooled.npy',{k:np.concatenate(v) for k,v in pooled.items()},allow_pickle=True)
    np.save('work/seg_per.npy',per,allow_pickle=True)
