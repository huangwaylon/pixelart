import json,os,glob
from PIL import Image
ROOT='/Users/waylonhuang/Documents/other/pixelart/'
REL=ROOT+'REVIEW/exp/2026-10-28_sw_skinned/release/'
B=REL+'out/20261030_66119a7/work/'
def info(act,v):
    clip=json.load(open(f'{B}{act}/{v}/clip.json'))
    p=REL+clip['passes']+'/'+clip['stem']+'.json'
    if not os.path.exists(p): p=f"{B}{act}/{v}/{clip['stem']}.json"
    return json.load(open(p)),clip
def final(act,v,i):
    return Image.open(f'{B}{act}/{v}/final/f{i:02d}.png').convert('RGBA')
PAL=json.load(open(ROOT+'swordswoman/v2/pixelize/palette.json'))['colors']
HEX={k:tuple(int(v['hex'][j:j+2],16) for j in (1,3,5)) for k,v in PAL.items()}
INV={v:k for k,v in HEX.items()}
import numpy as np
SKIN=np.array([248,218,194],float)
def px_align(act,v):
    clip=json.load(open(f'{B}{act}/{v}/clip.json'))
    p=f"{B}{act}/{v}/{clip['stem']}_px.json"
    return json.load(open(p))['align']
def pass_img(act,v,i,kind):
    clip=json.load(open(f'{B}{act}/{v}/clip.json'))
    a=np.asarray(Image.open(REL+clip['passes']+f"/{clip['stem']}_f{i:02d}_{kind}.png").convert('RGBA')).astype(float)
    al=px_align(act,v); dx,dy=al['dx'],al['dy']
    a=a[256:256+1024,256:256+1024]
    return np.roll(np.roll(a,dy*8,0),dx*8,1)
def blocks(a): return a.reshape(128,8,128,8,-1).transpose(0,2,1,3,4).reshape(128,128,64,-1)
def skin_mask(act,v,i):
    g=pass_img(act,v,i,'guide'); d=np.abs(g[...,:3]-SKIN).sum(-1)<30
    d&=g[...,3]>128
    return blocks(d[...,None].astype(float))[...,0].mean(-1)
FM=json.load(open(REL.replace('release/','')+'rig/face_mats.json'))
import sys
sys.path.insert(0,ROOT+'REVIEW/exp/2026-10-28_sw_hires3d/scripts')
import hx
ALLM=dict(hx.MATS); ALLM.update({k:tuple(v) for k,v in FM['mats'].items()})
MNAMES=list(ALLM); MCOLS=np.array([ALLM[k] for k in MNAMES],float)
def lin2s(c):
    return c
def mat_cells(act,v,i):
    g=pass_img(act,v,i,'guide'); al=g[...,3]>128
    d=((g[...,None,:3]-MCOLS[None,None])**2).sum(-1); mid=d.argmin(-1); mid[~al]=-1
    b=blocks(mid[...,None])[...,0]
    out=np.full((128,128),-1)
    for y in range(128):
        for x in range(128):
            vals,cnt=np.unique(b[y,x],return_counts=True); out[y,x]=vals[cnt.argmax()]
    return out
FACEMATS=['skin']+list(FM['mats'])
def face_mask(act,v,i,cover=0.5):
    g=pass_img(act,v,i,'guide'); al=g[...,3]>128
    d=((g[...,None,:3]-MCOLS[None,None])**2).sum(-1); mid=d.argmin(-1)
    fm=np.isin(mid,[MNAMES.index(k) for k in FACEMATS])&al
    return blocks(fm[...,None].astype(float))[...,0].mean(-1)
def rpos(act,v,i):
    clip=json.load(open(f'{B}{act}/{v}/clip.json')); pd=REL+clip['passes']+'/parts/'
    R_=json.load(open(pd+'rpos.json')); lo,hi=np.array(R_['lo']),np.array(R_['hi'])
    a=hx.rd16(pd+f"{clip['stem']}_f{i:02d}_rpos.png")
    al=px_align(act,v); dx,dy=al['dx'],al['dy']
    a=a[256:256+1024,256:256+1024]; a=np.roll(np.roll(a,dy*8,0),dx*8,1)
    return a[...,:3]*(hi-lo)+lo, a[...,3]>0.5
# chart = S-master pixel coords on the front planar face chart (x,z rest metres)
CX0,CXS=63.95,0.01473; CY0,CZ0,CZS=52.0,1.2249,0.01706
def to_chart(rp): return CX0-rp[...,0]/CXS, CY0-(rp[...,2]-CZ0)/CZS
