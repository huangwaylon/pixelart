import sys
p=sys.argv[1]; g=[list(l.rstrip('\n')) for l in open(p)]
def put(y,x,s):
    for i,c in enumerate(s):
        if c!=' ': g[y][x+i]=c
def clear(y,x0,x1):
    for x in range(x0,x1+1): g[y][x]='.'
# ---- collar / chin / neck rows 40-44
put(41,33,"KKKKKKKKKKKSSSSKK")
put(42,34,"KErEEEEEErSSrRRrK")
put(43,34,"KKERrEEEEEErSrRRreKK".replace('e','E'))
# ---- left sleeve bottom, hand, guard, blade
for y in range(55,58): clear(y,12,29)
for y in range(58,79): clear(y,12,27)
put(55,23,"Krrrrrrr")
put(56,22,"Krrrrrrrr")
put(57,22,"KKKKKKKKK")
put(58,23,"KsssK")
put(59,23,"KssSK")
put(60,23,"KssSK")
put(61,21,"KKKKKKK")
put(62,20,"KkkkkkkkK")
put(63,20,"KKkkkkkKK")
put(64,21,"KKKKKKK")
for y in range(65,76):
    xl=22-(y-65)//2; put(y,xl,"KWnK")
put(76,17,"KWK"); put(77,16,"KK")
open(p,'w').write('\n'.join(''.join(r) for r in g)+'\n')
g=[list(l.rstrip('\n')) for l in open(p)]
def row(y,x,s):
    for i,c in enumerate(s): g[y][x+i]=c
# ---- left bow loop + hair top band (rows 11-25, x 24-46)
row(11,32,"KhhKKKK")
row(12,30,"KKKKKeeeer")
row(13,28,"KKeeeeEEEEEr")
row(14,27,"KeeEEEEEEEKK")
row(15,26,"KEEEEEEEEKKhhhhhhh")
row(16,25,"KEEERRRKKhhHHLLLLLLLHHHHH")
row(17,24,"KRRRRRRKKhhLLLLLLHHHHHH")
row(18,24,"KKKKKKKhhLLLLLHHHH")
row(19,24,"KhhhhhhhLLLLHHHH")
row(20,24,"KHHHHLLLLHHH")
row(21,24,"KHHHLLLHHH")
row(22,24,"KHHHLLLHHH")
row(23,23,"KHHHHLLHHHH")
row(24,23,"KHHHHLLHHHHHHHhhhhhhhhhhhhhhhhhhhK")
row(25,23,"KHHHHLLHHHHHHHh")
# ---- chin / neck / collar
row(37,53,"hK")
row(38,50,"SKKK")
row(41,43,"KSSSSKK")
row(42,43,"rSSrRRrK")
row(43,32,"KeERrEEEEEEErrRRRrEK")
row(44,46,"R")
for y in range(42,49):
    for x in range(48,56):
        if g[y][x]=='e': g[y][x]='E'
# ---- shadow band under obi
for x in range(31,46):
    if g[55][x]=='E': g[55][x]='R'
row(43,51,"K..")
for y in range(71,78):
    for x in range(32,52): g[y][x]='.'
row(71,35,"KKKKK"); row(71,43,"KKKKK")
for x0,w in ((34,7),(42,7)): row(72,x0,"K"+"d"*(w-3)+"hK")
row(73,33,"KdddddhK"); row(73,42,"KdddddhK")
row(74,33,"KdddddhK"); row(74,42,"KddddddhK")
row(75,33,"KdddddhK"); row(75,42,"KddddddhK")
row(76,33,"KhhhhhhK"); row(76,42,"KhhhhhhhK")
row(77,34,"KKKKKK");  row(77,43,"KKKKKKK")
row(64,35,"KSSSK"); row(64,43,"KSSSK")
for y in (57,58,59): row(y,54,"KssSK")
g[10][40]='E'
for x in range(28,58):
    if g[62][x]=='E': g[62][x]='R'
# centre horizontally
xs=[x for r in g for x,c in enumerate(r) if c!='.']; sh=(80-1-max(xs)-min(xs))//2
g=[['.']*sh+r[:80-sh] if sh>=0 else r[-sh:]+['.']*(-sh) for r in g]
print('shift',sh,min(xs),max(xs))
open(p,'w').write('\n'.join(''.join(r) for r in g)+'\n')
