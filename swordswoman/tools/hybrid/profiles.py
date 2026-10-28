"""Row-width silhouette profiles normalised to figure height H (sole=0, top=1)."""
import numpy as np, json
from PIL import Image
def mask_white(p, box):
    a=np.array(Image.open(p).convert("RGB")).astype(int)[box[1]:box[3],box[0]:box[2]]
    return (a.min(-1)<225)
def mask_alpha(p):
    return np.array(Image.open(p))[...,3]>128
def prof(m, name, center=None):
    rows=np.where(m.any(1))[0]; top,bot=rows[0],rows[-1]; H=bot-top
    out={}
    for f in np.arange(0.0,1.0001,0.05):
        r=int(round(bot-f*H)); cols=np.where(m[r])[0]
        out[round(float(f),2)]=round(float((cols[-1]-cols[0])/H),3) if len(cols) else 0
    return out
M={
 "turnaround_v6_front": mask_white("concept/chibi_turnaround_v6.png",(60,150,385,900)),
 "p3d_front": mask_alpha("hybrid/guide/measure/sil_p3d_front.png"),
 "r9_front": mask_alpha("hybrid/guide/measure/sil_proc_front.png"),
}
P={k:prof(v,k) for k,v in M.items()}
print("f   "+"  ".join(f"{k[:12]:>12}" for k in P))
for f in P["p3d_front"]:
    print(f"{f:.2f}"+"  ".join(f"{P[k][f]:>12}" for k in P))
json.dump(P,open("hybrid/guide/measure/width_profiles.json","w"),indent=1)
