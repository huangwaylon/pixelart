# m3.py PARTS_DIR : 2D-equivalent front measures from rigid parts (same definitions as design front measurements)
import sys, os, json, numpy as np, trimesh
d=sys.argv[1]
def load(n):
    s=trimesh.load(os.path.join(d,n+".glb")); return s.to_geometry() if hasattr(s,"to_geometry") else s
M={n:load(n) for n in ["head","torso","skirt","arm_L","arm_R","leg_L","leg_R","bun","bow"] if os.path.exists(os.path.join(d,n+".glb"))}
def col(m): return m.visual.vertex_colors[:,:3].astype(int)
SKIN=np.array((239,179,138))
h=M["head"]; hv=h.vertices; FEET=-1.0
crown=hv[:,1].max(); hc=col(h); sk=np.all(np.abs(hc-SKIN)<40,axis=1)&(np.abs(hv[:,0])<0.15*np.ptp(hv[:,0]))&(hv[:,2]>np.median(hv[:,2]))
chin=hv[sk,1].min(); headH=crown-chin; headW=np.ptp(hv[:,0])
top_all=max(M[n].vertices[:,1].max() for n in M if n!="bow")
tv=M["torso"].vertices; ty0,ty1=tv[:,1].min(),tv[:,1].max()
# outer shoulder: x-extent of torso+arms in band just below torso top (8% headH)
band=lambda v,lo,hi: v[(v[:,1]>=lo)&(v[:,1]<=hi)]
yb=min(M[n].vertices[:,1].max() for n in ['arm_L','arm_R'])
pts=np.vstack([band(M[n].vertices,yb-0.06*headH,yb) for n in ["torso","arm_L","arm_R"]])
sh=np.ptp(pts[:,0])
# waist: min torso width over lower 45% of torso
ws=[np.ptp(band(tv,y,y+0.01)[:,0]) for y in np.linspace(ty0+0.02,ty0+0.45*(ty1-ty0),20) if len(band(tv,y,y+0.01))]
waist=min(ws)
sv=M["skirt"].vertices; hem=sv[:,1].min(); hemw=np.ptp(band(sv,hem,hem+0.05*headH)[:,0])
EYE=np.array((23,55,92)); ev=np.all(np.abs(hc-EYE)<30,axis=1); eye=(crown-hv[ev,1].mean())/headH if ev.any() else -1
fing=min(M[n].vertices[:,1].min() for n in ['arm_L','arm_R'])
r=dict(eye=eye, finger=(fing-FEET)/(crown-FEET), heads=(crown-FEET)/headH, sh=sh/headW, waist=waist/headW, hem=hemw/headW, legs=(hem-FEET)/(crown-FEET), neck=(chin-ty1)/(crown-FEET), headW_over_H=headW/headH, bun_above=(top_all-crown)/headH)
print(json.dumps({k:round(float(v),3) for k,v in r.items()}))
