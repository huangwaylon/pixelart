"""build.py: gifs, 1x atlas.png, labelled 3x sheet.png, manifest.json (fx96, 96 px figure in 128 cell)"""
import sys, json, os
sys.path.insert(0,__file__.rsplit('/',1)[0]); import fxlib as F
from PIL import Image, ImageDraw
order=['throw_orb','throw_trail','throw_sparkle','throw_pop','hit_spark','hit_flash','speed_lines_long','speed_lines_short',
 'dust_step','dust_land','dust_skid','jump_whoosh','land_ring','hurt_star','sweat_drop']
group={'throw_orb':'throw','throw_trail':'throw','throw_sparkle':'throw','throw_pop':'throw','hit_spark':'impact','hit_flash':'impact',
 'speed_lines_long':'dash','speed_lines_short':'dash','dust_step':'dust','dust_land':'dust','dust_skid':'dust','jump_whoosh':'jump','land_ring':'jump','hurt_star':'hurt','sweat_drop':'hurt'}
old=json.load(open(F.D+'../fx/manifest.json'))
man={'version':'fx96 r1 (2026-10-27)','palette':'palette.json','format':"char-map txt: '# frame N MSms' blocks, '.' transparent; PNGs are 1x RGBA",
 'conventions':{'coords':'pixels from the top-left of the effect frame; pivot sits on the attach point',
  'facing':'all drawn facing E; for W flip x (pivot_x -> w-1-pivot_x, negate dx of offsets/arc_*, cell_offset_x -> 127-x)',
  'cell':'96 px figure in a 128x128 cell (v2/pixelize/top1), feet pivot (64,124) = soles/ground row 124; cell_offset = where the pivot goes in that cell for the reference pose (SE master EC0_SE_96)',
  'from_48':'redrawn at 2x with 1 px detail from v2/fx (48 px); old cell_offset (x,y) ~ new (64+2(x-32), 124+2(y-62))'},
 'functions':{'afterimage':'tools/fxlib.py afterimage(rgba, light=a, dark=A, alpha in {1,.75,.5,.25}, mode 2tone|1tone, rim=1): flat ghost of any frame',
  'afterimage_trail':'tools/fxlib.py afterimage_trail(rgba, step=10, n=3, dx=-1, alphas=(.75,.5,.25)): 3 ghosts 10 px apart (96 px scale) behind the motion, returns (canvas, origin_x); live frame on top, speed lines behind',
  'whiteflash':'tools/fxlib.py whiteflash(rgba): 1-frame damage flash, all opaque px -> w #f8f8f8, near-black outline (K/X) kept'},
 'throw':dict(old['throw'],note=old['throw']['note'].replace('s48','s48 (x2 for 96 px until an s96 exists)')),
 'effects':{}}
rows=[]; aw=0; y=0
for n in order:
    p=F.D+f'maps/{n}.txt'
    if not os.path.exists(p): print('MISSING',n); continue
    F.gif(p); fr=F.read(p); a=json.load(open(F.D+f'maps/{n}.anchors.json'))
    ims=[F.to_img(g) for g,_ in fr]; w,h=ims[0].size
    rects=[[i*(w+1),y,w,h] for i in range(len(ims))]; rows.append((n,ims,y)); y+=h+1; aw=max(aw,len(ims)*(w+1))
    e=dict(a); e.update(group=group[n],map=f'maps/{n}.txt',gif=f'gif/{n}.gif',frames=[f'png/{n}_f{i}.png' for i in range(len(ims))],
         strip=f'png/{n}_strip.png',ms=[ms for _,ms in fr],size=[w,h],atlas='atlas.png',atlas_rects=rects)
    man['effects'][n]=e
At=Image.new('RGBA',(aw,y),(0,0,0,0))
for n,ims,yy in rows:
    for i,im in enumerate(ims): At.paste(im,(i*(ims[0].width+1),yy))
At.save(F.D+'atlas.png')
s=int(sys.argv[1]) if len(sys.argv)>1 else 3; lab=150
W=lab+max(len(ims)*(ims[0].width*s+8) for _,ims,_ in rows); H=sum(ims[0].height*s+8 for _,ims,_ in rows)+8
S=Image.new('RGB',(W,H),(50,50,50)); d=ImageDraw.Draw(S); yy=4
for n,ims,_ in rows:
    a=man['effects'][n]; d.text((4,yy+2),n,fill=(235,235,235)); d.text((4,yy+14),f"{a['size'][0]}x{a['size'][1]} {'/'.join(map(str,a['ms']))}ms",fill=(170,170,170)); d.text((4,yy+26),f"attach {a.get('attach')}",fill=(170,170,170))
    x=lab
    for im in ims:
        b=Image.new('RGBA',im.size,F.BG+(255,)); b.alpha_composite(im); b=b.convert('RGB').resize((im.width*s,im.height*s),Image.NEAREST)
        S.paste(b,(x,yy)); px,py=a['pivot']; d.rectangle([x+px*s,yy+py*s,x+px*s+s-1,yy+py*s+s-1],outline=(255,0,0)); x+=im.width*s+8
    yy+=ims[0].height*s+8
S.save(F.D+'sheet.png'); print('sheet',S.size,'atlas',At.size)
json.dump(man,open(F.D+'manifest.json','w'),indent=1)
