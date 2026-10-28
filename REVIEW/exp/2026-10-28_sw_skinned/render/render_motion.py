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
YAW = float(next((f.split("=")[1] for f in flags if f.startswith("--yaw=")), {"SE": -15.0}.get(VIEW, 0.0)))  # view cheat: whole-rig turn about Z (deg, - = toward the SE camera); SE default -15 = master 3/4 frontality (rig/qa/yaw_SE_sweep.png)
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
def mk(kind):
    nm = "rm_" + kind
    if nm in bpy.data.materials: return bpy.data.materials[nm]
    m = bpy.data.materials.new(nm); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    for n in list(N): N.remove(n)
    out = N.new("ShaderNodeOutputMaterial")
    if kind == "pv":
        at = N.new("ShaderNodeAttribute"); at.attribute_name = "PV" if "PV" in body.data.color_attributes else "Color"; df = N.new("ShaderNodeBsdfPrincipled")
        L.new(at.outputs["Color"], df.inputs["Base Color"]); df.inputs["Roughness"].default_value = 0.8
        L.new(df.outputs[0], out.inputs[0]); return m
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
def set_mat(kind):
    body.data.materials.clear(); body.data.materials.append(mk(kind))
def rpass(path, kind):
    sc.view_settings.view_transform = "Standard"; sc.render.image_settings.color_depth = "8"
    if kind == "guide":
        sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "FLAT"; sh.color_type = "VERTEX"
        sh.show_object_outline = False; sh.show_cavity = False; sc.display.render_aa = "OFF"
    else:
        sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = 16 if kind != "pv" else 8; set_mat(kind)
        if kind == "pv":
            sc.world.color = (0.32, 0.32, 0.34); sun.data.energy = 3.0
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
# ------------------------------------------------------------------ render
kinds = ["pv"] if PREVIEW else os.environ.get("KINDS", "guide,lum,dep").split(",")
stem = os.path.join(OUT, f"{act}_{VIEW}")
t0 = time.time()
apply({"bones": {}}); rest_meta = meta()
if not PREVIEW: rpass(stem + "_rest_guide.png", "guide")
info = {"action": act, "view": VIEW, "cell_1x": CELL, "pivot_1x": PIV, "ppu_h2": PPU, "m_per_h2": K, "scale": SC, "preview": PREVIEW,
        "rest": rest_meta, "frames": []}
for i in idxs:
    fr = frames[i]; apply(fr)
    for k in kinds: rpass(f"{stem}_f{i:02d}_{k}.png", k)
    info["frames"].append({"i": i, "t": fr.get("t", i), "ms": tim[i] if i < len(tim) else tim[-1], "pts": meta()})
json.dump(info, open(stem + ".json", "w"), indent=0)
print(f"RENDERED {len(idxs)} frames x {kinds} in {time.time() - t0:.1f}s", flush=True)
if not NOPOST:
    cmd = [PYX, os.path.join(HERE, "pixel_chain.py"), stem + ".json"] + (["--stamp"] if STAMP else [])
    r = subprocess.run(cmd, capture_output=True, text=True); print(r.stdout[-2000:], r.stderr[-2000:], flush=True)
print("ALLDONE", flush=True)
