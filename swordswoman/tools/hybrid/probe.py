import bpy, json
sc=bpy.context.scene
rig=bpy.data.objects["rig"]
print("ENGINE",sc.render.engine, "props", {k:(rig[k] if not hasattr(rig[k],'to_dict') else '..') for k in rig.keys()})
for o in sorted(bpy.data.objects, key=lambda o:o.name):
    print("OBJ",o.name,o.type,o.parent.name if o.parent else None,o.parent_bone, [m.type for m in getattr(o,'modifiers',[])], tuple(round(x,3) for x in o.dimensions), o.hide_render)
for b in rig.data.bones:
    print("BONE",b.name,b.parent.name if b.parent else None,tuple(round(x,3) for x in b.head_local),tuple(round(x,3) for x in b.tail_local))
for a in bpy.data.actions:
    print("ACT",a.name,tuple(a.frame_range))
