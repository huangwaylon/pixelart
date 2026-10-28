"""check3.py [glob prefix=''] : step-3 fidelity check over <V>.txt masters in final/ (or work/<V>_<suffix>.txt via arg)"""
import sys, numpy as np, json
sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/final/tools'); import fid
F=fid.F; V=['S','SE','E','NE','N']; suf=sys.argv[1] if len(sys.argv)>1 else None
RAMPS={'hair':'hHgL','skin':'sSmk','red':'eER','obi':'QOo'}
def head(g):
    hair=np.isin(g,list('hHgL')); red=np.isin(g,list('eER'))
    top=int(np.where(hair.any(1))[0].min())
    col=next(r for r in range(top+10,64) if red[r].sum()>=4)
    w=0
    for r in range(top,col):
        xs=np.where((g[r]!='.')&~red[r])[0]
        if len(xs): w=max(w,xs.max()-xs.min()+1)
    return top,col-top,w
out=[];use={}
for v in V:
    p=F+(f'work/{v}_{suf}.txt' if suf else f'{v}.txt')
    try: g=fid.load(p)
    except FileNotFoundError: continue
    d=fid.load(F+f'work/ds_{v}.txt'); r=fid.fid(g,d); i=fid.info(g); t,hh,hw=head(g)
    use[v]={m:''.join(c for c in ramp if (g==c).any()) for m,ramp in RAMPS.items()}
    major=[k for k in ['hair','red','skin','obi'] if r[k]<0.85]
    out.append(f"{v:3} IoU "+' '.join(f"{k}{r[k]:.2f}" for k in r)+f" | bad{i['bad']} sole{i['sole']} top{i['top']} head(top{t} h{hh} w{hw}) ramps {use[v]}"+(f" LOW:{major}" if major else ''))
print('\n'.join(out))
