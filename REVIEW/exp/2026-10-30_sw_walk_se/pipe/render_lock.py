"""render_lock.py (Blender, step 1c): play a motion file on pipe/rig_lock.blend through the game camera and write the 8x passes the
lock chain needs.  Lean copy of <skinned>/render/render_motion.py (same camera, cell, PPU, per-view yaw + head-yaw cheat from
rig/align.json, same motion semantics); no illustration/texture code.
  <blender> -b pipe/rig_lock.blend -P pipe/render_lock.py -- MOTION.json VIEW OUTDIR
Per frame fNN (192 cell x 8 = 1536 px, crop 256..1280 = the 128 game cell):
  _guide.png  material id (Workbench flat vertex colour 'Color', AA off)       _part.png  body part id (flat 'PARTID')
  _nrm.png    camera-space normal * .5 + .5 (EEVEE emission, 1 sample, 16 bit) _dep.png   camera depth in metres / 20 (16 bit)
<act>_<VIEW>.json: per frame ms, key, face expression keys, root_motion_m, eye surface points (screen px in the 128 cell incl. the
align.json output shift, depth m, facing) and hand/foot joints."""
import bpy, sys, os, json, math
from mathutils import Vector, Matrix, Quaternion
from bpy_extras.object_utils import world_to_camera_view
argv = sys.argv[sys.argv.index("--") + 1:]
MOT, VIEW, OUT = argv[:3]
SK = "/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned"
AL = dict(json.load(open(SK + "/rig/align.json"))[VIEW])
_LV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lock_view.json")  # Amendment 1: per-view overrides (yaw cheat, dx/dy) for the lock
if os.path.exists(_LV): AL.update(json.load(open(_LV)).get(VIEW, {}))
for _k in ("yaw", "head_yaw_off", "dx", "dy"):  # sweep overrides (env LOCK_<KEY>)
    if os.environ.get("LOCK_" + _k.upper()) is not None: AL[_k] = float(os.environ["LOCK_" + _k.upper()])
AL["dx"], AL["dy"] = int(AL.get("dx", 0)), int(AL.get("dy", 0))
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene; ao = bpy.data.objects["rig"]; body = bpy.data.objects["body"]; pbs = ao.pose.bones
K = float(ao.get("units_per_h2", 0.775)); CELL, PIV, PPU, SC = 192, (96, 152), 52.608, 8
M = json.load(open(MOT)) if MOT != "rest" else {"action": "rest", "frames": [{"bones": {}}]}; frames = M["frames"]; act = M.get("action", "walk")
tim = M.get("timing_ms") or [round(1000 / M.get("fps", 24))] * len(frames)
ao.rotation_mode = "XYZ"; ao.rotation_euler = (0, 0, math.radians(AL.get("yaw", 0.0)))
for p in pbs: p.rotation_mode = "QUATERNION"
REST = {p.name: ao.data.bones[p.name].matrix_local.copy() for p in pbs}


def apply(fr):
    for p in pbs: p.rotation_quaternion = (1, 0, 0, 0); p.location = (0, 0, 0); p.scale = (1, 1, 1)
    loc = Vector(fr.get("root", {}).get("loc", [0, 0, 0])); R3 = REST["root"].to_3x3()
    pbs["root"].location = R3.transposed() @ (loc - REST["root"].translation)
    for n, v in fr.get("bones", {}).items():
        if n in pbs and "rot" in v: pbs[n].rotation_quaternion = Quaternion(v["rot"])
    for n, s in (fr.get("scale") or {}).items():
        if n in pbs: pbs[n].scale = Vector(s)
    bpy.context.view_layer.update(); head_cheat()


def head_cheat():  # render_motion.head_cheat: extra head yaw toward the camera (SE -10 deg) + yaw clamp, every frame
    off = float(AL.get("head_yaw_off", 0.0)); lim = AL.get("head_yaw_limit")
    if not off and lim is None: return
    pb = pbs["head"]; Mh = pb.matrix.copy(); f = Mh.to_3x3() @ Vector((0, 0, 1)); f0 = REST["head"].to_3x3() @ Vector((0, 0, 1))
    yaw = math.degrees(math.atan2(f0.x * f.y - f0.y * f.x, f0.x * f.x + f0.y * f.y)); tgt = yaw + off
    if lim is not None: tgt = max(-float(lim) + off, min(float(lim) + off, tgt))
    d = math.radians(tgt - yaw)
    if abs(d) < 1e-6: return
    h = Mh.translation.copy(); pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(d, 4, "Z") @ Matrix.Translation(-h) @ Mh
    bpy.context.view_layer.update()


# camera (contract frame: her front +Y, her left -X), identical to render_motion.py
AZ = {"SE": (1, 1), "E": (1, 0), "S": (0, 1), "SW": (-1, 1), "NE": (1, -1), "N": (0, -1), "W": (-1, 0), "NW": (-1, -1)}
cam = bpy.data.objects.get("cam") or bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
sc.camera = cam; cam.data.type = "ORTHO"; cam.data.ortho_scale = CELL / PPU * K
cam.data.shift_x = 0.5 - PIV[0] / CELL; cam.data.shift_y = PIV[1] / CELL - 0.5; cam.data.clip_start = 0.1; cam.data.clip_end = 100
c = Vector((*AZ[VIEW], 0)).normalized(); el = math.radians(30); DIST = 10 * K
cam.location = Vector((c.x * math.cos(el), c.y * math.cos(el), math.sin(el))) * DIST
cam.rotation_euler = (-cam.location).to_track_quat("-Z", "Y").to_euler()
if not sc.world: sc.world = bpy.data.worlds.new("w")
sc.world.color = (0, 0, 0)
sc.render.resolution_x = sc.render.resolution_y = CELL * SC; sc.render.film_transparent = True; sc.render.resolution_percentage = 100
sc.render.dither_intensity = 0.0  # no output dither: exact matid/part colours and bit-identical passes run to run


