D='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face/portrait/tools/'
def rd(f): return [list(r) for r in open(D+f).read().split('\n') if r]
def compose(dy=0):
    head=rd('base_head.txt'); bow=rd('base_bow.txt'); bust=rd('base_bust.txt')
    if dy<0: head=head[-dy:]+[['.']*40]*(-dy)
    if dy>0: head=[head[0][:]]*dy+head[:-dy]
    g=[r[:] for r in head]
    for y,r in enumerate(bow):
        y2=y+dy
        if 0<=y2<40:
            for x,c in enumerate(r):
                if c!='.': g[y2][x]=c
    if dy>0:
        for y in range(dy): g[y]=[c if c!='.' else g[y][x] for x,c in enumerate(bow[0])] if True else g[y]
    for y,r in enumerate(rd('base_neck.txt')):
        for x,ch in enumerate(r):
            if ch!='.' and g[34+y][x]=='.': g[34+y][x]=ch
    for y,r in enumerate(bust):
        for x,c in enumerate(r):
            if c!='.': g[37+y][x]=c
    return g
if __name__=='__main__':
    import sys; g=compose(int(sys.argv[2]) if len(sys.argv)>2 else 0)
    open(sys.argv[1],'w').write('\n'.join(''.join(r) for r in g)+'\n')
