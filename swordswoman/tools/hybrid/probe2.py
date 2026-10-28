import bpy, json
rig=bpy.data.objects["rig"]
for k in rig.keys():
    v=rig[k]
    if isinstance(v,str) and k!='poses': print("PROP",k,v[:1500])
for a in ("anim_walk_SE","anim_slash_SE","anim_jump_E","anim_idle_SE"):
    act=bpy.data.actions[a]
    try: fcs=act.fcurves
    except: fcs=[fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
    paths=sorted(set(fc.data_path.split('"')[1] if '"' in fc.data_path else fc.data_path for fc in fcs))
    print("ACT",a,len(fcs),paths[:60])
    print("  keys",sorted(set(k.co[0] for fc in fcs for k in fc.keyframe_points)))
    print("  scalecurves",[fc.data_path for fc in fcs if fc.data_path.endswith("scale")][:10])
for c in bpy.data.objects["bow"].constraints: print("BOWC",c.type)
pb=rig.pose.bones["bow"]
for c in pb.constraints: print("BOWBONEC",c.type,c.name, getattr(c,'target',None), c.influence)
for d in rig.animation_data.drivers: print("DRV",d.data_path, d.driver.expression)
print("FREESTYLE", bpy.context.scene.render.use_freestyle)
for o in bpy.data.objects:
    for c in getattr(o,'constraints',[]): print("OBJC",o.name,c.type)
