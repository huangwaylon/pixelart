# render_motion.py (skinned rig, R) -- contract render command:
#   <blender> -b rig/rig.blend -P render/render_motion.py -- motion/<action>.json <view> <outdir> [--preview] [--stamp] [--frames a:b] [--no-post]
# Plays a motion file on the skinned rig (root.loc world metres, per-bone local quaternions = pose rotation_quaternion, optional scale)
# through the game camera (30 deg elevation, ortho, 192 cell with pivot (96,152) = in-game 128 cell crop 32..160, 52.608 px per H2 unit
# = 67.88 px per metre at 1x, same as rig H2 / v2/g96 / hires3d).  View SE|E|S|SW|NE|N (camera on her front-right for SE, as H2).
#   --preview : EEVEE smooth-shaded frames at 2x (256 px game cell) + <action>_<view>_preview.gif
#   full      : 8x passes guide (matid, AA off) + lum (white diffuse, camera-relative sun, 16 bit) + dep (camera depth, 16 bit)
#               -> render/pixel_chain.py: cel (locked palette ramps) + hi-res outline -> E2 k-centroid -> rig-material palette lock -> fix
#               -> pixel frames (pzlib txt/png) + <action>_<view>_4x.gif on mid-grey + contact sheet.  --stamp pastes the m96 neutral head.
# Motion file "rest" (literal) = identity pose, 1 frame.
import bpy, sys, os, json, math, subprocess, time
from mathutils import Vector, Matrix, Quaternion
from bpy_extras.object_utils import world_to_camera_view
argv = sys.argv[sys.argv.index("--") + 1:]
pos = [x for x in argv if not x.startswith("--")]; flags = [x for x in argv if x.startswith("--")]
MOT, VIEW, OUT = pos[:3]
PREVIEW = "--preview" in flags; STAMP = "--stamp" in flags; NOPOST = "--no-post" in flags
FR = next((f.split("=")[1] for f in flags if f.startswith("--frames=")), None)
_AL = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rig", "align.json")))
YAW = float(next((f.split("=")[1] for f in flags if f.startswith("--yaw=")), _AL.get(VIEW, {}).get("yaw", 0.0)))  # per-view yaw cheat (rig/align.json; SE -10, NE -25 = master 3/4 frontality, fitted by head_hull.py + rest IoU)
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(HERE)
PYX = "/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python"
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene; ao = bpy.data.objects["rig"]; body = bpy.data.objects["body"]; pbs = ao.pose.bones
K = float(ao.get("units_per_h2", 0.775))
CELL, PIV, PPU = 192, (96, 152), 52.608
SC = int(os.environ.get("PVS", "2")) if PREVIEW else int(os.environ.get("SCH", "8"))
# ------------------------------------------------------------------ motion
if MOT == "rest":
    M = {"action": "rest", "fps": 24, "loop": False, "frames": [{"t": 0, "root": {"loc": [0, 0, 0]}, "bones": {}}]}
else:
    M = json.load(open(MOT))
act = M.get("action", os.path.splitext(os.path.basename(MOT))[0])
frames = M["frames"]; idxs = list(range(len(frames)))
if FR: a_, b_ = FR.split(":"); idxs = idxs[int(a_ or 0):int(b_) if b_ else None]
tim = M.get("timing_ms") or [round(1000 / M.get("fps", 24))] * len(frames)
ao.rotation_mode = "XYZ"; ao.rotation_euler = (0, 0, math.radians(YAW))
for p in pbs: p.rotation_mode = "QUATERNION"
REST = {p.name: ao.data.bones[p.name].matrix_local.copy() for p in pbs}
def apply(fr):
    for p in pbs: p.rotation_quaternion = (1, 0, 0, 0); p.location = (0, 0, 0); p.scale = (1, 1, 1)
    loc = Vector(fr.get("root", {}).get("loc", [0, 0, 0]))
    R3 = REST["root"].to_3x3(); pbs["root"].location = R3.transposed() @ (loc - REST["root"].translation)
    for n, v in fr.get("bones", {}).items():
        if n not in pbs: continue
        if "rot" in v: pbs[n].rotation_quaternion = Quaternion(v["rot"])
        if "loc" in v and n != "root": pbs[n].location = Vector(v["loc"])
    for n, s in (fr.get("scale") or {}).items():
        if n in pbs: pbs[n].scale = Vector(s)
    bpy.context.view_layer.update()
