"""Scene setup, outlines, rendering and compositing helpers."""
import bpy, math, os
import numpy as np
from mathutils import Vector
from common import hexc

def setup_scene():
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.eevee.taa_render_samples = 16
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.render.film_transparent = True
    sc.unit_settings.system = 'METRIC'
    w = bpy.data.worlds.new('World') if not sc.world else sc.world
    sc.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    bg = w.node_tree.nodes.get('Background')
    if bg:
        bg.inputs[0].default_value = (0, 0, 0, 1); bg.inputs[1].default_value = 0.0
    if 'KeySun' not in bpy.data.objects:
        L = bpy.data.lights.new('KeySun', 'SUN'); L.energy = math.pi; L.angle = math.radians(2)
        try:
            L.use_shadow = True
        except Exception:
            pass
        ob = bpy.data.objects.new('KeySun', L); sc.collection.objects.link(ob)
        d = Vector((-0.40, -1.0, 0.95)).normalized()
        ob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        L2 = bpy.data.lights.new('FillSun', 'SUN'); L2.energy = 1.8; L2.angle = math.radians(5)
        L2.use_shadow = False
        ob2 = bpy.data.objects.new('FillSun', L2); sc.collection.objects.link(ob2)
        d2 = Vector((0.3, 1.0, 0.6)).normalized()
        ob2.rotation_euler = d2.to_track_quat('Z', 'Y').to_euler()
    return sc

def make_outlines(objs, mat, thick=0.0018, coll=None, per=None):
    """Inverted hull: copy evaluated mesh, push along normals, flip, backface-culled dark material."""
    import bmesh
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for ob in objs:
        t = (per or {}).get(ob.name, thick)
        ev = ob.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev, depsgraph=dg)
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.normal_update()
        for v in bm.verts:
            v.co += v.normal * t
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free()
        me.materials.clear(); me.materials.append(mat)
        me.shade_smooth()
        o = bpy.data.objects.new('OL_' + ob.name, me)
        o.matrix_world = ob.matrix_world.copy()
        (coll or bpy.context.scene.collection).objects.link(o)
        o['outline'] = True
        out.append(o)
    return out

def cam(name, loc, target, ortho=None, lens=50):
    c = bpy.data.objects.get(name)
    if c is None:
        c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); bpy.context.scene.collection.objects.link(c)
    c.location = loc
    d = Vector(target) - Vector(loc)
    c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        c.data.type = 'ORTHO'; c.data.ortho_scale = ortho
    else:
        c.data.type = 'PERSP'; c.data.lens = lens
    c.data.clip_start = 0.01; c.data.clip_end = 50
    return c

def render_to(camobj, path, w, h):
    sc = bpy.context.scene
    sc.camera = camobj
    sc.render.resolution_x = w; sc.render.resolution_y = h; sc.render.resolution_percentage = 100
    sc.render.filepath = path
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    bpy.ops.render.render(write_still=True)

def load_np(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    return a

def over_bg(a, bg=(0.80, 0.80, 0.80)):
    rgb = a[..., :3] * a[..., 3:4] + np.array(bg)[None, None, :] * (1 - a[..., 3:4])
    return np.concatenate([rgb, np.ones_like(a[..., :1])], -1)

def resize_nn(a, w, h):
    H, W = a.shape[:2]
    ys = (np.arange(h) * H / h).astype(int); xs = (np.arange(w) * W / w).astype(int)
    return a[ys][:, xs]

def save_np(a, path):
    h, w = a.shape[:2]
    img = bpy.data.images.new('tmp_save', w, h, alpha=True)
    img.pixels.foreach_set(a.astype(np.float32).ravel())
    img.filepath_raw = path; img.file_format = 'PNG'; img.save()
    bpy.data.images.remove(img)
