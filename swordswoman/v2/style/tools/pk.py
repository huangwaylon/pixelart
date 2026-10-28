"""pk.py: char-map tools for Pokemon-style tests. palette v2/style/pk_palette.json, '.' transparent.
 snap  src.png out.txt H [--w W] [--bg auto|white|grey] [--no-kat] [--outline]   image -> char-map, figure height H px, palette-locked
 render in.txt out.png [--s N] [--bg]                                           char-map -> png
 lint  in.txt...                                                                 colours used, off-palette, orphans, size
"""
import sys, json, numpy as np
from PIL import Image
D='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/style/'
PJ=json.load(open(D+'pk_palette.json'))['colors']
RGB={k:tuple(int(v[0][j:j+2],16) for j in (1,3,5)) for k,v in PJ.items()}
GREY=(128,128,128)
def read(p):
    L=[l.rstrip('\n') for l in open(p)]
    L=[l for l in L if l and set(l)<=set(RGB)|{'.'}]
    w=max(len(l) for l in L); return [l.ljust(w,'.') for l in L]
def write(p,g): open(p,'w').write('\n'.join(g)+'\n')
def to_img(g,s=1,bg=False):
    h,w=len(g),len(g[0]); im=Image.new('RGBA',(w,h),GREY+(255,) if bg else (0,0,0,0)); px=im.load()
    for y,l in enumerate(g):
        for x,c in enumerate(l):
            if c in RGB: px[x,y]=RGB[c]+(255,)
    return im.resize((w*s,h*s),Image.NEAREST)
def lab(a):
    a=a/255.0; a=np.where(a>0.04045,((a+0.055)/1.055)**2.4,a/12.92)
    M=np.array([[0.4124,0.3576,0.1805],[0.2126,0.7152,0.0722],[0.0193,0.1192,0.9505]]); xyz=a@M.T/np.array([0.9505,1,1.089])
    f=np.where(xyz>0.008856,np.cbrt(xyz),7.787*xyz+16/116)
    return np.stack([116*f[...,1]-16,500*(f[...,0]-f[...,1]),200*(f[...,1]-f[...,2])],-1)
def snap(src,H,W=None,bgmode='auto',kat=True,outline=False,cell=None):
    im=Image.open(src).convert('RGBA'); a=np.array(im).astype(float); x=a[...,:3]
    if bgmode=='auto':
        c=np.concatenate([x[:4].reshape(-1,3),x[-4:].reshape(-1,3),x[:,:4].reshape(-1,3),x[:,-4:].reshape(-1,3)]); bgc=np.median(c,0)
    else: bgc=np.array((255,255,255) if bgmode=='white' else GREY,float)
    m=(np.abs(x-bgc).max(-1)>28)&(a[...,3]>128)
    ys,xs=np.where(m); x=x[ys.min():ys.max()+1,xs.min():xs.max()+1]; m=m[ys.min():ys.max()+1,xs.min():xs.max()+1]
    h0,w0=m.shape; w=W or max(1,round(w0*H/h0)); mf=m.astype(np.float32)
    cov=np.array(Image.fromarray(mf,'F').resize((w,H),Image.BOX))
    num=np.stack([np.array(Image.fromarray((x[...,c]*mf).astype(np.float32),'F').resize((w,H),Image.BOX)) for c in range(3)],-1)
    col=num/np.maximum(cov[...,None],1e-6)
    keys=[k for k in RGB if kat or k not in 'nk']; P=lab(np.array([RGB[k] for k in keys],float))
    L=lab(col); d=((L[:,:,None,:]-P[None,None])**2).sum(-1); idx=d.argmin(-1)
    g=[''.join(keys[idx[y,xx]] if cov[y,xx]>0.5 else '.' for xx in range(w)) for y in range(H)]
    if outline:
        G=[list(r) for r in g]
        for y in range(H):
            for xx in range(w):
                if g[y][xx]!='.':
                    nb=[(y+dy,xx+dx) for dy,dx in((1,0),(-1,0),(0,1),(0,-1))]
                    if any(not(0<=yy<H and 0<=x2<w) or g[yy][x2]=='.' for yy,x2 in nb): G[y][xx]='K'
        g=[''.join(r) for r in G]
    if cell:
        cw,ch=cell; pad=[ '.'*cw for _ in range(ch-H-2)]
        lx=(cw-w)//2; g=pad+['.'*lx+r+'.'*(cw-w-lx) for r in g]+['.'*cw]*2
    return g
def lint(p):
    g=read(p); h,w=len(g),len(g[0]); used={}
    for l in g:
        for c in l:
            if c!='.': used[c]=used.get(c,0)+1
    orph=0
    for y in range(h):
        for x in range(w):
            c=g[y][x]
            if c in '.K': continue
            nb=[g[y+dy][x+dx] for dy in(-1,0,1) for dx in(-1,0,1) if (dy or dx) and 0<=y+dy<h and 0<=x+dx<w]
            if c not in nb: orph+=1
    edge=[(y,x) for y in range(h) for x in range(w) if g[y][x]!='.' and any(not(0<=y+dy<h and 0<=x+dx<w) or g[y+dy][x+dx]=='.' for dy,dx in((1,0),(-1,0),(0,1),(0,-1)))]
    nonk=sum(g[y][x]!='K' for y,x in edge)
    ys=[y for y in range(h) if g[y].strip('.')]; print(f"{p.split('/')[-1]}: {w}x{h} fig_h={ys[-1]-ys[0]+1 if ys else 0} colours={len(used)} orphans={orph} edge_nonK={nonk}/{len(edge)} used={''.join(sorted(used))}")
if __name__=='__main__':
    a=sys.argv; cmd=a[1]
    def opt(n,d=None):
        return a[a.index(n)+1] if n in a else d
    if cmd=='snap':
        cell=opt('--cell'); cell=tuple(map(int,cell.split('x'))) if cell else None
        g=snap(a[2],int(a[4]),int(opt('--w',0)) or None,opt('--bg','auto'),'--no-kat' not in a,'--outline' in a,cell); write(a[3],g); lint(a[3])
    elif cmd=='render':
        to_img(read(a[2]),int(opt('--s',1)),'--bg' in a).save(a[3])
    elif cmd=='lint':
        for p in a[2:]: lint(p)
