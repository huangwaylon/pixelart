# Blender -b --factory-startup -P rig_parts.py -- PARTS_DIR SKEL.txt KEYS.json OUT_DIR [actions,comma|all] [dirs=SE,E]
# Round 3: RIGID part rig. PARTS strand parts (head/bow/bun/torso/skirt/arm_L/R/leg_L/R; glb frame Y up, faces +Z, her left +X, feet y=-1)
# are parented 1:1 to bones of the same humanoid armature as rig.py (bone heads moved onto pivots.json). Legs are cut at the knee
# (thigh piece + shin/boot piece + knee ball) so crouches can bend; arms stay one rigid piece (cutout-rig style), katana on hand.R.
# Same keys.json pose table (lean / blade / sq / lift / fwd), same 30 deg iso camera + head-turn-to-camera cheat, same fNN_{matid,shade}.png.
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Euler
a = sys.argv[sys.argv.index("--") + 1:]
pdir, skp, keyp, outd = a[:4]
acts = a[4] if len(a) > 4 else "all"; dirs = (a[5] if len(a) > 5 else "SE,E").split(",")
CELL, SC, PIV = 96, 4, (48, 88)
ABD = 12.0; PPU = 26.0
SKMAX = float(os.environ.get('SKMAX', '30'))
SKL = float(os.environ.get('SKL', '0.78'))   # skirt length scale about its waist pivot (shows the legs)   # skirt tilt clamp (deg)
bpy.ops.wm.read_factory_settings(use_empty=True)
piv = {k: v for k, v in json.load(open(os.path.join(pdir, "pivots.json"))).items() if not k.startswith("_")}
parts = {}
for n in piv:
    bpy.ops.import_scene.gltf(filepath=os.path.join(pdir, n + ".glb"))
    ms = [o for o in bpy.context.selected_objects if o.type == "MESH"]
    for o in ms: o.data.transform(o.matrix_world); o.parent = None; o.matrix_world = Matrix.Identity(4)
    if len(ms) > 1:
        bpy.ops.object.select_all(action="DESELECT")
        for o in ms: o.select_set(True)
        bpy.context.view_layer.objects.active = ms[0]; bpy.ops.object.join()
    o = ms[0]; o.name = n; parts[n] = o
for o in list(bpy.context.scene.objects):
    if o.type != "MESH": bpy.data.objects.remove(o)
for o in parts.values():
    if o.data.color_attributes: o.data.color_attributes[0].name = "Color"
V = np.concatenate([np.array([v.co[:] for v in o.data.vertices]) for n, o in parts.items() if n != "katana"])
# glb -> blender: (x, y, z)glb = (x, -y?..) importer gives Z-up, faces -Y.  feet = min z, legs symmetric
zlo, H = V[:, 2].min(), V[:, 2].max() - V[:, 2].min(); S = 2.0 / H
T = Matrix.Scale(S, 4) @ Matrix.Translation(Vector((0, 0, -zlo)))
for o in parts.values(): o.data.transform(T)
def P(p): return T @ Vector((p[0], -p[2], p[1]))
def gz(y): return (y - zlo) * S
sk = np.loadtxt(skp)
# ---------------- armature (as rig.py) + pivots
arm = bpy.data.armatures.new("rig"); ao = bpy.data.objects.new("rig", arm); bpy.context.scene.collection.objects.link(ao)
bpy.context.view_layer.objects.active = ao; bpy.ops.object.mode_set(mode="EDIT")
E = arm.edit_bones
def bone(name, h, t, parent=None):
    b = E.new(name); b.head = h; b.tail = t
    if parent: b.parent = E[parent]
    return b
def row(i): return P(sk[i, :3]), P(sk[i, 3:])
bone("root", Vector((0, 0, 0)), Vector((0, 0.3, 0)))
pel = P(sk[0, :3]); bone("hips", pel, pel + Vector((0, 0, -0.15)), "root")
bone("spine", *row(0), "hips"); bone("chest", *row(1), "spine"); bone("neck", *row(2), "chest"); bone("head", *row(3), "neck")
for s, (ia, ie, iw) in (("R", (7, 8, 9)), ("L", (26, 27, 28))):
    bone(f"upper_arm.{s}", *row(ia), "chest"); bone(f"forearm.{s}", *row(ie), f"upper_arm.{s}")
    h, t = row(iw); bone(f"hand.{s}", h, h + 2.2 * (t - h), f"forearm.{s}")
