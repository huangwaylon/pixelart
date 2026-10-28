import re,sys
def rle(s):
    out=''
    for t in s.split():
        c=t[0]; n=int(t[1:]) if len(t)>1 else 1
        out+=c*n
    return out
def load_rle(path):
    rows=[]
    for l in open(path):
        l=l.rstrip('\n')
        if not l.strip() or l.startswith('#'): continue
        r=rle(l); rows.append(r)
    return rows
if __name__=='__main__':
    rows=load_rle(sys.argv[1])
    bad=[(i,len(r)) for i,r in enumerate(rows) if len(r)!=40]
    print('rows',len(rows),'bad',bad)
    open(sys.argv[2],'w').write('\n'.join(rows)+'\n')
