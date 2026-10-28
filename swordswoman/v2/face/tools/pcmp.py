import sys, os; sys.path.insert(0,os.path.dirname(__file__)); import prender
from PIL import Image, ImageDraw
D='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face/'
O=['neutral','determined','shout','effort','joy','smile','surprised','pain','worried','inspired','teary','blink']
RM={'neutral':'Normal','determined':'Determined','shout':'Shouting','effort':'Angry','joy':'Joyous','smile':'Happy','surprised':'Surprised','pain':'Pain','worried':'Worried','inspired':'Inspired','teary':'Teary','blink':'Stunned'}
BG={'neutral':(176,216,232),'determined':(240,128,150),'shout':(168,224,208),'effort':(240,128,150),'joy':(248,232,144),'smile':(248,232,144),'surprised':(200,224,248),'pain':(120,136,184),'worried':(120,160,200),'inspired':(248,232,144),'teary':(240,184,200),'blink':(176,216,232)}
sc=int(sys.argv[1]); out=sys.argv[2]; cols=6; tw=40*sc+6; th=40*sc+14
B=Image.new('RGB',(tw*cols+120,th*4+20),(128,128,128)); d=ImageDraw.Draw(B)
for k,o in enumerate(O):
    x=(k%cols)*tw+4; y=(k//cols)*th*2
    d.text((x,y+1),o,fill=(255,255,255)); B.paste(prender.img(D+f'portrait/P_{o}.txt',sc,BG[o]),(x,y+12))
    r=Image.open(D+f'refs/pmd_portrait/0648_{RM[o]}.png').convert('RGBA').resize((40*sc,40*sc),Image.NEAREST)
    B.paste(r,(x,y+th+10),r); d.text((x,y+th),'PMD '+RM[o],fill=(220,220,220))
    B.paste(prender.img(D+f'portrait/P_{o}.txt',1),(tw*cols+10+(k%2)*48,10+(k//2)*48))
B.save(out); print(out,B.size)
