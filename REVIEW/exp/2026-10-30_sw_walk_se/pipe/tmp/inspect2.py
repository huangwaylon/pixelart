import bpy, collections, numpy as np
b = bpy.data.objects["body"]; me = b.data
m = np.zeros(len(me.polygons), int); me.attributes["mat"].data.foreach_get("value", m)
print("MATCNT", collections.Counter(m.tolist()))
names = [g.name for g in b.vertex_groups]
co = np.array([v.co for v in me.vertices])
dom = []
for v in me.vertices:
    if v.groups: g = max(v.groups, key=lambda e: e.weight); dom.append(names[g.group])
    else: dom.append("none")
dom = np.array(dom)
# per-vertex material via polygons
vm = np.full(len(me.vertices), -1)
for p in me.polygons:
    for vi in p.vertices: vm[vi] = m[p.index]
for g in sorted(set(dom)):
    s = dom == g
    print("VG", g, s.sum(), "mats", collections.Counter(vm[s].tolist()).most_common(4), "z", co[s,2].min().round(3), co[s,2].max().round(3), "x", co[s,0].min().round(3), co[s,0].max().round(3))
print("BBOX", co.min(0), co.max(0))
