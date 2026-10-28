# derive SE variants from se/head_neutral.txt by row edits
import os
H=os.path.dirname(os.path.abspath(__file__))+'/..'
src=open(H+'/se/head_neutral.txt').read().split('\n')
meta=[l for l in src if l.startswith(';')]; R=[l for l in src if l and not l.startswith(';')]
def put(rows, y, x, s):
    r=rows[y]; rows[y]=r[:x]+s+r[x+len(s):]
def write(name, rows, pivot):
    m=[f'; pivot {pivot[0]} {pivot[1]}']+[l for l in meta if not l.startswith('; pivot')]
    assert all(len(r)==len(rows[0]) for r in rows), name
    open(f'{H}/se/head_{name}.txt','w').write('\n'.join(m+rows)+'\n')
# lean: face band rows 10-14 (cols 11-22) drop 1px, cheek row removed -> chin tucks in
L=R[:]
for y in range(14,9,-1): L[y]=R[y][:11]+R[y-1][11:]
put(L,10,11,'HHHHHHHHHHh#')
put(L,14,20,'2#.'); put(L,15,11,'22III22II#..')
write('lean',L,(12,17))
# lookup: brows up 1, irises up 1 (white below), mouth up 1, chin shadow off
U=R[:]
put(U,9,13,'33'); put(U,9,18,'33'); put(U,10,13,'22'); put(U,10,18,'22')
put(U,12,13,'wIi'); put(U,12,18,'wI'); put(U,13,13,'III'); put(U,13,18,'II'); put(U,14,13,'2ww'); put(U,14,18,'ww')
put(U,15,16,'1'); put(U,16,16,'2'); put(U,17,14,'2')
write('lookup',U,(13,18))
# blink: lash line closes to a curved line (outer corner tails down)
B=R[:]
put(B,11,13,'222'); put(B,11,18,'22'); put(B,12,13,'222'); put(B,12,18,'22')
put(B,13,13,'###'); put(B,13,18,'##'); put(B,14,12,'#222'); put(B,14,18,'22'); put(B,14,20,'2')
put(B,13,12,'2'); put(B,12,19,'2'); put(B,13,20,'#')
write('blink',B,(13,18))
