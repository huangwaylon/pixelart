import bpy, numpy as np, json
b = bpy.data.objects["body"]; me = b.data; names=[g.name for g in b.vertex_groups]
co = np.array([v.co for v in me.vertices])
fm = np.zeros(len(me.polygons), int); me.attributes["mat"].data.foreach_get("value", fm)
vm = np.full(len(co), -1)
for p in me.polygons: vm[list(p.vertices)] = fm[p.index]
for P in ([0.09408, 0.16209, 1.26129], [-0.09329, 0.16006, 1.26129]):
    d = np.linalg.norm(co - P, axis=1); o = np.argsort(d)[:5]
    for i in o: v = me.vertices[i]; print("EYE", i, round(d[i]*1000,1), vm[i], co[i].round(3), [ (names[g.group], round(g.weight,2)) for g in v.groups])
    sk = vm == 2; j = np.where(sk)[0][np.argmin(d[sk])]; print("EYE skin nearest", j, round(d[j]*1000,1), co[j].round(3))
