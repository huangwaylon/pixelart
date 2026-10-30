import bpy, collections
for o in bpy.data.objects: print("OBJ", o.name, o.type, len(o.data.vertices) if o.type=="MESH" else "", dict((k, (str(o[k])[:80])) for k in o.keys()))
b = bpy.data.objects["body"]; me = b.data
print("CA", [(c.name, c.domain, c.data_type) for c in me.color_attributes])
print("ATTR", [(a.name, a.domain, a.data_type) for a in me.attributes][:60])
print("UV", [u.name for u in me.uv_layers]); print("MATS", [m.name for m in me.materials])
ca = me.color_attributes["Color"]
cnt = collections.Counter(tuple(round(c*255) for c in d.color[:3]) for d in ca.data)
print("COLORS", cnt.most_common(30))
print("VG", len(b.vertex_groups), [g.name for g in b.vertex_groups])
print("MODS", [(m.name, m.type) for m in b.modifiers])