def emission_mat(kind):
    m = bpy.data.materials.new("lock_" + kind); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N): N.remove(n)
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); L.new(em.outputs[0], out.inputs[0])
    g = N.new("ShaderNodeNewGeometry"); vt = N.new("ShaderNodeVectorTransform"); vt.convert_from = "WORLD"; vt.convert_to = "CAMERA"
    if kind == "rpos":  # rest position (normalised in the rig's lock_rpos_box), raw 16 bit
        at = N.new("ShaderNodeAttribute"); at.attribute_type = "GEOMETRY"; at.attribute_name = "RPOS"; L.new(at.outputs["Color"], em.inputs[0])
        return m
    if kind == "nrm":
        vt.vector_type = "NORMAL"; L.new(g.outputs["Normal"], vt.inputs[0])
        ma = N.new("ShaderNodeVectorMath"); ma.operation = "MULTIPLY_ADD"; ma.inputs[1].default_value = (.5, .5, .5); ma.inputs[2].default_value = (.5, .5, .5)
        L.new(vt.outputs[0], ma.inputs[0]); L.new(ma.outputs[0], em.inputs[0])
    else:  # dep: camera-space z (shader camera space: +z forward, metres) / 20
        vt.vector_type = "POINT"; L.new(g.outputs["Position"], vt.inputs[0]); sp = N.new("ShaderNodeSeparateXYZ"); L.new(vt.outputs[0], sp.inputs[0])
        mm = N.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = 1 / 20; L.new(sp.outputs["Z"], mm.inputs[0]); L.new(mm.outputs[0], em.inputs[0])
    return m


MATS = {k: emission_mat(k) for k in ("nrm", "dep", "rpos")}


def rpass(path, kind):
    sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"; sc.view_settings.exposure = 0; sc.view_settings.gamma = 1
    sc.render.image_settings.color_mode = "RGBA"; cas = body.data.color_attributes
    if kind in ("guide", "part"):
        cas.active_color = cas["Color" if kind == "guide" else "PARTID"]; sc.render.image_settings.color_depth = "8"
        sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "FLAT"; sh.color_type = "VERTEX"
        sh.show_object_outline = False; sh.show_cavity = False; sc.display.render_aa = "OFF"
    else:
        body.data.materials.clear(); body.data.materials.append(MATS[kind])
        sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = 1
        sc.view_settings.view_transform = "Raw"; sc.render.image_settings.color_depth = "16"
    sc.render.filepath = path; bpy.ops.render.render(write_still=True); cas.active_color = cas["Color"]


def px(p):
    co = world_to_camera_view(sc, cam, p); return [co.x * CELL - 32 + AL.get("dx", 0), (1 - co.y) * CELL - 32 + AL.get("dy", 0)]


EYEV = json.loads(ao.get("lock_eye_verts", "{}")); tocam = None


def eyes():
    dg = bpy.context.evaluated_depsgraph_get(); me = body.evaluated_get(dg).data; Ci = cam.matrix_world.inverted()
    tc = cam.matrix_world.to_3x3().col[2].normalized(); out = {}
    for k, i in EYEV.items():
        v = me.vertices[i]; pw = body.matrix_world @ v.co; nw = (body.matrix_world.to_3x3() @ v.normal).normalized()
        out[k] = {"px": [round(x, 3) for x in px(pw)], "depth_m": round(-(Ci @ pw).z, 4), "facing": round(float(nw.dot(tc)), 3)}
    return out


W_ = lambda n, at: ao.matrix_world @ getattr(pbs[n], at)
info = {"action": act, "view": VIEW, "align": AL, "rpos_box": json.loads(ao.get("lock_rpos_box", "null")), "cell": CELL, "scale": SC, "frames": []}
for i, fr in enumerate(frames):
    apply(fr)
    for k in os.environ.get("LOCK_KINDS", "guide,part,nrm,dep,rpos").split(","): rpass(os.path.join(OUT, f"{act}_{VIEW}_f{i:02d}_{k}.png"), k)
    pts = {f"{j}.{s}": [round(x, 3) for x in px(W_(f"{j}.{s}", "head"))] for j in ("hand", "toe") for s in "LR"}
    info["frames"].append({"i": i, "ms": tim[i], "key": fr.get("key", ""), "face": fr.get("face"), "blink": fr.get("blink", 0),
                           "mouth": fr.get("mouth"), "root_motion_m": fr.get("root_motion_m"), "eyes": eyes(), "pts": pts})
json.dump(info, open(os.path.join(OUT, f"{act}_{VIEW}.json"), "w"), indent=0)
print("LOCK_RENDERED", len(frames), "frames ->", OUT, flush=True)
