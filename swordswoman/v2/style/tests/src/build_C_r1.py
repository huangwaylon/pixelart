# compose C_r1 char-map from hand-drawn row segments (abs y, abs x0, string); '.' does not overwrite
import sys
G=[['.']*64 for _ in range(64)]
def put(y,x0,s):
    for i,c in enumerate(s):
        if c!='.': G[y][x0+i]=c
BOW=[ # x0=16, y14..23, painted over the head
"...........KKK........KKKK..",
".....KKKK.KLLhK.....KKeeeeK.",
"....KeeeeKKHHhKKKKKKeeeEEEK.",
"....KeeEEEEEEEreErEEEEEEERK.",
"....KEEEEEEEEEreErEEEERRRK..",
"....KEEEERRRRRrRRrERRRRRK...",
"....KERRRRRRRrrrrrrKKKKK....",
"....KRRRRRRKKhhhhhh.........",
"....KRRRRKK.................",
".....KKKK...................",
]
HEAD=[ # x0=20, y18..37
"........KKKKKKK........",
"......KKHHHHHHHKK......",
"....KKHHHHHHHHHHHKK....",
"...KHHHHHHHHHHHHHHhK...",
"..KHHHHLLLLLLLLHHHhhK..",
".KHHLLLLLLLHHHHHHHHhhK.",
".KLLLLHHHHHHHHHHHHHhhK.",
"KHHHHHHHHHHHHHHHHHHHhhK",
"KHHHHHHHHhhhhhhhhhhhhhK",
"KHHHHHHHHhSSSSSSSSSSShK",
"KHHHHHHHHhssKKKsssKKShK",
"KHHHHHHHHhsKiWisssWiKhK",
"KHHHHHHHHhssiIisssIiShK",
"KHHHHHHHHhssIIIsssIIShK",
"KHHHHHHHHhssssssssssShK",
".KHHHHHHHhssssssssssShK",
".KhhHHHHHhssssssSsssShK",
"..KhhhhhhhsssssssssSShK",
"...KKKKKKKKsssssssSSKKK",
"........KKKKKKKKKKKKK..",
]
BODY=[ # x0=18, y38..61
".........KeeeEErssrEERRK......",
"........KeeERrEErrERRrRRK.....",
"........KEEERrEEEEERRrRRK.....",
".......KEEERRrEEEEERRrRRRK....",
".......KEEERRrEEEEERRrRRRK....",
"......KEEEERRrrrrrrrrrRRRRK...",
"......KEEEERRrdddddhhrRRRRK...",
".....KEEEEERRrdddddhhrRRRRRK..",
".....KEEEEERRrdddddhhrRRRRRK..",
"....KEEEEEERRrRRRRRRRrrrrrrK..",
"....KrrrrrrrEEEEEEERRKKKsSKK..",
"...KsSKKKKKKKEEEEEERRRRKsSK...",
"...KsSKEEEEEEEEEEEERRRRRKK....",
"..KkkkkKEEEEEEEEEEERRRRRRK....",
"..KkkkKKKKKKKKKKKKKKKKKKKK....",
"..KWnK.....KSSSK.KSSK.........",
"..KWnK.....KssSK.KsSK.........",
".KWnK......KssSK.KsSK.........",
".KWnK......KssSK.KsSK.........",
"KWnK.......KssSK.KsSK.........",
"KWnK.......KssSK.KsSK.........",
"...........KddhK.KdhK.........",
"...........KdddhKKddhK........",
"............KKKKK.KKKK........",
]
for i,s in enumerate(HEAD): put(18+i,20,s)
for i,s in enumerate(BOW): put(14+i,16,s)
for i,s in enumerate(BODY): put(38+i,18,s)
put(59,17,"KWnK"); put(60,17,"KWK"); put(61,17,"KK")
for n,(rows,w) in {'BOW':(BOW,28),'HEAD':(HEAD,23),'BODY':(BODY,30)}.items():
    for i,s in enumerate(rows):
        if len(s)!=w: print('len',n,i,len(s))
dx=int(sys.argv[2]) if len(sys.argv)>2 else 0
out=[''.join(r) for r in G]
if dx: out=[(r[-dx:]+r[:-dx]) if dx>0 else (r[-dx:]+r[:-dx]) for r in out]
open(sys.argv[1],'w').write('\n'.join(out)+'\n')
