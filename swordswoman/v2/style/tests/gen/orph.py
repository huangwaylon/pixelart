import sys
g=[l.rstrip('\n') for l in open(sys.argv[1])]; h=len(g); w=len(g[0])
for y in range(h):
    for x in range(w):
        c=g[y][x]
        if c in '.K': continue
        nb=[g[y+dy][x+dx] for dy in(-1,0,1) for dx in(-1,0,1) if (dy or dx) and 0<=y+dy<h and 0<=x+dx<w]
        if c not in nb: print(x,y,c)
