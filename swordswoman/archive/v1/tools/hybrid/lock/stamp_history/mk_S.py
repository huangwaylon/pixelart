F="hHh"
def f1(row): return ".K"+F+row+F+"K."
def f2(row): return "..K"+"hh"+row+"hh"+"K.."
rows=[
"....KKK...KKKKKK...KKK....",
"..."+"KCRRK"+"."+"K"+"hHJJHh"+"K"+"."+"KCRRK"+"...",
"..."+"KCRRRK"+"hHHHHhhh"+"KCRRRK"+"...",
"..."+"K"+"RRRRr"+"K"+"h"+"KKKK"+"h"+"K"+"rRRRR"+"K"+"...",
"..."+"K"+"RRRRrrv"+"CRRr"+"vrrRRRR"+"K"+"...",
"...."+"K"+"RRrrrv"+"RRrr"+"vrrrRR"+"K"+"....",
"....."+"KK"+"rvv"+"v"+"KrrK"+"v"+"vvr"+"KK"+".....",
"....."+"K"+"h"+"KKKK"+"hKKh"+"KKKK"+"h"+"K"+".....",
"...."+"K"+"hhHHhhhhhhhhHHhh"+"K"+"....",
"..."+"K"+"hHJJJJHHHhHHHHHhhh"+"K"+"...",
".."+"K"+"hJJHHHHHhHHHHHHHhhhh"+"K"+"..",
".."+"K"+"hHHHHHHhHHHHhhhHhhhh"+"K"+"..",
".K"+"hhHHHHHhHHHHhhHHhhhhhp"+"K.",
".K"+"hHHHHHhHHHHhhHHhhhhhhp"+"K.",
".K"+"hHHHHhHHHHhhHHHhhhhhhh"+"K.",
".K"+"hHHHhHHHHhhHHHhhhHhhhh"+"K.",
".K"+"hHHhHHHHhhHHHhhhHHhhhp"+"K.",
".K"+"hHhHHHHhhHHHhhhHHhhhhp"+"K.",
".K"+"hhHHHHhhHHHhhhHHHhhhhh"+"K.",
f1("HHHHhhHHHhhHHHhh"),
f1("hHhmshHHhmshHhhh"),
f1("KhmsssmhmsssmhmK"),
f1("sKKKKssssssKKKKs"),
f2("s"+"ewee"+"ssssss"+"ewee"+"s"),
f2("S"+"eEEe"+"ssssss"+"eEEe"+"s"),
f2("s"+"eEEe"+"ssssss"+"eEEe"+"s"),
f2("p"+"sEEs"+"ssssss"+"sEEs"+"p"),
"...K"+"h"+"s"+"pp"+"ssss"+"mm"+"ssss"+"pp"+"s"+"h"+"K...",
"....K"+"mssssssssssssssm"+"K....",
"......K"+"mssssssssssm"+"K......",
"........KmssssssmK........",
"..........KKKKKK..........",
]
for i,r in enumerate(rows): assert len(r)==26,(i,len(r),r)
open('head_S.pix','w').write("# canonical sprite-scale head, facing S (hand-typed). 26 x %d; chin = last row; centre between cols 12/13\nsize: 26 %d\ngrid:\n"%(len(rows),len(rows))+"\n".join(rows)+"\n")
