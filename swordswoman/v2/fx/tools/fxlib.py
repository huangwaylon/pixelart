"""fxlib: FX char-map library. Multi-frame txt: lines '# frame N MSms' start a frame; '.'=transparent.
 render  maps/X.txt            -> png/X_fN.png (1x RGBA), png/X_strip.png
 gif     maps/X.txt [--s 6]    -> gif/X.gif (6x, bg #6e6e6e, per-frame ms)
 lint    maps/X.txt...         -> size, colours, orphans per frame
 afterimage(rgba, ...)         -> ghost RGBA (see docstring)
"""
import sys, os, json, re
import numpy as np
from PIL import Image
D=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
PAL={k:v[0] for k,v in json.load(open(D+'fx_palette.json'))['colors'].items()}
PK={k:v[0] for k,v in json.load(open(D+'../style/pk_palette.json'))['colors'].items()}
def hx(h): return tuple(int(h[j:j+2],16) for j in (1,3,5))
RGB={k:hx(v) for k,v in PAL.items()}
BG=(0x6e,0x6e,0x6e)

def read(p):
    """-> list of (grid, ms)"""
    fr=[]; cur=None
    for l in open(p):
        l=l.rstrip('\n')
        m=re.match(r'#\s*frame\s+\d+\s+(\d+)\s*ms',l)
        if m: cur=[[],int(m.group(1))]; fr.append(cur); continue
        if l.startswith('#') or not l.strip(): continue
        if cur is None: cur=[[],100]; fr.append(cur)
        cur[0].append(l)
    out=[]
    w=max(len(l) for g,_ in fr for l in g); h=max(len(g) for g,_ in fr)
    for g,ms in fr:
        g=[l.ljust(w,'.') for l in g]+['.'*w]*(h-len(g)); out.append((g,ms))
    return out
def write(p,frames,header=''):
    s=''.join('# '+l+'\n' for l in header.split('\n') if l)
    for i,(g,ms) in enumerate(frames): s+=f'# frame {i} {ms}ms\n'+'\n'.join(g)+'\n'
    open(p,'w').write(s)
def to_img(g,s=1,bg=None,pal=None):
    pal=pal or RGB; h,w=len(g),len(g[0]); im=Image.new('RGBA',(w,h),(bg+(255,)) if bg else (0,0,0,0)); px=im.load()
    for y,l in enumerate(g):
        for x,c in enumerate(l):
            if c in pal: px[x,y]=pal[c]+(255,)
    return im.resize((w*s,h*s),Image.NEAREST) if s>1 else im
def grid_from_arr(a):
    return [''.join(r) for r in a]
def arr(g): return np.array([list(l) for l in g])

def orphans(g):
    a=arr(g); h,w=a.shape; n=[]
    for y in range(h):
        for x in range(w):
            c=a[y,x]
            if c=='.': continue
            nb=[a[yy,xx] for yy in range(y-1,y+2) for xx in range(x-1,x+2) if (yy,xx)!=(y,x) and 0<=yy<h and 0<=xx<w]
            if all(v=='.' for v in nb): n.append((x,y,c,'isolated'))
    return n
def lint(p):
    fr=read(p); bad=set(c for g,_ in fr for l in g for c in l)-set(RGB)-{'.'}
    cols=sorted(set(c for g,_ in fr for l in g for c in l)-{'.'})
    print(os.path.basename(p), f'{len(fr[0][0][0])}x{len(fr[0][0])}', f'{len(fr)}f', [ms for _,ms in fr], 'cols',''.join(cols), 'BAD' if bad else '', ''.join(bad),
          'isolated', [len(orphans(g)) for g,_ in fr])

def composite(frames_rgba, s=6, bg=BG):
    out=[]
    for im in frames_rgba:
        b=Image.new('RGBA',im.size,bg+(255,)); b.alpha_composite(im); out.append(b.convert('RGB').resize((im.width*s,im.height*s),Image.NEAREST))
    return out
def save_gif(path, frames_rgba, ms, s=6, bg=BG):
    ims=composite(frames_rgba,s,bg)
    ims[0].save(path,save_all=True,append_images=ims[1:],duration=ms,loop=0,disposal=1)

def render(p):
    name=os.path.splitext(os.path.basename(p))[0]; fr=read(p)
    ims=[to_img(g) for g,_ in fr]
    for i,im in enumerate(ims): im.save(D+f'png/{name}_f{i}.png')
    w,h=ims[0].size; st=Image.new('RGBA',(w*len(ims),h),(0,0,0,0))
    for i,im in enumerate(ims): st.paste(im,(i*w,0))
    st.save(D+f'png/{name}_strip.png'); return ims,[ms for _,ms in fr]

def gif(p,s=6,hold=200):
    name=os.path.splitext(os.path.basename(p))[0]; ims,ms=render(p)
    blank=Image.new('RGBA',ims[0].size,(0,0,0,0))
    save_gif(D+f'gif/{name}.gif',ims+[blank],ms+[hold],s)

def outline(g, col='K', diag=False):
    """add 1 px outline of col around all non-transparent pixels (grid grows by 0, uses empty space)"""
    a=arr(g); h,w=a.shape; o=a.copy()
    for y in range(h):
        for x in range(w):
            if a[y,x]!='.': continue
            nb=[(0,1),(1,0),(0,-1),(-1,0)]+([(1,1),(1,-1),(-1,1),(-1,-1)] if diag else [])
            if any(0<=y+dy<h and 0<=x+dx<w and a[y+dy,x+dx]!='.' for dy,dx in nb): o[y,x]=col
    return grid_from_arr(o)

def afterimage(rgba, light=RGB['a'], dark=RGB['A'], alpha=1.0, mode='2tone', rim=1):
    """Ghost of a sprite frame (PIL RGBA, any palette). Flat fill in `light` with a `rim`-px edge band in `dark`
    (mode '2tone'), or a single flat `dark` fill (mode '1tone'). alpha is quantised to the steps 1.0/0.75/0.5/0.25
    so a trail uses e.g. [0.75, 0.5, 0.25] for ghosts 1..3 frames old. Returns RGBA same size."""
    a=np.array(rgba.convert('RGBA')); m=a[...,3]>0
    st=min([1.0,0.75,0.5,0.25],key=lambda v:abs(v-alpha))
    out=np.zeros_like(a)
    if mode=='1tone':
        out[m,:3]=dark
    else:
        er=m.copy()
        for _ in range(rim):
            e=er.copy(); e[1:]&=er[:-1]; e[:-1]&=er[1:]; e[:,1:]&=er[:,:-1]; e[:,:-1]&=er[:,1:]; er=e
        out[m,:3]=dark; out[er,:3]=light
    out[m,3]=int(255*st)
    return Image.fromarray(out)

def whiteflash(rgba, keep_outline=True):
    """1-frame hit flash: every opaque pixel -> W, black outline pixels kept (Pokemon damage flash)."""
    a=np.array(rgba.convert('RGBA')); m=a[...,3]>0; k=m&(a[...,:3].sum(-1)==0)
    out=a.copy(); out[m,:3]=RGB['W']
    if keep_outline: out[k,:3]=0
    return Image.fromarray(out)

if __name__=='__main__':
    cmd=sys.argv[1]; args=sys.argv[2:]
    if cmd=='lint': [lint(p) for p in args]
    elif cmd=='render': [render(p) for p in args]
    elif cmd=='gif': [gif(p) for p in args]
