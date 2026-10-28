import os
H=os.path.dirname(os.path.abspath(__file__))+'/..'
src=open(H+'/e/head_neutral.txt').read().split('\n')
meta=[l for l in src if l.startswith(';')]; R=[l for l in src if l and not l.startswith(';')]
def put(rows,y,x,s): r=rows[y]; rows[y]=r[:x]+s+r[x+len(s):]
def write(name,rows,pivot):
    assert all(len(r)==len(rows[0]) for r in rows), name
    m=[f'; pivot {pivot[0]} {pivot[1]}']+[l for l in meta if not l.startswith('; pivot')]
    open(f'{H}/e/head_{name}.txt','w').write('\n'.join(m+rows)+'\n')
L=R[:]
L[10]='#hHHHHHHHHHHHHHHHHHh#.'
L[11]='#hHHHHHHHHHHHHHH2332#.'
L[12]='#hhHHHHHHHHHHHh2###2#.'
L[13]='.#hhHHHHHHHHHHh22wi2#.'
L[14]='.#hhHHHHHHHHHHh22iI2#.'
L[15]='..#hhHHHHHHHHHh22II22#'
L[16]='..#hhHHHHHHHHHh22221#.'
L[17]='...#hhhHHHHHHHh21###..'
write('lean',L,(12,17))
U=R[:]
put(U,9,17,'33'); put(U,10,17,'22')
put(U,12,17,'wI'); put(U,13,17,'II'); put(U,14,17,'ww')
put(U,15,18,'1'); put(U,16,18,'2'); put(U,17,16,'2')
write('lookup',U,(13,18))
