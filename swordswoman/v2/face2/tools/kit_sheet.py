"""kit_sheet.py [Z]: face_kit_sheet.png = views x expressions at Z (default 6) + 1x, size test, real trainer heads at the same scale; + _thumb.png (<=800)"""
import sys; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face2/tools'); import kit,pal
from PIL import Image, ImageDraw
Z=int(sys.argv[1]) if len(sys.argv)>1 else 6; B='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/'; O=B+'face2/'
VIEWS=['S','SE','E','NE','N']; E=kit.EXPR; TW,TH=19,22; BG=(176,190,204)
REF=[('Lyra HGSS',B+'style/refs/battle/lyra.png',(30,10,50,32)),('Dawn DPPt',B+'style/refs/battle/dawn.png',(28,13,48,35)),('Rosa B2W2',B+'style/refs/battle/rosa-bw.png',(23,11,43,33)),
     ('Hilda BW',B+'style/refs/battle/hilda-bw.png',(26,10,46,32)),('Lillie (SD)',O+'refs/sd/lillie.png',(30,11,50,33)),('Kris (SD)',O+'refs/sd/kris.png',(28,13,48,35)),('Serena (SD)',O+'refs/sd/serena.png',(26,12,46,34))]
cw=TW*Z+6; lw=40
W=lw+len(E)*cw; rows_h=len(VIEWS)*(TH*Z+8)
H=30+rows_h+20+ (TH+10)*len(VIEWS) + 30 + (22*Z+30) + 40
S=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(S)
d.text((4,4),f'FACE2 face kit on option-E placeholder head (crown-chin 15 px, head 16 px wide, bun+bow excluded; eyes 3x5) - {Z}x; 1x block below; real trainer heads at the same scale at the bottom',fill='black')
y=18
for j,e in enumerate(E): d.text((lw+j*cw,y),e,fill='black')
y+=12
for v in VIEWS:
    d.text((2,y+TH*Z//2),v,fill='black')
    for j,e in enumerate(E if v!='N' else E[:1]):
        im=pal.to_img(kit.build(v,e),Z); S.paste(im,(lw+j*cw,y),im)
    if v=='N': d.text((lw+cw+6,y+TH*Z//2),'N: no face; one cell for all expressions (head motion only)',fill='black')
    y+=TH*Z+8
y+=8; d.text((4,y),'1x (game size)',fill='black'); y+=12
for v in VIEWS:
    for j,e in enumerate(E if v!='N' else E[:1]):
        im=pal.to_img(kit.build(v,e)); S.paste(im,(lw+j*(TW+4),y),im)
    y+=TH+10
for i,(n,f,b) in enumerate(REF):
    im=Image.open(f).convert('RGBA').crop(b); S.paste(im,(lw+len(E)*(TW+4)+20+i*24,y-(TH+10)*3),im)
d.text((lw+len(E)*(TW+4)+20,y-(TH+10)*3-12),'real trainers 1x',fill='black')
y+=10; d.text((4,y),f'real Pokemon trainer heads at {Z}x (same scale): battle sprites have 1-3 px wide x 2-4 px tall eyes; ours are 3x5 (far 2x5) by design',fill='black'); y+=14
for i,(n,f,b) in enumerate(REF):
    im=Image.open(f).convert('RGBA').crop(b); x=lw+i*(20*Z+12)
    bg=Image.new('RGBA',im.size,BG+(255,)); bg.alpha_composite(im); S.paste(bg.resize((20*Z,22*Z),Image.NEAREST),(x,y)); d.text((x,y+22*Z+2),n,fill='black')
S=S.crop((0,0,W,y+22*Z+16)); S.save(O+'face_kit_sheet.png')
t=S.copy(); t.thumbnail((800,800),Image.NEAREST); t.save(O+'work/face_kit_thumb.png'); print(S.size,t.size)
