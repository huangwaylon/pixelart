def R(*segs, w=26):
    r=['.']*w
    for c,s in segs:
        if c+len(s)>w: print("OVERFLOW",c,s,c+len(s)-w)
        for i,ch in enumerate(s):
            if c+i<w: r[c+i]=ch
    return ''.join(r)
def line(rows,x0,y0,x1,y1,ch,only='h'):
    n=max(abs(x1-x0),abs(y1-y0)) or 1
    for k in range(n+1):
        x=round(x0+(x1-x0)*k/n); y=round(y0+(y1-y0)*k/n)
        r=list(rows[y])
        if r[x] in only: r[x]=ch
        rows[y]=''.join(r)
def save(name,rows,desc,w=26):
    for i,r in enumerate(rows): assert len(r)==w,(i,len(r),r)
    open(name,'w').write("# canonical sprite-scale head, %s (hand-typed). %d x %d\nsize: %d %d\ngrid:\n"%(desc,w,len(rows),w,len(rows))+"\n".join(rows)+"\n")
