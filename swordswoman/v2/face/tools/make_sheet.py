"""make_sheet.py tag: expression sheet (Level E views x expressions, C_r4 SE fit, real refs) at 6x and 1x + thumbs."""
import sys, os; sys.path.insert(0,os.path.dirname(__file__)); import faces, fc, build_all
from PIL import Image, ImageDraw
D='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face/'; R='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/style/refs/'
tag=sys.argv[1] if len(sys.argv)>1 else 'v1'
REFS=[(R+'battle/lyra.png',(27,14,49,38)),(R+'battle/dawn.png',(26,16,48,40)),(R+'battle/hilda-bw.png',(23,14,45,38)),(R+'battle/rosa-bw.png',(26,15,48,39)),
      (R+'battle/lass-bw.png',(30,12,52,36)),(R+'battle/lass-gen4.png',(23,7,45,31)),(R+'battle/battlegirl-bw.png',(36,8,58,32)),
      (D+'refs/pmd_portrait/0648_Normal.png',None),(D+'refs/pmd_portrait/0648_Happy.png',None),(D+'refs/pmd_portrait/0648_Angry.png',None)]
def refimgs(sc):
    out=[]
    for f,b in REFS:
        im=Image.open(f).convert('RGBA')
        if b: im=im.crop(b)
        out.append(im.resize((im.width*sc,im.height*sc),Image.NEAREST))
    # gen5 overworld (stored 2x) -> 1x
    ow=Image.open(R+'gen5/NPC_08.png').convert('RGBA').crop((0,0,64,48)); ow=ow.resize((32,24),Image.NEAREST)
    out.append(ow.resize((32*sc,24*sc),Image.NEAREST))
    return out
def cfit(sc):
    base=D+'heads/C_r4_SE_base.txt'; ims=[]
    for ex in faces.EXPR:
        g=faces.build_view(base,'SE',ex) if ex!='squash' else faces.build(base,'SE',ex,faces.anchors(base))
        s=[r[20:46] for r in [''.join(x) for x in g][12:40]]; fc.pk.write(D+f'out/sprite/C_SE_{ex}.txt',[''.join(x) for x in g])
        ims.append(fc.pk.to_img(s,sc))
    return ims
def sheet(sc,label=True):
    G,_=build_all.grid(sc,label=label); C=cfit(sc); Rf=refimgs(sc)
    cw=(G.width-(28 if label else 2))//len(faces.EXPR)
    hC=max(i.height for i in C)+6; hR=max(i.height for i in Rf)+6; ty=14 if label else 2
    cc=C[0].width+4
    W=max(G.width,(28 if label else 2)+len(C)*cc, sum(i.width+4 for i in Rf)+8)
    B=Image.new('RGB',(W,G.height+hC+hR+3*ty),(128,128,128)); d=ImageDraw.Draw(B); B.paste(G,(0,0))
    y=G.height+ty
    if label: d.text((2,y-12),'C_r4 SE fit (old 48px test body/head, same grammar)',fill=(255,255,255))
    for j,im in enumerate(C): B.paste(im,((28 if label else 2)+j*cc,y),im)
    y+=hC+ty
    if label: d.text((2,y-12),'REAL refs same scale: Lyra Dawn Hilda Rosa Lass-BW Lass-G4 BattleGirl-BW | PMD portrait Meloetta normal/happy/angry (40px) | BW overworld',fill=(255,255,255))
    x=4
    for im in Rf: B.paste(im,(x,y),im); x+=im.width+4
    return B
if __name__=='__main__':
    S6=sheet(6); S6.save(D+f'out/expr_sheet_6x_{tag}.png'); S1=sheet(1,label=False); S1.save(D+f'out/expr_sheet_1x_{tag}.png')
    S3=sheet(3); S3.save(D+f'out/expr_sheet_3x_{tag}.png')
    t=S6.copy(); t.thumbnail((990,990),Image.NEAREST); t.save(D+f'out/expr_sheet_6x_{tag}_thumb.png')
    S1.resize((S1.width*2,S1.height*2),Image.NEAREST).save(D+f'out/expr_sheet_1x_{tag}_at2x.png')
    print(S6.size,S3.size,S1.size)
