import math, sys, numpy as np
W=H=80
M=np.full((H,W),'',dtype=object)
YY,XX=np.mgrid[0:H,0:W]; PX=XX+.5; PY=YY+.5
def inpoly(P):
    c=np.zeros((H,W),bool); n=len(P)
    for i in range(n):
        x1,y1=P[i]; x2,y2=P[(i+1)%n]
        if y1==y2: continue
        cond=((y1>PY)!=(y2>PY)) & (PX < (x2-x1)*(PY-y1)/(y2-y1)+x1)
        c^=cond
    return c
def poly(P,m,where=None):
    k=inpoly(P)
    if where is not None: k&=where
    M[k]=m
def ell(cx,cy,rx,ry,m,p=2,where=None):
    k=(np.abs((PX-cx)/rx)**p+np.abs((PY-cy)/ry)**p)<=1
    if where is not None: k&=where
    M[k]=m
def seg(x0,y0,x1,y1,w,m):
    dx,dy=x1-x0,y1-y0; L=math.hypot(dx,dy); ux,uy=dx/L,dy/L
    t=(PX-x0)*ux+(PY-y0)*uy; d=np.abs(-(PX-x0)*uy+(PY-y0)*ux)
    M[(t>=0)&(t<=L)&(d<=w)]=m
def mat(*ms): return np.isin(M,ms)

# ---------- far arm (picture-right), extended forward-out, open hand
poly([(51,44),(56,44.5),(60,48),(63,51.5),(62.5,55.5),(59,56),(57,58.5),(54,57),(53,52)],'sleeveF')
ell(64.2,53.4,2.6,2.4,'handF',2.2)
poly([(64.6,51.2),(67.6,50.6),(67.8,52.2),(65.4,53.2)],'handF')   # fingers out
# ---------- legs + boots (near = picture-left, back leg braced; far = picture-right, stepped forward, 2 px higher)
poly([(33,62),(38,62),(36,73),(31,73)],'legN')
poly([(45.4,62),(50.4,62),(53.4,71),(48.4,71)],'legF')
poly([(30,72.4),(36.4,72.4),(36.8,74.4),(39.6,75.2),(39.8,77),(29,77),(29.2,75)],'bootN')
poly([(48,70.4),(54,70.4),(54.4,72.2),(57.2,73.2),(57.2,75),(47.8,75),(47.8,73)],'bootF')
# ---------- dress (kimono, flared, hem lifted on the forward side)
poly([(37,42.5),(51,42.5),(54,48),(55.8,55),(57.8,62.6),(52,63.6),(40,64),(30.8,63.2),(32.4,55),(34.4,48)],'dress')
obi=(PY>=50)&(PY<54.2); M[obi&mat('dress')]='obi'
# ---------- near arm (picture-right hand of hers = picture-left), raised ready guard
poly([(37.6,43),(33.4,44.6),(29,47.4),(25.6,49.8),(24.6,53.4),(26.4,59.6),(31.4,60.4),(34.6,56),(36.4,50)],'sleeveN')
# katana: grip through the hand, blade up-left (raised guard)
hx,hy=23.4,51.4; ux,uy=-0.48,-0.877
seg(hx-ux*5.5,hy-uy*5.5,hx+ux*2.6,hy+uy*2.6,1.25,'hilt')
seg(hx+ux*4.2,hy+uy*4.2,hx+ux*26,hy+uy*26,1.15,'blade')
ell(hx+ux*3.4,hy+uy*3.4,2.3,1.3,'guard',2)
ell(hx,hy,2.7,2.5,'handN',2.2)
# ---------- hair back mass, face, bangs
skull=(np.abs((PX-40.6)/16.6)**2.0+np.abs((PY-27.2)/15.8)**2.0)<=1
M[skull]='hair'
poly([(24.2,27),(23.0,32),(22.6,37),(23.4,40),(24.6,42.4),(27.4,40.2),(29.2,43.4),(31.8,40.8),(34.4,43.6),(36.6,41),(38.6,42.4),(40.6,38),(40.6,28)],'hair')  # bob ends, tapered points
face=inpoly([(40.4,28.6),(55.4,28.6),(55.4,35.6),(54.6,38.4),(52.8,40.6),(50.6,42.6),(47.4,42.6),(44.6,41),(42,38.6),(40.4,35)])
M[face]='face'
# fringe tips over the face (3-4 shallow tapered points)
poly([(40,27),(40.6,31),(42.4,29),(44.6,30.9),(46.8,29),(49,30.9),(51.2,29),(53.4,30.6),(55,28.8),(56,29.4),(56,27)],'hair')
# far-side lock (narrow), ends in a point at the jaw
poly([(54.6,24),(57.4,24.6),(57.4,32),(56.8,37.4),(55.6,41.8),(54.8,37),(55,30)],'hair')
poly([(45.4,41.4),(49.6,41.4),(49.4,44),(45.8,44)],'neck')
# bun + bow
ell(36.6,11.8,4.4,4.6,'bun',2.2)
poly([(43.2,10.6),(46.4,7.8),(50.6,7.0),(54.6,7.4),(56.4,9.4),(55.8,13.4),(52.6,15.4),(47.4,14.6),(43.2,13.8)],'bow')
poly([(40,12.8),(34,13.0),(28,14.6),(23,17.6),(19.8,22.2),(19,27.4),(21.4,29),(24.2,26.6),(25.6,22.4),(28.6,19.2),(33,17.2),(40,16.4)],'bow')
poly([(39.4,10.6),(43.8,10.4),(44.2,15.4),(39.6,15.8)],'knot')
np.save('/tmp/B_r2_mat.npy',M)
