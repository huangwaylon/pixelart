import sys
for p in sys.argv[1:]:
    g=[l.rstrip('\n') for l in open(p) if l.strip()]
    h,w=len(g),len(g[0]); out=[]
    for y in range(h):
        for x in range(w):
            c=g[y][x]
            if c in '.K': continue
            nb=[g[y+dy][x+dx] for dy in(-1,0,1) for dx in(-1,0,1) if (dy or dx) and 0<=y+dy<h and 0<=x+dx<w]
            if c not in nb: out.append(f"{c}@{x},{y}")
            if '.' in [g[y+dy][x+dx] for dy,dx in((0,1),(0,-1),(1,0),(-1,0)) if 0<=y+dy<h and 0<=x+dx<w]: out.append(f"EDGE!{c}@{x},{y}")
    # 2x2 K blocks
    for y in range(h-1):
        for x in range(w-1):
            if g[y][x]==g[y][x+1]==g[y+1][x]==g[y+1][x+1]=='K': out.append(f"KK2x2@{x},{y}")
    print(p.split('/')[-1], ' '.join(out))
