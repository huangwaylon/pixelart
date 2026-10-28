"""Make a measurement scene: guide.blend + the Pixal3D 4-view mesh (model/ai_ref/pixal3d/best), scaled so its
sole->top height equals the guide's sole->top (bow) height, parented to the rig (so it yaws with the
direction), all guide meshes hidden.  Render it with render_guides.py --blend <out> --passes mask.
  Blender -b --factory-startup -P tools/hybrid/p3d_scene.py -- [out.blend]"""
import bpy, sys
from mathutils import Vector as V
ROOT = "/Users/waylonhuang/Documents/other/pixelart/swordswoman"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = argv[0] if argv else "/tmp/p3d_scene.blend"
bpy.ops.wm.open_mainfile(filepath=ROOT + "/hybrid/guide/guide.blend")
rig = bpy.data.objects["rig"]
import json
meta = json.loads(rig["guide_meta"])
top = meta["top_z_incl_bow"]
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=ROOT + "/model/ai_ref/pixal3d/best/akane_pixal3d_mv4_gemfix_s42-r1024-8k.glb")
new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
bpy.context.view_layer.update()
pts = [o.matrix_world @ v.co for o in new for v in o.data.vertices]
zmin = min(p.z for p in pts); zmax = max(p.z for p in pts)
cx = sum(p.x for p in pts) / len(pts); cy = sum(p.y for p in pts) / len(pts)
k = top / (zmax - zmin)
for o in bpy.data.objects:
    if o.type == "MESH" and o not in new:
        o.hide_render = True
for o in new:
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw
    for v in o.data.vertices:
        w = mw @ v.co
        v.co = mw.inverted() @ V(((w.x - cx) * k, (w.y - cy) * k, (w.z - zmin) * k))
    o.name = "katana" if False else o.name
    o.parent = rig
    o.matrix_parent_inverse = rig.matrix_world.inverted()
print("P3D scale", k, "height", top)
bpy.ops.wm.save_as_mainfile(filepath=out)
