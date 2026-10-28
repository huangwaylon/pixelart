"""context.py OUT.png [scale] [frame]: every effect (maps/*.txt, anchors cell_offset) over the 48 px figure (C_r3) and the 40 px figure (A_r1),
offsets from the feet scaled by fig_h/48 for the 40 px check. Two rows per effect group, bg #6e6e6e."""
import sys, json, glob, os
sys.path.insert(0,__file__.rsplit('/',1)[0]); import fxlib as F
from PIL import Image
S=int(sys.argv[2]) if len(sys.argv)>2 else 2; FR=int(sys.argv[3]) if len(sys.argv)>3 else 0
PKR={k:F.hx(v) for k,v in F.PK.items()}
def fig(path):
    g=[l.rstrip('\n') for l in open(path) if l.strip()]; im=F.to_img(g,pal=PKR)
    bb=im.getbbox(); return im,bb
figs=[]
for p,h in [(F.D+'../style/tests/C_r3.txt',48),(F.D+'../style/tests/A_r1.txt',40)]:
    im,bb=fig(p); c=Image.new('RGBA',(64,80),(0,0,0,0)); fx=(bb[0]+bb[2])//2; fy=bb[3]-1
    c.alpha_composite(im,(32-fx,70-fy)); figs.append((c,h))
names=sorted(os.path.basename(p)[:-4] for p in glob.glob(F.D+'maps/*.txt'))
panels=[]
for fi,(c,h) in enumerate(figs):
    for n in names:
        a=json.load(open(F.D+f'maps/{n}.anchors.json')); fr=F.read(F.D+f'maps/{n}.txt'); g=fr[min(FR,len(fr)-1)][0]
        e=F.to_img(g); co=a.get('cell_offset',[32,62]); k=h/48
        if isinstance(co,dict): co=list(co.values())[0]
        x=32+round((co[0]-32)*k); y=70+round((co[1]-62)*k)
        P=Image.new('RGBA',(64,80),F.BG+(255,)); 
        if a.get('layer','over').startswith('behind'): P.alpha_composite(e,(x-a['pivot'][0],y-a['pivot'][1])); P.alpha_composite(c)
        else: P.alpha_composite(c); P.alpha_composite(e,(x-a['pivot'][0],y-a['pivot'][1]))
        panels.append(P)
cols=len(names); W=cols*64*S; H=2*80*S
B=Image.new('RGB',(W+cols*S,H+S),(40,40,40))
for i,P in enumerate(panels): B.paste(P.convert('RGB').resize((64*S,80*S),Image.NEAREST),((i%cols)*(64*S+S),(i//cols)*(80*S+S)))
B.save(sys.argv[1]); print(B.size, names)