LX = {"R": P(piv["leg_R"]["pivot"]).x, "L": P(piv["leg_L"]["pivot"]).x}
for s, (it, ik, ia) in (("R", (45, 46, 47)), ("L", (48, 49, 50))):
    def lx(v): v = v.copy(); v.x = LX[s]; return v
    h, t = row(it); bone(f"thigh.{s}", lx(h), lx(t), "hips")
    h2, t2 = row(ik); bone(f"shin.{s}", lx(t), lx(t2), f"thigh.{s}")
    h3, t3 = row(ia); bone(f"foot.{s}", lx(t2), lx(t3), f"shin.{s}")
bone("skirt", Vector((0, 0, 0)), Vector((0, 0, -0.3)), "hips")
for n, d in piv.items():  # move bone heads onto the part pivots (keep bone vectors)
    b = E.get(d["bone"])
    if b is None or d["bone"] == "head" and n != "head": continue
    vec = b.tail - b.head; b.head = P(d["pivot"]); b.tail = b.head + vec
for nm_, prt in (("bow", "bow"), ("bun", "bun")):  # own bones under head for 1-frame secondary lag
    vv_ = np.array([v.co[:] for v in parts[prt].data.vertices])
    if nm_ == "bow": h_ = Vector((vv_[:, 0].mean(), vv_[:, 1].mean(), vv_[:, 2].min() + 0.02)); t_ = h_ + Vector((0, 0, 0.15))
    else: h_ = Vector((vv_[:, 0].mean(), vv_[:, 1].min() + 0.02, vv_[:, 2].mean())); t_ = h_ + Vector((0, 0.12, 0))
    bone(nm_, h_, t_, "head")
for b in E: b.use_connect = False
for s_ in "RL":  # POSE strand fix: put the katana fist on the MESH hand (mitten centre), not on the skeleton wrist (~1/3 arm short on re-proportioned rigs)
    if "arm_" + s_ not in parts: continue
    vv_ = np.array([v.co[:] for v in parts["arm_" + s_].data.vertices]); sh_ = np.array(E["upper_arm." + s_].head[:])
    dd_ = np.linalg.norm(vv_ - sh_, axis=1); c_ = vv_[dd_ > np.percentile(dd_, 88)].mean(0)
    hb_ = E["hand." + s_]; vec_ = hb_.tail - hb_.head; hb_.head = Vector(c_) - vec_ / 2; hb_.tail = hb_.head + vec_
    E["forearm." + s_].tail = hb_.head.copy()
bpy.ops.object.mode_set(mode="OBJECT")
# ---------------- split legs at the knee (thigh piece / shin+boot piece) + knee ball
def split(o, zc, name_lo):
    me2 = o.data.copy(); lo = bpy.data.objects.new(name_lo, me2); bpy.context.scene.collection.objects.link(lo)
    for ob, keep_hi in ((o, True), (lo, False)):
        bm = bmesh.new(); bm.from_mesh(ob.data)
        kill = [f for f in bm.faces if (f.calc_center_median().z >= zc) != keep_hi]
        bmesh.ops.delete(bm, geom=kill, context="FACES"); bm.to_mesh(ob.data); bm.free()
    return lo
def ball(name, c, r, rgb):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=r, location=c); o = bpy.context.object; o.name = name
    ca = o.data.color_attributes.new("Color", "BYTE_COLOR", "POINT")
    for d in ca.data: d.color_srgb = (*[x / 255 for x in rgb], 1)
    return o
BIND = {}  # object -> bone
for n, d in piv.items():
    if n in parts and n != "katana": BIND[parts[n]] = n if n in ("bow", "bun") else d["bone"]
extra = []
for s in "RL":
    lg = parts[f"leg_{s}"]; kz = arm.bones[f"shin.{s}"].head_local.z
    lo = split(lg, kz, f"shin_{s}"); BIND[lo] = f"shin.{s}"
    vv = np.array([v.co[:] for v in lo.data.vertices]); near = vv[np.abs(vv[:, 2] - kz) < 0.03]
    r = 0.5 * max(np.ptp(near[:, 0]), np.ptp(near[:, 1])) if len(near) > 3 else 0.05
    c = Vector((near[:, 0].mean(), near[:, 1].mean(), kz)) if len(near) > 3 else arm.bones[f"shin.{s}"].head_local
    kb = ball(f"knee_{s}", c, r * 1.02, (0xf8, 0xda, 0xc2)); BIND[kb] = f"shin.{s}"; extra.append(kb)
