"""Round-1 review pack: polished sets per strategy (pre-polish small), refs row, labelled GIFs."""
import os
from PIL import Image, ImageDraw
R='/Users/waylonhuang/Documents/other/pixelart/swordswoman/'
OUT=R+'hybrid/review/r1/'; os.makedirs(OUT,exist_ok=True)
S=['S1_redraw','S2_gridsheet','S3_editchain','S4_textured3d','S5_pixelnative','S6_claude_pixel']
DIRS=['S','SE','E','NE','N','NW','W','SW']
SETS={'turntable':[f'turn_{d}' for d in DIRS],
      'walk':[f'walk_SE_k{i}' for i in range(4)],
      'slash':[f'slash_SE_k{i}' for i in range(4)],
      'jump':[f'jump_E_{k}' for k in ('crouch','apex','land')]}
COLHDR={'slash':['k0 antic','k1 SMEAR','k2 impact','k3 follow'],'walk':['k0 contact','k1 down','k2 pass','k3 up']}
BG=(120,120,128,255); GRASS=(78,122,58,255); INK=(255,255,255)
ref=Image.open(R+'docs/palette_v1_vs_v2_terrain.png').convert('RGBA').crop((490,20,715,350))
def load(s,n,pol=True):
    p=R+f'hybrid/{s}/r1/{"polished" if pol else "sprite"}/{n}.png'
    return Image.open(p).convert('RGBA') if os.path.exists(p) else Image.new('RGBA',(128,128))
def up(im,k): return im.resize((im.width*k,im.height*k),Image.NEAREST)
def tile(im,k,bg):
    t=Image.new('RGBA',(im.width*k,im.height*k),bg); t.alpha_composite(up(im,k)); return t
def sheet(name):
    names=SETS[name]; n=len(names); C4=4*128; LW=150; HH=24
    rowh=C4+128+8
    W=LW+n*(C4+8); H=HH+len(S)*rowh+C4+30
    sh=Image.new('RGBA',(W,H),(40,40,46,255)); d=ImageDraw.Draw(sh)
    hdr=COLHDR.get(name,[x.split('_')[-1] for x in names])
    for j,h in enumerate(hdr): d.text((LW+j*(C4+8)+4,6),h,fill=INK)
    for i,s in enumerate(S):
        y=HH+i*rowh
        d.text((4,y+4),s,fill=INK); d.text((4,y+20),'polished 4x / 1x',fill=(200,200,200))
        d.text((4,y+C4+4),'1x grass | pre 1x',fill=(200,200,200))
        for j,nm in enumerate(names):
            x=LW+j*(C4+8)
            sh.alpha_composite(tile(load(s,nm),4,BG),(x,y))
            sh.alpha_composite(tile(load(s,nm),1,GRASS),(x,y+C4+4))
            sh.alpha_composite(tile(load(s,nm,False),1,BG),(x+136,y+C4+4))
            if name=='slash' and j==1: d.rectangle((x-2,y-2,x+C4+1,y+C4+1),outline=(255,80,160),width=2)
    y=HH+len(S)*rowh; d.text((4,y+4),'REF: pixelized',fill=INK); d.text((4,y+20),'iso_v5 terrain',fill=INK)
    r=ref.resize((int(ref.width*C4/ref.height),C4),Image.NEAREST); sh.alpha_composite(r,(LW,y))
    sh.alpha_composite(ref,(LW+r.width+16,y+C4-ref.height))
    sh.convert('RGB').save(OUT+f'compare_{name}.png')
def gif(name,ms):
    names=names_=SETS[name]; k=3; LH=16; cw=128*k
    frames=[]
    for nm in names:
        fr=Image.new('RGBA',(len(S)*cw+cw,cw+LH),(40,40,46,255)); d=ImageDraw.Draw(fr)
        for i,s in enumerate(S):
            fr.alpha_composite(tile(load(s,nm),k,BG),(i*cw,LH)); d.text((i*cw+4,2),s,fill=INK)
        r=ref.resize((int(ref.width*cw/ref.height),cw),Image.NEAREST)
        fr.alpha_composite(r,(len(S)*cw,LH)); d.text((len(S)*cw+4,2),'REF iso_v5 px',fill=INK)
        d.text((4,cw+LH-14),nm,fill=INK)
        frames.append(fr.convert('RGB'))
    frames[0].save(OUT+f'compare_{name}.gif',save_all=True,append_images=frames[1:],duration=ms,loop=0)
for n in SETS: sheet(n)
gif('turntable',[400]*8); gif('walk',[160]*4)
gif('slash',[300,70,260,220])   # coil hold, fast smear, hit-stop hold, follow
gif('jump',[260,320,300])
print('ok')
