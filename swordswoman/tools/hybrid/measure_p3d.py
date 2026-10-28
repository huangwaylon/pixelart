import bpy, sys, os, math
from mathutils import Vector as V
ROOT="/Users/waylonhuang/Documents/other/pixelart/swordswoman"
OUT=ROOT+"/hybrid/guide/measure"; os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=ROOT+"/model/character.blend")
sc=bpy.context.scene; rig=bpy.data.objects["rig"]; cam=bpy.data.objects["cam"]
rig.animation_data.action=bpy.data.actions["pose_idle_S"]; sc.frame_set(1)
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=ROOT+"/model/ai_ref/pixal3d/best/akane_pixal3d_mv4_gemfix_s42-r1024-8k.glb")
new=[o for o in bpy.data.objects if o not in before]
for o in new: print("NEW",o.name,o.type,o.parent, tuple(o.location), tuple(o.rotation_euler), tuple(o.scale), tuple(o.dimensions))
dg=bpy.context.evaluated_depsgraph_get()
def bbox(objs):
    mn=V((1e9,)*3); mx=V((-1e9,)*3)
    for o in objs:
        if o.type!='MESH' or o.hide_render: continue
        e=o.evaluated_get(dg); m=e.to_mesh()
        for v in m.vertices:
            w=e.matrix_world@v.co
            mn=V(map(min,mn,w)); mx=V(map(max,mx,w))
        e.to_mesh_clear()
    return mn,mx
p=[o for o in new if o.type=='MESH']
print("P3D bbox",bbox(p))
proc=[o for o in bpy.data.objects if o.type=="MESH" and o not in new and not o.hide_render]
print("PROC bbox",bbox(proc))
print("PROC nosword bbox",bbox([o for o in proc if 'katana' not in o.name]))
print("PROC head",bbox([bpy.data.objects[n] for n in ("head",)]), "hair", bbox([bpy.data.objects[n] for n in ("hair_cap","bangs","hair_strands")]), "bow", bbox([bpy.data.objects["bow"]]), "bun", bbox([bpy.data.objects["bun"]]))
# ---- render silhouettes
S=3.3946/0.9185
for o in p:
    o.scale=(S,S,S); o.location=(0,0,0.0031*S)
bpy.context.view_layer.update()
sc.render.engine='BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else sc.render.engine
sc.render.film_transparent=True
sc.render.resolution_x=sc.render.resolution_y=1024
flat=bpy.data.materials.new("flat"); flat.use_nodes=True
nt=flat.node_tree; [nt.nodes.remove(n) for n in list(nt.nodes)]
em=nt.nodes.new("ShaderNodeEmission"); out=nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0],out.inputs[0])
vl=bpy.context.view_layer
def setcam(view):
    cam.data.ortho_scale=3.9; rig.rotation_euler=(0,0,0)
    zc=1.62; D=20
    if view=="front": cam.rotation_euler=(math.pi/2,0,0); cam.location=(0,-D,zc)
    if view=="side": cam.rotation_euler=(math.pi/2,0,math.pi/2); cam.location=(D,0,zc)
    if view=="back": cam.rotation_euler=(math.pi/2,0,math.pi); cam.location=(0,D,zc)
vl.material_override=flat
for view in ("front","side","back"):
    setcam(view)
    for which in ("proc","p3d"):
        for o in proc: o.hide_render = (which!="proc")
        for o in p: o.hide_render = (which!="p3d")
        sc.render.filepath=f"{OUT}/sil_{which}_{view}.png"; bpy.ops.render.render(write_still=True)
vl.material_override=None
for o in proc: o.hide_render=True
for o in p: o.hide_render=False
for view in ("front","side"):
    setcam(view); sc.render.filepath=f"{OUT}/tex_p3d_{view}.png"; bpy.ops.render.render(write_still=True)
