# Blender -b --factory-startup -P clean_mesh.py -- IN.glb OUT.glb [voxel=0.01] [faces=40000]
# voxel remesh (manifold, kills internal shells) + decimate; keeps glb frame on export.
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]
vox = float(a[2]) if len(a) > 2 else 0.01; nf = int(a[3]) if len(a) > 3 else 40000
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
o = [x for x in bpy.context.scene.objects if x.type == "MESH"][0]
bpy.context.view_layer.objects.active = o; o.select_set(True)
for att in list(o.data.color_attributes): o.data.color_attributes.remove(att)
m = o.modifiers.new("r", "REMESH"); m.mode = "VOXEL"; m.voxel_size = vox; bpy.ops.object.modifier_apply(modifier="r")
n = len(o.data.polygons); d = o.modifiers.new("d", "DECIMATE"); d.ratio = min(1.0, nf / n); bpy.ops.object.modifier_apply(modifier="d")
bpy.ops.object.shade_smooth()
print("CLEAN", n, "->", len(o.data.polygons))
bpy.ops.export_scene.gltf(filepath=a[1], export_format="GLB", use_selection=True)
