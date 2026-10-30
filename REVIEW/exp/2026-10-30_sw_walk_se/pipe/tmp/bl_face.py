import bpy, numpy as np
b = bpy.data.objects["body"]; me = b.data
fm = np.zeros(len(me.polygons), int); me.attributes["mat"].data.foreach_get("value", fm)
fc = np.array([p.center for p in me.polygons])
sel = np.where((fm != 2) & (fc[:,2] > 1.1) & (fc[:,2] < 1.36))[0]
par = list(range(len(sel)))
def find(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
v2f = {}
for k, fi in enumerate(sel):
    for v in me.polygons[fi].vertices:
        if v in v2f: 
            ra, rb = find(k), find(v2f[v])
            if ra != rb: par[ra] = rb
        else: v2f[v] = k
lab = np.array([find(k) for k in range(len(sel))])
u, inv, cnt = np.unique(lab, return_inverse=True, return_counts=True)
for c in range(len(u)):
    m = inv == c; f = sel[m]
    if cnt[c] < 5000: print("COMP", cnt[c], "mats", np.bincount(fm[f], minlength=8), "ctr", fc[f].mean(0).round(3), "ymax", fc[f][:,1].max().round(3))
    else: print("COMP big", cnt[c])
