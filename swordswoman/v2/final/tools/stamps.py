"""stamps.py : expression head stamps from final/<V>.txt using FACE specs (final/work/face_spec.json)
face_spec: {V: {"eyes": [[lash_row, c0, c1, outer_side('L'|'R')], ...], "mouth": [row, col], "cheeks": [[row,col],...], "head": [r0,r1,c0,c1]}}
writes heads/<V>_<expr>.txt ('; origin X Y' + '; view V' + rows, '.' transparent) and heads/sheet.png"""
import sys, json, copy
sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/final/tools'); import fid, ds
F=fid.F; SPEC=json.load(open(F+'work/face_spec.json'))
EX=["neutral","cheerful","determined","shout","effort","joy","surprised","pain","blink_half","blink_closed","embarrassed"]
def expr(g,sp,e):
    g=[list(r) for r in g]; S='s'
    def put(r,c,ch): g[r][c]=ch
    eyes=sp.get('eyes',[]); M=sp.get('mouth'); ck=sp.get('cheeks',[])
    def clear(l,c0,c1,rows=(0,1,2)):
        for dr in rows:
            for c in range(c0,c1+1): put(l+dr,c,S)
    eh=sp.get('eh',3); A=tuple(range(eh)); m=eh-3  # m = extra eye rows below the 3-row base (r2: 5-row eyes)
    for (l,c0,c1,o) in eyes:
        inner=c1 if o=='L' else c0; outer=c0 if o=='L' else c1
        if e=='blink_half':
            clear(l,c0,c1,tuple(range(2+m))); [put(l+1+m,c,'K') for c in range(c0,c1+1)]
        elif e=='blink_closed':
            clear(l,c0,c1,A); [put(l+2+m,c,'K') for c in range(c0,c1+1)]; put(l+1+m,outer,'K')
        elif e=='joy':
            clear(l,c0,c1,A); [put(l+1+m,c,'K') for c in range(c0,c1+1) if c not in (c0,c1)] if c1-c0>=2 else put(l+1+m,c0,'K'); put(l+2+m,c0,'K'); put(l+2+m,c1,'K')
        elif e in ('effort','pain'):
            l2=l+m//2; clear(l,c0,c1,A); [put(l2+1,c,'K') for c in range(c0,c1+1)]; put(l2,inner,'K') if e=='effort' else put(l2+2,inner,'K'); put(l2+2 if e=='effort' else l2,inner,'K')
        elif e in ('determined','shout'):
            put(l,inner,'K'); 
            for c in range(c0,c1+1):
                if g[l+1][c]=='W': put(l+1,c,'h')
            put(l-1,inner,'K') if g[l-1][inner] in 'sS' else None
        elif e=='surprised':
            for c in range(c0,c1+1):
                if g[l][c]=='K' and g[l-1][c] in 'sS': put(l-1,c,'K'); put(l,c,'W' if c==(c0 if o=='R' else c0) else 'h')
    if M:
        r,c=M
        if e=='cheerful': put(r,c,'m'); put(r,c+1,'m')
        elif e in ('shout',): put(r,c,'K'); put(r,c+1,'K'); put(r+1,c,'K'); put(r+1,c+1,'m')
        elif e=='joy': put(r,c,'K'); put(r,c+1,'K'); put(r+1,c,'m')
        elif e=='effort': put(r,c,'K'); put(r,c+1,'K')
        elif e=='surprised': put(r,c,'K'); put(r+1,c,'K')
        elif e=='pain': put(r,c,'K'); put(r,c+1,'m'); put(r+1,c+1,'K')
        elif e=='determined': put(r,c,'m'); put(r,c+1,'m')
        elif e=='embarrassed': put(r,c,'S'); put(r,c+1,'m')
    if e in ('cheerful','joy','effort','embarrassed'):
        for (r,c) in ck: put(r,c,'k')
        if e=='embarrassed':
            for (r,c) in ck: put(r,c+1 if g[r][c+1] in 'sS' else c,'k')
    return g
def main():
    import os; os.makedirs(F+'heads',exist_ok=True)
    from PIL import Image
    sheet=Image.new('RGB',(len(EX)*66,len(SPEC)*66+4),(150,150,160)); vi=0
    for v,sp in SPEC.items():
        g=fid.load(F+f'{v}.txt').tolist(); r0,r1,c0,c1=sp['head']
        for j,e in enumerate(EX):
            h=expr(copy.deepcopy(g),sp,e) if v!='N' else g
            rows=[''.join(h[r][c0:c1+1]) for r in range(r0,r1+1)]
            open(F+f'heads/{v}_{e}.txt','w').write(f'; origin {c0} {r0}\n; view {v}\n'+'\n'.join(rows)+'\n')
            im=ds.render([list(r.ljust(64,'.')) for r in [''.join(x) for x in h]]+[['.']*64]*(64-len(h)),1).crop((c0,r0,c1+1,r1+1))
            im=im.resize((im.width*3,im.height*3),0); sheet.paste(im,(j*66,vi*66),im)
        vi+=1
    sheet.save(F+'heads/sheet.png'); print('stamps ok')
if __name__=='__main__': main()
