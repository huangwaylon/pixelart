"""fid.py MASTER.txt V  -> per-material IoU vs work/ds_V.txt, palette check, rows. (also importable)"""
import sys, json, numpy as np
F='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/final/'
PAL=json.load(open(F+'palette.json'))['colors']
def load(p):
    rows=[l.rstrip('\n') for l in open(p) if l.strip() and not l.startswith(';')]
    return np.array([list(r.ljust(64,'.')[:64]) for r in rows[:64]])
def mats(g):
    M=np.full(g.shape,'',dtype='<U4'); rows=np.arange(64)[:,None]*np.ones((1,64))
    hair=np.isin(g,list('hHgL')); M[hair&(rows<50)]='hair'; M[hair&(rows>=50)]='boot'
    M[np.isin(g,list('sSmk'))]='skin'; M[np.isin(g,list('eER'))]='red'; M[np.isin(g,list('QOo'))]='obi'
    M[g=='W']='eyeW'; M[g=='K']='K'; return M
def fid(m,d):
    A,B=mats(m),mats(d); ok=(A!='K')&(B!='K'); r={}
    for k in ['hair','red','skin','obi','boot']:
        a=(A==k)&ok; b=(B==k)&ok; u=(a|b).sum(); r[k]=round((a&b).sum()/u,3) if u else 1.0
    sil=lambda g:(g!='.'); r['sil']=round((sil(m)&sil(d)).sum()/(sil(m)|sil(d)).sum(),3)
    return r
def info(g):
    bad=sorted(set(g.flatten())-set(PAL)-{'.'}); ys=np.where((g!='.').any(1))[0]
    return dict(bad=bad,top=int(ys.min()),sole=int(ys.max()))
if __name__=='__main__':
    m=load(sys.argv[1]); d=load(F+f'work/ds_{sys.argv[2]}.txt'); print(fid(m,d),info(m))
