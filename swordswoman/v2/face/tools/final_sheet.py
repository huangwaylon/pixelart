"""final_sheet.py: FINAL_expr_sheet.png (sprite faces S/SE/E at 4x + 1x, next to real BW/HGSS trainer faces + Gen5 OW at the
same scales) and FINAL_portraits.png (12 PMD-style portraits at 3x on emotion pastel bg above real PMD Meloetta, + 1x strips)."""
import sys, os; sys.path.insert(0,os.path.dirname(__file__)); import faces, fc, prender, make_sheet
from PIL import Image, ImageDraw
D='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face/'
def sprite_sheet(sc=4):
    views=['S','SE','E']; cells={(v,e):fc.pk.to_img([''.join(r) for r in faces.build_view(D+f'heads/E_{v}_base.txt',v,e)],1) for v in views for e in faces.EXPR}
    cw=19*sc+6; ox=40; W=ox+cw*len(faces.EXPR)+4
    refs=make_sheet.refimgs(1); rw=sum(r.width*sc+8 for r in refs)
    W=max(W,ox+rw); H=20+len(views)*(24*sc+6)+40+30+max(r.height for r in refs)*sc+50+max(r.height for r in refs)+20
    B=Image.new('RGB',(W,H),(128,128,128)); d=ImageDraw.Draw(B)
    d.text((4,2),'FINAL sprite expressions (Level E head 19x24, 4x and true 1x) vs real Pokemon trainers at the same scale',fill=(255,255,255))
    for j,e in enumerate(faces.EXPR): d.text((ox+j*cw,14),e[:11],fill=(255,255,255))
    y=26
    for v in views:
        d.text((4,y+24*sc//2),v,fill=(255,255,255))
        for j,e in enumerate(faces.EXPR):
            im=cells[v,e]; B.paste(im.resize((im.width*sc,im.height*sc),Image.NEAREST),(ox+j*cw,y),im.resize((im.width*sc,im.height*sc),Image.NEAREST))
        y+=24*sc+6
    d.text((4,y+8),'1x',fill=(255,255,255))
    for i,v in enumerate(views):
        for j,e in enumerate(faces.EXPR): B.paste(cells[v,e],(ox+j*cw+i*22,y+4),cells[v,e])
    y+=40
    d.text((4,y),'REAL (same scale): Lyra, Dawn, Hilda, Rosa, Lass BW, Lass G4, Battle Girl BW | PMD Meloetta portraits | Gen5 overworld',fill=(255,255,255)); y+=14
    x=ox
    for r in refs:
        R=r.resize((r.width*sc,r.height*sc),Image.NEAREST); B.paste(R,(x,y),R); x+=R.width+8
    y+=max(r.height for r in refs)*sc+8; x=ox
    for r in refs: B.paste(r,(x,y),r); x+=r.width+6
    return B
PO=['neutral','determined','shout','effort','joy','smile','surprised','pain','worried','inspired','teary','blink']
RM={'neutral':'Normal','determined':'Determined','shout':'Shouting','effort':'Angry','joy':'Joyous','smile':'Happy','surprised':'Surprised','pain':'Pain','worried':'Worried','inspired':'Inspired','teary':'Teary','blink':'Stunned'}
BG={'neutral':(176,216,232),'determined':(240,128,150),'shout':(168,224,208),'effort':(240,128,150),'joy':(248,232,144),'smile':(248,232,144),'surprised':(200,224,248),'pain':(120,136,184),'worried':(120,160,200),'inspired':(248,232,144),'teary':(240,184,200),'blink':(176,216,232)}
def portrait_sheet(sc=3):
    cols=6; tw=40*sc+8; th=40*sc+16
    B=Image.new('RGB',(tw*cols+8,20+4*th+120),(128,128,128)); d=ImageDraw.Draw(B)
    d.text((4,4),'FINAL PMD-style portraits 40x40 (3x; pastel bg = sheet only, files transparent) above REAL PMD SpriteCollab Meloetta, same slot',fill=(255,255,255))
    for k,o in enumerate(PO):
        x=(k%cols)*tw+4; y=20+(k//cols)*th*2
        d.text((x,y),o+(' (=Stunned)' if o=='blink' else ''),fill=(255,255,255)); B.paste(prender.img(D+f'portrait/P_{o}.txt',sc,BG[o]),(x,y+12))
        r=Image.open(D+f'refs/pmd_portrait/0648_{RM[o]}.png').convert('RGBA').resize((40*sc,40*sc),Image.NEAREST)
        d.text((x,y+th),'PMD '+RM[o],fill=(220,220,220)); B.paste(r,(x,y+th+12),r)
    y=20+4*th+8; d.text((4,y),'true 1x: ours (incl. P_blink_calm) / PMD',fill=(255,255,255)); y+=14
    for k,o in enumerate(PO+['blink_calm']):
        B.paste(prender.img(D+f'portrait/P_{o}.txt',1,BG.get(o,(176,216,232))),(4+k*44,y))
        if o in RM:
            r=Image.open(D+f'refs/pmd_portrait/0648_{RM[o]}.png').convert('RGBA'); B.paste(r,(4+k*44,y+44),r)
    return B
if __name__=='__main__':
    P=portrait_sheet(); P.save(D+'out/FINAL_portraits.png'); t=P.copy(); t.thumbnail((800,800)); t.save(D+'work/FINAL_portraits_thumb.png'); print(P.size)
    B=sprite_sheet(); B.save(D+'out/FINAL_expr_sheet.png'); t=B.copy(); t.thumbnail((800,800)); t.save(D+'work/FINAL_expr_sheet_thumb.png'); print(B.size)
