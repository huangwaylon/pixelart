"""procedural slash crescent drafts (to be hand-cleaned). facing E. writes draft/slash_*.txt + draft/slash_anchors.json"""
import sys, json, math, numpy as np
sys.path.insert(0,__file__.rsplit('/',1)[0]); import fxlib as F
def crescent(W,H,cx,cy,rx,ry,rot,a0,a1,wmax,tcut=0.0,wscale=1.0,gaps=(),bands=(1.6,0.62),rim=True,wmin=1.0):
    g=np.full((H,W),'.',dtype='<U1')
    N=600; ts=np.linspace(0,1,N); ang=np.radians(a0+(a1-a0)*ts); cr,sr=math.cos(math.radians(rot)),math.sin(math.radians(rot))
    def P(a,k=1.0):
        x,y=rx*k*np.cos(a),ry*k*np.sin(a); return cx+x*cr-y*sr, cy+x*sr+y*cr
    px,py=P(ang)
    for y in range(H):
        for x in range(W):
            X,Y=x+.5,y+.5
            # nearest param on path, signed inward distance via radial ratio
            dx,dy=X-cx,Y-cy; u= dx*cr+dy*sr; v=-dx*sr+dy*cr
            ad=math.degrees(math.atan2(v/ry,u/rx)); t=None
            for kk in (-360,0,360):
                tt=(ad+kk-a0)/(a1-a0)
                if 0<=tt<=1: t=tt
            if t is None: continue
            if t<tcut or any(a<=t<=b for a,b in gaps): continue
            # inward distance: compare to centre
            rr=math.hypot(u/rx,v/ry)
            ax=math.atan2(v/ry,u/rx); tip_x,tip_y=P(ax); dist=math.hypot(X-tip_x,Y-tip_y)*(1 if rr<1 else -1)
            # thickness profile: thin tail -> thick lead (t=1), with rounded lead cap over last 6%
            s=(t-tcut)/max(1e-6,1-tcut); w=wmin+(wmax-wmin)*math.sin(math.pi/2*min(1,s/0.78))**1.6
            if t>0.88: w=max(0.0,w*(1-((t-0.88)/0.12)**2)**0.5)
            w*=wscale
            if -0.5<=dist<w:
                if dist<bands[0] : c='W'
                elif dist<w*bands[1]+0.5 or w<3: c='p'
                else: c='n'
                if rim and w>=4.5 and dist>=w-1: c='b'
                g[y,x]=c
    return [''.join(r) for r in g]
specs={
 # name: canvas, ellipse, angles, wmax ; pivot = hand position on the smear frame
 'slash_h':   dict(W=48,H=24,cx=21,cy=8,rx=23,ry=10,rot=-8,a0=165,a1=-40,wmax=7),
 'slash_diag':dict(W=40,H=40,cx=14,cy=17,rx=22,ry=17,rot=20,a0=-130,a1=75,wmax=9),
 'slash_over':dict(W=40,H=44,cx=14,cy=22,rx=21,ry=21,rot=0,a0=-170,a1=70,wmax=9),
}
frames={'f0':dict(),'f1':dict(tcut=0.3,wscale=0.55,gaps=((0.62,0.68),)),'f2':dict(tcut=0.55,wscale=0.3,gaps=((0.66,0.72),(0.82,0.86)),rim=False)}
anch={}
for n,sp in specs.items():
    sp=dict(sp); sp['W']+=40; sp['H']+=40; sp['cx']+=20; sp['cy']+=20
    fr=[]
    for k,(fk,fv) in enumerate(frames.items()):
        kw=dict(sp); kw.update(fv); fr.append((crescent(**kw),40 if k==0 else 60))
    ys=[y for g,_ in fr for y,l in enumerate(g) if l.strip('.')]; xs=[x for g,_ in fr for l in g for x,c in enumerate(l) if c!='.']
    x0,y0,x1,y1=min(xs)-1,min(ys)-1,max(xs)+2,max(ys)+2
    fr=[([l[x0:x1] for l in g[y0:y1]],ms) for g,ms in fr]; sp['cx']-=x0; sp['cy']-=y0
    F.write(F.D+f'draft/{n}.txt',fr,f'{n} draft (procedural)')
    a0,a1=math.radians(sp['a0']),math.radians(sp['a1']); r=math.radians(sp['rot'])
    def P(a): x,y=sp['rx']*math.cos(a),sp['ry']*math.sin(a); return [round(sp['cx']+x*math.cos(r)-y*math.sin(r)),round(sp['cy']+x*math.sin(r)+y*math.cos(r))]
    anch[n]=dict(arc_centre=[sp['cx'],sp['cy']],arc_start=P(a0),arc_end=P(a1))
json.dump(anch,open(F.D+'draft/slash_anchors.json','w'),indent=1); print(anch)