# sleeves get their own darker red ID (dress red -> #8e222c) on the arm parts
SLV = (0x8e / 255, 0x22 / 255, 0x2c / 255)
for s in "RL":
    ca = parts[f"arm_{s}"].data.color_attributes["Color"]
    for d in ca.data:
        c = d.color_srgb
        if c[0] > 0.6 and c[1] < 0.35: d.color_srgb = (*SLV, 1)
def bind(o, bn):
    pb = arm.bones[bn]; o.parent = ao; o.parent_type = "BONE"; o.parent_bone = bn
    o.matrix_parent_inverse = (ao.matrix_world @ Matrix.Translation(pb.tail_local) @ pb.matrix_local.to_3x3().to_4x4()).inverted()
for o, bn in BIND.items(): bind(o, bn)
ARM_PI = {s_: (parts["arm_" + s_], parts["arm_" + s_].matrix_parent_inverse.copy()) for s_ in "RL" if "arm_" + s_ in parts}  # arm-stretch cheat
# ---------------- katana (as rig.py)
def box(name, size, loc, rgb):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    ca = o.data.color_attributes.new("Color", "BYTE_COLOR", "POINT")
    for d in ca.data: d.color_srgb = (rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, 1)
    return o
if "katana" in parts: bpy.data.objects.remove(parts.pop("katana"))
pb_hand = arm.bones["hand.R"]; fist = (pb_hand.head_local + pb_hand.tail_local) / 2
KL = float(os.environ.get("KL", "0.74"))  # blade length (char height 2)
hilt = box("hilt", (0.06, 0.24, 0.06), fist + Vector((0, 0.02, 0)), (0x24, 0x1c, 0x28))
tsuba = box("tsuba", (0.11, 0.025, 0.11), fist + Vector((0, -0.11, 0)), (0x24, 0x1c, 0x28))
blade = box("blade", (0.05, KL, 0.075), fist + Vector((0, -0.12 - KL / 2, 0)), (0xc8, 0xd0, 0xdc))
kat = [hilt, tsuba, blade]
for o in kat: bind(o, "hand.R")
bpy.context.view_layer.update()
ALL = list(BIND.keys()) + kat
# ---------------- materials (toon pass) as rig.py
def toon_mat(name, outline=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    for n in list(N): N.remove(n)
    o = N.new("ShaderNodeOutputMaterial")
    if outline:
        e = N.new("ShaderNodeEmission"); e.inputs[0].default_value = (0.012, 0.008, 0.01, 1); L.new(e.outputs[0], o.inputs[0])
        m.use_backface_culling = True; return m
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "Color"
    df = N.new("ShaderNodeBsdfDiffuse"); df.inputs[0].default_value = (1, 1, 1, 1)
    s2r = N.new("ShaderNodeShaderToRGB"); L.new(df.outputs[0], s2r.inputs[0])
    bw = N.new("ShaderNodeRGBToBW"); L.new(s2r.outputs[0], bw.inputs[0])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = "CONSTANT"
    el = cr.color_ramp.elements; el[0].position = 0.0; el[0].color = (0.42, 0.42, 0.46, 1); el[1].position = 0.18; el[1].color = (0.72, 0.72, 0.74, 1)
    e3 = el.new(0.55); e3.color = (1, 1, 1, 1)
    L.new(bw.outputs[0], cr.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 1
    ci = [i for i in mx.inputs if i.type == 'RGBA']; co = [o for o in mx.outputs if o.type == 'RGBA'][0]
    L.new(at.outputs[0], ci[0]); L.new(cr.outputs[0], ci[1])
    em = N.new("ShaderNodeEmission"); L.new(co, em.inputs[0]); L.new(em.outputs[0], o.inputs[0]); return m
TM, OM = toon_mat("toon"), toon_mat("outline", True)
for o in ALL:
    o.data.materials.clear(); o.data.materials.append(TM); o.data.materials.append(OM)
    so = o.modifiers.new("outline", "SOLIDIFY"); so.thickness = 0.008 if o in kat else 0.012; so.offset = 1; so.use_flip_normals = True
    so.material_offset = 1; so.show_render = False
# ---------------- scene / camera (identical to rig.py)
sc = bpy.context.scene
sc.render.resolution_x = sc.render.resolution_y = CELL * SC; sc.render.film_transparent = True
sc.view_settings.view_transform = "Standard"
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = CELL / PPU
cam.data.shift_x = 0.5 - PIV[0] / CELL; cam.data.shift_y = (PIV[1] / CELL) - 0.5
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun); sun.data.energy = 3.0
world = bpy.data.worlds.new("w"); sc.world = world; world.color = (0, 0, 0)
AZ = {"SE": (-1, -1), "E": (-1, 0), "S": (0, -1), "SW": (1, -1), "NE": (-1, 1), "N": (0, 1)}
VIEW = {'dn': 'SE'}
HEADV = {'SE': [-8, 0, -14], 'E': [-6, 0, float(os.environ.get('HEADV_E_TURN', '-10'))], 'S': [-8, 0, 0], 'NE': [0, 0, -10], 'N': [0, 0, 0]}
CHEAT = {'SE': float(os.environ.get('CHEAT', '0')), 'NE': -float(os.environ.get('CHEAT', '0'))}  # stride/blade yaw toward screen-x (legs+blade only)
HEADS = {'SE': float(os.environ.get('HEADS_SE', '1.07'))}  # head scale cheat on SE (face small under the deep bob)
def set_view(dn):
    VIEW['dn'] = dn
    c = Vector((*AZ[dn], 0)).normalized(); el = math.radians(30)
    loc = Vector((c.x * math.cos(el), c.y * math.cos(el), math.sin(el))) * 10
    cam.location = loc; cam.rotation_euler = (-loc).to_track_quat("-Z", "Y").to_euler()
    right = (-loc).normalized().cross(Vector((0, 0, 1))).normalized()
    ld = (-right * 0.7 + Vector((0, 0, 1)) * 0.9 + c * 0.6).normalized()
    sun.rotation_euler = (-ld).to_track_quat("-Z", "Y").to_euler()
# ---------------- posing
keys = json.load(open(keyp)); pbs = ao.pose.bones
for p in pbs: p.rotation_mode = "QUATERNION"
def pose(kd):
    ao.location = (0, 0, 0); ao.rotation_mode = "XYZ"; kd = dict(kd)
    yaw = kd.pop("yaw", 0.0); roll = kd.pop("roll", 0.0); bscr = kd.pop("blade_scr", None); scr = dict(kd.pop("scr", {})); bsc = dict(kd.pop("bs", {})); ik_ = {s_: kd.pop("ik." + s_) for s_ in "RL" if "ik." + s_ in kd}; ikg_ = {s_: kd.pop("ikg." + s_) for s_ in "RL" if "ikg." + s_ in kd}; drop_ = kd.pop("drop", 0.0)
    ao.rotation_euler = (0, 0, math.radians(yaw)); ao.scale = (1, 1, 1); bpy.context.view_layer.update()
    if roll:  # screen-plane lean of the whole figure about the root (feet) FIRST, so leg IK / scr / blade_scr are solved in the final screen frame
        vax = -cam.matrix_world.to_3x3().col[2]
        ao.matrix_world = Matrix.Rotation(math.radians(roll), 4, vax) @ ao.matrix_world; bpy.context.view_layer.update()
    for p in pbs: p.rotation_quaternion = (1, 0, 0, 0); p.location = (0, 0, 0); p.scale = (1, 1, 1)
    kd = dict(kd)
    for s_ in ("forearm.R", "forearm.L"): kd.pop(s_, None)   # arms are one rigid piece
    for s_ in ("upper_arm.R", "upper_arm.L", "head"): kd.setdefault(s_, [0, 0, 0])
    if VIEW['dn'] == 'E':  # parts hint: forward arm swing > ~60 deg clips the sleeve/hand into the obi in side views
        for s_ in ("upper_arm.R", "upper_arm.L"):
            e_ = kd[s_]
            if -110 < e_[0] < -60: kd[s_] = [-60, e_[1], e_[2]]
    hv = kd.pop("headv", HEADV.get(VIEW['dn'], [0, 0, 0])); kd['head'] = [kd['head'][i] + hv[i] for i in range(3)]
    ln = kd.pop("lean", 0)
    if ln:
        kd["hips"] = [kd.get("hips", [0, 0, 0])[0] + ln, 0, 0]
        for s_ in ("thigh.R", "thigh.L"): e_ = kd.get(s_, [0, 0, 0]); kd[s_] = [e_[0] - ln, e_[1], e_[2]]
    bl = kd.pop("blade", None); bs = kd.pop("blade_side", 0)  # absolute blade direction in her root frame, solved after posing
    if "skirt" not in kd:  # skirt shell tilts with the legs: follow the mean thigh swing, lean toward the leading thigh
        tx = [kd.get(f"thigh.{s}", [0, 0, 0])[0] + ln for s in "RL"]  # world thigh swing (lean already subtracted)
        ty = [kd.get(f"thigh.{s}", [0, 0, 0])[1] for s in "RL"]
        sx = max(-SKMAX, min(SKMAX, 0.40 * min(tx) + 0.20 * max(tx)))
        kd["skirt"] = [sx, 0.25 * (ty[0] + ty[1]) / 2, 0]
    gm = kd.pop("cheat", CHEAT.get(VIEW['dn'], 0.0))
    if gm:
        h_ = kd.get("hips", [0, 0, 0]); kd["hips"] = [h_[0], h_[1], h_[2] + gm]
        s_ = kd.get("spine", [0, 0, 0]); kd["spine"] = [s_[0], s_[1], s_[2] - gm]
    sa = kd.pop("skirt_add", None)
    if sa: kd["skirt"] = [kd["skirt"][i] + sa[i] for i in range(3)]
    sfl = kd.pop("skirt_flare", 1.0); sln = kd.pop("skirt_len", 1.0)
    bws = kd.pop("bow_s", None)
    q = kd.get("sq", 0.0); sy_ = kd.pop("sy", 1.0); absz = kd.pop("absz", 0)
    ao.scale = (1 + q / 2, (1 + q / 2) * sy_, 1 - q)  # sy = stretch along her travel axis (smears)
    for bn, e in kd.items():
        if bn in ("lift", "fwd", "katana", "sq", "hand_scale"): continue
        if bn.startswith("upper_arm"): e = [e[0], e[1] + (ABD if bn.endswith(".R") else -ABD), e[2]]
        R = arm.bones[bn].matrix_local.to_3x3(); Q = Euler([math.radians(x) for x in e], "XYZ").to_matrix()
        pbs[bn].rotation_quaternion = (R.inverted() @ Q @ R).to_quaternion()
    # flare the skirt a little when the legs spread (scale about its pivot)
    spread = abs(kd.get("thigh.R", [0, 0, 0])[0] - kd.get("thigh.L", [0, 0, 0])[0])
    f = (1 + min(0.18, spread / 600)) * sfl; pbs["skirt"].scale = (f, SKL * sln, f)
    if bws: pbs["bow"].scale = tuple(bws)
    hs = HEADS.get(VIEW['dn'], 1.0); pbs["head"].scale = (hs, hs, hs)
    stretch_ = {}
    for s_, (o_, pi_) in ARM_PI.items():  # arm stretch = mesh scaled along the rest arm axis about the shoulder (bone itself unscaled -> katana keeps its length)
        o_.matrix_parent_inverse = pi_.copy(); f_ = bsc.pop("upper_arm." + s_, None)
        if f_ is None: continue
        f_ = f_[1] if isinstance(f_, (list, tuple)) else f_; b_ = arm.bones["upper_arm." + s_]; p_ = b_.head_local; ax_ = (b_.tail_local - b_.head_local).normalized()
        S3 = Matrix.Identity(3) + (f_ - 1) * Matrix(((ax_.x * ax_.x, ax_.x * ax_.y, ax_.x * ax_.z), (ax_.y * ax_.x, ax_.y * ax_.y, ax_.y * ax_.z), (ax_.z * ax_.x, ax_.z * ax_.y, ax_.z * ax_.z)))
        o_.matrix_parent_inverse = pi_ @ Matrix.Translation(p_) @ S3.to_4x4() @ Matrix.Translation(-p_); stretch_[s_] = f_
    for bn_, sv_ in bsc.items(): pbs[bn_].scale = tuple(sv_) if isinstance(sv_, (list, tuple)) else (1, sv_, 1)  # other bone scales
    bpy.context.view_layer.update()
    def scr_dir(ang, dep):  # direction in the camera-facing VERTICAL plane: r = screen right (horizontal), z = world up; dep + = away from camera
        cm = cam.matrix_world.to_3x3(); r_ = cm.col[0].copy(); r_.z = 0; r_.normalize(); h_ = Vector((0, 0, 1)).cross(r_).normalized()
        a_, dp_ = math.radians(ang), math.radians(dep)
        dw = (r_ * math.cos(a_) + Vector((0, 0, 1)) * math.sin(a_)) * math.cos(dp_) + h_ * math.sin(dp_)
        return (ao.matrix_world.to_3x3().inverted() @ dw).normalized()
    def basis():
        cm = cam.matrix_world.to_3x3(); r_ = cm.col[0].copy(); r_.z = 0; r_.normalize(); return r_, Vector((0, 0, 1)), Vector((0, 0, 1)).cross(r_).normalized()
    WI = ao.matrix_world.to_3x3().inverted()
    if drop_:  # planted-feet mode: lower the body by `drop` leg lengths, feet targets ikg.* are absolute ground positions
        ao.location.z -= drop_ * (arm.bones["thigh.R"].length + arm.bones["shin.R"].length); bpy.context.view_layer.update()
    for s_ in "RL":
        g_ = ikg_.get(s_)
        if g_ is None: continue
        r_, z_, h_ = basis(); Lg = arm.bones["thigh." + s_].length + arm.bones["shin." + s_].length
        hipw = ao.matrix_world @ pbs["thigh." + s_].head
        ank0 = arm.bones["shin." + s_].tail_local.z * ao.scale.z  # rest ankle height above the sole
        tgt = Vector((ao.location.x, ao.location.y, 0)) + r_ * g_[0] * Lg + h_ * (g_[2] if len(g_) > 2 else 0) * Lg
        tgt.z = ank0 + (g_[1] if len(g_) > 1 else 0) * Lg
        rel = tgt - hipw
        ik_[s_] = [rel.dot(r_) / Lg, rel.z / Lg, rel.dot(h_) / Lg, g_[3] if len(g_) > 3 else 1, g_[4] if len(g_) > 4 else 0]
    for s_ in "RL":  # 2-bone leg IK in the camera-facing vertical plane: ik.S = [x, y, depth, knee] (x/y/depth in leg lengths from the hip joint; knee +1 = knee points screen right)
        ik = ik_.get(s_)
        if ik is None: continue
        r_, z_, h_ = basis(); th, sh = pbs["thigh." + s_], pbs["shin." + s_]
        L1 = arm.bones["thigh." + s_].length; L2 = arm.bones["shin." + s_].length; Lg = L1 + L2
        hipw = ao.matrix_world @ th.head
        tgt = hipw + (r_ * ik[0] + z_ * ik[1] + h_ * (ik[2] if len(ik) > 2 else 0)) * Lg
        dv = tgt - hipw; D = min(dv.length, 0.995 * Lg); dn = dv.normalized()
        hint = r_ * (ik[3] if len(ik) > 3 else 1) + h_ * (ik[4] if len(ik) > 4 else 0)
        bend = (hint - dn * hint.dot(dn)); bend = bend.normalized() if bend.length > 1e-4 else z_
        ca = (L1 * L1 + D * D - L2 * L2) / (2 * L1 * D); ca = max(-1, min(1, ca)); sa = math.sqrt(1 - ca * ca)
        knee = hipw + dn * (L1 * ca) + bend * (L1 * sa)
        scr["thigh." + s_] = (WI @ (knee - hipw)).normalized(); scr["shin." + s_] = (WI @ (hipw + dn * D - knee)).normalized()
        if "foot." + s_ not in scr: scr["foot." + s_] = None
    for bn_ in ("upper_arm.R", "upper_arm.L", "thigh.R", "shin.R", "foot.R", "thigh.L", "shin.L", "foot.L", "spine", "chest", "head"):
        if bn_ not in scr: continue
        sv = scr[bn_]
        if sv is None:  # keep the foot flat-ish: point the foot bone along its rest direction (world)
            continue
        dA = sv if isinstance(sv, Vector) else scr_dir(sv[0], sv[1] if len(sv) > 1 else 0)
        pb_ = pbs[bn_]; M = pb_.matrix.copy(); cur = M.to_3x3().col[1].normalized()
        pb_.matrix = Matrix.Translation(M.translation) @ (cur.rotation_difference(dA).to_matrix() @ M.to_3x3()).to_4x4()
        bpy.context.view_layer.update()
    for s_, f_ in stretch_.items():  # move the hand to the end of the stretched arm
        ph_ = pbs["hand." + s_]; sh_ = pbs["upper_arm." + s_].head.copy(); M = ph_.matrix.copy()
        ph_.matrix = Matrix.Translation(sh_ + (M.translation - sh_) * f_) @ M.to_3x3().to_4x4(); bpy.context.view_layer.update()
    if bscr is not None:  # screen-space blade: [angle deg (0 = screen right, 90 = up), depth deg (+ = away from camera)]
        dA = scr_dir(bscr[0], bscr[1] if len(bscr) > 1 else 0)
        ph_ = pbs["hand.R"]; M = ph_.matrix.copy(); R0 = arm.bones["hand.R"].matrix_local.to_3x3()
        cur = (M.to_3x3() @ R0.inverted() @ Vector((0, -1, 0))).normalized()
        ph_.matrix = Matrix.Translation(M.translation) @ (cur.rotation_difference(dA).to_matrix() @ M.to_3x3()).to_4x4()
        bpy.context.view_layer.update(); bl = None
    if bl is not None:  # rotate hand.R so the blade points along d (armature space): theta about X (0 fwd,90 down,180 back,270 up), side toward her right
        th, ph = math.radians(bl), math.radians(bs)
        d = Vector((0, -math.cos(th), -math.sin(th))) * math.cos(ph) + Vector((-1, 0, 0)) * math.sin(ph)
        if gm: d = Matrix.Rotation(math.radians(gm), 3, "Z") @ d
        ph_ = pbs["hand.R"]; M = ph_.matrix.copy(); R0 = arm.bones["hand.R"].matrix_local.to_3x3()
        cur = (M.to_3x3() @ R0.inverted() @ Vector((0, -1, 0))).normalized()
        q = cur.rotation_difference(d.normalized())
        ph_.matrix = Matrix.Translation(M.translation) @ (q.to_matrix() @ M.to_3x3()).to_4x4()
        bpy.context.view_layer.update()
    for o in kat: o.hide_render = not kd.get("katana", 0)
    bpy.context.view_layer.update()
    zmin = min((o.matrix_world @ o.data.vertices[i].co).z for o in BIND for i in range(0, len(o.data.vertices), 5))
    fv = Matrix.Rotation(math.radians(gm), 3, "Z") @ Vector((0, -kd.get("fwd", 0.0), 0))
    fv = Matrix.Rotation(math.radians(yaw), 3, "Z") @ fv
    ao.location = (fv.x, fv.y, (0.0 if absz else ao.location.z - zmin) + kd.get("lift", 0.0))  # absz: airborne, root height = lift (apex stays highest)
    bpy.context.view_layer.update()
def render(path, mode):
    if mode == "matid":
        sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "FLAT"; sh.color_type = "VERTEX"
        sh.show_object_outline = False; sh.show_cavity = False; sc.display.render_aa = "OFF"
        for o in ALL: o.modifiers["outline"].show_render = False
    else:
        sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = 8
        for o in ALL: o.modifiers["outline"].show_render = True
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
if os.environ.get("RIG_LIB") == "1": raise SystemExit  # used as a library by anim_parts.py (exec until here)
os.makedirs(outd, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outd, "rig_parts.blend"))
order = list(keys) if acts == "all" else acts.split(",")
for act in order:
    if act.startswith("_"): continue
    for dn in dirs:
        od = os.path.join(outd, f"{act}_{dn}"); os.makedirs(od, exist_ok=True); set_view(dn); names = []
        for fi, (kn, kd) in enumerate(keys[act].items()):
            pose(kd); names.append(kn)
            for mode in ("matid", "shade"): render(os.path.join(od, f"f{fi:02d}_{mode}.png"), mode)
        json.dump({"action": act, "dir": dn, "keys": names, "cell_1x": CELL, "scale": SC, "pivot_1x": PIV, "px_per_unit_1x": PPU,
                   "elev_deg": 30, "rig": "rigid parts " + pdir,
                   "ids": ["skin", "hair", "dress", "obi", "boots", "eyes", "bow", "sleeve", "blade", "hilt"]},
                  open(os.path.join(od, "keys.json"), "w"), indent=1)
        print("DONE", act, dn, names, flush=True)
