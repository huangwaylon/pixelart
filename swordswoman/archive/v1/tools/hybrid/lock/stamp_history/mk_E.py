def R(*segs, w=26):
    """segs: (col, string) placements on a '.' row"""
    r=['.']*w
    for c,s in segs:
        if c+len(s)>w: print("OVERFLOW",c,s,c+len(s)-w)
        for i,ch in enumerate(s):
            if c+i<w: r[c+i]=ch
    return ''.join(r)
rows=[
R((6,"KKK"),(12,"KKK")),
R((2,"KKKK"),(5,"KCRRK"),(11,"KCRRK")),
R((1,"KhHJhK"),(5,"KCRRRK"),(11,"KRRRRK")),
R((0,"KhHJJHhK"),(7,"RRRrKRRRrK")),
R((0,"KhHHHhhK"),(8,"RrvCRrvRK")),
R((0,"KhHhhhhhK"),(9,"vvRRrvvK")),
R((0,"KhhhhhhhhKKKrrKKKhK")),
R((0,"KhhhhhhhhhhhKKhhhHhKK")),
R((1,"KhhhhhhhhhhhhhHHHJJHhK")),
R((1,"KhhhhhhhhhhhhHHHJJHHHhK")),
R((2,"KhhhhhhhhhhHHHHHHHHHHhK")),
R((2,"KhhhhhhhhhHHHHHHHHHHHHhK")),
R((2,"KhhhhhhhHHHHHHhHHHHHHHhK")),
R((2,"KhhhhhhHHHHHHhHHHHHHHHhK")),
R((2,"KhhhhhhHHHHHhHHHHHHHHHHK")),
R((2,"KhhhhhHHHHHhHHHHHHHHHhHK")),
R((2,"KhhhhhHHHHhHHHHHHHHHhHHK")),
R((2,"KhhhhhHHHhHHHHHHHHHhHHHK")),
R((2,"KhhhhHHHhhHHHHHHHHhHHHhK")),
R((3,"KhhhhHHhhhhHHHHHHhHHHhK")),
R((3,"KhhhhhhhhhhhHHHhHHhHhmK")),
R((3,"KhhhhhhKKhhhHhhmsssmhsK")),
R((3,"KhhhhhKmsKhhHhsKKKKssK")),
R((4,"KhhhhKsmKhhHhsseweesK")),
R((4,"KhhhhKmsKhhhhSseEEesK")),
R((4,"KhhhhhKKhhhhhsseEEesK")),
R((5,"KhhhhhhhhhhhsspsEEssK")),
R((5,"KhhhhhhhhhhsspppssssK")),
R((5,"KKhhhhhhhhKmsssssssmK")),
R((8,"KKhhhhhhKmssssssmK")),
R((10,"KhhhhhKmssssssK")),
R((11,"KKKKKKmssssK")),
R((17,"KKKKKK")),
]
for i,r in enumerate(rows): assert len(r)==26,(i,len(r),r)
open('head_E.pix','w').write("# canonical sprite-scale head, facing E profile (hand-typed). 26 x %d\nsize: 26 %d\ngrid:\n"%(len(rows),len(rows))+"\n".join(rows)+"\n")
# paint-over: back-of-head strands pulled up toward the bun (hair_1 over hair_0 only)
def line(rows,x0,y0,x1,y1,ch,only='h'):
    n=max(abs(x1-x0),abs(y1-y0))
    for k in range(n+1):
        x=round(x0+(x1-x0)*k/n); y=round(y0+(y1-y0)*k/n)
        r=list(rows[y])
        if r[x] in only: r[x]=ch
        rows[y]=''.join(r)
for (a,b,c,d) in [(12,19,5,8),(10,23,3,12),(13,13,8,6),(8,26,4,19)]:
    line(rows,a,b,c,d,'H')
line(rows,11,20,6,10,'H')
open('head_E.pix','w').write("# canonical sprite-scale head, facing E profile (hand-typed). 26 x %d\nsize: 26 %d\ngrid:\n"%(len(rows),len(rows))+"\n".join(rows)+"\n")