# ------------------------------------------------------------------ camera / light (contract frame: her front +Y, her left -X)
AZ = {"SE": (1, 1), "E": (1, 0), "S": (0, 1), "SW": (-1, 1), "NE": (1, -1), "N": (0, -1), "W": (-1, 0), "NW": (-1, -1)}
cam = bpy.data.objects.get("cam") or bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
sc.camera = cam; cam.data.type = "ORTHO"; cam.data.ortho_scale = CELL / PPU * K
cam.data.shift_x = 0.5 - PIV[0] / CELL; cam.data.shift_y = PIV[1] / CELL - 0.5; cam.data.clip_start = 0.1; cam.data.clip_end = 100
c = Vector((*AZ[VIEW], 0)).normalized(); el = math.radians(30); DIST = 10 * K
cam.location = Vector((c.x * math.cos(el), c.y * math.cos(el), math.sin(el))) * DIST
cam.rotation_euler = (-cam.location).to_track_quat("-Z", "Y").to_euler()
sun = bpy.data.objects.get("sun") or bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
if sun.name not in sc.collection.objects: sc.collection.objects.link(sun)
right = (-cam.location).normalized().cross(Vector((0, 0, 1))).normalized()
ld = (-right * float(os.environ.get("SUN_L", "0.6")) + Vector((0, 0, 1)) * 0.9 + c * float(os.environ.get("SUN_C", "0.9"))).normalized()  # from screen-left, above, camera side (rig_lib used 0.7/0.6; a bit more frontal so her front reads lit as in the masters)
sun.rotation_euler = (-ld).to_track_quat("-Z", "Y").to_euler(); sun.data.energy = 3.0
if not sc.world: sc.world = bpy.data.worlds.new("w")
sc.render.resolution_x = sc.render.resolution_y = CELL * SC; sc.render.film_transparent = True; sc.render.resolution_percentage = 100
# ------------------------------------------------------------------ materials
ILLUS = ao.get("head_mode", "") == "illus"
def _tex_base(v): return os.path.join(EXP, "rig", "tex_illus", f"{v}.png") if ILLUS else os.path.join(EXP, "rig", "tex", f"tex_{v}.png")
TEXV = VIEW if ("pj_" + VIEW) in body.data.uv_layers and os.path.exists(_tex_base(VIEW)) else None
EXPR_SRC = {"S": ("S", False), "SE": ("SE", False), "E": ("E", False), "SW": ("SE", True), "W": ("E", True)}  # NE/N/NW: no face swap
def illus_tex(fr, view=None):
    """round 7: per-view illustration texture for this frame. F's aligned expression illustrations: face/illus/out/<S|SE|E>/<face>[_half|_blink][_open].png
    (+ face_mask.png); W/SW use the flipped E/SE files; NE/N/NW have no face swap (base illustration). The exact name must exist: a missing
    file raises (no silent fallback / placeholder). The swap is composited into the background-filled base texture inside F's face_mask and cached
    as rig/tex_illus/expr/<VIEW>/<name>.png."""
    if not (ILLUS and TEXV): return None
    view = view or VIEW
    if view not in EXPR_SRC: return _tex_base(view)
    f_ = str(fr.get("face", "neutral")); bl = fr.get("blink", 0) or 0
    try: bl = float(bl)
    except Exception: bl = 1.0 if str(bl) in ("closed", "blink") else 0.5 if str(bl) == "half" else 0.0
    b_ = "blink" if bl >= 0.75 else "half" if bl >= 0.25 else ""; m_ = "open" if str(fr.get("mouth", "")) == "open" else ""
    name = "_".join(x for x in (f_, b_, m_) if x); sv, flip = EXPR_SRC[view]
    src = os.path.join(EXP, "face", "illus", "out", sv, name + ".png")
    if not os.path.exists(src):  # fail loudly: message + non-zero exit code (Blender would otherwise exit 0 after a script exception)
        print(f"FATAL render_motion: missing expression illustration {src} (frame keys face={f_!r} blink={bl} mouth={fr.get('mouth')!r})", flush=True); os._exit(3)
    out = os.path.join(EXP, "rig", "tex_illus", "expr", view, name + ".png")
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(src):
        import numpy as np
        def arr(pth):
            im = bpy.data.images.load(pth); a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4); bpy.data.images.remove(im); return a
        base = arr(os.path.join(EXP, "rig", "tex_illus", f"{sv}.png")); ex = arr(src); mk = arr(os.path.join(EXP, "face", "illus", "out", sv, "face_mask.png"))[..., :1] > 0.5
        comp = np.where(mk, ex, base); comp[..., 3] = 1.0
        if flip: comp = comp[:, ::-1]
        os.makedirs(os.path.dirname(out), exist_ok=True); im = bpy.data.images.new("expr_tmp", comp.shape[1], comp.shape[0], alpha=True)
        im.pixels.foreach_set(comp.ravel()); im.filepath_raw = out; im.file_format = "PNG"; im.save(); bpy.data.images.remove(im)
    return out
