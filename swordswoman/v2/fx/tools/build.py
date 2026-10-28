"""build.py: gifs, 1x atlas (atlas_48.png / atlas_32.png), labelled 4x sheet (sheet_48.png, sheet_32.png), manifest.json"""
import sys, json, glob, os
sys.path.insert(0,__file__.rsplit('/',1)[0]); import fxlib as F
from PIL import Image, ImageDraw
order=['slash_h','slash_diag','slash_over','hit_spark','hit_flash','speed_lines_long','speed_lines_short','dust_step','dust_land','dust_skid','jump_whoosh','land_ring','hurt_star','sweat_drop']
group={'slash_h':'slash','slash_diag':'slash','slash_over':'slash','hit_spark':'impact','hit_flash':'impact','speed_lines_long':'dash','speed_lines_short':'dash',
 'dust_step':'dust','dust_land':'dust','dust_skid':'dust','jump_whoosh':'jump','land_ring':'jump','hurt_star':'hurt','sweat_drop':'hurt'}
man={'version':'fx r3 (2026-10-26)','palette':'fx_palette.json','format':"char-map txt: '# frame N MSms' blocks, '.' transparent; PNGs are 1x RGBA",
 'conventions':{'coords':'pixels from the top-left of the effect frame; pivot sits on the attach point','facing':'all drawn facing E; for W flip x (pivot_x -> w-1-pivot_x, negate dx of offsets/arc_*)',
  'cell':'primary: 48 px figure in a 64x64 cell, feet pivot (32,62); cell_offset = where the pivot goes in that cell for the reference pose',
  'size_40':'for a 40 px figure scale cell_offset relative to the feet by 40/48 (effects unchanged; checked in context_48.png bottom rows)'},
 'functions':{'afterimage':'tools/fxlib.py afterimage(rgba, light=a, dark=A, alpha in {1,.75,.5,.25}, mode 2tone|1tone, rim=1): flat ghost of any frame; trail = ghosts 5 px apart at .75/.5/.25, speed lines drawn behind',
  'whiteflash':'tools/fxlib.py whiteflash(rgba): 1-frame damage flash, all opaque px -> W, black outline kept'},
 'effects':{},'secondary_32':{}}
def build(mapdir,suffix,key,atlas_name,sheet_name):
    rows=[]; aw=0; y=0; rects={}
    for n in order:
        fn=n+suffix; p=F.D+f'{mapdir}/{fn}.txt'
        if not os.path.exists(p): continue
        F.gif(p); fr=F.read(p); a=json.load(open(F.D+f'{mapdir}/{fn}.anchors.json'))
        ims=[F.to_img(g) for g,_ in fr]; w,h=ims[0].size
        rects[fn]=[[i*(w+1),y,w,h] for i in range(len(ims))]; rows.append((fn,ims,y)); y+=h+1; aw=max(aw,len(ims)*(w+1))
        e=dict(a); e.update(group=group[n],map=f'{mapdir}/{fn}.txt',gif=f'gif/{fn}.gif',frames=[f'png/{fn}_f{i}.png' for i in range(len(ims))],
             strip=f'png/{fn}_strip.png',ms=[ms for _,ms in fr],size=[w,h],atlas=atlas_name,atlas_rects=rects[fn])
        man[key][fn]=e
    At=Image.new('RGBA',(aw,y),(0,0,0,0))
    for fn,ims,yy in rows:
        for i,im in enumerate(ims): At.paste(im,(i*(ims[0].width+1),yy))
    At.save(F.D+atlas_name)
    s=4; lab=150; W=lab+max(len(ims)*(ims[0].width*s+8) for _,ims,_ in rows); H=sum(ims[0].height*s+8 for _,ims,_ in rows)+8
    S=Image.new('RGB',(W,H),(50,50,50)); d=ImageDraw.Draw(S); yy=4
    for fn,ims,_ in rows:
        a=man[key][fn]; d.text((4,yy+2),fn,fill=(235,235,235)); d.text((4,yy+14),f"{a['size'][0]}x{a['size'][1]} {'/'.join(map(str,a['ms']))}ms",fill=(170,170,170)); d.text((4,yy+26),f"attach {a['attach']}",fill=(170,170,170))
        x=lab
        for im in ims:
            b=Image.new('RGBA',im.size,F.BG+(255,)); b.alpha_composite(im); b=b.convert('RGB').resize((im.width*s,im.height*s),Image.NEAREST)
            S.paste(b,(x,yy)); px,py=a['pivot']; d.rectangle([x+px*s,yy+py*s,x+px*s+s-1,yy+py*s+s-1],outline=(255,0,0)); x+=im.width*s+8
        yy+=ims[0].height*s+8
    S.save(F.D+sheet_name); print(sheet_name,S.size,atlas_name,At.size)
build('maps','','effects','atlas_48.png','sheet_48.png')
build('maps32','_32','secondary_32','atlas_32.png','sheet_32.png')
json.dump(man,open(F.D+'manifest.json','w'),indent=1)
