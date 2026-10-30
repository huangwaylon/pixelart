import bpy, numpy as np
ao = bpy.data.objects["rig"]; b = bpy.data.objects["body"]; me = b.data
names = [g.name for g in b.vertex_groups]
co = np.array([v.co for v in me.vertices]); m = np.zeros(len(me.polygons), int); me.attributes["mat"].data.foreach_get("value", m)
vm = np.full(len(co), -1)
for p in me.polygons: vm[list(p.vertices)] = m[p.index]
B = ao.data.bones
def H(n): return np.array(B[n].head_local)
for s in "L":
    P = [H("upper_arm."+s), H("forearm."+s), H("hand."+s), np.array(B["hand."+s].tail_local)]
    sel = vm == 3
    pts = co[sel]
    def proj(p):
        best = (1e9, None, None)
        for i in range(2):
            a, c = P[i], P[i+1]; ab = c - a; t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1.5 if i == 1 else 1)
            q = a + t[:, None] * ab; d = np.linalg.norm(p - q, axis=1)
            yield d, t + i
    ds = list(proj(pts)); D = np.minimum(ds[0][0], ds[1][0]); T = np.where(ds[0][0] < ds[1][0], ds[0][1], ds[1][1])
    side = pts[:, 0] < 0 if s == "L" else pts[:, 0] > 0
    for lo in np.arange(0, 2.6, 0.25):
        k = side & (T >= lo) & (T < lo + 0.25)
        if k.sum(): print("T", round(lo,2), k.sum(), "r pct50/90/max", np.percentile(D[k], [50, 90, 100]).round(3))
    hs = (vm == 2) & side & (co[:, 2] < 0.7) & (co[:, 2] > 0.5)
    print("hand verts", hs.sum(), co[hs].min(0).round(3), co[hs].max(0).round(3))
