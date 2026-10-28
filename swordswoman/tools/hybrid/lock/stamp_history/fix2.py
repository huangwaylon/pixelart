import sys; sys.path.insert(0,'/tmp'); from stamplib import *
def load(p): return open(p).read().split('grid:\n')[1].strip('\n').split('\n')
def desc(p): return open(p).read().split('\n')[0].replace('# canonical sprite-scale head, ','').split(' (hand')[0]
def desep(rows,y0,y1,x0,x1):
    for y in range(y0,y1):
        r=list(rows[y])
        for x in range(max(x0,1),min(x1,len(r)-1)):
            if r[x]=='h' and r[x-1] in 'HJ' and r[x+1] in 'HJ': r[x]='H'
        rows[y]=''.join(r)
def derim(rows):
    first=next(i for i,r in enumerate(rows) if 's' in r)
    for y in range(first): rows[y]=rows[y].replace('p','h')
    return rows
# ---- S
p='head_S.pix'; rows=load(p)
new={13:"..K"+"hJJHHHHHHHHHHHHHHhhh"+"K..",
14:".K"+"hhHHHHHHHHhHHHHHHHhhhh"+"K.",15:".K"+"hHHHHHHHHhHHHHHHHHhhhh"+"K.",
16:".K"+"hHHHHHHHhHHHHHHHHHhhhh"+"K.",17:".K"+"hHHHHHHhHHHHHHHHhHhhhh"+"K.",
18:".K"+"hHHHHHhHHHHHHHHhHHhhhh"+"K.",19:".K"+"hHHHHhHHHHHHHHhHHHhhhh"+"K.",
20:".K"+"hhHHhHHHHHHHHhHHHHhhhh"+"K.",21:".K"+"hHhHHHHHHHHhHHHHHHhhHh"+"K.",
27:"..Khh"+"s"+"sEEs"+"ssssss"+"sEEs"+"s"+"hhK..",
28:"..Khh"+"s"+"pp"+"s"*10+"pp"+"s"+"hhK..",
29:"...Kh"+"ssssssss"+"m"+"sssssss"+"hK..."}
for k,v in new.items(): rows[k]=v
save(p,derim(rows),'facing S')
# ---- SE
p='head_SE.pix'; rows=load(p)
desep(rows,12,22,4,22)
line(rows,12,11,7,21,'h',only='H'); line(rows,17,12,14,21,'h',only='H')
old=rows[:]
rows[27]=old[28].replace('p','s'); rows[28]=old[29]; rows[29]=old[30].replace('mm','ms'); rows[30]=old[30].replace('mm','ss')
save(p,derim(rows),'facing SE three-quarter')
# ---- E
p='head_E.pix'; rows=load(p)
desep(rows,10,23,9,25)
line(rows,16,11,12,21,'h',only='H'); line(rows,21,12,19,21,'h',only='H')
old=rows[:]
rows[27]=old[28].replace('p','s'); rows[28]=old[29]; rows[29]=old[29].replace('p','s')
line(rows,14,22,15,29,'H',only='h')
save(p,derim(rows),'facing E profile')
# ---- NE: rim off
p='head_NE.pix'; rows=load(p); save(p,derim(rows),'facing NE back three-quarter')