def _texnodes(N, L):
    """master-projection colour (Closest) through UV pj_<VIEW> + face mask pm_<VIEW> (1 = head-group face visible from this view at rest)"""
    im = N.new("ShaderNodeTexImage"); im.name = "ILLUS_TEX"; im.image = bpy.data.images.load(_tex_base(TEXV), check_existing=True)
    im.interpolation = "Linear" if ILLUS else "Closest"; im.extension = "EXTEND"; uvn = N.new("ShaderNodeUVMap"); uvn.name = "ILLUS_UV"; uvn.uv_map = "pj_" + TEXV; L.new(uvn.outputs[0], im.inputs[0])
    pm = N.new("ShaderNodeAttribute"); pm.name = "ILLUS_PM"; pm.attribute_type = "GEOMETRY"; pm.attribute_name = "pm_" + TEXV
    return im, pm
# ---- round 5: 3D face textures (UV face_uv, mask fmask), switched per frame from M's face/blink/mouth keys
FACE_DIRS = [os.path.join(EXP, "face", "tex3d"), os.path.join(EXP, "rig", "face_tex")]
HASFACE = "face_uv" in body.data.uv_layers and "fmask" in body.data.attributes
def face_tex(fr, col=False):
    """first existing texture of: <face>_<blink>_<mouth>, <face>_<blink>, <face>_<mouth>, <face>, neutral_<blink>, neutral
    (blink >= .75 -> 'blink', >= .25 -> 'half'; mouth 'open' -> 'open'); col=True looks for the *_col.png preview colours first"""
    f_ = str(fr.get("face", "neutral")); bl = fr.get("blink", 0) or 0
    try: bl = float(bl)
    except Exception: bl = 1.0 if str(bl) in ("closed", "blink") else 0.5 if str(bl) == "half" else 0.0
    b_ = "blink" if bl >= 0.75 else "half" if bl >= 0.25 else ""; m_ = "open" if str(fr.get("mouth", "")) == "open" else ""
    names = [n for n in ("_".join(x for x in (f_, b_, m_) if x), "_".join(x for x in (f_, b_) if x), "_".join(x for x in (f_, m_) if x), f_,
                         "_".join(x for x in ("neutral", b_) if x), "neutral")]
    for n in names:
        for d_ in FACE_DIRS:
            for sfx in (("_col", "") if col else ("",)):
                pth = os.path.join(d_, n + sfx + ".png")
                if os.path.exists(pth): return pth
    return None
