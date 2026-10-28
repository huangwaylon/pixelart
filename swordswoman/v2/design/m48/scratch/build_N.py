W=64
g=[['.']*W for _ in range(W)]
tpl=open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/design/m48/work/head_tpl.txt').read().split('\n')
r2=open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/design/m48/work/N_r2.txt').read().split('\n')
def put(r,c,s):
    for i,ch in enumerate(s):
        if ch!=' ': g[r][c+i]=ch
# head from template, add right shadow
for r in range(16,36):
    row=tpl[r]
    xs=[i for i,ch in enumerate(row) if ch!='.']
    if not xs: continue
    a,b=xs[0],xs[-1]
    for c in range(a,b+1): g[r][c]=row[c]
    # interior
    ins=[c for c in range(a,b+1) if row[c]=='H']
    if ins and r>=19:
        for c in ins[-2:]: g[r][c]='h'
    elif ins and r>=17:
        g[r][ins[-1]]='h'
for c in range(25,36):
    if g[34][c]=='H': g[34][c]='h'
# body from r2: rows 37..49 same, drop row 50, shift 51.. up
for r in range(37,50): put(r,0,r2[r])
put(36,0,'.......................#RRRRRRRRRRRRR#........................')
put(50,0,r2[51])
legs=r2[52:60]  # rows 52..59
seq=[legs[0],legs[1],legs[1],legs[2],legs[3],legs[4],legs[5],legs[6],legs[7]]
for i,s in enumerate(seq): put(51+i,0,s)
exec(open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/design/m48/scratch/bow.py').read())
out='\n'.join(''.join(x) for x in g)+'\n'
open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/design/m48/work/N_r3.txt','w').write(out)
print(out)
