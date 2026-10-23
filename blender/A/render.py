"""Render helpers: toon EEVEE setup, ortho cameras, stitched turnaround / face sheets."""
import bpy, math, os
import numpy as np
from mathutils import Vector
import lib

def setup_scene():
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    try:
        sc.eevee.taa_render_samples = 16
    except Exception:
        pass
    w = bpy.data.worlds.new('World'); sc.world = w
    w.use_nodes = True
    nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    lp = nt.nodes.new('ShaderNodeLightPath')
    bg_cam = nt.nodes.new('ShaderNodeBackground'); bg_cam.inputs['Color'].default_value = lib.hexc('#BCBCBC'); bg_cam.inputs['Strength'].default_value = 1
    bg_amb = nt.nodes.new('ShaderNodeBackground'); bg_amb.inputs['Color'].default_value = (1, 1, 1, 1); bg_amb.inputs['Strength'].default_value = 0.15
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
    nt.links.new(bg_amb.outputs['Background'], mix.inputs[1])
    nt.links.new(bg_cam.outputs['Background'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    # key light: from viewer's upper-left front
    ld = bpy.data.lights.new('Key', 'SUN'); ld.energy = 3.0; ld.angle = math.radians(2)
    ld.use_shadow = False
    lo = bpy.data.objects.new('Key', ld); sc.collection.objects.link(lo)
    d = -Vector((-0.38, -1.0, 0.70)).normalized()
    lo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cd = bpy.data.cameras.new('Cam'); cd.type = 'ORTHO'
    co = bpy.data.objects.new('Cam', cd); sc.collection.objects.link(co)
    sc.camera = co
    return co, lo


def aim(cam, target, azim_deg, dist=5.0, elev_deg=0.0):
    a = math.radians(azim_deg); e = math.radians(elev_deg)
    # azim 0 = front (camera at -Y), 90 = her left side (+X)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam.location = Vector(target) + d * dist
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()


def render_view(path, azim, target, scale, res_x, res_y, elev=0.0, light_follow=True):
    sc = bpy.context.scene
    cam = sc.camera; key = bpy.data.objects['Key']
    cam.data.ortho_scale = scale
    cam.data.clip_start = 0.01; cam.data.clip_end = 20
    aim(cam, target, azim, elev_deg=elev)
    if light_follow:
        a = math.radians(azim)
        base = Vector((-0.38, -1.0, 0.70))
        rot = Vector((base.x * math.cos(a) - base.y * math.sin(a), base.x * math.sin(a) + base.y * math.cos(a), base.z))
        key.rotation_euler = (-rot.normalized()).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x = res_x; sc.render.resolution_y = res_y
    sc.render.resolution_percentage = 100
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def load_np(path):
    im = bpy.data.images.load(path)
    w, h = im.size
    a = np.empty(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    return a.reshape(h, w, 4)


def save_np(arr, path):
    h, w = arr.shape[:2]
    img = bpy.data.images.new('tmp_save', w, h, alpha=True)
    img.pixels.foreach_set(arr.astype(np.float32).ravel())
    img.filepath_raw = path; img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)


def resize_h(a, H):
    h, w = a.shape[:2]
    W = int(round(w * H / h))
    yi = (np.arange(H) * h / H).astype(int); xi = (np.arange(W) * w / W).astype(int)
    return a[yi][:, xi]


def hstack(paths, out, H=None, gap=4):
    arrs = [load_np(p) for p in paths]
    H = H or max(a.shape[0] for a in arrs)
    arrs = [resize_h(a, H) if a.shape[0] != H else a for a in arrs]
    g = np.ones((H, gap, 4), dtype=np.float32)
    parts = []
    for i, a in enumerate(arrs):
        if i:
            parts.append(g)
        parts.append(a)
    save_np(np.concatenate(parts, axis=1), out)


def turnaround(tag, outdir):
    tmp = os.path.join(outdir, '_tmp'); os.makedirs(tmp, exist_ok=True)
    paths = []
    for name, az in [('front', 0), ('q34', 35), ('side', 90), ('back', 180)]:
        p = os.path.join(tmp, f'{tag}_{name}.png')
        render_view(p, az, (0, 0, 0.83), 1.72, 640, 1024)
        paths.append(p)
    hstack(paths, os.path.join(outdir, f'{tag}_turnaround.png'))


def face(tag, outdir):
    tmp = os.path.join(outdir, '_tmp'); os.makedirs(tmp, exist_ok=True)
    paths = []
    for name, az in [('front', 0), ('q34', 32), ('side', 90)]:
        p = os.path.join(tmp, f'{tag}_face_{name}.png')
        render_view(p, az, (0, 0.0, 1.45), 0.42, 720, 720)
        paths.append(p)
    hstack(paths, os.path.join(outdir, f'{tag}_face.png'))


def ref_compare(tag, outdir, refdir):
    tmp = os.path.join(outdir, '_tmp'); os.makedirs(tmp, exist_ok=True)
    # ref5 (front, 1242x2000, figure ~0.30..0.88 of height), ref4 (side, same framing)
    p5 = os.path.join(tmp, f'{tag}_cmp_front.png')
    p4 = os.path.join(tmp, f'{tag}_cmp_side.png')
    # figure in refs spans ~0.145..0.875 of image height (crown..soles)
    frac = 0.875 - 0.145
    scale = 1.61 / frac
    cz = 1.61 / 2 + (0.5 - (0.145 + 0.875) / 2) * scale * -1
    render_view(p5, 0, (0, 0, 0.805 - (0.51 - 0.5) * scale), scale * 1.0, 621, 1000)
    render_view(p4, 90, (0, 0, 0.805 - (0.51 - 0.5) * scale), scale * 1.0, 621, 1000)
    hstack([os.path.join(refdir, 'ref4.png'), p4, os.path.join(refdir, 'ref5.png'), p5],
           os.path.join(outdir, 'final_vs_ref4_ref5.png' if tag == 'final' else f'{tag}_vs_ref4_ref5.png'), H=1000)


def detail(tag, outdir):
    tmp = os.path.join(outdir, '_tmp'); os.makedirs(tmp, exist_ok=True)
    paths = []
    for name, az, tgt, sc in [('bowback', 180, (0, 0.1, 1.50), 0.45), ('bow34', 145, (0, 0.1, 1.50), 0.45),
                              ('chest', 0, (0, 0, 1.12), 0.40)]:
        p = os.path.join(tmp, f'{tag}_det_{name}.png')
        render_view(p, az, tgt, sc, 640, 640)
        paths.append(p)
    hstack(paths, os.path.join(outdir, f'{tag}_detail.png'))