_FIMG = {}
def _img(pth):
    if pth not in _FIMG:
        im = bpy.data.images.load(pth, check_existing=True); im.colorspace_settings.name = "sRGB"; _FIMG[pth] = im
    return _FIMG[pth]
def _facenodes(N, L, col):
    im = N.new("ShaderNodeTexImage"); im.name = "FACE_COL" if col else "FACE_MAT"; im.interpolation = "Closest"; im.extension = "CLIP"
    uvn = N.new("ShaderNodeUVMap"); uvn.uv_map = "face_uv"; L.new(uvn.outputs[0], im.inputs[0])
    fm = N.new("ShaderNodeAttribute"); fm.attribute_type = "GEOMETRY"; fm.attribute_name = "fmask"
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; L.new(fm.outputs["Fac"], mul.inputs[0]); L.new(im.outputs["Alpha"], mul.inputs[1])
    return im, mul
def eff_view():
    """projection view whose rest camera direction (in the head's rest frame, per-view yaw cheat removed) is closest to this frame's camera
    direction seen from the posed head: a head turn beyond ~22 deg switches to the neighbouring illustration instead of smearing the current one"""
    R = (ao.matrix_world @ pbs["head"].matrix).to_3x3() @ REST["head"].to_3x3().inverted()
    ch = R.transposed() @ cam.matrix_world.to_3x3().col[2].normalized(); ch.z = 0; ch.normalize(); best, bv = -9, VIEW
    for v, (ax_, ay_) in AZ.items():
        if ("pj_" + v) not in body.data.uv_layers or not os.path.exists(_tex_base(v)): continue
        yv = math.radians(_AL.get(v, {}).get("yaw", 0.0)); c = Vector((ax_, ay_, 0)).normalized()
        cv = Vector((c.x * math.cos(-yv) - c.y * math.sin(-yv), c.x * math.sin(-yv) + c.y * math.cos(-yv), 0))
        s = ch.dot(cv) + (1e-3 if v == VIEW else 0)
        if s > best: best, bv = s, v
    return bv
def set_face(fr):
    if ILLUS and TEXV:  # round 7: expression swap on the illustration texture; round 8: projection view picked by head yaw vs the camera
        ev = eff_view(); CUR["eff"] = ev; pth = illus_tex(fr, ev)
        for m in bpy.data.materials:
            if m.use_nodes:
                for nd_ in m.node_tree.nodes:
                    if nd_.name == "ILLUS_UV": nd_.uv_map = "pj_" + ev
                    if nd_.name == "ILLUS_PM": nd_.attribute_name = "pm_" + ev
                    if nd_.name == "ILLUS_TEX" and pth:
                        im_ = bpy.data.images.load(pth, check_existing=True); im_.reload() if im_.filepath == pth else None; nd_.image = im_
        return os.path.basename(pth) if pth else None
    if not HASFACE: return None
    pm, pc = face_tex(fr), face_tex(fr, col=True)
    for m in bpy.data.materials:
        if not m.use_nodes: continue
        for nd_ in m.node_tree.nodes:
            if nd_.name == "FACE_MAT" and pm: nd_.image = _img(pm)
            if nd_.name == "FACE_COL" and (pc or pm): nd_.image = _img(pc or pm)
    return os.path.basename(pm) if pm else None
