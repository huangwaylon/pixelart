import sys, re, json
from PIL import Image
P={k:v[0] for k,v in json.load(open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/style/pk_palette.json'))['colors'].items()}
def readp(p):
    pal=dict(P); rows=[]
    for l in open(p):
        l=l.rstrip('\n')
        m=re.match(r';\s*pal\s+(\S)\s+(#[0-9a-fA-F]{6})',l)
        if m: pal[m.group(1)]=m.group(2); continue
        if l.startswith(';') or not l: continue
        rows.append(l)
    return rows,pal
def img(p,s=1,bg=(128,128,128)):
    rows,pal=readp(p); w=max(len(r) for r in rows); im=Image.new('RGB',(w,len(rows)),bg); px=im.load()
    for y,r in enumerate(rows):
        for x,c in enumerate(r):
            if c in pal: px[x,y]=tuple(int(pal[c][j:j+2],16) for j in (1,3,5))
    return im.resize((w*s,len(rows)*s),Image.NEAREST)
if __name__=='__main__':
    img(sys.argv[1],int(sys.argv[3]) if len(sys.argv)>3 else 8).save(sys.argv[2])
