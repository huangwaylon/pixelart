"""ds.py V [h=48]: palette-locked material-constrained downsample of turnE_final/iso_V -> work/ds_V.txt/.png, work/ill_V.png (crop at master scale x4)"""
import sys, json, numpy as np
from PIL import Image
sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/final/tools'); from seg import seg
F='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/final/'
S='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/hair/turnE_final/'
PAL={k:(v['hex'] if isinstance(v,dict) else v[0]) for k,v in json.load(open(F+'palette.json'))['colors'].items()}
KEYS=list(PAL); rgb=np.array([[int(PAL[k][j:j+2],16) for j in (1,3,5)] for k in KEYS],float)
ALLOW={'K':'K','hair':'KhHgLW','boot':'KhHgL','red':'RE','skin':'sSm','obi':'oOQ','?':'KhHgLsSmReEoOQW'}
MIRROR=set()  # r2: SE now from iso_SE_r2.png (correct lower-right facing), no mirror
SRC={'SE':'iso_SE_r2.png'}
def illus(v):
    x=np.array(Image.open(S+SRC.get(v,f'iso_{v}.png')).convert('RGB')).astype(float)
    if v in MIRROR: x=x[:,::-1].copy()
    m=(x.min(-1)<215)|(x.max(-1)-x.min(-1)>30)
    ys,xs=np.where(m); y0,y1,x0,x1=ys.min(),ys.max(),xs.min(),xs.max()
    return x[y0:y1+1,x0:x1+1],m[y0:y1+1,x0:x1+1]
def snapmap(x,m):
    L=seg(x,m,0,x.shape[0]-1)
    d=((x[:,:,None,:]-rgb[None,None])**2).sum(-1)
    idx=np.full(m.shape,-1)
    for mat,al in ALLOW.items():
        sel=(L==mat)
        if not sel.any(): continue
        cols=[KEYS.index(c) for c in al]; dd=d[sel][:,cols]; idx[sel]=np.array(cols)[dd.argmin(1)]
    br=m&(x.min(-1)>200)&((x.max(-1)-x.min(-1))<40)&(L!='obi'); idx[br]=KEYS.index('W')
    return idx,L
KW=0.3
FEAT=True
def clean(sub,mm):
    # interior K specks / orphans -> majority of 4-neighbours (keep W glints)
    h,w=sub.shape
    for _ in range(2):
        out=sub.copy()
        for r in range(1,h-1):
            for c in range(1,w-1):
                if not mm[r,c] or sub[r,c] in 'W.': continue
                nb=[sub[r-1,c],sub[r+1,c],sub[r,c-1],sub[r,c+1]]
                if '.' in nb: continue
                same=sum(n==sub[r,c] for n in nb+[sub[r-1,c-1],sub[r-1,c+1],sub[r+1,c-1],sub[r+1,c+1]])
                if same==0:
                    cand=[n for n in nb if n not in 'W']
                    if cand: out[r,c]=max(set(cand),key=cand.count)
        sub=out
    return sub
def down(v,h=48,F4=4,top=14,foot=61,N=64):
    x,m=illus(v); H,W=m.shape; w=max(1,round(W*h/H))
    hi=np.array(Image.fromarray(x.astype(np.uint8)).resize((w*F4,h*F4),Image.LANCZOS)).astype(float)
    hm=np.array(Image.fromarray(m.astype(np.uint8)*255).resize((w*F4,h*F4),Image.BOX))>127
    idx,_=snapmap(hi,hm); idx[~hm]=-1
    blk=idx.reshape(h,F4,w,F4).transpose(0,2,1,3).reshape(h,w,F4*F4)
    wt=np.ones(len(KEYS)); wt[KEYS.index('K')]=KW; wt[KEYS.index('W')]=2.5; wt[KEYS.index('m')]=1.5
    votes=np.stack([(blk==k).sum(-1)*wt[k] for k in range(len(KEYS))],-1)
    q=votes.argmax(-1); mm=(blk>=0).sum(-1)>F4*F4*0.45
    if FEAT:
        from scipy import ndimage as nd
        sk=np.isin(idx,[KEYS.index(c) for c in 'sSm']); hd=int(idx.shape[0]*0.40); sk[hd:]=False
        hull=nd.binary_fill_holes(nd.binary_closing(sk,iterations=5)); face=(hull.reshape(h,F4,w,F4).mean((1,3))>0.5)
        n=F4*F4; cnt=lambda cs:np.stack([(blk==KEYS.index(c)).sum(-1) for c in cs],-1)
        eye=cnt('KhHgL'); wc=cnt('W')[...,0]; red=cnt('ER')
        for r in range(int(h*0.40)):
            for c in range(w):
                if face[r,c]:
                    if wc[r,c]>=2: q[r,c]=KEYS.index('W')
                    elif eye[r,c].sum()>=n*0.30: q[r,c]=KEYS.index('KhHgL'[np.argmax(eye[r,c]*np.array([2.0,1.5,0.25,1.2,1.4]))])
                elif red[r,c].sum()>=n*0.30: q[r,c]=KEYS.index('ER'[np.argmax(red[r,c])])
    p=np.pad(mm,1); e=mm&~(p[:-2,1:-1]&p[2:,1:-1]&p[1:-1,:-2]&p[1:-1,2:])
    g=np.full((N,N),'.',dtype='<U1'); ox=(N-w)//2
    sub=np.array([[KEYS[q[r,c]] if mm[r,c] else '.' for c in range(w)] for r in range(h)]); sub[e]='K'; sub=clean(sub,mm)
    g[foot-h+1:foot+1,ox:ox+w]=sub
    # illustration crop at same scale x4, placed in a 64x64 cell x4
    ill=Image.new('RGB',(256,256),'white'); ill.paste(Image.fromarray(x.astype(np.uint8)).resize((w*4,h*4),Image.LANCZOS),(ox*4,(foot-h+1)*4))
    return g,ill
def save(g,p): open(p,'w').write('\n'.join(''.join(r) for r in g)+'\n')
def render(g,s=1):
    im=Image.new('RGBA',(64,64),(0,0,0,0)); px=im.load()
    for y in range(64):
        for xx in range(64):
            c=g[y][xx]
            if c in PAL: hx=PAL[c]; px[xx,y]=(int(hx[1:3],16),int(hx[3:5],16),int(hx[5:7],16),255)
    return im.resize((64*s,64*s),0)
if __name__=='__main__':
    if sys.argv[1]=='2x':
        for v in sys.argv[2:]:
            g,_=down(v,h=96,top=28,foot=123,N=128); g=g[16:76]; open(F+f'work/ds2_{v}.txt','w').write('; 2x detail map: rows 16-75 of a 128 cell (master row = (r+16)//2 , master col = c//2)\n'+'\n'.join(''.join(r) for r in g)+'\n'); print(v,'2x ok')
        sys.exit()
    for v in sys.argv[1:]:
        g,ill=down(v); save(g,F+f'work/ds_{v}.txt'); render(g,4).save(F+f'work/ds_{v}_4x.png'); ill.save(F+f'work/ill_{v}.png')
        print(v,'ok')