def mk(kind):
    nm = "rm_" + kind + "_" + str(TEXV)
    if nm in bpy.data.materials: return bpy.data.materials[nm]
    m = bpy.data.materials.new(nm); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    for n in list(N): N.remove(n)
    out = N.new("ShaderNodeOutputMaterial")
    if kind == "guide":  # round 5: matid flat colours incl. the face texture mats (EEVEE emission, 1 sample = exact colours)
        at = N.new("ShaderNodeAttribute"); at.attribute_name = "Color"; em = N.new("ShaderNodeEmission")
        if HASFACE:
            im, mul = _facenodes(N, L, False); mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
            L.new(mul.outputs[0], mx.inputs[0]); L.new(at.outputs["Color"], mx.inputs[6]); L.new(im.outputs["Color"], mx.inputs[7]); L.new(mx.outputs[2], em.inputs[0])
        else: L.new(at.outputs["Color"], em.inputs[0])
        L.new(em.outputs[0], out.inputs[0]); return m
    if kind == "pv":
        at = N.new("ShaderNodeAttribute"); at.attribute_name = "PV" if "PV" in body.data.color_attributes else "Color"; df = N.new("ShaderNodeBsdfPrincipled")
        df.inputs["Roughness"].default_value = 0.8
        if HASFACE:
            im, mul = _facenodes(N, L, True); mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
            L.new(mul.outputs[0], mx.inputs[0]); L.new(at.outputs["Color"], mx.inputs[6]); L.new(im.outputs["Color"], mx.inputs[7]); L.new(mx.outputs[2], df.inputs["Base Color"])
        else: L.new(at.outputs["Color"], df.inputs["Base Color"])
        if TEXV:  # head shows the projected master pixels (flat), body smooth-shaded
            im, pm = _texnodes(N, L); em = N.new("ShaderNodeEmission"); L.new(im.outputs["Color"], em.inputs[0]); mx = N.new("ShaderNodeMixShader")
            L.new(pm.outputs["Fac"], mx.inputs[0]); L.new(df.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
        else: L.new(df.outputs[0], out.inputs[0])
        return m
    if kind == "tex":
        im, pm = _texnodes(N, L); em = N.new("ShaderNodeEmission"); L.new(im.outputs["Color"], em.inputs[0]); tr = N.new("ShaderNodeBsdfTransparent")
        mx = N.new("ShaderNodeMixShader"); L.new(pm.outputs["Fac"], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
        return m
    em = N.new("ShaderNodeEmission"); L.new(em.outputs[0], out.inputs[0])
    if kind == "lum":
        df = N.new("ShaderNodeBsdfDiffuse"); df.inputs[0].default_value = (1, 1, 1, 1)
        s2r = N.new("ShaderNodeShaderToRGB"); L.new(df.outputs[0], s2r.inputs[0]); L.new(s2r.outputs[0], em.inputs[0])
    else:  # dep: camera-space depth, same normalisation as hires3d (H2 units 8..12 -> 0..1)
        g = N.new("ShaderNodeNewGeometry"); vt = N.new("ShaderNodeVectorTransform"); vt.convert_from = "WORLD"; vt.convert_to = "CAMERA"; vt.vector_type = "POINT"
        L.new(g.outputs["Position"], vt.inputs[0]); sp = N.new("ShaderNodeSeparateXYZ"); L.new(vt.outputs[0], sp.inputs[0])
        ma = N.new("ShaderNodeMath"); ma.operation = "MULTIPLY_ADD"; ma.inputs[1].default_value = 0.25 / K; ma.inputs[2].default_value = -2.0
        L.new(sp.outputs["Z"], ma.inputs[0]); L.new(ma.outputs[0], em.inputs[0])
    return m
CUR = {"fr": {}}
def set_mat(kind):
    body.data.materials.clear(); body.data.materials.append(mk(kind)); set_face(CUR["fr"])
def rpass(path, kind):
    """passes: guide (matid flat, AA off) | lid (limb IDs flat: L leg red, R leg green, L arm blue, R arm yellow; .L = her left) |
    tex (projected master head pixels, alpha = head-group mask) | lum | dep | pv (preview)"""
    sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"; sc.view_settings.exposure = 0; sc.view_settings.gamma = 1
    sc.render.image_settings.color_depth = "8"; sc.render.image_settings.color_mode = "RGBA"
    cas = body.data.color_attributes
    if kind == "lid" or (kind == "guide" and not HASFACE):
        cas.active_color = cas["LID" if kind == "lid" else "Color"]
        sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "FLAT"; sh.color_type = "VERTEX"
        sh.show_object_outline = False; sh.show_cavity = False; sc.display.render_aa = "OFF"
        sc.render.filepath = path; bpy.ops.render.render(write_still=True); cas.active_color = cas["Color"]; return
    if kind == "tex" and not TEXV: return
    sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = 16 if kind != "pv" else 8; set_mat(kind)
    if kind == "pv":
        sc.world.color = (0.32, 0.32, 0.34); sun.data.energy = 3.0
    elif kind in ("tex", "guide"):
        sc.world.color = (0, 0, 0); sc.eevee.taa_render_samples = 1  # 1 sample: no AA, exact colours
    else:
        sc.world.color = (0, 0, 0); sc.view_settings.view_transform = "Raw"; sc.render.image_settings.color_depth = "16"
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
def px(p):
    co = world_to_camera_view(sc, cam, p); return [round(co.x * CELL, 3), round((1 - co.y) * CELL, 3)]
W_ = lambda n, at: ao.matrix_world @ getattr(pbs[n], at)
def meta():
    m = {"head": px((W_("head", "head") + W_("head", "tail")) / 2), "neck": px(W_("neck", "head")), "pelvis": px(W_("pelvis", "head"))}
    for s in "LR": m["foot." + s] = px(W_("toe." + s, "head")); m["hand." + s] = px(W_("hand." + s, "head"))
    return m
# ---- round 3: face anchors (empties face.* parented to the head bone; rest data in ao["face_anchors"] / rig/face_anchors.json)
FAJ = json.loads(ao.get("face_anchors", "{}")); _NHF = None; _OUT = _AL.get(VIEW, {"dx": 0, "dy": 0})
_FAS = json.load(open(os.path.join(EXP, "rig", "face_anchors.json")))["anchors"] if os.path.exists(os.path.join(EXP, "rig", "face_anchors.json")) else {}
def face_meta():
    """per anchor: px192 (192-cell 1x, float), px (128 game cell 1x incl. the output placement dx/dy of rig/align.json = the pixel frame coords),
    depth_m (distance from the camera plane), facing (anchor normal . toward-camera, -1..1), visible (facing > 0.05 and the surface point is
    not occluded by the deformed mesh); head: rotation from rest in CAMERA axes (deg): pitch (+ = chin down / nod toward camera-bottom),
    yaw (+ = face turns toward screen right), roll (+ = top tilts toward screen left, CCW on screen)"""
    if not FAJ: return {}
    from mathutils.bvhtree import BVHTree
    global _NHF
    dg = bpy.context.evaluated_depsgraph_get(); be = body.evaluated_get(dg); me_ = be.data
    if _NHF is None:  # occluders = everything except the head group (the visual-hull head over-estimates the face -> self-hits are not real)
        pmA = [me_.attributes.get("pm_" + v_) for v_ in ("S", "SE", "E", "NE", "N", "SW", "W", "NW")]; fl_ = [0.0] * len(me_.polygons); hg = [0.0] * len(me_.polygons)
        for at_ in pmA:
            if at_: at_.data.foreach_get("value", fl_); hg = [max(x, y) for x, y in zip(hg, fl_)]
        _NHF = [tuple(p_.vertices) for p_, h_ in zip(me_.polygons, hg) if h_ < 0.5]
    vs_ = [be.matrix_world @ v_.co for v_ in me_.vertices]; bvh = BVHTree.FromPolygons(vs_, _NHF)
    Mh = (ao.matrix_world @ pbs["head"].matrix) @ (ao.matrix_world @ REST["head"]).inverted(); R3 = Mh.to_3x3()
    Ci = cam.matrix_world.inverted(); tocam = cam.matrix_world.to_3x3().col[2].normalized(); out = {}
    for n, a in FAJ.items():
        pw = Mh @ Vector(a["rest"]); nw = (R3 @ Vector(a["normal"])).normalized(); fac = float(nw.dot(tocam))
        sw = Mh @ Vector(_FAS[n]["surf"]) if n in _FAS and "surf" in _FAS[n] else pw; vis = fac > 0.05
        hit = bvh.ray_cast(sw + tocam * 0.006, tocam, 5.0); occ = None if hit[0] is None else round(hit[3], 4)
        vis = vis and (occ is None or occ < 0.01)  # facing handles head self-occlusion (turns); occluders = body, arms, hands, hair locks below the head
        q = px(pw); out[n] = {"px192": q, "px": [round(q[0] - 32 + _OUT["dx"], 3), round(q[1] - 32 + _OUT["dy"], 3)],
                             "depth_m": round(-(Ci @ pw).z, 4), "facing": round(fac, 3), "occ_m": occ, "visible": bool(vis)}
    Ct = cam.matrix_world.to_3x3().transposed(); R0 = (ao.matrix_world @ REST["head"]).to_3x3()
    f0 = Ct @ (R0 @ Vector((0, 0, 1))); f1 = Ct @ (R3 @ R0 @ Vector((0, 0, 1))); u0 = Ct @ (R0 @ Vector((0, 1, 0))); u1 = Ct @ (R3 @ R0 @ Vector((0, 1, 0)))
    wrap = lambda d: (d + 180) % 360 - 180
    yaw = wrap(math.degrees(math.atan2(f1.x, f1.z) - math.atan2(f0.x, f0.z))); pitch = math.degrees(math.asin(max(-1, min(1, -f1.y))) - math.asin(max(-1, min(1, -f0.y))))
    roll = wrap(math.degrees(math.atan2(-u1.x, u1.y) - math.atan2(-u0.x, u0.y)))
    out["_head"] = {"pitch": round(pitch, 2), "yaw": round(yaw, 2), "roll": round(roll, 2),
                    "centre_px": [round(c, 3) for c in [px((W_("head", "head") + W_("head", "tail")) / 2)[0] - 32 + _OUT["dx"], px((W_("head", "head") + W_("head", "tail")) / 2)[1] - 32 + _OUT["dy"]]]}
    return out
# ------------------------------------------------------------------ render
kinds = ["pv"] if PREVIEW else os.environ.get("KINDS", "guide,lum,dep,tex,lid").split(",")
stem = os.path.join(OUT, f"{act}_{VIEW}")
t0 = time.time()
apply({"bones": {}}); rest_meta = meta()
if not PREVIEW: rpass(stem + "_rest_guide.png", "guide")
info = {"action": act, "view": VIEW, "cell_1x": CELL, "pivot_1x": PIV, "ppu_h2": PPU, "m_per_h2": K, "scale": SC, "preview": PREVIEW, "yaw": YAW, "tex": TEXV,
        "rest": rest_meta, "rest_face": face_meta(), "out_dxdy": [_OUT.get("dx", 0), _OUT.get("dy", 0)], "frames": []}
for i in idxs:
    fr = frames[i]; apply(fr); CUR["fr"] = fr; ftex = set_face(fr)
    for k in kinds: rpass(f"{stem}_f{i:02d}_{k}.png", k)
    info["frames"].append({"i": i, "t": fr.get("t", i), "ms": tim[i] if i < len(tim) else tim[-1], "pts": meta(), "face": face_meta(), "face_tex": ftex, "proj_view": CUR.get("eff")})
json.dump(info, open(stem + ".json", "w"), indent=0)
print(f"RENDERED {len(idxs)} frames x {kinds} in {time.time() - t0:.1f}s", flush=True)
if not NOPOST:
    cmd = [PYX, os.path.join(HERE, "pixel_chain.py"), stem + ".json"] + (["--stamp"] if STAMP else [])
    r = subprocess.run(cmd, capture_output=True, text=True); print(r.stdout[-2000:], r.stderr[-2000:], flush=True)
print("ALLDONE", flush=True)
